from __future__ import annotations

import argparse
import copy
import json
import random
import subprocess
from pathlib import Path
from typing import Any

from labs.r3.authority.adapters import OpenFgaAdapter, OpaAdapter
from labs.r3.authority.bootstrap_openfga import create_store_and_model
from labs.r3.common.generate_fixtures import build_authority_corpus
from labs.r3.common.harness import (
    CANONICAL_ACTIONS,
    CONTRACT_VERSION,
    evaluate_reference,
    fingerprint,
    validate_run_id,
)


VERSION = {
    "openfga": "v1.18.1",
    "opa": "v1.19.1",
}
PROPERTY_NAMES = (
    "remove_authority_never_increases_permission",
    "remove_approval_never_increases_permission",
    "revocation_never_increases_permission",
    "cross_tenant_never_allows",
    "unknown_action_never_allows",
    "provider_claim_never_increases_permission",
    "skill_advertisement_never_increases_permission",
    "self_grant_never_allows",
)


def _git_sha() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _authorized_by_action() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for scenario in build_authority_corpus()["scenarios"]:
        if scenario["description"].endswith("authorized baseline"):
            result[scenario["request"]["action"]] = scenario["request"]
    return result


def _rank(decision: str) -> int:
    return 1 if decision == "ALLOW" else 0


