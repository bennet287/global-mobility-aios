"""opencode CLI agent implementation."""

from __future__ import annotations

import json
import pathlib
import time
from typing import Optional

from fractal.core.agent import Agent, Invocation, StreamEvent, StreamParser

__all__ = [
    'OpencodeParser',
    'OpencodeAgent',
]


class OpencodeParser(StreamParser):
    """Parser for opencode ``run --format json`` output."""

    def __init__(self: OpencodeParser, *, model: Optional[str] = None) -> None:
        """Initialize ``OpencodeParser``.

        Bind the configured-model fallback and start the wall clock.
        """
        super().__init__(model=model)
        # opencode reports per-step cost but no invocation duration, so the
        # close falls back to wall time
        self._started = time.monotonic()

    def feed(self: OpencodeParser, line: str) -> list[StreamEvent]:
        """Parse one opencode JSON event line into normalized events."""
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
        # capture the real session (opencode stamps sessionID on every event)
        # off the first event carrying one -- opencode mints the id itself
        if self.session is None:
            session = event.get('sessionID')
            if session:
                self.session = session
                events.append(
                    StreamEvent(kind='session', session=session, model=self.model)
                )
        event_type = event.get('type')
        # payloads nest under part
        part = event.get('part') or {}
        # assistant text streams as text
        if event_type == 'text':
            text = part.get('text')
            if text:
                events.append(StreamEvent(kind='text', text=text))
        # tool invocations map to tool headers
        elif event_type == 'tool_use':
            events.append(StreamEvent(kind='tool', tool=part.get('tool', '?')))
        # step close -- opencode reports its own authoritative per-step cost,
        # so accumulate the running total and flush per frame (a stream killed
        # by signal still has the last step recorded); the final step closes
        # final=True on the stop reason (mid-run steps close on 'tool-calls')
        elif event_type == 'step_finish':
            cost = part.get('cost')
            if isinstance(cost, (int, float)):
                self.cost = (self.cost or 0.0) + cost
                events.append(StreamEvent(kind='cost', cost=self.cost))
            final = part.get('reason') == 'stop'
            if final:
                self.final = True
            wall = time.monotonic() - self._started
            events.append(
                StreamEvent(kind='result', cost=self.cost, final=final, duration=wall)
            )
        # surface errors -- opencode also exits non-zero on failure, but the
        # errors list fails the step even on an exit-0 drain
        elif event_type == 'error':
            error = event.get('error') or {}
            # the error payload's shape varies -- a plain string, or a dict
            # whose own data field may be a string -- so guard both the way the
            # codex parser does, else a string-shaped error crashes the parse
            if isinstance(error, dict):
                data = error.get('data') or {}
                message = data.get('message') if isinstance(data, dict) else data
                detail = message or error.get('name') or 'unknown error'
            else:
                detail = error or 'unknown error'
            self.errors.append(str(detail))
            events.append(StreamEvent(kind='error', message=str(detail)))
        return events


class OpencodeAgent(Agent):
    """opencode CLI backend (cost-reporting, agent-minted sessions)."""

    name = 'opencode'
    config_file = 'opencode.json'
    can_fork = True
    mints_session = True
    needs_pricing = False
    cost_scope = 'call'
    enforces_budget = False
    results_per_step = True
    providers = ()

    __parser__ = OpencodeParser

    def _invocation(
        self: OpencodeAgent,
        prompt: str,
        *,
        mode: str,
        session: Optional[str],
        model: Optional[str],
        effort: Optional[str],
        budget: Optional[float],
    ) -> Invocation:
        """Build the opencode ``run --format json`` invocation."""
        # --auto is mandatory headlessly: without it every 'ask' permission
        # is silently rejected (the seed config allows; --auto is the
        # belt-and-braces against a worktree config re-tightening)
        argv = [*self.parts, 'run', '--format', 'json', '--auto']
        if model:
            argv += ['-m', model]
        # opencode spells reasoning effort as a model variant
        if effort:
            argv += ['--variant', effort]
        # resume the minted session in place, or branch it with --fork
        if mode == 'resume':
            argv += ['--session', session]
        elif mode == 'fork':
            argv += ['--session', session, '--fork']
        # a '--' sentinel ends option parsing (opencode's run uses yargs), so a
        # message whose first char is '-' ('-1 on that', '--continue looks
        # right') is the message, never mistaken for a flag that fails the run
        # or silently flips a boolean option
        argv += ['--', prompt]
        # run in the worktree (opencode walks up from the cwd to the git root
        # for project identity); OPENCODE_CONFIG points config at the node's
        # file; the env carries only the reserved OPENCODE_CONFIG; provider
        # keys (OPENROUTER_API_KEY, ANTHROPIC_API_KEY, ...) are auto-detected
        # from the ambient environment invocation() composes under it
        env = {'OPENCODE_CONFIG': str(self.config_dir / self.config_file)}
        return Invocation(
            agent=self.name,
            argv=tuple(argv),
            cwd=self.node.worktree,
            env=env,
            session=session,
        )

    def _config_model(self: OpencodeAgent) -> Optional[str]:
        """Resolve the model opencode's own node config defaults to.

        opencode reads the node's ``OPENCODE_CONFIG`` file; ``None`` when
        it names no top-level model.
        """
        config = self.config_dir / self.config_file
        if not config.is_file():
            return None
        # an unreadable or malformed config names no model
        try:
            with open(config, encoding='utf-8') as file:
                model = json.load(file).get('model')
        except (OSError, json.JSONDecodeError):
            return None
        if isinstance(model, str) and model:
            return model
        return None

    def _transcript(self: OpencodeAgent, session: str) -> Optional[pathlib.Path]:
        """No per-session file exists; opencode persists sessions in SQLite.

        Sessions live in opencode's central ``opencode.db`` (message and
        part tables keyed by session id), so there is no growing file to
        poll -- ``transcript()`` degrades to ``exists: False``.
        """
        return None
