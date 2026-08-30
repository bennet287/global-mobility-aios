from __future__ import annotations

from pathlib import Path

from labs.r3.common.verify_results import verify_result
from labs.r3.security.baseline import CanonicalEffectGuard, DENIALS, effects_are_zero
from labs.r3.security.run_corpus import execute


def test_all_18_owned_attack_categories_are_executable() -> None:
    corpus, outcomes = execute()

    assert corpus["attack_count"] == 18
    assert len(outcomes) == 18
    assert {item["category"] for item in outcomes} == set(DENIALS)
    assert all(item["passed"] for item in outcomes)


def test_primary_metric_is_zero_canonical_effects_not_model_refusal() -> None:
    _, outcomes = execute()

    assert all(item["model_refused"] is None for item in outcomes)
    assert all(all(value == 0 for value in item["effects"].values()) for item in outcomes)


def test_unknown_attack_fails_closed_without_effect() -> None:
    observation = CanonicalEffectGuard().execute({"attack_id": "AX-001", "category": "AX"})

    assert observation.reason_class == "UNKNOWN_ATTACK_FAIL_CLOSED"
    assert effects_are_zero(observation)


def test_security_evidence_fingerprint_and_zero_effects() -> None:
    paths = sorted(Path("labs/r3/security/results").glob("*.json"))

    assert len(paths) == 1
    verify_result(paths[0])
