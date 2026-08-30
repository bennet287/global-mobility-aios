from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from labs.r3.common.harness import CONTRACT_VERSION, fingerprint, validate_run_id
from labs.r3.orchestration.common import NativeDurableReference, framework_result


def _git_sha() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def run_native() -> dict:
    first = NativeDurableReference()
    first.apply("cmd-1", "DOCUMENTS_REQUESTED")
    checkpoint = first.snapshot()

    resumed = NativeDurableReference()
    resumed.apply("cmd-1", "DOCUMENTS_REQUESTED")
    resumed.apply("cmd-2", "SOURCE_UPDATED")
    duplicate_suppressed = not resumed.apply("cmd-2", "SOURCE_UPDATED")

    before_approval = resumed.snapshot()
    try:
        resumed.apply("cmd-complete-early", "COMPLETE")
        early_blocked = False
    except ValueError:
        early_blocked = True

    resumed.apply("cmd-3", "HUMAN_APPROVED")
    resumed.apply("cmd-4", "COMPLETE")
    final = resumed.snapshot()

    result = framework_result(
        candidate="native-aios-reference",
        final_status=final["status"],
        framework_events=final["events"],
        resumed_after_pause=checkpoint["status"] == "WAITING_DOCUMENTS",
        duplicate_suppressed=duplicate_suppressed,
        human_gate_observed=(
            early_blocked and before_approval["human_approval"] is False
        ),
    )
    result["final_snapshot"] = final
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    validate_run_id(args.run_id)

    observed = run_native()
    passed = all(
        [
            observed["final_status"] == "COMPLETED",
            observed["resumed_after_pause"],
            observed["duplicate_suppressed"],
            observed["human_gate_observed"],
            observed["canonical_authority_effects"] == 0,
        ]
    )
    result = {
        "contract_version": CONTRACT_VERSION,
        "r3_run_id": args.run_id,
        "candidate": "native-aios-reference",
        "candidate_version": "r3-v1",
        "git_sha": _git_sha(),
        "environment": "synthetic-isolated",
        "experiment": "t2-t3-t5-t8-durable-orchestration",
        "test_tiers": ["T2", "T3", "T5", "T8"],
        "scenario_count": 1,
        "passes": int(passed),
        "failures": int(not passed),
        "critical_failures": 0,
        "unauthorized_canonical_effects": 0,
        "outcomes": [observed],
        "decision_candidate": "CONTINUE_R3_WITH_SPECIFIC_GAP",
    }
    result["result_sha256"] = fingerprint(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"native orchestration R3: {result['passes']}/1 passed")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
