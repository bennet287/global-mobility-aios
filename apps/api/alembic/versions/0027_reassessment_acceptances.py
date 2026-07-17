"""Explicit reassessment acceptance controls.

Revision ID: 0027_reassessment_acceptances
Revises: 0026_document_access_grants
Create Date: 2026-07-14
"""
from alembic import op
import sqlalchemy as sa
revision = "0027_reassessment_acceptances"
down_revision = "0026_document_access_grants"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "reassessment_acceptances",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("acceptance_key", sa.String(), nullable=False),
        sa.Column("lead_id", sa.Uuid(), nullable=False),
        sa.Column("baseline_assessment_id", sa.Uuid(), nullable=False),
        sa.Column("accepted_profile_id", sa.Uuid(), nullable=True),
        sa.Column("accepted_profile_version", sa.Integer(), nullable=True),
        sa.Column("regulatory_impact_ids_json", sa.String(), nullable=False, server_default="[]"),
        sa.Column("accepted_pathway_version_ids_json", sa.String(), nullable=False, server_default="[]"),
        sa.Column("explicit_user_acceptance", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("user_attestation", sa.String(), nullable=False),
        sa.Column("notes", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="accepted"),
        sa.Column("recorded_by", sa.String(), nullable=False),
        sa.Column("accepted_at", sa.DateTime(), nullable=False),
        sa.Column("consumed_at", sa.DateTime(), nullable=True),
        sa.Column("generated_assessment_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.ForeignKeyConstraint(["baseline_assessment_id"], ["pathway_comparison_assessments.id"]),
        sa.ForeignKeyConstraint(["accepted_profile_id"], ["profiles.id"]),
        sa.ForeignKeyConstraint(["generated_assessment_id"], ["pathway_comparison_assessments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("id","lead_id","baseline_assessment_id","accepted_profile_id","accepted_profile_version","status","recorded_by","accepted_at","consumed_at","generated_assessment_id","created_at"):
        op.create_index(f"ix_reassessment_acceptances_{column}", "reassessment_acceptances", [column])
    op.create_index("ix_reassessment_acceptances_acceptance_key", "reassessment_acceptances", ["acceptance_key"], unique=True)

def downgrade() -> None:
    op.drop_table("reassessment_acceptances")
