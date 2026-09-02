"""Versioned global immigration-jurisdiction registry.

Revision ID: 0017_global_jurisdiction_registry
Revises: 0016_document_consistency_assessments
Create Date: 2026-07-14
"""

from alembic import op
import sqlalchemy as sa


revision = "0017_global_jurisdiction_registry"
down_revision = "0016_document_consistency_assessments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "jurisdiction_registry_releases",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.String(), nullable=False),
        sa.Column("source_name", sa.String(), nullable=False),
        sa.Column("source_url", sa.String(), nullable=False),
        sa.Column("source_sha256", sa.String(), nullable=False),
        sa.Column("source_retrieved_at", sa.DateTime(), nullable=False),
        sa.Column("expected_entries", sa.Integer(), nullable=False),
        sa.Column("imported_entries", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("released_by", sa.String(), nullable=False),
        sa.Column("released_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_sha256"),
        sa.UniqueConstraint("version"),
    )
    for column in ("id", "version", "source_sha256", "status", "released_at"):
        op.create_index(
            f"ix_jurisdiction_registry_releases_{column}",
            "jurisdiction_registry_releases",
            [column],
        )

    op.create_table(
        "jurisdiction_registry_entries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("registry_release_id", sa.Uuid(), nullable=False),
        sa.Column("jurisdiction_id", sa.Uuid(), nullable=False),
        sa.Column("alpha2_code", sa.String(), nullable=False),
        sa.Column("alpha3_code", sa.String(), nullable=False),
        sa.Column("m49_code", sa.String(), nullable=False),
        sa.Column("canonical_name", sa.String(), nullable=False),
        sa.Column("jurisdiction_type", sa.String(), nullable=False),
        sa.Column("membership_status", sa.String(), nullable=False),
        sa.Column("parent_code", sa.String(), nullable=True),
        sa.Column("region", sa.String(), nullable=True),
        sa.Column("subregion", sa.String(), nullable=True),
        sa.Column("immigration_rule_status", sa.String(), nullable=False),
        sa.Column("coverage_required", sa.Boolean(), nullable=False),
        sa.Column("payload_sha256", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["jurisdiction_id"], ["jurisdictions.id"]),
        sa.ForeignKeyConstraint(["registry_release_id"], ["jurisdiction_registry_releases.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("registry_release_id", "alpha2_code", name="uq_registry_release_alpha2"),
    )
    for column in (
        "id",
        "registry_release_id",
        "jurisdiction_id",
        "alpha2_code",
        "alpha3_code",
        "m49_code",
        "canonical_name",
        "jurisdiction_type",
        "membership_status",
        "parent_code",
        "region",
        "subregion",
        "immigration_rule_status",
        "coverage_required",
        "payload_sha256",
    ):
        op.create_index(
            f"ix_jurisdiction_registry_entries_{column}",
            "jurisdiction_registry_entries",
            [column],
        )


def downgrade() -> None:
    op.drop_table("jurisdiction_registry_entries")
    op.drop_table("jurisdiction_registry_releases")
