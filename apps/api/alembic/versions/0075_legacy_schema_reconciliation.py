"""Reconcile preserved legacy tables with the intended 0072/0073/0074 schema.

Revision ID: 0075_legacy_schema_reconciliation
Revises: 0074_durable_contribution_activity_model
Create Date: 2026-08-15

This migration is intentionally compatibility-safe. Correctly migrated 0074 databases
already contain every column, constraint, and index below, so the upgrade is a no-op for
them. It repairs databases that were stamped forward while retaining older physical
versions of intake_sessions, leads, organizational_work_items, or executive_decisions.
"""

from __future__ import annotations

import json

from alembic import op
import sqlalchemy as sa


revision = "0075_legacy_schema_reconciliation"
down_revision = "0074_durable_contribution_activity_model"
branch_labels = None
depends_on = None


def _uuid() -> sa.Uuid:
    return sa.Uuid()


def _inspector() -> sa.Inspector:
    return sa.inspect(op.get_bind())


def _require_table(table_name: str) -> None:
    if table_name not in _inspector().get_table_names():
        raise RuntimeError(
            f"0075 reconciliation requires existing table {table_name!r}; "
            "the database is not a compatible stamped legacy schema"
        )


def _column_names(table_name: str) -> set[str]:
    return {column["name"] for column in _inspector().get_columns(table_name)}


def _index_names(table_name: str) -> set[str]:
    return {index["name"] for index in _inspector().get_indexes(table_name) if index.get("name")}


def _named_constraints(table_name: str) -> tuple[set[str], set[str], set[str]]:
    inspector = _inspector()
    unique_names = {
        item["name"] for item in inspector.get_unique_constraints(table_name) if item.get("name")
    }
    check_names = {
        item["name"] for item in inspector.get_check_constraints(table_name) if item.get("name")
    }
    foreign_key_names = {
        item["name"] for item in inspector.get_foreign_keys(table_name) if item.get("name")
    }
    return unique_names, check_names, foreign_key_names



def _reconcile_intake_sessions() -> None:
    table = "intake_sessions"
    _require_table(table)
    existing = _column_names(table)
    missing = [
        name
        for name in ("submission_key", "submission_fingerprint")
        if name not in existing
    ]
    if missing:
        with op.batch_alter_table(table) as batch:
            if "submission_key" in missing:
                batch.add_column(sa.Column("submission_key", sa.String(), nullable=True))
            if "submission_fingerprint" in missing:
                batch.add_column(sa.Column("submission_fingerprint", sa.String(), nullable=True))

    indexes = _index_names(table)
    if "ix_intake_sessions_submission_key" not in indexes:
        with op.batch_alter_table(table) as batch:
            batch.create_index(
                "ix_intake_sessions_submission_key",
                ["submission_key"],
                unique=True,
            )

def _reconcile_leads() -> None:
    _require_table("leads")
    definitions: tuple[tuple[str, sa.types.TypeEngine], ...] = (
        ("nationality", sa.String()),
        ("current_country", sa.String()),
        ("occupation_title", sa.String()),
        ("years_experience", sa.Float()),
        ("job_offer_status", sa.String()),
        ("qualification_recognition", sa.String()),
        ("german_level", sa.String()),
        ("employment_province", sa.String()),
    )
    existing = _column_names("leads")
    missing = [(name, column_type) for name, column_type in definitions if name not in existing]
    if not missing:
        return

    with op.batch_alter_table("leads") as batch:
        for name, column_type in missing:
            batch.add_column(sa.Column(name, column_type, nullable=True))

    # Restore the same structured-intake backfill semantics intended by 0073 while
    # preserving any already-populated values on partially reconciled databases.
    if "intake_sessions" not in _inspector().get_table_names():
        return

    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            "SELECT lead_id, answers_json FROM intake_sessions "
            "WHERE lead_id IS NOT NULL ORDER BY updated_at DESC"
        )
    ).fetchall()
    seen: set[str] = set()
    for lead_id, raw_answers in rows:
        key = str(lead_id)
        if key in seen:
            continue
        seen.add(key)
        try:
            answers = json.loads(raw_answers or "{}")
        except (TypeError, ValueError):
            answers = {}
        bind.execute(
            sa.text(
                "UPDATE leads SET "
                "nationality=COALESCE(nationality,:nationality), "
                "current_country=COALESCE(current_country,:current_country), "
                "occupation_title=COALESCE(occupation_title,:occupation_title), "
                "years_experience=COALESCE(years_experience,:years_experience), "
                "job_offer_status=COALESCE(job_offer_status,:job_offer_status), "
                "qualification_recognition=COALESCE(qualification_recognition,:qualification_recognition), "
                "german_level=COALESCE(german_level,:german_level), "
                "employment_province=COALESCE(employment_province,:employment_province) "
                "WHERE id=:lead_id"
            ),
            {
                "lead_id": lead_id,
                "nationality": answers.get("nationality"),
                "current_country": answers.get("current_country"),
                "occupation_title": answers.get("profession"),
                "years_experience": answers.get("years_experience"),
                "job_offer_status": answers.get("job_offer_status"),
                "qualification_recognition": answers.get("qualification_recognition"),
                "german_level": answers.get("language_level"),
                "employment_province": answers.get("employment_province"),
            },
        )


