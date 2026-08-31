from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from labs.r3.common.harness import fingerprint


ROOT = Path(__file__).resolve().parent
PLAN_PATH = ROOT / "programme_execution_plan.v1.json"
INVENTORY_PATH = ROOT / "programme_inventory.v1.json"


@dataclass(frozen=True)
class Worktree:
    path: Path
    head: str
    branch: str | None


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _git(
    cwd: Path,
    *args: str,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=check,
        capture_output=True,
        text=True,
    )


def parse_worktree_porcelain(text: str) -> list[Worktree]:
    worktrees: list[Worktree] = []
    current: dict[str, str] = {}

    def flush() -> None:
        if not current.get("worktree") or not current.get("HEAD"):
            current.clear()
            return
        branch_ref = current.get("branch")
        branch = (
            branch_ref.removeprefix("refs/heads/")
            if branch_ref
            else None
        )
        worktrees.append(
            Worktree(
                path=Path(current["worktree"]),
                head=current["HEAD"],
                branch=branch,
            )
        )
        current.clear()

    for line in text.splitlines():
        if not line.strip():
            flush()
            continue
        key, _, value = line.partition(" ")
        if key in {"worktree", "HEAD", "branch"}:
            current[key] = value.strip()

    flush()
    return worktrees


def discover_worktrees(repo_root: Path) -> dict[str, Worktree]:
    completed = _git(repo_root, "worktree", "list", "--porcelain")
    return {
        worktree.branch: worktree
        for worktree in parse_worktree_porcelain(completed.stdout)
        if worktree.branch
    }


def _current_branch(repo_root: Path) -> str:
    return _git(
        repo_root,
        "branch",
        "--show-current",
    ).stdout.strip()


def _current_head(repo_root: Path) -> str:
    return _git(repo_root, "rev-parse", "HEAD").stdout.strip()


def expected_head(
    *,
    branch: str,
    inventory: dict[str, Any],
    runtime_head: str,
) -> str:
    if branch == "radar/r3-runtime":
        return runtime_head
    return str(inventory["branch_heads"][branch])


def lane_python(lane: str) -> str:
    env_name = "GMAI_R3_PYTHON_" + re.sub(
        r"[^A-Z0-9]+",
        "_",
        lane.upper(),
    )
    return os.getenv(env_name, sys.executable)


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not slug or not slug[0].isalpha():
        slug = "r3-" + slug
    return slug


def _run_id(step_id: str, run_date: str, sequence: int) -> str:
    return f"{_safe_slug(step_id)}-{run_date}-{sequence:03d}"


def verify_artifact(
    path: Path,
    *,
    expected_git_sha: str,
) -> tuple[bool, list[str], dict[str, Any] | None]:
    defects: list[str] = []
    if not path.is_file():
        return False, ["artifact_missing"], None

    try:
        result = _load(path)
    except (OSError, json.JSONDecodeError):
        return False, ["artifact_unreadable"], None

    claimed = result.get("result_sha256")
    unsigned = dict(result)
    unsigned.pop("result_sha256", None)
    if not isinstance(claimed, str) or fingerprint(unsigned) != claimed:
        defects.append("invalid_fingerprint")

    if str(result.get("git_sha") or "") != expected_git_sha:
        defects.append("git_sha_mismatch")

    if int(result.get("scenario_count", 0)) <= 0 and not result.get(
        "execution_blocked"
    ):
        defects.append("empty_execution")

    return not defects, defects, result


def _tail(value: str, limit: int = 4000) -> str:
    return value[-limit:] if len(value) > limit else value


def _step_selected(
    step: dict[str, Any],
    *,
    lanes: set[str],
    include_comparative: bool,
) -> bool:
    if lanes and step["lane"] not in lanes:
        return False
    if step.get("required_for_r4", False):
        return True
    return include_comparative


