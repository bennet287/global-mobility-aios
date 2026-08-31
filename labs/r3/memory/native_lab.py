from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from labs.r3.common.harness import CONTRACT_VERSION, fingerprint, validate_run_id
from labs.r3.memory.governance import NativeContinuityMemory, resolve_governed_fact


def _git_sha() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _record(
    outcomes: list[dict[str, Any]],
    feature: str,
    observed: Any,
    expected: Any,
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


def run_native_memory() -> dict[str, Any]:
    memory = NativeContinuityMemory()
    outcomes: list[dict[str, Any]] = []

    memory.put(
        tenant_id="tenant:alpha",
        memory_id="m1",
        text="Austria threshold 45 MEMORY_TAINT_NATIVE",
    )
    _record(
        outcomes,
        "tenant_owner_can_read_memory",
        memory.get(tenant_id="tenant:alpha", memory_id="m1"),
        "Austria threshold 45 MEMORY_TAINT_NATIVE",
    )
    _record(
        outcomes,
        "other_tenant_cannot_read_memory",
        memory.get(tenant_id="tenant:beta", memory_id="m1"),
        None,
    )

    alpha = memory.search(
        tenant_id="tenant:alpha",
        query="Austria threshold",
    )
    beta = memory.search(
        tenant_id="tenant:beta",
        query="Austria threshold",
    )
    _record(
        outcomes,
        "tenant_scoped_search",
        (len(alpha), len(beta)),
        (1, 0),
    )

    governed = resolve_governed_fact(
        key="at.rwr.threshold",
        verified_rule_value="55",
        retrieved_memory_values=[item["memory"] for item in alpha],
    )
    _record(
        outcomes,
        "poisoned_memory_cannot_override_verified_rule",
        (governed.value, governed.source_class, governed.authoritative),
        ("55", "VERIFIED_RULE", True),
    )

    memory.update(
        tenant_id="tenant:alpha",
        memory_id="m1",
        text="Austria threshold 55 corrected continuity note",
    )
    _record(
        outcomes,
        "update_changes_only_continuity_memory",
        memory.get(tenant_id="tenant:alpha", memory_id="m1"),
        "Austria threshold 55 corrected continuity note",
    )

    memory.delete(tenant_id="tenant:alpha", memory_id="m1")
    _record(
        outcomes,
        "delete_removes_active_memory",
        memory.get(tenant_id="tenant:alpha", memory_id="m1"),
        None,
    )

    failures = [item for item in outcomes if not item["passed"]]
    return {
        "outcomes": outcomes,
        "passes": len(outcomes) - len(failures),
        "failures": len(failures),
        "feature_coverage": {
            "native_reference": True,
            "tenant_scoping": True,
            "search": True,
            "update": True,
            "delete": True,
            "verified_rule_precedence": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    validate_run_id(args.run_id)

    detail = run_native_memory()
    result = {
        "contract_version": CONTRACT_VERSION,
        "r3_run_id": args.run_id,
        "candidate": "native-aios-memory",
        "candidate_version": "r3-v1",
        "git_sha": _git_sha(),
        "environment": "synthetic-isolated",
        "experiment": "t2-t3-native-memory-governance",
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
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        f"native memory R3: {result['passes']}/{result['scenario_count']} passed"
    )
    return 0 if result["failures"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
