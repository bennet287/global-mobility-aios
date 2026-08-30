from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from labs.r3.common.generate_fixtures import (
    ATTACK_CATEGORIES,
    build_attack_corpus,
    build_authority_corpus,
)
from labs.r3.common.harness import (
    CONTRACT_VERSION,
    evaluate_reference,
    fingerprint,
    run_reference_corpus,
    summarize_outcomes,
    validate_run_id,
    validate_security_findings,
)


COMMON_ROOT = Path(__file__).resolve().parents[1]


def test_authority_corpus_has_120_deterministic_scenarios() -> None:
    corpus = build_authority_corpus()

    assert corpus["contract_version"] == CONTRACT_VERSION
    assert corpus["scenario_count"] == 120
    assert len({item["scenario_id"] for item in corpus["scenarios"]}) == 120
    assert fingerprint(corpus) == fingerprint(build_authority_corpus())


def test_reference_oracle_matches_every_committed_expectation() -> None:
    corpus = build_authority_corpus()
    outcomes = run_reference_corpus(corpus)

    assert len(outcomes) == 120
    assert all(outcome["passed"] for outcome in outcomes)
    assert all(not outcome["unauthorized_canonical_effects"] for outcome in outcomes)


def test_capability_never_implies_authority_for_any_action() -> None:
    corpus = build_authority_corpus()
    scenarios = [
        scenario
        for scenario in corpus["scenarios"]
        if "capability_without_authority" in scenario["tags"]
    ]

    assert len(scenarios) == 20
    assert all(scenario["expected"]["decision"] == "DENY" for scenario in scenarios)
    assert all(
        scenario["expected"]["reason_class"] == "AUTHORITY_MISSING"
        for scenario in scenarios
    )


@pytest.mark.parametrize(
    ("mutation", "expected_reason"),
    [
        ({"technical_capability": False}, "CAPABILITY_MISSING"),
        ({"context": {"known_action": False}}, "UNKNOWN_ACTION"),
        ({"context": {"same_tenant": False}}, "CROSS_TENANT"),
        ({"context": {"self_grant_attempt": True}}, "SELF_ESCALATION"),
    ],
)
def test_constitutional_mutations_fail_closed(
    mutation: dict[str, object], expected_reason: str
) -> None:
    request = copy.deepcopy(build_authority_corpus()["scenarios"][0]["request"])
    if "context" in mutation:
        request["context"].update(mutation["context"])
    else:
        request.update(mutation)

    observed = evaluate_reference(request)

    assert observed.decision == "DENY"
    assert observed.reason_class == expected_reason


def test_attack_corpus_covers_all_18_owned_categories() -> None:
    corpus = build_attack_corpus()

    assert corpus["attack_count"] == 18
    assert {item["category"] for item in corpus["attacks"]} == {
        code for code, _, _ in ATTACK_CATEGORIES
    }
    assert all(
        all(value == 0 for value in attack["expected"].values())
        for attack in corpus["attacks"]
    )


def test_severity_and_hold_rules_are_machine_enforced() -> None:
    validate_security_findings(
        [
            {
                "severity": "SEV-0",
                "disposition": "REJECT",
                "hold_trigger": None,
            },
            {
                "severity": "SEV-3",
                "disposition": "HOLD_WITH_TRIGGER",
                "hold_trigger": "re-evaluate after upstream v2.0",
            },
        ]
    )
    with pytest.raises(ValueError, match="SEV-0"):
        validate_security_findings(
            [{"severity": "SEV-0", "disposition": "ADVANCE_TO_R4"}]
        )
    with pytest.raises(ValueError, match="hold_trigger"):
        validate_security_findings(
            [{"severity": "SEV-3", "disposition": "HOLD_WITH_TRIGGER"}]
        )


def test_result_manifest_is_fingerprinted_and_zero_effect() -> None:
    corpus = build_authority_corpus()
    outcomes = run_reference_corpus(corpus)

    result = summarize_outcomes(
        run_id="authority-20260901-001",
        candidate="reference",
        candidate_version="v1",
        git_sha="0" * 40,
        corpus=corpus,
        outcomes=outcomes,
    )

    assert result["passes"] == 120
    assert result["failures"] == 0
    assert result["critical_failures"] == 0
    assert result["unauthorized_canonical_effects"] == 0
    assert len(result["corpus_sha256"]) == 64
    assert len(result["result_sha256"]) == 64


def test_run_id_requires_lane_date_and_sequence() -> None:
    validate_run_id("mcp-20260901-001")
    with pytest.raises(ValueError, match="invalid r3_run_id"):
        validate_run_id("latest")


def test_versioned_contracts_are_valid_json_with_unique_ids() -> None:
    contract_paths = sorted((COMMON_ROOT / "contracts").glob("*.schema.json"))
    contracts = [json.loads(path.read_text(encoding="utf-8")) for path in contract_paths]

    assert len(contracts) == 6
    assert len({contract["$id"] for contract in contracts}) == 6
    assert all(contract["$schema"].endswith("draft/2020-12/schema") for contract in contracts)


def test_committed_fixtures_match_deterministic_generators() -> None:
    authority = json.loads(
        (COMMON_ROOT / "fixtures" / "authority_corpus.v1.json").read_text(
            encoding="utf-8"
        )
    )
    attacks = json.loads(
        (COMMON_ROOT / "fixtures" / "attack_corpus.v1.json").read_text(
            encoding="utf-8"
        )
    )

    assert authority == build_authority_corpus()
    assert attacks == build_attack_corpus()
