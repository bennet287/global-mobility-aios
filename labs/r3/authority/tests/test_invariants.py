from __future__ import annotations

from labs.r3.authority.invariants import evaluate_corpus_invariants, invariant_summary


def test_all_corpus_invariants_pass() -> None:
    summary = invariant_summary()
    assert summary["failed"] == 0
    assert summary["passed"] == 12


def test_invariant_i01_detects_self_grant() -> None:
    results = evaluate_corpus_invariants()
    i01 = next(r for r in results if r.invariant_id == "I01")
    assert i01.passed


def test_invariant_i07_detects_expired_delegation() -> None:
    results = evaluate_corpus_invariants()
    i07 = next(r for r in results if r.invariant_id == "I07")
    assert i07.passed


def test_invariant_summary_has_expected_shape() -> None:
    summary = invariant_summary()
    assert summary["passed"] >= 0
    assert summary["failed"] >= 0
    assert len(summary["items"]) == 12
