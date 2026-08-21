"""Bootstrap behavior of ``fractal init`` on a folder that is not a git repo.

``fractal init`` anchors the user node at the git root, so when run in a fresh,
non-git folder it first ``git init``s a repo on a branch named after the project
(the sanitized folder name) and births that branch with an initial commit, then
proceeds with the normal user-node init. These drive the real CLI as a
subprocess and assert the resulting repo, branch, and commit -- and that an
enclosing repo is never clobbered.
"""

from __future__ import annotations

import pathlib

from fractal.core.node import Node
from tests._helpers import _git

from .conftest import _run

__all__ = [
    'test_init_bootstraps_a_fresh_repo',
    'test_init_is_idempotent_on_a_bootstrapped_repo',
    'test_init_skips_an_existing_enclosing_repo',
    'test_init_rejects_an_unsanitizable_directory_name',
    'test_init_preserves_an_existing_gitignore',
    'test_init_reports_missing_git_identity',
    'test_init_completes_a_repo_with_an_unborn_branch',
]

# git identity for the bootstrap commit, supplied via env so a fresh repo needs
# no pre-existing user config (the same way a real user's global identity applies)
_IDENTITY = {
    'GIT_AUTHOR_NAME': 'Test',
    'GIT_AUTHOR_EMAIL': 'test@test.com',
    'GIT_COMMITTER_NAME': 'Test',
    'GIT_COMMITTER_EMAIL': 'test@test.com',
}


# ------ tests


def test_init_bootstraps_a_fresh_repo(tmp_path: pathlib.Path) -> None:
    """A non-git folder gets a repo on the sanitized project branch.

    The branch is the folder name with dashes converted (``my-app`` -> ``my_app``,
    matching the wiki/project name), birthed by an initial commit of an empty
    ``.gitignore``; the user node and project wiki are created on top.
    """
    folder = tmp_path / 'my-app'
    folder.mkdir()
    result = _run(folder, 'init', **_IDENTITY)
    assert result.returncode == 0, result.stderr
    assert 'Initialized user node on branch my_app' in result.stdout
    # repo created on the sanitized project branch
    branch = _git(folder, 'rev-parse', '--abbrev-ref', 'HEAD').stdout.strip()
    assert branch == 'my_app'
    # the branch was birthed by our initial commit -- the root commit `init my_app`
    # with an empty, tracked .gitignore (`wiki init` adds its own commit on top)
    root = _git(folder, 'rev-list', '--max-parents=0', 'HEAD').stdout.strip()
    subject = _git(folder, 'log', '-1', '--format=%s', root).stdout.strip()
    assert subject == 'init my_app'
    assert '.gitignore' in _git(folder, 'ls-files').stdout.split()
    assert (folder / '.gitignore').read_text() == ''
    # user node + project wiki landed on top
    assert Node(folder).is_user
    assert (folder / 'wiki').is_dir()


def test_init_is_idempotent_on_a_bootstrapped_repo(tmp_path: pathlib.Path) -> None:
    """Re-running ``init`` neither re-inits git nor adds a second commit."""
    folder = tmp_path / 'my-app'
    folder.mkdir()
    assert _run(folder, 'init', **_IDENTITY).returncode == 0
    tip = _git(folder, 'rev-parse', 'HEAD').stdout.strip()
    result = _run(folder, 'init', **_IDENTITY)
    assert result.returncode == 0, result.stderr
    assert 'already initialized' in result.stdout
    # the branch tip is unchanged -- no new commit
    assert _git(folder, 'rev-parse', 'HEAD').stdout.strip() == tip


def test_init_skips_an_existing_enclosing_repo(tmp_path: pathlib.Path) -> None:
    """In a subdir of an existing repo, init reuses it -- no nested repo."""
    repo = _init_repo(tmp_path / 'outer')
    sub = repo / 'app'
    sub.mkdir()
    result = _run(sub, 'init')
    assert result.returncode == 0, result.stderr
    # the enclosing repo is reused: no nested .git, current branch untouched
    assert not (sub / '.git').exists()
    assert _git(repo, 'rev-parse', '--abbrev-ref', 'HEAD').stdout.strip() == 'main'


