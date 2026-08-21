"""Implements ``RadioPane`` -- the message pane.

Three sources over the scoped node's radio (modes:
``radio``/``rdrop``/``rdetail``/``rreact``): its own ``Messages``, the
cross-subtree ``Feed`` (every descendant's public/outbox posts), and the
``Archive`` of saved messages. A zone ladder (source tabs, filters, rows)
drives selection; opening a row shows the detail view with its
Reply / Chat / React / Save action bar (React drops a +1 / -1 choice). All reads come
from the snapshot; the only writes are the explicit detail actions (and the
read receipt on open) through ``TuiActions``.
"""

from __future__ import annotations

import sqlite3
import typing
from typing import Optional

from rich.table import Table
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.events import Key
from textual.widgets import OptionList, Rule as Divider, Static

import fractal.tui.fmt
import fractal.tui.theme
from fractal.tui.data import leaf_of, user_tag
from fractal.tui.widgets import PaneScroll

if typing.TYPE_CHECKING:
    from textual.widget import Widget

    from fractal.tui.app import FractalApp
    from fractal.tui.snapshot import Snapshot

__all__ = ['RadioPane']

# the source tabs, in display and cycle order (left/right steps through them)
_SOURCES = ('Messages', 'Feed', 'Archive')

# the detail action chips, in display and cycle order (left/right steps
# through them; React drops its +1 / -1 choice above its own chip)
_RD_ACTIONS = ('Reply', 'Chat', 'React', 'Save')


