"""HNWI and family-office mobility readiness.

Revision ID: 0041_family_office_mobility
Revises: 0040_investment_rule_review
Create Date: 2026-07-23
"""

from alembic import op
import sqlalchemy as sa


revision = "0041_family_office_mobility"
down_revision = "0040_investment_rule_review"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "family_office_mobility_assessments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("lead_id", sa.Uuid(), nullable=False),
        sa.Column("business_advisory_assessment_id", sa.Uuid(), nullable=True),
        sa.Column("family_office_name", sa.String(), nullable=True),
        sa.Column("input_json", sa.String(), nullable=False),
        sa.Column("readiness_score", sa.Float(), nullable=False),
        sa.Column("readiness_band", sa.String(), nullable=False),
        sa.Column("identity_score", sa.Float(), nullable=False),
        sa.Column("wealth_evidence_score", sa.Float(), nullable=False),
        sa.Column("ownership_transparency_score", sa.Float(), nullable=False),
        sa.Column("governance_score", sa.Float(), nullable=False),
        sa.Column("mobility_grounding_score", sa.Float(), nullable=False),
        sa.Column("workstreams_json", sa.String(), nullable=False),
        sa.Column("blockers_json", sa.String(), nullable=False),
        sa.Column("next_actions_json", sa.String(), nullable=False),
        sa.Column("evidence_basis_json", sa.String(), nullable=False),
        sa.Column("grounded_pathway_versions_json", sa.String(), nullable=False),
        sa.Column("grounded_program_versions_json", sa.String(), nullable=False),
        sa.Column("escalation_flags_json", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("human_review_required", sa.Boolean(), nullable=False),
        sa.Column("generated_by", sa.String(), nullable=False),
        sa.Column("reviewed_by", sa.String(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("review_notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.ForeignKeyConstraint(
            ["business_advisory_assessment_id"],
            ["business_mobility_advisory_assessments.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    index_columns = {
        "id": "id",
        "lead_id": "lead",
        "business_advisory_assessment_id": "advisory",
        "family_office_name": "office_name",
        "readiness_band": "readiness",
        "status": "status",
        "generated_by": "generator",
        "reviewed_by": "reviewer",
        "reviewed_at": "reviewed_at",
        "created_at": "created_at",
    }
    for column, suffix in index_columns.items():
        op.create_index(
            f"ix_family_office_assessments_{suffix}",
            "family_office_mobility_assessments",
            [column],
        )

    op.create_table(
        "family_office_mobility_reviews",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("assessment_id", sa.Uuid(), nullable=False),
        sa.Column("decision", sa.String(), nullable=False),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column("reviewer", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["assessment_id"],
            ["family_office_mobility_assessments.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("id", "assessment_id", "decision", "reviewer", "created_at"):
        op.create_index(
            f"ix_family_office_mobility_reviews_{column}",
            "family_office_mobility_reviews",
            [column],
        )


def downgrade() -> None:
    op.drop_table("family_office_mobility_reviews")
    op.drop_table("family_office_mobility_assessments")
