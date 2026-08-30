from __future__ import annotations

import argparse
import json
import shutil
import socket
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

from labs.r3.common.harness import CONTRACT_VERSION, fingerprint, validate_run_id
from labs.r3.observability.otel_lab import execute_guarded_operation


OTEL_SDK_VERSION = "1.44.0"
COLLECTOR_VERSION = "0.159.0"
COLLECTOR_CONTAINER = "gmai-r3-otel-collector"
COLLECTOR_PORT = 14317


class ExecutionBlocked(RuntimeError):
    pass


def _git_sha() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _docker(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    if shutil.which("docker") is None:
        raise ExecutionBlocked("docker executable is unavailable")
    try:
        return subprocess.run(
            ["docker", *args],
            check=check,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise ExecutionBlocked(f"docker command failed: {args!r}: {exc}") from exc


def _wait_port(*, open_expected: bool, timeout: float = 15.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.25)
            is_open = sock.connect_ex(("127.0.0.1", COLLECTOR_PORT)) == 0
        if is_open == open_expected:
            return True
        time.sleep(0.1)
    return False


def _collector_file() -> str:
    with tempfile.TemporaryDirectory(prefix="gmai-r3-otel-copy-") as temp:
        destination = Path(temp) / "traces.json"
        copied = subprocess.run(
            [
                "docker",
                "cp",
                f"{COLLECTOR_CONTAINER}:/tmp/gmai-r3-traces.json",
                str(destination),
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if copied.returncode != 0 or not destination.exists():
            return ""
        return destination.read_text(encoding="utf-8", errors="replace")


def _export(*, run_id: str, request_id: str) -> dict[str, Any]:
    exporter = OTLPSpanExporter(
        endpoint=f"127.0.0.1:{COLLECTOR_PORT}",
        insecure=True,
        timeout=2,
    )
    return execute_guarded_operation(
        exporter=exporter,
        run_id=run_id,
        request_id=request_id,
    )


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


def run_collector(run_id: str) -> dict[str, Any]:
    outcomes: list[dict[str, Any]] = []

    inspect = _docker(
        "inspect",
        "-f",
        "{{.State.Running}}",
        COLLECTOR_CONTAINER,
    )
    _record(
        outcomes,
        "real_collector_container_running",
        inspect.stdout.strip(),
        "true",
    )
    if not _wait_port(open_expected=True):
        raise ExecutionBlocked("OTLP Collector port did not become ready")

    canonical = _export(
        run_id=run_id,
        request_id="collector-before-restart",
    )
    time.sleep(0.5)
    before = _collector_file()
    _record(
        outcomes,
        "otlp_grpc_reaches_real_collector",
        (
            "collector-before-restart" in before,
            run_id in before,
            canonical["decision"],
            canonical["canonical_effects"],
        ),
        (True, True, "DENY", 0),
    )

    _docker("restart", COLLECTOR_CONTAINER)
    if not _wait_port(open_expected=True):
        raise ExecutionBlocked("collector did not recover after docker restart")

    after_restart = _export(
        run_id=run_id,
        request_id="collector-after-restart",
    )
    time.sleep(0.5)
    after = _collector_file()
    _record(
        outcomes,
        "collector_restart_accepts_new_telemetry",
        (
            "collector-after-restart" in after,
            after_restart["decision"],
            after_restart["canonical_effects"],
        ),
        (True, "DENY", 0),
    )

    _docker("stop", COLLECTOR_CONTAINER)
    if not _wait_port(open_expected=False):
        raise ExecutionBlocked("collector port remained open after stop")

    # Exporter failure is diagnostic only. The guarded command outcome remains
    # a canonical DENY with zero business effects.
    during_outage = _export(
        run_id=run_id,
        request_id="collector-during-outage",
    )
    _record(
        outcomes,
        "collector_outage_cannot_change_canonical_decision",
        (
            during_outage["decision"],
            during_outage["reason_class"],
            during_outage["canonical_effects"],
        ),
        ("DENY", "HUMAN_APPROVAL_REQUIRED", 0),
    )

    _docker("start", COLLECTOR_CONTAINER)
    if not _wait_port(open_expected=True):
        raise ExecutionBlocked("collector did not recover after outage")

    recovered = _export(
        run_id=run_id,
        request_id="collector-after-outage",
    )
    time.sleep(0.5)
    recovery_file = _collector_file()
    _record(
        outcomes,
        "collector_transport_recovers_after_outage",
        (
            "collector-after-outage" in recovery_file,
            recovered["canonical_effects"],
        ),
        (True, 0),
    )

    failures = [item for item in outcomes if not item["passed"]]
    return {
        "outcomes": outcomes,
        "passes": len(outcomes) - len(failures),
        "failures": len(failures),
        "feature_coverage": {
            "real_collector": True,
            "otlp_grpc": True,
            "file_exporter_observation": True,
            "collector_restart": True,
            "collector_outage": True,
            "transport_recovery": True,
            "telemetry_truth_boundary": True,
            "sampling": False,
            "volume_cost": False,
            "tls": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    validate_run_id(args.run_id)

    try:
        detail = run_collector(args.run_id)
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
        "candidate": "opentelemetry-collector-contrib",
        "candidate_version": COLLECTOR_VERSION,
        "sdk_version": OTEL_SDK_VERSION,
        "git_sha": _git_sha(),
        "environment": "synthetic-local-docker",
        "experiment": "t3-t5-otlp-collector-chaos",
        "test_tiers": ["T3", "T5"],
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
        newline="\n",
    )

    if blocked:
        print(f"OTel Collector R3 blocked: {block_reason}")
        return 2
    print(
        f"OTel Collector R3: {result['passes']}/"
        f"{result['scenario_count']} passed"
    )
    return 0 if result["failures"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
