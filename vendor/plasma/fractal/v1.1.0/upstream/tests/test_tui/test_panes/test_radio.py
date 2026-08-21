"""Test the ``fractal.tui.panes.radio`` module.

The pane is driven through a real ``Pilot``. Navigation (the zone ladder,
source cycling, the filter drop, the detail view) runs on the canonical
tree's rich radio traffic. The write actions (react / save / read receipt)
and the Chat hand-off run on the writable pair tree, where a real ``Radio``
send seeds a message the pane then acts on.
"""

from __future__ import annotations

import pathlib
from collections.abc import Callable

from rich.text import Text
from textual.widgets import OptionList, Static

from fractal.cli.utils import resolve_node
from fractal.core.radio import Radio
from fractal.tui.app import FractalApp
from fractal.tui.data import TuiData

__all__ = [
    'test_zone_ladder_walks_source_filter_rows',
    'test_source_cycles_through_feed_and_archive',
    'test_show_filter_applies_to_feed_rows',
    'test_filter_dropdown_narrows_the_channel',
    'test_filter_dropdown_escape_closes_without_applying',
    'test_filter_chips_hold_their_width_across_focus',
    'test_open_row_shows_the_detail_and_action_bar_cycles',
    'test_empty_rows_open_is_a_no_op',
    'test_detail_react_and_save_write_through',
    'test_opening_the_roots_own_message_marks_it_read',
    'test_enter_opens_the_highlighted_row_after_a_snapshot_lands',
    'test_detail_chat_hands_off_to_the_composer',
    'test_hostile_message_markup_renders_literally',
]


# ------ navigation on the canonical tree


async def test_zone_ladder_walks_source_filter_rows(
    cockpit_app: Callable[..., FractalApp],
) -> None:
    """Down steps source -> filter -> the first row; up climbs back and leaves."""
    app = cockpit_app(branch='main.alpha')
    async with app.run_test(size=(150, 48)) as pilot:
        pane = app.radio_pane
        await pilot.press('right', 'enter')  # ring -> radio, into the source tabs
        assert (app.mode, pane.rfocus) == ('radio', 'source')
        await pilot.press('down')  # -> filter
        assert pane.rfocus == 'filter'
        await pilot.press('down')  # -> the rows, cursor on the first message
        assert (pane.rfocus, pane.rsel) == ('rows', 0)
        await pilot.press('down')  # the cursor moves; the zone stays put
        assert (pane.rfocus, pane.rsel) == ('rows', 1)
        await pilot.press('up', 'up')  # past the first row -> the filter chips
        assert pane.rfocus == 'filter'
        await pilot.press('up')  # -> source
        assert pane.rfocus == 'source'
        await pilot.press('up')  # up above the source leaves to the ring
        assert app.mode == 'ring'


async def test_source_cycles_through_feed_and_archive(
    cockpit_app: Callable[..., FractalApp],
) -> None:
    """Left/right on the source tabs cycle Messages/Feed/Archive, re-filling rows."""
    app = cockpit_app(branch='main.alpha')
    async with app.run_test(size=(150, 48)) as pilot:
        pane = app.radio_pane
        await pilot.press('right', 'enter')  # into the source tabs
        assert pane.source == 'Messages'
        await pilot.press('right')  # -> Feed (cross-subtree public/outbox posts)
        assert pane.source == 'Feed'
        assert pane.want_feed
        feed = pane.rows(app.snapshot)
        assert feed  # the subtree has public/outbox posts to surface
        assert all(row['channel'] in ('public', 'outbox') for row in feed)
        await pilot.press('right')  # -> Archive (the root's saved messages)
        assert pane.source == 'Archive'
        assert pane.want_archive
        saved = pane.rows(app.snapshot)
        assert [row['subject'] for row in saved] == ['status']
        await pilot.press('left', 'left')  # back to Messages
        assert pane.source == 'Messages'


async def test_show_filter_applies_to_feed_rows(
    cockpit_app: Callable[..., FractalApp],
) -> None:
    """The read/unread ``show`` filter narrows Feed rows, not just Messages.

    Feed rows carry the owning node's read state (the unread dot renders from
    it), and the show chip is operable on every source -- so picking it must
    honor the filter on Feed the way it does on Messages.
    """
    app = cockpit_app(branch='main.alpha')
    async with app.run_test(size=(150, 48)) as pilot:
        pane = app.radio_pane
        await pilot.press('right', 'enter', 'right')  # source tabs -> Feed
        assert pane.source == 'Feed'
        feed = pane.rows(app.snapshot)
        assert feed  # the subtree has feed posts to filter
        # mark one post read via the local override, then partition by show
        marked = feed[0]['message_uuid']
        pane._read_overrides.add(marked)
        pane.fshow = 'unread'
        assert marked not in {row['message_uuid'] for row in pane.rows(app.snapshot)}
        pane.fshow = 'read'
        assert marked in {row['message_uuid'] for row in pane.rows(app.snapshot)}


