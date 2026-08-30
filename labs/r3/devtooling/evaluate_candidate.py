from __future__ import annotations

import argparse
import asyncio
import json
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from labs.r3.common.harness import CONTRACT_VERSION, fingerprint, validate_run_id


MICROSANDBOX_VERSION = "0.6.16"
FIXTURE_DIR = Path(__file__).resolve().parent / "fixture"
MAX_CANDIDATE_BYTES = 100_000


class ExecutionBlocked(RuntimeError):
    pass


def _git_sha() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _safe_name(run_id: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9-]+", "-", run_id).strip("-").lower()
    return ("gmai-dev-" + normalized)[-60:]


def _runner_source() -> str:
    return """from __future__ import annotations

import json
import unittest

loader = unittest.TestLoader()
suite = loader.discover(".", pattern="test_candidate.py")
result = unittest.TextTestRunner(verbosity=2).run(suite)
print(
    "GMAI_TEST_RESULT="
    + json.dumps(
        {
            "tests_run": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
            "skipped": len(result.skipped),
            "successful": result.wasSuccessful(),
        },
        sort_keys=True,
    )
)
raise SystemExit(0 if result.wasSuccessful() else 1)
"""


async def _evaluate_in_microsandbox(
    *,
    candidate_source: str,
    run_id: str,
) -> dict[str, Any]:
    try:
        from microsandbox import Network, Sandbox
    except ImportError as exc:
        raise ExecutionBlocked("microsandbox==0.6.16 is required") from exc

    name = _safe_name(run_id)
    started = time.perf_counter()
    try:
        async with await Sandbox.create(
            name,
            image="python:3.12-alpine",
            network=Network.none(),
            memory=256,
            cpus=1,
            replace=True,
        ) as sandbox:
            await sandbox.shell("mkdir -p /workspace")
            await sandbox.fs.write(
                "/workspace/candidate.py",
                candidate_source.encode("utf-8"),
            )
            await sandbox.fs.write(
                "/workspace/test_candidate.py",
                (FIXTURE_DIR / "test_candidate.py").read_bytes(),
            )
            await sandbox.fs.write(
                "/workspace/run_tests.py",
                _runner_source().encode("utf-8"),
            )

            command = (
                "cd /workspace && "
                "ulimit -t 8 2>/dev/null || true; "
                "python run_tests.py"
            )
            completed = await sandbox.shell(command, timeout=12.0)
    except Exception as exc:
        if "microsandbox" in type(exc).__module__.lower():
            raise ExecutionBlocked(
                f"Microsandbox unavailable: {type(exc).__name__}: {exc}"
            ) from exc
        raise

    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    stdout = completed.stdout_text
    marker = "GMAI_TEST_RESULT="
    payload = next(
        (
            line[len(marker) :]
            for line in reversed(stdout.splitlines())
            if line.startswith(marker)
        ),
        None,
    )
    if payload is None:
        raise RuntimeError(
            "sandbox test runner returned no structured result; "
            f"exit={completed.exit_code}"
        )

    parsed = json.loads(payload)
    return {
        "tests_run": int(parsed["tests_run"]),
        "test_failures": int(parsed["failures"]),
        "test_errors": int(parsed["errors"]),
        "test_skipped": int(parsed["skipped"]),
        "successful": bool(parsed["successful"]),
        "sandbox_exit_code": int(completed.exit_code),
        "evaluation_duration_ms": elapsed_ms,
        "stdout_tail": "\n".join(stdout.splitlines()[-40:]),
        "stderr_tail": "\n".join(completed.stderr_text.splitlines()[-40:]),
    }


def evaluate_candidate(
    *,
    candidate_file: Path,
    run_id: str,
) -> dict[str, Any]:
    if not candidate_file.is_file():
        raise ExecutionBlocked(
            "candidate implementation is absent; no model output was supplied"
        )
    raw = candidate_file.read_bytes()
    if len(raw) > MAX_CANDIDATE_BYTES:
        raise ValueError("candidate file exceeds bounded benchmark size")
    try:
        source = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("candidate file must be UTF-8 Python source") from exc

    return asyncio.run(
        _evaluate_in_microsandbox(
            candidate_source=source,
            run_id=run_id,
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--candidate-file", type=Path)
    parser.add_argument("--candidate-name", default="unspecified-dev-model")
    parser.add_argument(
        "--provenance",
        choices=[
            "UNKNOWN",
            "LOCAL_MODEL_USER_REPORTED",
            "MANUAL_EXTERNAL_MODEL_RUN",
        ],
        default="UNKNOWN",
    )
    parser.add_argument("--generation-duration-ms", type=float)
    args = parser.parse_args()
    validate_run_id(args.run_id)

    try:
        if args.candidate_file is None:
            raise ExecutionBlocked(
                "candidate implementation is absent; no model output was supplied"
            )
        detail = evaluate_candidate(
            candidate_file=args.candidate_file,
            run_id=args.run_id,
        )
        blocked = False
        block_reason = None
    except ExecutionBlocked as exc:
        detail = {
            "tests_run": 0,
            "test_failures": 0,
            "test_errors": 0,
            "test_skipped": 0,
            "successful": False,
            "sandbox_exit_code": None,
            "evaluation_duration_ms": None,
            "stdout_tail": "",
            "stderr_tail": "",
        }
        blocked = True
        block_reason = str(exc)

    passed = (
        not blocked
        and detail["successful"]
        and detail["test_failures"] == 0
        and detail["test_errors"] == 0
        and detail["tests_run"] >= 14
    )
    result = {
        "contract_version": CONTRACT_VERSION,
        "r3_run_id": args.run_id,
        "candidate": "dev-model-benchmark",
        "candidate_name": args.candidate_name,
        "candidate_version": "benchmark-v1",
        "candidate_provenance": args.provenance,
        "provider_identity_verified": False,
        "git_sha": _git_sha(),
        "environment": "synthetic-microsandbox-network-none",
        "experiment": "bounded-development-model-correctness",
        "test_tiers": ["T1", "T4", "T5"],
        "execution_blocked": blocked,
        "block_reason": block_reason,
        "scenario_count": int(detail["tests_run"]),
        "passes": int(detail["tests_run"]) if passed else 0,
        "failures": (
            0
            if passed
            else int(detail["test_failures"]) + int(detail["test_errors"])
        ),
        "critical_failures": 0,
        "unauthorized_canonical_effects": 0,
        "generation_duration_ms": args.generation_duration_ms,
        "evaluation": detail,
        "safety_boundary": {
            "network": "NONE",
            "host_volumes": False,
            "credentials": False,
            "memory_mib": 256,
            "cpus": 1,
            "wall_timeout_seconds": 12,
        },
        "decision_candidate": (
            "CONTINUE_R3_WITH_SPECIFIC_GAP"
            if not passed
            else "R3_BOUNDED_DEV_TOOL_EVIDENCE_CANDIDATE"
        ),
    }
    result["result_sha256"] = fingerprint(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    if blocked:
        print(f"dev-model benchmark blocked: {block_reason}")
        return 2
    print(
        "dev-model benchmark: "
        f"{detail['tests_run']} tests; "
        f"failures={detail['test_failures']}; errors={detail['test_errors']}"
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
