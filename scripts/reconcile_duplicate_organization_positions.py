#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import make_url
from sqlmodel import Session, select

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.core.database_url import is_sqlite_url, mask_database_url, normalize_database_url  # noqa: E402
from app.models.domain import OrganizationPosition  # noqa: E402
from app.services.audit_log import record_audit  # noqa: E402
from app.services.organization_governance import POSITION_SPECS  # noqa: E402


ACTOR = "phase-13.16.3a3r-position-identity-reconciliation"
SOURCE = "organization_position_identity_reconciliation_v1"


def _engine(database_url: str):
    return create_engine(database_url, connect_args={"check_same_thread": False})


def _sqlite_path(database_url: str) -> Path:
    database = make_url(database_url).database
    if not database:
        raise RuntimeError("SQLite database path could not be resolved.")
    path = Path(database)
    if not path.is_absolute():
        path = (ROOT / path).resolve()
    return path


def _backup_sqlite(database_url: str) -> Path:
    source_path = _sqlite_path(database_url)
    backup_dir = ROOT / ".local" / "sqlite-backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = backup_dir / f"gmai-before-13.16.3a3r-position-identity-{stamp}.db"

    source = sqlite3.connect(f"file:{source_path.as_posix()}?mode=ro", uri=True)
    target = sqlite3.connect(backup_path)
    try:
        source.backup(target)
        source_integrity = source.execute("PRAGMA integrity_check").fetchone()[0]
        target_integrity = target.execute("PRAGMA integrity_check").fetchone()[0]
        if source_integrity != "ok" or target_integrity != "ok":
            raise RuntimeError(
                "SQLite backup integrity check failed: "
                f"source={source_integrity}, backup={target_integrity}"
            )
    finally:
        target.close()
        source.close()
    return backup_path


def _active_rows(session: Session) -> list[OrganizationPosition]:
    return list(
        session.exec(
            select(OrganizationPosition).where(OrganizationPosition.status == "active")
        ).all()
    )


def _group_active(rows: list[OrganizationPosition]) -> dict[str, list[OrganizationPosition]]:
    grouped: dict[str, list[OrganizationPosition]] = defaultdict(list)
    for row in rows:
        grouped[row.position_key].append(row)
    return {
        key: sorted(items, key=lambda item: (item.created_at, str(item.id)))
        for key, items in grouped.items()
    }


def _duplicate_key_versions(session: Session) -> dict[tuple[str, int], list[OrganizationPosition]]:
    grouped: dict[tuple[str, int], list[OrganizationPosition]] = defaultdict(list)
    for row in session.exec(select(OrganizationPosition)).all():
        grouped[(row.position_key, row.version)].append(row)
    return {
        identity: sorted(items, key=lambda item: (item.created_at, str(item.id)))
        for identity, items in grouped.items()
        if len(items) > 1
    }


def _next_archival_versions(
    session: Session,
    position_key: str,
    count: int,
) -> list[int]:
    existing_versions = [
        row.version
        for row in session.exec(
            select(OrganizationPosition).where(
                OrganizationPosition.position_key == position_key
            )
        ).all()
    ]
    next_version = max(existing_versions, default=0) + 1
    return list(range(next_version, next_version + count))


def _semantic_signature(position: OrganizationPosition) -> tuple[Any, ...]:
    return (
        position.position_key,
        position.title,
        position.department,
        position.reports_to_position_key,
        position.role_card_name,
        position.authority_level,
        position.contract_json,
        position.status,
        position.version,
        position.created_by,
    )


def _foreign_key_references_to_position_ids(engine) -> list[str]:
    inspector = inspect(engine)
    references: list[str] = []
    for table_name in inspector.get_table_names():
        if table_name == "organization_positions":
            continue
        for foreign_key in inspector.get_foreign_keys(table_name):
            if foreign_key.get("referred_table") != "organization_positions":
                continue
            references.append(
                f"{table_name}:{foreign_key.get('constrained_columns')}->"
                f"organization_positions:{foreign_key.get('referred_columns')}"
            )
    return sorted(references)


