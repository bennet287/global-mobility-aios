"""Fixtures for the TUI suite: the canonical tree, the read stack, the app."""

from __future__ import annotations

import datetime as dt
import pathlib
from collections.abc import Callable
from typing import Any

import pytest

from fractal.cli.utils import resolve_node
from fractal.tui.app import FractalApp
from fractal.tui.data import TuiData
from fractal.tui.poller import NodePoller
from fractal.tui.snapshot import SnapshotBuilder

from ._tree import NOW_EPOCH, build_pair, build_tree


class _AllLive(frozenset):
    """A tmux-session set that reports every name as live.

    The suite has no real tmux, so without this the snapshot builder's
    crashed-active display reconcile would relabel every ``active`` node
    ``exited``. Crash-path tests override ``live_sessions`` on their own data.
    """

    def __contains__(self: _AllLive, _name: object) -> bool:
        """Report every name as a live session."""
        return True


@pytest.fixture(autouse=True)
def _stub_live_sessions(monkeypatch: pytest.MonkeyPatch) -> None:
    """Report every node's tmux session as live (no real tmux in the suite)."""
    monkeypatch.setattr(TuiData, 'live_sessions', lambda self: _AllLive())


@pytest.fixture(scope='session')
def cockpit_tree(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    """Return the canonical deterministic tree (READ-ONLY by convention).

    Tests that write build their own small tree instead of mutating this one.
    """
    root = tmp_path_factory.mktemp('cockpit_tree', numbered=False)
    build_tree(root)
    return root


@pytest.fixture
def pair_tree(tmp_path: pathlib.Path) -> pathlib.Path:
    """Return a minimal writable tree (root + ``main.alpha``) for mutating tests."""
    build_pair(tmp_path)
    return tmp_path


@pytest.fixture
def data(cockpit_tree: pathlib.Path) -> TuiData:
    """Return a fresh read stack over the canonical tree."""
    return TuiData(resolve_node(cockpit_tree))


@pytest.fixture
def builder(data: TuiData) -> SnapshotBuilder:
    """Return a snapshot builder with the pinned clock (live elapsed is stable)."""
    return SnapshotBuilder(data, NodePoller(data.db_dir), now=lambda: NOW_EPOCH)


@pytest.fixture
def cockpit_app(
    cockpit_tree: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Callable[..., FractalApp]:
    """Return a cockpit-app factory over the canonical tree (UTC, pinned clock)."""
    # the send-key capability probe reads the terminal env at import; pin it
    # so the compose hint (and its snapshot) is environment-independent
    monkeypatch.setattr('fractal.tui.panes.message._ENTER_SENDS', True)

    def factory(**kwargs: Any) -> FractalApp:
        kwargs.setdefault('tz', dt.UTC)
        kwargs.setdefault('now', lambda: NOW_EPOCH)
        return FractalApp(resolve_node(cockpit_tree), **kwargs)

    return factory
