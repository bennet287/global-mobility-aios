from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

import httpx

from labs.r3.common.harness import CONTRACT_VERSION, fingerprint, validate_run_id


OPENFGA_VERSION = "v1.18.1"
MODEL_PATH = Path(__file__).resolve().parent / "openfga" / "conditions_model.json"


def _git_sha() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()


def _post(base_url: str, path: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = httpx.post(
        f"{base_url.rstrip('/')}{path}", json=payload, timeout=5.0
    )
    response.raise_for_status()
    return response.json()


def _record(
    outcomes: list[dict[str, Any]], feature: str, observed: Any, expected: Any
) -> None:
    outcomes.append(
        {
            "feature": feature,
            "observed": observed,
            "expected": expected,
            "passed": observed == expected,
            "unauthorized_canonical_effects": [],
        }
    )


def run_conditions(*, base_url: str) -> dict[str, Any]:
    outcomes: list[dict[str, Any]] = []
    store = _post(base_url, "/stores", {"name": "gmai-r3-openfga-conditions"})
    store_id = str(store["id"])
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    model_result = _post(
        base_url, f"/stores/{store_id}/authorization-models", model
    )
    model_id = str(model_result["authorization_model_id"])

    _post(
        base_url,
        f"/stores/{store_id}/write",
        {
            "writes": {
                "tuple_keys": [
                    {
                        "user": "agent:austria-regulatory",
                        "relation": "viewer",
                        "object": "case:AT-001",
                        "condition": {
                            "name": "non_expired_grant",
                            "context": {
                                "grant_time": "2026-08-30T20:00:00Z",
                                "grant_duration": "1h",
                            },
                        },
                    }
                ]
            },
            "authorization_model_id": model_id,
        },
    )

    def check(current_time: str | None) -> bool:
        payload: dict[str, Any] = {
            "tuple_key": {
                "user": "agent:austria-regulatory",
                "relation": "viewer",
                "object": "case:AT-001",
            },
            "authorization_model_id": model_id,
        }
        if current_time is not None:
            payload["context"] = {"current_time": current_time}
        return bool(
            _post(base_url, f"/stores/{store_id}/check", payload).get("allowed")
        )

    _record(
        outcomes,
        "condition_allows_inside_grant_window",
        check("2026-08-30T20:30:00Z"),
        True,
    )
    _record(
        outcomes,
        "condition_denies_after_expiry",
        check("2026-08-30T21:00:01Z"),
        False,
    )
    _record(
        outcomes,
        "missing_condition_context_fails_closed",
        check(None),
        False,
    )

    list_before = _post(
        base_url,
        f"/stores/{store_id}/list-objects",
        {
            "type": "case",
            "relation": "viewer",
            "user": "agent:austria-regulatory",
            "context": {"current_time": "2026-08-30T20:30:00Z"},
            "authorization_model_id": model_id,
        },
    )
    list_after = _post(
        base_url,
        f"/stores/{store_id}/list-objects",
        {
            "type": "case",
            "relation": "viewer",
            "user": "agent:austria-regulatory",
            "context": {"current_time": "2026-08-30T21:00:01Z"},
            "authorization_model_id": model_id,
        },
    )
    _record(
        outcomes,
        "list_objects_respects_condition",
        (
            "case:AT-001" in list_before.get("objects", []),
            "case:AT-001" in list_after.get("objects", []),
        ),
        (True, False),
    )

    failures = [item for item in outcomes if not item["passed"]]
    return {
        "outcomes": outcomes,
        "passes": len(outcomes) - len(failures),
        "failures": len(failures),
        "feature_coverage": {
            "conditional_relationship": True,
            "temporal_context": True,
            "missing_context_fail_closed": True,
            "conditional_list_objects": True,
            "canonical_authority_ownership": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:18080")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    validate_run_id(args.run_id)

    detail = run_conditions(base_url=args.base_url)
    result = {
        "contract_version": CONTRACT_VERSION,
        "r3_run_id": args.run_id,
        "candidate": "openfga",
        "candidate_version": OPENFGA_VERSION,
        "git_sha": _git_sha(),
        "environment": "synthetic-isolated-real-engine",
        "experiment": "t2-openfga-conditions",
        "test_tiers": ["T2", "T3"],
        "scenario_count": len(detail["outcomes"]),
        "passes": detail["passes"],
        "failures": detail["failures"],
        "critical_failures": 0,
        "unauthorized_canonical_effects": 0,
        "feature_coverage": detail["feature_coverage"],
        "outcomes": detail["outcomes"],
        "decision_candidate": "CONTINUE_R3_WITH_SPECIFIC_GAP",
    }
    result["result_sha256"] = fingerprint(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        f"OpenFGA conditions: {result['passes']}/{result['scenario_count']} passed"
    )
    return 0 if result["failures"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
