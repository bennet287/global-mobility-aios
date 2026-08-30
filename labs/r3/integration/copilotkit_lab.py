from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from labs.r3.common.harness import CONTRACT_VERSION, fingerprint, validate_run_id


COPILOTKIT_VERSION = "1.69.3"
LAB_DIR = Path(__file__).resolve().parent / "copilotkit"
PROBE = LAB_DIR / "runtime_probe.mjs"


class ExecutionBlocked(RuntimeError):
    pass


def _git_sha() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def run_copilotkit() -> dict[str, Any]:
    node = shutil.which("node")
    if node is None:
        raise ExecutionBlocked("Node.js is required for the CopilotKit R3 lab")

    runtime_module = LAB_DIR / "node_modules" / "@copilotkit" / "runtime"
    if not runtime_module.exists():
        raise ExecutionBlocked(
            "isolated CopilotKit dependencies are not installed; "
            "run npm install inside labs/r3/integration/copilotkit"
        )

    completed = subprocess.run(
        [node, str(PROBE)],
        cwd=LAB_DIR,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    marker = "GMAI_RESULT="
    payload_line = next(
        (
            line[len(marker) :]
            for line in reversed(completed.stdout.splitlines())
            if line.startswith(marker)
        ),
        None,
    )
    if payload_line is None:
        diagnostic = " ".join(
            value.strip()
            for value in (completed.stderr, completed.stdout)
            if value.strip()
        )[:1500]
        raise RuntimeError(
            "CopilotKit runtime probe returned no result: "
            + (diagnostic or f"exit={completed.returncode}")
        )

    detail = json.loads(payload_line)
    if completed.returncode != 0:
        raise RuntimeError(
            f"CopilotKit runtime probe exited {completed.returncode}"
        )
    return detail


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    validate_run_id(args.run_id)

    try:
        detail = run_copilotkit()
        blocked = False
        block_reason = None
    except ExecutionBlocked as exc:
        detail = {
            "scenario_count": 0,
            "passes": 0,
            "failures": 0,
            "critical_failures": 0,
            "unauthorized_canonical_effects": 0,
            "feature_coverage": {},
            "outcomes": [],
        }
        blocked = True
        block_reason = str(exc)

    result = {
        "contract_version": CONTRACT_VERSION,
        "r3_run_id": args.run_id,
        "candidate": "copilotkit-runtime",
        "candidate_version": COPILOTKIT_VERSION,
        "git_sha": _git_sha(),
        "environment": "synthetic-isolated-real-node-runtime",
        "experiment": "t1-t2-t4-governed-copilotkit-runtime",
        "test_tiers": ["T1", "T2", "T4"],
        "execution_blocked": blocked,
        "block_reason": block_reason,
        "scenario_count": int(detail.get("scenario_count", 0)),
        "passes": int(detail.get("passes", 0)),
        "failures": int(detail.get("failures", 0)),
        "critical_failures": int(detail.get("critical_failures", 0)),
        "unauthorized_canonical_effects": int(
            detail.get("unauthorized_canonical_effects", 0)
        ),
        "feature_coverage": detail.get("feature_coverage", {}),
        "outcomes": detail.get("outcomes", []),
        "decision_candidate": "CONTINUE_R3_WITH_SPECIFIC_GAP",
    }
    result["result_sha256"] = fingerprint(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    if blocked:
        print(f"CopilotKit R3 execution blocked: {block_reason}")
        return 2

    print(
        f"CopilotKit R3: {result['passes']}/{result['scenario_count']} passed"
    )
    return 0 if result["failures"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
