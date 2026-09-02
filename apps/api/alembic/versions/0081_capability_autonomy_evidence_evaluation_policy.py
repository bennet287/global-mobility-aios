"""Add Board-authored qualified autonomy evidence evaluation policy.

Revision ID: 0081_capability_autonomy_evidence_evaluation_policy
Revises: 0080_capability_autonomy_promotion_policy_foundation
Create Date: 2026-08-22
"""

from alembic import op
import sqlalchemy as sa


revision = "0081_capability_autonomy_evidence_evaluation_policy"
down_revision = "0080_capability_autonomy_promotion_policy_foundation"
branch_labels = None
depends_on = None


def _uuid() -> sa.Uuid:
    return sa.Uuid()


def upgrade() -> None:
    op.create_table(
        "capability_autonomy_evidence_evaluation_policies",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("tenant_key", sa.String(), nullable=False),
        sa.Column("profile_id", _uuid(), nullable=False),
        sa.Column("profile_sequence", sa.Integer(), nullable=False),
        sa.Column("profile_record_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("position_id", _uuid(), nullable=False),
        sa.Column("position_key", sa.String(), nullable=False),
        sa.Column("capability_key", sa.String(), nullable=False),
        sa.Column("context_scope", sa.String(), nullable=False),
        sa.Column("policy_sequence", sa.Integer(), nullable=False),
        sa.Column("qualification_contract", sa.String(), nullable=False),
        sa.Column("max_observation_age_seconds", sa.Integer(), nullable=False),
        sa.Column("max_source_age_seconds", sa.Integer(), nullable=False),
        sa.Column("max_candidate_observations", sa.Integer(), nullable=False),
        sa.Column("policy_reason", sa.String(), nullable=False),
        sa.Column("supersedes_policy_id", _uuid(), nullable=True),
        sa.Column("decision_activity_id", _uuid(), nullable=False),
        sa.Column("decision_activity_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("idempotency_key", sa.String(), nullable=False),
        sa.Column("record_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.CheckConstraint(
            "profile_sequence >= 1",
            name="ck_cap_auto_eval_profile_sequence_positive",
        ),
        sa.CheckConstraint(
            "policy_sequence >= 1",
            name="ck_cap_auto_eval_policy_sequence_positive",
        ),
        sa.CheckConstraint(
            "max_observation_age_seconds >= 1",
            name="ck_cap_auto_eval_observation_age_positive",
        ),
        sa.CheckConstraint(
            "max_source_age_seconds >= 1",
            name="ck_cap_auto_eval_source_age_positive",
        ),
        sa.CheckConstraint(
            "max_candidate_observations >= 1 AND max_candidate_observations <= 5000",
            name="ck_cap_auto_eval_candidate_bound",
        ),
        sa.CheckConstraint(
            "supersedes_policy_id IS NULL OR supersedes_policy_id <> id",
            name="ck_cap_auto_eval_not_self_superseding",
        ),
        sa.CheckConstraint(
            "length(profile_record_fingerprint) = 64",
            name="ck_cap_auto_eval_profile_fingerprint",
        ),
        sa.CheckConstraint(
            "length(decision_activity_fingerprint) = 64",
            name="ck_cap_auto_eval_activity_fingerprint",
        ),
        sa.CheckConstraint(
            "length(record_fingerprint) = 64",
            name="ck_cap_auto_eval_record_fingerprint",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_key", "profile_id"],
            ["capability_autonomy_profiles.tenant_key", "capability_autonomy_profiles.id"],
            name="fk_cap_auto_eval_profile_tenant",
        ),
        sa.ForeignKeyConstraint(
            ["position_id"],
            ["organization_positions.id"],
            name="fk_cap_auto_eval_position",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_key", "decision_activity_id"],
            ["organization_activities.tenant_key", "organization_activities.id"],
            name="fk_cap_auto_eval_activity_tenant",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_key", "supersedes_policy_id"],
            [
                "capability_autonomy_evidence_evaluation_policies.tenant_key",
                "capability_autonomy_evidence_evaluation_policies.id",
            ],
            name="fk_cap_auto_eval_supersedes_tenant",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_key",
            "id",
            name="uq_cap_auto_eval_policy_tenant_id",
        ),
        sa.UniqueConstraint(
            "tenant_key",
            "idempotency_key",
            name="uq_cap_auto_eval_policy_idempotency",
        ),
        sa.UniqueConstraint(
            "tenant_key",
            "profile_id",
            "policy_sequence",
            name="uq_cap_auto_eval_policy_profile_sequence",
        ),
        sa.UniqueConstraint(
            "tenant_key",
            "supersedes_policy_id",
            name="uq_cap_auto_eval_policy_supersedes",
        ),
    )
    op.create_index(
        "ix_cap_auto_eval_policy_profile_seq",
        "capability_autonomy_evidence_evaluation_policies",
        ["tenant_key", "profile_id", "policy_sequence"],
    )
    op.create_index(
        "ix_cap_auto_eval_policy_profile_created",
        "capability_autonomy_evidence_evaluation_policies",
        ["tenant_key", "profile_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_table("capability_autonomy_evidence_evaluation_policies")
