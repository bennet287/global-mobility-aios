from __future__ import annotations

from labs.r3.authority.policy_mutations import evaluate_mutations, mutation_summary


def test_all_dangerous_mutations_are_detected() -> None:
    summary = mutation_summary()
    assert summary["escaped"] == 0, summary
    assert summary["detected"] == 10


def test_mutation_summary_contains_ten_items() -> None:
    summary = mutation_summary()
    assert len(summary["items"]) == 10


def test_self_grant_mutation_is_detected() -> None:
    results = evaluate_mutations()
    m08 = next(r for r in results if r.mutation_id == "M08")
    assert m08.detected
