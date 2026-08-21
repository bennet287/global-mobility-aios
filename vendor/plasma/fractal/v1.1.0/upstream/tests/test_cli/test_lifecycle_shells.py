"""Script-internal stress tests for the secondary lifecycle shells.

Drives ``fractal/_scripts/{destroy,attach,retire,unretire}.sh`` directly via
``bash`` against throwaway git repos, exercising the edges that the
end-to-end CLI tests (``test_node_cli.py``, ``test_lifecycle.py``) leave
uncovered: ``destroy.sh``'s teardown error paths and idempotency, and the
no-op hook stubs' argument contract.

``destroy.sh`` is the only one of the four with real logic -- the fractal
teardown (``fractal destroy`` -> ``Node.destroy``), scoped to one tree by
default and repo-wide with ``--all``. The others are pre/post hooks whose
state changes live in ``node.py``; here we pin only their shell-level
contract (accept a path, reject a missing one).

The teardown is destructive, so every test builds its own fresh repo under
``tmp_path`` rather than sharing a fixture.
"""

from __future__ import annotations

import pathlib
import subprocess

import pytest

import fractal
from tests._helpers import _git

from .conftest import _require_tmux

__all__ = [
    'test_destroy_noop_without_fractal',
    'test_destroy_all_removes_worktrees_and_branches',
    'test_destroy_tree_scope_spares_sibling_worktrees',
    'test_destroy_all_sweeps_every_user_data_dir',
    'test_destroy_rejects_node_dir_without_all',
    'test_destroy_removes_node_dir',
    'test_destroy_is_idempotent',
    'test_destroy_rejects_non_repo_path',
    'test_destroy_does_not_orphan_a_locked_worktree',
    'test_destroy_pre_flights_locks_before_any_removal',
    'test_destroy_refuses_a_running_tmux_session',
    'test_destroy_refuses_a_paused_node',
    'test_hook_stub_accepts_path_and_is_a_noop',
    'test_hook_stub_requires_a_path',
]


# ------ destroy.sh: teardown error paths + idempotency


def test_destroy_noop_without_fractal(tmp_path: pathlib.Path) -> None:
    """A repo with no worktrees and no node data destroys as a no-op."""
    repo = _make_repo(tmp_path / 'repo')
    result = _bash('destroy.sh', str(repo))
    assert result.returncode == 0, result.stderr
    assert 'Nothing to destroy' in result.stdout


def test_destroy_all_removes_worktrees_and_branches(
    tmp_path: pathlib.Path,
) -> None:
    """``--all`` tears down worktrees, their branches, and ``.worktrees/``."""
    repo = _make_repo(tmp_path / 'repo')
    _add_worktree(repo, 'main.foo')
    result = _bash('destroy.sh', str(repo), '--all')
    assert result.returncode == 0, result.stderr
    assert not (repo / '.worktrees').exists()
    # branch is gone and git holds no stale worktree registration
    branches = _git_out(repo, 'branch', '--list', 'main.foo')
    assert branches.strip() == ''
    assert '.worktrees' not in _git_out(repo, 'worktree', 'list')


def test_destroy_tree_scope_spares_sibling_worktrees(
    tmp_path: pathlib.Path,
) -> None:
    """A bare (tree-scoped) destroy removes only the named tree's worktrees.

    Worktree dirs are named by branch, so the ``<branch>.*`` scope takes the
    tree's own nodes and leaves a sibling tree's worktree -- and the shared
    ``.worktrees/`` plumbing -- in place.
    """
    repo = _make_repo(tmp_path / 'repo')
    _add_worktree(repo, 'main.foo')
    sibling = _add_worktree(repo, 'other.bar')
    result = _bash('destroy.sh', str(repo), '--branch=main')
    assert result.returncode == 0, result.stderr
    assert 'Destroyed tree: main' in result.stdout
    # the tree's worktree and branch are gone; the sibling's are untouched
    assert _git_out(repo, 'branch', '--list', 'main.foo').strip() == ''
    assert sibling.is_dir()
    assert _git_out(repo, 'branch', '--list', 'other.bar').strip() != ''
    assert (repo / '.worktrees').is_dir()


def test_destroy_all_sweeps_every_user_data_dir(tmp_path: pathlib.Path) -> None:
    """``--all`` removes every data dir the caller names, not just the anchor's.

    Which dirs are user roots is a config question the caller answers, so the
    sweep clears each ``--node-dir`` it is handed. A root branch may itself be
    dotted (``v1.0`` is the user's own branch name), so the sweep never reads
    the name -- a name-shaped filter would strand that tree's database.
    """
    repo = _make_repo(tmp_path / 'repo')
    (repo / '.worktrees' / '.project').mkdir(parents=True)
    branches = ('main', 'other', 'v1.0')
    for branch in branches:
        node_dir = repo / '.fractal' / branch
        node_dir.mkdir(parents=True)
        (node_dir / 'config.json').write_text(
            '{\n  "user": true\n}\n', encoding='utf-8'
        )
    named = [f'--node-dir=.fractal/{branch}' for branch in branches]
    result = _bash('destroy.sh', str(repo), '--branch=main', '--all', *named)
    assert result.returncode == 0, result.stderr
    assert not (repo / '.fractal').exists()


