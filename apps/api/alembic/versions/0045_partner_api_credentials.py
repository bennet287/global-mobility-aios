"""Versioned partner API credentials.

Revision ID: 0045_partner_api_credentials
Revises: 0044_ecosystem_portal_tenancy
Create Date: 2026-07-23
"""

from alembic import op
import sqlalchemy as sa


revision = "0045_partner_api_credentials"
down_revision = "0044_ecosystem_portal_tenancy"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "partner_api_credentials",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("key_hash", sa.String(), nullable=False),
        sa.Column("key_prefix", sa.String(), nullable=False),
        sa.Column("corporate_account_id", sa.Uuid(), nullable=False),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("scopes", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("access_count", sa.Integer(), nullable=False),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_by", sa.String(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("revocation_reason", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["corporate_account_id"], ["corporate_accounts.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key_hash"),
    )
    for column in (
        "id",
        "key_hash",
        "key_prefix",
        "corporate_account_id",
        "status",
        "expires_at",
        "created_by",
        "last_used_at",
        "revoked_by",
        "revoked_at",
        "created_at",
    ):
        op.create_index(
            f"ix_partner_api_credentials_{column}",
            "partner_api_credentials",
            [column],
        )


def downgrade() -> None:
    op.drop_table("partner_api_credentials")
