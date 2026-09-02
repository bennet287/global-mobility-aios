"""In-process doubles for the ``fractal.core.agent`` contract tests.

``SampleParser`` speaks a scripted line protocol -- each stdout line is a
JSON object of ``StreamEvent`` fields -- so tests write agent streams as
readable frame lists while the parser honors the real state contract
(session capture, model overwrite, cost accumulation, error collection).
``SampleAgent`` is a real subclass with every mandatory hook implemented;
``TrackingAgent`` layers the sanctioned override recipe (call super, record
the event, return it) over every ``on_*`` hook. Never ``MagicMock``.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any, Optional

from fractal.core.agent import Agent, Invocation, StreamEvent, StreamParser
from fractal.core.event import Event
from fractal.core.node import Node

__all__ = [
    'SampleParser',
    'SampleAgent',
    'RoutedAgent',
    'TrackingAgent',
]


class SampleParser(StreamParser):
    """Parser for scripted JSON frames (the canned agent stream)."""

    def feed(self: SampleParser, line: str) -> list[StreamEvent]:
        """Parse one scripted frame and fold it into the stream state."""
        # tolerate blank lines like the real wire parsers
        line = line.strip()
        if not line:
            return []
        event = StreamEvent(**json.loads(line))
        # accumulate the state the driver attributes from after draining
        if event.session is not None:
            self.session = event.session
        if event.model is not None:
            self.model = event.model
            if event.model not in self.models:
                self.models.append(event.model)
        if event.cost is not None:
            self.cost = event.cost
        if event.final:
            self.final = True
        if event.budget_stopped:
            self.budget_stopped = True
        if event.kind == 'error':
            self.errors.append(event.message or 'unknown error')
        return [event]


class SampleAgent(Agent):
    """Concrete backend double with every mandatory hook implemented."""

    name = 'sample'
    config_file = 'sample.json'
    can_fork = True
    mints_session = False
    needs_pricing = False
    cost_scope = 'call'
    enforces_budget = True

    __parser__ = SampleParser

    def _invocation(
        self: SampleAgent,
        prompt: str,
        *,
        mode: str,
        session: Optional[str],
        model: Optional[str],
        effort: Optional[str],
        budget: Optional[float],
    ) -> Invocation:
        """Build a deterministic argv recording every resolved input."""
        # record every resolved input so tests can assert the builder contract
        argv = [*self.parts, mode, prompt]
        if session is not None:
            argv += ['--session', session]
        if model is not None:
            argv += ['--model', model]
        if effort is not None:
            argv += ['--effort', effort]
        if budget is not None:
            argv += ['--budget', str(budget)]
        return Invocation(
            agent=self.name,
            argv=tuple(argv),
            cwd=self.node.worktree,
            env={'SAMPLE_HOME': str(self.config_dir)},
            session=session,
        )

    def _transcript(self: SampleAgent, session: str) -> Optional[pathlib.Path]:
        """Expected transcript layout under the node's agent dir."""
        return self.config_dir / 'transcripts' / f'{session}.jsonl'

    def _transcript_fallback(
        self: SampleAgent,
        session: str,
    ) -> Optional[pathlib.Path]:
        """Last-resort discovery: glob the agent dir for the id."""
        found = sorted(self.config_dir.glob(f'*/{session}.jsonl'))
        if found:
            return found[-1]
        return None


class RoutedAgent(SampleAgent):
    """Sample backend with a provider route for the seam validations."""

    providers = ('openrouter',)


class TrackingAgent(SampleAgent):
    """Sample agent recording every fired hook via the override recipe."""

    def __init__(
        self: TrackingAgent,
        node: Node,
        command: Optional[str] = None,
    ) -> None:
        """Initialize ``TrackingAgent``."""
        super().__init__(node, command)
        self.calls: list[Event] = []

    def on_call(self: TrackingAgent, *args: Any, **kwargs: Any) -> Event:
        """Record the call event."""
        event = super().on_call(*args, **kwargs)
        self.calls.append(event)
        return event

    def on_call_success(self: TrackingAgent, *args: Any, **kwargs: Any) -> Event:
        """Record the call success event."""
        event = super().on_call_success(*args, **kwargs)
        self.calls.append(event)
        return event

    def on_call_failure(self: TrackingAgent, *args: Any, **kwargs: Any) -> Event:
        """Record the call failure event."""
        event = super().on_call_failure(*args, **kwargs)
        self.calls.append(event)
        return event

    def on_spawn(self: TrackingAgent, *args: Any, **kwargs: Any) -> Event:
        """Record the spawn event."""
        event = super().on_spawn(*args, **kwargs)
        self.calls.append(event)
        return event

    def on_action(self: TrackingAgent, *args: Any, **kwargs: Any) -> Event:
        """Record the action event."""
        event = super().on_action(*args, **kwargs)
        self.calls.append(event)
        return event

    def on_session(self: TrackingAgent, *args: Any, **kwargs: Any) -> Event:
        """Record the session event."""
        event = super().on_session(*args, **kwargs)
        self.calls.append(event)
        return event

    def on_record_session(self: TrackingAgent, *args: Any, **kwargs: Any) -> Event:
        """Record the session record event."""
        event = super().on_record_session(*args, **kwargs)
        self.calls.append(event)
        return event

    def on_record_cost(self: TrackingAgent, *args: Any, **kwargs: Any) -> Event:
        """Record the cost record event."""
        event = super().on_record_cost(*args, **kwargs)
        self.calls.append(event)
        return event

    def on_budget(self: TrackingAgent, *args: Any, **kwargs: Any) -> Event:
        """Record the budget event."""
        event = super().on_budget(*args, **kwargs)
        self.calls.append(event)
        return event

    def on_error(self: TrackingAgent, *args: Any, **kwargs: Any) -> Event:
        """Record the error event."""
        event = super().on_error(*args, **kwargs)
        self.calls.append(event)
        return event

    def on_preflight(self: TrackingAgent, *args: Any, **kwargs: Any) -> Event:
        """Record the preflight event."""
        event = super().on_preflight(*args, **kwargs)
        self.calls.append(event)
        return event
