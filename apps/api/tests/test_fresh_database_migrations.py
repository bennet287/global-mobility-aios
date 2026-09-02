from __future__ import annotations

import json
import os
import subprocess
import sys
from uuid import uuid4
from pathlib import Path

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKeyConstraint,
    MetaData,
    String,
    Table,
    UniqueConstraint,
    create_engine,
    inspect,
    text,
)
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
    assert schema_result["extra_tables"] == []
    assert schema_result["infrastructure_tables"] == ["alembic_version"]
    assert schema_result["registered_tables"] == schema_result["actual_tables"]
    assert schema_result["physical_tables"] == schema_result["actual_tables"] + 1

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
            "0081_capability_autonomy_evidence_evaluation_policy"
        )
        position_inspector = inspect(connection)
        position_indexes = {
            index["name"]: index for index in position_inspector.get_indexes("organization_positions")
        }
        position_unique_constraints = {
            constraint["name"]: constraint
            for constraint in position_inspector.get_unique_constraints("organization_positions")
            if constraint.get("name")
        }
        assert "uq_org_position_version" in position_unique_constraints
        assert tuple(position_unique_constraints["uq_org_position_version"].get("column_names") or ()) == (
            "position_key",
            "version",
        )
        assert "ux_organization_positions_active_position_key" in position_indexes
        assert position_indexes["ux_organization_positions_active_position_key"].get("unique") in {True, 1}
        for table in durable_tables:
            assert connection.execute(text(f"SELECT count(*) FROM {table}")).scalar_one() == 0




