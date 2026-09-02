"""Test the ``fractal.core.worktree`` module."""

from __future__ import annotations

import pathlib
import subprocess
import sys
import threading

import pytest

import fractal.core.worktree
import fractal.util
from fractal.core.node import Node
from tests._helpers import _stub_run_script

from .conftest import _resolve_branch

__all__ = [
    'test_init_rejects_slash_in_name',
    'test_init_rejects_invalid_name_chars',
    'test_init_caps_name_length_at_64',
    'test_user_init_records_project_and_places_data',
    'test_user_init_rejects_invalid_repo_name',
    'test_failed_init_preserves_reused_branch_but_prunes_created',
    'test_exclude_update_preserves_content_and_collapses_blocks',
    'test_exclude_update_orphan_begin_preserves_tail',
    'test_exclude_update_concurrent_writers_preserve_custom',
    'test_seed_ignore_toggle_hides_and_exposes_the_dir',
    'test_clone_cache_dirs_clones_missing_and_skips_unusable',
]


# ------ name validation


def test_init_rejects_slash_in_name(git_repo: pathlib.Path) -> None:
    """Init rejects a name containing '/' instead of stranding a worktree.

    ``main.sub/dir`` is a valid git ref, so ``init.sh``'s ``git worktree add``
    succeeds and creates the branch plus a nested worktree -- but the later
    ``.project`` cache write targets a never-created directory and aborts,
    stranding a half-built worktree and branch the node layer never registers.
    ``init`` must reject the name up front, mirroring the ``.``/``-`` rejections.
    """
    node = Node(git_repo)
    node.init(agent='claude', user=True)

    # '/' is the git ref path separator -- reject before any git operation
    with pytest.raises(ValueError, match="contain '/'"):
        node.init(name='sub/dir')

    # nothing stranded: no nested worktree dir and no partial branch left behind
    assert not (git_repo / '.worktrees' / 'main.sub').exists()
    branches = subprocess.run(
        ['git', 'branch', '--format=%(refname:short)'],
        cwd=git_repo,
        capture_output=True,
        text=True,
        check=True,
    )
    assert not any(b.startswith('main.sub') for b in branches.stdout.split())


@pytest.mark.parametrize(
    argnames=('name', 'match'),
    argvalues=[
        ('a.b', 'hierarchy separator'),
        ('a-b', "use '_' instead"),
        ('a b', 'letters, digits'),
        ('task~1', 'letters, digits'),
        ('café', 'letters, digits'),
    ],
)
def test_init_rejects_invalid_name_chars(
    git_repo: pathlib.Path,
    name: str,
    match: str,
) -> None:
    """Init rejects names that are not git-/worktree-safe before any git op.

    The common separators (``.``/``-``) get targeted guidance; every other
    non-word character falls through to the allowlist rejection. A name must
    never reach ``git worktree``/``branch`` and fail there with a raw error.
    """
    node = Node(git_repo)
    node.init(agent='claude', user=True)

    with pytest.raises(ValueError, match=match):
        node.init(name=name)


