"""Versioned mobility pathway catalogue.

Revision ID: 0012_versioned_pathway_catalogue
Revises: 0011_universal_mobility_profile
Create Date: 2026-07-14
"""

from alembic import op
import sqlalchemy as sa


revision = "0012_versioned_pathway_catalogue"
down_revision = "0011_universal_mobility_profile"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mobility_pathways",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("pathway_key", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("country", sa.String(), nullable=False),
        sa.Column("domain", sa.String(), nullable=False),
        sa.Column("jurisdiction_id", sa.Uuid(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("catalogue_status", sa.String(), nullable=False, server_default="draft"),
        sa.Column("created_by", sa.String(), nullable=False, server_default="system"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["jurisdiction_id"], ["jurisdictions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("pathway_key", name="uq_mobility_pathways_pathway_key"),
    )
    for column in ("id", "pathway_key", "name", "country", "domain", "jurisdiction_id", "catalogue_status"):
        op.create_index(f"ix_mobility_pathways_{column}", "mobility_pathways", [column], unique=False)

    op.create_table(
        "mobility_pathway_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("pathway_id", sa.Uuid(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("lifecycle_status", sa.String(), nullable=False, server_default="draft"),
        sa.Column("supersedes_version_id", sa.Uuid(), nullable=True),
        sa.Column("official_source_id", sa.Uuid(), nullable=True),
        sa.Column("source_snapshot_id", sa.Uuid(), nullable=True),
        sa.Column("verified_rule_ids_json", sa.String(), nullable=True),
        sa.Column("eligibility_criteria_json", sa.String(), nullable=True),
        sa.Column("required_documents_json", sa.String(), nullable=True),
        sa.Column("costs_json", sa.String(), nullable=True),
        sa.Column("processing_time_json", sa.String(), nullable=True),
        sa.Column("benefits_json", sa.String(), nullable=True),
        sa.Column("risks_json", sa.String(), nullable=True),
        sa.Column("metadata_json", sa.String(), nullable=True),
        sa.Column("effective_from", sa.DateTime(), nullable=True),
        sa.Column("effective_to", sa.DateTime(), nullable=True),
        sa.Column("human_review_required", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("approved_by", sa.String(), nullable=True),
        sa.Column("review_notes", sa.String(), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.String(), nullable=False, server_default="system"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["pathway_id"], ["mobility_pathways.id"]),
        sa.ForeignKeyConstraint(["supersedes_version_id"], ["mobility_pathway_versions.id"]),
        sa.ForeignKeyConstraint(["official_source_id"], ["official_sources.id"]),
        sa.ForeignKeyConstraint(["source_snapshot_id"], ["source_snapshots.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("pathway_id", "version_number", name="uq_pathway_version_number"),
    )
    for column in (
        "id",
        "pathway_id",
        "version_number",
        "lifecycle_status",
        "supersedes_version_id",
        "official_source_id",
        "source_snapshot_id",
    ):
        op.create_index(
            f"ix_mobility_pathway_versions_{column}",
            "mobility_pathway_versions",
            [column],
            unique=False,
        )


def downgrade() -> None:
    op.drop_table("mobility_pathway_versions")
    op.drop_table("mobility_pathways")
