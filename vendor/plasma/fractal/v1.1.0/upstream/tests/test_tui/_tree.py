"""Deterministic fractal-tree builder for the TUI suite.

Builds a real repository -- ``git init`` + ``fractal init`` + ``Node.init``
per branch -- then seeds run/iteration/step history, signals, events, and
radio traffic exclusively through the core APIs, so any core drift breaks the
fixture loudly. Three devices make every byte deterministic: a frozen core
clock (:func:`deterministic_core` patches ``utc_now`` so timestamps are
written correctly the first time), a counting radio-uuid mint, and one generic
:func:`pin` for the few SQL-DEFAULT columns the clock cannot reach.
"""

from __future__ import annotations

import contextlib
import dataclasses
import datetime as dt
import hashlib
import os
import pathlib
import sqlite3
from collections.abc import Iterator
from typing import Any
from unittest import mock

from fractal.core.node import Node
from fractal.core.radio import Radio
from tests._helpers import _git

__all__ = [
    'REF',
    'REF_DT',
    'NOW_EPOCH',
    'Clock',
    'deterministic_core',
    'pin',
    'session_for',
    'NodeSpec',
    'SPECS',
    'active_branches',
    'build_tree',
    'build_pair',
]

# the fixed instant every stored timestamp hangs off; live-elapsed tests
# inject NOW_EPOCH (ten minutes later) as the data layer's clock
REF = '2026-06-07T18:00:00.000000Z'
REF_DT = dt.datetime(2026, 6, 7, 18, 0, 0, tzinfo=dt.UTC)
NOW_EPOCH = REF_DT.timestamp() + 600.0

# the stock loop pipeline (PREPARE..COMMIT) the seeded iterations replay
_STEP_NAMES = ('PREPARE', 'PLAN', 'EXECUTE', 'REVIEW', 'COMMIT')
_STEP_SECONDS = (43.0, 66.0, 186.0, 75.0, 30.0)

# claude nodes carry the full six-cap matrix; codex carries no cost caps
_CLAUDE_CONFIG = {
    'model': 'opus 4.8',
    'max_iters': 10,
    'timeout': '2h',
    'iter_timeout': '30m',
    'step_timeout': '10m',
    'max_cost': 5.0,
    'max_iter_cost': 1.0,
    'max_step_cost': 0.5,
}
_CODEX_CONFIG = {'model': 'gpt-5.1', 'max_iters': 10}


class Clock:
    """A settable stand-in for ``utc_now`` (one instant per call site)."""

    def __init__(self: Clock) -> None:
        """Initialize at the reference instant."""
        self._at = REF_DT

    def at(self: Clock, seconds_ago: float) -> None:
        """Move the clock to ``seconds_ago`` before the reference instant."""
        self._at = REF_DT - dt.timedelta(seconds=seconds_ago)

    def __call__(self: Clock) -> str:
        """Return the current instant in ``utc_now`` format."""
        return self._at.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'


@contextlib.contextmanager
def deterministic_core() -> Iterator[Clock]:
    """Freeze core's clock and the radio's uuid mint for a seeding block."""
    clock = Clock()
    counter = iter(range(1, 10_000))

    def mint(nbytes: int) -> str:
        return f'{next(counter):0{2 * nbytes}x}'

    with (
        mock.patch('fractal.util.time.utc_now', clock),
        mock.patch('fractal.core.radio.secrets.token_hex', mint),
    ):
        yield clock


def pin(db_path: pathlib.Path, table: str, where: dict, **columns: Any) -> None:
    """Back-date SQL-DEFAULT columns the frozen clock cannot reach.

    Args:
        db_path: The node database file.
        table: The table to update.
        where: Equality predicates selecting the rows.
        **columns: Column values to set.

    """
    sets = ', '.join(f'{column} = ?' for column in columns)
    match = ' AND '.join(f'{column} = ?' for column in where)
    connection = sqlite3.connect(db_path)
    try:
        connection.execute(
            f'UPDATE {table} SET {sets} WHERE {match}',
            (*columns.values(), *where.values()),
        )
        connection.commit()
    finally:
        connection.close()


def session_for(branch: str, run: int, it: int) -> str:
    """Return a deterministic uuid-shaped session id for a branch's iteration."""
    head = hashlib.sha1(branch.encode(), usedforsecurity=False).hexdigest()[:8]
    return f'{head}-0000-4000-8000-{run:06d}{it:06d}'


@dataclasses.dataclass(frozen=True)
class NodeSpec:
    """One node in the canonical tree."""

    name: str  # leaf name; nesting via `children`
    status: str = 'idle'  # the node's final lifecycle status
    signal: str = ''  # ''|'stop'|'finish'|'pause' pending while active
    agent: str = 'claude'
    detached: bool = False
    runs: str = 'auto'  # 'auto' shapes history from status; 'none'
    children: tuple[NodeSpec, ...] = ()


