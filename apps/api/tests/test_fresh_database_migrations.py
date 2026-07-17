from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine

from app.core.db import register_models
from scripts.check_local_db_schema import check_local_db_schema


ROOT = Path(__file__).resolve().parents[3]


def test_fresh_database_upgrades_to_current_schema(tmp_path: Path) -> None:
    database_path = tmp_path / "fresh-migrations.db"
    database_url = f"sqlite:///{database_path.as_posix()}"
    env = {**os.environ, "DATABASE_URL": database_url}

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            str(ROOT / "alembic.ini"),
            "upgrade",
            "head",
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout

    downgrade = subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            str(ROOT / "alembic.ini"),
            "downgrade",
            "0010_authority_parser_profiles",
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert downgrade.returncode == 0, downgrade.stderr or downgrade.stdout

    reupgrade = subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            str(ROOT / "alembic.ini"),
            "upgrade",
            "head",
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert reupgrade.returncode == 0, reupgrade.stderr or reupgrade.stdout

    register_models()
    schema_result = check_local_db_schema(create_engine(database_url))
    assert schema_result["status"] == "ok"
    assert schema_result["missing_tables"] == {}
    assert schema_result["missing_columns"] == {}

def test_postgresql_offline_migration_sql_compiles() -> None:
    env = {
        **os.environ,
        "DATABASE_URL": "postgresql+psycopg://gmai:gmai@localhost:5432/gmai",
    }
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            str(ROOT / "alembic.ini"),
            "upgrade",
            "0031_global_coverage_source_onboarding:0032_initial_rule_assertions",
            "--sql",
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout

