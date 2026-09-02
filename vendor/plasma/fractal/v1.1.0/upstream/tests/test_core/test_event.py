"""Test the ``fractal.core.event`` module.

The tower is the observability vocabulary for paired operations: payload
fields are bare class annotations extracted from kwargs and deep-copied,
events shallow-copy their emitting source, and terminal events pair with
their initial event to compute a duration.
"""

from __future__ import annotations

from typing import Any, Optional

import pytest

from fractal.core.event import FailureEvent, InitialEvent, TerminalEvent

__all__ = [
    'test_event_extracts_and_isolates_payload',
    'test_event_rejects_unknown_fields',
    'test_event_snapshots_the_source',
    'test_event_name_derives_from_class_name_and_info',
    'test_event_description_folds_messages',
    'test_terminal_event_computes_duration',
    'test_failure_event_carries_the_error',
]


def test_event_extracts_and_isolates_payload() -> None:
    """Annotated payload kwargs bind as attributes, isolated by deep copy."""
    payload = {'tool': 'Read', 'args': ['a.txt']}
    event = SampleCallEvent(_Emitter(), payload=payload, session='sess_1')
    # later caller mutation must not reach into the snapshot
    payload['args'].append('b.txt')
    assert event.payload == {'tool': 'Read', 'args': ['a.txt']}
    assert event.session == 'sess_1'


def test_event_rejects_unknown_fields() -> None:
    """A kwarg matching no annotated field raises instead of vanishing."""
    with pytest.raises(TypeError, match='Unexpected event fields'):
        SampleCallEvent(_Emitter(), payload={}, sesion='typo')


def test_event_snapshots_the_source() -> None:
    """The emitting source is copied, so a later rebind never leaks in."""
    emitter = _Emitter()
    event = SampleCallEvent(emitter)
    emitter.state = 'mutated'
    assert event.source is not emitter
    assert event.source.state == 'ready'


def test_event_name_derives_from_class_name_and_info() -> None:
    """The display name is the SCREAMING_SNAKE class name plus ``(info)``."""
    plain = SampleCallEvent(_Emitter())
    assert plain.name == 'SAMPLE_CALL_EVENT'
    qualified = SampleCallEvent(_Emitter(), info='turn 2')
    assert qualified.name == 'SAMPLE_CALL_EVENT (turn 2)'


@pytest.mark.parametrize(
    argnames=('message', 'folded'),
    argvalues=[
        pytest.param(None, '', id='none'),
        pytest.param('one line', '\none line', id='string'),
        pytest.param(['first', 'second'], '\nfirst, second', id='list'),
        pytest.param(
            ['first\nline', 'second'],
            '\nfirst\nline\nsecond',
            id='multiline',
        ),
    ],
)
def test_event_description_folds_messages(
    message: Optional[str | list[str]],
    folded: str,
) -> None:
    """Description is ``{name} : {source class}`` plus the folded messages."""
    emitter = _Emitter()
    event = SampleCallEvent(emitter, message)
    assert event.description == f'SAMPLE_CALL_EVENT : _Emitter{folded}'


def test_terminal_event_computes_duration() -> None:
    """A terminal event pairs with its initial event and times the span."""
    emitter = _Emitter()
    initial = SampleCallEvent(emitter)
    # back-date the initial instant so the span is deterministic, never slept
    initial.created -= 5.0
    terminal = SampleCallSuccessEvent(emitter, initial_event=initial)
    assert 5.0 <= terminal.duration < 6.0
    assert terminal.duration == terminal.created - initial.created


def test_failure_event_carries_the_error() -> None:
    """A failure event is terminal and stores the raised error."""
    emitter = _Emitter()
    initial = SampleCallEvent(emitter)
    error = ValueError('boom')
    failure = SampleCallFailureEvent(emitter, initial_event=initial, error=error)
    assert failure.duration >= 0
    assert isinstance(failure.error, ValueError)
    assert str(failure.error) == 'boom'


# ------ sample tower


class SampleCallEvent(InitialEvent):
    """Emitted when a sample call begins."""

    payload: dict[str, Any]
    session: Optional[str]


class SampleCallSuccessEvent(TerminalEvent):
    """Emitted when a sample call succeeds."""


class SampleCallFailureEvent(FailureEvent):
    """Emitted when a sample call fails."""


class _Emitter:
    """Sample event source with mutable state."""

    def __init__(self: _Emitter) -> None:
        """Initialize ``_Emitter``."""
        self.state = 'ready'