def _reconcile_work_items() -> None:
    table = "organizational_work_items"
    _require_table(table)
    definitions = {
        "idempotency_fingerprint": sa.Column("idempotency_fingerprint", sa.String(length=64), nullable=True),
        "tenant_key": sa.Column("tenant_key", sa.String(), server_default="default", nullable=False),
        "work_type": sa.Column("work_type", sa.String(), server_default="organizational", nullable=False),
        "objective_key": sa.Column("objective_key", sa.String(), nullable=True),
        "phase_key": sa.Column("phase_key", sa.String(), nullable=True),
        "priority": sa.Column("priority", sa.String(), server_default="normal", nullable=False),
        "parent_work_item_id": sa.Column("parent_work_item_id", _uuid(), nullable=True),
        "profile_id": sa.Column("profile_id", _uuid(), nullable=True),
        "application_id": sa.Column("application_id", _uuid(), nullable=True),
        "source_object_type": sa.Column("source_object_type", sa.String(), nullable=True),
        "source_object_id": sa.Column("source_object_id", sa.String(), nullable=True),
        "source_object_version": sa.Column("source_object_version", sa.String(), nullable=True),
        "requested_by_type": sa.Column("requested_by_type", sa.String(), nullable=True),
        "requested_by_id": sa.Column("requested_by_id", sa.String(), nullable=True),
    }
    existing = _column_names(table)
    added = [name for name in definitions if name not in existing]
    if added:
        with op.batch_alter_table(table) as batch:
            for name in added:
                batch.add_column(definitions[name])

    unique_names, check_names, foreign_key_names = _named_constraints(table)
    indexes = _index_names(table)
    with op.batch_alter_table(table) as batch:
        if "uq_org_work_tenant_id" not in unique_names:
            batch.create_unique_constraint("uq_org_work_tenant_id", ["tenant_key", "id"])
        if "fk_org_work_parent_tenant" not in foreign_key_names:
            batch.create_foreign_key(
                "fk_org_work_parent_tenant",
                table,
                ["tenant_key", "parent_work_item_id"],
                ["tenant_key", "id"],
            )
        if "fk_org_work_profile" not in foreign_key_names:
            batch.create_foreign_key("fk_org_work_profile", "profiles", ["profile_id"], ["id"])
        if "fk_org_work_application" not in foreign_key_names:
            batch.create_foreign_key("fk_org_work_application", "applications", ["application_id"], ["id"])
        if "ck_org_work_priority" not in check_names:
            batch.create_check_constraint(
                "ck_org_work_priority", "priority IN ('low','normal','high','critical')"
            )
        if "ck_org_work_not_self_parent" not in check_names:
            batch.create_check_constraint(
                "ck_org_work_not_self_parent",
                "parent_work_item_id IS NULL OR parent_work_item_id <> id",
            )

        expected_indexes = {
            "ix_org_work_tenant_status_due": ["tenant_key", "status", "due_at"],
            "ix_org_work_tenant_department_status": ["tenant_key", "department", "status"],
            "ix_organizational_work_items_idempotency_fingerprint": ["idempotency_fingerprint"],
            "ix_organizational_work_items_tenant_key": ["tenant_key"],
            "ix_organizational_work_items_work_type": ["work_type"],
            "ix_organizational_work_items_objective_key": ["objective_key"],
            "ix_organizational_work_items_phase_key": ["phase_key"],
            "ix_organizational_work_items_priority": ["priority"],
            "ix_organizational_work_items_parent_work_item_id": ["parent_work_item_id"],
            "ix_organizational_work_items_profile_id": ["profile_id"],
            "ix_organizational_work_items_application_id": ["application_id"],
            "ix_organizational_work_items_source_object_type": ["source_object_type"],
            "ix_organizational_work_items_source_object_id": ["source_object_id"],
            "ix_organizational_work_items_requested_by_type": ["requested_by_type"],
            "ix_organizational_work_items_requested_by_id": ["requested_by_id"],
        }
        for name, columns in expected_indexes.items():
            if name not in indexes:
                batch.create_index(name, columns)

    if {"tenant_key", "work_type", "priority"} & set(added):
        with op.batch_alter_table(table) as batch:
            for name in ("tenant_key", "work_type", "priority"):
                if name in added:
                    batch.alter_column(name, server_default=None)


