"""Human-reviewed jurisdiction immigration-rule assessments.

Revision ID: 0018_jurisdiction_immigration_assessments
Revises: 0017_global_jurisdiction_registry
Create Date: 2026-07-14
"""

from alembic import op
import sqlalchemy as sa


revision = "0018_jurisdiction_immigration_assessments"
down_revision = "0017_global_jurisdiction_registry"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "jurisdiction_immigration_assessments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("jurisdiction_id", sa.Uuid(), nullable=False),
        sa.Column("registry_entry_id", sa.Uuid(), nullable=False),
        sa.Column("assessment_version", sa.Integer(), nullable=False),
        sa.Column("rule_relationship", sa.String(), nullable=False),
        sa.Column("parent_code", sa.String(), nullable=True),
        sa.Column("evidence_url", sa.String(), nullable=False),
        sa.Column("evidence_title", sa.String(), nullable=False),
        sa.Column("official_source_id", sa.Uuid(), nullable=True),
        sa.Column("source_snapshot_id", sa.Uuid(), nullable=True),
        sa.Column("rationale", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("proposed_by", sa.String(), nullable=False),
        sa.Column("reviewed_by", sa.String(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("review_notes", sa.String(), nullable=True),
        sa.Column("supersedes_assessment_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["jurisdiction_id"], ["jurisdictions.id"]),
        sa.ForeignKeyConstraint(["registry_entry_id"], ["jurisdiction_registry_entries.id"]),
        sa.ForeignKeyConstraint(["official_source_id"], ["official_sources.id"]),
        sa.ForeignKeyConstraint(["source_snapshot_id"], ["source_snapshots.id"]),
        sa.ForeignKeyConstraint(
            ["supersedes_assessment_id"],
            ["jurisdiction_immigration_assessments.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "jurisdiction_id",
            "assessment_version",
            name="uq_jurisdiction_immigration_assessment_version",
        ),
    )
    for column in (
        "id",
        "jurisdiction_id",
        "registry_entry_id",
        "assessment_version",
        "rule_relationship",
        "parent_code",
        "official_source_id",
        "source_snapshot_id",
        "status",
        "reviewed_by",
        "reviewed_at",
        "supersedes_assessment_id",
        "created_at",
    ):
        op.create_index(
            f"ix_jia_{column}",
            "jurisdiction_immigration_assessments",
            [column],
        )


def downgrade() -> None:
    op.drop_table("jurisdiction_immigration_assessments")
