"""Test the ``fractal.util.git`` module.

Runs against real repositories built in pytest tmp dirs -- the git layer is
never mocked -- with the on-disk worktree probe pinned alongside the
resolution verbs built on the raw runner.
"""

from __future__ import annotations

import pathlib
import shutil

import pytest

import fractal.util.git
from tests._helpers import _git

__all__ = [
    'test_resolution_verbs_read_the_repo',
    'test_common_dir_resolves_a_submodule_checkout',
    'test_worktree_probe_reflects_on_disk_state',
    'test_unchecked_failure_degrades_to_none',
    'test_missing_git_binary_degrades_to_none',
    'test_checked_failure_raises_runtime_error',
]


@pytest.fixture
def repo(tmp_path: pathlib.Path) -> pathlib.Path:
    """Return a fresh git repository with pinned identity and one initial commit."""
    root = tmp_path / 'repo'
    root.mkdir()
    _git(root, 'init', '-b', 'main')
    _git(root, 'config', 'user.name', 'Test User')
    _git(root, 'config', 'user.email', 'test@example.com')
    (root / 'README.md').write_text('# repo\n', encoding='utf-8')
    _git(root, 'add', 'README.md')
    _git(root, 'commit', '-m', 'initial commit')
    return root


# ------ resolution verbs


def test_resolution_verbs_read_the_repo(repo: pathlib.Path) -> None:
    """``toplevel``, ``branch``, and ``common_dir`` resolve the live repo."""
    # toplevel canonicalizes a subdirectory to the worktree root
    sub = repo / 'sub'
    sub.mkdir()
    assert fractal.util.git.toplevel(sub) == repo
    # branch reports the pinned initial branch
    assert fractal.util.git.branch(repo) == 'main'
    # common_dir resolves the main repo root, from a linked worktree included
    worktree = repo.parent / 'wt'
    _git(repo, 'worktree', 'add', '-b', 'main.wt', f'{worktree}', 'main')
    assert fractal.util.git.common_dir(worktree) == repo
    assert fractal.util.git.common_dir(repo) == repo


def test_common_dir_resolves_a_submodule_checkout(
    repo: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    """``common_dir`` resolves a submodule checkout to its own root.

    A submodule's git dir nests inside the superproject
    (``.git/modules/<name>``), so the root is not the common dir's parent --
    it resolves back through ``core.worktree`` to the checkout, from a linked
    worktree of the submodule included.
    """
    super_dir = tmp_path / 'super'
    super_dir.mkdir()
    _git(super_dir, 'init', '-b', 'main')
    _git(super_dir, 'config', 'user.name', 'Test User')
    _git(super_dir, 'config', 'user.email', 'test@example.com')
    _git(
        super_dir,
        '-c',
        'protocol.file.allow=always',
        'submodule',
        'add',
        f'{repo}',
        'sub',
    )
    _git(super_dir, 'commit', '-m', 'add submodule')
    sub = super_dir / 'sub'
    assert fractal.util.git.common_dir(sub) == sub
    # a linked worktree of the submodule resolves to the checkout as well
    worktree = tmp_path / 'sub_wt'
    _git(sub, 'worktree', 'add', '-b', 'main.wt', f'{worktree}', 'main')
    assert fractal.util.git.common_dir(worktree) == sub


# ------ worktree probe


def test_worktree_probe_reflects_on_disk_state(repo: pathlib.Path) -> None:
    """The worktree map trusts the disk: an rm-rf'd worktree reads as gone.

    Git still lists a hand-removed worktree (as ``prunable``) until
    ``git worktree prune``; the map and resolver must agree it is gone while
    ``prunable`` points at the one-shot cleanup.
    """
    worktree = repo.parent / 'wt'
    _git(repo, 'worktree', 'add', '-b', 'main.wt', f'{worktree}', 'main')
    # both branches list with their on-disk paths
    mapped = fractal.util.git.worktree_map(repo)
    assert mapped['main'] == repo
    assert mapped['main.wt'] == worktree
    assert fractal.util.git.find_worktree(repo, 'main.wt') == worktree
    assert fractal.util.git.prunable(repo) is False
    # a worktree removed out of band drops from the map but lists as prunable
    shutil.rmtree(worktree)
    assert 'main.wt' not in fractal.util.git.worktree_map(repo)
    assert fractal.util.git.find_worktree(repo, 'main.wt') is None
    assert fractal.util.git.prunable(repo) is True


# ------ failure shape


def test_unchecked_failure_degrades_to_none(tmp_path: pathlib.Path) -> None:
    """Unchecked verbs outside a repository return their empty shapes."""
    outside = tmp_path / 'not_a_repo'
    outside.mkdir()
    assert fractal.util.git.toplevel(outside, check=False) is None
    assert fractal.util.git.branch(outside, check=False) is None
    assert fractal.util.git.worktree_map(outside) == {}
    assert fractal.util.git.prunable(outside) is False


def test_missing_git_binary_degrades_to_none(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A missing ``git`` binary degrades non-raising runs to ``None``."""
    # an empty PATH makes the git lookup itself fail, like an ungit'd host
    empty = tmp_path / 'empty'
    monkeypatch.setenv('PATH', f'{empty}')
    assert fractal.util.git.run(['status'], cwd=tmp_path, check=False) is None
    blob = fractal.util.git.run_bytes(['show', 'HEAD:README.md'], cwd=tmp_path)
    assert blob is None


def test_checked_failure_raises_runtime_error(tmp_path: pathlib.Path) -> None:
    """Checked verbs wrap git failures in a descriptive ``RuntimeError``.

    The message carries the subcommand, exit code, and captured stderr, so
    callers see the failing invocation without re-running it.
    """
    outside = tmp_path / 'not_a_repo'
    outside.mkdir()
    with pytest.raises(RuntimeError, match=r'git rev-parse .* failed \(exit'):
        fractal.util.git.branch(outside)
