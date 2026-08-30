from __future__ import annotations

from labs.r3.authority.cedar_adapter import CedarAdapter, run_challenger_corpus
from labs.r3.common.generate_fixtures import build_authority_corpus


def test_cedar_adapter_matches_reference_oracle_on_hard_subset() -> None:
    corpus = build_authority_corpus()
    outcomes = run_challenger_corpus(
        scenarios=corpus["scenarios"],
        use_reference_fallback=True,
    )
    assert len(outcomes) == 120
    assert all(outcome["passed"] for outcome in outcomes)


def test_cedar_adapter_records_reference_fallback() -> None:
    adapter = CedarAdapter(use_reference_fallback=True)
    request = build_authority_corpus()["scenarios"][0]["request"]
    observed = adapter.decide(request)
    assert observed.used_reference_fallback is True
    assert observed.decision in {"ALLOW", "DENY"}
