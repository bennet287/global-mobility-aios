from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import CheckConstraint, ForeignKeyConstraint, UniqueConstraint, create_engine, inspect, text
from sqlmodel import SQLModel

from app.core.db import register_models
from scripts.check_local_db_schema import check_local_db_schema


ROOT = Path(__file__).resolve().parents[3]

ALEMBIC_CHAIN_TIMEOUT_SECONDS = 180


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
        timeout=ALEMBIC_CHAIN_TIMEOUT_SECONDS,
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
        timeout=ALEMBIC_CHAIN_TIMEOUT_SECONDS,
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
        timeout=ALEMBIC_CHAIN_TIMEOUT_SECONDS,
        check=False,
    )
    assert reupgrade.returncode == 0, reupgrade.stderr or reupgrade.stdout

    register_models()
    schema_result = check_local_db_schema(create_engine(database_url))
    assert schema_result["status"] == "ok"
    assert schema_result["missing_tables"] == {}
    assert schema_result["missing_columns"] == {}

    inspector = inspect(create_engine(database_url))
    durable_tables = {
        "organization_activity_streams",
        "organization_activities",
        "organization_contributions",
        "organization_work_item_dependencies",
        "organization_blockers",
        "organization_human_action_requests",
        "organization_human_actions",
        "organization_record_references",
    }
    assert durable_tables <= set(inspector.get_table_names())
    for table_name in durable_tables:
        metadata_table = SQLModel.metadata.tables[table_name]
        assert {index.name for index in metadata_table.indexes} == {
            index["name"] for index in inspector.get_indexes(table_name)
        }
        assert {
            constraint.name
            for constraint in metadata_table.constraints
            if isinstance(constraint, CheckConstraint)
        } == {constraint["name"] for constraint in inspector.get_check_constraints(table_name)}
        assert {
            constraint.name
            for constraint in metadata_table.constraints
            if isinstance(constraint, UniqueConstraint)
        } == {constraint["name"] for constraint in inspector.get_unique_constraints(table_name)}
        assert sum(
            isinstance(constraint, ForeignKeyConstraint) for constraint in metadata_table.constraints
        ) == len(inspector.get_foreign_keys(table_name))
    expected_extension_indexes = {
        "organizational_work_items": {
            "ix_org_work_tenant_status_due",
            "ix_org_work_tenant_department_status",
            "ix_organizational_work_items_idempotency_fingerprint",
            "ix_organizational_work_items_tenant_key",
            "ix_organizational_work_items_work_type",
            "ix_organizational_work_items_objective_key",
            "ix_organizational_work_items_phase_key",
            "ix_organizational_work_items_priority",
            "ix_organizational_work_items_parent_work_item_id",
            "ix_organizational_work_items_profile_id",
            "ix_organizational_work_items_application_id",
            "ix_organizational_work_items_source_object_type",
            "ix_organizational_work_items_source_object_id",
            "ix_organizational_work_items_requested_by_type",
            "ix_organizational_work_items_requested_by_id",
        },
        "executive_decisions": {
            "ix_exec_decision_tenant_status_due",
            "ix_executive_decisions_tenant_key",
            "ix_executive_decisions_decision_type",
            "ix_executive_decisions_record_fingerprint",
            "ix_executive_decisions_lead_id",
            "ix_executive_decisions_profile_id",
            "ix_executive_decisions_application_id",
            "ix_executive_decisions_corporate_account_id",
            "ix_executive_decisions_corporate_mobility_case_id",
            "ix_executive_decisions_source_object_type",
            "ix_executive_decisions_source_object_id",
            "ix_executive_decisions_supersedes_decision_id",
            "ix_executive_decisions_expires_at",
        },
    }
    for table_name, expected_indexes in expected_extension_indexes.items():
        assert expected_indexes <= {index["name"] for index in inspector.get_indexes(table_name)}
    with create_engine(database_url).connect() as connection:
        assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == (
            "0074_durable_contribution_activity_model"
        )
        for table in durable_tables:
            assert connection.execute(text(f"SELECT count(*) FROM {table}")).scalar_one() == 0


def test_migrations_do_not_use_integer_defaults_for_boolean_columns() -> None:
    versions = ROOT / "alembic" / "versions"

    forbidden = (
        'sa.Boolean(), nullable=False, server_default=sa.text("0")',
        'sa.Boolean(), nullable=False, server_default=sa.text("1")',
    )

    violations: list[str] = []

    for migration in sorted(versions.glob("*.py")):
        source = migration.read_text(encoding="utf-8")
        for pattern in forbidden:
            if pattern in source:
                violations.append(f"{migration.name}: {pattern}")

    assert violations == [], (
        "Boolean migration defaults must be cross-dialect safe "
        "(use sa.false()/sa.true()), not integer 0/1 defaults:\n"
        + "\n".join(violations)
    )



def test_organization_position_migration_binds_preserve_uuid_type() -> None:
    versions = ROOT / "alembic" / "versions"

    violations: list[str] = []

    for migration in sorted(versions.glob("*.py")):
        source = migration.read_text(encoding="utf-8")

        if (
            'sa.table(' in source
            and '"organization_positions"' in source
            and 'sa.column("id", sa.String())' in source
        ):
            violations.append(migration.name)

    assert violations == [], (
        "organization_positions.id is UUID in PostgreSQL; "
        "migration table bindings must use sa.Uuid(...), not sa.String():\n"
        + "\n".join(violations)
    )


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


def test_postgresql_offline_durable_migration_sql_compiles() -> None:
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
            "0073_austria_candidate_integrity:0074_durable_contribution_activity_model",
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
