"""Concurrency of the worktree-init lock (``Node.init``'s ``fcntl.flock``).

``Node.init`` serializes the not-parallel-safe ``git worktree add`` with an
exclusive ``fcntl.flock`` on ``<repo>/.worktrees/.lock``, held across the whole
critical section (the sibling parent ``nodes``-table writes already serialize via
SQLite's default busy timeout, but the worktree add does not). It is a kernel
lock: mutual exclusion across processes, auto-released when the holder dies (no
PID, no stale-break -- a symlink lock would race around exactly those).

These race the real ``fractal node init`` against one repo and contend the real
lock file directly, each bounded by a subprocess timeout so a regression that
wedges the lock fails loudly instead of hanging.
"""

from __future__ import annotations

import os
import pathlib
import signal
import subprocess
import sys
import time

import pytest

from tests._helpers import _git

from .conftest import _cli_env, _fractal_bin, _reap_group, _run

__all__ = [
    'test_concurrent_init_serializes_without_crashing',
    'test_held_lock_blocks_init_until_holder_dies',
]

# a standalone holder of the real lock file: acquire an exclusive fcntl.flock on
# argv[1], signal readiness via argv[2], then block -- the same lock and mode
# Node.init contends, so a real init must wait behind it
_LOCK_HOLDER = (
    'import fcntl, sys, time; '
    "f = open(sys.argv[1], 'a'); "
    'fcntl.flock(f, fcntl.LOCK_EX); '
    "open(sys.argv[2], 'w').close(); "
    'time.sleep(120)'
)


@pytest.fixture(scope='module')
def repo(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    """Return a repo with a user (root) node so child ``init`` calls have a parent.

    Module-scoped and built once via the real CLI; tests use distinct child
    names so they never collide on the shared repo.
    """
    root = tmp_path_factory.mktemp('init_lock')
    _git(root, 'init', '-b', 'main')
    _git(root, 'config', 'user.email', 'lock@test.local')
    _git(root, 'config', 'user.name', 'lock')
    (root / 'README.md').write_text('# lock\n', encoding='utf-8')
    wiki = root / 'wiki'
    wiki.mkdir()
    (wiki / '_index.md').write_text(
        '---\nname: wiki\n---\n# wiki\n\n***\n',
        encoding='utf-8',
    )
    _git(root, 'add', '-A')
    _git(root, 'commit', '-m', 'init')
    # fractal init creates the user node so child inits have a parent
    assert _run(root, 'init').returncode == 0
    return root


# ------ tests


def test_concurrent_init_serializes_without_crashing(repo: pathlib.Path) -> None:
    """Many concurrent ``init`` calls all succeed -- no ref-lock crash, no hang.

    Without serialization, parallel ``git worktree add`` against one repo fails
    all-but-one with ``cannot lock ref`` (exit 255). Sibling ``child_add`` writes
    to the parent DB already serialize via SQLite's default busy timeout, but the
    worktree/branch creation does not -- so the flock serializes them too, and
    every child worktree and branch is created exactly once.
    """
    # race many child inits at once and collect every outcome
    names = [f'race_{i}' for i in range(4)]
    procs = [_init_proc(repo, name) for name in names]
    outcomes = []
    for proc in procs:
        try:
            out, err = proc.communicate(timeout=120)
        except subprocess.TimeoutExpired:
            # init spawns its own script chain: reap the whole group, not the pid
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            out, err = proc.communicate()
        outcomes.append((proc.returncode, out, err))
    # every init succeeded and none hit git's ref lock
    for code, out, err in outcomes:
        assert code == 0, err
        assert 'cannot lock ref' not in (out + err)
    # every child worktree + branch exists exactly once
    branches = _branches(repo)
    for name in names:
        assert (repo / '.worktrees' / f'main.{name}').is_dir()
        assert branches.count(f'main.{name}') == 1


@pytest.mark.parametrize(
    argnames='sig',
    argvalues=[signal.SIGKILL, signal.SIGTERM],
    ids=['sigkill', 'sigterm'],
)
def test_held_lock_blocks_init_until_holder_dies(
    repo: pathlib.Path,
    sig: signal.Signals,
) -> None:
    """A held lock blocks ``init``; the holder's death frees it (even SIGKILL).

    Proves both halves of the kernel lock: exclusive contention (init does not
    proceed while the lock is held) and auto-release on holder death -- including
    the uncatchable SIGKILL that would strand a symlink lock and is the
    precondition for its stale-break races.
    """
    # start a holder that grabs the lock and blocks
    lock_file = repo / '.worktrees' / '.lock'
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    ready = repo / f'holder_ready_{sig.name}'
    if ready.exists():
        ready.unlink()
    holder = subprocess.Popen(
        [sys.executable, '-c', _LOCK_HOLDER, f'{lock_file}', f'{ready}']
    )
    init = None
    try:
        _await(ready, proc=holder, deadline=time.monotonic() + 10)
        # a real init now contends the same lock -- it must block, not proceed
        name = f'after_{sig.name.lower()}'
        init = _init_proc(repo, name)
        with pytest.raises(subprocess.TimeoutExpired):
            init.wait(timeout=3)
        # the holder dies -> the kernel releases the lock -> init proceeds
        holder.send_signal(sig)
        holder.wait(timeout=5)
        _, err = init.communicate(timeout=60)
        assert init.returncode == 0, err
        assert (repo / '.worktrees' / f'main.{name}').is_dir()
    finally:
        # init spawns its own script chain: reap the whole group, not the pid
        if init is not None:
            _reap_group(init)
        # the holder is a single leaf process, so a pid kill reaps it fully
        if holder.poll() is None:
            holder.kill()
            holder.wait()


# ------ helpers


def _branches(repo: pathlib.Path) -> list[str]:
    """Local branch names in ``repo``."""
    result = subprocess.run(
        ['git', 'branch', '--format=%(refname:short)'],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.split()


def _init_proc(repo: pathlib.Path, name: str) -> subprocess.Popen:
    """Launch ``fractal node init <name>`` against ``repo`` as a background process.

    Uses the hermetic CLI env so the subprocess runs *this* worktree's code (the
    flock under test), not the frozen site-packages install.
    """
    return subprocess.Popen(
        [
            _fractal_bin(),
            'node',
            'init',
            name,
            '--agent',
            'claude',
            '--path',
            f'{repo}',
        ],
        cwd=f'{repo}',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=_cli_env(),
        start_new_session=True,
    )


def _await(marker: pathlib.Path, *, proc: subprocess.Popen, deadline: float) -> None:
    """Block (bounded) until ``marker`` appears, failing if ``proc`` dies first."""
    while not marker.exists():
        assert proc.poll() is None, 'holder exited before acquiring the lock'
        assert time.monotonic() < deadline, 'holder never signalled ready'
        time.sleep(0.02)