def test_destroy_rejects_node_dir_without_all(tmp_path: pathlib.Path) -> None:
    """``--node-dir`` is refused outside an ``--all`` sweep.

    The flag names data dirs for the repo-wide sweep; honoring it on a
    tree-scoped run would remove dirs the scope never authorized.
    """
    repo = _make_repo(tmp_path / 'repo')
    node_dir = repo / '.fractal' / 'main'
    node_dir.mkdir(parents=True)
    result = _bash('destroy.sh', str(repo), '--node-dir=.fractal/main')
    assert result.returncode == 1
    assert '--node-dir requires --all' in result.stderr
    # nothing was removed
    assert node_dir.is_dir()


@pytest.mark.parametrize('project', ['.', 'sub'])
def test_destroy_removes_node_dir(tmp_path: pathlib.Path, project: str) -> None:
    """The node dir is derived (via the ``.project`` cache) and removed."""
    repo = _make_repo(tmp_path / 'repo')
    base = repo if project == '.' else repo / project
    node_dir = base / '.fractal' / 'main'
    node_dir.mkdir(parents=True)
    (node_dir / 'config.json').write_text('{}\n', encoding='utf-8')
    # the central database lives here too -- destroy must take it with the dir
    (node_dir / '.db').write_text('', encoding='utf-8')
    # a sub-project node dir is located through the .worktrees/.project cache
    if project != '.':
        cache = repo / '.worktrees' / '.project'
        cache.mkdir(parents=True)
        (cache / 'main').write_text(f'{project}\n', encoding='utf-8')
    result = _bash('destroy.sh', str(repo))
    assert result.returncode == 0, result.stderr
    # the node dir and the emptied .fractal/ container are both gone
    assert not (base / '.fractal').exists()
    assert 'Destroyed tree: main' in result.stdout


def test_destroy_is_idempotent(tmp_path: pathlib.Path) -> None:
    """Re-running a completed destroy is a clean no-op, not an error."""
    repo = _make_repo(tmp_path / 'repo')
    _add_worktree(repo, 'main.foo')
    first = _bash('destroy.sh', str(repo))
    assert first.returncode == 0, first.stderr
    second = _bash('destroy.sh', str(repo))
    assert second.returncode == 0, second.stderr
    assert 'Nothing to destroy' in second.stdout


def test_destroy_rejects_non_repo_path(tmp_path: pathlib.Path) -> None:
    """A path that is not a git repo is rejected, not silently torn down."""
    plain = tmp_path / 'plain'
    plain.mkdir()
    result = _bash('destroy.sh', str(plain))
    assert result.returncode == 1
    assert 'not a git repository' in result.stderr


def test_destroy_does_not_orphan_a_locked_worktree(
    tmp_path: pathlib.Path,
) -> None:
    """``destroy.sh`` must not silently orphan a worktree it can't remove.

    A locked worktree makes ``git worktree remove --force`` fail. The script
    must surface that as a non-zero exit and leave the worktree (and its
    ``.worktrees/`` registration) intact -- rather than ``rm -rf``-ing the
    directory out from under git while reporting success, which leaves an
    orphaned worktree registration that ``git worktree prune`` cannot clean.
    """
    repo = _make_repo(tmp_path / 'repo')
    worktree = _add_worktree(repo, 'main.foo')
    _git(repo, 'worktree', 'lock', str(worktree))
    result = _bash('destroy.sh', str(repo))
    # must fail loudly, never claim success
    assert result.returncode != 0, (
        f'destroy.sh reported success but could not remove a locked worktree; '
        f'stdout={result.stdout!r}'
    )
    # must NOT have deleted the directory -- no orphaned git registration
    assert worktree.is_dir()
    # the worktree is still registered (not orphaned by an rm -rf)
    assert worktree.name in _git_out(repo, 'worktree', 'list')


def test_destroy_pre_flights_locks_before_any_removal(
    tmp_path: pathlib.Path,
) -> None:
    """A locked worktree aborts the destroy before any sibling is removed.

    The teardown is non-atomic, so a lock discovered mid-tear would strand
    a half-destroyed tree; the script must pre-flight every worktree's lock
    and leave the whole tree intact.
    """
    repo = _make_repo(tmp_path / 'repo')
    sibling = _add_worktree(repo, 'main.aaa')
    locked = _add_worktree(repo, 'main.zzz')
    _git(repo, 'worktree', 'lock', str(locked))
    result = _bash('destroy.sh', str(repo))
    assert result.returncode == 1
    assert 'locked' in result.stderr
    # the unlocked sibling was not removed -- no half-destroyed tree
    assert sibling.is_dir()
    assert locked.is_dir()


