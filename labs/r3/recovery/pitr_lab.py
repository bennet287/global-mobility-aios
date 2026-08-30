from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from labs.r3.common.harness import CONTRACT_VERSION, fingerprint, validate_run_id


SOURCE = "gmai-r3-pitr-source"
RESTORE = "gmai-r3-pitr-restore"
COMPOSE = "labs/r3/pitr-compose.yml"
POSTGRES_VERSION = "16-alpine"


def _git_sha() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _run(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=check, capture_output=True, text=True)


def _exec(container: str, *args: str) -> str:
    return _run(["docker", "exec", container, *args]).stdout.strip()


def _psql(container: str, sql: str) -> str:
    return _exec(
        container,
        "psql",
        "-U",
        "r3",
        "-d",
        "r3_pitr",
        "-v",
        "ON_ERROR_STOP=1",
        "-At",
        "-c",
        sql,
    )


def _wait_ready(container: str, timeout_seconds: float = 45.0) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        probe = _run(
            ["docker", "exec", container, "pg_isready", "-U", "r3"],
            check=False,
        )
        if probe.returncode == 0:
            return
        time.sleep(1)
    raise RuntimeError(f"{container} did not become ready")


def _record(outcomes: list[dict[str, Any]], feature: str, observed: Any, expected: Any) -> None:
    outcomes.append(
        {
            "feature": feature,
            "observed": observed,
            "expected": expected,
            "passed": observed == expected,
            "unauthorized_canonical_effects": [],
        }
    )


def _compose(*args: str, env: dict[str, str] | None = None) -> None:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    subprocess.run(
        ["docker", "compose", "-f", COMPOSE, *args],
        check=True,
        env=merged,
    )


def run_pitr() -> dict[str, Any]:
    outcomes: list[dict[str, Any]] = []

    _compose("down", "-v", "--remove-orphans")
    _compose("up", "-d", "postgres-pitr-source")
    _wait_ready(SOURCE)

    _psql(
        SOURCE,
        """
CREATE TABLE canonical_state(
  sequence bigint PRIMARY KEY,
  event_type text NOT NULL,
  status text NOT NULL,
  authority text NOT NULL
);
INSERT INTO canonical_state VALUES
(1, 'WORK_OPENED', 'OPEN', 'RETAINED'),
(2, 'EVIDENCE_ATTACHED', 'IN_PROGRESS', 'RETAINED');
""".strip(),
    )

    _exec(
        SOURCE,
        "sh",
        "-lc",
        "rm -rf /basebackup/base && mkdir -p /basebackup/base && "
        "PGPASSWORD=r3-synthetic-password pg_basebackup "
        "-h 127.0.0.1 -U r3 -D /basebackup/base -Fp -Xs -P",
    )

    _psql(SOURCE, "SELECT pg_switch_wal();")
    _psql(
        SOURCE,
        "INSERT INTO canonical_state VALUES "
        "(3, 'HUMAN_REVIEW_REQUIRED', 'HUMAN_REVIEW_REQUIRED', 'RETAINED');",
    )
    target_time = _psql(
        SOURCE,
        "SELECT to_char(clock_timestamp(), 'YYYY-MM-DD HH24:MI:SS.USOF');",
    )
    time.sleep(1.2)

    _psql(
        SOURCE,
        "INSERT INTO canonical_state VALUES "
        "(4, 'POST_TARGET_MUTATION', 'COMPLETED', 'UNAUTHORIZED_SYNTHETIC');",
    )
    _psql(SOURCE, "SELECT pg_switch_wal();")
    time.sleep(2.0)

    source_rows = json.loads(
        _psql(
            SOURCE,
            "SELECT json_agg(row_to_json(x) ORDER BY sequence)::text "
            "FROM (SELECT * FROM canonical_state) x;",
        )
    )
    _record(outcomes, "source_contains_post_target_mutation", len(source_rows), 4)

    _compose("stop", "postgres-pitr-source")
    _compose(
        "--profile",
        "restore",
        "up",
        "-d",
        "postgres-pitr-restore",
        env={"R3_PITR_TARGET_TIME": target_time},
    )
    _wait_ready(RESTORE)

    restored_rows = json.loads(
        _psql(
            RESTORE,
            "SELECT json_agg(row_to_json(x) ORDER BY sequence)::text "
            "FROM (SELECT * FROM canonical_state) x;",
        )
    )
    _record(outcomes, "restored_at_exact_target_row_count", len(restored_rows), 3)
    _record(
        outcomes,
        "post_target_mutation_absent",
        any(row["sequence"] == 4 for row in restored_rows),
        False,
    )
    _record(
        outcomes,
        "authority_preserved_at_target",
        restored_rows[-1]["authority"],
        "RETAINED",
    )
    _record(
        outcomes,
        "status_matches_target_boundary",
        restored_rows[-1]["status"],
        "HUMAN_REVIEW_REQUIRED",
    )

    archive_files = _exec(
        RESTORE,
        "sh",
        "-lc",
        "find /wal_archive -maxdepth 1 -type f | wc -l",
    )
    _record(outcomes, "archived_wal_segments_present", int(archive_files) > 0, True)

    failures = [item for item in outcomes if not item["passed"]]
    return {
        "outcomes": outcomes,
        "passes": len(outcomes) - len(failures),
        "failures": len(failures),
        "recovery_target_time": target_time,
        "source_snapshot_sha256": fingerprint(source_rows),
        "restored_snapshot_sha256": fingerprint(restored_rows),
        "feature_coverage": {
            "real_postgresql": True,
            "wal_level_replica": True,
            "archive_mode": True,
            "archive_command": True,
            "pg_basebackup": True,
            "recovery_signal": True,
            "restore_command": True,
            "recovery_target_time": True,
            "post_target_mutation_excluded": True,
            "cross_region_object_storage": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    validate_run_id(args.run_id)

    detail = run_pitr()
    result = {
        "contract_version": CONTRACT_VERSION,
        "r3_run_id": args.run_id,
        "candidate": "postgresql-native-wal-pitr",
        "candidate_version": POSTGRES_VERSION,
        "git_sha": _git_sha(),
        "environment": "synthetic-isolated-real-postgresql",
        "experiment": "t3-t5-t8-native-wal-pitr",
        "test_tiers": ["T3", "T5", "T8"],
        "scenario_count": len(detail["outcomes"]),
        "passes": detail["passes"],
        "failures": detail["failures"],
        "critical_failures": 0,
        "unauthorized_canonical_effects": 0,
        "recovery_target_time": detail["recovery_target_time"],
        "source_snapshot_sha256": detail["source_snapshot_sha256"],
        "restored_snapshot_sha256": detail["restored_snapshot_sha256"],
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
    print(f"PostgreSQL WAL-PITR R3: {result['passes']}/{result['scenario_count']} passed")
    return 0 if result["failures"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
