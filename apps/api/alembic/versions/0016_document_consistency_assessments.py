"""Document consistency assessments against profile and application facts.

Revision ID: 0016_document_consistency_assessments
Revises: 0015_document_intelligence_foundation
Create Date: 2026-07-14
"""

from alembic import op
import sqlalchemy as sa


revision = "0016_document_consistency_assessments"
down_revision = "0015_document_intelligence_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "document_consistency_assessments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("extraction_job_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("lead_id", sa.Uuid(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("profile_version", sa.Integer(), nullable=False),
        sa.Column("application_id", sa.Uuid(), nullable=True),
        sa.Column("result_status", sa.String(), nullable=False, server_default="insufficient_context"),
        sa.Column("review_status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("match_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("mismatch_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("missing_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("findings_json", sa.String(), nullable=False),
        sa.Column("source_facts_json", sa.String(), nullable=False),
        sa.Column("summary", sa.String(), nullable=False),
        sa.Column("human_review_required", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("generated_by", sa.String(), nullable=False, server_default="system"),
        sa.Column("reviewed_by", sa.String(), nullable=True),
        sa.Column("review_notes", sa.String(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["extraction_job_id"], ["document_extraction_jobs.id"]),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"]),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"]),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "id", "extraction_job_id", "document_id", "lead_id", "profile_id", "profile_version",
        "application_id", "result_status", "review_status", "created_at",
    ):
        op.create_index(
            f"ix_document_consistency_assessments_{column}",
            "document_consistency_assessments",
            [column],
        )


def downgrade() -> None:
    op.drop_table("document_consistency_assessments")
