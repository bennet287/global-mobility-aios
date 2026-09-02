"""Implements ``NodePoller`` -- the cockpit's change-detection signal.

The central database runs in WAL mode, so every write anywhere in the tree
touches its ``.db-wal`` sidecar (or ``.db`` itself on a checkpoint truncate);
lifecycle transitions touch each node's ``.status``, and a config retune
touches only its ``config.json``. Stat-polling those few mtimes detects
change across a whole tree for ~1ms without opening a single database.
"""

from __future__ import annotations

import pathlib
from collections.abc import Mapping
from typing import Optional

from fractal.constants import CONFIG_FILE, DB_FILE, STATUS_FILE

__all__ = ['NodePoller']


class NodePoller:
    """Mtime tokens over the central database + per-branch node files.

    A branch's token pairs its ``.status`` and ``config.json`` mtimes -- a
    config retune writes only ``config.json`` (no database row, no status
    transition), so watching the file itself is the only way to see it.
    """

    def __init__(self: NodePoller, db_dir: pathlib.Path) -> None:
        """Initialize ``NodePoller``.

        Args:
            db_dir: The root node's data directory (holds the central ``.db``).

        """
        self._db_dir = db_dir
        self._db: Optional[tuple] = None
        self._nodes: dict[str, tuple] = {}

    def changed(
        self: NodePoller,
        dirs: Mapping[str, pathlib.Path],
    ) -> frozenset[str]:
        """Return the branches whose on-disk token moved since the last call.

        The first call reports every watched branch. A branch that vanished
        from ``dirs`` is also reported (its sections must drop). A central
        database write reports **every** watched branch -- attributing it
        per-branch would itself need reads, and the builder's section caches
        make the broad re-read cheap.

        Args:
            dirs: The watched branches mapped to their node data directories.

        Returns:
            Branches that changed.

        """
        db = (
            _mtime(self._db_dir / DB_FILE),
            _mtime(self._db_dir / f'{DB_FILE}-wal'),
        )
        nodes = {
            branch: (
                _mtime(node_dir / STATUS_FILE),
                _mtime(node_dir / CONFIG_FILE),
            )
            for branch, node_dir in dirs.items()
        }
        if db != self._db:
            moved = set(nodes)
        else:
            moved = {
                branch
                for branch, token in nodes.items()
                if self._nodes.get(branch) != token
            }
        moved |= set(self._nodes) - set(nodes)
        self._db = db
        self._nodes = nodes
        return frozenset(moved)


# ------ helper functions


def _mtime(path: pathlib.Path) -> Optional[float]:
    """Return a file's mtime, or ``None`` when it does not exist."""
    try:
        return path.stat().st_mtime
    except OSError:
        return None
