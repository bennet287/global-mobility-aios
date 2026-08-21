"""Implements ``TreePane`` -- the whole-tree pane (mode: ``tree``).

A box-drawing view of every live node with its status dot, foldable per
branch; ``enter`` on a row re-scopes the whole cockpit to that node (the
headline interaction).
"""

from __future__ import annotations

import typing
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.events import Enter, Key, Leave, Resize
from textual.widgets import Rule as Divider, Static

import fractal.tui.fmt
import fractal.tui.theme
from fractal.tui.widgets import PaneScroll

if typing.TYPE_CHECKING:
    from textual.widget import Widget

    from fractal.tui.app import FractalApp
    from fractal.tui.snapshot import Snapshot

__all__ = [
    'TreeRow',
    'TreePane',
]


class TreeRow(Horizontal):
    """One tree row: a fixed glyph head beside a truncating label.

    The stylesheet keeps resting labels on one ellipsis-truncated line
    however narrow the pane; the hovered row (and only it) carries
    ``expanded``, which lets the label wrap -- hanging under its own start
    column, past the tree glyphs. The keyboard selection (``tsel``) shares
    the unfold rule, so terminals without any-motion mouse reporting still
    reach the full text. ``Enter``/``Leave`` bubble from the children, so
    the row container owns the hover class. On resize the head refills to
    the row's height with its hang line, so the tree's vertical glyphs run
    unbroken through the wrap (at rest the stylesheet crops the head back
    to one line).
    """

    def __init__(
        self: TreeRow,
        head: str,
        hang: str,
        label: str,
        *,
        classes: str,
    ) -> None:
        """Initialize the row from its head, hang, and label markup."""
        super().__init__(classes=classes)
        self._head = head
        self._hang = hang
        self._label = label
        # the head's current line count (compose seeds one; resizes refill)
        self._lines = 1

    def compose(self: TreeRow) -> ComposeResult:
        """Lay the fixed glyph head beside the wrapping label."""
        yield Static(self._head, classes='tprefix')
        yield Static(self._label, classes='tlabel')

    def set_lines(self: TreeRow, head: str, hang: str, label: str) -> None:
        """Swap the row's markup in place (the remount-free rebuild path)."""
        self._head = head
        self._hang = hang
        self._label = label
        lines = [head] + [hang] * (self._lines - 1)
        self.query_one('.tprefix', Static).update('\n'.join(lines))
        self.query_one('.tlabel', Static).update(label)

    def on_resize(self: TreeRow, event: Resize) -> None:
        """Refill the glyph head to the row's height, hang lines below."""
        if event.size.height == self._lines:
            return
        self._lines = event.size.height
        lines = [self._head] + [self._hang] * (event.size.height - 1)
        self.query_one('.tprefix', Static).update('\n'.join(lines))

    def on_enter(self: TreeRow, event: Enter) -> None:
        """Unfold the hovered row."""
        self.set_class(True, 'expanded')

    def on_leave(self: TreeRow, event: Leave) -> None:
        """Fold the row back when the pointer leaves."""
        self.set_class(False, 'expanded')