def test_0076_refuses_duplicate_active_organization_position_identity(tmp_path: Path) -> None:
    database_path = tmp_path / "duplicate-organization-position.db"
    database_url = f"sqlite:///{database_path.as_posix()}"
    env = {**os.environ, "DATABASE_URL": database_url}

    # Reproduce the preserved-SQLite condition that motivated 0076 rather than a
    # normal fresh 0075 schema. Fresh databases already have uq_org_position_version
    # from 0056 and therefore correctly reject the duplicate before 0076 can see it.
    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE organization_positions (
                    id TEXT PRIMARY KEY NOT NULL,
                    position_key TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    status TEXT NOT NULL
                )
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO organization_positions (id, position_key, version, status)
                VALUES
                    (:first_id, 'board', 1, 'active'),
                    (:second_id, 'board', 1, 'active')
                """
            ),
            {"first_id": str(uuid4()), "second_id": str(uuid4())},
        )
        connection.execute(
            text(
                """
                CREATE TABLE alembic_version (
                    version_num VARCHAR(64) NOT NULL PRIMARY KEY
                )
                """
            )
        )
        connection.execute(
            text("INSERT INTO alembic_version (version_num) VALUES (:revision)"),
            {"revision": "0075_legacy_schema_reconciliation"},
        )

    to_head = subprocess.run(
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
    assert to_head.returncode != 0
    output = (to_head.stderr or "") + (to_head.stdout or "")
    assert "0076 refuses to hide duplicate active organization identities" in output


def test_0076_restores_position_version_uniqueness_on_preserved_like_0075(tmp_path: Path) -> None:
    database_path = tmp_path / "reconciled-organization-position.db"
    database_url = f"sqlite:///{database_path.as_posix()}"
    env = {**os.environ, "DATABASE_URL": database_url}

    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE organization_positions (
                    id TEXT PRIMARY KEY NOT NULL,
                    position_key TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    status TEXT NOT NULL
                )
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO organization_positions (id, position_key, version, status)
                VALUES
                    (:canonical_id, 'board', 1, 'active'),
                    (:archived_id, 'board', 2, 'suspended')
                """
            ),
            {"canonical_id": str(uuid4()), "archived_id": str(uuid4())},
        )
        connection.execute(
            text(
                """
                CREATE TABLE alembic_version (
                    version_num VARCHAR(64) NOT NULL PRIMARY KEY
                )
                """
            )
        )
        connection.execute(
            text("INSERT INTO alembic_version (version_num) VALUES (:revision)"),
            {"revision": "0075_legacy_schema_reconciliation"},
        )

    to_head = subprocess.run(
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
    assert to_head.returncode == 0, to_head.stderr or to_head.stdout

    inspector = inspect(create_engine(database_url))
    indexes = {
        index["name"]: index
        for index in inspector.get_indexes("organization_positions")
        if index.get("name")
    }
    assert "ux_organization_positions_position_key_version_reconciled" in indexes
    assert indexes["ux_organization_positions_position_key_version_reconciled"].get("unique") in {True, 1}
    assert "ux_organization_positions_active_position_key" in indexes
    assert indexes["ux_organization_positions_active_position_key"].get("unique") in {True, 1}


def test_0075_reconciles_stamped_legacy_extension_drift(tmp_path: Path) -> None:
    database_path = tmp_path / "stamped-legacy-drift.db"
    database_url = f"sqlite:///{database_path.as_posix()}"
    engine = create_engine(database_url)

    register_models()
    source_tables = SQLModel.metadata.tables
    legacy_metadata = MetaData()

    work_missing = {
        "idempotency_fingerprint", "tenant_key", "work_type", "objective_key", "phase_key", "priority",
        "parent_work_item_id", "profile_id", "application_id", "source_object_type", "source_object_id",
        "source_object_version", "requested_by_type", "requested_by_id",
    }
    decision_missing = {
        "tenant_key", "decision_type", "record_fingerprint", "lead_id", "profile_id", "application_id",
        "corporate_account_id", "corporate_mobility_case_id", "source_object_type", "source_object_id",
        "source_object_version", "supersedes_decision_id", "conditions_json", "effect_summary", "expires_at",
    }
    lead_missing = {
        "nationality", "current_country", "occupation_title", "years_experience", "job_offer_status",
        "qualification_recognition", "german_level", "employment_province",
    }
    intake_missing = {"submission_key", "submission_fingerprint"}

    def clone_legacy_table(table_name: str, excluded: set[str]) -> None:
        source = source_tables[table_name]
        columns = [
            Column(
                column.name,
                column.type,
                primary_key=column.primary_key,
                nullable=column.nullable,
            )
            for column in source.columns
            if column.name not in excluded
        ]
        Table(table_name, legacy_metadata, *columns)

    clone_legacy_table("leads", lead_missing)
    clone_legacy_table("organizational_work_items", work_missing)
    clone_legacy_table("executive_decisions", decision_missing)
    for table_name in ("profiles", "applications", "corporate_accounts", "corporate_mobility_cases"):
        source_id = source_tables[table_name].columns["id"]
        Table(
            table_name,
            legacy_metadata,
            Column("id", source_id.type, primary_key=True, nullable=False),
        )
    Table(
        "intake_sessions",
        legacy_metadata,
        Column("id", source_tables["intake_sessions"].columns["id"].type, primary_key=True, nullable=False),
        Column("lead_id", source_tables["leads"].columns["id"].type, nullable=True),
        Column("answers_json", String(), nullable=True),
        Column("updated_at", DateTime(), nullable=False),
    )
    Table("alembic_version", legacy_metadata, Column("version_num", String(128), primary_key=True))
    legacy_metadata.create_all(engine)

    lead_id = uuid4().hex
    intake_id = uuid4().hex
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO leads "
                "(id, full_name, email, phone, source, intent, target_country, status, notes, created_at, updated_at) "
                "VALUES (:id, 'Legacy Lead', NULL, NULL, 'public_intake', 'visa', 'AT', 'new', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
            ),
            {"id": lead_id},
        )
        connection.execute(
            text(
                "INSERT INTO intake_sessions (id, lead_id, answers_json, updated_at) "
                "VALUES (:id, :lead_id, :answers_json, CURRENT_TIMESTAMP)"
            ),
            {
                "id": intake_id,
                "lead_id": lead_id,
                "answers_json": json.dumps(
                    {
                        "nationality": "IN",
                        "current_country": "AT",
                        "profession": "Software Engineer",
                        "years_experience": 5,
                        "job_offer_status": "absent",
                        "qualification_recognition": "unresolved",
                        "language_level": "A2",
                        "employment_province": "Vienna",
                    }
                ),
            },
        )
        connection.execute(
            text("INSERT INTO alembic_version (version_num) VALUES ('0074_durable_contribution_activity_model')")
        )

    env = {**os.environ, "DATABASE_URL": database_url}
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            str(ROOT / "alembic.ini"),
            "upgrade",
            "0075_legacy_schema_reconciliation",
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=ALEMBIC_CHAIN_TIMEOUT_SECONDS,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout

    schema_result = check_local_db_schema(engine)
    assert schema_result["status"] == "schema_drift"  # minimal fixture intentionally omits unrelated tables
    assert "leads" not in schema_result["missing_columns"]
    assert "organizational_work_items" not in schema_result["missing_columns"]
    assert "executive_decisions" not in schema_result["missing_columns"]

    inspector = inspect(engine)
    assert work_missing <= {column["name"] for column in inspector.get_columns("organizational_work_items")}
    assert decision_missing <= {column["name"] for column in inspector.get_columns("executive_decisions")}
    assert lead_missing <= {column["name"] for column in inspector.get_columns("leads")}
    assert intake_missing <= {column["name"] for column in inspector.get_columns("intake_sessions")}
    intake_indexes = {index["name"]: index for index in inspector.get_indexes("intake_sessions")}
    assert "ix_intake_sessions_submission_key" in intake_indexes
    assert intake_indexes["ix_intake_sessions_submission_key"].get("unique") in {True, 1}
    assert "ix_org_work_tenant_status_due" in {
        index["name"] for index in inspector.get_indexes("organizational_work_items")
    }
    assert "ix_exec_decision_tenant_status_due" in {
        index["name"] for index in inspector.get_indexes("executive_decisions")
    }

    with engine.connect() as connection:
        assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == (
            "0075_legacy_schema_reconciliation"
        )
        row = connection.execute(
            text(
                "SELECT nationality, current_country, occupation_title, years_experience, job_offer_status, "
                "qualification_recognition, german_level, employment_province FROM leads WHERE id=:lead_id"
            ),
            {"lead_id": lead_id},
        ).one()
    assert tuple(row) == ("IN", "AT", "Software Engineer", 5.0, "absent", "unresolved", "A2", "Vienna")


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