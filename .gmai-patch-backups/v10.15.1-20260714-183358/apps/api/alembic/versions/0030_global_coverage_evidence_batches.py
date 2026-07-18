"""Controlled global coverage evidence batches.

Revision ID: 0030_global_coverage_evidence_batches
Revises: 0029_multi_year_mobility_scenarios
Create Date: 2026-07-14
"""
from alembic import op
import sqlalchemy as sa

revision = "0030_global_coverage_evidence_batches"
down_revision = "0029_multi_year_mobility_scenarios"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "jurisdiction_coverage_evidence_batches",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("registry_release_id", sa.Uuid(), nullable=False),
        sa.Column("batch_key", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("notes", sa.String(), nullable=False),
        sa.Column("item_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("immigration_assessment_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("source_certification_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(), nullable=False, server_default="submitted_for_review"),
        sa.Column("submitted_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["registry_release_id"], ["jurisdiction_registry_releases.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "id", "registry_release_id", "name", "status", "submitted_by", "created_at",
    ):
        op.create_index(
            f"ix_jurisdiction_coverage_evidence_batches_{column}",
            "jurisdiction_coverage_evidence_batches",
            [column],
        )
    op.create_index(
        "ix_jurisdiction_coverage_evidence_batches_batch_key",
        "jurisdiction_coverage_evidence_batches",
        ["batch_key"],
        unique=True,
    )

    op.create_table(
        "jurisdiction_coverage_evidence_batch_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("batch_id", sa.Uuid(), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("jurisdiction_id", sa.Uuid(), nullable=False),
        sa.Column("registry_entry_id", sa.Uuid(), nullable=False),
        sa.Column("alpha2_code", sa.String(), nullable=False),
        sa.Column("immigration_assessment_id", sa.Uuid(), nullable=True),
        sa.Column("source_certification_id", sa.Uuid(), nullable=True),
        sa.Column("payload_sha256", sa.String(), nullable=False),
        sa.Column("payload_json", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["jurisdiction_coverage_evidence_batches.id"]),
        sa.ForeignKeyConstraint(["jurisdiction_id"], ["jurisdictions.id"]),
        sa.ForeignKeyConstraint(["registry_entry_id"], ["jurisdiction_registry_entries.id"]),
        sa.ForeignKeyConstraint(["immigration_assessment_id"], ["jurisdiction_immigration_assessments.id"]),
        sa.ForeignKeyConstraint(["source_certification_id"], ["jurisdiction_source_certifications.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "id", "batch_id", "row_number", "jurisdiction_id", "registry_entry_id", "alpha2_code",
        "immigration_assessment_id", "source_certification_id", "payload_sha256", "created_at",
    ):
        op.create_index(
            f"ix_jurisdiction_coverage_evidence_batch_items_{column}",
            "jurisdiction_coverage_evidence_batch_items",
            [column],
        )


def downgrade() -> None:
    op.drop_table("jurisdiction_coverage_evidence_batch_items")
    op.drop_table("jurisdiction_coverage_evidence_batches")
