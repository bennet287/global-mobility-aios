"""End-to-end tests for the public ``fractal plan`` CLI.

Drives the real ``fractal`` console script against a worker node, exercising
the agent-facing plan commands: ``plan init`` (seed a plan file with its H1) and
``plan list`` (resolve an iteration's plans by the loop-supplied ``{run.iter}``
reference). That reference reaches the CLI through the ``$ITER_REF`` env var the
loop exports, so the agent passes only ``--name``.
"""

from __future__ import annotations

import pathlib

import pytest

from tests._helpers import _git

from .conftest import _run

__all__ = ['test_plan_init_seeds_heading_and_list_finds_it']


@pytest.fixture(scope='module')
def task(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    """Return a worker node worktree, bootstrapped once via the real CLI.

    Module-scoped for the expensive bootstrap; the module's single test
    owns the node outright, so there is no sharing to collide on.
    """
    root = tmp_path_factory.mktemp('fractal_plan')
    _git(root, 'init', '-b', 'main')
    _git(root, 'config', 'user.email', 'plan@test.local')
    _git(root, 'config', 'user.name', 'plan')
    (root / 'README.md').write_text('# plan\n', encoding='utf-8')
    wiki = root / 'wiki'
    wiki.mkdir()
    (wiki / '_index.md').write_text(
        '---\nname: wiki\n---\n# wiki\n\n***\n',
        encoding='utf-8',
    )
    _git(root, 'add', '-A')
    _git(root, 'commit', '-m', 'init')
    assert _run(root, 'init').returncode == 0
    assert _run(root, 'node', 'init', 'task', '--agent', 'claude').returncode == 0
    return root / '.worktrees' / 'main.task'


def test_plan_init_seeds_heading_and_list_finds_it(task: pathlib.Path) -> None:
    """``plan init`` seeds the H1 and ``plan list`` finds it via the env ref."""
    # the agent passes only --name; the run.iter ref comes from the loop env
    created = _run(task, 'plan', 'init', '--name', 'add_widget', ITER_REF='3.2')
    assert created.returncode == 0, created.stderr
    path = pathlib.Path(created.stdout.strip())
    assert path.name.endswith('-3.2-add_widget.md')
    assert path.read_text(encoding='utf-8').startswith('# 3.2 Add Widget\n')

    # list resolves this iteration's plans by the env run.iter ref
    listed = _run(task, 'plan', 'list', ITER_REF='3.2')
    assert listed.returncode == 0, listed.stderr
    assert listed.stdout.strip() == str(path)

    # an empty iteration keeps stdout path-only; the notice goes to stderr
    empty = _run(task, 'plan', 'list', ITER_REF='9.9')
    assert empty.returncode == 0, empty.stderr
    assert empty.stdout == ''
    assert 'No plans for this iteration.' in empty.stderr
