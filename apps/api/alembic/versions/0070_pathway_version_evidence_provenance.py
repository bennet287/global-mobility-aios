"""Normalize multi-source pathway-version evidence provenance.

Revision ID: 0070_pathway_version_evidence_provenance
Revises: 0069_source_certification_multiplicity
Create Date: 2026-08-10
"""

from alembic import op
import sqlalchemy as sa


revision = "0070_pathway_version_evidence_provenance"
down_revision = "0069_source_certification_multiplicity"
branch_labels = None
depends_on = None


_TABLE = "mobility_pathway_version_evidence"
_UNIQUE = "uq_pathway_version_evidence_identity"


def upgrade() -> None:
    op.create_table(
        _TABLE,
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("pathway_version_id", sa.Uuid(), nullable=False),
        sa.Column("evidence_role", sa.String(), nullable=False),
        sa.Column("official_source_id", sa.Uuid(), nullable=False),
        sa.Column("source_snapshot_id", sa.Uuid(), nullable=False),
        sa.Column(
            "required_for_publication",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column("metadata_json", sa.String(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["pathway_version_id"],
            ["mobility_pathway_versions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["official_source_id"], ["official_sources.id"]),
        sa.ForeignKeyConstraint(["source_snapshot_id"], ["source_snapshots.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "pathway_version_id",
            "evidence_role",
            "official_source_id",
            "source_snapshot_id",
            name=_UNIQUE,
        ),
    )
    for column in (
        "pathway_version_id",
        "evidence_role",
        "official_source_id",
        "source_snapshot_id",
        "required_for_publication",
    ):
        op.create_index(
            f"ix_{_TABLE}_{column}",
            _TABLE,
            [column],
            unique=False,
        )

    # Historical pathway versions already pin one source/snapshot pair.  Reuse
    # the version UUID as the child-row UUID; UUID uniqueness is table-local,
    # portable across PostgreSQL/SQLite, and avoids database-specific UUID
    # generator functions during migration.
    op.execute(
        sa.text(
            f"""
            INSERT INTO {_TABLE} (
                id,
                pathway_version_id,
                evidence_role,
                official_source_id,
                source_snapshot_id,
                required_for_publication,
                metadata_json,
                created_at
            )
            SELECT
                id,
                id,
                'core_route',
                official_source_id,
                source_snapshot_id,
                :required,
                '{{}}',
                created_at
            FROM mobility_pathway_versions
            WHERE official_source_id IS NOT NULL
              AND source_snapshot_id IS NOT NULL
            """
        ).bindparams(required=True)
    )


def downgrade() -> None:
    op.drop_table(_TABLE)
