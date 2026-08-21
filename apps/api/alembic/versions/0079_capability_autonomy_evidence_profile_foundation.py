"""Add immutable shadow autonomy evidence observations.

Revision ID: 0079_capability_autonomy_evidence_profile_foundation
Revises: 0078_capability_autonomy_profile_foundation
Create Date: 2026-08-22
"""

from alembic import op
import sqlalchemy as sa


revision = "0079_capability_autonomy_evidence_profile_foundation"
down_revision = "0078_capability_autonomy_profile_foundation"
branch_labels = None
depends_on = None


def _uuid() -> sa.Uuid:
    return sa.Uuid()


def upgrade() -> None:
    op.create_table(
        "capability_autonomy_evidence_observations",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("tenant_key", sa.String(), nullable=False),
        sa.Column("profile_id", _uuid(), nullable=False),
        sa.Column("position_id", _uuid(), nullable=False),
        sa.Column("position_key", sa.String(), nullable=False),
        sa.Column("capability_key", sa.String(), nullable=False),
        sa.Column("context_scope", sa.String(), nullable=False),
        sa.Column("profile_sequence", sa.Integer(), nullable=False),
        sa.Column("evidence_policy_version", sa.String(), nullable=False),
        sa.Column("source_activity_id", _uuid(), nullable=False),
        sa.Column("source_activity_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("human_review_outcome", sa.String(), nullable=False),
        sa.Column("evidence_grounded", sa.Boolean(), nullable=False),
        sa.Column("verifier_contradiction", sa.Boolean(), nullable=False),
        sa.Column("policy_compliant", sa.Boolean(), nullable=False),
        sa.Column("freshness_compliant", sa.Boolean(), nullable=False),
        sa.Column("critical_error", sa.Boolean(), nullable=False),
        sa.Column("recovery_outcome", sa.String(), nullable=False),
        sa.Column("sla_met", sa.Boolean(), nullable=False),
        sa.Column("incident_count", sa.Integer(), nullable=False),
        sa.Column("idempotency_key", sa.String(), nullable=False),
        sa.Column("record_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("created_by_actor_type", sa.String(), nullable=False),
        sa.Column("created_by_actor_key", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "profile_sequence >= 1",
            name="ck_cap_autonomy_observation_profile_sequence_positive",
        ),
        sa.CheckConstraint(
            "human_review_outcome IN ('accepted','modified','rejected','not_reviewed')",
            name="ck_cap_autonomy_observation_human_outcome",
        ),
        sa.CheckConstraint(
            "recovery_outcome IN ('succeeded','failed','not_applicable')",
            name="ck_cap_autonomy_observation_recovery_outcome",
        ),
        sa.CheckConstraint(
            "incident_count >= 0",
            name="ck_cap_autonomy_observation_incident_nonnegative",
        ),
        sa.CheckConstraint(
            "length(source_activity_fingerprint) = 64",
            name="ck_cap_autonomy_observation_source_fingerprint",
        ),
        sa.CheckConstraint(
            "length(record_fingerprint) = 64",
            name="ck_cap_autonomy_observation_record_fingerprint",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_key", "profile_id"],
            ["capability_autonomy_profiles.tenant_key", "capability_autonomy_profiles.id"],
            name="fk_cap_autonomy_observation_profile_tenant",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_key", "source_activity_id"],
            ["organization_activities.tenant_key", "organization_activities.id"],
            name="fk_cap_autonomy_observation_activity_tenant",
        ),
        sa.ForeignKeyConstraint(
            ["position_id"],
            ["organization_positions.id"],
            name="fk_cap_autonomy_observation_position",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_key", "id", name="uq_cap_autonomy_observation_tenant_id"),
        sa.UniqueConstraint(
            "tenant_key",
            "idempotency_key",
            name="uq_cap_autonomy_observation_idempotency",
        ),
        sa.UniqueConstraint(
            "tenant_key",
            "profile_id",
            "source_activity_id",
            name="uq_cap_autonomy_observation_profile_activity",
        ),
    )
    for column in (
        "id",
        "tenant_key",
        "profile_id",
        "position_id",
        "position_key",
        "capability_key",
        "context_scope",
        "profile_sequence",
        "evidence_policy_version",
        "source_activity_id",
        "source_activity_fingerprint",
        "human_review_outcome",
        "evidence_grounded",
        "verifier_contradiction",
        "policy_compliant",
        "freshness_compliant",
        "critical_error",
        "recovery_outcome",
        "sla_met",
        "idempotency_key",
        "record_fingerprint",
        "created_by_actor_type",
        "created_by_actor_key",
        "created_at",
    ):
        op.create_index(
            f"ix_capability_autonomy_evidence_observations_{column}",
            "capability_autonomy_evidence_observations",
            [column],
        )
    op.create_index(
        "ix_cap_autonomy_observation_profile_created",
        "capability_autonomy_evidence_observations",
        ["tenant_key", "profile_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_table("capability_autonomy_evidence_observations")