# the canonical 10-node tree: every lifecycle status, both pending signals,
# codex, detached, deep nesting, and a user root with no runs
SPECS = (
    NodeSpec(
        name='alpha',
        status='active',
        children=(
            NodeSpec(
                name='deep',
                status='active',
                children=(NodeSpec(name='leaf', status='completed'),),
            ),
            NodeSpec(name='stopper', status='active', signal='stop'),
        ),
    ),
    NodeSpec(name='beta', status='active', signal='finish', agent='codex'),
    NodeSpec(name='gamma', status='active', detached=True),
    NodeSpec(name='delta', status='stopped'),
    NodeSpec(name='epsilon', status='exited'),
    NodeSpec(name='zeta', status='killed'),
)


def active_branches() -> tuple[str, ...]:
    """The canonical tree's branches whose final status is ``active``."""
    return tuple(branch for branch, spec in _walk(SPECS) if spec.status == 'active')


def build_tree(root: pathlib.Path) -> None:
    """Build the canonical deterministic tree at ``root``.

    A real repository: ``git init`` + ``fractal init`` (the user node) +
    ``Node.init`` per spec, then per-status history, signals, events, and
    radio traffic -- all timestamped by the frozen clock.
    """
    _git_repo(root)
    with deterministic_core() as clock:
        clock.at(7200.0)
        user = Node(root)
        user.init(path='.', agent='claude', user=True)
        nodes = {'main': user}
        # spawn every spec breadth-first; the parent is identified the way a
        # real spawning node is -- via the _NODE caller environment variable
        pending = [('main', spec) for spec in SPECS]
        while pending:
            parent_branch, spec = pending.pop(0)
            branch = f'{parent_branch}.{spec.name}'
            config = dict(_CODEX_CONFIG if spec.agent == 'codex' else _CLAUDE_CONFIG)
            caller = {'_NODE': str(nodes[parent_branch].node_dir)}
            with mock.patch.dict(os.environ, caller):
                user.init(
                    name=spec.name,
                    agent=spec.agent,
                    detached=spec.detached,
                    **config,
                )
            worktree = root / '.worktrees' / branch
            nodes[branch] = Node(worktree)
            pending.extend((branch, child) for child in spec.children)
        _pin_setup_events(nodes)
        # seed each node's history + terminal state
        for branch, spec in _walk(SPECS):
            if spec.runs == 'auto' and spec.status != 'idle':
                _seed_runs(nodes[branch], branch, spec, clock)
            nodes[branch].status_set(spec.status)
            if spec.signal:
                nodes[branch].record.signal_set(spec.signal)
        _seed_radio(nodes, clock)


def build_pair(root: pathlib.Path, *, agent: str = 'claude') -> None:
    """Build a minimal writable tree: a user root plus one child ``main.alpha``.

    The small fixture for tests that write (actions, chat, poller) --
    the canonical tree stays read-only.
    """
    _git_repo(root)
    user = Node(root)
    user.init(path='.', agent='claude', user=True)
    user.init(name='alpha', agent=agent)


# ------ helpers


def _stamp(seconds_ago: float) -> str:
    """A core-format timestamp ``seconds_ago`` before the reference instant."""
    at = REF_DT - dt.timedelta(seconds=seconds_ago)
    return at.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'


def _central_db(node: Node) -> pathlib.Path:
    """The tree's central database (at the user node; the fixture root is main)."""
    return node.repo_dir / '.fractal' / 'main' / '.db'


def _pin_setup_events(nodes: dict[str, Node]) -> None:
    """Pin every setup event to a distinct instant so logs sort stably.

    init logs init/spawn events from a subprocess (outside the frozen clock)
    and ``events.created_at`` is an SQL DEFAULT besides; the pins land in
    creation order.
    """
    db_path = _central_db(nodes['main'])
    connection = sqlite3.connect(db_path)
    try:
        cursor = connection.execute('SELECT event_id FROM events ORDER BY event_id')
        rows = cursor.fetchall()
    finally:
        connection.close()
    for index, (event_id,) in enumerate(rows):
        pin(
            db_path=db_path,
            table='events',
            where={'event_id': event_id},
            created_at=_stamp(7200.0 - index),
        )


def _git_repo(root: pathlib.Path) -> None:
    """A minimal committed repository (``fractal init`` requires a clean tree)."""
    root.mkdir(parents=True, exist_ok=True)
    _git(root, 'init', '-q', '-b', 'main')
    _git(root, 'config', 'user.email', 'tui@test')
    _git(root, 'config', 'user.name', 'tui')
    (root / 'README.md').write_text('# cockpit tree\n', encoding='utf-8')
    wiki = root / 'wiki'
    wiki.mkdir()
    (wiki / '_index.md').write_text(
        '---\nname: wiki\n---\n# wiki\n\n***\n',
        encoding='utf-8',
    )
    _git(root, 'add', '-A')
    _git(root, 'commit', '-qm', 'init')