class TreePane:
    """The TREE pane: fold, select, and re-scope over the node tree."""

    def __init__(self: TreePane, app: FractalApp) -> None:
        """Initialize ``TreePane``.

        Args:
            app: The owning cockpit app (widget access + mode flips).

        """
        self.app = app
        self.sel = 0
        self.collapsed: set[str] = set()
        self._branches: list[str] = []
        self._kids: dict[str, bool] = {}
        self._last: Optional[list] = None

    def compose(self: TreePane) -> ComposeResult:
        """Compose the pane interior (rows mount on the first rebuild)."""
        yield PaneScroll(id='treebody')
        with Vertical(classes='footwrap'):
            yield Divider()
            yield Static('', id='treefoot')

    def _foot(self: TreePane) -> str:
        """Render the foot: tree-mode key hints, else the running-node tally."""
        if self.app.mode == 'tree':
            return (
                f'[{fractal.tui.theme.DIM}]{fractal.tui.theme.UP}'
                f'{fractal.tui.theme.DOWN} select {fractal.tui.theme.SEP}'
                f' {fractal.tui.theme.RET} re-scope {fractal.tui.theme.SEP}'
                f' {fractal.tui.theme.LEFT}{fractal.tui.theme.RIGHT} fold'
                f' {fractal.tui.theme.SEP} esc back[/]'
            )
        total, running = self.app.snapshot.counts
        return f'[{fractal.tui.theme.DIM}]{running}/{total} nodes running[/]'

    def rebuild(self: TreePane, snap: Snapshot) -> None:
        """Re-render the tree when its lines changed (in place when it can)."""
        lines = fractal.tui.fmt.tree_lines(list(snap.tree), self.collapsed)
        if lines == self._last:
            return
        self._last = lines
        self._branches = [branch for branch, _, _, _ in lines]
        self._kids = {row['branch']: row['has_kids'] for row in snap.tree}
        box = self.app.query_one('#treebody', PaneScroll)
        rows = list(box.query(TreeRow))
        if len(rows) == len(lines):
            # same shape (a re-scope's bold move, a status flip): swap the
            # markup in place -- a remount empties the pane for a frame
            for row, (_, head, hang, label) in zip(rows, lines):
                row.set_lines(head, hang, label)
        else:
            box.remount(
                *[
                    TreeRow(head, hang, label, classes='trow treenode')
                    for _, head, hang, label in lines
                ]
            )
        self.app.query_one('#treefoot', Static).update(self._foot())
        self.sel = min(self.sel, max(0, len(lines) - 1))
        self.app.call_after_refresh(self.paint)

    def paint(self: TreePane) -> None:
        """Paint the selection highlight (mode-gated) and the mode-aware foot."""
        for index, widget in enumerate(self.app.query('#treebody .treenode')):
            selected = self.app.mode == 'tree' and index == self.sel
            widget.set_class(selected, 'tsel')
            if selected:
                widget.scroll_visible(animate=False)
        self.app.query_one('#treefoot', Static).update(self._foot())

    def rescope(self: TreePane, snap: Snapshot) -> None:
        """Re-render after a scope change (the focused name re-bolds)."""
        self._last = None
        self.rebuild(snap)

    def click_row(self: TreePane, row: Widget) -> bool:
        """Move the selection cursor to the clicked row; a re-click activates.

        The first click lands the cursor, like arrowing there; a click on the
        already-highlighted row acts like ``enter`` (re-scope, or fold when already
        scoped).

        Returns:
            Whether ``row`` is a selectable tree row.

        """
        rows = list(self.app.query('#treebody .treenode'))
        if row not in rows:
            return False
        index = rows.index(row)
        if self.app.mode == 'tree' and self.sel == index:
            self._activate()
            return True
        self.app.mode = 'tree'
        self.sel = index
        self.paint()
        return True

    def enter(self: TreePane) -> None:
        """Enter the pane: select the scoped node and start tree mode."""
        self.app.mode = 'tree'
        if self.app.scope in self._branches:
            self.sel = self._branches.index(self.app.scope)
        self.paint()

    def leave(self: TreePane) -> None:
        """Return to ring mode."""
        self.app.mode = 'ring'
        self.paint()
        self.app.paint_ring()

    def key(self: TreePane, event: Key) -> None:
        """Handle tree mode: up/down move, right/left fold, enter re-scope/fold, esc."""
        key = event.key
        branches = self._branches
        sel = branches[self.sel] if 0 <= self.sel < len(branches) else None
        kids = bool(sel and self._kids.get(sel))
        if key == 'escape':
            self.leave()
        elif key == 'up':
            self.sel = max(0, self.sel - 1)
            self.paint()
        elif key == 'down':
            self.sel = min(len(branches) - 1, self.sel + 1)
            self.paint()
        elif key == 'right' and kids:
            self.collapsed.discard(sel)
            self._last = None
            self.rebuild(self.app.snapshot)
        elif key == 'left' and kids:
            self.collapsed.add(sel)
            self._last = None
            self.rebuild(self.app.snapshot)
        elif key == 'enter' and sel:
            self._activate()
        else:
            return
        event.stop()

    def _activate(self: TreePane) -> None:
        """Activate the selected branch: re-scope, or fold when already scoped."""
        branches = self._branches
        sel = branches[self.sel] if 0 <= self.sel < len(branches) else None
        if sel is None:
            return
        if sel == self.app.scope and self._kids.get(sel):
            # enter on the already-focused branch folds/unfolds its subtree
            self.collapsed.symmetric_difference_update({sel})
            self._last = None
            self.rebuild(self.app.snapshot)
        else:
            self.app.scope_to(sel)
            if sel in self._branches:
                self.sel = self._branches.index(sel)
            self.paint()