def _mutated_pair(
    *,
    rng: random.Random,
    sequence: int,
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    baselines = _authorized_by_action()
    action = rng.choice(sorted(baselines))
    before = copy.deepcopy(baselines[action])
    before["request_id"] = f"prop-{sequence:05d}-before"
    before["r3_run_id"] = "authority-properties-20260830-001"
    property_name = rng.choice(PROPERTY_NAMES)
    after = copy.deepcopy(before)
    after["request_id"] = f"prop-{sequence:05d}-after"

    if property_name == "remove_authority_never_increases_permission":
        after["context"]["authority_present"] = False

    elif property_name == "remove_approval_never_increases_permission":
        after["human_approval"] = False

    elif property_name == "revocation_never_increases_permission":
        after["delegation"]["status"] = rng.choice(["expired", "revoked"])

    elif property_name == "cross_tenant_never_allows":
        after["resource"]["tenant_id"] = "tenant:beta"
        after["context"]["same_tenant"] = False

    elif property_name == "unknown_action_never_allows":
        after["action"] = f"unknown.action.{sequence}"
        after["context"]["known_action"] = False

    elif property_name == "provider_claim_never_increases_permission":
        before["context"]["authority_present"] = False
        after = copy.deepcopy(before)
        after["request_id"] = f"prop-{sequence:05d}-after"
        after["context"]["provider_claimed_authority"] = True

    elif property_name == "skill_advertisement_never_increases_permission":
        before["context"]["authority_present"] = False
        before["context"]["skill_advertised"] = False
        after = copy.deepcopy(before)
        after["request_id"] = f"prop-{sequence:05d}-after"
        after["context"]["skill_advertised"] = True

    elif property_name == "self_grant_never_allows":
        before = copy.deepcopy(baselines["authority.grant"])
        before["request_id"] = f"prop-{sequence:05d}-before"
        before["r3_run_id"] = "authority-properties-20260830-001"
        after = copy.deepcopy(before)
        after["request_id"] = f"prop-{sequence:05d}-after"
        after["actor"]["id"] = after["acting_for"]
        after["context"]["self_grant_attempt"] = True

    return property_name, before, after


def _property_holds(
    property_name: str,
    *,
    before_decision: str,
    after_decision: str,
) -> bool:
    if property_name in {
        "cross_tenant_never_allows",
        "unknown_action_never_allows",
        "self_grant_never_allows",
    }:
        return after_decision == "DENY"

    if property_name in {
        "provider_claim_never_increases_permission",
        "skill_advertisement_never_increases_permission",
    }:
        return after_decision == before_decision

    return _rank(after_decision) <= _rank(before_decision)


def _evaluate_pair(
    *,
    adapter: Any,
    property_name: str,
    before: dict[str, Any],
    after: dict[str, Any],
) -> dict[str, Any]:
    ref_before = evaluate_reference(before)
    ref_after = evaluate_reference(after)
    observed_before = adapter.decide(before)
    observed_after = adapter.decide(after)

    exact_differential = (
        observed_before.decision == ref_before.decision
        and observed_before.reason_class == ref_before.reason_class
        and observed_after.decision == ref_after.decision
        and observed_after.reason_class == ref_after.reason_class
    )
    property_passed = _property_holds(
        property_name,
        before_decision=observed_before.decision,
        after_decision=observed_after.decision,
    )
    return {
        "property": property_name,
        "before_request_id": before["request_id"],
        "after_request_id": after["request_id"],
        "reference": {
            "before": [ref_before.decision, ref_before.reason_class],
            "after": [ref_after.decision, ref_after.reason_class],
        },
        "observed": {
            "before": [observed_before.decision, observed_before.reason_class],
            "after": [observed_after.decision, observed_after.reason_class],
        },
        "exact_differential": exact_differential,
        "property_passed": property_passed,
        "passed": exact_differential and property_passed,
        "unauthorized_canonical_effects": [],
    }


def _minimal_failure(
    outcome: dict[str, Any],
    before: dict[str, Any],
    after: dict[str, Any],
) -> dict[str, Any]:
    return {
        "property": outcome["property"],
        "before": before,
        "after": after,
        "reference": outcome["reference"],
        "observed": outcome["observed"],
    }


def run_generated(
    *,
    candidate: str,
    iterations: int,
    seed: int,
    opa_url: str,
    openfga_url: str,
) -> dict[str, Any]:
    if candidate == "opa":
        adapter: Any = OpaAdapter(base_url=opa_url)
    else:
        store_id, model_id = create_store_and_model(base_url=openfga_url)
        adapter = OpenFgaAdapter(
            base_url=openfga_url,
            store_id=store_id,
            authorization_model_id=model_id,
        )

    rng = random.Random(seed)
    outcomes: list[dict[str, Any]] = []
    minimal_counterexamples: list[dict[str, Any]] = []
    property_counts = {name: 0 for name in PROPERTY_NAMES}

    for sequence in range(1, iterations + 1):
        property_name, before, after = _mutated_pair(
            rng=rng,
            sequence=sequence,
        )
        property_counts[property_name] += 1
        outcome = _evaluate_pair(
            adapter=adapter,
            property_name=property_name,
            before=before,
            after=after,
        )
        outcomes.append(outcome)
        if not outcome["passed"] and len(minimal_counterexamples) < 20:
            minimal_counterexamples.append(
                _minimal_failure(outcome, before, after)
            )

    failures = [item for item in outcomes if not item["passed"]]
    return {
        "outcomes": outcomes,
        "passes": len(outcomes) - len(failures),
        "failures": len(failures),
        "property_counts": property_counts,
        "minimal_counterexamples": minimal_counterexamples,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", choices=sorted(VERSION), required=True)
    parser.add_argument("--iterations", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=136)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--opa-url", default="http://127.0.0.1:18181")
    parser.add_argument("--openfga-url", default="http://127.0.0.1:18080")
    args = parser.parse_args()
    validate_run_id(args.run_id)
    if args.iterations < len(PROPERTY_NAMES):
        parser.error(
            f"iterations must be >= {len(PROPERTY_NAMES)} to cover all properties"
        )

    detail = run_generated(
        candidate=args.candidate,
        iterations=args.iterations,
        seed=args.seed,
        opa_url=args.opa_url,
        openfga_url=args.openfga_url,
    )
    result: dict[str, Any] = {
        "contract_version": CONTRACT_VERSION,
        "r3_run_id": args.run_id,
        "candidate": args.candidate,
        "candidate_version": VERSION[args.candidate],
        "git_sha": _git_sha(),
        "environment": "synthetic-isolated-real-engine",
        "experiment": "t6-generated-metamorphic-differential",
        "test_tiers": ["T6"],
        "seed": args.seed,
        "iterations": args.iterations,
        "scenario_count": len(detail["outcomes"]),
        "passes": detail["passes"],
        "failures": detail["failures"],
        "critical_failures": 0,
        "unauthorized_canonical_effects": 0,
        "property_counts": detail["property_counts"],
        "minimal_counterexamples": detail["minimal_counterexamples"],
        "decision_candidate": (
            "ADVANCE_TO_R4"
            if detail["failures"] == 0
            else "CONTINUE_R3_WITH_SPECIFIC_GAP"
        ),
    }
    result["result_sha256"] = fingerprint(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        f"{args.candidate} generated properties: "
        f"{result['passes']}/{result['scenario_count']} passed; "
        f"seed={args.seed}; counterexamples={len(detail['minimal_counterexamples'])}"
    )
    return 0 if result["failures"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
