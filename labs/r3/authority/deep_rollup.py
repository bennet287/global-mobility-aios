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


def _load(path: Path) -> dict[str, Any]:
    verify_result(path)
    return json.loads(path.read_text(encoding="utf-8"))


def _has(
    artifacts: list[dict[str, Any]],
    candidate: str,
    experiment: str,
    predicate,
) -> bool:
    return any(
        item.get("candidate") == candidate
        and item.get("experiment") == experiment
        and predicate(item)
        for item in artifacts
    )


def build_rollup(run_id: str, paths: list[Path]) -> dict[str, Any]:
    validate_run_id(run_id)
    artifacts = [_load(path) for path in paths]

    gates = {
        "openfga_correctness": any(
            item.get("candidate") == "openfga"
            and item.get("scenario_count") == 120
            and item.get("failures") == 0
            and isinstance(item.get("outcomes"), list)
            for item in artifacts
        ),
        "opa_correctness": any(
            item.get("candidate") == "opa"
            and item.get("scenario_count") == 120
            and item.get("failures") == 0
            and isinstance(item.get("outcomes"), list)
            for item in artifacts
        ),
        "cedar_real_cli": any(
            item.get("candidate") == "cedar"
            and item.get("scenario_count", 0) >= 76
            and item.get("failures") == 0
            and item.get("reference_fallback_count") == 0
            and item.get("real_cedar_execution_count") == item.get("scenario_count")
            for item in artifacts
        ),
        "openfga_native_features": _has(
            artifacts,
            "openfga",
            "t2-t3-t8-native-feature-depth",
            lambda item: item.get("failures") == 0
            and item.get("feature_coverage", {}).get("relationship_graph") is True
            and item.get("feature_coverage", {}).get("list_objects") is True
            and item.get("feature_coverage", {}).get("revocation") is True
            and item.get("feature_coverage", {}).get("derived_store_rebuild") is True,
        ),
        "opa_native_features": _has(
            artifacts,
            "opa",
            "t2-t3-t8-native-feature-depth",
            lambda item: item.get("failures") == 0
            and item.get("feature_coverage", {}).get("canonical_data_document") is True
            and item.get("feature_coverage", {}).get("hot_data_update") is True
            and item.get("feature_coverage", {}).get("rollback") is True,
        ),
        "openfga_generated_properties": _has(
            artifacts,
            "openfga",
            "t6-generated-metamorphic-differential",
            lambda item: item.get("failures") == 0
            and item.get("iterations", 0) >= 2000
            and not item.get("minimal_counterexamples"),
        ),
        "opa_generated_properties": _has(
            artifacts,
            "opa",
            "t6-generated-metamorphic-differential",
            lambda item: item.get("failures") == 0
            and item.get("iterations", 0) >= 2000
            and not item.get("minimal_counterexamples"),
        ),
        "static_controls": any(
            item.get("candidate") == "aios-authority-static-controls"
            and item.get("invariants", {}).get("passed") == 12
            and item.get("mutations", {}).get("detected") == 10
            and item.get("failures") == 0
            for item in artifacts
        ),
        "openfga_chaos": _has(
            artifacts,
            "openfga",
            "adapter-chaos-matrix",
            lambda item: item.get("failures") == 0,
        ),
        "opa_chaos": _has(
            artifacts,
            "opa",
            "adapter-chaos-matrix",
            lambda item: item.get("failures") == 0,
        ),
    }

    unauthorized = sum(
        int(item.get("unauthorized_canonical_effects", 0)) for item in artifacts
    )
    critical = sum(int(item.get("critical_failures", 0)) for item in artifacts)

    result: dict[str, Any] = {
        "contract_version": CONTRACT_VERSION,
        "r3_run_id": run_id,
        "candidate": "authority-deep-rollup",
        "candidate_version": "v1",
        "git_sha": _git_sha(),
        "environment": "synthetic-isolated-real-engines",
        "experiment": "authority-deep-r3-rollup",
        "test_tiers": ["T0", "T1", "T2", "T3", "T5", "T6", "T8"],
        "scenario_count": len(gates),
        "passes": sum(1 for value in gates.values() if value),
        "failures": sum(1 for value in gates.values() if not value),
        "critical_failures": critical,
        "unauthorized_canonical_effects": unauthorized,
        "gates": gates,
        "remaining_depth": [
            "openfga_conditions",
            "opa_bundle_lifecycle",
            "cedar_typed_entities_and_schema",
            "authority_security_integration",
            "cross_component_integration",
        ],
        "decision_candidate": "CONTINUE_R3_WITH_SPECIFIC_GAP",
        "artifacts": [
            {
                "candidate": item.get("candidate"),
                "experiment": item.get("experiment"),
                "r3_run_id": item.get("r3_run_id"),
                "result_sha256": item.get("result_sha256"),
            }
            for item in artifacts
        ],
    }
    result["result_sha256"] = fingerprint(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("inputs", nargs="*", type=Path)
    args = parser.parse_args()

    paths = args.inputs or sorted(
        path
        for path in RESULTS_DIR.glob("*.json")
        if "rollup" not in path.name
    )
    if not paths:
        raise SystemExit("no authority evidence inputs found")

    result = build_rollup(args.run_id, paths)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        f"authority deep rollup: {result['passes']}/{result['scenario_count']} gates present; "
        f"remaining={len(result['remaining_depth'])}"
    )
    return 0 if result["failures"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
