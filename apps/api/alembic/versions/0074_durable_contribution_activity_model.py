"""Add the durable organization contribution and activity persistence model.

Revision ID: 0074_durable_contribution_activity_model
Revises: 0073_austria_candidate_integrity
Create Date: 2026-08-13
"""

from alembic import op
import sqlalchemy as sa


revision = "0074_durable_contribution_activity_model"
down_revision = "0073_austria_candidate_integrity"
branch_labels = None
depends_on = None


def _uuid() -> sa.Uuid:
    return sa.Uuid()


def _add_existing_columns() -> None:
    with op.batch_alter_table("organizational_work_items") as batch:
        batch.add_column(sa.Column("idempotency_fingerprint", sa.String(length=64), nullable=True))
        batch.add_column(sa.Column("tenant_key", sa.String(), server_default="default", nullable=False))
        batch.add_column(sa.Column("work_type", sa.String(), server_default="organizational", nullable=False))
        batch.add_column(sa.Column("objective_key", sa.String(), nullable=True))
        batch.add_column(sa.Column("phase_key", sa.String(), nullable=True))
        batch.add_column(sa.Column("priority", sa.String(), server_default="normal", nullable=False))
        batch.add_column(sa.Column("parent_work_item_id", _uuid(), nullable=True))
        batch.add_column(sa.Column("profile_id", _uuid(), nullable=True))
        batch.add_column(sa.Column("application_id", _uuid(), nullable=True))
        batch.add_column(sa.Column("source_object_type", sa.String(), nullable=True))
        batch.add_column(sa.Column("source_object_id", sa.String(), nullable=True))
        batch.add_column(sa.Column("source_object_version", sa.String(), nullable=True))
        batch.add_column(sa.Column("requested_by_type", sa.String(), nullable=True))
        batch.add_column(sa.Column("requested_by_id", sa.String(), nullable=True))
        batch.create_unique_constraint("uq_org_work_tenant_id", ["tenant_key", "id"])
        batch.create_foreign_key(
            "fk_org_work_parent_tenant",
            "organizational_work_items",
            ["tenant_key", "parent_work_item_id"],
            ["tenant_key", "id"],
        )
        batch.create_foreign_key("fk_org_work_profile", "profiles", ["profile_id"], ["id"])
        batch.create_foreign_key("fk_org_work_application", "applications", ["application_id"], ["id"])
        batch.create_check_constraint("ck_org_work_priority", "priority IN ('low','normal','high','critical')")
        batch.create_check_constraint(
            "ck_org_work_not_self_parent", "parent_work_item_id IS NULL OR parent_work_item_id <> id"
        )
        batch.create_index("ix_org_work_tenant_status_due", ["tenant_key", "status", "due_at"])
        batch.create_index(
            "ix_org_work_tenant_department_status", ["tenant_key", "department", "status"]
        )
        for column in (
            "idempotency_fingerprint", "tenant_key", "work_type", "objective_key", "phase_key", "priority",
            "parent_work_item_id", "profile_id", "application_id", "source_object_type", "source_object_id",
            "requested_by_type", "requested_by_id",
        ):
            batch.create_index(f"ix_organizational_work_items_{column}", [column])
    with op.batch_alter_table("organizational_work_items") as batch:
        batch.alter_column("tenant_key", server_default=None)
        batch.alter_column("work_type", server_default=None)
        batch.alter_column("priority", server_default=None)

    with op.batch_alter_table("executive_decisions") as batch:
        batch.add_column(sa.Column("tenant_key", sa.String(), server_default="default", nullable=False))
        batch.add_column(sa.Column("decision_type", sa.String(), server_default="operational", nullable=False))
        batch.add_column(sa.Column("record_fingerprint", sa.String(length=64), nullable=True))
        batch.add_column(sa.Column("lead_id", _uuid(), nullable=True))
        batch.add_column(sa.Column("profile_id", _uuid(), nullable=True))
        batch.add_column(sa.Column("application_id", _uuid(), nullable=True))
        batch.add_column(sa.Column("corporate_account_id", _uuid(), nullable=True))
        batch.add_column(sa.Column("corporate_mobility_case_id", _uuid(), nullable=True))
        batch.add_column(sa.Column("source_object_type", sa.String(), nullable=True))
        batch.add_column(sa.Column("source_object_id", sa.String(), nullable=True))
        batch.add_column(sa.Column("source_object_version", sa.String(), nullable=True))
        batch.add_column(sa.Column("supersedes_decision_id", _uuid(), nullable=True))
        batch.add_column(sa.Column("conditions_json", sa.String(), server_default="[]", nullable=False))
        batch.add_column(sa.Column("effect_summary", sa.String(), nullable=True))
        batch.add_column(sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))
        batch.create_unique_constraint("uq_exec_decision_tenant_id", ["tenant_key", "id"])
        batch.create_foreign_key(
            "fk_exec_decision_work_tenant",
            "organizational_work_items",
            ["tenant_key", "work_item_id"],
            ["tenant_key", "id"],
        )
        batch.create_foreign_key(
            "fk_exec_decision_supersedes_tenant",
            "executive_decisions",
            ["tenant_key", "supersedes_decision_id"],
            ["tenant_key", "id"],
        )
        batch.create_foreign_key("fk_exec_decision_lead", "leads", ["lead_id"], ["id"])
        batch.create_foreign_key("fk_exec_decision_profile", "profiles", ["profile_id"], ["id"])
        batch.create_foreign_key("fk_exec_decision_application", "applications", ["application_id"], ["id"])
        batch.create_foreign_key(
            "fk_exec_decision_corporate_account", "corporate_accounts", ["corporate_account_id"], ["id"]
        )
        batch.create_foreign_key(
            "fk_exec_decision_corporate_case",
            "corporate_mobility_cases",
            ["corporate_mobility_case_id"],
            ["id"],
        )
        batch.create_check_constraint(
            "ck_exec_decision_type",
            "decision_type IN ('operational','policy','risk','exception','board_reserved')",
        )
        batch.create_check_constraint(
            "ck_exec_decision_not_self_superseding",
            "supersedes_decision_id IS NULL OR supersedes_decision_id <> id",
        )
        batch.create_index("ix_exec_decision_tenant_status_due", ["tenant_key", "status", "due_at"])
        for column in (
            "tenant_key", "decision_type", "record_fingerprint", "lead_id", "profile_id", "application_id",
            "corporate_account_id", "corporate_mobility_case_id", "source_object_type", "source_object_id",
            "supersedes_decision_id", "expires_at",
        ):
            batch.create_index(f"ix_executive_decisions_{column}", [column])
    with op.batch_alter_table("executive_decisions") as batch:
        batch.alter_column("tenant_key", server_default=None)
        batch.alter_column("decision_type", server_default=None)


