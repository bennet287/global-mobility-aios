from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from labs.r3.common.harness import CONTRACT_VERSION, fingerprint, validate_run_id
from labs.r3.common.verify_results import verify_result


RESULTS_DIR = Path(__file__).resolve().parent / "results"


def _git_sha() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _load_verified(path: Path) -> dict[str, Any]:
    verify_result(path)
    return json.loads(path.read_text(encoding="utf-8"))


def _has(
    artifacts: list[dict[str, Any]],
    *,
    candidate: str,
    predicate,
) -> bool:
    return any(
        artifact.get("candidate") == candidate and predicate(artifact)
        for artifact in artifacts
    )


def build_rollup(
    *,
    run_id: str,
    input_paths: list[Path],
) -> dict[str, Any]:
    validate_run_id(run_id)
    artifacts = [_load_verified(path) for path in input_paths]

    coverage = {
        "openfga_correctness_120": _has(
            artifacts,
            candidate="openfga",
            predicate=lambda item: item.get("scenario_count") == 120
            and item.get("failures") == 0
            and isinstance(item.get("outcomes"), list),
        ),
        "opa_correctness_120": _has(
            artifacts,
            candidate="opa",
            predicate=lambda item: item.get("scenario_count") == 120
            and item.get("failures") == 0
            and isinstance(item.get("outcomes"), list),
        ),
        "openfga_benchmark_10000": _has(
            artifacts,
            candidate="openfga",
            predicate=lambda item: item.get("measured_requests", 0) >= 10000
            and item.get("errors") == 0,
        ),
        "opa_benchmark_10000": _has(
            artifacts,
            candidate="opa",
            predicate=lambda item: item.get("measured_requests", 0) >= 10000
            and item.get("errors") == 0,
        ),
        "openfga_real_outage_fail_closed": _has(
            artifacts,
            candidate="openfga",
            predicate=lambda item: item.get("experiment") == "engine-unavailable"
            and item.get("passed") is True
            and item.get("observed_decision") == "DENY",
        ),
        "opa_real_outage_fail_closed": _has(
            artifacts,
            candidate="opa",
            predicate=lambda item: item.get("experiment") == "engine-unavailable"
            and item.get("passed") is True
            and item.get("observed_decision") == "DENY",
        ),
        "openfga_adapter_chaos": _has(
            artifacts,
            candidate="openfga",
            predicate=lambda item: item.get("experiment") == "adapter-chaos-matrix"
            and item.get("failures") == 0,
        ),
        "opa_adapter_chaos": _has(
            artifacts,
            candidate="opa",
            predicate=lambda item: item.get("experiment") == "adapter-chaos-matrix"
            and item.get("failures") == 0,
        ),
        "cedar_real_hard_subset": _has(
            artifacts,
            candidate="cedar",
            predicate=lambda item: item.get("scenario_count", 0) >= 76
            and item.get("failures") == 0
            and item.get("reference_fallback_count") == 0
            and item.get("real_cedar_execution_count")
            == item.get("scenario_count"),
        ),
        "invariants_12_and_mutations_10": _has(
            artifacts,
            candidate="aios-authority-static-controls",
            predicate=lambda item: item.get("invariants", {}).get("passed") == 12
            and item.get("invariants", {}).get("failed") == 0
            and item.get("mutations", {}).get("detected") == 10
            and item.get("mutations", {}).get("escaped") == 0,
        ),
    }

    unauthorized_effects = sum(
        int(item.get("unauthorized_canonical_effects", 0)) for item in artifacts
    )
    critical_failures = sum(
        int(item.get("critical_failures", 0)) for item in artifacts
    )
    coverage_complete = all(coverage.values())
    result: dict[str, Any] = {
        "contract_version": CONTRACT_VERSION,
        "r3_run_id": run_id,
        "candidate": "authority-lane-rollup",
        "candidate_version": "v1",
        "git_sha": _git_sha(),
        "environment": "synthetic-isolated-plus-local-engines",
        "experiment": "authority-r3-unified-rollup",
        "scenario_count": len(coverage),
        "passes": sum(1 for value in coverage.values() if value),
        "failures": sum(1 for value in coverage.values() if not value),
        "critical_failures": critical_failures,
        "unauthorized_canonical_effects": unauthorized_effects,
        "coverage": coverage,
        "artifacts": [
            {
                "r3_run_id": item.get("r3_run_id"),
                "candidate": item.get("candidate"),
                "result_sha256": item.get("result_sha256"),
            }
            for item in artifacts
        ],
        "decision_candidate": (
            "ADVANCE_TO_R4"
            if coverage_complete
            and unauthorized_effects == 0
            and critical_failures == 0
            else "CONTINUE_R3_WITH_SPECIFIC_GAP"
        ),
    }
    result["result_sha256"] = fingerprint(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("inputs", nargs="*", type=Path)
    args = parser.parse_args()

    inputs = args.inputs or sorted(
        path
        for path in RESULTS_DIR.glob("*.json")
        if "rollup" not in path.name
    )
    if not inputs:
        raise SystemExit("no authority evidence inputs found")

    result = build_rollup(run_id=args.run_id, input_paths=inputs)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        "authority rollup: "
        f"{result['passes']}/{result['scenario_count']} coverage gates passed; "
        f"disposition={result['decision_candidate']}"
    )
    return 0 if result["decision_candidate"] == "ADVANCE_TO_R4" else 2


if __name__ == "__main__":
    raise SystemExit(main())