def test_init_caps_name_length_at_64(
    git_repo: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Init rejects a single name segment over 64 characters.

    Without a segment cap, names would be bounded only by git's 255-char
    *branch* limit -- a 200-char name would pass end-to-end and produce
    unusable worktree paths and radio columns. The cap is per segment --
    branches accrete one name per level, and the 255 composed-branch guard
    (reachable only from a deep parent prefix, not in one hop) owns the
    deep-tree bound.
    """
    node = Node(git_repo)
    node.init(agent='claude', user=True)

    # 65 overflows the segment cap with a legible, name-scoped rejection
    with pytest.raises(ValueError, match=r'too long.*max 64'):
        node.init(name='a' * 65)
    # 64 fits (the rest of init is stubbed)
    _stub_run_script(monkeypatch, Node)
    node.init(name='a' * 64)


# ------ project cache


@pytest.mark.parametrize('project', ['.', 'app', 'packages/core'])
def test_user_init_records_project_and_places_data(
    git_repo: pathlib.Path,
    project: str,
) -> None:
    """User init places data under ``<project>/.fractal`` and records it.

    The repo root (``.``) and monorepo sub-projects share one path, with the
    project prefix applied exactly once (no ``app/app`` doubling).
    """
    if project != '.':
        (git_repo / project).mkdir(parents=True)
    node = Node(git_repo)
    node.init(path=project, user=True)
    # data dir lives under the project, applied exactly once
    branch = _resolve_branch(git_repo)
    if project == '.':
        node_dir = git_repo / '.fractal' / branch
    else:
        node_dir = git_repo / project / '.fractal' / branch
    assert node_dir.is_dir()
    assert (node_dir / '.db').exists()
    # project recorded in both the config and the worktree cache
    assert node.is_user
    assert node.config.get('project') == project
    cache = git_repo / '.worktrees' / '.project' / branch
    assert cache.read_text(encoding='utf-8').strip() == project


def test_user_init_rejects_invalid_repo_name(tmp_path: pathlib.Path) -> None:
    """An invalid repo directory name is rejected up front, not half-initialized.

    ``fractal init`` derives the project wiki name from the repo directory,
    converting dashes to underscores. A name still invalid after that (e.g. one
    with a ``.``) is rejected *before* any node data is written -- rather than
    crashing mid-``wiki init`` and stranding a partial user node with no wiki.
    """
    # a repo dir name invalid as a wiki name even after dash conversion (has a '.')
    repo = tmp_path / 'bad.name'
    repo.mkdir()

    def git(*args: str) -> None:
        subprocess.run(['git', *args], cwd=repo, capture_output=True, check=True)

    git('init', '-b', 'main')
    git('config', 'user.email', 'test@test.com')
    git('config', 'user.name', 'Test')
    (repo / 'README.md').write_text('# r\n', encoding='utf-8')
    git('add', '-A')
    git('commit', '-m', 'init')

    with pytest.raises(ValueError, match='valid project name'):
        Node(repo).init(agent='claude', user=True)
    # rejected before any writes -- no partial user node left behind
    assert not (repo / '.fractal').exists()


# ------ rollback


def test_failed_init_preserves_reused_branch_but_prunes_created(
    git_repo: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed init removes its worktree but deletes only a branch it created.

    init.sh reuses an existing branch in place (``worktree add`` with no ``-b``).
    If the init then fails after the worktree exists, the rollback must NOT
    delete a reused pre-existing branch -- its committed history would be lost --
    while a branch this init created is still pruned.
    """
    Node(git_repo).init(agent='claude', user=True)

    def show_ref(branch: str) -> bool:
        cmd = [
            'git',
            '-C',
            f'{git_repo}',
            'show-ref',
            '--verify',
            f'refs/heads/{branch}',
        ]
        result = subprocess.run(cmd, capture_output=True)
        return result.returncode == 0

    # an orphan branch: exists with no worktree (a half-deleted / out-of-band node)
    subprocess.run(
        ['git', '-C', f'{git_repo}', 'branch', 'main.reused'],
        check=True,
        capture_output=True,
    )

    # fail every init right after init.sh creates the worktree (registration)
    def boom(self: Node, *args: object, **kwargs: object) -> None:
        raise RuntimeError('induced post-worktree-add failure')

    monkeypatch.setattr(Node, 'child_add', boom)

    # reused branch: worktree rolled back, branch SURVIVES
    with pytest.raises(RuntimeError, match='induced'):
        Node(git_repo).init(name='reused')
    assert fractal.util.git.find_worktree(git_repo, 'main.reused') is None
    assert show_ref('main.reused')  # reused branch ref preserved

    # created branch: worktree rolled back, branch PRUNED
    with pytest.raises(RuntimeError, match='induced'):
        Node(git_repo).init(name='created')
    assert fractal.util.git.find_worktree(git_repo, 'main.created') is None
    assert not show_ref('main.created')  # a branch this init created is removed


# ------ git excludes


@pytest.mark.parametrize(
    argnames=('seed', 'keep', 'drop'),
    argvalues=[
        # custom lines before AND after a real block survive; block stays one
        (
            'keep_before\n# >>> fractal >>>\nstale_inner\n# <<< fractal <<<\nkeep_after\n',
            ['keep_before', 'keep_after'],
            ['stale_inner'],
        ),
        # two stacked blocks collapse to exactly one
        (
            '# >>> fractal >>>\nstale_one\n# <<< fractal <<<\n'
            '# >>> fractal >>>\nstale_two\n# <<< fractal <<<\nkeep_outer\n',
            ['keep_outer'],
            ['stale_one', 'stale_two'],
        ),
        # a custom line that merely mentions the markers is left untouched
        (
            'doc mentions # >>> fractal >>> and # <<< fractal <<< inline\nkeep_plain\n',
            [
                'doc mentions # >>> fractal >>> and # <<< fractal <<< inline',
                'keep_plain',
            ],
            [],
        ),
    ],
)
def test_exclude_update_preserves_content_and_collapses_blocks(
    tmp_path: pathlib.Path,
    seed: str,
    keep: list[str],
    drop: list[str],
) -> None:
    """``exclude_update`` preserves non-fractal content and keeps exactly one block.

    Whole-line marker matching means a custom line that *mentions* the markers is
    never treated as a delimiter, and stacked blocks collapse to one -- so a
    re-init never duplicates the block or mangles user lines.
    """
    repo = _git_repo(tmp_path)
    exclude = repo / '.git' / 'info' / 'exclude'
    exclude.write_text(seed, encoding='utf-8')
    fractal.core.worktree.exclude_update(repo)
    out = exclude.read_text(encoding='utf-8')
    for line in keep:
        assert line in out
    for line in drop:
        assert line not in out
    blocks = sum(1 for ln in out.splitlines() if ln.strip() == '# >>> fractal >>>')
    assert blocks == 1


def test_exclude_update_orphan_begin_preserves_tail(tmp_path: pathlib.Path) -> None:
    """An unmatched begin marker is left as content, not swallowing the tail.

    A ``find()``-based strip would delete everything from a lone begin marker to
    EOF; the whole-line walk leaves the orphan in place and still appends a fresh
    block, so content after the orphan survives.
    """
    repo = _git_repo(tmp_path)
    exclude = repo / '.git' / 'info' / 'exclude'
    exclude.write_text('top_custom\n# >>> fractal >>>\nkeep_tail\n', encoding='utf-8')
    fractal.core.worktree.exclude_update(repo)
    out = exclude.read_text(encoding='utf-8')
    assert 'top_custom' in out
    assert 'keep_tail' in out
    # a complete fresh block is still written
    assert '# >>> fractal >>>' in out
    assert '# <<< fractal <<<' in out


def test_exclude_update_concurrent_writers_preserve_custom(
    tmp_path: pathlib.Path,
) -> None:
    """Concurrent ``exclude_update`` writers never drop the user's custom lines.

    The common-dir ``info/exclude`` is shared by every worktree, so sibling
    ``init``/``start`` fan-out races on it. The atomic unique-temp ``os.replace``
    keeps a racing writer from observing a truncated file and overwriting custom
    content -- a non-atomic ``write_text`` loses ``CUSTOM_KEEP`` under contention.
    """
    repo = _git_repo(tmp_path)
    exclude = repo / '.git' / 'info' / 'exclude'
    exclude.write_text('CUSTOM_KEEP\n', encoding='utf-8')
    workers = 8
    barrier = threading.Barrier(workers)

    def hammer() -> None:
        barrier.wait(timeout=30)
        for _ in range(15):
            fractal.core.worktree.exclude_update(repo)

    threads = [threading.Thread(target=hammer) for _ in range(workers)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    out = exclude.read_text(encoding='utf-8')
    assert 'CUSTOM_KEEP' in out
    blocks = sum(1 for ln in out.splitlines() if ln.strip() == '# >>> fractal >>>')
    assert blocks == 1


def test_seed_ignore_toggle_hides_and_exposes_the_dir(
    tmp_path: pathlib.Path,
) -> None:
    """The seed dir's self-ignore hides it from status; removal exposes it.

    The self-ignore silences the whole dir -- the ignore file included -- so
    an untracked tree never surfaces in ``git status``, and no shared-block
    rewrite can flip the choice. ``seed_ignore_remove`` (``fractal track``)
    makes the dir stageable again.
    """
    repo = _git_repo(tmp_path)
    node_dir = repo / '.fractal' / 'main'
    node_dir.mkdir(parents=True)
    (node_dir / 'config.json').write_text('{}\n', encoding='utf-8')
    fractal.core.worktree.seed_ignore_write(node_dir)
    assert fractal.core.worktree.seed_tracked(node_dir) is False
    # the whole dir is silent in status, and a block rewrite changes nothing
    fractal.core.worktree.exclude_update(repo)
    status = subprocess.run(
        ['git', 'status', '--porcelain'],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert '.fractal' not in status
    # lifting the self-ignore exposes the dir to git again
    fractal.core.worktree.seed_ignore_remove(node_dir)
    assert fractal.core.worktree.seed_tracked(node_dir) is True
    status = subprocess.run(
        ['git', 'status', '--porcelain'],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert '.fractal/' in status


# ------ helpers


def _git_repo(tmp_path: pathlib.Path) -> pathlib.Path:
    """Create a bare-bones git repo (enough for ``exclude_update`` to resolve)."""
    repo = tmp_path / 'repo'
    repo.mkdir()
    subprocess.run(
        ['git', 'init', '-b', 'main'],
        cwd=repo,
        capture_output=True,
        check=True,
    )
    return repo


@pytest.mark.skipif(sys.platform != 'darwin', reason='clonefile is APFS-only')
def test_clone_cache_dirs_clones_missing_and_skips_unusable(
    tmp_path: pathlib.Path,
) -> None:
    """Configured cache dirs clone in; every unusable entry skips silently.

    The clone runs after the child node is registered, so a raise would fail
    a spawn whose node already exists -- an absent source, an existing target
    (a warm cache the node has since diverged), and an entry escaping the
    worktree must each degrade to a skip, leaving the worktree to re-derive
    the cache exactly as it would have without the clone.
    """
    repo = tmp_path / 'repo'
    (repo / 'lean' / '.lake').mkdir(parents=True)
    (repo / 'lean' / '.lake' / 'artifact.olean').write_text('built', encoding='utf-8')
    (tmp_path / 'outside').mkdir()
    worktree_dir = tmp_path / 'child'
    worktree_dir.mkdir()
    fractal.core.worktree.clone_cache_dirs(
        repo_dir=repo,
        worktree_dir=worktree_dir,
        dirs=['lean/.lake', 'missing/.cache', '../outside', '/etc'],
    )
    # the configured dir arrived with its content; every other entry skipped
    clone = worktree_dir / 'lean' / '.lake' / 'artifact.olean'
    assert clone.read_text(encoding='utf-8') == 'built'
    assert not (worktree_dir / 'missing').exists()
    assert not (worktree_dir / 'outside').exists()
    # no temp residue anywhere under the worktree (asserted by shape, so a
    # change to the temp naming cannot quietly void the check)
    assert not list(worktree_dir.rglob('*.tmp'))
    # an existing target is never overwritten
    clone.write_text('diverged', encoding='utf-8')
    fractal.core.worktree.clone_cache_dirs(
        repo_dir=repo,
        worktree_dir=worktree_dir,
        dirs=['lean/.lake'],
    )
    assert clone.read_text(encoding='utf-8') == 'diverged'
