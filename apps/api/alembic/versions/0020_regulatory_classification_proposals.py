"""Governed regulatory classification proposals.

Revision ID: 0020_regulatory_classification_proposals
Revises: 0019_jurisdiction_source_certifications
Create Date: 2026-07-14
"""

from alembic import op
import sqlalchemy as sa


revision = "0020_regulatory_classification_proposals"
down_revision = "0019_jurisdiction_source_certifications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "regulatory_classification_proposals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("regulatory_change_id", sa.Uuid(), nullable=False),
        sa.Column("previous_snapshot_id", sa.Uuid(), nullable=True),
        sa.Column("current_snapshot_id", sa.Uuid(), nullable=False),
        sa.Column("proposed_change_type", sa.String(), nullable=False),
        sa.Column("proposed_materiality", sa.String(), nullable=False),
        sa.Column("proposed_summary", sa.String(), nullable=False),
        sa.Column("rationale", sa.String(), nullable=False),
        sa.Column("evidence_json", sa.String(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("method", sa.String(), nullable=False),
        sa.Column("provider", sa.String(), nullable=True),
        sa.Column("model", sa.String(), nullable=True),
        sa.Column("prompt_version", sa.String(), nullable=False),
        sa.Column("model_metadata_json", sa.String(), nullable=True),
        sa.Column("fallback_reason", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("reviewed_by", sa.String(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("review_notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["regulatory_change_id"], ["regulatory_changes.id"]),
        sa.ForeignKeyConstraint(["previous_snapshot_id"], ["source_snapshots.id"]),
        sa.ForeignKeyConstraint(["current_snapshot_id"], ["source_snapshots.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "id",
        "regulatory_change_id",
        "previous_snapshot_id",
        "current_snapshot_id",
        "proposed_change_type",
        "proposed_materiality",
        "method",
        "provider",
        "status",
        "created_by",
        "reviewed_by",
        "reviewed_at",
        "created_at",
    ):
        op.create_index(
            f"ix_regulatory_classification_proposals_{column}",
            "regulatory_classification_proposals",
            [column],
        )


def downgrade() -> None:
    op.drop_table("regulatory_classification_proposals")
