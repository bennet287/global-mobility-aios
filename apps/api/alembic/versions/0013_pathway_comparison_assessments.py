"""Persisted pathway comparison assessments.

Revision ID: 0013_pathway_comparison_assessments
Revises: 0012_versioned_pathway_catalogue
Create Date: 2026-07-14
"""

from alembic import op
import sqlalchemy as sa


revision = "0013_pathway_comparison_assessments"
down_revision = "0012_versioned_pathway_catalogue"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pathway_comparison_assessments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("lead_id", sa.Uuid(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=True),
        sa.Column("profile_version", sa.Integer(), nullable=True),
        sa.Column("primary_pathway_id", sa.Uuid(), nullable=True),
        sa.Column("primary_pathway_version_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="insufficient_pathways"),
        sa.Column("comparison_json", sa.String(), nullable=True),
        sa.Column("cost_summary_json", sa.String(), nullable=True),
        sa.Column("risk_summary_json", sa.String(), nullable=True),
        sa.Column("alternative_pathways_json", sa.String(), nullable=True),
        sa.Column("missing_evidence_json", sa.String(), nullable=True),
        sa.Column("summary", sa.String(), nullable=True),
        sa.Column("human_review_required", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("generated_by", sa.String(), nullable=False, server_default="system"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"]),
        sa.ForeignKeyConstraint(["primary_pathway_id"], ["mobility_pathways.id"]),
        sa.ForeignKeyConstraint(["primary_pathway_version_id"], ["mobility_pathway_versions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "id",
        "lead_id",
        "profile_id",
        "primary_pathway_id",
        "primary_pathway_version_id",
        "status",
        "created_at",
    ):
        op.create_index(
            f"ix_pathway_comparison_assessments_{column}",
            "pathway_comparison_assessments",
            [column],
            unique=False,
        )


def downgrade() -> None:
    op.drop_table("pathway_comparison_assessments")