def _preflight(session: Session, engine) -> dict[str, Any]:
    foundation = {item[0] for item in POSITION_SPECS}
    active = _active_rows(session)
    grouped = _group_active(active)
    duplicates = {key: rows for key, rows in grouped.items() if len(rows) > 1}

    active_v1_keys = {
        row.position_key for row in active if row.version == 1
    }
    extra = active_v1_keys - foundation
    missing = foundation - active_v1_keys
    if extra or missing:
        raise RuntimeError(
            "Refusing duplicate reconciliation while foundation coverage also drifts: "
            f"extra={sorted(extra)}, missing={sorted(missing)}"
        )

    non_foundation_duplicates = set(duplicates) - foundation
    if non_foundation_duplicates:
        raise RuntimeError(
            "Refusing duplicate reconciliation for non-foundation position identities: "
            f"{sorted(non_foundation_duplicates)}"
        )

    nonidentical: list[str] = []
    wrong_version: list[str] = []
    for key, rows in duplicates.items():
        if any(row.version != 1 for row in rows):
            wrong_version.append(key)
            continue
        signatures = {_semantic_signature(row) for row in rows}
        if len(signatures) != 1:
            nonidentical.append(key)
    if wrong_version:
        raise RuntimeError(
            "Refusing automatic reconciliation for duplicate identities spanning non-v1 rows: "
            f"{sorted(wrong_version)}"
        )
    if nonidentical:
        raise RuntimeError(
            "Refusing automatic reconciliation because duplicate rows differ semantically: "
            f"{sorted(nonidentical)}"
        )

    duplicate_key_versions = _duplicate_key_versions(session)
    expected_duplicate_ids = {
        row.id
        for rows in duplicates.values()
        for row in rows
    }
    unexpected_version_duplicates = {
        identity: rows
        for identity, rows in duplicate_key_versions.items()
        if {row.id for row in rows} - expected_duplicate_ids
        or any(row.status != "active" for row in rows)
    }
    if unexpected_version_duplicates:
        summary = [
            f"{key}@v{version}"
            for key, version in sorted(unexpected_version_duplicates)
        ]
        raise RuntimeError(
            "Refusing automatic reconciliation because unrelated duplicate "
            f"(position_key, version) identities exist: {summary}"
        )

    foreign_key_references = _foreign_key_references_to_position_ids(engine)
    if foreign_key_references:
        raise RuntimeError(
            "Refusing automatic reconciliation because another table has a physical foreign key to "
            "organization_positions; identity-level impact requires manual review: "
            f"{foreign_key_references}"
        )

    redundant = sum(len(rows) - 1 for rows in duplicates.values())
    return {
        "foundation_count": len(foundation),
        "active_row_count": len(active),
        "distinct_active_key_count": len(grouped),
        "duplicates": duplicates,
        "duplicate_key_count": len(duplicates),
        "redundant_active_row_count": redundant,
        "duplicate_key_version_count": len(duplicate_key_versions),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Guarded local-SQLite reconciliation for semantically identical duplicate active "
            "OrganizationPosition identities. Preflight is read-only. --apply creates an "
            "integrity-checked backup and suspends only redundant rows; rows are never deleted."
        )
    )
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    database_url = normalize_database_url(args.database_url)
    if not is_sqlite_url(database_url):
        raise RuntimeError(
            "Refusing duplicate-position reconciliation: this helper is limited to the preserved local SQLite database."
        )

    engine = _engine(database_url)
    with Session(engine) as session:
        before = _preflight(session, engine)

    print("OrganizationPosition active-identity reconciliation preflight passed.")
    print(f"database_url={mask_database_url(database_url)}")
    print(f"foundation_positions={before['foundation_count']}")
    print(f"active_rows={before['active_row_count']}")
    print(f"distinct_active_position_keys={before['distinct_active_key_count']}")
    print(f"duplicate_key_count={before['duplicate_key_count']}")
    print(f"redundant_active_row_count={before['redundant_active_row_count']}")
    print(f"duplicate_key_version_count={before['duplicate_key_version_count']}")
    for key, rows in sorted(before["duplicates"].items()):
        canonical = rows[0]
        redundant_rows = rows[1:]
        print(
            f"duplicate={key} canonical_id={canonical.id} "
            f"redundant_ids={[str(row.id) for row in redundant_rows]}"
        )
    print("mutation_scope=suspend semantically identical redundant active foundation rows and assign non-colliding archival versions only")
    print("rows_deleted=false")
    print("foundation_positions_added=false")
    print("execution_authority_added=false")
    print("delegation_sets_changed=false")

    if not args.apply:
        print("apply_required=" + ("true" if before["duplicate_key_count"] else "false"))
        print("next=rerun with --apply only after reviewing canonical and redundant row identities")
        return 0

    if not before["duplicate_key_count"]:
        print("result=already_reconciled")
        return 0

    backup_path = _backup_sqlite(database_url)
    print(f"backup={backup_path}")

    suspended_ids: list[str] = []
    canonical_ids: dict[str, str] = {}
    now = datetime.now(timezone.utc)
    with Session(engine) as session:
        current = _preflight(session, engine)
        archived_versions: dict[str, int] = {}
        for key, rows in sorted(current["duplicates"].items()):
            canonical = rows[0]
            canonical_ids[key] = str(canonical.id)
            archival_versions = _next_archival_versions(session, key, len(rows) - 1)
            for redundant, archival_version in zip(rows[1:], archival_versions, strict=True):
                before_state = {
                    "position_key": redundant.position_key,
                    "status": redundant.status,
                    "version": redundant.version,
                    "canonical_position_id": str(canonical.id),
                }
                redundant.version = archival_version
                redundant.status = "suspended"
                redundant.suspended_at = now
                redundant.suspended_by = ACTOR
                redundant.suspended_reason = (
                    "Semantically identical duplicate active OrganizationPosition identity; "
                    f"canonical row preserved as {canonical.id}; redundant row archived as version "
                    f"{archival_version}."
                )
                redundant.updated_at = now
                session.add(redundant)
                record_audit(
                    session,
                    action="organization_position_duplicate_suspended",
                    entity_type="organization_position",
                    entity_id=redundant.id,
                    before_state=before_state,
                    after_state={
                        "position_key": redundant.position_key,
                        "status": redundant.status,
                        "version": redundant.version,
                        "canonical_position_id": str(canonical.id),
                        "suspended_by": ACTOR,
                    },
                    reason=(
                        "Reconcile duplicate active organization identity without deleting history; "
                        "assign a non-colliding archival version so the original position/version "
                        "identity invariant can be restored."
                    ),
                    actor=ACTOR,
                    source=SOURCE,
                )
                suspended_ids.append(str(redundant.id))
                archived_versions[str(redundant.id)] = archival_version
        session.commit()

    with Session(engine) as session:
        after = _preflight(session, engine)
    if after["duplicate_key_count"] != 0:
        raise RuntimeError(
            "Duplicate-position reconciliation verification failed; active duplicates remain: "
            f"{sorted(after['duplicates'])}"
        )
    if after["active_row_count"] != after["foundation_count"]:
        raise RuntimeError(
            "Duplicate-position reconciliation verification failed; active row count does not equal "
            f"foundation count: active={after['active_row_count']}, foundation={after['foundation_count']}"
        )
    if after["duplicate_key_version_count"] != 0:
        raise RuntimeError(
            "Duplicate-position reconciliation verification failed; duplicate position/version "
            "identities remain."
        )

    print("OrganizationPosition active-identity reconciliation applied.")
    print(f"canonical_ids={canonical_ids}")
    print(f"suspended_count={len(suspended_ids)}")
    print(f"suspended_ids={suspended_ids}")
    print(f"archived_versions={archived_versions}")
    print(f"active_rows={after['active_row_count']}")
    print(f"distinct_active_position_keys={after['distinct_active_key_count']}")
    print("rows_deleted=false")
    print("foundation_positions_added=false")
    print("execution_authority_added=false")
    print("delegation_sets_changed=false")
    print("result=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
