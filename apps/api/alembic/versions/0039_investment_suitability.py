"""Client investment-mobility suitability comparisons.

Revision ID: 0039_investment_suitability
Revises: 0038_investment_programs
Create Date: 2026-07-23
"""
from alembic import op
import sqlalchemy as sa


revision = "0039_investment_suitability"
down_revision = "0038_investment_programs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "investment_mobility_suitability_assessments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("lead_id", sa.Uuid(), nullable=False),
        sa.Column("business_advisory_assessment_id", sa.Uuid(), nullable=True),
        sa.Column("input_json", sa.String(), nullable=False),
        sa.Column("candidate_program_version_ids_json", sa.String(), nullable=False),
        sa.Column("ranked_programs_json", sa.String(), nullable=False),
        sa.Column("blockers_json", sa.String(), nullable=False),
        sa.Column("next_actions_json", sa.String(), nullable=False),
        sa.Column("evidence_basis_json", sa.String(), nullable=False),
        sa.Column("overall_readiness_score", sa.Float(), nullable=False),
        sa.Column("readiness_band", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("human_review_required", sa.Boolean(), nullable=False),
        sa.Column("generated_by", sa.String(), nullable=False),
        sa.Column("reviewed_by", sa.String(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("review_notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.ForeignKeyConstraint(["business_advisory_assessment_id"], ["business_mobility_advisory_assessments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes = {
        "ix_inv_suitability_id": "id", "ix_inv_suitability_lead": "lead_id",
        "ix_inv_suitability_advisory": "business_advisory_assessment_id",
        "ix_inv_suitability_band": "readiness_band", "ix_inv_suitability_status": "status",
        "ix_inv_suitability_generated": "generated_by", "ix_inv_suitability_reviewed": "reviewed_by",
        "ix_inv_suitability_reviewed_at": "reviewed_at", "ix_inv_suitability_created": "created_at",
    }
    for name, column in indexes.items():
        op.create_index(name, "investment_mobility_suitability_assessments", [column])

    op.create_table(
        "investment_mobility_suitability_reviews",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("assessment_id", sa.Uuid(), nullable=False),
        sa.Column("decision", sa.String(), nullable=False),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column("reviewer", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["assessment_id"], ["investment_mobility_suitability_assessments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("id", "assessment_id", "decision", "reviewer", "created_at"):
        op.create_index(f"ix_inv_suitability_reviews_{column}", "investment_mobility_suitability_reviews", [column])


def downgrade() -> None:
    op.drop_table("investment_mobility_suitability_reviews")
    op.drop_table("investment_mobility_suitability_assessments")
