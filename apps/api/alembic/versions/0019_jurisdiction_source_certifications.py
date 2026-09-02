"""Reviewed primary authority and source certifications.

Revision ID: 0019_jurisdiction_source_certifications
Revises: 0018_jurisdiction_immigration_assessments
Create Date: 2026-07-14
"""

from alembic import op
import sqlalchemy as sa


revision = "0019_jurisdiction_source_certifications"
down_revision = "0018_jurisdiction_immigration_assessments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "jurisdiction_source_certifications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("jurisdiction_id", sa.Uuid(), nullable=False),
        sa.Column("registry_entry_id", sa.Uuid(), nullable=False),
        sa.Column("regulatory_authority_id", sa.Uuid(), nullable=False),
        sa.Column("official_source_id", sa.Uuid(), nullable=False),
        sa.Column("certification_version", sa.Integer(), nullable=False),
        sa.Column("certification_scope", sa.String(), nullable=False),
        sa.Column("coverage_domains_json", sa.String(), nullable=False),
        sa.Column("evidence_notes", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("proposed_by", sa.String(), nullable=False),
        sa.Column("reviewed_by", sa.String(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("review_notes", sa.String(), nullable=True),
        sa.Column("supersedes_certification_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["jurisdiction_id"], ["jurisdictions.id"]),
        sa.ForeignKeyConstraint(["registry_entry_id"], ["jurisdiction_registry_entries.id"]),
        sa.ForeignKeyConstraint(["regulatory_authority_id"], ["regulatory_authorities.id"]),
        sa.ForeignKeyConstraint(["official_source_id"], ["official_sources.id"]),
        sa.ForeignKeyConstraint(
            ["supersedes_certification_id"],
            ["jurisdiction_source_certifications.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "jurisdiction_id",
            "certification_scope",
            "certification_version",
            name="uq_jsc_scope_version",
        ),
    )
    for column in (
        "id",
        "jurisdiction_id",
        "registry_entry_id",
        "regulatory_authority_id",
        "official_source_id",
        "certification_version",
        "certification_scope",
        "status",
        "reviewed_by",
        "reviewed_at",
        "supersedes_certification_id",
        "created_at",
    ):
        op.create_index(f"ix_jsc_{column}", "jurisdiction_source_certifications", [column])


def downgrade() -> None:
    op.drop_table("jurisdiction_source_certifications")
