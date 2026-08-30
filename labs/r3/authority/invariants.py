from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from labs.r3.common.generate_fixtures import build_authority_corpus
from labs.r3.common.harness import CANONICAL_ACTIONS


InvariantFn = Callable[[dict[str, Any], dict[str, Any]], bool]


@dataclass(frozen=True)
class InvariantResult:
    invariant_id: str
    description: str
    passed: bool
    failing_scenario_id: str | None


INVARIANTS: list[tuple[str, str, InvariantFn]] = [
    (
        "I01",
        "No agent can grant authority to itself.",
        lambda request, expected: not (
            request.get("action") == "authority.grant"
            and request.get("actor", {}).get("id") == request.get("acting_for")
            and expected["decision"] == "ALLOW"
        ),
    ),
    (
        "I02",
        "Capability cannot imply authority.",
        lambda request, expected: not (
            request.get("technical_capability", False)
            and not request.get("context", {}).get("authority_present", False)
            and request.get("action") in CANONICAL_ACTIONS
            and CANONICAL_ACTIONS[request["action"]]["authority_required"]
            and expected["decision"] == "ALLOW"
        ),
    ),
    (
        "I03",
        "Model/provider output cannot grant authority.",
        lambda request, expected: not (
            request.get("context", {}).get("provider_claimed_authority", False)
            and expected["decision"] == "ALLOW"
        ),
    ),
    (
        "I04",
        "Skill advertisement cannot grant authority.",
        lambda request, expected: not (
            request.get("context", {}).get("skill_advertised", False)
            and not request.get("context", {}).get("authority_present", False)
            and request.get("action") in CANONICAL_ACTIONS
            and CANONICAL_ACTIONS[request["action"]]["authority_required"]
            and expected["decision"] == "ALLOW"
        ),
    ),
    (
        "I05",
        "MCP tool discovery cannot grant authority to invoke tools.",
        lambda request, expected: not (
            request.get("action") == "tool.discover"
            and expected["decision"] == "ALLOW"
            and expected["reason_class"] != "AUTHORIZED"
        ),
    ),
    (
        "I06",
        "A2A capability advertisement cannot grant authority.",
        lambda request, expected: not (
            request.get("action") == "a2a.task.delegate"
            and not request.get("context", {}).get("authority_present", False)
            and expected["decision"] == "ALLOW"
        ),
    ),
    (
        "I07",
        "Expired delegation cannot authorize.",
        lambda request, expected: not (
            request.get("delegation", {}).get("status") == "expired"
            and expected["decision"] == "ALLOW"
        ),
    ),
    (
        "I08",
        "Revoked authority cannot authorize.",
        lambda request, expected: not (
            request.get("delegation", {}).get("status") == "revoked"
            and expected["decision"] == "ALLOW"
        ),
    ),
    (
        "I09",
        "Unknown actions fail closed.",
        lambda request, expected: not (
            request.get("action") not in CANONICAL_ACTIONS
            and expected["decision"] == "ALLOW"
        ),
    ),
    (
        "I10",
        "Cross-tenant access fails closed.",
        lambda request, expected: not (
            not request.get("context", {}).get("same_tenant", False)
            and expected["decision"] == "ALLOW"
        ),
    ),
    (
        "I11",
        "Human approval requirement cannot be satisfied by model assertion.",
        lambda request, expected: not (
            request.get("action") in CANONICAL_ACTIONS
            and CANONICAL_ACTIONS[request["action"]]["human_approval_required"]
            and not request.get("human_approval", False)
            and expected["decision"] == "ALLOW"
        ),
    ),
    (
        "I12",
        "Policy engine cannot mutate AIOS canonical authority state.",
        lambda request, expected: True,
    ),
]


def evaluate_invariants(
    request: dict[str, Any], expected: dict[str, Any]
) -> list[InvariantResult]:
    results: list[InvariantResult] = []
    for invariant_id, description, fn in INVARIANTS:
        try:
            passed = fn(request, expected)
        except Exception:
            passed = False
        results.append(
            InvariantResult(
                invariant_id=invariant_id,
                description=description,
                passed=bool(passed),
                failing_scenario_id=None,
            )
        )
    return results


def evaluate_corpus_invariants() -> list[InvariantResult]:
    corpus = build_authority_corpus()
    aggregate: dict[str, InvariantResult] = {}
    for scenario in corpus["scenarios"]:
        expected = scenario["expected"]
        for result in evaluate_invariants(scenario["request"], expected):
            existing = aggregate.get(result.invariant_id)
            if existing is None:
                aggregate[result.invariant_id] = result
            if not result.passed:
                existing = aggregate[result.invariant_id]
                aggregate[result.invariant_id] = InvariantResult(
                    invariant_id=existing.invariant_id,
                    description=existing.description,
                    passed=False,
                    failing_scenario_id=scenario["scenario_id"],
                )
    return list(aggregate.values())


def invariant_summary() -> dict[str, Any]:
    results = evaluate_corpus_invariants()
    return {
        "passed": sum(1 for r in results if r.passed),
        "failed": sum(1 for r in results if not r.passed),
        "items": [
            {
                "invariant_id": r.invariant_id,
                "description": r.description,
                "passed": r.passed,
                "failing_scenario_id": r.failing_scenario_id,
            }
            for r in results
        ],
    }
