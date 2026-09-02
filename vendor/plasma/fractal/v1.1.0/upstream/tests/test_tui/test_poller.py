"""Test the ``fractal.tui.poller`` module.

Both halves of the perf contract: the poller reports a branch exactly when its
on-disk token moved, and the builder hands back the identical ``Snapshot``
object until then -- so a steady tick renders nothing.
"""

from __future__ import annotations

import pathlib

from fractal.cli.utils import resolve_node
from fractal.core.node import Node
from fractal.core.radio import Radio
from fractal.tui.data import TuiData
from fractal.tui.poller import NodePoller
from fractal.tui.snapshot import SnapshotBuilder

__all__ = [
    'test_poller_fires_on_change_only',
    'test_builder_reuses_snapshot_until_disk_changes',
]


def test_poller_fires_on_change_only(pair_tree: pathlib.Path) -> None:
    """The poller reports first sight, real movement, and vanishing -- only."""
    data = TuiData(resolve_node(pair_tree))
    data.refresh_worktrees()
    dirs = {branch: data.node_dir(branch) for branch in ('main', 'main.alpha')}
    poller = NodePoller(data.db_dir)
    # first call reports every watched branch; a steady tree is then silent
    assert poller.changed(dirs) == frozenset(dirs)
    assert poller.changed(dirs) == frozenset()
    # a lifecycle transition touches .status -- only that branch reports
    (dirs['main.alpha'] / '.status').write_text('active\n', encoding='utf-8')
    assert poller.changed(dirs) == frozenset({'main.alpha'})
    assert poller.changed(dirs) == frozenset()
    # a config retune touches only config.json -- only that branch reports
    Node(pair_tree / '.worktrees' / 'main.alpha').config.set('max_cost', 50)
    assert poller.changed(dirs) == frozenset({'main.alpha'})
    assert poller.changed(dirs) == frozenset()
    # a database write touches the central WAL -- every watched branch reports
    Radio(data.root).send(
        node='main.alpha',
        channel='inbox',
        subject='s',
        data='d',
        priority=5,
    )
    assert poller.changed(dirs) == frozenset(dirs)
    # a branch dropped from the watch list is reported once (sections must drop)
    assert poller.changed({'main': dirs['main']}) == frozenset({'main.alpha'})


def test_builder_reuses_snapshot_until_disk_changes(
    pair_tree: pathlib.Path,
) -> None:
    """An idle build returns the same object; a write produces a fresh one."""
    data = TuiData(resolve_node(pair_tree))
    builder = SnapshotBuilder(data, NodePoller(data.db_dir))
    first = builder.build('main.alpha')
    assert builder.build('main.alpha') is first
    Radio(data.root).send(
        node='main.alpha',
        channel='inbox',
        subject='ping',
        data='!',
        priority=5,
    )
    second = builder.build('main.alpha')
    assert second is not first
    assert [row['subject'] for row in second.messages] == ['ping']
    # a config retune on a quiet tree rebuilds too -- the new cap shows
    Node(pair_tree / '.worktrees' / 'main.alpha').config.set('max_cost', 50)
    third = builder.build('main.alpha')
    assert third is not second
    assert third.config['max_cost'] == 50