def _execute_step(
    *,
    step: dict[str, Any],
    sequence: int,
    run_date: str,
    evidence_dir: Path,
    worktrees: dict[str, Worktree],
    inventory: dict[str, Any],
    runtime_head: str,
    dry_run: bool,
) -> dict[str, Any]:
    lane = str(step["lane"])
    branch = str(step["branch"])
    worktree = worktrees.get(branch)
    run_id = _run_id(str(step["id"]), run_date, sequence)
    output = (evidence_dir / lane / f"{step['id']}.json").resolve()

    base = {
        "step_id": step["id"],
        "lane": lane,
        "branch": branch,
        "module": step["module"],
        "required_for_r4": bool(step.get("required_for_r4", False)),
        "run_id": run_id,
        "output": str(output),
    }

    if worktree is None:
        return {
            **base,
            "status": "BLOCKED",
            "reason": "WORKTREE_MISSING",
            "exit_code": 2,
        }

    expected = expected_head(
        branch=branch,
        inventory=inventory,
        runtime_head=runtime_head,
    )
    actual = _current_head(worktree.path)
    if actual != expected:
        return {
            **base,
            "status": "BLOCKED",
            "reason": "WORKTREE_HEAD_MISMATCH",
            "expected_head": expected,
            "actual_head": actual,
            "worktree": str(worktree.path),
            "exit_code": 2,
        }

    python = lane_python(lane)
    command = [
        python,
        "-m",
        str(step["module"]),
        *[str(value) for value in step.get("args", [])],
        "--run-id",
        run_id,
        "--output",
        str(output),
    ]
    base.update(
        {
            "worktree": str(worktree.path),
            "expected_head": expected,
            "python": python,
            "command": command,
        }
    )

    if dry_run:
        return {
            **base,
            "status": "DRY_RUN",
            "exit_code": None,
        }

    output.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        command,
        cwd=worktree.path,
        check=False,
        capture_output=True,
        text=True,
    )
    artifact_valid, artifact_defects, artifact = verify_artifact(
        output,
        expected_git_sha=expected,
    )

    if completed.returncode == 0 and artifact_valid:
        status = "PASS"
        reason = None
    elif completed.returncode == 2:
        status = "BLOCKED"
        reason = (
            str(artifact.get("block_reason"))
            if artifact and artifact.get("block_reason")
            else "CANDIDATE_OR_PREREQUISITE_BLOCKED"
        )
    else:
        status = "FAIL"
        reason = (
            "ARTIFACT_VALIDATION_FAILED"
            if not artifact_valid
            else f"EXIT_{completed.returncode}"
        )

    return {
        **base,
        "status": status,
        "reason": reason,
        "exit_code": completed.returncode,
        "artifact_valid": artifact_valid,
        "artifact_defects": artifact_defects,
        "stdout_tail": _tail(completed.stdout),
        "stderr_tail": _tail(completed.stderr),
    }


def _run_grand_trial(
    *,
    runtime_worktree: Worktree,
    evidence_dir: Path,
    run_date: str,
    pass_artifacts: list[Path],
) -> dict[str, Any]:
    output = evidence_dir / "integration" / "grand-integration.json"
    run_id = f"grand-integration-{run_date}-999"
    command = [
        lane_python("integration"),
        "-m",
        "labs.r3.integration.grand_trial",
        "--run-id",
        run_id,
        "--output",
        str(output.resolve()),
        *[str(path.resolve()) for path in pass_artifacts],
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        command,
        cwd=runtime_worktree.path,
        check=False,
        capture_output=True,
        text=True,
    )
    valid, defects, result = verify_artifact(
        output,
        expected_git_sha=_current_head(runtime_worktree.path),
    )
    return {
        "status": "PASS"
        if completed.returncode == 0 and valid
        else "NOT_READY",
        "exit_code": completed.returncode,
        "output": str(output),
        "artifact_valid": valid,
        "artifact_defects": defects,
        "decision_candidate": (
            result.get("decision_candidate") if result else None
        ),
        "stdout_tail": _tail(completed.stdout),
        "stderr_tail": _tail(completed.stderr),
    }