def _walk(
    specs: tuple[NodeSpec, ...],
    prefix: str = 'main',
) -> list[tuple[str, NodeSpec]]:
    """Flatten the spec tree into ``(branch, spec)`` pairs, depth-first."""
    result = []
    for spec in specs:
        branch = f'{prefix}.{spec.name}'
        result.append((branch, spec))
        result.extend(_walk(spec.children, branch))
    return result


def _seed_runs(node: Node, branch: str, spec: NodeSpec, clock: Clock) -> None:
    """Shape the node's history from its final status.

    Settled statuses get one closed run; ``active`` gets a completed prior
    run plus a live one open at step 3 (EXECUTE).
    """
    if spec.status == 'active':
        _seed_run(
            node=node,
            branch=branch,
            spec=spec,
            clock=clock,
            run_number=1,
            iters=1,
            start_ago=7000.0,
            status='completed',
            exit_code=0,
        )
        _seed_live_run(node, branch, spec, clock)
        return
    status = spec.status
    exit_code = 1 if status in ('exited', 'killed', 'failed') else 0
    _seed_run(
        node=node,
        branch=branch,
        spec=spec,
        clock=clock,
        run_number=1,
        iters=1,
        start_ago=5400.0,
        status=status,
        exit_code=exit_code,
    )
    # the terminal lifecycle event a real loop records; events.created_at is
    # an SQL DEFAULT the frozen clock cannot reach, so pin it
    event = {'stopped': 'stop', 'killed': 'kill', 'completed': 'finish'}.get(status)
    if event is not None:
        event_id = node.record.event_start(event)
        if event_id is not None:
            node.record.event_end(event_id=event_id, status='completed')
            pin(
                db_path=_central_db(node),
                table='events',
                where={'event_id': event_id},
                created_at=_stamp(3000.0),
            )


def _seed_run(
    node: Node,
    branch: str,
    spec: NodeSpec,
    clock: Clock,
    *,
    run_number: int,
    iters: int,
    start_ago: float,
    status: str,
    exit_code: int,
) -> None:
    """Seed one closed run: ``iters`` settled iterations ending in ``status``."""
    clock.at(start_ago)
    run_id = node.record.run_start()
    at = start_ago
    for iteration in range(1, iters + 1):
        clock.at(at)
        iter_id = node.record.iter_start(run_id=run_id, iter=iteration)
        # a settled SYNC pre-step (step=0) precedes the numbered pipeline
        at = _seed_step(
            node=node,
            branch=branch,
            spec=spec,
            clock=clock,
            run_id=run_id,
            iter_id=iter_id,
            run_number=run_number,
            iteration=iteration,
            step=0,
            at=at,
        )
        cut = status == 'killed'
        for step in range(1, len(_STEP_NAMES) + 1):
            # a killed run is cut mid-pipeline: step 3 dies, 4-5 never run
            if cut and step > 3:
                break
            at = _seed_step(
                node=node,
                branch=branch,
                spec=spec,
                clock=clock,
                run_id=run_id,
                iter_id=iter_id,
                run_number=run_number,
                iteration=iteration,
                step=step,
                at=at,
                killed=cut and step == 3,
            )
        clock.at(at)
        iter_status = 'killed' if cut else 'completed'
        node.record.iter_end(iter_id=iter_id, status=iter_status, exit_code=exit_code)
        _pin_iter_session(node, iter_id, branch, run_number, iteration, spec)
        at -= 30.0
    clock.at(at)
    node.record.run_end(run_id=run_id, status=status, exit_code=exit_code)


def _seed_live_run(node: Node, branch: str, spec: NodeSpec, clock: Clock) -> None:
    """The live run: iteration 1 settled, iteration 2 open at step 3 (EXECUTE)."""
    clock.at(3600.0)
    run_id = node.record.run_start()
    at = 3600.0
    clock.at(at)
    iter_id = node.record.iter_start(run_id=run_id, iter=1)
    for step in range(0, len(_STEP_NAMES) + 1):
        at = _seed_step(
            node=node,
            branch=branch,
            spec=spec,
            clock=clock,
            run_id=run_id,
            iter_id=iter_id,
            run_number=2,
            iteration=1,
            step=step,
            at=at,
        )
    clock.at(at)
    node.record.iter_end(iter_id=iter_id, status='completed', exit_code=0)
    _pin_iter_session(node, iter_id, branch, 2, 1, spec)
    # the open iteration: steps 1-2 settled, step 3 active since `at`
    clock.at(at - 10.0)
    live_iter = node.record.iter_start(run_id=run_id, iter=2)
    at -= 10.0
    for step in (1, 2):
        at = _seed_step(
            node=node,
            branch=branch,
            spec=spec,
            clock=clock,
            run_id=run_id,
            iter_id=live_iter,
            run_number=2,
            iteration=2,
            step=step,
            at=at,
        )
    clock.at(at)
    step_id = node.record.step_start(
        iter_id=live_iter,
        run_id=run_id,
        step=3,
        step_name=_STEP_NAMES[2],
    )
    if spec.agent == 'claude':
        node.record.step_session(
            'claude',
            step_id=step_id,
            model=_CLAUDE_CONFIG['model'],
            session=session_for(branch, 2, 2),
        )