def test_destroy_refuses_a_running_tmux_session(tmp_path: pathlib.Path) -> None:
    """A node with a live tmux session blocks the destroy before any removal."""
    _require_tmux()
    repo = _make_repo(tmp_path / 'tmuxguard')
    worktree = _add_worktree(repo, 'main.foo')
    # the session name destroy.sh derives: <repo dirname> (<branch, dots dashed>)
    session = f'{repo.name} (main-foo)'
    subprocess.run(['tmux', 'new-session', '-d', '-s', session], check=True)
    try:
        result = _bash('destroy.sh', str(repo))
        assert result.returncode == 1
        assert 'still running in tmux' in result.stderr
        # nothing was removed
        assert worktree.is_dir()
    finally:
        # `=` prefix forces an exact target match (no prefix resolution)
        subprocess.run(
            ['tmux', 'kill-session', '-t', f'={session}'],
            capture_output=True,
        )


@pytest.mark.parametrize('project', ['.', 'sub'])
def test_destroy_refuses_a_paused_node(
    tmp_path: pathlib.Path,
    project: str,
) -> None:
    """A paused node blocks the bare script before any removal.

    The script's ``.status`` re-check (through the ``.project`` cache) is
    the race backstop behind the caller's kill sweep: a pause landing after
    the sweep, mid-teardown, must still refuse rather than discard the
    parked worktree.
    """
    repo = _make_repo(tmp_path / 'repo')
    worktree = _add_worktree(repo, 'main.foo')
    base = worktree if project == '.' else worktree / project
    node_dir = base / '.fractal' / 'main.foo'
    node_dir.mkdir(parents=True)
    (node_dir / '.status').write_text('paused\n', encoding='utf-8')
    # a sub-project node dir is located through the .worktrees/.project cache
    if project != '.':
        cache = repo / '.worktrees' / '.project'
        cache.mkdir(parents=True)
        (cache / 'main.foo').write_text(f'{project}\n', encoding='utf-8')
    result = _bash('destroy.sh', str(repo))
    assert result.returncode == 1
    assert 'paused' in result.stderr
    # nothing was removed
    assert worktree.is_dir()


# ------ attach.sh / retire.sh / unretire.sh: no-op hook contract


@pytest.mark.parametrize('script', ['attach.sh', 'retire.sh', 'unretire.sh'])
def test_hook_stub_accepts_path_and_is_a_noop(
    tmp_path: pathlib.Path,
    script: str,
) -> None:
    """Each hook stub accepts a worktree path and exits 0 without output."""
    result = _bash(script, str(tmp_path))
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == ''


@pytest.mark.parametrize('script', ['attach.sh', 'retire.sh', 'unretire.sh'])
def test_hook_stub_requires_a_path(script: str) -> None:
    """Each hook stub rejects a missing path with a clear error."""
    result = _bash(script)
    assert result.returncode == 1
    assert 'path is required' in result.stderr


# ------ helpers


def _scripts_dir() -> pathlib.Path:
    """Bundled ``_scripts/`` directory (resolved lazily, not at import)."""
    return pathlib.Path(fractal.__file__).resolve().parent / '_scripts'


def _git_out(cwd: pathlib.Path, *args: str) -> str:
    """Return stdout of a git command in ``cwd``."""
    return _git(cwd, *args).stdout


def _bash(script: str, *args: str) -> subprocess.CompletedProcess:
    """Run a bundled ``_scripts/`` shell with args and capture output."""
    return subprocess.run(
        ['bash', str(_scripts_dir() / script), *args],
        capture_output=True,
        text=True,
    )


def _make_repo(root: pathlib.Path) -> pathlib.Path:
    """Build a fresh git repo with a single commit under ``root``."""
    root.mkdir(parents=True, exist_ok=True)
    _git(root, 'init', '-q', '-b', 'main')
    _git(root, 'config', 'user.email', 'node@test.local')
    _git(root, 'config', 'user.name', 'node')
    (root / 'README.md').write_text('# repo\n', encoding='utf-8')
    _git(root, 'add', '-A')
    _git(root, 'commit', '-qm', 'init')
    return root


def _add_worktree(repo: pathlib.Path, name: str) -> pathlib.Path:
    """Add a worktree under ``repo/.worktrees/<name>`` on branch ``<name>``."""
    worktree = repo / '.worktrees' / name
    _git(repo, 'worktree', 'add', '-q', str(worktree), '-b', name)
    return worktree
