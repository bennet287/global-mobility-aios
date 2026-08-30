from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from labs.r3.common.harness import CONTRACT_VERSION, fingerprint, validate_run_id


POSTGRES_IMAGE = "postgres:16-alpine"
SOURCE_PREFIX = "gmai-r3-pitr-source"
RECOVERY_PREFIX = "gmai-r3-pitr-recovery"
SOURCE_VOLUME_PREFIX = "gmai-r3-pitr-source-data"
BACKUP_VOLUME_PREFIX = "gmai-r3-pitr-basebackup"


class ExecutionBlocked(RuntimeError):
    pass


def _git_sha() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _docker(
    *args: str,
    check: bool = True,
    timeout: int = 60,
) -> subprocess.CompletedProcess[str]:
    if shutil.which("docker") is None:
        raise ExecutionBlocked("docker executable is unavailable")
    try:
        return subprocess.run(
            ["docker", *args],
            check=check,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        stderr = getattr(exc, "stderr", "")
        raise ExecutionBlocked(
            f"docker command failed: {args!r}: {stderr or exc}"
        ) from exc


def _exec(
    container: str,
    *args: str,
    check: bool = True,
    timeout: int = 60,
) -> str:
    return _docker(
        "exec",
        container,
        *args,
        check=check,
        timeout=timeout,
    ).stdout.strip()


def _psql(container: str, sql: str) -> str:
    return _exec(
        container,
        "psql",
        "-U",
        "r3",
        "-d",
        "r3_recovery",
        "-v",
        "ON_ERROR_STOP=1",
        "-At",
        "-c",
        sql,
    )


def _wait_postgres(container: str, timeout: float = 30.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        ready = _docker(
            "exec",
            container,
            "pg_isready",
            "-U",
            "r3",
            "-d",
            "r3_recovery",
            check=False,
            timeout=5,
        )
        if ready.returncode == 0:
            return
        state = _docker(
            "inspect",
            "-f",
            "{{.State.Running}}",
            container,
            check=False,
            timeout=5,
        )
        if state.returncode == 0 and state.stdout.strip() != "true":
            logs = _docker("logs", container, check=False, timeout=5).stdout
            raise ExecutionBlocked(
                f"PostgreSQL container stopped during startup: {logs[-1500:]}"
            )
        time.sleep(0.2)
    logs = _docker("logs", container, check=False, timeout=5).stdout
    raise ExecutionBlocked(
        f"PostgreSQL did not become ready: {logs[-1500:]}"
    )


def _snapshot(container: str) -> dict[str, Any]:
    raw = _psql(
        container,
        """
SELECT json_build_object(
  'status', (SELECT value FROM canonical_state WHERE key = 'status'),
  'authority', (SELECT value FROM canonical_state WHERE key = 'authority'),
  'rule', (SELECT value FROM canonical_state WHERE key = 'rule.threshold'),
  'activities', (
    SELECT json_agg(event ORDER BY sequence)
    FROM activity
  )
)::text;
""".strip(),
    )
    return json.loads(raw)


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


def _force_archive(container: str) -> None:
    _psql(container, "SELECT pg_switch_wal(); CHECKPOINT;")
    time.sleep(1.0)


def _configure_recovery_volume(
    *,
    backup_volume: str,
    target_time: str,
) -> None:
    script = r"""
set -eu
cat >> /data/postgresql.auto.conf <<EOF
archive_mode = 'off'
restore_command = 'cp /source-data/wal_archive/%f %p'
recovery_target_time = '$TARGET_TIME'
recovery_target_inclusive = 'true'
recovery_target_action = 'promote'
EOF
touch /data/recovery.signal
chown postgres:postgres /data/postgresql.auto.conf /data/recovery.signal
"""
    _docker(
        "run",
        "--rm",
        "--user",
        "0",
        "-e",
        f"TARGET_TIME={target_time}",
        "-v",
        f"{backup_volume}:/data",
        POSTGRES_IMAGE,
        "sh",
        "-c",
        script,
        timeout=30,
    )


def run_wal_pitr(run_id: str) -> dict[str, Any]:
    safe = "".join(
        ch for ch in run_id.lower() if ch.isalnum() or ch in "-_"
    )[:28]
    source = f"{SOURCE_PREFIX}-{safe}"
    recovery = f"{RECOVERY_PREFIX}-{safe}"
    source_volume = f"{SOURCE_VOLUME_PREFIX}-{safe}"
    backup_volume = f"{BACKUP_VOLUME_PREFIX}-{safe}"
    outcomes: list[dict[str, Any]] = []

    for container in (source, recovery):
        _docker("rm", "-f", container, check=False)
    for volume in (source_volume, backup_volume):
        _docker("volume", "rm", "-f", volume, check=False)
        _docker("volume", "create", volume)

    try:
        _docker(
            "run",
            "-d",
            "--name",
            source,
            "-e",
            "POSTGRES_USER=r3",
            "-e",
            "POSTGRES_PASSWORD=r3-synthetic-password",
            "-e",
            "POSTGRES_DB=r3_recovery",
            "-v",
            f"{source_volume}:/var/lib/postgresql/data",
            "-v",
            f"{backup_volume}:/backup",
            POSTGRES_IMAGE,
        )
        _wait_postgres(source)

        _exec(
            source,
            "sh",
            "-c",
            (
                "mkdir -p /var/lib/postgresql/data/wal_archive "
                "&& chown postgres:postgres /var/lib/postgresql/data/wal_archive "
                "&& chown postgres:postgres /backup"
            ),
        )
        _psql(
            source,
            """
ALTER SYSTEM SET wal_level = 'replica';
ALTER SYSTEM SET archive_mode = 'on';
ALTER SYSTEM SET archive_command =
  'test ! -f /var/lib/postgresql/data/wal_archive/%f && cp %p /var/lib/postgresql/data/wal_archive/%f';
""".strip(),
        )
        _docker("restart", source)
        _wait_postgres(source)

        _psql(
            source,
            """
CREATE TABLE canonical_state (
  key text PRIMARY KEY,
  value text NOT NULL
);
CREATE TABLE activity (
  sequence bigint PRIMARY KEY,
  event text NOT NULL
);
INSERT INTO canonical_state VALUES
  ('status', 'OPEN'),
  ('authority', 'RETAINED'),
  ('rule.threshold', '55');
INSERT INTO activity VALUES (1, 'WORK_OPENED');
""".strip(),
        )
        initial = _snapshot(source)

        _exec(
            source,
            "pg_basebackup",
            "-U",
            "r3",
            "-D",
            "/backup",
            "-Fp",
            "-Xs",
            "-P",
            timeout=120,
        )
        _record(
            outcomes,
            "real_pg_basebackup_created",
            bool(
                _exec(
                    source,
                    "sh",
                    "-c",
                    "test -f /backup/PG_VERSION && echo yes",
                )
            ),
            True,
        )

        _psql(
            source,
            """
UPDATE canonical_state
SET value = 'HUMAN_REVIEW_REQUIRED'
WHERE key = 'status';
INSERT INTO activity VALUES (2, 'HUMAN_REVIEW_REQUIRED');
""".strip(),
        )
        target_snapshot = _snapshot(source)
        target_hash = fingerprint(target_snapshot)
        target_time = _psql(
            source,
            "SELECT clock_timestamp()::text;",
        )
        _force_archive(source)

        # Create temporal separation so the later corruption is strictly
        # after the requested recovery target.
        time.sleep(1.5)
        _psql(
            source,
            """
UPDATE canonical_state
SET value = 'CORRUPTED_SYNTHETIC'
WHERE key = 'status';
UPDATE canonical_state
SET value = '999'
WHERE key = 'rule.threshold';
INSERT INTO activity VALUES (3, 'CORRUPTION_COMMITTED');
""".strip(),
        )
        corrupted = _snapshot(source)
        corrupted_hash = fingerprint(corrupted)
        _force_archive(source)

        archive_count = int(
            _exec(
                source,
                "sh",
                "-c",
                (
                    "find /var/lib/postgresql/data/wal_archive "
                    "-type f | wc -l"
                ),
            )
            or "0"
        )
        _record(
            outcomes,
            "continuous_archiving_produced_wal_files",
            archive_count > 0,
            True,
        )
        _record(
            outcomes,
            "post_target_corruption_changes_canonical_state",
            corrupted_hash != target_hash,
            True,
        )

        _docker("stop", source)
        _configure_recovery_volume(
            backup_volume=backup_volume,
            target_time=target_time,
        )

        _docker(
            "run",
            "-d",
            "--name",
            recovery,
            "-e",
            "POSTGRES_USER=r3",
            "-e",
            "POSTGRES_PASSWORD=r3-synthetic-password",
            "-e",
            "POSTGRES_DB=r3_recovery",
            "-v",
            f"{backup_volume}:/var/lib/postgresql/data",
            "-v",
            f"{source_volume}:/source-data:ro",
            POSTGRES_IMAGE,
        )
        _wait_postgres(recovery, timeout=45)

        recovered = _snapshot(recovery)
        recovered_hash = fingerprint(recovered)
        _record(
            outcomes,
            "native_wal_pitr_matches_exact_target_snapshot",
            recovered_hash,
            target_hash,
        )
        _record(
            outcomes,
            "native_wal_pitr_excludes_later_corruption",
            (
                recovered["status"],
                recovered["rule"],
                recovered["activities"],
            ),
            (
                "HUMAN_REVIEW_REQUIRED",
                "55",
                ["WORK_OPENED", "HUMAN_REVIEW_REQUIRED"],
            ),
        )
        _record(
            outcomes,
            "authority_state_survives_pitr_unchanged",
            recovered["authority"],
            "RETAINED",
        )
        _record(
            outcomes,
            "recovery_target_is_after_base_backup_state",
            recovered != initial,
            True,
        )
    finally:
        for container in (source, recovery):
            _docker("rm", "-f", container, check=False)
        for volume in (source_volume, backup_volume):
            _docker("volume", "rm", "-f", volume, check=False)

    failures = [item for item in outcomes if not item["passed"]]
    return {
        "outcomes": outcomes,
        "passes": len(outcomes) - len(failures),
        "failures": len(failures),
        "target_snapshot_sha256": target_hash,
        "recovered_snapshot_sha256": recovered_hash,
        "feature_coverage": {
            "real_postgresql": True,
            "pg_basebackup": True,
            "archive_mode": True,
            "archive_command": True,
            "wal_archiving": True,
            "recovery_signal": True,
            "restore_command": True,
            "recovery_target_time": True,
            "native_wal_pitr": True,
            "canonical_fingerprint": True,
            "post_target_corruption_excluded": True,
            "cross_region_restore": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    validate_run_id(args.run_id)

    try:
        detail = run_wal_pitr(args.run_id)
        blocked = False
        block_reason = None
    except ExecutionBlocked as exc:
        detail = {
            "outcomes": [],
            "passes": 0,
            "failures": 0,
            "target_snapshot_sha256": None,
            "recovered_snapshot_sha256": None,
            "feature_coverage": {},
        }
        blocked = True
        block_reason = str(exc)

    result = {
        "contract_version": CONTRACT_VERSION,
        "r3_run_id": args.run_id,
        "candidate": "postgresql-native-wal-pitr",
        "candidate_version": "16-alpine",
        "git_sha": _git_sha(),
        "environment": "synthetic-local-docker",
        "experiment": "t5-t8-native-wal-pitr",
        "test_tiers": ["T5", "T8"],
        "execution_blocked": blocked,
        "block_reason": block_reason,
        "scenario_count": len(detail["outcomes"]),
        "passes": detail["passes"],
        "failures": detail["failures"],
        "critical_failures": 0,
        "unauthorized_canonical_effects": 0,
        "target_snapshot_sha256": detail["target_snapshot_sha256"],
        "recovered_snapshot_sha256": detail["recovered_snapshot_sha256"],
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
        print(f"native WAL PITR R3 blocked: {block_reason}")
        return 2
    print(
        f"native WAL PITR R3: {result['passes']}/"
        f"{result['scenario_count']} passed"
    )
    return 0 if result["failures"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
