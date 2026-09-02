"""Reviewed global country ranking assessments.

Revision ID: 0028_country_ranking_assessments
Revises: 0027_reassessment_acceptances
Create Date: 2026-07-14
"""
from alembic import op
import sqlalchemy as sa

revision = "0028_country_ranking_assessments"
down_revision = "0027_reassessment_acceptances"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "country_ranking_assessments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("ranking_key", sa.String(), nullable=False),
        sa.Column("lead_id", sa.Uuid(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=True),
        sa.Column("profile_version", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="reviewed_catalogue_only"),
        sa.Column("input_sha256", sa.String(), nullable=False),
        sa.Column("catalogue_version_ids_json", sa.String(), nullable=False, server_default="[]"),
        sa.Column("scope_json", sa.String(), nullable=False, server_default="{}"),
        sa.Column("ranking_json", sa.String(), nullable=False, server_default="[]"),
        sa.Column("explicit_user_acceptance", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("user_attestation", sa.String(), nullable=False),
        sa.Column("notes", sa.String(), nullable=False),
        sa.Column("global_coverage_claim_ready", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("human_review_required", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("generated_by", sa.String(), nullable=False),
        sa.Column("summary", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "id", "lead_id", "profile_id", "profile_version", "status", "input_sha256",
        "global_coverage_claim_ready", "generated_by", "created_at",
    ):
        op.create_index(
            f"ix_country_ranking_assessments_{column}",
            "country_ranking_assessments",
            [column],
        )
    op.create_index(
        "ix_country_ranking_assessments_ranking_key",
        "country_ranking_assessments",
        ["ranking_key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_table("country_ranking_assessments")
