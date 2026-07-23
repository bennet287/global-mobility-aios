"""Independent review for investment mobility rule proposals.

Revision ID: 0040_investment_rule_review
Revises: 0039_investment_suitability
Create Date: 2026-07-23
"""
from alembic import op
import sqlalchemy as sa


revision = "0040_investment_rule_review"
down_revision = "0039_investment_suitability"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "investment_mobility_rule_proposals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("pathway_version_id", sa.Uuid(), nullable=False),
        sa.Column("official_source_id", sa.Uuid(), nullable=False),
        sa.Column("source_snapshot_id", sa.Uuid(), nullable=False),
        sa.Column("proposed_rules_json", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("proposed_by", sa.String(), nullable=False),
        sa.Column("reviewed_by", sa.String(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("review_notes", sa.String(), nullable=True),
        sa.Column("created_verified_rule_ids_json", sa.String(), nullable=False),
        sa.Column("replacement_pathway_version_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["pathway_version_id"], ["mobility_pathway_versions.id"]),
        sa.ForeignKeyConstraint(["official_source_id"], ["official_sources.id"]),
        sa.ForeignKeyConstraint(["source_snapshot_id"], ["source_snapshots.id"]),
        sa.ForeignKeyConstraint(["replacement_pathway_version_id"], ["mobility_pathway_versions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "id", "pathway_version_id", "official_source_id", "source_snapshot_id", "status",
        "proposed_by", "reviewed_by", "reviewed_at", "replacement_pathway_version_id", "created_at",
    ):
        op.create_index(
            f"ix_inv_rule_proposals_{column}",
            "investment_mobility_rule_proposals",
            [column],
        )

    op.create_table(
        "investment_mobility_rule_decisions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("proposal_id", sa.Uuid(), nullable=False),
        sa.Column("decision", sa.String(), nullable=False),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column("reviewer", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["proposal_id"], ["investment_mobility_rule_proposals.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("id", "proposal_id", "decision", "reviewer", "created_at"):
        op.create_index(
            f"ix_inv_rule_decisions_{column}",
            "investment_mobility_rule_decisions",
            [column],
        )


def downgrade() -> None:
    op.drop_table("investment_mobility_rule_decisions")
    op.drop_table("investment_mobility_rule_proposals")