class RadioPane:
    """The RADIO pane: sources, filters, message rows, and the detail view."""

    def __init__(self: RadioPane, app: FractalApp) -> None:
        """Initialize ``RadioPane``.

        Args:
            app: The owning cockpit app (widget access + mode flips).

        """
        self.app = app
        self.source = 'Messages'
        self.rfocus = 'source'
        self.rfilter = 0
        self.fchannel = 'all'
        self.fshow = 'all'
        self.rsel = 0
        self.rd_action = 0
        self._rows: list[dict] = []
        self._detail_row: Optional[dict] = None
        self._read_overrides: set[str] = set()

    @property
    def want_feed(self: RadioPane) -> bool:
        """Return whether the snapshot must populate the feed section."""
        return self.source == 'Feed'

    @property
    def want_archive(self: RadioPane) -> bool:
        """Return whether the snapshot must populate the archive section."""
        return self.source == 'Archive'

    def compose(self: RadioPane) -> ComposeResult:
        """Compose the pane interior (rows mount on the first rebuild)."""
        yield Static('', id='radiosrc')
        yield Divider()
        with Vertical(id='radiolist'):
            yield Static('', id='radiofilters')
            yield Divider()
            yield Static('', id='radiocols')
            yield PaneScroll(id='radiorows')
        with PaneScroll(id='rdetail'):
            yield Static('', id='rd_text')
        with Vertical(classes='footwrap'):
            yield Divider()
            yield Static('', id='radiofoot')

    def rows(self: RadioPane, snap: Snapshot) -> list[dict]:
        """Return the visible rows for the active source + filters."""
        if self.source == 'Messages':
            rows = snap.messages
        elif self.source == 'Feed':
            rows = snap.feed
        else:
            rows = snap.saved
        result = []
        for row in rows:
            if self.fchannel != 'all' and row['channel'] != self.fchannel:
                continue
            read = self._is_read(row)
            if self.fshow == 'unread' and read:
                continue
            if self.fshow == 'read' and not read:
                continue
            result.append(row)
        return result

    def _is_read(self: RadioPane, row: dict) -> bool:
        """Return whether a row reads as read (its state or a local override)."""
        return row['read'] or row['message_uuid'] in self._read_overrides

    def _src(self: RadioPane) -> str:
        """Render the source tabs (Messages / Feed / Archive)."""
        result = []
        for source in _SOURCES:
            if source == self.source:
                if self.rfocus == 'source':
                    result.append(f'[reverse {fractal.tui.theme.PRIMARY}] {source} [/]')
                else:
                    result.append(f'[{fractal.tui.theme.PRIMARY}] {source} [/]')
            else:
                result.append(f' [{fractal.tui.theme.DIM}]{source}[/] ')
        return ' '.join(result)

    def _filters(self: RadioPane) -> str:
        """Render the channel/show filter chips.

        Each chip reserves its one-space padding in every state -- the accent
        box when focused, an invisible margin otherwise -- so moving the
        focus between the chips never shifts the row.
        """
        ch_text = f'channel: {self.fchannel} {fractal.tui.theme.CARET_OPEN}'
        sh_text = f'show: {self.fshow} {fractal.tui.theme.CARET_OPEN}'
        focus = self.rfocus == 'filter'
        channel_lit = focus and self.rfilter == 0
        show_lit = focus and self.rfilter == 1
        if channel_lit:
            channel = f'[reverse {fractal.tui.theme.PRIMARY}] {ch_text} [/]'
        else:
            channel = f' [{fractal.tui.theme.DIM}]{ch_text}[/] '
        if show_lit:
            show = f'[reverse {fractal.tui.theme.PRIMARY}] {sh_text} [/]'
        else:
            show = f' [{fractal.tui.theme.DIM}]{sh_text}[/] '
        return f'{channel}{show}'

    def _grid(self: RadioPane, left: str, right: str) -> Table:
        """Build a one-row grid: flexing left side, right-snapped timestamp.

        Subject flexes + truncates short of the timestamp; the seam gets one
        extra column so it reads even with the padded sender/channel/priority
        gaps; a one-column gap keeps the scrollbar off the time.
        """
        grid = Table.grid(expand=True)
        grid.add_column(ratio=1, no_wrap=True, overflow='ellipsis')
        grid.add_column(width=fractal.tui.theme.GAP + 1, no_wrap=True)
        grid.add_column(justify='right', no_wrap=True)
        grid.add_column(width=1, no_wrap=True)
        grid.add_row(Text.from_markup(left), Text(), Text.from_markup(right), Text(' '))
        return grid

    def _cols(self: RadioPane) -> Table:
        """Render the column header line."""
        gap = ' ' * fractal.tui.theme.GAP
        sender = fractal.tui.fmt.col('sender', fractal.tui.theme.SENDER_W)
        channel = fractal.tui.fmt.col('channel', fractal.tui.theme.CHANNEL_W)
        priority = fractal.tui.fmt.col('priority', fractal.tui.theme.PRIORITY_W)
        left = (
            f'  [{fractal.tui.theme.DIM}]{sender}{gap}{channel}{gap}{priority}'
            f'{gap}subject[/]'
        )
        return self._grid(left, f'[{fractal.tui.theme.DIM}]timestamp[/]')

    def _foot(self: RadioPane) -> str:
        """Render the foot hints for the active zone."""
        hints = {
            'source': f'{fractal.tui.theme.LEFT}{fractal.tui.theme.RIGHT} source'
            f' {fractal.tui.theme.SEP} {fractal.tui.theme.DOWN} filters'
            f' {fractal.tui.theme.SEP} esc back',
            'filter': f'{fractal.tui.theme.LEFT}{fractal.tui.theme.RIGHT} pick'
            f' {fractal.tui.theme.SEP} {fractal.tui.theme.RET} open'
            f' {fractal.tui.theme.SEP} {fractal.tui.theme.UP}{fractal.tui.theme.DOWN}'
            f' zones {fractal.tui.theme.SEP} esc back',
            'rows': f'{fractal.tui.theme.UP}{fractal.tui.theme.DOWN} select'
            f' {fractal.tui.theme.SEP} {fractal.tui.theme.RET} open'
            f' {fractal.tui.theme.SEP} esc back',
        }
        return (
            f'{fractal.tui.theme.DOT_ON} [{fractal.tui.theme.DIM}]unread'
            f' {fractal.tui.theme.SEP} {hints[self.rfocus]}[/]'
        )

    def _row_render(self: RadioPane, row: dict) -> Table:
        """Render one message row (unread dot, sender, channel, priority, subject)."""
        read = self._is_read(row)
        dot = ' ' if read else fractal.tui.theme.DOT_ON
        gap = ' ' * fractal.tui.theme.GAP
        root = self.app.data.root_branch
        name = leaf_of(row['sender']) + user_tag(row['sender'], root)
        # escape after col: the pad width is by visible length, and markup
        # escapes render as single chars, so alignment survives
        sender = fractal.tui.fmt.esc(
            fractal.tui.fmt.col(name, fractal.tui.theme.SENDER_W)
        )
        channel = fractal.tui.fmt.esc(
            fractal.tui.fmt.col(row['channel'], fractal.tui.theme.CHANNEL_W)
        )
        priority = fractal.tui.fmt.col(
            str(row['priority']), fractal.tui.theme.PRIORITY_W
        )
        subject = fractal.tui.fmt.esc(row['subject'])
        left = f'{dot} {sender}{gap}{channel}{gap}{priority}{gap}{subject}'
        stamp = fractal.tui.fmt.timestamp(row['created_at'], self.app.tz)
        return self._grid(left, f'[{fractal.tui.theme.DIM}]{stamp}[/]')

    def rebuild(self: RadioPane, snap: Snapshot) -> None:
        """Re-mount the head and rows."""
        self.rebuild_head()
        self.rebuild_rows(snap)

    def rebuild_head(self: RadioPane) -> None:
        """Update the source tabs, filters, and foot."""
        self.app.query_one('#radiosrc', Static).update(self._src())
        self.app.query_one('#radiofilters', Static).update(self._filters())
        self.app.query_one('#radiocols', Static).update(self._cols())
        self.app.query_one('#radiofoot', Static).update(self._foot())

    def rebuild_rows(self: RadioPane, snap: Snapshot) -> None:
        """Re-mount the message rows."""
        box = self.app.query_one('#radiorows', PaneScroll)
        rows = self.rows(snap)
        # the rows as mounted: while the user drives the pane the app keeps
        # landing fresh snapshots without rebuilding the rows, so the cursor
        # resolves against this list, never the live snapshot
        self._rows = rows
        self.rsel = min(self.rsel, max(0, len(rows) - 1))
        box.remount(*[Static(self._row_render(row), classes='rrow') for row in rows])
        self.app.call_after_refresh(self.paint)

    def paint(self: RadioPane) -> None:
        """Paint the selected row highlight."""
        in_rows = self.app.mode == 'radio' and self.rfocus == 'rows'
        for index, widget in enumerate(self.app.query('#radiorows .rrow')):
            selected = in_rows and index == self.rsel
            widget.set_class(selected, 'rsel')
            if selected:
                widget.scroll_visible(animate=False)

    def rescope(self: RadioPane, snap: Snapshot) -> None:
        """Reset selection and close the detail for a new scope."""
        self.rsel = 0
        self._read_overrides = set()
        self.app.query_one('#rdetail').display = False
        self.app.query_one('#radiolist').display = True
        self.rebuild(snap)

    def click_row(self: RadioPane, row: Widget) -> bool:
        """Move the row cursor to the clicked message; a re-click opens it.

        The first click lands the cursor, like arrowing there; a click on
        the already-highlighted row acts like ``enter`` (opens the detail).

        Returns:
            Whether ``row`` is a selectable message row.

        """
        rows = list(self.app.query('#radiorows .rrow'))
        if row not in rows:
            return False
        index = rows.index(row)
        if self.app.mode == 'radio' and self.rfocus == 'rows' and self.rsel == index:
            self._open_row()
            return True
        self.app.mode = 'radio'
        self.rfocus = 'rows'
        self.rsel = index
        self.rebuild_head()
        self.paint()
        return True

    def enter(self: RadioPane) -> None:
        """Enter the pane on the source tabs (or back into an open detail)."""
        # a detail left open (reply-in-progress) is where the user returns
        if self._detail_row is not None and self.app.query_one('#rdetail').display:
            self.app.mode = 'rdetail'
            self.app.query_one('#radiofoot', Static).update(self._detail_foot())
            return
        self.app.mode = 'radio'
        self.rfocus = 'source'
        self.rsel = 0
        self.rebuild_head()
        self.paint()

    def leave(self: RadioPane) -> None:
        """Return to ring mode."""
        self.app.mode = 'ring'
        self.rfocus = 'source'
        # repay any row rebuild a landing skipped while this mode drove
        self.app.refresh_stale()
        self.rebuild_head()
        self.paint()
        self.app.paint_ring()

    def key(self: RadioPane, event: Key) -> None:
        """Handle radio mode: the zone ladder and row selection."""
        key = event.key
        if self.rfocus == 'rows':
            if key == 'escape':
                self.leave()
            elif key == 'up':
                if self.rsel <= 0:
                    self._zone(-1)  # past the first row -> the filter chips
                else:
                    self.rsel -= 1
                    self.paint()
            elif key == 'down':
                self.rsel = min(len(self._rows) - 1, self.rsel + 1)
                self.paint()
            elif key == 'enter':
                self._open_row()
            else:
                return
        else:
            if key == 'escape':
                self.leave()
            elif key == 'down':
                self._zone(1)
            elif key == 'up':
                self._zone(-1)
            elif key in ('left', 'right'):
                self._zone_lr(key)
            elif key == 'enter':
                self._zone_enter()
            else:
                return
        event.stop()

    def _zone(self: RadioPane, step: int) -> None:
        """Step the zone ladder (source / filter / rows); past the top leaves."""
        zones = ['source', 'filter', 'rows']
        index = zones.index(self.rfocus) + step
        if index < 0:
            self.leave()
            return
        self.rfocus = zones[min(index, len(zones) - 1)]
        if self.rfocus == 'rows':
            # arriving in the rows lands the cursor on the first message
            self.rsel = 0
        self.rebuild_head()
        self.paint()

    def _zone_lr(self: RadioPane, key: str) -> None:
        """Handle left/right in a zone: cycle the source or pick a filter chip."""
        if self.rfocus == 'source':
            self._cycle_source(1 if key == 'right' else -1)
        elif self.rfocus == 'filter':
            self.rfilter = 1 if key == 'right' else 0
            self.rebuild_head()

    def _zone_enter(self: RadioPane) -> None:
        """Open the focused zone (the filter drop; the rows open themselves)."""
        if self.rfocus == 'filter':
            self._open_filter()

    def _cycle_source(self: RadioPane, step: int) -> None:
        """Cycle the message source and re-render."""
        index = (_SOURCES.index(self.source) + step) % len(_SOURCES)
        self.source = _SOURCES[index]
        self.rsel = 0
        # Feed/Archive are lazy snapshot sections: ask the app to re-build with
        # the new want flags before re-rendering the rows
        self.app.refresh_radio()
        self.rebuild_head()

    def _open_filter(self: RadioPane) -> None:
        """Drop the open filter's option list under its chip."""
        if self.rfilter == 0:
            options = ['all', 'inbox', 'outbox', 'public', 'private']
        else:
            options = ['all', 'unread', 'read']
        region = self.app.query_one('#radiofilters').region
        drop = OptionList(*options, id='rdrop')
        self.app.mount(drop)
        drop.styles.height = len(options) + 2
        drop.styles.width = max(len(option) for option in options) + 6
        # the show drop opens under its chip: past the channel chip's padded box
        channel_chip = f'channel: {self.fchannel} {fractal.tui.theme.CARET_OPEN}'
        offset = 0 if self.rfilter == 0 else len(channel_chip) + 2
        drop.styles.offset = (region.x + offset, region.y + 1)
        current = self.fchannel if self.rfilter == 0 else self.fshow
        if current in options:
            drop.highlighted = options.index(current)
        self.app.mode = 'rdrop'
        drop.focus()

    def key_drop(self: RadioPane, event: Key) -> None:
        """Handle the filter dropdown: esc closes (enter lands via OptionList)."""
        if event.key == 'escape':
            self._close_drop()
            event.stop()

    def _close_drop(self: RadioPane) -> None:
        """Remove the filter dropdown and return to radio mode."""
        for drop in self.app.query('#rdrop'):
            drop.remove()
        self.app.set_focus(None)
        self.app.mode = 'radio'

    def pick_filter(self: RadioPane, value: str) -> None:
        """Apply a dropdown pick (forwarded from the app's OptionList event)."""
        if self.rfilter == 0:
            self.fchannel = value
        else:
            self.fshow = value
        self.rsel = 0
        self._close_drop()
        self.rebuild_rows(self.app.snapshot)
        self.rebuild_head()

    def _open_row(self: RadioPane) -> None:
        """Open the selected row's detail, marking it read where allowed.

        Only the user's own mailbox is interactive: opening one of the root's
        messages stamps its read receipt (the override shows it until the next
        snapshot lands); any other node's mailbox is observed without
        touching -- or appearing to touch -- its state.
        """
        rows = self._rows
        if not rows:
            return
        row = rows[min(self.rsel, len(rows) - 1)]
        if row['node'] == self.app.data.root_branch:
            try:
                self.app.actions.read(message_uuid=row['message_uuid'])
            except (ValueError, PermissionError, sqlite3.Error) as error:
                self.app.notify(str(error), severity='warning')
            self._read_overrides.add(row['message_uuid'])
        self._open_detail(row)

    def _detail_text(self: RadioPane, row: dict) -> str:
        """Render the detail body: labeled rows in grouped blocks.

        Who (sender + the session that wrote it), where/when, what -- then
        the body.
        """
        stamp = fractal.tui.fmt.timestamp(row['created_at'], self.app.tz)
        sender = row['sender'] + user_tag(row['sender'], self.app.data.root_branch)
        groups = (
            (
                ('sender', sender),
                ('session', row['session'] or fractal.tui.theme.EMPTY),
            ),
            (
                ('channel', row['channel']),
                ('timestamp', stamp),
                ('uuid', row['message_uuid']),
            ),
            (('priority', row['priority']),),
        )
        blocks = [
            '\n'.join(
                f'[{fractal.tui.theme.DIM}]'
                f'{fractal.tui.fmt.col(label, fractal.tui.theme.RD_LABEL_W)}[/]'
                f'{fractal.tui.fmt.esc(str(value))}'
                for label, value in group
            )
            for group in groups
        ]
        label = fractal.tui.fmt.col('subject', fractal.tui.theme.RD_LABEL_W)
        value = fractal.tui.fmt.esc(row['subject'])
        subject = f'[{fractal.tui.theme.DIM}]{label}[/][b]{value}[/]'
        blocks[-1] = f'{blocks[-1]}\n{subject}'
        meta = '\n\n'.join(blocks)
        data = fractal.tui.fmt.esc(row['data'])
        return f'{meta}\n\n{data}'

    def _sender_session(self: RadioPane, row: dict) -> Optional[str]:
        """Look up the sender's live loop session (what Chat would fork).

        One read-only lookup on the explicit open, never on a poll path.
        """
        agent = self.app.data.config(row['sender']).get('agent') or ''
        try:
            with self.app.data.reader() as connection:
                return self.app.data.live_session(connection, row['sender'], agent)
        except (FileNotFoundError, sqlite3.Error):
            return None

    def _detail_actions(self: RadioPane) -> str:
        """Render the Reply / Chat / React / Save action chips."""
        result = []
        for index, label in enumerate(_RD_ACTIONS):
            if index == self.rd_action:
                result.append(
                    f'[{fractal.tui.theme.INK_INVERSE} on'
                    f' {fractal.tui.theme.PRIMARY}] {label} [/]'
                )
            else:
                result.append(f'[{fractal.tui.theme.CHROME}] {label} [/]')
        return '  '.join(result)

    def _detail_foot(self: RadioPane) -> str:
        """Render the detail foot (action chips + key hints)."""
        return (
            self._detail_actions()
            + f'  [{fractal.tui.theme.DIM}]{fractal.tui.theme.LEFT}'
            f'{fractal.tui.theme.RIGHT} {fractal.tui.theme.SEP}'
            f' {fractal.tui.theme.RET} select {fractal.tui.theme.SEP} esc back[/]'
        )

    def _open_detail(self: RadioPane, row: dict) -> None:
        """Swap the list for the row's detail view."""
        self.rd_action = 0
        self._detail_row = row
        self.app.query_one('#rd_text', Static).update(self._detail_text(row))
        self.app.query_one('#radiolist').display = False
        self.app.query_one('#rdetail').display = True
        self.app.query_one('#radiofoot', Static).update(self._detail_foot())
        self.app.mode = 'rdetail'

    def key_detail(self: RadioPane, event: Key) -> None:
        """Handle the detail view: the Reply / Chat / React / Save bar."""
        key = event.key
        row = self._detail_row
        if key == 'escape':
            self._close_detail()
        elif key in ('left', 'right'):
            step = 1 if key == 'right' else -1
            self.rd_action = (self.rd_action + step) % len(_RD_ACTIONS)
            self.app.query_one('#radiofoot', Static).update(self._detail_foot())
        elif key == 'enter' and row is not None:
            action = _RD_ACTIONS[self.rd_action]
            if action == 'Reply':
                # the detail stays open for reference while the reply composes
                self.app.compose_reply(row)
            elif action == 'Chat':
                session = row['session'] or self._sender_session(row)
                self._close_detail()
                self.leave()
                self.app.compose_chat(row, session=session)
            elif action == 'React':
                self._open_react()
            else:
                self._act(row, 'save')
        else:
            return
        event.stop()

    def _open_react(self: RadioPane) -> None:
        """Drop the +1 / -1 choice above the React chip."""
        options = ['+1', '-1']
        region = self.app.query_one('#radiofoot').region
        drop = OptionList(*options, id='rreact')
        self.app.mount(drop)
        drop.styles.height = len(options) + 2
        drop.styles.width = max(len(option) for option in options) + 6
        # above the foot, at the React chip (past every chip before it)
        before = _RD_ACTIONS[: _RD_ACTIONS.index('React')]
        offset = sum(len(f' {label} ') + 2 for label in before)
        drop.styles.offset = (region.x + offset, region.y - (len(options) + 2))
        drop.highlighted = 0
        self.app.mode = 'rreact'
        drop.focus()

    def key_react(self: RadioPane, event: Key) -> None:
        """Handle the react dropdown: esc closes (enter lands via OptionList)."""
        if event.key == 'escape':
            self._close_react()
            event.stop()

    def _close_react(self: RadioPane) -> None:
        """Remove the react dropdown and return to the detail."""
        for drop in self.app.query('#rreact'):
            drop.remove()
        self.app.set_focus(None)
        self.app.mode = 'rdetail'

    def pick_react(self: RadioPane, value: str) -> None:
        """Apply a react pick (forwarded from the app's OptionList event)."""
        row = self._detail_row
        self._close_react()
        if row is not None:
            self._act(row, 'react', value=1 if value == '+1' else -1)

    def _act(self: RadioPane, row: dict, action: str, *, value: int = 1) -> None:
        """React/Save through the write surface; failures notify."""
        try:
            if action == 'react':
                self.app.actions.react(
                    message_uuid=row['message_uuid'],
                    value=value,
                )
                self.app.notify(f'reacted {value:+d}')
            else:
                self.app.actions.save(message_uuid=row['message_uuid'])
                self.app.notify('saved to archive')
        except (ValueError, PermissionError, sqlite3.Error) as error:
            self.app.notify(str(error), severity='warning')
        self._close_detail()

    def _close_detail(self: RadioPane) -> None:
        """Close the detail back to the list."""
        self.app.query_one('#rdetail').display = False
        self.app.query_one('#radiolist').display = True
        self.app.mode = 'radio'
        self.rebuild_head()
        # re-mount the rows so the open's read mark shows the moment we return
        self.rebuild_rows(self.app.snapshot)
