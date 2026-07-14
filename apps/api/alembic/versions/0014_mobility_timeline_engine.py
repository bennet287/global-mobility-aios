"""Multi-stage mobility timeline engine.

Revision ID: 0014_mobility_timeline_engine
Revises: 0013_pathway_comparison_assessments
Create Date: 2026-07-14
"""

from alembic import op
import sqlalchemy as sa


revision = "0014_mobility_timeline_engine"
down_revision = "0013_pathway_comparison_assessments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mobility_timelines",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("lead_id", sa.Uuid(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=True),
        sa.Column("profile_version", sa.Integer(), nullable=True),
        sa.Column("comparison_assessment_id", sa.Uuid(), nullable=False),
        sa.Column("primary_pathway_id", sa.Uuid(), nullable=False),
        sa.Column("primary_pathway_version_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="draft"),
        sa.Column("current_stage_key", sa.String(), nullable=True),
        sa.Column("target_date", sa.DateTime(), nullable=True),
        sa.Column("schedule_json", sa.String(), nullable=True),
        sa.Column("generated_by", sa.String(), nullable=False, server_default="system"),
        sa.Column("activated_by", sa.String(), nullable=True),
        sa.Column("activated_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"]),
        sa.ForeignKeyConstraint(["comparison_assessment_id"], ["pathway_comparison_assessments.id"]),
        sa.ForeignKeyConstraint(["primary_pathway_id"], ["mobility_pathways.id"]),
        sa.ForeignKeyConstraint(["primary_pathway_version_id"], ["mobility_pathway_versions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "id", "lead_id", "profile_id", "primary_pathway_id", "primary_pathway_version_id",
        "status", "current_stage_key", "created_at",
    ):
        op.create_index(f"ix_mobility_timelines_{column}", "mobility_timelines", [column], unique=False)
    op.create_index(
        "ix_mobility_timelines_comparison_assessment_id",
        "mobility_timelines",
        ["comparison_assessment_id"],
        unique=True,
    )

    op.create_table(
        "mobility_timeline_milestones",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("timeline_id", sa.Uuid(), nullable=False),
        sa.Column("stage_order", sa.Integer(), nullable=False),
        sa.Column("stage_key", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("dependencies_json", sa.String(), nullable=True),
        sa.Column("required_evidence_json", sa.String(), nullable=True),
        sa.Column("owner_role", sa.String(), nullable=False, server_default="mobility_operator"),
        sa.Column("due_at", sa.DateTime(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("blockers_json", sa.String(), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("requires_human_approval", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("approved_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["timeline_id"], ["mobility_timelines.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("id", "timeline_id", "stage_order", "stage_key", "status"):
        op.create_index(
            f"ix_mobility_timeline_milestones_{column}",
            "mobility_timeline_milestones",
            [column],
            unique=False,
        )


def downgrade() -> None:
    op.drop_table("mobility_timeline_milestones")
    op.drop_table("mobility_timelines")
