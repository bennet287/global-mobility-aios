from __future__ import annotations

from scripts.check_ai_domain_adversarial_contract import run_adversarial_contract_gate


def _by_key(result: dict[str, object]) -> dict[str, dict[str, object]]:
    return {
        str(item["key"]): item
        for item in result["scenarios"]
        if isinstance(item, dict)
    }


def test_adversarial_contract_gate_passes_all_declared_scenarios() -> None:
    result = run_adversarial_contract_gate()

    assert result["contract_version"] == "aios-ai-domain-adversarial-contract.v1"
    assert result["status"] == "PASS"
    assert result["failed_count"] == 0
    assert result["passed_count"] == result["scenario_count"]
    assert result["scenario_count"] >= 16
    assert result["professional_review_status_effect"] == "NONE"
    assert result["live_model_security_claim"] is False
    assert result["red_team_runtime_claim"] is False


def test_authority_route_source_and_case_mutations_fail_closed() -> None:
    scenarios = _by_key(run_adversarial_contract_gate())

    for key in (
        "authority-escalation",
        "route-substitution",
        "forged-source",
        "duplicate-case",
        "missing-case",
        "invented-classification",
        "empty-source-set",
        "empty-reason",
    ):
        assert scenarios[key]["status"] == "PASS"
        assert scenarios[key]["observed_error"]


def test_corroboration_resists_fake_consensus_and_identity_failure() -> None:
    scenarios = _by_key(run_adversarial_contract_gate())

    assert scenarios["single-provider-is-insufficient"]["actual_candidate"] is False
    assert scenarios["duplicate-provider-is-insufficient"]["actual_candidate"] is False
    assert scenarios["provider-disagreement-fails"]["actual_candidate"] is False
    assert scenarios["identity-mismatch-is-disqualified"]["actual_candidate"] is False
    assert scenarios["structural-failure-is-disqualified"]["actual_candidate"] is False
    assert scenarios["source-label-mismatch-fails"]["actual_candidate"] is False
    assert scenarios["two-distinct-matching-providers-qualify"]["actual_candidate"] is True

    for key in (
        "single-provider-is-insufficient",
        "duplicate-provider-is-insufficient",
        "provider-disagreement-fails",
        "identity-mismatch-is-disqualified",
        "structural-failure-is-disqualified",
        "source-label-mismatch-fails",
        "two-distinct-matching-providers-qualify",
    ):
        assert scenarios[key]["professional_review_status_effect"] == "NONE"


def test_indirect_prompt_injection_is_data_not_authority() -> None:
    scenario = _by_key(run_adversarial_contract_gate())[
        "indirect-prompt-injection-boundary"
    ]

    assert scenario["status"] == "PASS"
    assert scenario["attack_preserved_as_untrusted_data"] is True
    assert scenario["system_boundary_present"] is True
    assert scenario["expected_labels_absent"] is True
    assert "does not claim live-model prompt-injection resistance" in str(
        scenario["note"]
    )
