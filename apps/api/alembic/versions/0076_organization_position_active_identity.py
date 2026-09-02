"""Enforce durable OrganizationPosition identity uniqueness.

Revision ID: 0076_organization_position_active_identity
Revises: 0075_legacy_schema_reconciliation
Create Date: 2026-08-16

The original 0056 schema defined ``uq_org_position_version`` on
(position_key, version). Some preserved legacy SQLite databases lost that physical
constraint even though their Alembic revision later reported 0075. 0076 repairs that
legacy drift and adds the stronger invariant that at most one row for a position_key may
be active at a time.

The migration is intentionally data-preserving and fail-closed. A preserved database
with duplicate active identities must first be reconciled with
scripts/reconcile_duplicate_organization_positions.py. That helper keeps the earliest
canonical row active and archives semantically identical redundant rows as suspended
later versions; rows are never deleted.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0076_organization_position_active_identity"
down_revision = "0075_legacy_schema_reconciliation"
branch_labels = None
depends_on = None

ACTIVE_INDEX_NAME = "ux_organization_positions_active_position_key"
RECONCILED_VERSION_INDEX_NAME = "ux_organization_positions_position_key_version_reconciled"
LEGACY_VERSION_CONSTRAINT_NAME = "uq_org_position_version"


def _inspector() -> sa.Inspector:
    return sa.inspect(op.get_bind())


def _duplicates(where_clause: str = "") -> list[dict[str, object]]:
    where_sql = f"WHERE {where_clause}" if where_clause else ""
    rows = op.get_bind().execute(
        sa.text(
            f"""
            SELECT position_key, COUNT(*) AS row_count
            FROM organization_positions
            {where_sql}
            GROUP BY position_key
            HAVING COUNT(*) > 1
            ORDER BY position_key
            """
        )
    ).mappings().all()
    return [dict(row) for row in rows]


def _version_duplicates() -> list[dict[str, object]]:
    rows = op.get_bind().execute(
        sa.text(
            """
            SELECT position_key, version, COUNT(*) AS row_count
            FROM organization_positions
            GROUP BY position_key, version
            HAVING COUNT(*) > 1
            ORDER BY position_key, version
            """
        )
    ).mappings().all()
    return [dict(row) for row in rows]


def _has_position_version_uniqueness(inspector: sa.Inspector) -> bool:
    for constraint in inspector.get_unique_constraints("organization_positions"):
        if constraint.get("name") == LEGACY_VERSION_CONSTRAINT_NAME:
            return True
        if tuple(constraint.get("column_names") or ()) == ("position_key", "version"):
            return True
    for index in inspector.get_indexes("organization_positions"):
        if not index.get("unique"):
            continue
        if tuple(index.get("column_names") or ()) == ("position_key", "version"):
            return True
    return False


def upgrade() -> None:
    inspector = _inspector()
    if "organization_positions" not in inspector.get_table_names():
        raise RuntimeError(
            "0076 requires organization_positions to exist; the database is not at a compatible 0075 schema."
        )

    active_duplicates = _duplicates("status = 'active'")
    if active_duplicates:
        summary = ", ".join(
            f"{row['position_key']}={row['row_count']}" for row in active_duplicates
        )
        raise RuntimeError(
            "0076 refuses to hide duplicate active organization identities. "
            "Run scripts/reconcile_duplicate_organization_positions.py against the preserved database first. "
            f"Duplicates: {summary}"
        )

    version_duplicates = _version_duplicates()
    if version_duplicates:
        summary = ", ".join(
            f"{row['position_key']}@v{row['version']}={row['row_count']}"
            for row in version_duplicates
        )
        raise RuntimeError(
            "0076 cannot restore OrganizationPosition version uniqueness while duplicate "
            f"(position_key, version) identities remain: {summary}"
        )

    # Fresh databases already carry uq_org_position_version from 0056. Preserved
    # SQLite databases that lost the constraint get equivalent physical protection here.
    if not _has_position_version_uniqueness(inspector):
        op.create_index(
            RECONCILED_VERSION_INDEX_NAME,
            "organization_positions",
            ["position_key", "version"],
            unique=True,
        )
        inspector = _inspector()

    index_names = {
        index["name"]
        for index in inspector.get_indexes("organization_positions")
        if index.get("name")
    }
    if ACTIVE_INDEX_NAME not in index_names:
        op.create_index(
            ACTIVE_INDEX_NAME,
            "organization_positions",
            ["position_key"],
            unique=True,
            sqlite_where=sa.text("status = 'active'"),
            postgresql_where=sa.text("status = 'active'"),
        )


def downgrade() -> None:
    inspector = _inspector()
    if "organization_positions" not in inspector.get_table_names():
        return
    index_names = {
        index["name"]
        for index in inspector.get_indexes("organization_positions")
        if index.get("name")
    }
    if ACTIVE_INDEX_NAME in index_names:
        op.drop_index(ACTIVE_INDEX_NAME, table_name="organization_positions")
    if RECONCILED_VERSION_INDEX_NAME in index_names:
        op.drop_index(RECONCILED_VERSION_INDEX_NAME, table_name="organization_positions")
