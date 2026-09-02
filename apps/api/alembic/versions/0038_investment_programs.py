"""Governed investment mobility program catalogue.

Revision ID: 0038_investment_programs
Revises: 0037_business_advisory
Create Date: 2026-07-23
"""
from alembic import op
import sqlalchemy as sa


revision = "0038_investment_programs"
down_revision = "0037_business_advisory"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "investment_mobility_programs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("program_key", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("country", sa.String(), nullable=False),
        sa.Column("program_type", sa.String(), nullable=False),
        sa.Column("pathway_id", sa.Uuid(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("catalogue_status", sa.String(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["pathway_id"], ["mobility_pathways.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("program_key"),
    )
    for column in ("id", "program_key", "name", "country", "program_type", "pathway_id", "catalogue_status", "created_by", "created_at"):
        op.create_index(f"ix_investment_mobility_programs_{column}", "investment_mobility_programs", [column])

    op.create_table(
        "investment_mobility_program_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("program_id", sa.Uuid(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("lifecycle_status", sa.String(), nullable=False),
        sa.Column("supersedes_version_id", sa.Uuid(), nullable=True),
        sa.Column("pathway_version_id", sa.Uuid(), nullable=False),
        sa.Column("official_source_id", sa.Uuid(), nullable=False),
        sa.Column("source_snapshot_id", sa.Uuid(), nullable=False),
        sa.Column("minimum_commitment_minor", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(), nullable=False),
        sa.Column("investment_options_json", sa.String(), nullable=False),
        sa.Column("holding_period_text", sa.String(), nullable=True),
        sa.Column("physical_presence_text", sa.String(), nullable=True),
        sa.Column("family_scope_json", sa.String(), nullable=False),
        sa.Column("due_diligence_json", sa.String(), nullable=False),
        sa.Column("fees_json", sa.String(), nullable=False),
        sa.Column("benefits_json", sa.String(), nullable=False),
        sa.Column("risks_json", sa.String(), nullable=False),
        sa.Column("effective_from", sa.DateTime(), nullable=True),
        sa.Column("effective_to", sa.DateTime(), nullable=True),
        sa.Column("human_review_required", sa.Boolean(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("approved_by", sa.String(), nullable=True),
        sa.Column("review_notes", sa.String(), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["program_id"], ["investment_mobility_programs.id"]),
        sa.ForeignKeyConstraint(["supersedes_version_id"], ["investment_mobility_program_versions.id"]),
        sa.ForeignKeyConstraint(["pathway_version_id"], ["mobility_pathway_versions.id"]),
        sa.ForeignKeyConstraint(["official_source_id"], ["official_sources.id"]),
        sa.ForeignKeyConstraint(["source_snapshot_id"], ["source_snapshots.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    indexes = {
        "ix_inv_program_versions_id": "id",
        "ix_inv_program_versions_program_id": "program_id",
        "ix_inv_program_versions_number": "version_number",
        "ix_inv_program_versions_status": "lifecycle_status",
        "ix_inv_program_versions_supersedes": "supersedes_version_id",
        "ix_inv_program_versions_pathway": "pathway_version_id",
        "ix_inv_program_versions_source": "official_source_id",
        "ix_inv_program_versions_snapshot": "source_snapshot_id",
        "ix_inv_program_versions_created_by": "created_by",
        "ix_inv_program_versions_approved_by": "approved_by",
        "ix_inv_program_versions_published_at": "published_at",
        "ix_inv_program_versions_created_at": "created_at",
    }
    for name, column in indexes.items():
        op.create_index(name, "investment_mobility_program_versions", [column])


def downgrade() -> None:
    op.drop_table("investment_mobility_program_versions")
    op.drop_table("investment_mobility_programs")
