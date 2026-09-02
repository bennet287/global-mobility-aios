"""Client portal access foundation.

Revision ID: 0043_client_portal_foundation
Revises: 0042_tax_residency_treaty
Create Date: 2026-07-23
"""

from alembic import op
import sqlalchemy as sa


revision = "0043_client_portal_foundation"
down_revision = "0042_tax_residency_treaty"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "client_portal_access_grants",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(), nullable=False),
        sa.Column("lead_id", sa.Uuid(), nullable=False),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("access_count", sa.Integer(), nullable=False),
        sa.Column("last_accessed_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_by", sa.String(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("revocation_reason", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    for column in (
        "id",
        "token_hash",
        "lead_id",
        "status",
        "expires_at",
        "created_by",
        "last_accessed_at",
        "revoked_by",
        "revoked_at",
        "created_at",
    ):
        op.create_index(
            f"ix_client_portal_access_grants_{column}",
            "client_portal_access_grants",
            [column],
        )


def downgrade() -> None:
    op.drop_table("client_portal_access_grants")