def _create_activity_tables() -> None:
    op.create_table(
        "organization_activity_streams",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("tenant_key", sa.String(), nullable=False),
        sa.Column("stream_key", sa.String(), nullable=False),
        sa.Column("last_sequence", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("last_sequence >= 0", name="ck_org_activity_stream_sequence_nonnegative"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_key", "id", name="uq_org_activity_stream_tenant_id"),
        sa.UniqueConstraint("tenant_key", "stream_key", name="uq_org_activity_stream_tenant_key"),
    )
    op.create_index(
        "ix_organization_activity_streams_tenant_key", "organization_activity_streams", ["tenant_key"]
    )
    op.create_index(
        "ix_organization_activity_streams_stream_key", "organization_activity_streams", ["stream_key"]
    )

    op.create_table(
        "organization_activities",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("activity_key", sa.String(), nullable=False),
        sa.Column("record_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("tenant_key", sa.String(), nullable=False),
        sa.Column("activity_stream_id", _uuid(), nullable=False),
        sa.Column("stream_sequence", sa.BigInteger(), nullable=False),
        sa.Column("activity_class", sa.String(), nullable=False),
        sa.Column("activity_type", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("summary", sa.String(), nullable=False),
        sa.Column("department", sa.String(), nullable=True),
        sa.Column("position_key", sa.String(), nullable=True),
        sa.Column("authority_level", sa.String(), nullable=True),
        sa.Column("actor_type", sa.String(), nullable=False),
        sa.Column("actor_id", sa.String(), nullable=False),
        sa.Column("work_item_id", _uuid(), nullable=True),
        sa.Column("execution_attempt_id", _uuid(), nullable=True),
        sa.Column("agent_run_id", _uuid(), nullable=True),
        sa.Column("automation_event_id", _uuid(), nullable=True),
        sa.Column("lead_id", _uuid(), nullable=True),
        sa.Column("profile_id", _uuid(), nullable=True),
        sa.Column("application_id", _uuid(), nullable=True),
        sa.Column("corporate_account_id", _uuid(), nullable=True),
        sa.Column("corporate_mobility_case_id", _uuid(), nullable=True),
        sa.Column("source_object_type", sa.String(), nullable=False),
        sa.Column("source_object_id", sa.String(), nullable=False),
        sa.Column("source_object_version", sa.String(), nullable=True),
        sa.Column("correlation_key", sa.String(), nullable=True),
        sa.Column("causation_activity_id", _uuid(), nullable=True),
        sa.Column("supersedes_activity_id", _uuid(), nullable=True),
        sa.Column("payload_json", sa.String(), server_default="{}", nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.CheckConstraint("stream_sequence >= 1", name="ck_org_activity_sequence_positive"),
        sa.CheckConstraint("length(record_fingerprint) = 64", name="ck_org_activity_fingerprint_length"),
        sa.CheckConstraint(
            "activity_class IN ('domain','work','decision','blocker','human_action','contribution','operational')",
            name="ck_org_activity_class",
        ),
        sa.CheckConstraint(
            "actor_type IN ('human','agent','worker','system','external_human')", name="ck_org_activity_actor_type"
        ),
        sa.CheckConstraint("authority_level IS NULL OR authority_level <> ''", name="ck_org_activity_authority"),
        sa.CheckConstraint(
            "causation_activity_id IS NULL OR causation_activity_id <> id", name="ck_org_activity_not_self_caused"
        ),
        sa.CheckConstraint(
            "supersedes_activity_id IS NULL OR supersedes_activity_id <> id",
            name="ck_org_activity_not_self_superseding",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_key", "activity_stream_id"],
            ["organization_activity_streams.tenant_key", "organization_activity_streams.id"],
            name="fk_org_activity_stream_tenant",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_key", "work_item_id"],
            ["organizational_work_items.tenant_key", "organizational_work_items.id"],
            name="fk_org_activity_work_tenant",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_key", "causation_activity_id"],
            ["organization_activities.tenant_key", "organization_activities.id"],
            name="fk_org_activity_causation_tenant",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_key", "supersedes_activity_id"],
            ["organization_activities.tenant_key", "organization_activities.id"],
            name="fk_org_activity_supersedes_tenant",
        ),
        sa.ForeignKeyConstraint(["execution_attempt_id"], ["organization_execution_attempts.id"]),
        sa.ForeignKeyConstraint(["agent_run_id"], ["agent_runs.id"]),
        sa.ForeignKeyConstraint(["automation_event_id"], ["automation_events.id"]),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"]),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"]),
        sa.ForeignKeyConstraint(["corporate_account_id"], ["corporate_accounts.id"]),
        sa.ForeignKeyConstraint(["corporate_mobility_case_id"], ["corporate_mobility_cases.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_key", "id", name="uq_org_activity_tenant_id"),
        sa.UniqueConstraint("tenant_key", "activity_key", name="uq_org_activity_tenant_key"),
        sa.UniqueConstraint("activity_stream_id", "stream_sequence", name="uq_org_activity_stream_sequence"),
    )
    for name, columns in {
        "ix_org_activity_tenant_occurred": ["tenant_key", "occurred_at"],
        "ix_org_activity_tenant_department_occurred": ["tenant_key", "department", "occurred_at"],
        "ix_org_activity_tenant_type_occurred": ["tenant_key", "activity_type", "occurred_at"],
        "ix_org_activity_tenant_source": ["tenant_key", "source_object_type", "source_object_id"],
        "ix_organization_activities_activity_type": ["activity_type"],
        "ix_organization_activities_actor_id": ["actor_id"],
        "ix_organization_activities_agent_run_id": ["agent_run_id"],
        "ix_organization_activities_application_id": ["application_id"],
        "ix_organization_activities_automation_event_id": ["automation_event_id"],
        "ix_organization_activities_causation_activity_id": ["causation_activity_id"],
        "ix_organization_activities_corporate_account_id": ["corporate_account_id"],
        "ix_organization_activities_corporate_mobility_case_id": ["corporate_mobility_case_id"],
        "ix_organization_activities_correlation_key": ["correlation_key"],
        "ix_organization_activities_department": ["department"],
        "ix_organization_activities_execution_attempt_id": ["execution_attempt_id"],
        "ix_organization_activities_lead_id": ["lead_id"],
        "ix_organization_activities_occurred_at": ["occurred_at"],
        "ix_organization_activities_profile_id": ["profile_id"],
        "ix_organization_activities_source_object_id": ["source_object_id"],
        "ix_organization_activities_source_object_type": ["source_object_type"],
        "ix_organization_activities_supersedes_activity_id": ["supersedes_activity_id"],
        "ix_organization_activities_tenant_key": ["tenant_key"],
        "ix_organization_activities_work_item_id": ["work_item_id"],
    }.items():
        op.create_index(name, "organization_activities", columns)


def _create_contribution_table() -> None:
    op.create_table(
        "organization_contributions",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("contribution_key", sa.String(), nullable=False),
        sa.Column("record_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("tenant_key", sa.String(), nullable=False),
        sa.Column("contribution_type", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("outcome_summary", sa.String(), nullable=False),
        sa.Column("actor_type", sa.String(), nullable=False),
        sa.Column("actor_id", sa.String(), nullable=False),
        sa.Column("department", sa.String(), nullable=False),
        sa.Column("accountable_position_key", sa.String(), nullable=False),
        sa.Column("authority_level", sa.String(), nullable=False),
        sa.Column("objective_key", sa.String(), nullable=True),
        sa.Column("phase_key", sa.String(), nullable=True),
        sa.Column("work_item_id", _uuid(), nullable=True),
        sa.Column("decision_id", _uuid(), nullable=True),
        sa.Column("lead_id", _uuid(), nullable=True),
        sa.Column("profile_id", _uuid(), nullable=True),
        sa.Column("application_id", _uuid(), nullable=True),
        sa.Column("corporate_account_id", _uuid(), nullable=True),
        sa.Column("corporate_mobility_case_id", _uuid(), nullable=True),
        sa.Column("source_object_type", sa.String(), nullable=False),
        sa.Column("source_object_id", sa.String(), nullable=False),
        sa.Column("source_object_version", sa.String(), nullable=False),
        sa.Column("source_state", sa.String(), nullable=False),
        sa.Column("verification_method", sa.String(), nullable=False),
        sa.Column("record_kind", sa.String(), server_default="outcome", nullable=False),
        sa.Column("verified_by", sa.String(), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("human_review_state", sa.String(), nullable=False),
        sa.Column("impact_kind", sa.String(), nullable=False),
        sa.Column("measured_value", sa.Numeric(18, 4), nullable=True),
        sa.Column("baseline_value", sa.Numeric(18, 4), nullable=True),
        sa.Column("target_value", sa.Numeric(18, 4), nullable=True),
        sa.Column("measurement_unit", sa.String(), nullable=True),
        sa.Column("impact_json", sa.String(), server_default="{}", nullable=False),
        sa.Column("evidence_summary_json", sa.String(), server_default="[]", nullable=False),
        sa.Column("human_action_required", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("effective_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("supersedes_contribution_id", _uuid(), nullable=True),
        sa.Column("retraction_reason", sa.String(), nullable=True),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("length(record_fingerprint) = 64", name="ck_org_contribution_fingerprint_length"),
        sa.CheckConstraint(
            "actor_type IN ('human','agent','worker','system','external_human')",
            name="ck_org_contribution_actor_type",
        ),
        sa.CheckConstraint(
            "verification_method IN ('domain_transition','human_attestation','deterministic_gate')",
            name="ck_org_contribution_verification_method",
        ),
        sa.CheckConstraint(
            "record_kind IN ('outcome','supersession','retraction')", name="ck_org_contribution_record_kind"
        ),
        sa.CheckConstraint(
            "impact_kind IN ('state_change','risk_reduction','milestone','delivery','validation','knowledge')",
            name="ck_org_contribution_impact_kind",
        ),
        sa.CheckConstraint(
            "human_review_state IN ('not_required','completed')", name="ck_org_contribution_human_review_state"
        ),
        sa.CheckConstraint(
            "source_object_type NOT IN ('agent_run','workflow_run','organization_execution_attempt',"
            "'organizational_action_output','audit_log','tool_call','message')",
            name="ck_org_contribution_authoritative_source",
        ),
        sa.CheckConstraint(
            "(measured_value IS NULL AND baseline_value IS NULL AND target_value IS NULL) "
            "OR measurement_unit IS NOT NULL",
            name="ck_org_contribution_measurement_unit",
        ),
        sa.CheckConstraint(
            "(record_kind = 'outcome' AND supersedes_contribution_id IS NULL AND retraction_reason IS NULL) OR "
            "(record_kind = 'supersession' AND supersedes_contribution_id IS NOT NULL AND retraction_reason IS NULL) OR "
            "(record_kind = 'retraction' AND supersedes_contribution_id IS NOT NULL AND retraction_reason IS NOT NULL)",
            name="ck_org_contribution_correction_shape",
        ),
        sa.CheckConstraint(
            "supersedes_contribution_id IS NULL OR supersedes_contribution_id <> id",
            name="ck_org_contribution_not_self_superseding",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_key", "work_item_id"],
            ["organizational_work_items.tenant_key", "organizational_work_items.id"],
            name="fk_org_contribution_work_tenant",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_key", "decision_id"],
            ["executive_decisions.tenant_key", "executive_decisions.id"],
            name="fk_org_contribution_decision_tenant",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_key", "supersedes_contribution_id"],
            ["organization_contributions.tenant_key", "organization_contributions.id"],
            name="fk_org_contribution_supersedes_tenant",
        ),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"]),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"]),
        sa.ForeignKeyConstraint(["corporate_account_id"], ["corporate_accounts.id"]),
        sa.ForeignKeyConstraint(["corporate_mobility_case_id"], ["corporate_mobility_cases.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_key", "id", name="uq_org_contribution_tenant_id"),
        sa.UniqueConstraint("tenant_key", "contribution_key", name="uq_org_contribution_tenant_key"),
        sa.UniqueConstraint(
            "tenant_key", "supersedes_contribution_id", "record_kind", name="uq_org_contribution_correction"
        ),
    )
    for name, columns in {
        "ix_org_contribution_tenant_kind_effective": ["tenant_key", "record_kind", "effective_at"],
        "ix_org_contribution_tenant_department_effective": ["tenant_key", "department", "effective_at"],
        "ix_org_contribution_tenant_type_effective": ["tenant_key", "contribution_type", "effective_at"],
        "ix_org_contribution_tenant_source": [
            "tenant_key", "source_object_type", "source_object_id", "source_object_version"
        ],
        "ix_organization_contributions_actor_id": ["actor_id"],
        "ix_organization_contributions_application_id": ["application_id"],
        "ix_organization_contributions_contribution_type": ["contribution_type"],
        "ix_organization_contributions_corporate_account_id": ["corporate_account_id"],
        "ix_organization_contributions_corporate_mobility_case_id": ["corporate_mobility_case_id"],
        "ix_organization_contributions_decision_id": ["decision_id"],
        "ix_organization_contributions_department": ["department"],
        "ix_organization_contributions_effective_at": ["effective_at"],
        "ix_organization_contributions_lead_id": ["lead_id"],
        "ix_organization_contributions_objective_key": ["objective_key"],
        "ix_organization_contributions_phase_key": ["phase_key"],
        "ix_organization_contributions_profile_id": ["profile_id"],
        "ix_organization_contributions_source_object_id": ["source_object_id"],
        "ix_organization_contributions_source_object_type": ["source_object_type"],
        "ix_organization_contributions_supersedes_contribution_id": ["supersedes_contribution_id"],
        "ix_organization_contributions_tenant_key": ["tenant_key"],
        "ix_organization_contributions_work_item_id": ["work_item_id"],
    }.items():
        op.create_index(name, "organization_contributions", columns)


def _create_dependency_table() -> None:
    op.create_table(
        "organization_work_item_dependencies",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("dependency_key", sa.String(), nullable=False),
        sa.Column("record_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("tenant_key", sa.String(), nullable=False),
        sa.Column("work_item_id", _uuid(), nullable=False),
        sa.Column("depends_on_work_item_id", _uuid(), nullable=False),
        sa.Column("dependency_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), server_default="active", nullable=False),
        sa.Column("satisfied_by_contribution_id", _uuid(), nullable=True),
        sa.Column("waived_by_human_id", sa.String(), nullable=True),
        sa.Column("waiver_reason", sa.String(), nullable=True),
        sa.Column("waived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("updated_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("work_item_id <> depends_on_work_item_id", name="ck_org_work_dependency_not_self"),
        sa.CheckConstraint("length(record_fingerprint) = 64", name="ck_org_work_dependency_fingerprint_length"),
        sa.CheckConstraint(
            "dependency_type IN ('blocks','requires','informs')", name="ck_org_work_dependency_type"
        ),
        sa.CheckConstraint(
            "status IN ('active','satisfied','waived','superseded')", name="ck_org_work_dependency_status"
        ),
        sa.CheckConstraint(
            "status <> 'waived' OR (waived_by_human_id IS NOT NULL AND waiver_reason IS NOT NULL AND waived_at IS NOT NULL)",
            name="ck_org_work_dependency_waiver",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_key", "work_item_id"],
            ["organizational_work_items.tenant_key", "organizational_work_items.id"],
            name="fk_org_work_dependency_work_tenant",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_key", "depends_on_work_item_id"],
            ["organizational_work_items.tenant_key", "organizational_work_items.id"],
            name="fk_org_work_dependency_depends_tenant",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_key", "satisfied_by_contribution_id"],
            ["organization_contributions.tenant_key", "organization_contributions.id"],
            name="fk_org_work_dependency_contribution_tenant",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_key", "id", name="uq_org_work_dependency_tenant_id"),
        sa.UniqueConstraint("tenant_key", "dependency_key", name="uq_org_work_dependency_tenant_key"),
        sa.UniqueConstraint(
            "tenant_key", "work_item_id", "depends_on_work_item_id", "dependency_type",
            name="uq_org_work_dependency_edge",
        ),
    )
    op.create_index("ix_org_work_dependency_tenant_status", "organization_work_item_dependencies", ["tenant_key", "status"])
    op.create_index("ix_org_work_dependency_forward", "organization_work_item_dependencies", ["tenant_key", "work_item_id"])
    op.create_index("ix_org_work_dependency_reverse", "organization_work_item_dependencies", ["tenant_key", "depends_on_work_item_id"])


def _common_subject_columns() -> list[sa.Column]:
    return [
        sa.Column("lead_id", _uuid(), nullable=True),
        sa.Column("profile_id", _uuid(), nullable=True),
        sa.Column("application_id", _uuid(), nullable=True),
        sa.Column("corporate_account_id", _uuid(), nullable=True),
        sa.Column("corporate_mobility_case_id", _uuid(), nullable=True),
    ]


def _common_subject_fks() -> list[sa.ForeignKeyConstraint]:
    return [
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"]),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"]),
        sa.ForeignKeyConstraint(["corporate_account_id"], ["corporate_accounts.id"]),
        sa.ForeignKeyConstraint(["corporate_mobility_case_id"], ["corporate_mobility_cases.id"]),
    ]


def _create_blocker_table() -> None:
    op.create_table(
        "organization_blockers",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("blocker_key", sa.String(), nullable=False),
        sa.Column("record_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("tenant_key", sa.String(), nullable=False),
        sa.Column("blocker_type", sa.String(), nullable=False),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("status", sa.String(), server_default="open", nullable=False),
        sa.Column("department", sa.String(), nullable=True),
        sa.Column("accountable_position_key", sa.String(), nullable=True),
        sa.Column("authority_level", sa.String(), nullable=True),
        sa.Column("work_item_id", _uuid(), nullable=True),
        sa.Column("decision_id", _uuid(), nullable=True),
        sa.Column("contribution_id", _uuid(), nullable=True),
        *_common_subject_columns(),
        sa.Column("risk_escalation_id", _uuid(), nullable=True),
        sa.Column("external_validation_finding_id", _uuid(), nullable=True),
        sa.Column("source_object_type", sa.String(), nullable=True),
        sa.Column("source_object_id", sa.String(), nullable=True),
        sa.Column("source_object_version", sa.String(), nullable=True),
        sa.Column("requires_human_action", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("mitigated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_summary", sa.String(), nullable=True),
        sa.Column("resolving_actor_type", sa.String(), nullable=True),
        sa.Column("resolving_actor_id", sa.String(), nullable=True),
        sa.Column("waived_by_human_id", sa.String(), nullable=True),
        sa.Column("waiver_reason", sa.String(), nullable=True),
        sa.Column("waived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("supersedes_blocker_id", _uuid(), nullable=True),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("updated_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("length(record_fingerprint) = 64", name="ck_org_blocker_fingerprint_length"),
        sa.CheckConstraint(
            "blocker_type IN ('evidence','dependency','authority','human_input','external','safety','technical')",
            name="ck_org_blocker_type",
        ),
        sa.CheckConstraint("severity IN ('low','medium','high','critical')", name="ck_org_blocker_severity"),
        sa.CheckConstraint(
            "status IN ('open','mitigated','resolved','waived','superseded')", name="ck_org_blocker_status"
        ),
        sa.CheckConstraint(
            "work_item_id IS NOT NULL OR decision_id IS NOT NULL OR contribution_id IS NOT NULL OR lead_id IS NOT NULL "
            "OR profile_id IS NOT NULL OR application_id IS NOT NULL OR corporate_account_id IS NOT NULL "
            "OR corporate_mobility_case_id IS NOT NULL",
            name="ck_org_blocker_has_target",
        ),
        sa.CheckConstraint(
            "status <> 'resolved' OR (resolved_at IS NOT NULL AND resolution_summary IS NOT NULL "
            "AND resolving_actor_type IS NOT NULL AND resolving_actor_id IS NOT NULL)",
            name="ck_org_blocker_resolution",
        ),
        sa.CheckConstraint(
            "status <> 'waived' OR (waived_by_human_id IS NOT NULL AND waiver_reason IS NOT NULL AND waived_at IS NOT NULL)",
            name="ck_org_blocker_waiver",
        ),
        sa.CheckConstraint("supersedes_blocker_id IS NULL OR supersedes_blocker_id <> id", name="ck_org_blocker_not_self"),
        sa.ForeignKeyConstraint(
            ["tenant_key", "work_item_id"], ["organizational_work_items.tenant_key", "organizational_work_items.id"],
            name="fk_org_blocker_work_tenant",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_key", "decision_id"], ["executive_decisions.tenant_key", "executive_decisions.id"],
            name="fk_org_blocker_decision_tenant",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_key", "contribution_id"], ["organization_contributions.tenant_key", "organization_contributions.id"],
            name="fk_org_blocker_contribution_tenant",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_key", "supersedes_blocker_id"], ["organization_blockers.tenant_key", "organization_blockers.id"],
            name="fk_org_blocker_supersedes_tenant",
        ),
        *_common_subject_fks(),
        sa.ForeignKeyConstraint(["risk_escalation_id"], ["risk_escalations.id"]),
        sa.ForeignKeyConstraint(["external_validation_finding_id"], ["external_validation_findings.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_key", "id", name="uq_org_blocker_tenant_id"),
        sa.UniqueConstraint("tenant_key", "blocker_key", name="uq_org_blocker_tenant_key"),
    )
    for name, columns in {
        "ix_org_blocker_tenant_status_severity_due": ["tenant_key", "status", "severity", "due_at"],
        "ix_org_blocker_tenant_department_status": ["tenant_key", "department", "status"],
        "ix_org_blocker_tenant_source": ["tenant_key", "source_object_type", "source_object_id"],
        "ix_organization_blockers_application_id": ["application_id"],
        "ix_organization_blockers_contribution_id": ["contribution_id"],
        "ix_organization_blockers_corporate_account_id": ["corporate_account_id"],
        "ix_organization_blockers_corporate_mobility_case_id": ["corporate_mobility_case_id"],
        "ix_organization_blockers_decision_id": ["decision_id"],
        "ix_organization_blockers_department": ["department"],
        "ix_organization_blockers_due_at": ["due_at"],
        "ix_organization_blockers_external_validation_finding_id": ["external_validation_finding_id"],
        "ix_organization_blockers_lead_id": ["lead_id"],
        "ix_organization_blockers_profile_id": ["profile_id"],
        "ix_organization_blockers_risk_escalation_id": ["risk_escalation_id"],
        "ix_organization_blockers_severity": ["severity"],
        "ix_organization_blockers_source_object_id": ["source_object_id"],
        "ix_organization_blockers_source_object_type": ["source_object_type"],
        "ix_organization_blockers_status": ["status"],
        "ix_organization_blockers_supersedes_blocker_id": ["supersedes_blocker_id"],
        "ix_organization_blockers_tenant_key": ["tenant_key"],
        "ix_organization_blockers_work_item_id": ["work_item_id"],
    }.items():
        op.create_index(name, "organization_blockers", columns)


def _create_human_action_tables() -> None:
    op.create_table(
        "organization_human_action_requests",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("request_key", sa.String(), nullable=False),
        sa.Column("record_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("tenant_key", sa.String(), nullable=False),
        sa.Column("request_type", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("instructions", sa.String(), nullable=False),
        sa.Column("status", sa.String(), server_default="required", nullable=False),
        sa.Column("priority", sa.String(), server_default="normal", nullable=False),
        sa.Column("required_role", sa.String(), nullable=False),
        sa.Column("assigned_human_id", sa.String(), nullable=True),
        sa.Column("requested_by_type", sa.String(), nullable=False),
        sa.Column("requested_by_id", sa.String(), nullable=False),
        sa.Column("authority_level", sa.String(), nullable=True),
        sa.Column("work_item_id", _uuid(), nullable=True),
        sa.Column("decision_id", _uuid(), nullable=True),
        sa.Column("blocker_id", _uuid(), nullable=True),
        sa.Column("contribution_id", _uuid(), nullable=True),
        *_common_subject_columns(),
        sa.Column("source_object_type", sa.String(), nullable=True),
        sa.Column("source_object_id", sa.String(), nullable=True),
        sa.Column("source_object_version", sa.String(), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledged_by_human_id", sa.String(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_by_human_id", sa.String(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_by_human_id", sa.String(), nullable=True),
        sa.Column("declined_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("declined_by_human_id", sa.String(), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_by_actor_id", sa.String(), nullable=True),
        sa.Column("expired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("outcome", sa.String(), nullable=True),
        sa.Column("completion_notes", sa.String(), nullable=True),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("updated_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("length(record_fingerprint) = 64", name="ck_org_human_request_fingerprint_length"),
        sa.CheckConstraint(
            "request_type IN ('review','decision','attestation','acknowledgement','provide_information','approval','exception')",
            name="ck_org_human_request_type",
        ),
        sa.CheckConstraint(
            "status IN ('required','acknowledged','in_progress','completed','declined','cancelled','expired')",
            name="ck_org_human_request_status",
        ),
        sa.CheckConstraint("priority IN ('low','normal','high','critical')", name="ck_org_human_request_priority"),
        sa.CheckConstraint(
            "work_item_id IS NOT NULL OR decision_id IS NOT NULL OR blocker_id IS NOT NULL OR contribution_id IS NOT NULL "
            "OR lead_id IS NOT NULL OR profile_id IS NOT NULL OR application_id IS NOT NULL "
            "OR corporate_account_id IS NOT NULL OR corporate_mobility_case_id IS NOT NULL",
            name="ck_org_human_request_has_target",
        ),
        sa.CheckConstraint(
            "status <> 'completed' OR (completed_at IS NOT NULL AND completed_by_human_id IS NOT NULL AND outcome IS NOT NULL)",
            name="ck_org_human_request_completed",
        ),
        sa.CheckConstraint(
            "status <> 'declined' OR (declined_at IS NOT NULL AND declined_by_human_id IS NOT NULL AND outcome IS NOT NULL)",
            name="ck_org_human_request_declined",
        ),
        sa.CheckConstraint(
            "status <> 'cancelled' OR (cancelled_at IS NOT NULL AND cancelled_by_actor_id IS NOT NULL AND outcome IS NOT NULL)",
            name="ck_org_human_request_cancelled",
        ),
        sa.CheckConstraint("status <> 'expired' OR expired_at IS NOT NULL", name="ck_org_human_request_expired"),
        sa.ForeignKeyConstraint(["tenant_key", "work_item_id"], ["organizational_work_items.tenant_key", "organizational_work_items.id"], name="fk_org_human_request_work_tenant"),
        sa.ForeignKeyConstraint(["tenant_key", "decision_id"], ["executive_decisions.tenant_key", "executive_decisions.id"], name="fk_org_human_request_decision_tenant"),
        sa.ForeignKeyConstraint(["tenant_key", "blocker_id"], ["organization_blockers.tenant_key", "organization_blockers.id"], name="fk_org_human_request_blocker_tenant"),
        sa.ForeignKeyConstraint(["tenant_key", "contribution_id"], ["organization_contributions.tenant_key", "organization_contributions.id"], name="fk_org_human_request_contribution_tenant"),
        *_common_subject_fks(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_key", "id", name="uq_org_human_request_tenant_id"),
        sa.UniqueConstraint("tenant_key", "request_key", name="uq_org_human_request_tenant_key"),
    )
    for name, columns in {
        "ix_org_human_request_tenant_status_priority_due": ["tenant_key", "status", "priority", "due_at"],
        "ix_org_human_request_assignee_status_due": ["assigned_human_id", "status", "due_at"],
        "ix_org_human_request_tenant_source": ["tenant_key", "source_object_type", "source_object_id"],
        "ix_organization_human_action_requests_application_id": ["application_id"],
        "ix_organization_human_action_requests_assigned_human_id": ["assigned_human_id"],
        "ix_organization_human_action_requests_blocker_id": ["blocker_id"],
        "ix_organization_human_action_requests_contribution_id": ["contribution_id"],
        "ix_organization_human_action_requests_corporate_account_id": ["corporate_account_id"],
        "ix_org_human_request_corporate_case": ["corporate_mobility_case_id"],
        "ix_organization_human_action_requests_decision_id": ["decision_id"],
        "ix_organization_human_action_requests_due_at": ["due_at"],
        "ix_organization_human_action_requests_lead_id": ["lead_id"],
        "ix_organization_human_action_requests_priority": ["priority"],
        "ix_organization_human_action_requests_profile_id": ["profile_id"],
        "ix_organization_human_action_requests_required_role": ["required_role"],
        "ix_organization_human_action_requests_source_object_id": ["source_object_id"],
        "ix_organization_human_action_requests_source_object_type": ["source_object_type"],
        "ix_organization_human_action_requests_status": ["status"],
        "ix_organization_human_action_requests_tenant_key": ["tenant_key"],
        "ix_organization_human_action_requests_work_item_id": ["work_item_id"],
    }.items():
        op.create_index(name, "organization_human_action_requests", columns)

    op.create_table(
        "organization_human_actions",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("action_key", sa.String(), nullable=False),
        sa.Column("record_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("tenant_key", sa.String(), nullable=False),
        sa.Column("human_action_request_id", _uuid(), nullable=True),
        sa.Column("action_type", sa.String(), nullable=False),
        sa.Column("actor_type", sa.String(), server_default="human", nullable=False),
        sa.Column("human_actor_id", sa.String(), nullable=False),
        sa.Column("actor_role", sa.String(), nullable=True),
        sa.Column("actor_position_key", sa.String(), nullable=True),
        sa.Column("actor_department", sa.String(), nullable=True),
        sa.Column("authority_level", sa.String(), nullable=True),
        sa.Column("work_item_id", _uuid(), nullable=True),
        sa.Column("decision_id", _uuid(), nullable=True),
        sa.Column("blocker_id", _uuid(), nullable=True),
        sa.Column("contribution_id", _uuid(), nullable=True),
        *_common_subject_columns(),
        sa.Column("source_object_type", sa.String(), nullable=True),
        sa.Column("source_object_id", sa.String(), nullable=True),
        sa.Column("source_object_version", sa.String(), nullable=True),
        sa.Column("outcome", sa.String(), nullable=False),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column("metadata_json", sa.String(), server_default="{}", nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.CheckConstraint("length(record_fingerprint) = 64", name="ck_org_human_action_fingerprint_length"),
        sa.CheckConstraint("actor_type = 'human'", name="ck_org_human_action_actor_human"),
        sa.CheckConstraint(
            "action_type IN ('reviewed','approved','rejected','requested_changes','attested','acknowledged',"
            "'assigned','reassigned','resolved','declined','cancelled')",
            name="ck_org_human_action_type",
        ),
        sa.CheckConstraint(
            "human_action_request_id IS NOT NULL OR work_item_id IS NOT NULL OR decision_id IS NOT NULL "
            "OR blocker_id IS NOT NULL OR contribution_id IS NOT NULL OR lead_id IS NOT NULL OR profile_id IS NOT NULL "
            "OR application_id IS NOT NULL OR corporate_account_id IS NOT NULL OR corporate_mobility_case_id IS NOT NULL",
            name="ck_org_human_action_has_target",
        ),
        sa.ForeignKeyConstraint(["tenant_key", "human_action_request_id"], ["organization_human_action_requests.tenant_key", "organization_human_action_requests.id"], name="fk_org_human_action_request_tenant"),
        sa.ForeignKeyConstraint(["tenant_key", "work_item_id"], ["organizational_work_items.tenant_key", "organizational_work_items.id"], name="fk_org_human_action_work_tenant"),
        sa.ForeignKeyConstraint(["tenant_key", "decision_id"], ["executive_decisions.tenant_key", "executive_decisions.id"], name="fk_org_human_action_decision_tenant"),
        sa.ForeignKeyConstraint(["tenant_key", "blocker_id"], ["organization_blockers.tenant_key", "organization_blockers.id"], name="fk_org_human_action_blocker_tenant"),
        sa.ForeignKeyConstraint(["tenant_key", "contribution_id"], ["organization_contributions.tenant_key", "organization_contributions.id"], name="fk_org_human_action_contribution_tenant"),
        *_common_subject_fks(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_key", "id", name="uq_org_human_action_tenant_id"),
        sa.UniqueConstraint("tenant_key", "action_key", name="uq_org_human_action_tenant_key"),
    )
    for name, columns in {
        "ix_org_human_action_tenant_occurred": ["tenant_key", "occurred_at"],
        "ix_org_human_action_actor_occurred": ["human_actor_id", "occurred_at"],
        "ix_org_human_action_type_occurred": ["action_type", "occurred_at"],
        "ix_org_human_action_tenant_source": ["tenant_key", "source_object_type", "source_object_id"],
        "ix_organization_human_actions_application_id": ["application_id"],
        "ix_organization_human_actions_blocker_id": ["blocker_id"],
        "ix_organization_human_actions_contribution_id": ["contribution_id"],
        "ix_organization_human_actions_corporate_account_id": ["corporate_account_id"],
        "ix_organization_human_actions_corporate_mobility_case_id": ["corporate_mobility_case_id"],
        "ix_organization_human_actions_decision_id": ["decision_id"],
        "ix_organization_human_actions_human_action_request_id": ["human_action_request_id"],
        "ix_organization_human_actions_human_actor_id": ["human_actor_id"],
        "ix_organization_human_actions_lead_id": ["lead_id"],
        "ix_organization_human_actions_occurred_at": ["occurred_at"],
        "ix_organization_human_actions_profile_id": ["profile_id"],
        "ix_organization_human_actions_source_object_id": ["source_object_id"],
        "ix_organization_human_actions_source_object_type": ["source_object_type"],
        "ix_organization_human_actions_tenant_key": ["tenant_key"],
        "ix_organization_human_actions_work_item_id": ["work_item_id"],
    }.items():
        op.create_index(name, "organization_human_actions", columns)


def _create_reference_table() -> None:
    op.create_table(
        "organization_record_references",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("reference_key", sa.String(), nullable=False),
        sa.Column("record_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("tenant_key", sa.String(), nullable=False),
        sa.Column("activity_id", _uuid(), nullable=True),
        sa.Column("contribution_id", _uuid(), nullable=True),
        sa.Column("work_item_id", _uuid(), nullable=True),
        sa.Column("decision_id", _uuid(), nullable=True),
        sa.Column("blocker_id", _uuid(), nullable=True),
        sa.Column("human_action_request_id", _uuid(), nullable=True),
        sa.Column("human_action_id", _uuid(), nullable=True),
        sa.Column("reference_role", sa.String(), nullable=False),
        sa.Column("target_type", sa.String(), nullable=False),
        sa.Column("target_id", sa.String(), nullable=False),
        sa.Column("target_version", sa.String(), nullable=True),
        sa.Column("target_state", sa.String(), nullable=True),
        sa.Column("content_hash", sa.String(), nullable=True),
        sa.Column("label", sa.String(), nullable=True),
        sa.Column("source_url", sa.String(), nullable=True),
        sa.Column("metadata_json", sa.String(), server_default="{}", nullable=False),
        sa.Column("supersedes_reference_id", _uuid(), nullable=True),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("length(record_fingerprint) = 64", name="ck_org_record_reference_fingerprint_length"),
        sa.CheckConstraint(
            "reference_role IN ('authoritative_outcome','affected_subject','evidence','caused_by','supports','contradicts')",
            name="ck_org_record_reference_role",
        ),
        sa.CheckConstraint(
            "target_type IN ('lead','profile','application','corporate_mobility_case','pathway_comparison_assessment',"
            "'eligibility_assessment','source_snapshot','official_source','external_validation_run',"
            "'external_validation_finding','agent_run','automation_event','audit_log','regulatory_change','verified_rule',"
            "'mobility_pathway_version','agency_submission','corporate_compliance_event','mobility_timeline_milestone')",
            name="ck_org_record_reference_target_type",
        ),
        sa.CheckConstraint(
            "(CASE WHEN activity_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN contribution_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN work_item_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN decision_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN blocker_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN human_action_request_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN human_action_id IS NOT NULL THEN 1 ELSE 0 END) = 1",
            name="ck_org_record_reference_one_owner",
        ),
        sa.CheckConstraint("supersedes_reference_id IS NULL OR supersedes_reference_id <> id", name="ck_org_record_reference_not_self"),
        sa.ForeignKeyConstraint(["tenant_key", "activity_id"], ["organization_activities.tenant_key", "organization_activities.id"], name="fk_org_reference_activity_tenant"),
        sa.ForeignKeyConstraint(["tenant_key", "contribution_id"], ["organization_contributions.tenant_key", "organization_contributions.id"], name="fk_org_reference_contribution_tenant"),
        sa.ForeignKeyConstraint(["tenant_key", "work_item_id"], ["organizational_work_items.tenant_key", "organizational_work_items.id"], name="fk_org_reference_work_tenant"),
        sa.ForeignKeyConstraint(["tenant_key", "decision_id"], ["executive_decisions.tenant_key", "executive_decisions.id"], name="fk_org_reference_decision_tenant"),
        sa.ForeignKeyConstraint(["tenant_key", "blocker_id"], ["organization_blockers.tenant_key", "organization_blockers.id"], name="fk_org_reference_blocker_tenant"),
        sa.ForeignKeyConstraint(["tenant_key", "human_action_request_id"], ["organization_human_action_requests.tenant_key", "organization_human_action_requests.id"], name="fk_org_reference_human_request_tenant"),
        sa.ForeignKeyConstraint(["tenant_key", "human_action_id"], ["organization_human_actions.tenant_key", "organization_human_actions.id"], name="fk_org_reference_human_action_tenant"),
        sa.ForeignKeyConstraint(["tenant_key", "supersedes_reference_id"], ["organization_record_references.tenant_key", "organization_record_references.id"], name="fk_org_reference_supersedes_tenant"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_key", "id", name="uq_org_record_reference_tenant_id"),
        sa.UniqueConstraint("tenant_key", "reference_key", name="uq_org_record_reference_tenant_key"),
    )
    op.create_index("ix_org_record_reference_tenant_target", "organization_record_references", ["tenant_key", "target_type", "target_id"])
    for column in (
        "activity_id", "contribution_id", "work_item_id", "decision_id", "blocker_id",
        "human_action_request_id", "human_action_id", "supersedes_reference_id",
    ):
        op.create_index(
            f"ix_organization_record_references_{column}", "organization_record_references", [column]
        )
    op.create_index(
        "ix_organization_record_references_target_id", "organization_record_references", ["target_id"]
    )
    op.create_index(
        "ix_organization_record_references_target_type", "organization_record_references", ["target_type"]
    )
    op.create_index(
        "ix_organization_record_references_tenant_key", "organization_record_references", ["tenant_key"]
    )


def upgrade() -> None:
    _add_existing_columns()
    _create_activity_tables()
    _create_contribution_table()
    _create_dependency_table()
    _create_blocker_table()
    _create_human_action_tables()
    _create_reference_table()


def downgrade() -> None:
    for table in (
        "organization_record_references",
        "organization_human_actions",
        "organization_human_action_requests",
        "organization_blockers",
        "organization_work_item_dependencies",
        "organization_contributions",
        "organization_activities",
        "organization_activity_streams",
    ):
        op.drop_table(table)

    with op.batch_alter_table("executive_decisions") as batch:
        for name in (
            "ix_exec_decision_tenant_status_due", "ix_executive_decisions_tenant_key",
            "ix_executive_decisions_decision_type", "ix_executive_decisions_record_fingerprint",
            "ix_executive_decisions_lead_id", "ix_executive_decisions_profile_id",
            "ix_executive_decisions_application_id", "ix_executive_decisions_corporate_account_id",
            "ix_executive_decisions_corporate_mobility_case_id",
            "ix_executive_decisions_source_object_type", "ix_executive_decisions_source_object_id",
            "ix_executive_decisions_supersedes_decision_id", "ix_executive_decisions_expires_at",
        ):
            batch.drop_index(name)
        batch.drop_constraint("ck_exec_decision_not_self_superseding", type_="check")
        batch.drop_constraint("ck_exec_decision_type", type_="check")
        for name in (
            "fk_exec_decision_corporate_case", "fk_exec_decision_corporate_account", "fk_exec_decision_application",
            "fk_exec_decision_profile", "fk_exec_decision_lead", "fk_exec_decision_supersedes_tenant",
            "fk_exec_decision_work_tenant",
        ):
            batch.drop_constraint(name, type_="foreignkey")
        batch.drop_constraint("uq_exec_decision_tenant_id", type_="unique")
        for column in (
            "expires_at", "effect_summary", "conditions_json", "supersedes_decision_id", "source_object_version",
            "source_object_id", "source_object_type", "corporate_mobility_case_id", "corporate_account_id",
            "application_id", "profile_id", "lead_id", "record_fingerprint", "decision_type", "tenant_key",
        ):
            batch.drop_column(column)

    with op.batch_alter_table("organizational_work_items") as batch:
        for name in (
            "ix_org_work_tenant_status_due", "ix_org_work_tenant_department_status",
            "ix_organizational_work_items_idempotency_fingerprint", "ix_organizational_work_items_tenant_key",
            "ix_organizational_work_items_work_type", "ix_organizational_work_items_objective_key",
            "ix_organizational_work_items_phase_key", "ix_organizational_work_items_priority",
            "ix_organizational_work_items_parent_work_item_id", "ix_organizational_work_items_profile_id",
            "ix_organizational_work_items_application_id", "ix_organizational_work_items_source_object_type",
            "ix_organizational_work_items_source_object_id", "ix_organizational_work_items_requested_by_type",
            "ix_organizational_work_items_requested_by_id",
        ):
            batch.drop_index(name)
        batch.drop_constraint("ck_org_work_not_self_parent", type_="check")
        batch.drop_constraint("ck_org_work_priority", type_="check")
        batch.drop_constraint("fk_org_work_application", type_="foreignkey")
        batch.drop_constraint("fk_org_work_profile", type_="foreignkey")
        batch.drop_constraint("fk_org_work_parent_tenant", type_="foreignkey")
        batch.drop_constraint("uq_org_work_tenant_id", type_="unique")
        for column in (
            "requested_by_id", "requested_by_type", "source_object_version", "source_object_id", "source_object_type",
            "application_id", "profile_id", "parent_work_item_id", "priority", "phase_key", "objective_key",
            "work_type", "tenant_key", "idempotency_fingerprint",
        ):
            batch.drop_column(column)
