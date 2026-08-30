from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from labs.r3.authority.invariants import invariant_summary
from labs.r3.authority.policy_mutations import mutation_summary
from labs.r3.common.harness import CONTRACT_VERSION, fingerprint, validate_run_id


def _git_sha() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def build_static_evidence(run_id: str) -> dict[str, object]:
    validate_run_id(run_id)
    invariants = invariant_summary()
    mutations = mutation_summary()
    failures = int(invariants["failed"]) + int(mutations["escaped"])
    checks = len(invariants["items"]) + len(mutations["items"])
    result: dict[str, object] = {
        "contract_version": CONTRACT_VERSION,
        "r3_run_id": run_id,
        "candidate": "aios-authority-static-controls",
        "candidate_version": "v1",
        "git_sha": _git_sha(),
        "environment": "synthetic-isolated",
        "experiment": "invariants-and-policy-mutations",
        "scenario_count": checks,
        "passes": checks - failures,
        "failures": failures,
        "critical_failures": 0,
        "unauthorized_canonical_effects": 0,
        "invariants": invariants,
        "mutations": mutations,
        "decision_candidate": (
            "ADVANCE_TO_R4"
            if failures == 0
            else "CONTINUE_R3_WITH_SPECIFIC_GAP"
        ),
    }
    result["result_sha256"] = fingerprint(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    result = build_static_evidence(args.run_id)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        "authority static controls: "
        f"{result['passes']}/{result['scenario_count']} passed"
    )
    return 0 if result["failures"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
