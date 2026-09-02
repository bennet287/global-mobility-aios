"""Test the ``fractal.util.tmux`` module.

The probe is exercised against a faked ``subprocess.run`` -- tmux is an
external boundary, and the contract under test is exactly how its absence
and failure modes fold into the returned set: only an answer from tmux
(names, or the definitive ``no server running``) is conclusive.
"""

from __future__ import annotations

import subprocess
from typing import Any, Optional

import pytest

import fractal.util.tmux

__all__ = [
    'test_probe_parses_live_session_names',
    'test_probe_distinguishes_definitive_empty_from_failure',
    'test_sessions_folds_inconclusive_probe_into_empty',
]


def test_probe_parses_live_session_names(monkeypatch: pytest.MonkeyPatch) -> None:
    """``probe`` returns the newline-separated names as a set."""

    def _list_sessions(*_args: Any, **_kwargs: Any) -> subprocess.CompletedProcess:
        return subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout='repo (main)\nrepo (main-kid)\n',
            stderr='',
        )

    monkeypatch.setattr('fractal.util.tmux.subprocess.run', _list_sessions)
    result = fractal.util.tmux.probe()
    assert result == frozenset({'repo (main)', 'repo (main-kid)'})


@pytest.mark.parametrize(
    argnames=('returncode', 'stderr', 'expected'),
    argvalues=[
        # 'no server running' is tmux answering: definitively no sessions
        (1, 'no server running on /tmp/tmux-501/default', frozenset()),
        # a socket path that does not exist means no server ever started there
        (
            1,
            'error connecting to /tmp/tmux-501/default (No such file or directory)',
            frozenset(),
        ),
        # any other error leaves liveness unknown
        (1, 'error connecting to /tmp/tmux-501/default (Permission denied)', None),
    ],
)
def test_probe_distinguishes_definitive_empty_from_failure(
    monkeypatch: pytest.MonkeyPatch,
    returncode: int,
    stderr: str,
    expected: Optional[frozenset[str]],
) -> None:
    """A non-zero exit is empty only for the ``no server running`` answer."""

    def _list_sessions(*_args: Any, **_kwargs: Any) -> subprocess.CompletedProcess:
        return subprocess.CompletedProcess(
            args=[],
            returncode=returncode,
            stdout='',
            stderr=stderr,
        )

    monkeypatch.setattr('fractal.util.tmux.subprocess.run', _list_sessions)
    assert fractal.util.tmux.probe() == expected


def test_sessions_folds_inconclusive_probe_into_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A host with no tmux binary is inconclusive; ``sessions`` never crashes.

    ``subprocess.run`` raises ``FileNotFoundError`` (an ``OSError``) when the
    binary is absent -- before any result object -- so a returncode guard
    alone would let it escape. ``probe`` reports the ignorance as ``None``;
    ``sessions`` folds it into the empty set for display-only callers.
    """

    def _no_tmux(*_args: Any, **_kwargs: Any) -> None:
        raise FileNotFoundError(2, 'No such file or directory', 'tmux')

    monkeypatch.setattr('fractal.util.tmux.subprocess.run', _no_tmux)
    assert fractal.util.tmux.probe() is None
    assert fractal.util.tmux.sessions() == frozenset()
