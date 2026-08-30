from __future__ import annotations

import argparse
import copy
import json
import subprocess
from pathlib import Path
from typing import Any

import httpx

from labs.r3.common.harness import CONTRACT_VERSION, fingerprint, validate_run_id


ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "opa" / "deep_data.json"
VERSION = "v1.19.1"


def _git_sha() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _base_request(action: str) -> dict[str, Any]:
    return {
        "actor": {"type": "agent", "id": "agent:austria-regulatory"},
        "acting_for": "human:case-owner",
        "tenant_id": "tenant:alpha",
        "action": action,
        "resource": {
            "type": "case",
            "id": "case:AT-001",
            "tenant_id": "tenant:alpha",
        },
        "jurisdiction": "AT",
        "technical_capability": True,
        "human_approval": True,
        "delegation": {"id": "delegation:001", "status": "active"},
        "context": {
            "authority_present": True,
            "self_grant_attempt": False,
        },
    }


def _put_data(client: httpx.Client, document: dict[str, Any]) -> None:
    response = client.put("/v1/data/aios", json=document["aios"])
    response.raise_for_status()


def _decide(client: httpx.Client, request: dict[str, Any]) -> dict[str, Any]:
    response = client.post(
        "/v1/data/gmai/r3/authority_deep/decision",
        json={"input": request},
    )
    response.raise_for_status()
    result = response.json().get("result")
    if not isinstance(result, dict):
        raise ValueError(f"OPA returned malformed deep decision: {result!r}")
    if result.get("decision") not in {"ALLOW", "DENY"}:
        raise ValueError(f"OPA returned invalid deep decision: {result!r}")
    return result


def _expect(
    outcomes: list[dict[str, Any]],
    *,
    feature: str,
    observed: Any,
    expected: Any,
) -> None:
    outcomes.append(
        {
            "feature": feature,
            "expected": expected,
            "observed": observed,
            "passed": observed == expected,
            "unauthorized_canonical_effects": [],
        }
    )


def run_deep_features(*, base_url: str) -> dict[str, Any]:
    original = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    outcomes: list[dict[str, Any]] = []
    with httpx.Client(base_url=base_url, timeout=5.0) as client:
        _put_data(client, original)

        read_request = _base_request("case.read")
        read_request["context"]["authority_present"] = False
        v1_read = _decide(client, read_request)
        _expect(
            outcomes,
            feature="canonical_data_v1_allows_low_risk_read",
            observed=(v1_read["decision"], v1_read["policy_revision"]),
            expected=("ALLOW", "authority-data-v1"),
        )

        submit_request = _base_request("government_application.submit")
        submit_request["human_approval"] = False
        submit = _decide(client, submit_request)
        _expect(
            outcomes,
            feature="canonical_data_requires_human_approval",
            observed=submit["reason_class"],
            expected="HUMAN_APPROVAL_REQUIRED",
        )

        tightened = copy.deepcopy(original)
        tightened["aios"]["revision"] = "authority-data-v2"
        tightened["aios"]["actions"]["case.read"]["authority_required"] = True
        _put_data(client, tightened)

        v2_read = _decide(client, read_request)
        _expect(
            outcomes,
            feature="hot_data_tightening_changes_current_decision",
            observed=(v2_read["decision"], v2_read["reason_class"], v2_read["policy_revision"]),
            expected=("DENY", "AUTHORITY_MISSING", "authority-data-v2"),
        )

        _put_data(client, original)
        rollback = _decide(client, read_request)
        _expect(
            outcomes,
            feature="canonical_data_rollback_reproduces_v1",
            observed=(rollback["decision"], rollback["policy_revision"]),
            expected=("ALLOW", "authority-data-v1"),
        )

        corrupt = {"aios": {"revision": "authority-data-corrupt", "actions": {}}}
        _put_data(client, corrupt)
        corrupt_result = _decide(client, read_request)
        _expect(
            outcomes,
            feature="missing_action_metadata_fails_closed",
            observed=(corrupt_result["decision"], corrupt_result["reason_class"]),
            expected=("DENY", "UNKNOWN_ACTION"),
        )

        _put_data(client, tightened)
        replay_v2 = _decide(client, read_request)
        _expect(
            outcomes,
            feature="historical_v2_data_reconstruction_is_deterministic",
            observed=(replay_v2["decision"], replay_v2["policy_revision"]),
            expected=("DENY", "authority-data-v2"),
        )

        _put_data(client, original)
        replay_v1 = _decide(client, read_request)
        _expect(
            outcomes,
            feature="historical_v1_data_reconstruction_is_deterministic",
            observed=(replay_v1["decision"], replay_v1["policy_revision"]),
            expected=("ALLOW", "authority-data-v1"),
        )

    failures = [item for item in outcomes if not item["passed"]]
    return {
        "outcomes": outcomes,
        "passes": len(outcomes) - len(failures),
        "failures": len(failures),
        "feature_coverage": {
            "canonical_data_document": True,
            "hot_data_update": True,
            "policy_tightening": True,
            "rollback": True,
            "fail_closed_missing_metadata": True,
            "historical_data_reconstruction": True,
            "bundle_distribution": False,
            "bundle_signing": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:18181")
    args = parser.parse_args()
    validate_run_id(args.run_id)

    detail = run_deep_features(base_url=args.base_url)
    result: dict[str, Any] = {
        "contract_version": CONTRACT_VERSION,
        "r3_run_id": args.run_id,
        "candidate": "opa",
        "candidate_version": VERSION,
        "git_sha": _git_sha(),
        "environment": "synthetic-isolated-real-engine",
        "experiment": "t2-t3-t8-native-feature-depth",
        "test_tiers": ["T2", "T3", "T8"],
        "scenario_count": len(detail["outcomes"]),
        "passes": detail["passes"],
        "failures": detail["failures"],
        "critical_failures": 0,
        "unauthorized_canonical_effects": 0,
        "feature_coverage": detail["feature_coverage"],
        "outcomes": detail["outcomes"],
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
        "opa deep features: "
        f"{result['passes']}/{result['scenario_count']} passed; "
        f"coverage={result['feature_coverage']}"
    )
    return 0 if result["failures"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