async def test_filter_dropdown_narrows_the_channel(
    cockpit_app: Callable[..., FractalApp],
) -> None:
    """The channel filter drop applies a pick that narrows the visible rows."""
    app = cockpit_app(branch='main.alpha')
    async with app.run_test(size=(150, 48)) as pilot:
        pane = app.radio_pane
        await pilot.press('right', 'enter', 'down')  # radio -> filter zone
        assert pane.rfocus == 'filter'
        await pilot.press('enter')  # drop the channel filter
        assert app.mode == 'rdrop'
        drop = app.query_one('#rdrop', OptionList)
        # pick 'inbox' (the steer + note live there)
        drop.highlighted = ['all', 'inbox', 'outbox', 'public', 'private'].index(
            'inbox'
        )
        await pilot.press('enter')
        assert app.mode == 'radio'
        assert pane.fchannel == 'inbox'
        assert {row['channel'] for row in pane.rows(app.snapshot)} == {'inbox'}


async def test_filter_dropdown_escape_closes_without_applying(
    cockpit_app: Callable[..., FractalApp],
) -> None:
    """Esc out of the filter drop closes it and leaves the filter unchanged."""
    app = cockpit_app(branch='main.alpha')
    async with app.run_test(size=(150, 48)) as pilot:
        pane = app.radio_pane
        await pilot.press('right', 'enter', 'down', 'enter')  # open the drop
        assert app.mode == 'rdrop'
        await pilot.press('escape')
        assert app.mode == 'radio'
        assert not app.query('#rdrop')
        assert pane.fchannel == 'all'  # nothing applied


async def test_filter_chips_hold_their_width_across_focus(
    cockpit_app: Callable[..., FractalApp],
) -> None:
    """The focused chip's box replaces its margin -- the row never shifts."""
    app = cockpit_app(branch='main.alpha')
    async with app.run_test(size=(150, 48)) as pilot:
        pane = app.radio_pane
        rest = Text.from_markup(pane._filters()).plain
        await pilot.press('right', 'enter', 'down')  # into the filter zone
        assert pane.rfocus == 'filter'
        focused = Text.from_markup(pane._filters()).plain
        assert len(focused) == len(rest)
        await pilot.press('right')  # channel chip -> show chip
        shifted = Text.from_markup(pane._filters()).plain
        assert len(shifted) == len(rest)


async def test_open_row_shows_the_detail_and_action_bar_cycles(
    cockpit_app: Callable[..., FractalApp],
) -> None:
    """Enter on a row opens the detail; left/right cycle Reply/Chat/React/Save."""
    app = cockpit_app(branch='main.alpha')
    async with app.run_test(size=(150, 48)) as pilot:
        pane = app.radio_pane
        await pilot.press('right', 'enter', 'down', 'down')  # into the rows
        assert pane.rfocus == 'rows'
        await pilot.press('enter')  # open the selected row
        assert app.mode == 'rdetail'
        assert app.query_one('#rdetail').display
        assert not app.query_one('#radiolist').display
        # the detail body shows the message's subject and sender
        text = str(app.query_one('#rd_text', Static).render())
        assert pane._detail_row['subject'] in text
        # the action bar cycles right (0..3) and wraps
        assert pane.rd_action == 0
        await pilot.press('right')
        assert pane.rd_action == 1
        await pilot.press('left', 'left')  # wrap past 0 -> 3
        assert pane.rd_action == 3
        await pilot.press('escape')  # close back to the list
        assert app.mode == 'radio'
        assert app.query_one('#radiolist').display


