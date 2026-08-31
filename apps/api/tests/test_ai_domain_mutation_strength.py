from __future__ import annotations

from scripts.check_ai_domain_mutation_strength import run_mutation_strength_gate


def test_ai_domain_mutation_strength_gate_kills_all_declared_mutants() -> None:
    result = run_mutation_strength_gate()

    assert result["contract_version"] == "aios-ai-domain-mutation-strength.v1"
    assert result["status"] == "PASS"
    assert result["mutation_count"] >= 8
    assert result["killed_count"] == result["mutation_count"]
    assert result["survived_count"] == 0


def test_mutation_strength_gate_preserves_proof_boundaries() -> None:
    result = run_mutation_strength_gate()

    assert result["mutation_engine"] == "first-party-bounded-semantic-source-mutation"
    assert result["external_mutation_engine_adopted"] is False
    assert result["professional_review_status_effect"] == "NONE"
    assert result["live_model_security_claim"] is False
    assert result["fuzzing_claim"] is False
    assert result["red_team_runtime_claim"] is False


def test_every_declared_mutant_has_a_passing_baseline_and_is_killed() -> None:
    result = run_mutation_strength_gate()

    for mutation in result["mutations"]:
        assert mutation["baseline_probe_passed"] is True
        assert mutation["mutant_probe_passed"] is False
        assert mutation["status"] == "KILLED"