def _reconcile_decisions() -> None:
    table = "executive_decisions"
    _require_table(table)
    definitions = {
        "tenant_key": sa.Column("tenant_key", sa.String(), server_default="default", nullable=False),
        "decision_type": sa.Column("decision_type", sa.String(), server_default="operational", nullable=False),
        "record_fingerprint": sa.Column("record_fingerprint", sa.String(length=64), nullable=True),
        "lead_id": sa.Column("lead_id", _uuid(), nullable=True),
        "profile_id": sa.Column("profile_id", _uuid(), nullable=True),
        "application_id": sa.Column("application_id", _uuid(), nullable=True),
        "corporate_account_id": sa.Column("corporate_account_id", _uuid(), nullable=True),
        "corporate_mobility_case_id": sa.Column("corporate_mobility_case_id", _uuid(), nullable=True),
        "source_object_type": sa.Column("source_object_type", sa.String(), nullable=True),
        "source_object_id": sa.Column("source_object_id", sa.String(), nullable=True),
        "source_object_version": sa.Column("source_object_version", sa.String(), nullable=True),
        "supersedes_decision_id": sa.Column("supersedes_decision_id", _uuid(), nullable=True),
        "conditions_json": sa.Column("conditions_json", sa.String(), server_default="[]", nullable=False),
        "effect_summary": sa.Column("effect_summary", sa.String(), nullable=True),
        "expires_at": sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    }
    existing = _column_names(table)
    added = [name for name in definitions if name not in existing]
    if added:
        with op.batch_alter_table(table) as batch:
            for name in added:
                batch.add_column(definitions[name])

    unique_names, check_names, foreign_key_names = _named_constraints(table)
    indexes = _index_names(table)
    with op.batch_alter_table(table) as batch:
        if "uq_exec_decision_tenant_id" not in unique_names:
            batch.create_unique_constraint("uq_exec_decision_tenant_id", ["tenant_key", "id"])
        if "fk_exec_decision_work_tenant" not in foreign_key_names:
            batch.create_foreign_key(
                "fk_exec_decision_work_tenant",
                "organizational_work_items",
                ["tenant_key", "work_item_id"],
                ["tenant_key", "id"],
            )
        if "fk_exec_decision_supersedes_tenant" not in foreign_key_names:
            batch.create_foreign_key(
                "fk_exec_decision_supersedes_tenant",
                table,
                ["tenant_key", "supersedes_decision_id"],
                ["tenant_key", "id"],
            )
        for name, remote_table, local_column in (
            ("fk_exec_decision_lead", "leads", "lead_id"),
            ("fk_exec_decision_profile", "profiles", "profile_id"),
            ("fk_exec_decision_application", "applications", "application_id"),
            ("fk_exec_decision_corporate_account", "corporate_accounts", "corporate_account_id"),
            (
                "fk_exec_decision_corporate_case",
                "corporate_mobility_cases",
                "corporate_mobility_case_id",
            ),
        ):
            if name not in foreign_key_names:
                batch.create_foreign_key(name, remote_table, [local_column], ["id"])
        if "ck_exec_decision_type" not in check_names:
            batch.create_check_constraint(
                "ck_exec_decision_type",
                "decision_type IN ('operational','policy','risk','exception','board_reserved')",
            )
        if "ck_exec_decision_not_self_superseding" not in check_names:
            batch.create_check_constraint(
                "ck_exec_decision_not_self_superseding",
                "supersedes_decision_id IS NULL OR supersedes_decision_id <> id",
            )

        expected_indexes = {
            "ix_exec_decision_tenant_status_due": ["tenant_key", "status", "due_at"],
            "ix_executive_decisions_tenant_key": ["tenant_key"],
            "ix_executive_decisions_decision_type": ["decision_type"],
            "ix_executive_decisions_record_fingerprint": ["record_fingerprint"],
            "ix_executive_decisions_lead_id": ["lead_id"],
            "ix_executive_decisions_profile_id": ["profile_id"],
            "ix_executive_decisions_application_id": ["application_id"],
            "ix_executive_decisions_corporate_account_id": ["corporate_account_id"],
            "ix_executive_decisions_corporate_mobility_case_id": ["corporate_mobility_case_id"],
            "ix_executive_decisions_source_object_type": ["source_object_type"],
            "ix_executive_decisions_source_object_id": ["source_object_id"],
            "ix_executive_decisions_supersedes_decision_id": ["supersedes_decision_id"],
            "ix_executive_decisions_expires_at": ["expires_at"],
        }
        for name, columns in expected_indexes.items():
            if name not in indexes:
                batch.create_index(name, columns)

    if {"tenant_key", "decision_type", "conditions_json"} & set(added):
        with op.batch_alter_table(table) as batch:
            for name in ("tenant_key", "decision_type", "conditions_json"):
                if name in added:
                    batch.alter_column(name, server_default=None)


def upgrade() -> None:
    _reconcile_intake_sessions()
    _reconcile_leads()
    _reconcile_work_items()
    _reconcile_decisions()


def downgrade() -> None:
    # 0075 only restores schema that already belongs to 0073/0074. Downgrading to
    # 0074 must therefore retain the reconciled shape rather than remove those
    # earlier-revision columns or constraints.
    pass
