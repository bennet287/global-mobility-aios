"""Tests for ``merge.sh`` signal-atomicity in the squash->commit window."""

from __future__ import annotations

import os
import pathlib
import shutil
import subprocess

import pytest

from fractal.core.node import Node
from tests._helpers import _git

from .conftest import _parse_project_dir, _resolve_branch

__all__ = ['test_merge_restores_parent_when_signalled_mid_merge']

# resolve merge.sh from the worktree source (relative to this test), not the
# installed package -- a non-editable install would otherwise test a stale copy
MERGE_SH = pathlib.Path(__file__).parents[2] / 'fractal' / '_scripts' / 'merge.sh'

# a `git` shim that forwards to the real git, except when merge.sh invokes
# `git <intercept>`: it SIGTERMs its parent (the bash running merge.sh) and skips
# the real subcommand -- a deterministic stand-in for an async signal arriving in
# the unprotected window; the subcommand is matched after skipping a leading
# -C <dir> (merge.sh always targets the parent worktree that way)
_GIT_SHIM = """\
#!/usr/bin/env bash
args=("$@")
sub=""
while [ ${#args[@]} -gt 0 ]; do
  case "${args[0]}" in
    -C) args=("${args[@]:2}") ;;
    -*) args=("${args[@]:1}") ;;
    *) sub="${args[0]}"; break ;;
  esac
done
if [ "$sub" = "__INTERCEPT__" ]; then
  kill -TERM "$PPID"
  exit 0
fi
exec "__REAL_GIT__" "$@"
"""


@pytest.mark.parametrize('intercept', ['rm', 'commit'])
def test_merge_restores_parent_when_signalled_mid_merge(
    git_repo: pathlib.Path,
    tmp_path_factory: pytest.TempPathFactory,
    intercept: str,
) -> None:
    """An INT/TERM mid-merge must leave the parent exactly as it began.

    ``merge.sh`` squash-stages the child into the parent's index and working
    tree, strips the child's seed, then commits -- a multi-step sequence with no
    ``trap``. A signal (``fractal node kill``, or the loop interrupting a step)
    arriving between the squash and the commit terminates the script with the
    parent left staged-but-uncommitted. That residue is wrong: the parent's next
    commit absorbs it -- and if the signal landed before the seed-strip, it
    commits the child's own ``.fractal/<branch>/`` seed into the parent, the very
    orphaning ``merge.sh`` exists to prevent. The conflict path already restores
    the parent with ``reset --hard``; the signal path must do the same.

    Parametrized over the two interception points spanning the unprotected
    window: ``rm`` (after squash, before the seed-strip) and ``commit`` (after
    the seed-strip, before the commit lands).
    """
    parent_dir = git_repo
    child_dir, branch = _setup_parent_and_child(git_repo)

    pre_head = _git(parent_dir, 'rev-parse', 'HEAD').stdout.strip()
    pre_tree = _git(parent_dir, 'rev-parse', 'HEAD^{tree}').stdout.strip()

    # inject a SIGTERM when merge.sh reaches `git <intercept>` on the parent
    # the shim dir must live OUTSIDE the repo (the git_repo fixture roots the
    # repo at tmp_path), or it would show up as untracked parent residue
    real_git = shutil.which('git')
    assert real_git is not None, 'git must be on PATH'
    bin_dir = tmp_path_factory.mktemp('shim')
    _write_git_shim(bin_dir, intercept=intercept, real_git=real_git)
    env = dict(os.environ)  # the session fixture already strips _NODE et al.
    path = env['PATH']
    env['PATH'] = f'{bin_dir}{os.pathsep}{path}'

    result = subprocess.run(
        ['bash', f'{MERGE_SH}', f'{child_dir}'],
        cwd=parent_dir,
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
    )

    # the interrupted merge must not have committed on the parent...
    assert result.returncode != 0
    assert _git(parent_dir, 'rev-parse', 'HEAD').stdout.strip() == pre_head
    # ...and must leave the parent exactly as it began -- no staged/working residue
    assert _git(parent_dir, 'status', '--porcelain').stdout.strip() == ''

    # concrete harm if not restored: the parent's next commit absorbs the stray
    # staged changes; drive that commit and assert it captured nothing (tree
    # unchanged) and never tracked the child's seed
    subprocess.run(
        ['git', 'add', '-A'],
        cwd=parent_dir,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ['git', 'commit', '-m', 'parent next commit', '--allow-empty'],
        cwd=parent_dir,
        capture_output=True,
        check=True,
    )
    assert _git(parent_dir, 'rev-parse', 'HEAD^{tree}').stdout.strip() == pre_tree
    assert _git(parent_dir, 'ls-files', f'.fractal/{branch}').stdout.strip() == ''


# ------ helpers


def _setup_parent_and_child(git_repo: pathlib.Path) -> tuple[pathlib.Path, str]:
    """Init a child node with committed work + seed; return ``(child_dir, branch)``.

    Mirrors ``test_merge_excludes_merged_node_seed``: the loop's COMMIT step
    tracks the node's own seed dir on its branch, so the squash has a committed
    seed to pull in (and orphan, if the merge is interrupted before the strip).
    """
    node = Node(git_repo)
    node.init(agent='claude', user=True)
    output = node.init(name='feature')
    child_dir = _parse_project_dir(output)
    branch = _resolve_branch(child_dir)
    # configure git identity in the child worktree
    for cmd in (
        ['git', 'config', 'user.email', 'test@test.com'],
        ['git', 'config', 'user.name', 'Test'],
    ):
        subprocess.run(cmd, cwd=child_dir, capture_output=True, check=True)
    # commit real work alongside the node's own seed dir
    (child_dir / 'feature.txt').write_text('hello from feature\n', encoding='utf-8')
    subprocess.run(
        ['git', 'add', 'feature.txt', f'.fractal/{branch}'],
        cwd=child_dir,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ['git', 'commit', '-m', 'work and seed'],
        cwd=child_dir,
        capture_output=True,
        check=True,
    )
    # the parent's user-node seed is now git-ignored, so its tree is already clean;
    # make a baseline commit (allow-empty) so any post-merge residue is then
    # unambiguously the interrupted merge's
    subprocess.run(['git', 'add', '-A'], cwd=git_repo, capture_output=True, check=True)
    subprocess.run(
        ['git', 'commit', '--allow-empty', '-m', 'parent baseline'],
        cwd=git_repo,
        capture_output=True,
        check=True,
    )
    return child_dir, branch


def _write_git_shim(
    bin_dir: pathlib.Path,
    *,
    intercept: str,
    real_git: str,
) -> None:
    """Write an executable ``git`` shim that SIGTERMs merge.sh at ``intercept``."""
    bin_dir.mkdir(parents=True, exist_ok=True)
    shim = bin_dir / 'git'
    script = _GIT_SHIM.replace('__INTERCEPT__', intercept).replace(
        '__REAL_GIT__',
        real_git,
    )
    shim.write_text(script, encoding='utf-8')
    shim.chmod(0o755)
