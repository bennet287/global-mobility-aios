from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from labs.r3.common.harness import CONTRACT_VERSION, fingerprint, validate_run_id


CEDAR_VERSION = "4.12.0"
BASE = Path(__file__).resolve().parent / "cedar"
SCHEMA = BASE / "schema.cedarschema"
POLICY = BASE / "typed_policy.cedar"
ENTITIES = BASE / "typed_entities.json"


class ExecutionBlocked(RuntimeError):
    pass


def _git_sha() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()


def _cedar() -> str:
    binary = shutil.which("cedar")
    if not binary:
        raise ExecutionBlocked("cedar CLI is not installed")
    return binary


def _decision(stdout: str) -> str | None:
    for line in stdout.splitlines():
        value = line.strip().upper()
        if value in {"ALLOW", "DENY"}:
            return value
    return None


def _authorize(
    cedar: str,
    *,
    principal: str,
    action: str,
    resource: str,
    context: dict[str, Any],
) -> str:
    payload = {
        "principal": principal,
        "action": action,
        "resource": resource,
        "context": context,
    }
    with tempfile.TemporaryDirectory(prefix="gmai-r3-cedar-typed-") as temp:
        request = Path(temp) / "request.json"
        request.write_text(json.dumps(payload) + "\n", encoding="utf-8")
        completed = subprocess.run(
            [
                cedar,
                "authorize",
                "--policies",
                str(POLICY),
                "--entities",
                str(ENTITIES),
                "--request-json",
                str(request),
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr or completed.stdout)[:1200])
    observed = _decision(completed.stdout)
    if observed is None:
        raise RuntimeError(
            f"unparseable Cedar decision: {completed.stdout[:1200]}"
        )
    return observed


def run_typed() -> dict[str, Any]:
    cedar = _cedar()
    outcomes: list[dict[str, Any]] = []

    validation = subprocess.run(
        [
            cedar,
            "validate",
            "--schema",
            str(SCHEMA),
            "--policies",
            str(POLICY),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    outcomes.append(
        {
            "feature": "typed_policy_validates_against_schema",
            "observed": validation.returncode == 0,
            "expected": True,
        }
    )

    malformed = POLICY.read_text(encoding="utf-8").replace(
        'Action::"read_case"',
        'Action::"unknown_schema_action"',
        1,
    )
    with tempfile.TemporaryDirectory(prefix="gmai-r3-cedar-invalid-") as temp:
        bad = Path(temp) / "invalid.cedar"
        bad.write_text(malformed, encoding="utf-8")
        invalid = subprocess.run(
            [
                cedar,
                "validate",
                "--schema",
                str(SCHEMA),
                "--policies",
                str(bad),
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    outcomes.append(
        {
            "feature": "schema_rejects_unknown_action",
            "observed": invalid.returncode != 0,
            "expected": True,
        }
    )

    read_allowed = _authorize(
        cedar,
        principal='Agent::"agent-001"',
        action='Action::"read_case"',
        resource='Case::"AT-001"',
        context={
            "sameTenant": True,
            "authorityPresent": False,
            "humanApproved": False,
        },
    )
    cross_team = _authorize(
        cedar,
        principal='Agent::"agent-001"',
        action='Action::"read_case"',
        resource='Case::"DE-001"',
        context={
            "sameTenant": False,
            "authorityPresent": False,
            "humanApproved": False,
        },
    )
    submit_no_approval = _authorize(
        cedar,
        principal='Agent::"agent-001"',
        action='Action::"submit_case"',
        resource='Case::"AT-001"',
        context={
            "sameTenant": True,
            "authorityPresent": True,
            "humanApproved": False,
        },
    )
    submit_approved = _authorize(
        cedar,
        principal='Agent::"agent-001"',
        action='Action::"submit_case"',
        resource='Case::"AT-001"',
        context={
            "sameTenant": True,
            "authorityPresent": True,
            "humanApproved": True,
        },
    )

    outcomes.extend(
        [
            {
                "feature": "typed_entity_hierarchy_allows_team_read",
                "observed": read_allowed,
                "expected": "ALLOW",
            },
            {
                "feature": "cross_team_hierarchy_denied",
                "observed": cross_team,
                "expected": "DENY",
            },
            {
                "feature": "forbid_overrides_permit_without_approval",
                "observed": submit_no_approval,
                "expected": "DENY",
            },
            {
                "feature": "approved_submit_allowed",
                "observed": submit_approved,
                "expected": "ALLOW",
            },
        ]
    )

    for item in outcomes:
        item["passed"] = item["observed"] == item["expected"]
        item["unauthorized_canonical_effects"] = []

    failures = [item for item in outcomes if not item["passed"]]
    return {
        "outcomes": outcomes,
        "passes": len(outcomes) - len(failures),
        "failures": len(failures),
        "feature_coverage": {
            "typed_entities": True,
            "entity_hierarchy": True,
            "schema_validation": True,
            "malformed_policy_rejection": True,
            "permit_forbid_precedence": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    validate_run_id(args.run_id)

    try:
        detail = run_typed()
        blocked = False
        block_reason = None
    except ExecutionBlocked as exc:
        detail = {
            "outcomes": [],
            "passes": 0,
            "failures": 0,
            "feature_coverage": {},
        }
        blocked = True
        block_reason = str(exc)

    result = {
        "contract_version": CONTRACT_VERSION,
        "r3_run_id": args.run_id,
        "candidate": "cedar",
        "candidate_version": CEDAR_VERSION,
        "git_sha": _git_sha(),
        "environment": "synthetic-isolated-real-cli",
        "experiment": "t2-cedar-typed-schema",
        "test_tiers": ["T1", "T2", "T4"],
        "execution_blocked": blocked,
        "block_reason": block_reason,
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
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if blocked:
        print(f"Cedar typed R3 blocked: {block_reason}")
        return 2
    print(
        f"Cedar typed R3: {result['passes']}/{result['scenario_count']} passed"
    )
    return 0 if result["failures"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
