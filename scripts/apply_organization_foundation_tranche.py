#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlmodel import Session, select

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.core.database_url import is_sqlite_url, mask_database_url, normalize_database_url  # noqa: E402
from app.models.domain import OrganizationControl, OrganizationPosition  # noqa: E402
from app.services.organization_capability_architecture import (  # noqa: E402
    TECHNOLOGY_SECURITY_FOUNDATION_TRANCHE_KEYS,
)
from app.services.organization_governance import POSITION_SPECS, ensure_foundation_positions  # noqa: E402

ACTOR = "phase-13.16.3a2-technology-security-foundation"


def _engine(database_url: str):
    return create_engine(database_url, connect_args={"check_same_thread": False})


def _live_keys(session: Session) -> set[str]:
    return {
        row.position_key
        for row in session.exec(
            select(OrganizationPosition).where(
                OrganizationPosition.version == 1,
                OrganizationPosition.status == "active",
            )
        ).all()
    }


def _preflight(session: Session) -> dict[str, Any]:
    foundation = {item[0] for item in POSITION_SPECS}
    live = _live_keys(session)
    extra = live - foundation
    missing = foundation - live
    unexpected_missing = missing - TECHNOLOGY_SECURITY_FOUNDATION_TRANCHE_KEYS
    global_control = session.exec(
        select(OrganizationControl).where(OrganizationControl.control_key == "global")
    ).first()

    if global_control is None:
        raise RuntimeError(
            "Refusing foundation expansion: global OrganizationControl is missing; "
            "this tranche must not bootstrap unrelated organization state."
        )
    if extra:
        raise RuntimeError(
            f"Refusing foundation expansion: unexpected live position keys: {sorted(extra)}"
        )
    if unexpected_missing:
        raise RuntimeError(
            "Refusing foundation expansion: missing pre-existing foundation keys outside the "
            f"Technology + Security tranche: {sorted(unexpected_missing)}"
        )

    return {
        "foundation_count": len(foundation),
        "live_count": len(live),
        "missing_keys": sorted(missing),
        "missing_tranche_keys": sorted(missing & TECHNOLOGY_SECURITY_FOUNDATION_TRANCHE_KEYS),
        "already_present_tranche_keys": sorted(TECHNOLOGY_SECURITY_FOUNDATION_TRANCHE_KEYS & live),
    }


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
    backup_path = backup_dir / f"gmai-before-13.16.3a2-{stamp}.db"

    source = sqlite3.connect(f"file:{source_path.as_posix()}?mode=ro", uri=True)
    target = sqlite3.connect(backup_path)
    try:
        source.backup(target)
        source_integrity = source.execute("PRAGMA integrity_check").fetchone()[0]
        target_integrity = target.execute("PRAGMA integrity_check").fetchone()[0]
        if source_integrity != "ok" or target_integrity != "ok":
            raise RuntimeError(
                f"SQLite backup integrity check failed: source={source_integrity}, backup={target_integrity}"
            )
    finally:
        target.close()
        source.close()
    return backup_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Guarded local SQLite application of the Phase 13.16.3A.2 Technology + Security "
            "organization-foundation tranche. The operation is additive and does not repair, "
            "delete, suspend, delegate, or grant execution authority."
        )
    )
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    database_url = normalize_database_url(args.database_url)
    if not is_sqlite_url(database_url):
        raise RuntimeError(
            "Refusing foundation expansion: this controlled helper is limited to the preserved local SQLite database."
        )

    engine = _engine(database_url)
    with Session(engine) as session:
        before = _preflight(session)

    print("Organization foundation tranche preflight passed.")
    print(f"database_url={mask_database_url(database_url)}")
    print(f"foundation_positions={before['foundation_count']}")
    print(f"live_active_positions={before['live_count']}")
    print(f"missing_tranche_keys={before['missing_tranche_keys']}")
    print(f"already_present_tranche_keys={before['already_present_tranche_keys']}")
    print("mutation_scope=add missing Technology + Security foundation positions only")
    print("execution_authority_added=false")
    print("delegation_sets_changed=false")

    if not args.apply:
        print("apply_required=" + ("true" if before["missing_tranche_keys"] else "false"))
        print("next=rerun with --apply only after reviewing this preflight")
        return 0

    if not before["missing_tranche_keys"]:
        print("result=already_applied")
        return 0

    backup_path = _backup_sqlite(database_url)
    print(f"backup={backup_path}")

    with Session(engine) as session:
        ensure_foundation_positions(session, actor=ACTOR, repair_contracts=False)
        session.commit()

    with Session(engine) as session:
        after = _preflight(session)

    if after["missing_keys"]:
        raise RuntimeError(
            f"Foundation expansion incomplete; missing keys remain: {after['missing_keys']}"
        )
    created = sorted(set(before["missing_tranche_keys"]) - set(after["missing_tranche_keys"]))
    if set(created) != set(before["missing_tranche_keys"]):
        raise RuntimeError(
            "Foundation expansion verification failed: created set did not match the preflight missing tranche."
        )

    print("Organization foundation tranche applied.")
    print(f"created_count={len(created)}")
    print(f"created_keys={created}")
    print(f"live_active_positions={after['live_count']}")
    print("existing_positions_updated=false")
    print("positions_deleted=false")
    print("positions_suspended=false")
    print("execution_authority_added=false")
    print("delegation_sets_changed=false")
    print("result=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
