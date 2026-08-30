from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
from pathlib import Path
from typing import Any

from microsandbox import Network, Sandbox, Secret, Snapshot, Volume

from labs.r3.common.harness import CONTRACT_VERSION, fingerprint, validate_run_id


MICROSANDBOX_VERSION = "0.6.16"
SYNTHETIC_SECRET = "AIOS_R3_SYNTHETIC_SECRET_NEVER_PRODUCTION"


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


async def _cleanup_sandbox(name: str) -> None:
    try:
        handle = await Sandbox.get(name)
    except Exception:
        return
    try:
        await handle.stop()
    except Exception:
        pass
    try:
        await Sandbox.remove(name)
    except Exception:
        pass


async def _volume_depth(prefix: str, outcomes: list[dict[str, Any]]) -> None:
    volume_name = f"{prefix}-volume"
    writer_name = f"{prefix}-writer"
    reader_name = f"{prefix}-reader"
    await Volume.create(volume_name, quota_mib=64)
    try:
        writer = await Sandbox.create(
            writer_name,
            image="alpine",
            network=Network.none(),
            volumes={"/data": Volume.named(volume_name)},
            replace=True,
        )
        try:
            written = await writer.shell(
                "printf 'tenant-alpha-owned' > /data/owner.txt && sync"
            )
            _record(
                outcomes,
                "named_volume_writer_commits_synthetic_marker",
                written.exit_code,
                0,
            )
        finally:
            await writer.stop()
            await Sandbox.remove(writer_name)

        reader = await Sandbox.create(
            reader_name,
            image="alpine",
            network=Network.none(),
            volumes={
                "/data": Volume.named(
                    volume_name,
                    readonly=True,
                    noexec=True,
                    nosuid=True,
                    nodev=True,
                )
            },
            replace=True,
        )
        try:
            read = await reader.shell("cat /data/owner.txt")
            _record(
                outcomes,
                "named_volume_survives_sandbox_replacement",
                (read.exit_code, read.stdout_text),
                (0, "tenant-alpha-owned"),
            )

            write_attempt = await reader.shell(
                "if printf 'must-not-write' > /data/blocked.txt 2>/dev/null; "
                "then echo writable; else echo readonly; fi"
            )
            _record(
                outcomes,
                "readonly_named_volume_rejects_mutation",
                write_attempt.stdout_text.strip(),
                "readonly",
            )
        finally:
            await reader.stop()
            await Sandbox.remove(reader_name)
    finally:
        try:
            await Volume.remove(volume_name)
        except Exception:
            pass


async def _snapshot_depth(prefix: str, outcomes: list[dict[str, Any]]) -> None:
    baseline_name = f"{prefix}-baseline"
    fork_name = f"{prefix}-fork"
    snapshot_name = f"{prefix}-snapshot"

    baseline = await Sandbox.create(
        baseline_name,
        image="alpine",
        network=Network.none(),
        replace=True,
    )
    try:
        marker = await baseline.shell(
            "printf 'snapshot-authority-neutral' > /root/r3-marker.txt && sync"
        )
        _record(outcomes, "snapshot_baseline_written", marker.exit_code, 0)
        await baseline.stop()

        handle = await Sandbox.get(baseline_name)
        snapshot = await handle.snapshot(snapshot_name)
        _record(
            outcomes,
            "stopped_microvm_snapshot_created",
            (bool(snapshot.digest), bool(snapshot.path)),
            (True, True),
        )

        fork = await Sandbox.create(
            fork_name,
            from_snapshot=snapshot_name,
            network=Network.none(),
            replace=True,
        )
        try:
            restored = await fork.shell("cat /root/r3-marker.txt")
            _record(
                outcomes,
                "snapshot_fork_restores_guest_state",
                (restored.exit_code, restored.stdout_text),
                (0, "snapshot-authority-neutral"),
            )
            egress = await fork.shell(
                "wget -q -T 2 -O- https://example.com >/dev/null 2>&1; "
                "test $? -ne 0 && echo blocked",
                timeout=5.0,
            )
            _record(
                outcomes,
                "snapshot_does_not_relax_network_none",
                egress.stdout_text.strip(),
                "blocked",
            )
        finally:
            await fork.stop()
            await Sandbox.remove(fork_name)
    finally:
        await _cleanup_sandbox(baseline_name)
        try:
            await Snapshot.remove(snapshot_name, force=True)
        except Exception:
            pass


