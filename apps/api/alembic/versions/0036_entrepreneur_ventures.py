"""Review-gated entrepreneur and startup venture dossiers.

Revision ID: 0036_entrepreneur_ventures
Revises: 0035_relocation_tasks
Create Date: 2026-07-23
"""
from alembic import op
import sqlalchemy as sa


revision = "0036_entrepreneur_ventures"
down_revision = "0035_relocation_tasks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "entrepreneur_venture_profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("corporate_mobility_case_id", sa.Uuid(), nullable=False),
        sa.Column("founder_lead_id", sa.Uuid(), nullable=False),
        sa.Column("venture_name", sa.String(), nullable=False),
        sa.Column("venture_stage", sa.String(), nullable=False),
        sa.Column("sector", sa.String(), nullable=False),
        sa.Column("target_country", sa.String(), nullable=False),
        sa.Column("incorporation_country", sa.String(), nullable=True),
        sa.Column("founder_role", sa.String(), nullable=False),
        sa.Column("business_model_summary", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("human_review_required", sa.Boolean(), nullable=False),
        sa.Column("submitted_by", sa.String(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(), nullable=True),
        sa.Column("reviewed_by", sa.String(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("review_notes", sa.String(), nullable=True),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("updated_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["corporate_mobility_case_id"], ["corporate_mobility_cases.id"]),
        sa.ForeignKeyConstraint(["founder_lead_id"], ["leads.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_entrepreneur_venture_profiles_corporate_mobility_case_id",
        "entrepreneur_venture_profiles",
        ["corporate_mobility_case_id"],
        unique=True,
    )
    for column in (
        "id", "founder_lead_id", "venture_name", "venture_stage", "sector", "target_country",
        "incorporation_country", "status", "submitted_by", "submitted_at", "reviewed_by",
        "reviewed_at", "created_by", "updated_by", "created_at",
    ):
        op.create_index(f"ix_entrepreneur_venture_profiles_{column}", "entrepreneur_venture_profiles", [column])

    op.create_table(
        "venture_evidence_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("venture_profile_id", sa.Uuid(), nullable=False),
        sa.Column("evidence_type", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("declared_amount_minor", sa.Integer(), nullable=True),
        sa.Column("currency", sa.String(), nullable=True),
        sa.Column("document_record_id", sa.Uuid(), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["venture_profile_id"], ["entrepreneur_venture_profiles.id"]),
        sa.ForeignKeyConstraint(["document_record_id"], ["documents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "id", "venture_profile_id", "evidence_type", "currency", "document_record_id", "created_by", "created_at",
    ):
        op.create_index(f"ix_venture_evidence_items_{column}", "venture_evidence_items", [column])

    op.create_table(
        "venture_review_decisions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("venture_profile_id", sa.Uuid(), nullable=False),
        sa.Column("decision", sa.String(), nullable=False),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column("reviewer", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["venture_profile_id"], ["entrepreneur_venture_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("id", "venture_profile_id", "decision", "reviewer", "created_at"):
        op.create_index(f"ix_venture_review_decisions_{column}", "venture_review_decisions", [column])


def downgrade() -> None:
    op.drop_table("venture_review_decisions")
    op.drop_table("venture_evidence_items")
    op.drop_table("entrepreneur_venture_profiles")
