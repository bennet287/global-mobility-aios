#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"

if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.core.config import settings  # noqa: E402
from app.core.database_url import is_sqlite_url, mask_database_url, normalize_database_url  # noqa: E402
from app.core.db import register_models  # noqa: E402
from sqlmodel import SQLModel  # noqa: E402


INFRASTRUCTURE_TABLES = {"alembic_version"}


def _engine_for_url(database_url: str) -> Engine:
    normalized = normalize_database_url(database_url)
    connect_args = {"check_same_thread": False} if is_sqlite_url(normalized) else {}
    return create_engine(normalized, connect_args=connect_args)


def check_local_db_schema(engine: Engine) -> dict[str, Any]:
    register_models()
    inspector = inspect(engine)
    expected_tables = SQLModel.metadata.tables
    physical_tables = set(inspector.get_table_names())
    infrastructure_tables = sorted(physical_tables & INFRASTRUCTURE_TABLES)
    actual_tables = physical_tables - INFRASTRUCTURE_TABLES

    missing_tables: dict[str, list[str]] = {}
    missing_columns: dict[str, list[str]] = {}
    extra_tables = sorted(actual_tables - set(expected_tables))

    for table_name, table in sorted(expected_tables.items()):
        expected_columns = sorted(table.columns.keys())
        if table_name not in actual_tables:
            missing_tables[table_name] = expected_columns
            continue

        actual_columns = {column["name"] for column in inspector.get_columns(table_name)}
        missing = sorted(set(expected_columns) - actual_columns)
        if missing:
            missing_columns[table_name] = missing

    ok = not missing_tables and not missing_columns and not extra_tables
    return {
        "status": "ok" if ok else "schema_drift",
        "registered_tables": len(expected_tables),
        "actual_tables": len(actual_tables),
        "physical_tables": len(physical_tables),
        "infrastructure_tables": infrastructure_tables,
        "missing_tables": missing_tables,
        "missing_columns": missing_columns,
        "extra_tables": extra_tables,
        "suggested_local_demo_fix": (
            "Do not reset a preserved database merely to clear drift. Apply the current "
            "Alembic head first; only disposable demo databases should be recreated with "
            "`python scripts/seed_demo_data.py --reset-all --yes`."
            if not ok
            else None
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check local database schema against SQLModel metadata.")
    parser.add_argument("--database-url", default=settings.database_url, help="Database URL to inspect.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON only.")
    args = parser.parse_args()

    database_url = normalize_database_url(args.database_url)
    result = check_local_db_schema(_engine_for_url(database_url))
    result["database_url"] = mask_database_url(database_url)

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("Local DB schema check " + ("passed." if result["status"] == "ok" else "found schema drift."))
        print(f"database_url={result['database_url']}")
        print(f"registered_tables={result['registered_tables']}")
        print(f"actual_tables={result['actual_tables']}")
        print(f"physical_tables={result['physical_tables']}")
        if result["infrastructure_tables"]:
            print("infrastructure_tables=" + json.dumps(result["infrastructure_tables"]))
        if result["missing_tables"]:
            print("missing_tables=" + json.dumps(result["missing_tables"], sort_keys=True))
        if result["missing_columns"]:
            print("missing_columns=" + json.dumps(result["missing_columns"], sort_keys=True))
        if result["suggested_local_demo_fix"]:
            print("suggested_fix=" + result["suggested_local_demo_fix"])

    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
