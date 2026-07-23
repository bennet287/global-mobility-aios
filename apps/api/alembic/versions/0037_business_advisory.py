"""Evidence-grounded business and wealth mobility advisory.

Revision ID: 0037_business_advisory
Revises: 0036_entrepreneur_ventures
Create Date: 2026-07-23
"""
from alembic import op
import sqlalchemy as sa


revision = "0037_business_advisory"
down_revision = "0036_entrepreneur_ventures"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "business_mobility_advisory_assessments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("lead_id", sa.Uuid(), nullable=True),
        sa.Column("corporate_mobility_case_id", sa.Uuid(), nullable=True),
        sa.Column("primary_intent", sa.String(), nullable=False),
        sa.Column("situation_text", sa.String(), nullable=False),
        sa.Column("input_json", sa.String(), nullable=False),
        sa.Column("feasibility_score", sa.Float(), nullable=False),
        sa.Column("feasibility_band", sa.String(), nullable=False),
        sa.Column("information_score", sa.Float(), nullable=False),
        sa.Column("evidence_score", sa.Float(), nullable=False),
        sa.Column("commercial_fit_score", sa.Float(), nullable=False),
        sa.Column("pathway_grounding_score", sa.Float(), nullable=False),
        sa.Column("strategy_options_json", sa.String(), nullable=False),
        sa.Column("blockers_json", sa.String(), nullable=False),
        sa.Column("next_actions_json", sa.String(), nullable=False),
        sa.Column("evidence_basis_json", sa.String(), nullable=False),
        sa.Column("risk_flags_json", sa.String(), nullable=False),
        sa.Column("escalation_required", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("human_review_required", sa.Boolean(), nullable=False),
        sa.Column("generated_by", sa.String(), nullable=False),
        sa.Column("reviewed_by", sa.String(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("review_notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.ForeignKeyConstraint(["corporate_mobility_case_id"], ["corporate_mobility_cases.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_business_advisory_case_id",
        "business_mobility_advisory_assessments",
        ["corporate_mobility_case_id"],
    )
    for column in (
        "id", "lead_id", "primary_intent", "feasibility_band", "status", "generated_by",
        "reviewed_by", "reviewed_at", "created_at",
    ):
        op.create_index(
            f"ix_business_mobility_advisory_assessments_{column}",
            "business_mobility_advisory_assessments",
            [column],
        )

    op.create_table(
        "business_mobility_advisory_reviews",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("assessment_id", sa.Uuid(), nullable=False),
        sa.Column("decision", sa.String(), nullable=False),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column("reviewer", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["assessment_id"], ["business_mobility_advisory_assessments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("id", "assessment_id", "decision", "reviewer", "created_at"):
        op.create_index(
            f"ix_business_mobility_advisory_reviews_{column}",
            "business_mobility_advisory_reviews",
            [column],
        )


def downgrade() -> None:
    op.drop_table("business_mobility_advisory_reviews")
    op.drop_table("business_mobility_advisory_assessments")
