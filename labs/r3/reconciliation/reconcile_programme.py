from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from labs.r3.common.verify_results import verify_result


MANIFEST = Path(__file__).resolve().parent / "execution_manifest.v2.json"


def _git_head(path: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _load_verified_artifacts(root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    artifacts: list[dict[str, Any]] = []
    invalid: list[str] = []
    for path in sorted(root.rglob("*.json")):
        try:
            verify_result(path)
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            invalid.append(f"{path}:{type(exc).__name__}")
            continue
        payload["_path"] = str(path)
        artifacts.append(payload)
    return artifacts, invalid


def _haystack(item: dict[str, Any]) -> str:
    return " ".join(
        str(item.get(key, "")).lower()
        for key in ("candidate", "experiment", "candidate_version")
    )


def _matches_group(item: dict[str, Any], markers: list[str]) -> bool:
    text = _haystack(item)
    return any(marker.lower() in text for marker in markers)


def _clean(item: dict[str, Any], expected_head: str) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if item.get("git_sha") != expected_head:
        reasons.append("git_sha_mismatch")
    if item.get("execution_blocked") is True:
        reasons.append("execution_blocked")
    if int(item.get("failures", 0)) != 0:
        reasons.append("failures")
    if int(item.get("critical_failures", 0)) != 0:
        reasons.append("critical_failures")
    if int(item.get("unauthorized_canonical_effects", 0)) != 0:
        reasons.append("unauthorized_canonical_effects")
    return not reasons, reasons


def reconcile(
    *,
    manifest: dict[str, Any],
    worktrees: dict[str, Path],
    evidence_root: Path,
) -> dict[str, Any]:
    artifacts, invalid_artifacts = _load_verified_artifacts(evidence_root)
    branch_snapshots: dict[str, Any] = {}
    global_defects: list[str] = [f"invalid_artifact:{item}" for item in invalid_artifacts]

    for physical, config in manifest["physical_branches"].items():
        path = worktrees.get(physical)
        actual = _git_head(path) if path else None
        expected = config["head"]
        status = "MATCH" if actual == expected else ("MISSING" if actual is None else "MISMATCH")
        branch_snapshots[physical] = {
            "branch": config["branch"],
            "expected_head": expected,
            "actual_head": actual,
            "status": status,
        }
        if status != "MATCH":
            global_defects.append(f"branch_snapshot:{physical}:{status.lower()}")

    logical_results: dict[str, Any] = {}
    for lane, config in manifest["logical_lanes"].items():
        physical = config["physical_branch"]
        expected_head = manifest["physical_branches"][physical]["head"]
        groups: dict[str, Any] = {}

        for group, markers in config["required_evidence_groups"].items():
            matching = [item for item in artifacts if _matches_group(item, markers)]
            audited = []
            clean_exact = []
            for item in matching:
                clean, reasons = _clean(item, expected_head)
                audited.append({
                    "path": item["_path"],
                    "git_sha": item.get("git_sha"),
                    "r3_run_id": item.get("r3_run_id"),
                    "result_sha256": item.get("result_sha256"),
                    "clean": clean,
                    "reasons": reasons,
                })
                if clean:
                    clean_exact.append(item)

            if clean_exact:
                chosen = clean_exact[-1]
                groups[group] = {
                    "status": "PASS",
                    "artifact": chosen["_path"],
                    "r3_run_id": chosen.get("r3_run_id"),
                    "result_sha256": chosen.get("result_sha256"),
                    "audited_runs": audited,
                }
            else:
                status = "FAILED_OR_BLOCKED" if matching else "PENDING"
                groups[group] = {
                    "status": status,
                    "markers": markers,
                    "audited_runs": audited,
                }
                global_defects.append(f"evidence:{lane}:{group}:{status.lower()}")

        branch_ok = branch_snapshots[physical]["status"] == "MATCH"
        groups_ok = all(item["status"] == "PASS" for item in groups.values())
        logical_results[lane] = {
            "physical_branch": physical,
            "status": "PASS" if branch_ok and groups_ok else "PENDING_OR_FAILED",
            "groups": groups,
        }

    grand = manifest["grand_trial"]
    grand_physical = grand["physical_branch"]
    grand_head = manifest["physical_branches"][grand_physical]["head"]
    grand_matches = [
        item for item in artifacts
        if item.get("experiment") == grand["experiment"]
    ]
    grand_clean = []
    grand_audit = []
    for item in grand_matches:
        clean, reasons = _clean(item, grand_head)
        required_count_ok = int(item.get("evidence", {}).get("required_lane_count", 0)) == int(grand["required_lane_count"])
        if not required_count_ok:
            reasons.append("required_lane_count_mismatch")
            clean = False
        if int(item.get("passes", 0)) != 1:
            reasons.append("grand_trial_not_passed")
            clean = False
        grand_audit.append({
            "path": item["_path"],
            "git_sha": item.get("git_sha"),
            "clean": clean,
            "reasons": reasons,
        })
        if clean:
            grand_clean.append(item)

    if not grand_clean:
        global_defects.append("grand_trial:no_clean_exact_head_v2_result")

    snapshot_valid = all(item["status"] == "MATCH" for item in branch_snapshots.values())
    lanes_pass = all(item["status"] == "PASS" for item in logical_results.values())
    eligible = snapshot_valid and lanes_pass and bool(grand_clean) and not invalid_artifacts

    return {
        "contract_version": "gmai.r3.reconciliation.v2",
        "programme": manifest["programme"],
        "snapshot_valid": snapshot_valid,
        "branch_snapshots": branch_snapshots,
        "logical_lanes": logical_results,
        "invalid_artifacts": invalid_artifacts,
        "grand_trial": {
            "status": "PASS" if grand_clean else "PENDING_OR_FAILED",
            "audited_runs": grand_audit,
        },
        "defects": sorted(set(global_defects)),
        "r4_evidence_eligible": eligible,
        "decision": "ELIGIBLE_FOR_R4_DECISION" if eligible else "CONTINUE_R3_EVIDENCE",
        "production_adoption_authorized": False,
    }


def _worktree(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("expected physical_branch=path")
    name, raw_path = value.split("=", 1)
    return name, Path(raw_path).resolve()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--worktree", action="append", type=_worktree, default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    worktrees = dict(args.worktree)
    expected = set(manifest["physical_branches"])
    unknown = sorted(set(worktrees) - expected)
    if unknown:
        raise SystemExit(f"unknown physical worktree names: {unknown}")

    result = reconcile(
        manifest=manifest,
        worktrees=worktrees,
        evidence_root=args.evidence_root.resolve(),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "R3 reconciliation: "
        f"snapshot_valid={result['snapshot_valid']} "
        f"grand_trial={result['grand_trial']['status']} "
        f"decision={result['decision']}"
    )
    return 0 if result["r4_evidence_eligible"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
