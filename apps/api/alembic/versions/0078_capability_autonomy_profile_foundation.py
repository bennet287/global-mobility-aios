"""Add capability-scoped canonical autonomy profile and evidence lineage.

Revision ID: 0078_capability_autonomy_profile_foundation
Revises: 0077_canonical_eligibility_assessment_revision
Create Date: 2026-08-21
"""

from alembic import op
import sqlalchemy as sa


revision = "0078_capability_autonomy_profile_foundation"
down_revision = "0077_canonical_eligibility_assessment_revision"
branch_labels = None
depends_on = None


def _uuid() -> sa.Uuid:
    return sa.Uuid()


def upgrade() -> None:
    op.create_table(
        "capability_autonomy_profiles",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("tenant_key", sa.String(), nullable=False),
        sa.Column("position_key", sa.String(), nullable=False),
        sa.Column("capability_key", sa.String(), nullable=False),
        sa.Column("context_scope", sa.String(), nullable=False),
        sa.Column("profile_sequence", sa.Integer(), nullable=False),
        sa.Column("autonomy_level", sa.String(), nullable=False),
        sa.Column("board_ceiling", sa.String(), nullable=False),
        sa.Column("authority_requirement", sa.String(), nullable=False),
        sa.Column("risk_ceiling", sa.String(), nullable=False),
        sa.Column("evidence_policy_version", sa.String(), nullable=False),
        sa.Column("supersedes_profile_id", _uuid(), nullable=True),
        sa.Column("governance_source", sa.String(), nullable=False),
        sa.Column("decision_activity_id", _uuid(), nullable=False),
        sa.Column("idempotency_key", sa.String(), nullable=False),
        sa.Column("record_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.CheckConstraint(
            "profile_sequence >= 1",
            name="ck_cap_autonomy_profile_sequence_positive",
        ),
        sa.CheckConstraint(
            "autonomy_level IN ('A0','A1','A2','A3','A4','A5')",
            name="ck_cap_autonomy_profile_level",
        ),
        sa.CheckConstraint(
            "board_ceiling IN ('A0','A1','A2','A3','A4','A5')",
            name="ck_cap_autonomy_profile_board_ceiling",
        ),
        sa.CheckConstraint(
            "risk_ceiling IN ('R0','R1','R2','R3','R4','R5')",
            name="ck_cap_autonomy_profile_risk_ceiling",
        ),
        sa.CheckConstraint(
            "CASE autonomy_level "
            "WHEN 'A0' THEN 0 WHEN 'A1' THEN 1 WHEN 'A2' THEN 2 "
            "WHEN 'A3' THEN 3 WHEN 'A4' THEN 4 WHEN 'A5' THEN 5 END <= "
            "CASE board_ceiling "
            "WHEN 'A0' THEN 0 WHEN 'A1' THEN 1 WHEN 'A2' THEN 2 "
            "WHEN 'A3' THEN 3 WHEN 'A4' THEN 4 WHEN 'A5' THEN 5 END",
            name="ck_cap_autonomy_profile_within_board_ceiling",
        ),
        sa.CheckConstraint(
            "supersedes_profile_id IS NULL OR supersedes_profile_id <> id",
            name="ck_cap_autonomy_profile_not_self_superseding",
        ),
        sa.CheckConstraint(
            "length(record_fingerprint) = 64",
            name="ck_cap_autonomy_profile_fingerprint",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_key", "decision_activity_id"],
            ["organization_activities.tenant_key", "organization_activities.id"],
            name="fk_cap_autonomy_profile_decision_activity_tenant",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_key", "supersedes_profile_id"],
            ["capability_autonomy_profiles.tenant_key", "capability_autonomy_profiles.id"],
            name="fk_cap_autonomy_profile_supersedes_tenant",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_key",
            "id",
            name="uq_cap_autonomy_profile_tenant_id",
        ),
        sa.UniqueConstraint(
            "tenant_key",
            "idempotency_key",
            name="uq_cap_autonomy_profile_idempotency",
        ),
        sa.UniqueConstraint(
            "tenant_key",
            "position_key",
            "capability_key",
            "context_scope",
            "profile_sequence",
            name="uq_cap_autonomy_profile_scope_sequence",
        ),
        sa.UniqueConstraint(
            "tenant_key",
            "supersedes_profile_id",
            name="uq_cap_autonomy_profile_supersedes",
        ),
    )
    for column in (
        "id",
        "tenant_key",
        "position_key",
        "capability_key",
        "context_scope",
        "profile_sequence",
        "autonomy_level",
        "board_ceiling",
        "authority_requirement",
        "risk_ceiling",
        "evidence_policy_version",
        "supersedes_profile_id",
        "governance_source",
        "decision_activity_id",
        "idempotency_key",
        "record_fingerprint",
        "effective_from",
        "created_at",
        "created_by",
    ):
        op.create_index(
            f"ix_capability_autonomy_profiles_{column}",
            "capability_autonomy_profiles",
            [column],
        )
    op.create_index(
        "ix_cap_autonomy_profile_scope_sequence",
        "capability_autonomy_profiles",
        ["tenant_key", "position_key", "capability_key", "context_scope", "profile_sequence"],
    )

    op.create_table(
        "capability_autonomy_evidence",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("tenant_key", sa.String(), nullable=False),
        sa.Column("profile_id", _uuid(), nullable=False),
        sa.Column("evidence_sequence", sa.Integer(), nullable=False),
        sa.Column("source_activity_id", _uuid(), nullable=False),
        sa.Column("source_activity_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("record_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "evidence_sequence >= 1",
            name="ck_cap_autonomy_evidence_sequence_positive",
        ),
        sa.CheckConstraint(
            "length(source_activity_fingerprint) = 64",
            name="ck_cap_autonomy_evidence_source_fingerprint",
        ),
        sa.CheckConstraint(
            "length(record_fingerprint) = 64",
            name="ck_cap_autonomy_evidence_record_fingerprint",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_key", "profile_id"],
            ["capability_autonomy_profiles.tenant_key", "capability_autonomy_profiles.id"],
            name="fk_cap_autonomy_evidence_profile_tenant",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_key", "source_activity_id"],
            ["organization_activities.tenant_key", "organization_activities.id"],
            name="fk_cap_autonomy_evidence_activity_tenant",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_key",
            "id",
            name="uq_cap_autonomy_evidence_tenant_id",
        ),
        sa.UniqueConstraint(
            "tenant_key",
            "profile_id",
            "evidence_sequence",
            name="uq_cap_autonomy_evidence_profile_sequence",
        ),
        sa.UniqueConstraint(
            "tenant_key",
            "profile_id",
            "source_activity_id",
            name="uq_cap_autonomy_evidence_profile_activity",
        ),
    )
    for column in (
        "id",
        "tenant_key",
        "profile_id",
        "evidence_sequence",
        "source_activity_id",
        "source_activity_fingerprint",
        "record_fingerprint",
        "created_at",
    ):
        op.create_index(
            f"ix_capability_autonomy_evidence_{column}",
            "capability_autonomy_evidence",
            [column],
        )
    op.create_index(
        "ix_cap_autonomy_evidence_profile_sequence",
        "capability_autonomy_evidence",
        ["tenant_key", "profile_id", "evidence_sequence"],
    )


def downgrade() -> None:
    op.drop_table("capability_autonomy_evidence")
    op.drop_table("capability_autonomy_profiles")