async def test_empty_rows_open_is_a_no_op(
    cockpit_app: Callable[..., FractalApp],
) -> None:
    """Entering rows with an empty list and pressing enter opens nothing safely."""
    app = cockpit_app(branch='main.alpha')
    async with app.run_test(size=(150, 48)) as pilot:
        pane = app.radio_pane
        # filter to a channel with no messages, then dive into the (empty) rows
        await pilot.press('right', 'enter', 'down', 'enter')  # drop the channel filter
        drop = app.query_one('#rdrop', OptionList)
        drop.highlighted = ['all', 'inbox', 'outbox', 'public', 'private'].index(
            'private'
        )
        await pilot.press('enter')  # apply: alpha has no private messages
        await pilot.press('down')
        assert pane.rfocus == 'rows'
        assert pane.rows(app.snapshot) == []
        await pilot.press('enter')  # no row to open
        assert app.mode == 'radio'  # stayed on the rows, no detail


# ------ write actions on the pair tree


async def test_detail_react_and_save_write_through(pair_tree: pathlib.Path) -> None:
    """React drops a +1 / -1 choice; picks and Save land real rows.

    Reacting -1 after +1 re-reacts: the value changes rather than stacking.
    """
    root = resolve_node(pair_tree)
    uuid, _, _ = Radio(root).send(
        node='main.alpha',
        channel='public',
        subject='please review',
        data='the diff is up',
        priority=6,
    )
    app = FractalApp(root, branch='main.alpha')
    async with app.run_test(size=(150, 48)) as pilot:
        await pilot.press('right', 'enter', 'down', 'down')  # into the rows
        await pilot.press('enter')  # open the detail
        assert app.mode == 'rdetail'
        await pilot.press('right', 'right')  # Reply -> Chat -> React
        await pilot.press('enter')  # open the +1 / -1 choice
        assert app.mode == 'rreact'
        await pilot.pause()
        # the choice floats on the overlay just above the action bar --
        # never in the base flow, where it would push the layout up
        drop = app.query_one('#rreact')
        foot = app.query_one('#radiofoot')
        assert drop.region.y == foot.region.y - drop.region.height
        await pilot.press('escape')  # esc returns to the detail
        assert app.mode == 'rdetail'
        await pilot.press('enter')  # re-open the choice
        await pilot.press('enter')  # pick +1
        await pilot.pause()
        assert app.mode == 'radio'  # the action closed the detail (back on rows)
        # re-open the same row and react -1 (a re-react changes the value)
        await pilot.press('enter')  # open the detail again
        assert app.mode == 'rdetail'
        await pilot.press('right', 'right')  # Reply -> Chat -> React
        await pilot.press('enter')  # open the choice
        await pilot.press('down', 'enter')  # pick -1
        await pilot.pause()
        assert app.mode == 'radio'
        # re-open the same row and Save it (the action bar resets to Reply)
        await pilot.press('enter')  # open the detail again
        assert app.mode == 'rdetail'
        await pilot.press('right', 'right', 'right')  # Reply -> Chat -> React -> Save
        await pilot.press('enter')  # Save to the archive
        await pilot.pause()
    data = TuiData(root)
    data.refresh_worktrees()
    connection = data.connect()
    try:
        reacts = data.rows(
            connection=connection,
            query='SELECT value FROM reacts r JOIN messages m'
            ' ON r.message_id = m.message_id WHERE m.message_uuid = ?',
            params=(uuid,),
        )
        archived = data.rows(
            connection=connection,
            query='SELECT node, owner FROM archive WHERE message_uuid = ?',
            params=(uuid,),
        )
    finally:
        connection.close()
    assert [row['value'] for row in reacts] == [-1]
    # the root saved it (node) and the row is tagged with its source host (owner)
    assert [(row['node'], row['owner']) for row in archived] == [('main', 'main.alpha')]


async def test_opening_the_roots_own_message_marks_it_read(
    pair_tree: pathlib.Path,
) -> None:
    """Opening one of the root's own messages stamps its read receipt."""
    root = resolve_node(pair_tree)
    uuid, _, _ = Radio(root).send(
        node='main',
        channel='public',
        subject='note to self',
        data='remember the milestone',
        priority=5,
    )
    app = FractalApp(root, branch='main')
    async with app.run_test(size=(150, 48)) as pilot:
        await pilot.press('right', 'enter', 'down', 'down')  # into the rows
        await pilot.press('enter')  # open -> stamps the read receipt
        await pilot.pause()
        assert app.mode == 'rdetail'
    data = TuiData(root)
    data.refresh_worktrees()
    connection = data.connect()
    try:
        readers = data.rows(
            connection=connection,
            query='SELECT r.node FROM reads r JOIN messages m'
            ' ON r.message_id = m.message_id WHERE m.message_uuid = ?',
            params=(uuid,),
        )
    finally:
        connection.close()
    assert [row['node'] for row in readers] == ['main']


