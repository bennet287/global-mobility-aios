#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

EXPECTED_ADOPTION_REVISION = "0074_durable_contribution_activity_model"
EXPECTED_HEAD = "0075_legacy_schema_reconciliation"

ALLOWED_MISSING_COLUMNS = {
    "intake_sessions": {"submission_key", "submission_fingerprint"},
    "leads": {
        "nationality", "current_country", "occupation_title", "years_experience",
        "job_offer_status", "qualification_recognition", "german_level", "employment_province",
    },
    "organizational_work_items": {
        "idempotency_fingerprint", "tenant_key", "work_type", "objective_key", "phase_key", "priority",
        "parent_work_item_id", "profile_id", "application_id", "source_object_type", "source_object_id",
        "source_object_version", "requested_by_type", "requested_by_id",
    },
    "executive_decisions": {
        "tenant_key", "decision_type", "record_fingerprint", "lead_id", "profile_id", "application_id",
        "corporate_account_id", "corporate_mobility_case_id", "source_object_type", "source_object_id",
        "source_object_version", "supersedes_decision_id", "conditions_json", "effect_summary", "expires_at",
    },
}


def _sqlite_path(database_url: str) -> Path:
    url = make_url(database_url)
    if not url.drivername.startswith("sqlite"):
        raise RuntimeError("Preserved-schema reconciliation is SQLite-only.")
    if not url.database:
        raise RuntimeError("SQLite URL has no database path.")
    path = Path(url.database)
    if not path.is_absolute():
        path = (ROOT / path).resolve()
    return path


def _read_revision(engine) -> tuple[bool, list[str]]:
    inspector = inspect(engine)
    if "alembic_version" not in inspector.get_table_names():
        return False, []
    with engine.connect() as connection:
        return True, [str(row[0]) for row in connection.execute(text("SELECT version_num FROM alembic_version"))]


def _validate_whitelisted_drift(schema_result: dict) -> None:
    if schema_result["missing_tables"]:
        raise RuntimeError(f"Refusing adoption: missing tables: {schema_result['missing_tables']}")
    if schema_result.get("extra_tables"):
        raise RuntimeError(f"Refusing adoption: unexpected extra tables: {schema_result['extra_tables']}")
    if schema_result["registered_tables"] != schema_result["actual_tables"]:
        raise RuntimeError(
            "Refusing adoption: registered/actual table counts differ "
            f"({schema_result['registered_tables']} != {schema_result['actual_tables']})."
        )

    observed = {table: set(columns) for table, columns in schema_result["missing_columns"].items()}
    unsupported_tables = set(observed) - set(ALLOWED_MISSING_COLUMNS)
    if unsupported_tables:
        raise RuntimeError(f"Refusing adoption: unsupported drift tables: {sorted(unsupported_tables)}")
    for table, columns in observed.items():
        unsupported = columns - ALLOWED_MISSING_COLUMNS[table]
        if unsupported:
            raise RuntimeError(
                f"Refusing adoption: unsupported drift columns in {table}: {sorted(unsupported)}"
            )


def _backup_sqlite(source_path: Path, backup_dir: Path) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    target_path = backup_dir / f"{source_path.stem}-before-0075-{stamp}{source_path.suffix or '.db'}"
    source = sqlite3.connect(f"file:{source_path.as_posix()}?mode=ro", uri=True)
    target = sqlite3.connect(target_path)
    try:
        source.backup(target)
        if source.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise RuntimeError("Source SQLite integrity_check failed.")
        if target.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise RuntimeError("Backup SQLite integrity_check failed.")
    finally:
        target.close()
        source.close()
    return target_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Safely adopt and reconcile a preserved unversioned/empty-stamp SQLite database."
    )
    parser.add_argument(
        "--database-url",
        default="sqlite:///./gmai.db",
        help="Preserved SQLite database URL (default: sqlite:///./gmai.db).",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Create a verified backup, adopt at 0074 when safe, and upgrade through 0075.",
    )
    args = parser.parse_args()

    database_url = args.database_url.strip()
    os.environ["DATABASE_URL"] = database_url

    # Import application metadata only after DATABASE_URL is fixed for this process.
    from alembic import command
    from alembic.config import Config
    from app.core.db import register_models
    from check_local_db_schema import check_local_db_schema

    register_models()
    sqlite_path = _sqlite_path(database_url)
    if not sqlite_path.exists():
        raise RuntimeError(f"Preserved SQLite database does not exist: {sqlite_path}")

    engine = create_engine(database_url, connect_args={"check_same_thread": False})
    schema_result = check_local_db_schema(engine)
    _validate_whitelisted_drift(schema_result)

    has_version_table, revisions = _read_revision(engine)
    if len(revisions) > 1:
        raise RuntimeError(f"Refusing adoption: multiple Alembic revisions found: {revisions}")
    if revisions and revisions[0] not in {EXPECTED_ADOPTION_REVISION, EXPECTED_HEAD}:
        raise RuntimeError(f"Refusing adoption: unexpected Alembic revision {revisions[0]!r}")
    if revisions == [EXPECTED_HEAD]:
        if schema_result["status"] != "ok":
            raise RuntimeError("Database is stamped at 0075 but still has physical schema drift.")
        print("Preserved SQLite database is already reconciled at 0075.")
        return 0

    print("Preserved SQLite reconciliation preflight passed.")
    print(f"database={sqlite_path}")
    print(f"alembic_version_table={'present' if has_version_table else 'absent'}")
    print(f"current_revision={revisions[0] if revisions else '<empty/unversioned>'}")
    print(f"infrastructure_tables={schema_result.get('infrastructure_tables', [])}")
    print(f"missing_columns={schema_result['missing_columns']}")

    if not args.apply:
        print("apply_required=true")
        print("next=rerun with --apply after reviewing the preflight")
        return 0

    backup_path = _backup_sqlite(sqlite_path, ROOT / ".local" / "sqlite-backups")
    print(f"backup={backup_path}")

    # Adopt only after the strict whitelist preflight. The failed historical databases
    # already contain the pre-0075 tables and must not replay 0001..0074.
    with engine.begin() as connection:
        if not has_version_table:
            connection.execute(text(
                "CREATE TABLE alembic_version (version_num VARCHAR(128) NOT NULL PRIMARY KEY)"
            ))
        connection.execute(text("DELETE FROM alembic_version"))
        connection.execute(
            text("INSERT INTO alembic_version (version_num) VALUES (:revision)"),
            {"revision": EXPECTED_ADOPTION_REVISION},
        )
    print(f"adopted_revision={EXPECTED_ADOPTION_REVISION}")

    config = Config(str(ROOT / "alembic.ini"))
    command.upgrade(config, "head")

    post_engine = create_engine(database_url, connect_args={"check_same_thread": False})
    post_schema = check_local_db_schema(post_engine)
    if post_schema["status"] != "ok":
        raise RuntimeError(
            "0075 completed but physical schema parity still failed. "
            f"Backup retained at {backup_path}. Drift: {post_schema['missing_columns']}"
        )
    _, post_revisions = _read_revision(post_engine)
    if post_revisions != [EXPECTED_HEAD]:
        raise RuntimeError(
            f"Expected revision {EXPECTED_HEAD} after reconciliation, got {post_revisions}. "
            f"Backup retained at {backup_path}."
        )

    print("Preserved SQLite reconciliation passed.")
    print(f"revision={EXPECTED_HEAD}")
    print("physical_schema=ok")
    print(f"backup_retained={backup_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
