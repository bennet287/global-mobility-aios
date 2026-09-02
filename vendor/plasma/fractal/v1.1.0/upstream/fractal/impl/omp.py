"""Oh My Pi (omp) CLI agent implementation."""

from __future__ import annotations

import json
import pathlib
import time
from typing import Optional

from fractal.core.agent import Agent, Invocation, StreamEvent, StreamParser

__all__ = [
    'OmpParser',
    'OmpAgent',
]


class OmpParser(StreamParser):
    """Parser for omp ``-p --mode json`` output."""

    def __init__(self: OmpParser, *, model: Optional[str] = None) -> None:
        """Initialize ``OmpParser``.

        Bind the configured-model fallback and start the wall clock.
        """
        super().__init__(model=model)
        # omp reports per-turn cost but no invocation duration, so the close
        # falls back to wall time
        self._started = time.monotonic()

    def feed(self: OmpParser, line: str) -> list[StreamEvent]:
        """Parse one omp AgentSessionEvent line into normalized events."""
        # tolerate blank, malformed, and non-object lines (wire noise)
        line = line.strip()
        if not line:
            return []
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            return []
        if not isinstance(event, dict):
            return []
        events: list[StreamEvent] = []
        event_type = event.get('type')
        # the session header is the first frame and carries the agent-minted
        # id (omp mints it; a fresh run passes no id in)
        if event_type == 'session':
            session = event.get('id')
            if session and self.session is None:
                self.session = session
                events.append(
                    StreamEvent(kind='session', session=session, model=self.model)
                )
        # assistant text streams as text_delta events nested under the
        # message_update envelope (text_start/text_end bracket them)
        elif event_type == 'message_update':
            delta = event.get('assistantMessageEvent') or {}
            if delta.get('type') == 'text_delta':
                text = delta.get('delta')
                if text:
                    events.append(StreamEvent(kind='text', text=text))
        # tool invocations map to tool headers
        elif event_type == 'tool_execution_start':
            events.append(StreamEvent(kind='tool', tool=event.get('toolName', '?')))
        # a turn closes with its own per-turn usage (turns are NOT cumulative
        # -- a later turn can report fewer tokens), so accumulate the running
        # total and flush per turn (a stream killed by signal keeps the last
        # increment); the served model rides the same frame
        elif event_type == 'turn_end':
            message = event.get('message') or {}
            # the session header names no model, so the served model first
            # arrives here -- re-stamp the session once it is known so the
            # step row records the real model (record_session is idempotent;
            # the isinstance guards the wire type); every distinct served
            # model also joins the `models` record -- the row keeps only
            # the last, and a substitution that recovers mid-stream must
            # still stay visible to the drop check
            model = message.get('model')
            if isinstance(model, str) and model and self.session is not None:
                if model not in self.models:
                    self.models.append(model)
                if model != self.model:
                    self.model = model
                    events.append(
                        StreamEvent(kind='session', session=self.session, model=model)
                    )
            cost = ((message.get('usage') or {}).get('cost') or {}).get('total')
            if isinstance(cost, (int, float)):
                self.cost = (self.cost or 0.0) + cost
                events.append(StreamEvent(kind='cost', cost=self.cost))
            # an API failure (401/429/overload/context-overflow) rides a normal
            # turn_end with stopReason 'error' and no error-typed frame -- omp
            # still exits 0, so without this the step books completed doing zero
            # work; classify it so the step fails and names the cause
            if message.get('stopReason') == 'error':
                detail = message.get('errorMessage') or 'omp turn failed'
                self.errors.append(str(detail))
                events.append(StreamEvent(kind='error', message=str(detail)))
        # the agent close is the invocation's authoritative end
        elif event_type == 'agent_end':
            self.final = True
            wall = time.monotonic() - self._started
            events.append(
                StreamEvent(kind='result', cost=self.cost, final=True, duration=wall)
            )
        # surface errors -- omp also exits non-zero on failure, but the errors
        # list fails the step even on an exit-0 drain (isinstance guards the
        # substring test against a non-string type on wire noise)
        elif isinstance(event_type, str) and 'error' in event_type:
            detail = event.get('message') or event.get('error') or 'unknown error'
            self.errors.append(str(detail))
            events.append(StreamEvent(kind='error', message=str(detail)))
        return events


class OmpAgent(Agent):
    """Oh My Pi CLI backend (cost-reporting, agent-minted sessions).

    Todo:
        Resolve the ``config.yml`` default model once a YAML parser is
        available (``_config_model`` falls back to the base ``None``).

    """

    name = 'omp'
    config_file = 'config.yml'
    can_fork = True
    mints_session = True
    needs_pricing = False
    cost_scope = 'call'
    enforces_budget = False
    providers = ()

    __parser__ = OmpParser

    def _invocation(
        self: OmpAgent,
        prompt: str,
        *,
        mode: str,
        session: Optional[str],
        model: Optional[str],
        effort: Optional[str],
        budget: Optional[float],
    ) -> Invocation:
        """Build the omp ``-p --mode json`` invocation."""
        # --yolo auto-approves every tool call: mandatory for an unattended
        # run (the seed config sets approvalMode too; the flag is the
        # belt-and-braces against a config that re-tightens it)
        argv = [*self.parts, '-p', '--mode', 'json', '--yolo']
        if model:
            argv += ['--model', model]
        # omp spells reasoning effort as a thinking level
        if effort:
            argv += ['--thinking', effort]
        # resume the agent-minted session in place, or fork it to a new id
        if mode == 'resume':
            argv += ['-r', session]
        elif mode == 'fork':
            argv += ['--fork', session]
        # a '--' sentinel ends option parsing, so a message whose first char is
        # '-' ('-1 on that', '--continue looks right') is the message, never
        # mistaken for a flag that fails the run or silently flips a boolean option
        argv += ['--', prompt]
        # run in the worktree (omp anchors the project at the cwd);
        # PI_CODING_AGENT_DIR relocates config, credentials, and the session
        # tree to the node dir; the env carries only the reserved
        # PI_CODING_AGENT_DIR; provider keys (OPENROUTER_API_KEY, ...) ride the
        # ambient environment invocation() composes under it
        env = {'PI_CODING_AGENT_DIR': str(self.config_dir)}
        return Invocation(
            agent=self.name,
            argv=tuple(argv),
            cwd=self.node.worktree,
            env=env,
            session=session,
        )

    def _transcript(self: OmpAgent, session: str) -> Optional[pathlib.Path]:
        """Newest session log under the node's own omp home.

        omp writes one JSONL file per session, nested under a
        ``sessions/`` directory omp derives from the working directory
        (the slug scheme is omp's private contract, so the glob
        wildcards it); ``None`` until omp creates the file (the
        timestamp prefix makes the path unconstructable in advance).
        """
        sessions_dir = self.config_dir / 'sessions'
        # sort on the filename: its timestamp prefix orders chronologically,
        # where a full-path sort would rank the wildcarded slug directory
        # above the timestamp
        found = sorted(
            sessions_dir.glob(f'*/*_{session}.jsonl'),
            key=lambda path: path.name,
        )
        if found:
            return found[-1]
        return None
