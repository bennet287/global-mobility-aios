"""Test the ``fractal.core.plan`` module."""

from __future__ import annotations

import pytest

from fractal.core.node import Node

__all__ = [
    'test_plan_init_seeds_heading_and_lists',
    'test_plan_init_rejects_unsafe_name',
    'test_plan_rejects_malformed_iter_ref',
]


def test_plan_init_seeds_heading_and_lists(node_with_db: Node) -> None:
    """``Plans.init`` seeds the H1; ``Plans.list`` resolves an iteration's plans by run.iter."""
    node = node_with_db

    # one iteration writes two plans, each stamped at its own time
    auth = node.plans.init(
        iter_ref='12.5',
        name='add_auth',
        title='Add auth layer',
        timestamp='2026-06-27T14:03:11.000Z',
    )
    db = node.plans.init(
        iter_ref='12.5',
        name='refactor_db',
        timestamp='2026-06-27T14:05:42.000Z',
    )

    # the H1 carries the run.iter and the title (de-slugged when omitted)
    assert auth.read_text(encoding='utf-8').startswith('# 12.5 Add auth layer\n')
    assert db.read_text(encoding='utf-8').startswith('# 12.5 Refactor Db\n')

    # a later iteration's plans belong to a different run.iter
    later = node.plans.init(iter_ref='12.6', name='ship')

    # list resolves by the run.iter segment, across differing timestamps
    listed = node.plans.list(iter_ref='12.5')
    assert set(listed) == {auth, db}
    assert later not in listed


def test_plan_init_rejects_unsafe_name(node_with_db: Node) -> None:
    """``Plans.init`` validates the slug at the filesystem boundary."""
    node = node_with_db
    with pytest.raises(ValueError, match='Invalid plan name'):
        node.plans.init(iter_ref='1.1', name='../escape')


@pytest.mark.parametrize('iter_ref', ['x/../../escape', '12/5', '*', '12.5.1'])
def test_plan_rejects_malformed_iter_ref(node_with_db: Node, iter_ref: str) -> None:
    """``Plans`` refuses a non-``run.iter`` iteration reference.

    ``init`` interpolates it into the plan filename and ``list`` into a glob
    pattern, so a traversal or metacharacter value must be refused, not
    written outside ``plans/`` or matched against every plan.
    """
    node = node_with_db
    with pytest.raises(ValueError, match='Invalid iteration reference'):
        node.plans.init(iter_ref=iter_ref, name='plan')
    with pytest.raises(ValueError, match='Invalid iteration reference'):
        node.plans.list(iter_ref=iter_ref)
