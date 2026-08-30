from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

from labs.r3.common.generate_fixtures import build_authority_corpus
from labs.r3.common.harness import evaluate_reference


@dataclass(frozen=True)
class MutationResult:
    mutation_id: str
    description: str
    detected: bool
    failing_scenario_id: str | None


MUTATIONS: list[tuple[str, str, Any]] = [
    (
        "M01",
        "Remove human approval from critical government submission.",
        {"action": "government_application.submit", "human_approval": False},
    ),
    (
        "M02",
        "Remove authority presence from critical government submission.",
        {"action": "government_application.submit", "context": {"authority_present": False}},
    ),
    (
        "M03",
        "Wrong jurisdiction on Austria-specific action.",
        {"action": "government_application.submit", "jurisdiction": "DE"},
    ),
    (
        "M04",
        "Cross-tenant access without tenant match.",
        {"resource": {"tenant_id": "tenant:beta"}, "context": {"same_tenant": False}},
    ),
    (
        "M05",
        "Expired delegation still treated as active.",
        {"delegation": {"status": "expired"}},
    ),
    (
        "M06",
        "Revoked delegation still treated as active.",
        {"delegation": {"status": "revoked"}},
    ),
    (
        "M07",
        "Unknown action treated as known.",
        {"action": "super_admin.execute"},
    ),
    (
        "M08",
        "Agent grants authority to itself.",
        {
            "action": "authority.grant",
            "actor": {"id": "agent:austria-regulatory"},
            "acting_for": "agent:austria-regulatory",
        },
    ),
    (
        "M09",
        "Provider claimed authority satisfies canonical requirement.",
        {
            "action": "government_application.submit",
            "context": {"authority_present": False, "provider_claimed_authority": True},
        },
    ),
    (
        "M10",
        "Skill advertised satisfies canonical authority requirement.",
        {
            "action": "government_application.submit",
            "context": {"authority_present": False, "skill_advertised": True},
        },
    ),
]


def _apply_mutation(request: dict[str, Any], mutation: dict[str, Any]) -> dict[str, Any]:
    mutated = copy.deepcopy(request)

    def _merge(base: Any, override: Any) -> Any:
        if isinstance(override, dict) and isinstance(base, dict):
            for key, value in override.items():
                base[key] = _merge(base.get(key), value)
            return base
        return override

    return _merge(mutated, mutation)


def evaluate_mutations() -> list[MutationResult]:
    corpus = build_authority_corpus()
    results: list[MutationResult] = []
    for mutation_id, description, mutation in MUTATIONS:
        detected = False
        failing_scenario_id: str | None = None
        for scenario in corpus["scenarios"]:
            mutated = _apply_mutation(scenario["request"], mutation)
            observed = evaluate_reference(mutated)
            # A dangerous mutation is detected if the reference oracle still denies
            # the mutated request. If it allows, the mutation escaped detection.
            if observed.decision == "ALLOW":
                detected = False
                failing_scenario_id = scenario["scenario_id"]
                break
        else:
            detected = True
        results.append(
            MutationResult(
                mutation_id=mutation_id,
                description=description,
                detected=detected,
                failing_scenario_id=failing_scenario_id,
            )
        )
    return results


def mutation_summary() -> dict[str, Any]:
    results = evaluate_mutations()
    return {
        "detected": sum(1 for r in results if r.detected),
        "escaped": sum(1 for r in results if not r.detected),
        "items": [
            {
                "mutation_id": r.mutation_id,
                "description": r.description,
                "detected": r.detected,
                "failing_scenario_id": r.failing_scenario_id,
            }
            for r in results
        ],
    }