def test_init_rejects_an_unsanitizable_directory_name(tmp_path: pathlib.Path) -> None:
    """A folder name that can't be sanitized fails before ``git init`` runs."""
    folder = tmp_path / 'bad name'  # a space cannot become a valid identifier
    folder.mkdir()
    result = _run(folder, 'init')
    assert result.returncode != 0
    assert 'valid project name' in result.stderr
    # nothing was created -- we fail before touching git
    assert not (folder / '.git').exists()


def test_init_preserves_an_existing_gitignore(tmp_path: pathlib.Path) -> None:
    """Bootstrap commits a user's existing .gitignore without clobbering it."""
    folder = tmp_path / 'my-app'
    folder.mkdir()
    (folder / '.gitignore').write_text('__pycache__/\n', encoding='utf-8')
    result = _run(folder, 'init', **_IDENTITY)
    assert result.returncode == 0, result.stderr
    # the user's content is preserved and the file is committed (branch birthed)
    assert (folder / '.gitignore').read_text() == '__pycache__/\n'
    assert '.gitignore' in _git(folder, 'ls-files').stdout.split()


def test_init_reports_missing_git_identity(tmp_path: pathlib.Path) -> None:
    """A failed bootstrap commit surfaces guidance and a recoverable half-state.

    With no resolvable git identity the initial commit fails; ``init`` must exit
    non-zero, tell the user to configure git, and leave the repo in the
    recoverable half-state (``.git`` present, branch unborn) that
    ``test_init_completes_a_repo_with_an_unborn_branch`` then completes.
    """
    folder = tmp_path / 'my-app'
    folder.mkdir()
    # empty identity forces `git commit` to fail ('empty ident name not allowed')
    noident = dict.fromkeys(_IDENTITY, '')
    result = _run(folder, 'init', **noident)
    assert result.returncode != 0
    assert 'git config user' in result.stderr
    # the repo is left recoverable: .git exists with an unborn branch (no commit)
    assert (folder / '.git').is_dir()
    assert _git(folder, 'rev-list', '--count', '--all').stdout.strip() == '0'


def test_init_completes_a_repo_with_an_unborn_branch(tmp_path: pathlib.Path) -> None:
    """A prior bootstrap whose commit failed (unborn branch) is finished on re-run.

    Mirrors the half-initialized state left when the initial commit fails (e.g. no
    git identity): ``.git`` exists on an unborn branch. Re-running ``init`` -- with
    identity now configured, as the error message instructs -- births the branch
    and completes the user node, rather than dying on the unborn ``HEAD``.
    """
    folder = tmp_path / 'my-app'
    folder.mkdir()
    # leave the repo as a failed bootstrap would: init, no commit (unborn branch)
    _git(folder, 'init', '-b', 'my_app')
    result = _run(folder, 'init', **_IDENTITY)
    assert result.returncode == 0, result.stderr
    assert 'Initialized user node on branch my_app' in result.stdout
    # the branch is now born (abbrev-ref resolves) and the user node landed
    assert _git(folder, 'rev-parse', '--abbrev-ref', 'HEAD').stdout.strip() == 'my_app'
    assert Node(folder).is_user


# ------ helpers


def _init_repo(path: pathlib.Path) -> pathlib.Path:
    """Create a git repo on ``main`` with one commit (an enclosing repo)."""
    path.mkdir(parents=True, exist_ok=True)
    _git(path, 'init', '-b', 'main')
    _git(path, 'config', 'user.email', 'test@test.com')
    _git(path, 'config', 'user.name', 'Test')
    (path / 'README.md').write_text('# outer\n', encoding='utf-8')
    _git(path, 'add', 'README.md')
    _git(path, 'commit', '-m', 'initial')
    return path
