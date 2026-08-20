"""Add canonical governed EligibilityAssessment revision lineage.

Revision ID: 0077_canonical_eligibility_assessment_revision
Revises: 0076_organization_position_active_identity
Create Date: 2026-08-20
"""

from alembic import op
import sqlalchemy as sa


revision = "0077_canonical_eligibility_assessment_revision"
down_revision = "0076_organization_position_active_identity"
branch_labels = None
depends_on = None


def _uuid() -> sa.Uuid:
    return sa.Uuid()


def upgrade() -> None:
    op.create_table(
        "eligibility_assessment_revisions",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("assessment_id", _uuid(), nullable=False),
        sa.Column("tenant_key", sa.String(), nullable=False),
        sa.Column("aggregate_key", sa.String(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("lifecycle_status", sa.String(), nullable=False),
        sa.Column("supersedes_revision_id", _uuid(), nullable=True),
        sa.Column("lead_id", _uuid(), nullable=False),
        sa.Column("profile_id", _uuid(), nullable=False),
        sa.Column("profile_version", sa.Integer(), nullable=False),
        sa.Column("pathway_version_id", _uuid(), nullable=False),
        sa.Column("governance_activity_id", _uuid(), nullable=False),
        sa.Column("verification_activity_id", _uuid(), nullable=False),
        sa.Column("verification_floor_activity_id", _uuid(), nullable=False),
        sa.Column("semantic_activity_id", _uuid(), nullable=True),
        sa.Column("original_action_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("intent_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("readiness_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("verification_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("verification_floor_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("effect_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("post_review_required", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("version >= 1", name="ck_eligibility_revision_version_positive"),
        sa.CheckConstraint(
            "lifecycle_status IN ('active','superseded')",
            name="ck_eligibility_revision_lifecycle_status",
        ),
        sa.CheckConstraint(
            "length(original_action_fingerprint) = 64",
            name="ck_eligibility_revision_action_fingerprint",
        ),
        sa.CheckConstraint(
            "length(intent_fingerprint) = 64",
            name="ck_eligibility_revision_intent_fingerprint",
        ),
        sa.CheckConstraint(
            "length(readiness_fingerprint) = 64",
            name="ck_eligibility_revision_readiness_fingerprint",
        ),
        sa.CheckConstraint(
            "length(verification_fingerprint) = 64",
            name="ck_eligibility_revision_verification_fingerprint",
        ),
        sa.CheckConstraint(
            "length(verification_floor_fingerprint) = 64",
            name="ck_eligibility_revision_floor_fingerprint",
        ),
        sa.CheckConstraint(
            "length(effect_fingerprint) = 64",
            name="ck_eligibility_revision_effect_fingerprint",
        ),
        sa.ForeignKeyConstraint(["assessment_id"], ["eligibility_assessments.id"]),
        sa.ForeignKeyConstraint(["supersedes_revision_id"], ["eligibility_assessment_revisions.id"]),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"]),
        sa.ForeignKeyConstraint(["pathway_version_id"], ["mobility_pathway_versions.id"]),
        sa.ForeignKeyConstraint(
            ["tenant_key", "governance_activity_id"],
            ["organization_activities.tenant_key", "organization_activities.id"],
            name="fk_eligibility_revision_governance_activity_tenant",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_key", "verification_activity_id"],
            ["organization_activities.tenant_key", "organization_activities.id"],
            name="fk_eligibility_revision_verification_activity_tenant",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_key", "verification_floor_activity_id"],
            ["organization_activities.tenant_key", "organization_activities.id"],
            name="fk_eligibility_revision_floor_activity_tenant",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_key", "semantic_activity_id"],
            ["organization_activities.tenant_key", "organization_activities.id"],
            name="fk_eligibility_revision_semantic_activity_tenant",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_key",
            "aggregate_key",
            "version",
            name="uq_eligibility_revision_aggregate_version",
        ),
        sa.UniqueConstraint("assessment_id", name="uq_eligibility_revision_assessment"),
        sa.UniqueConstraint(
            "tenant_key",
            "governance_activity_id",
            name="uq_eligibility_revision_governance_activity",
        ),
        sa.UniqueConstraint(
            "tenant_key",
            "effect_fingerprint",
            name="uq_eligibility_revision_effect_fingerprint",
        ),
    )
    for column in (
        "id",
        "assessment_id",
        "tenant_key",
        "aggregate_key",
        "version",
        "lifecycle_status",
        "supersedes_revision_id",
        "lead_id",
        "profile_id",
        "profile_version",
        "pathway_version_id",
        "governance_activity_id",
        "verification_activity_id",
        "verification_floor_activity_id",
        "semantic_activity_id",
        "original_action_fingerprint",
        "intent_fingerprint",
        "readiness_fingerprint",
        "verification_fingerprint",
        "verification_floor_fingerprint",
        "effect_fingerprint",
        "post_review_required",
        "created_at",
    ):
        op.create_index(
            f"ix_eligibility_assessment_revisions_{column}",
            "eligibility_assessment_revisions",
            [column],
        )


def downgrade() -> None:
    op.drop_table("eligibility_assessment_revisions")
