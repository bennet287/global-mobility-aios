"""``--iter-timeout`` scopes to the single *active* iteration -- never a sum.

The per-iteration time budget is ``--iter-timeout``:
``Time.remaining(scope='iter')`` reports ``iter_timeout`` minus the wall-clock
elapsed of the **one** ``status='active'`` iteration in the resolved run. It must
never roll up elapsed across *several iterations of a run* nor across *runs* (the
way the cost budget legitimately sums per-run cost). The method-level
``test_time.py`` and CLI ``test_time_remaining.py`` suites only ever
place a single iteration in a single run, so neither exercises the
multi-iteration cases where a partial rollup bug would hide. This file is that
stressor, pinning the active-iteration scoping with two sharply discriminating
scenarios:

- a run that has already cycled through a long completed iteration before the
  active one (a "sum the run's iterations" bug would zero the budget); and
- a sequence of nearly-exhausted-then-ended runs followed by a fresh continue
  (a "sum across runs" rollup would clamp the continue to ``0``).

Uses the in-process ``node_with_db`` fixture and back-dates ``started_at`` to
simulate elapsed time deterministically (no sleeps), mirroring
``test_time.py``.
"""

from __future__ import annotations

from fractal.core.node import Node
from tests._helpers import _age_iter

__all__ = [
    'test_remaining_scopes_to_active_iteration_within_run',
    'test_remaining_does_not_accumulate_across_continues',
]

# a 10-minute per-iteration budget, in the suffix form the loop validates
ITER_TIMEOUT = '10m'
ITER_TIMEOUT_SECONDS = 600.0


# ------ active-iteration scoping


def test_remaining_scopes_to_active_iteration_within_run(node_with_db: Node) -> None:
    """A run's earlier completed iteration does not deplete the active one.

    A single run cycles through many iterations (iter 1 completes, iter 2 starts,
    ...), all sharing one ``run_id``. ``--iter-timeout`` must count down only the
    current ``active`` iteration -- not the sum of every iteration's elapsed in
    the run. Here iter 1 burned ~580s and completed; the active iter 2 has burned
    ~20s. Correct behavior reports ~580s left (iter 2 only); a "sum the run's
    iterations" bug would report ``600 - (580 + 20) = 0``.
    """
    node = node_with_db
    node.config.set('iter_timeout', ITER_TIMEOUT)
    run_id = node.record.run_start()
    # iter 1: long-lived, then completed -- its elapsed must not be charged
    iter1 = node.record.iter_start(run_id=run_id, iter=1)
    _age_iter(node, iter1, 580.0)
    node.record.iter_end(iter_id=iter1, status='completed', exit_code=0)
    # iter 2: the active iteration in the same run, freshly started
    iter2 = node.record.iter_start(run_id=run_id, iter=2)
    _age_iter(node, iter2, 20.0)
    remaining = node.time.remaining(scope='iter')
    # only iter 2 counts: ~580s left, never the run-summed 0
    assert remaining is not None
    assert 578.0 < remaining <= ITER_TIMEOUT_SECONDS - 20.0


def test_remaining_does_not_accumulate_across_continues(node_with_db: Node) -> None:
    """Repeated continues never accumulate elapsed; each gets the full budget.

    The cost budget is an accumulating quantity; the per-iteration time budget is not.
    Two runs each nearly exhaust the per-iteration budget and end, then a third
    run (the continue) starts a fresh iteration. ``--iter-timeout`` auto-resolves
    to that live run and reports ~585s left -- the full budget minus only its own
    ~15s. A rollup that summed elapsed across runs would sum ``590 + 590 + 15``
    and clamp the continue to ``0``.
    """
    node = node_with_db
    node.config.set('iter_timeout', ITER_TIMEOUT)
    # two prior runs, each nearly exhausted then cleanly ended
    for iter in (1, 2):
        run_id = node.record.run_start()
        iter_id = node.record.iter_start(run_id=run_id, iter=iter)
        _age_iter(node, iter_id, 590.0)
        node.record.iter_end(iter_id=iter_id, status='completed', exit_code=0)
        node.record.run_end(run_id=run_id, status='completed', exit_code=0)
    # continue: a fresh run + iteration, only ~15s elapsed
    continued = node.record.run_start()
    iter3 = node.record.iter_start(run_id=continued, iter=3)
    _age_iter(node, iter3, 15.0)
    remaining = node.time.remaining(scope='iter')
    # the continue gets the full budget back, not the across-run-summed 0
    assert remaining is not None
    assert 583.0 < remaining <= ITER_TIMEOUT_SECONDS - 15.0