async def _synthetic_secret_depth(
    prefix: str,
    outcomes: list[dict[str, Any]],
) -> None:
    name = f"{prefix}-secret"
    sandbox = await Sandbox.create(
        name,
        image="alpine",
        cpus=1,
        memory=256,
        secrets=[
            Secret.env(
                "GMAI_R3_API_KEY",
                value=SYNTHETIC_SECRET,
                allow_hosts=["example.com"],
            )
        ],
        replace=True,
    )
    try:
        guest = await sandbox.shell('printf "%s" "$GMAI_R3_API_KEY"')
        visible = guest.stdout_text.strip()
        _record(
            outcomes,
            "synthetic_secret_value_never_enters_guest_environment",
            (
                guest.exit_code,
                visible == SYNTHETIC_SECRET,
                visible.startswith("$MSB_GMAI_R3_API_KEY"),
            ),
            (0, False, True),
        )

        handle = await Sandbox.get(name)
        config = handle.config_json
        _record(
            outcomes,
            "raw_sdk_secret_pattern_is_flagged_nonproduction",
            (
                SYNTHETIC_SECRET in config,
                "GMAI_R3_API_KEY" in config,
            ),
            (True, True),
        )
    finally:
        await sandbox.stop()
        await Sandbox.remove(name)


async def _concurrency_depth(
    prefix: str,
    outcomes: list[dict[str, Any]],
) -> None:
    names = [f"{prefix}-c{i}" for i in range(4)]

    async def create_one(index: int, name: str) -> tuple[str, bool]:
        sandbox = await Sandbox.create(
            name,
            image="alpine",
            network=Network.none(),
            cpus=1,
            memory=192,
            replace=True,
        )
        marker = f"tenant-{index}-marker"
        try:
            await sandbox.shell(
                f"printf '{marker}' > /tmp/tenant-marker"
            )
            own = await sandbox.shell("cat /tmp/tenant-marker")
            egress = await sandbox.shell(
                "wget -q -T 2 -O- https://example.com >/dev/null 2>&1; "
                "test $? -ne 0 && echo blocked",
                timeout=5.0,
            )
            return (
                name,
                own.stdout_text == marker
                and egress.stdout_text.strip() == "blocked",
            )
        finally:
            await sandbox.stop()
            await Sandbox.remove(name)

    results = await asyncio.gather(
        *(create_one(index, name) for index, name in enumerate(names))
    )
    _record(
        outcomes,
        "four_concurrent_microvms_preserve_guest_and_network_isolation",
        (
            len(results),
            all(isolated for _, isolated in results),
            sorted(name for name, _ in results),
        ),
        (4, True, sorted(names)),
    )


async def run_depth(run_id: str) -> dict[str, Any]:
    safe = "".join(
        char for char in run_id.lower() if char.isalnum() or char == "-"
    )[:24]
    prefix = f"gmai-r3-{safe}"
    outcomes: list[dict[str, Any]] = []

    await _volume_depth(prefix, outcomes)
    await _snapshot_depth(prefix, outcomes)
    await _synthetic_secret_depth(prefix, outcomes)
    await _concurrency_depth(prefix, outcomes)

    failures = [item for item in outcomes if not item["passed"]]
    return {
        "outcomes": outcomes,
        "passes": len(outcomes) - len(failures),
        "failures": len(failures),
        "feature_coverage": {
            "real_microvm": True,
            "named_volume_persistence": True,
            "readonly_named_volume": True,
            "snapshot_restore": True,
            "snapshot_network_policy_retained": True,
            "synthetic_secret_guest_nonexposure": True,
            "raw_sdk_secret_persistence_risk_recorded": True,
            "concurrent_four_sandboxes": True,
            "concurrent_guest_isolation": True,
            "concurrent_network_none": True,
            "allowed_host_secret_substitution": False,
            "secret_rotation": False,
            "production_credentials": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    validate_run_id(args.run_id)

    detail = asyncio.run(run_depth(args.run_id))
    result = {
        "contract_version": CONTRACT_VERSION,
        "r3_run_id": args.run_id,
        "candidate": "microsandbox-depth",
        "candidate_version": MICROSANDBOX_VERSION,
        "git_sha": _git_sha(),
        "environment": "synthetic-local-real-microvm",
        "experiment": "t3-t5-t8-sandbox-depth",
        "test_tiers": ["T3", "T5", "T8"],
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
    print(
        f"Microsandbox depth R3: {result['passes']}/"
        f"{result['scenario_count']} passed"
    )
    return 0 if result["failures"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
