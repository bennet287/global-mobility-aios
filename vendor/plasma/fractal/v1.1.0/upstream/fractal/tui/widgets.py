"""Implements the cockpit's shared widget primitives.

Pane scrolling must be independent by construction: Textual only stops a
wheel event when the scroll actually moved, so at a scroller's limit (or over
content that fits) the event bubbles up the DOM and would pan whatever
scrollable ancestor claims it -- the screen itself, once anything overflows.
``Pane`` and ``PaneScroll`` confine wheel input to the pane it is
aimed at.
"""

from __future__ import annotations

from typing import Optional

from textual.containers import Vertical, VerticalScroll
from textual.events import (
    MouseDown,
    MouseMove,
    MouseScrollDown,
    MouseScrollUp,
    MouseUp,
)
from textual.geometry import Size
from textual.widget import Widget

__all__ = [
    'Pane',
    'PaneScroll',
]


class Pane(Vertical):
    """A pane shell: wheel input inside it never reaches the screen.

    An optional ``resize`` edge makes the shell drag-resizable: a press on
    that border captures the mouse, every move drags the edge to the pointer
    (clamped between ``floor`` and half the terminal), and release lets go.
    The dragged size persists as ``user_size`` -- a session-scoped override
    the app's geometry path respects and re-clamps on terminal resizes.
    """

    def __init__(
        self: Pane,
        *,
        id: Optional[str] = None,
        classes: Optional[str] = None,
        resize: Optional[str] = None,
        floor: int = 0,
    ) -> None:
        """Initialize ``Pane``.

        Args:
            id: The DOM id (the stylesheet join key).
            classes: Space-separated CSS classes.
            resize: The draggable border edge -- ``'right'`` drags the
                width, ``'top'`` the height; ``None`` fixes the pane.
            floor: The smallest draggable total size (borders included).

        """
        super().__init__(id=id, classes=classes)
        self._resize = resize
        self._floor = floor
        self._dragging = False
        # the dragged size (total, borders included): None until the user
        # drags the edge; dragging back is the only way to change it after
        self.user_size: Optional[int] = None

    def grab_edge(self: Pane, event: MouseDown) -> None:
        """Start the edge drag (the press may come from the divide's far side).

        The near border column lands here via ``_on_mouse_down``; the far
        column (the neighbor pane's border) never reaches this widget, so
        the app forwards that press explicitly.
        """
        self._dragging = True
        self.capture_mouse()
        # the press also seeded the screen's text selection before the pane
        # saw the event; drop it or the drag smears a selection across panes
        self.screen.clear_selection()
        event.stop()

    def clamp_user_size(self: Pane, terminal: Size) -> None:
        """Re-clamp the dragged size to ``terminal`` (a shrink moves the cap)."""
        if self.user_size is not None:
            self._drag_to(self.user_size, terminal)

    def _drag_to(self: Pane, size: int, terminal: Size) -> None:
        """Apply ``size``, clamped between the floor and half the terminal.

        On a terminal too small for both bounds the floor wins -- a
        below-minimum pane is unusable, an oversized one is merely large.
        """
        if self._resize == 'right':
            self.user_size = max(self._floor, min(size, terminal.width // 2))
            self.styles.width = self.user_size
        else:
            self.user_size = max(self._floor, min(size, terminal.height // 2))
            self.styles.height = self.user_size

    async def _on_mouse_down(self: Pane, event: MouseDown) -> None:
        """Start an edge drag when a primary press lands on the resize border."""
        await super()._on_mouse_down(event)
        if self._resize is None or event.button != 1:
            return
        # the edge test uses screen coordinates: a press bubbling up from a
        # child arrives with child-relative x/y, which would alias the border
        if self._resize == 'right':
            on_edge = event.screen_x == self.region.right - 1
        else:
            on_edge = event.screen_y == self.region.y
        if not on_edge:
            return
        self.grab_edge(event)

    def _on_mouse_move(self: Pane, event: MouseMove) -> None:
        """Drag the resize edge to the pointer (the opposite edge is fixed)."""
        if not self._dragging:
            return
        if self._resize == 'right':
            self._drag_to(event.screen_x - self.region.x + 1, self.app.size)
        else:
            self._drag_to(self.region.bottom - event.screen_y, self.app.size)
        event.stop()

    async def _on_mouse_up(self: Pane, event: MouseUp) -> None:
        """End the edge drag."""
        await super()._on_mouse_up(event)
        if not self._dragging:
            return
        self._dragging = False
        self.release_mouse()
        event.stop()

    def _on_mouse_scroll_down(self: Pane, event: MouseScrollDown) -> None:
        """Stop a wheel-down event at the pane edge."""
        event.stop()

    def _on_mouse_scroll_up(self: Pane, event: MouseScrollUp) -> None:
        """Stop a wheel-up event at the pane edge."""
        event.stop()


class PaneScroll(VerticalScroll):
    """A pane-local scroller: wheel input never bubbles past it.

    Never focusable: a focused ``ScrollableContainer`` carries its own arrow
    bindings, so one stray click would make every cursor key both drive the
    mode machine and scroll whatever was clicked.
    """

    can_focus = False

    def _on_mouse_scroll_down(self: PaneScroll, event: MouseScrollDown) -> None:
        """Scroll down, then stop the event from bubbling past the pane."""
        super()._on_mouse_scroll_down(event)
        event.stop()

    def _on_mouse_scroll_up(self: PaneScroll, event: MouseScrollUp) -> None:
        """Scroll up, then stop the event from bubbling past the pane."""
        super()._on_mouse_scroll_up(event)
        event.stop()

    def remount(self: PaneScroll, *widgets: Widget) -> None:
        """Replace the children, preserving the scroll position.

        A poll-driven rebuild must not move the user's scrollbar: a plain
        ``remove_children`` + ``mount`` resets the scroll to the top, so every
        off-pane refresh would yank positions across the cockpit. The restore
        lands after the next refresh (the new layout must settle first) and
        clamps to the new content height.
        """
        y = self.scroll_y
        self.remove_children()
        self.mount(*widgets)
        self.call_after_refresh(lambda: self.scroll_to(y=y, animate=False))