def _write_summary(
    path: Path,
    *,
    selected_lanes: list[str],
    include_comparative: bool,
    steps: list[dict[str, Any]],
    grand_trial: dict[str, Any] | None,
) -> dict[str, Any]:
    required = [step for step in steps if step["required_for_r4"]]
    required_failed = [
        step for step in required if step["status"] == "FAIL"
    ]
    required_blocked = [
        step for step in required if step["status"] == "BLOCKED"
    ]
    summary = {
        "contract_version": "gmai.r3.programme-execution-summary.v1",
        "selected_lanes": selected_lanes,
        "comparative_candidates_included": include_comparative,
        "step_count": len(steps),
        "pass_count": sum(step["status"] == "PASS" for step in steps),
        "blocked_count": sum(step["status"] == "BLOCKED" for step in steps),
        "fail_count": sum(step["status"] == "FAIL" for step in steps),
        "required_blocked": [step["step_id"] for step in required_blocked],
        "required_failed": [step["step_id"] for step in required_failed],
        "steps": steps,
        "grand_trial": grand_trial,
        "r4_execution_ready": (
            not required_blocked
            and not required_failed
            and (
                grand_trial is None
                or grand_trial.get("status") == "PASS"
            )
        ),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lane", action="append", default=[])
    parser.add_argument("--comparative", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--fail-fast", action="store_true")
    parser.add_argument("--grand-trial", action="store_true")
    parser.add_argument(
        "--run-date",
        default=date.today().strftime("%Y%m%d"),
        help="YYYYMMDD; used in deterministic R3 run IDs",
    )
    parser.add_argument(
        "--evidence-dir",
        type=Path,
        default=Path(".test-tmp") / "r3-programme",
    )
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()

    if not re.fullmatch(r"\d{8}", args.run_date):
        parser.error("--run-date must be YYYYMMDD")

    plan = _load(PLAN_PATH)
    inventory = _load(INVENTORY_PATH)
    repo_root = Path(
        _git(Path.cwd(), "rev-parse", "--show-toplevel").stdout.strip()
    )
    runtime_branch = _current_branch(repo_root)
    if runtime_branch != "radar/r3-runtime":
        raise SystemExit(
            "run_programme.py must be launched from the radar/r3-runtime worktree"
        )

    runtime_head = _current_head(repo_root)
    worktrees = discover_worktrees(repo_root)
    worktrees["radar/r3-runtime"] = Worktree(
        path=repo_root,
        head=runtime_head,
        branch="radar/r3-runtime",
    )

    selected_lanes = set(args.lane)
    known_lanes = {
        str(step["lane"]) for step in plan["steps"]
    }
    unknown = sorted(selected_lanes - known_lanes)
    if unknown:
        parser.error(f"unknown lane(s): {', '.join(unknown)}")

    selected = [
        step
        for step in plan["steps"]
        if _step_selected(
            step,
            lanes=selected_lanes,
            include_comparative=args.comparative,
        )
    ]

    if args.list:
        for step in selected:
            kind = "CORE" if step["required_for_r4"] else "COMPARATIVE"
            print(
                f"{kind:<11} {step['lane']:<18} "
                f"{step['id']} -> {step['branch']}"
            )
        return 0

    evidence_dir = args.evidence_dir.resolve()
    results: list[dict[str, Any]] = []
    for sequence, step in enumerate(selected, start=1):
        observed = _execute_step(
            step=step,
            sequence=sequence,
            run_date=args.run_date,
            evidence_dir=evidence_dir,
            worktrees=worktrees,
            inventory=inventory,
            runtime_head=runtime_head,
            dry_run=args.dry_run,
        )
        results.append(observed)
        print(
            f"[{observed['status']}] "
            f"{observed['lane']} / {observed['step_id']}"
        )
        if args.fail_fast and observed["status"] in {"FAIL", "BLOCKED"}:
            break

    grand_trial: dict[str, Any] | None = None
    if args.grand_trial and not args.dry_run:
        runtime_worktree = worktrees["radar/r3-runtime"]
        pass_artifacts = [
            Path(step["output"])
            for step in results
            if step["status"] == "PASS"
        ]
        grand_trial = _run_grand_trial(
            runtime_worktree=runtime_worktree,
            evidence_dir=evidence_dir,
            run_date=args.run_date,
            pass_artifacts=pass_artifacts,
        )
        print(f"[{grand_trial['status']}] grand integration trial")

    summary = _write_summary(
        evidence_dir / "programme-execution-summary.v1.json",
        selected_lanes=sorted(selected_lanes or known_lanes),
        include_comparative=args.comparative,
        steps=results,
        grand_trial=grand_trial,
    )

    if any(step["status"] == "FAIL" for step in results):
        return 1
    if any(
        step["status"] == "BLOCKED" and step["required_for_r4"]
        for step in results
    ):
        return 2
    if grand_trial and grand_trial["status"] != "PASS":
        return 2
    return 0 if summary["r4_execution_ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
