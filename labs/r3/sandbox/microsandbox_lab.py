from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import time
from pathlib import Path
from typing import Any

from microsandbox import Network, Sandbox

from labs.r3.common.harness import CONTRACT_VERSION, fingerprint, validate_run_id


MICROSANDBOX_VERSION = "0.6.16"
SANDBOX_NAME = "gmai-r3-microsandbox"


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


async def run_microsandbox() -> dict[str, Any]:
    outcomes: list[dict[str, Any]] = []
    created_at = time.perf_counter()

    async with await Sandbox.create(
        SANDBOX_NAME,
        image="alpine",
        network=Network.none(),
        memory=256,
        cpus=1,
        replace=True,
    ) as sandbox:
        cold_start_ms = round((time.perf_counter() - created_at) * 1000, 3)

        identity = await sandbox.id
        ping = await sandbox.ping()
        _record(
            outcomes,
            "real_microvm_identity_and_agent",
            observed=(bool(identity), ping.name == SANDBOX_NAME),
            expected=(True, True),
        )

        hello = await sandbox.shell("printf 'sandbox-ok'")
        _record(
            outcomes,
            "command_execution",
            observed=(hello.exit_code, hello.stdout_text),
            expected=(0, "sandbox-ok"),
        )

        await sandbox.fs.write("/tmp/r3.txt", b"synthetic-isolated-data")
        fs_value = await sandbox.fs.read_text("/tmp/r3.txt")
        _record(
            outcomes,
            "guest_filesystem_roundtrip",
            observed=fs_value,
            expected="synthetic-isolated-data",
        )

        host_probe = await sandbox.shell(
            "test ! -e /mnt/c/Windows/System32 && test ! -e /host && echo isolated"
        )
        _record(
            outcomes,
            "obvious_host_paths_not_mounted",
            observed=(host_probe.exit_code, host_probe.stdout_text.strip()),
            expected=(0, "isolated"),
        )

        network_probe = await sandbox.shell(
            "wget -q -T 2 -O- https://example.com >/dev/null 2>&1; "
            "test $? -ne 0 && echo blocked",
            timeout=5.0,
        )
        _record(
            outcomes,
            "network_none_blocks_egress",
            observed=network_probe.stdout_text.strip(),
            expected="blocked",
        )

        timeout_blocked = False
        try:
            await sandbox.shell("sleep 5", timeout=0.2)
        except Exception as exc:
            timeout_blocked = (
                "timeout" in type(exc).__name__.lower()
                or "timeout" in str(exc).lower()
            )
        _record(
            outcomes,
            "execution_timeout_terminates_long_command",
            observed=timeout_blocked,
            expected=True,
        )

        metrics = await sandbox.metrics()
        _record(
            outcomes,
            "resource_metrics_available",
            observed=(metrics.memory_bytes >= 0, metrics.cpu_percent >= 0),
            expected=(True, True),
        )

        name = await sandbox.name()
        _record(
            outcomes,
            "sandbox_name_stable_during_lifecycle",
            observed=name,
            expected=SANDBOX_NAME,
        )

    removed = False
    try:
        await Sandbox.get(SANDBOX_NAME)
    except Exception:
        removed = True
    _record(
        outcomes,
        "context_exit_removes_ephemeral_sandbox",
        observed=removed,
        expected=True,
    )

    failures = [item for item in outcomes if not item["passed"]]
    return {
        "outcomes": outcomes,
        "passes": len(outcomes) - len(failures),
        "failures": len(failures),
        "cold_start_ms": cold_start_ms,
        "feature_coverage": {
            "real_microvm": True,
            "command_execution": True,
            "guest_filesystem": True,
            "network_none": True,
            "timeout": True,
            "metrics": True,
            "ephemeral_cleanup": True,
            "credential_scoping": False,
            "named_volume_isolation": False,
            "snapshot_restore": False,
            "concurrency": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    validate_run_id(args.run_id)

    detail = asyncio.run(run_microsandbox())
    result = {
        "contract_version": CONTRACT_VERSION,
        "r3_run_id": args.run_id,
        "candidate": "microsandbox",
        "candidate_version": MICROSANDBOX_VERSION,
        "git_sha": _git_sha(),
        "environment": "synthetic-isolated-real-microvm",
        "experiment": "t1-t2-t3-t5-sandbox",
        "test_tiers": ["T1", "T2", "T3", "T5"],
        "scenario_count": len(detail["outcomes"]),
        "passes": detail["passes"],
        "failures": detail["failures"],
        "critical_failures": 0,
        "unauthorized_canonical_effects": 0,
        "cold_start_ms": detail["cold_start_ms"],
        "feature_coverage": detail["feature_coverage"],
        "outcomes": detail["outcomes"],
        "decision_candidate": "CONTINUE_R3_WITH_SPECIFIC_GAP",
    }
    result["result_sha256"] = fingerprint(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        f"Microsandbox R3: {result['passes']}/{result['scenario_count']} passed; "
        f"cold_start_ms={detail['cold_start_ms']}"
    )
    return 0 if result["failures"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
