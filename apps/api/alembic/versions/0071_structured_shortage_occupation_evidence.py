"""Add deterministic structured shortage-occupation evidence.

Revision ID: 0071_structured_shortage_occupation_evidence
Revises: 0070_pathway_version_evidence_provenance
Create Date: 2026-08-10
"""

from alembic import op
import sqlalchemy as sa


revision = "0071_structured_shortage_occupation_evidence"
down_revision = "0070_pathway_version_evidence_provenance"
branch_labels = None
depends_on = None


_TABLE = "shortage_occupation_entries"
_UNIQUE_ORDINAL = "uq_shortage_occupation_snapshot_scope_ordinal"
_UNIQUE_HASH = "uq_shortage_occupation_entry_sha256"


def upgrade() -> None:
    op.create_table(
        _TABLE,
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("jurisdiction_id", sa.Uuid(), nullable=False),
        sa.Column("official_source_id", sa.Uuid(), nullable=False),
        sa.Column("source_snapshot_id", sa.Uuid(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("scope", sa.String(), nullable=False),
        sa.Column("source_ordinal", sa.Integer(), nullable=False),
        sa.Column("occupation_group", sa.String(), nullable=False),
        sa.Column("normalized_occupation_group", sa.String(), nullable=False),
        sa.Column("occupation_aliases_json", sa.String(), nullable=False, server_default="[]"),
        sa.Column("province_codes_json", sa.String(), nullable=False, server_default="[]"),
        sa.Column("province_names_json", sa.String(), nullable=False, server_default="[]"),
        sa.Column("extraction_version", sa.String(), nullable=False),
        sa.Column("entry_sha256", sa.String(), nullable=False),
        sa.Column("metadata_json", sa.String(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["jurisdiction_id"], ["jurisdictions.id"]),
        sa.ForeignKeyConstraint(["official_source_id"], ["official_sources.id"]),
        sa.ForeignKeyConstraint(["source_snapshot_id"], ["source_snapshots.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_snapshot_id",
            "year",
            "scope",
            "source_ordinal",
            name=_UNIQUE_ORDINAL,
        ),
        sa.UniqueConstraint("entry_sha256", name=_UNIQUE_HASH),
        sa.CheckConstraint(
            "scope IN ('national', 'regional')",
            name="ck_shortage_occupation_scope",
        ),
        sa.CheckConstraint(
            "year BETWEEN 2000 AND 2200",
            name="ck_shortage_occupation_year",
        ),
        sa.CheckConstraint(
            "source_ordinal > 0",
            name="ck_shortage_occupation_source_ordinal",
        ),
    )

    for column in (
        "jurisdiction_id",
        "official_source_id",
        "source_snapshot_id",
        "year",
        "scope",
        "source_ordinal",
        "normalized_occupation_group",
        "entry_sha256",
    ):
        op.create_index(
            f"ix_{_TABLE}_{column}",
            _TABLE,
            [column],
            unique=False,
        )


def downgrade() -> None:
    op.drop_table(_TABLE)
