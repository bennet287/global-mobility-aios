"""Test doubles for the TUI suite.

Built on the app's own extension points -- ``MockTurn`` slots into the
``turn_factory`` seam wherever a test needs a deterministic chat turn
without spawning a real agent subprocess.
"""

from __future__ import annotations

import time
from collections.abc import Iterator

from fractal.tui.chat import ChatEvent

__all__ = ['MockTurn']


class MockTurn:
    """A ``ChatTurn``-shaped canned event stream."""

    def __init__(
        self: MockTurn,
        events: list[ChatEvent],
        *,
        pause: float = 0.0,
    ) -> None:
        """Initialize ``MockTurn``.

        Args:
            events: The events to replay.
            pause: Optional inter-event sleep (simulates streaming pace).

        """
        self._events = list(events)
        self._pause = pause
        self._cancelled = False

    @property
    def cancelled(self: MockTurn) -> bool:
        """Return whether ``cancel`` was called."""
        return self._cancelled

    def cancel(self: MockTurn) -> None:
        """Stop the replay."""
        self._cancelled = True

    def events(self: MockTurn) -> Iterator[ChatEvent]:
        """Replay the canned events."""
        for event in self._events:
            if self._cancelled:
                return
            if self._pause:
                time.sleep(self._pause)
            yield event