def _seed_step(
    *,
    node: Node,
    branch: str,
    spec: NodeSpec,
    clock: Clock,
    run_id: int,
    iter_id: int,
    run_number: int,
    iteration: int,
    step: int,
    at: float,
    killed: bool = False,
) -> float:
    """One settled step: start at ``at``, run its nominal seconds.

    Records cost + session (claude weaves sessions; codex reports no cost).
    A sync pass (step=0 here) is recorded against the step it precedes --
    step 1.
    """
    clock.at(at)
    name = 'SYNC' if step == 0 else _STEP_NAMES[step - 1]
    stored = 1 if step == 0 else step
    step_id = node.record.step_start(
        iter_id=iter_id,
        run_id=run_id,
        step=stored,
        step_name=name,
    )
    if spec.agent == 'claude':
        node.record.step_session(
            'claude',
            step_id=step_id,
            model=_CLAUDE_CONFIG['model'],
            session=session_for(branch, run_number, iteration),
        )
        node.record.step_cost(step_id=step_id, cost=round(0.02 + 0.02 * step, 2))
    seconds = 20.0 if step == 0 else _STEP_SECONDS[step - 1]
    at -= seconds
    clock.at(at)
    if killed:
        node.record.step_end(step_id=step_id, status='killed', exit_code=1)
    else:
        node.record.step_end(step_id=step_id, status='completed', exit_code=0)
    return at - 5.0


def _pin_iter_session(
    node: Node,
    iter_id: int,
    branch: str,
    run_number: int,
    iteration: int,
    spec: NodeSpec,
) -> None:
    """Pin the deterministic session id the seeded steps carry.

    ``iter_end`` stamps the session from the live ``.session`` map, which is
    absent in a seeded tree.
    """
    if spec.agent != 'claude':
        return
    pin(
        db_path=_central_db(node),
        table='iters',
        where={'iter_id': iter_id},
        session=session_for(branch, run_number, iteration),
    )


def _seed_radio(nodes: dict[str, Node], clock: Clock) -> None:
    """Seed radio traffic on alpha.

    An unread steer, a read note, outbox/public posts, a reply thread, a
    react, and one save into the root's archive.
    """
    root = nodes['main']
    alpha = nodes['main.alpha']
    db_path = _central_db(root)
    root_radio = Radio(root)
    alpha_radio = Radio(alpha)
    # alpha's posts carry the live session that wrote them (the root weaves
    # no session, so its sends stamp NULL)
    alpha.sessions.set('claude', session_for('main.alpha', 2, 2))
    steer, _, _ = root_radio.send(
        node='main.alpha',
        channel='inbox',
        subject='steer',
        data='prioritize the auth work',
        priority=8,
    )
    note, _, _ = root_radio.send(
        node='main.alpha',
        channel='inbox',
        subject='note',
        data='budget approved',
        priority=4,
    )
    status, _, _ = alpha_radio.send(
        channel='outbox',
        subject='status',
        data='iteration 2 underway',
        priority=5,
    )
    alpha_radio.send(
        channel='public',
        subject='hello',
        data='cohort kickoff',
        priority=3,
    )
    # the note is read (alpha's receipt lands); the steer stays unread
    alpha_radio.read(note)
    # a reply thread under the steer; a react + a save on the status post
    root_radio.reply(steer, 'starting now')
    root_radio.react(status, 1)
    root_radio.save(status)
    # pin the SQL-DEFAULT created_at columns to clock-relative instants
    clock.at(0)
    for uuid, ago in ((steer, 500.0), (note, 400.0), (status, 300.0)):
        pin(db_path, 'messages', {'message_uuid': uuid}, created_at=_stamp(ago))
    pin(db_path, 'archive', {'message_uuid': status}, created_at=REF)
    connection = sqlite3.connect(db_path)
    try:
        connection.execute(
            'UPDATE messages SET created_at = ? WHERE subject = ?',
            (REF, 'hello'),
        )
        connection.commit()
    finally:
        connection.close()