async def test_enter_opens_the_highlighted_row_after_a_snapshot_lands(
    pair_tree: pathlib.Path,
) -> None:
    """A snapshot landing under the cursor never redirects the open.

    While the user drives the rows the app keeps landing fresh snapshots
    without rebuilding them (never yank rows out from under a cursor). A new
    arrival sorts in above the highlight (newest first), so resolving the
    cursor against the fresh snapshot would open -- and read-stamp -- the
    row above the one on screen.
    """
    root = resolve_node(pair_tree)
    highlighted, _, _ = Radio(root).send(
        node='main',
        channel='public',
        subject='the one on screen',
        data='the row under the cursor',
        priority=5,
    )
    app = FractalApp(root, branch='main')
    async with app.run_test(size=(150, 48)) as pilot:
        await pilot.press('right', 'enter', 'down', 'down')  # into the rows
        assert (app.radio_pane.rfocus, app.radio_pane.rsel) == ('rows', 0)
        # a new message arrives mid-browse and its snapshot lands off-thread
        before = app.snapshot
        Radio(root).send(
            node='main',
            channel='public',
            subject='the new arrival',
            data='shifts every row down one',
            priority=5,
        )
        app._tick()
        for _ in range(100):
            await pilot.pause(0.05)
            if app.snapshot is not before:
                break
        assert [row['subject'] for row in app.snapshot.messages] == [
            'the new arrival',
            'the one on screen',
        ]
        await pilot.press('enter')  # open: the highlight still shows the first send
        await pilot.pause()
        assert app.mode == 'rdetail'
        assert app.radio_pane._detail_row['message_uuid'] == highlighted
    data = TuiData(root)
    data.refresh_worktrees()
    connection = data.connect()
    try:
        readers = data.rows(
            connection=connection,
            query='SELECT m.message_uuid FROM reads r JOIN messages m'
            ' ON r.message_id = m.message_id WHERE r.node = ?',
            params=('main',),
        )
    finally:
        connection.close()
    # the receipt stamped the opened row -- and only it
    assert [row['message_uuid'] for row in readers] == [highlighted]


async def test_detail_chat_hands_off_to_the_composer(pair_tree: pathlib.Path) -> None:
    """The Chat action closes the detail and lands in the chat composer."""
    root = resolve_node(pair_tree)
    Radio(root).send(
        node='main.alpha',
        channel='public',
        subject='ping',
        data='got a sec?',
        priority=5,
    )
    app = FractalApp(root, branch='main.alpha')
    async with app.run_test(size=(150, 48)) as pilot:
        await pilot.press('right', 'enter', 'down', 'down')  # into the rows
        await pilot.press('enter')  # open the detail
        await pilot.press('right')  # Reply -> Chat
        await pilot.press('enter')  # Chat: closes detail, opens the composer
        await pilot.pause()
        assert (app.mode, app.focus_id) == ('edit', 'message')
        assert app.message_pane.kind == 'chat'


async def test_hostile_message_markup_renders_literally(
    pair_tree: pathlib.Path,
) -> None:
    """An agent-authored subject/body carrying markup never renders as markup.

    A subject or body containing ``[/]`` would raise ``MarkupError`` and
    crash the radio list and detail render; ``[link=...]`` would inject a
    terminal escape sequence into the operator's cockpit. The pane escapes
    both fields, so the row and detail open cleanly and show them verbatim.
    """
    root = resolve_node(pair_tree)
    subject = 'review [/] now'
    body = 'open [link=file:///etc/passwd]this[/link] please'
    Radio(root).send(
        node='main.alpha',
        channel='public',
        subject=subject,
        data=body,
        priority=6,
    )
    app = FractalApp(root, branch='main.alpha')
    async with app.run_test(size=(150, 48)) as pilot:
        await pilot.press('right', 'enter', 'down', 'down')  # into the rows
        pane = app.radio_pane
        row = next(r for r in pane.rows(app.snapshot) if r['subject'] == subject)
        # building the list row runs Text.from_markup over the composed left
        # string -- an unescaped subject would raise MarkupError here
        pane._row_render(row)
        await pilot.press('enter')  # open the detail
        await pilot.pause()
        assert app.mode == 'rdetail'  # opened without crashing
        # the detail shows both fields verbatim; the literal [link=...] text
        # surviving into .plain proves it was not parsed as a real link
        detail = Text.from_markup(pane._detail_text(row))
        assert subject in detail.plain
        assert body in detail.plain
