from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from labs.r3.common.harness import CONTRACT_VERSION, fingerprint, validate_run_id


POSTGRES_VERSION = "16-alpine"
CONTAINER = "gmai-r3-recovery-postgres"
SOURCE_DB = "r3_recovery"
RESTORE_DB = "r3_restore"


SCHEMA_SQL = r"""
DROP TABLE IF EXISTS activity CASCADE;
DROP TABLE IF EXISTS verified_rule CASCADE;
DROP TABLE IF EXISTS evidence CASCADE;
DROP TABLE IF EXISTS work_item CASCADE;
DROP TABLE IF EXISTS organization CASCADE;
DROP TABLE IF EXISTS event_log CASCADE;

CREATE TABLE organization (
  organization_id text PRIMARY KEY,
  tenant_id text NOT NULL,
  name text NOT NULL
);

CREATE TABLE work_item (
  work_item_id text PRIMARY KEY,
  organization_id text NOT NULL REFERENCES organization(organization_id),
  status text NOT NULL,
  authority_state text NOT NULL
);

CREATE TABLE evidence (
  evidence_id text PRIMARY KEY,
  work_item_id text NOT NULL REFERENCES work_item(work_item_id),
  source_ref text NOT NULL,
  evidence_hash text NOT NULL
);

CREATE TABLE verified_rule (
  rule_id text PRIMARY KEY,
  jurisdiction text NOT NULL,
  rule_key text NOT NULL,
  rule_value text NOT NULL,
  evidence_id text NOT NULL REFERENCES evidence(evidence_id)
);

CREATE TABLE activity (
  sequence bigint PRIMARY KEY,
  activity_id text UNIQUE NOT NULL,
  work_item_id text NOT NULL REFERENCES work_item(work_item_id),
  event_type text NOT NULL,
  payload text NOT NULL
);

CREATE TABLE event_log (
  sequence bigint PRIMARY KEY,
  occurred_at timestamptz NOT NULL,
  aggregate_id text NOT NULL,
  event_type text NOT NULL,
  status_after text NOT NULL,
  authority_after text NOT NULL
);
"""

SEED_SQL = r"""
INSERT INTO organization VALUES
('org:alpha', 'tenant:alpha', 'Austria Mobility Team');

INSERT INTO work_item VALUES
('work:AT-001', 'org:alpha', 'HUMAN_REVIEW_REQUIRED', 'RETAINED');

INSERT INTO evidence VALUES
('evidence:001', 'work:AT-001', 'migration.gv.at', 'sha256:synthetic-official');

INSERT INTO verified_rule VALUES
('rule:001', 'AT', 'rwr.shortage.minimum_points', '55', 'evidence:001');

INSERT INTO activity VALUES
(1, 'activity:001', 'work:AT-001', 'WORK_OPENED', 'synthetic'),
(2, 'activity:002', 'work:AT-001', 'EVIDENCE_ATTACHED', 'evidence:001'),
(3, 'activity:003', 'work:AT-001', 'HUMAN_REVIEW_REQUIRED', 'retained');

INSERT INTO event_log VALUES
(1, '2026-08-30T18:00:00Z', 'work:AT-001', 'WORK_OPENED', 'OPEN', 'RETAINED'),
(2, '2026-08-30T18:05:00Z', 'work:AT-001', 'ASSESSMENT_STARTED', 'IN_PROGRESS', 'RETAINED'),
(3, '2026-08-30T18:10:00Z', 'work:AT-001', 'HUMAN_REVIEW_REQUIRED', 'HUMAN_REVIEW_REQUIRED', 'RETAINED'),
(4, '2026-08-30T18:15:00Z', 'work:AT-001', 'SYNTHETIC_POST_REVIEW', 'COMPLETED', 'RETAINED');
"""


