"""Test the ``fractal.tui.actions`` module.

Writes run against the small writable pair tree (the canonical tree stays
read-only) and are verified the way the cockpit sees them: through a fresh
snapshot build after each write.
"""

from __future__ import annotations

import pathlib

import pytest

from fractal.cli.utils import resolve_node
from fractal.tui.actions import TuiActions
from fractal.tui.data import TuiData
from fractal.tui.poller import NodePoller
from fractal.tui.snapshot import SnapshotBuilder

__all__ = [
    'test_send_reply_react_save_round_trip',
    'test_read_receipts_name_the_root',
]


@pytest.fixture
def stack(pair_tree: pathlib.Path) -> tuple[TuiData, TuiActions, SnapshotBuilder]:
    """Return a fresh write stack over the pair tree: data + actions + builder."""
    data = TuiData(resolve_node(pair_tree))
    data.refresh_worktrees()
    return data, TuiActions(data), SnapshotBuilder(data, NodePoller(data.db_dir))


def test_send_reply_react_save_round_trip(
    stack: tuple[TuiData, TuiActions, SnapshotBuilder],
) -> None:
    """A send lands unread; reply threads under it; react counts; save archives.

    The round trip runs on the target's ``public`` channel -- the one default
    channel a non-owner may both post to and read/react/save from (``inbox``
    is owner-read-only, ``outbox`` owner-write-only).
    """
    _, actions, builder = stack
    uuid = actions.send(
        target='main.alpha',
        channel='public',
        subject='task',
        data='ship the auth work',
        priority=9,
    )
    snap = builder.build('main.alpha')
    [row] = [r for r in snap.messages if r['message_uuid'] == uuid]
    assert (row['channel'], row['sender'], row['priority']) == ('public', 'main', 9)
    assert not row['read']
    # reply / react / save against the same message (resolved by global uuid)
    reply_uuid = actions.reply(
        message_uuid=uuid,
        data='on it',
        priority=9,
    )
    actions.react(message_uuid=uuid, value=1)
    actions.save(message_uuid=uuid)
    snap = builder.build('main.alpha', want_archive=True)
    [row] = [r for r in snap.messages if r['message_uuid'] == uuid]
    assert (row['pos_reacts'], row['neg_reacts']) == (1, 0)
    assert not row['read']  # the root's receipts never touch alpha's own state
    # the reply is a thread member, not a new top-level row
    assert all(r['message_uuid'] != reply_uuid for r in snap.messages)
    # the saved copy lands in the ROOT's archive, tagged with its owner
    assert [(r['message_uuid'], r['node']) for r in snap.saved] == [
        (uuid, 'main.alpha')
    ]


def test_read_receipts_name_the_root(
    stack: tuple[TuiData, TuiActions, SnapshotBuilder],
) -> None:
    """Reading lands the root's receipt; the target's own state never moves."""
    data, actions, builder = stack
    # another node's message: a `reads` receipt names the root; alpha holds no
    # receipt of its own, so its mailbox still shows the message unread
    uuid = actions.send(
        target='main.alpha',
        channel='public',
        subject='steer',
        data='look at the flaky test',
        priority=5,
    )
    actions.read(message_uuid=uuid)
    connection = data.connect()
    try:
        readers = data.rows(connection, 'SELECT node FROM reads ORDER BY read_id')
    finally:
        connection.close()
    assert [row['node'] for row in readers] == ['main']
    # the root's own message reads through the same receipt mechanism
    own = actions.send(
        target='main',
        channel='public',
        subject='note',
        data='kickoff at noon',
        priority=5,
    )
    actions.read(message_uuid=own)
    # only the owner's receipt renders the read: alpha's row shows alpha's
    # untouched state, the root's own message shows its receipt
    [row] = [
        r for r in builder.build('main.alpha').messages if r['message_uuid'] == uuid
    ]
    assert not row['read']
    [row] = [r for r in builder.build('main').messages if r['message_uuid'] == own]
    assert row['read']
