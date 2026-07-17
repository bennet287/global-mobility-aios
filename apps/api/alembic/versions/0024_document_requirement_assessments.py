"""Immutable document requirement coverage assessments.

Revision ID: 0024_document_requirement_assessments
Revises: 0023_document_expiry_reminders
Create Date: 2026-07-14
"""

from alembic import op
import sqlalchemy as sa


revision = "0024_document_requirement_assessments"
down_revision = "0023_document_expiry_reminders"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "document_requirement_assessments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("assessment_key", sa.String(), nullable=False),
        sa.Column("lead_id", sa.Uuid(), nullable=False),
        sa.Column("application_id", sa.Uuid(), nullable=True),
        sa.Column("pathway_id", sa.Uuid(), nullable=True),
        sa.Column("pathway_version_id", sa.Uuid(), nullable=True),
        sa.Column("eligibility_assessment_id", sa.Uuid(), nullable=True),
        sa.Column("profile_id", sa.Uuid(), nullable=True),
        sa.Column("profile_version", sa.Integer(), nullable=True),
        sa.Column("requirement_source", sa.String(), nullable=False),
        sa.Column("result_status", sa.String(), nullable=False, server_default="insufficient_context"),
        sa.Column("review_status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("required_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("satisfied_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("missing_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("inconsistency_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("requirements_json", sa.String(), nullable=False),
        sa.Column("findings_json", sa.String(), nullable=False),
        sa.Column("source_snapshot_json", sa.String(), nullable=False),
        sa.Column("document_snapshot_json", sa.String(), nullable=False),
        sa.Column("summary", sa.String(), nullable=False),
        sa.Column("human_review_required", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("generated_by", sa.String(), nullable=False, server_default="system"),
        sa.Column("reviewed_by", sa.String(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("review_notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"]),
        sa.ForeignKeyConstraint(["pathway_id"], ["mobility_pathways.id"]),
        sa.ForeignKeyConstraint(["pathway_version_id"], ["mobility_pathway_versions.id"]),
        sa.ForeignKeyConstraint(["eligibility_assessment_id"], ["eligibility_assessments.id"]),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "id",
        "lead_id",
        "application_id",
        "pathway_id",
        "pathway_version_id",
        "eligibility_assessment_id",
        "profile_id",
        "profile_version",
        "requirement_source",
        "result_status",
        "review_status",
        "reviewed_by",
        "reviewed_at",
        "created_at",
    ):
        op.create_index(
            f"ix_document_requirement_assessments_{column}",
            "document_requirement_assessments",
            [column],
        )
    op.create_index(
        "ix_document_requirement_assessments_assessment_key",
        "document_requirement_assessments",
        ["assessment_key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_table("document_requirement_assessments")