def _git_sha() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _docker_exec(*args: str, input_text: str | None = None) -> str:
    completed = subprocess.run(
        ["docker", "exec", "-i", CONTAINER, *args],
        check=True,
        input=input_text,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _psql(db: str, sql: str) -> str:
    return _docker_exec(
        "psql",
        "-U",
        "r3",
        "-d",
        db,
        "-v",
        "ON_ERROR_STOP=1",
        "-At",
        "-c",
        sql,
    )


def _psql_script(db: str, sql: str) -> None:
    _docker_exec(
        "psql",
        "-U",
        "r3",
        "-d",
        db,
        "-v",
        "ON_ERROR_STOP=1",
        input_text=sql,
    )


def _table_rows(db: str, table: str, order_by: str) -> list[dict[str, Any]]:
    raw = _psql(
        db,
        (
            "SELECT COALESCE(json_agg(row_to_json(x) ORDER BY "
            f"{order_by})::text, '[]') "
            f"FROM (SELECT * FROM {table}) x;"
        ),
    )
    return json.loads(raw)


def canonical_snapshot(db: str) -> dict[str, Any]:
    return {
        "organization": _table_rows(db, "organization", "organization_id"),
        "work_item": _table_rows(db, "work_item", "work_item_id"),
        "evidence": _table_rows(db, "evidence", "evidence_id"),
        "verified_rule": _table_rows(db, "verified_rule", "rule_id"),
        "activity": _table_rows(db, "activity", "sequence"),
    }


def relationship_snapshot(db: str) -> dict[str, Any]:
    return {
        "work_to_org": _psql(
            db,
            """
SELECT count(*)
FROM work_item w
JOIN organization o ON o.organization_id = w.organization_id;
""".strip(),
        ),
        "evidence_to_work": _psql(
            db,
            """
SELECT count(*)
FROM evidence e
JOIN work_item w ON w.work_item_id = e.work_item_id;
""".strip(),
        ),
        "rule_to_evidence": _psql(
            db,
            """
SELECT count(*)
FROM verified_rule r
JOIN evidence e ON e.evidence_id = r.evidence_id;
""".strip(),
        ),
        "activity_to_work": _psql(
            db,
            """
SELECT count(*)
FROM activity a
JOIN work_item w ON w.work_item_id = a.work_item_id;
""".strip(),
        ),
    }


def reconstruct_at(events: list[dict[str, Any]], cutoff: str) -> dict[str, str]:
    selected = [
        event
        for event in events
        if str(event["occurred_at"]) <= cutoff
    ]
    if not selected:
        return {"status": "ABSENT", "authority": "ABSENT"}
    latest = max(selected, key=lambda item: int(item["sequence"]))
    return {
        "status": str(latest["status_after"]),
        "authority": str(latest["authority_after"]),
    }


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


def run_recovery() -> dict[str, Any]:
    outcomes: list[dict[str, Any]] = []

    _psql_script(SOURCE_DB, SCHEMA_SQL + "
" + SEED_SQL)
    source = canonical_snapshot(SOURCE_DB)
    source_hash = fingerprint(source)
    source_relationships = relationship_snapshot(SOURCE_DB)

    _docker_exec(
        "pg_dump",
        "-U",
        "r3",
        "-d",
        SOURCE_DB,
        "-Fc",
        "-f",
        "/tmp/r3-logical.dump",
    )

    _psql(
        "postgres",
        f"DROP DATABASE IF EXISTS {RESTORE_DB} WITH (FORCE);",
    )
    _psql(
        "postgres",
        f"CREATE DATABASE {RESTORE_DB} OWNER r3;",
    )
    _docker_exec(
        "pg_restore",
        "-U",
        "r3",
        "-d",
        RESTORE_DB,
        "--no-owner",
        "--exit-on-error",
        "/tmp/r3-logical.dump",
    )
    restored = canonical_snapshot(RESTORE_DB)
    restored_hash = fingerprint(restored)
    restored_relationships = relationship_snapshot(RESTORE_DB)

    _record(
        outcomes,
        "logical_backup_restore_exact_canonical_fingerprint",
        restored_hash,
        source_hash,
    )
    _record(
        outcomes,
        "foreign_key_relationships_reconstructed",
        restored_relationships,
        source_relationships,
    )

    _psql(
        SOURCE_DB,
        """
UPDATE work_item
SET status = 'CORRUPTED_SYNTHETIC', authority_state = 'UNAUTHORIZED_SYNTHETIC'
WHERE work_item_id = 'work:AT-001';
""".strip(),
    )
    corrupted_hash = fingerprint(canonical_snapshot(SOURCE_DB))
    _record(
        outcomes,
        "destructive_mutation_changes_canonical_fingerprint",
        corrupted_hash != source_hash,
        True,
    )
    _record(
        outcomes,
        "restored_copy_remains_original_after_source_mutation",
        fingerprint(canonical_snapshot(RESTORE_DB)),
        source_hash,
    )

    events = _table_rows(RESTORE_DB, "event_log", "sequence")
    at_review = reconstruct_at(events, "2026-08-30 18:10:00+00")
    before_review = reconstruct_at(events, "2026-08-30 18:09:59+00")
    after_review = reconstruct_at(events, "2026-08-30 18:15:00+00")
    _record(
        outcomes,
        "pitr_style_event_replay_before_review",
        before_review,
        {"status": "IN_PROGRESS", "authority": "RETAINED"},
    )
    _record(
        outcomes,
        "pitr_style_event_replay_at_review",
        at_review,
        {"status": "HUMAN_REVIEW_REQUIRED", "authority": "RETAINED"},
    )
    _record(
        outcomes,
        "pitr_style_event_replay_after_review",
        after_review,
        {"status": "COMPLETED", "authority": "RETAINED"},
    )

    activity_sequences = [
        int(item["sequence"]) for item in restored["activity"]
    ]
    _record(
        outcomes,
        "activity_order_exact_after_restore",
        activity_sequences,
        [1, 2, 3],
    )

    rule = restored["verified_rule"][0]
    evidence = restored["evidence"][0]
    _record(
        outcomes,
        "verified_rule_evidence_lineage_exact_after_restore",
        (rule["evidence_id"], evidence["evidence_hash"]),
        ("evidence:001", "sha256:synthetic-official"),
    )

    failures = [item for item in outcomes if not item["passed"]]
    return {
        "outcomes": outcomes,
        "passes": len(outcomes) - len(failures),
        "failures": len(failures),
        "source_snapshot_sha256": source_hash,
        "restored_snapshot_sha256": restored_hash,
        "feature_coverage": {
            "real_postgresql": True,
            "logical_pg_dump": True,
            "logical_pg_restore": True,
            "canonical_fingerprint": True,
            "relationship_reconstruction": True,
            "activity_order": True,
            "verified_rule_evidence_lineage": True,
            "pitr_style_event_replay": True,
            "native_wal_pitr": False,
            "cross_service_restore": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    validate_run_id(args.run_id)

    detail = run_recovery()
    result = {
        "contract_version": CONTRACT_VERSION,
        "r3_run_id": args.run_id,
        "candidate": "postgresql-recovery",
        "candidate_version": POSTGRES_VERSION,
        "git_sha": _git_sha(),
        "environment": "synthetic-isolated-real-postgresql",
        "experiment": "t3-t5-t8-backup-restore-replay",
        "test_tiers": ["T3", "T5", "T8"],
        "scenario_count": len(detail["outcomes"]),
        "passes": detail["passes"],
        "failures": detail["failures"],
        "critical_failures": 0,
        "unauthorized_canonical_effects": 0,
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
    print(
        f"recovery R3: {result['passes']}/{result['scenario_count']} passed; "
        "native WAL PITR remains pending"
    )
    return 0 if result["failures"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
