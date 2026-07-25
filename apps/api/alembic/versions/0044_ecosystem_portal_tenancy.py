"""Employer and partner portal tenant isolation.

Revision ID: 0044_ecosystem_portal_tenancy
Revises: 0043_client_portal_foundation
Create Date: 2026-07-23
"""

from alembic import op
import sqlalchemy as sa


revision = "0044_ecosystem_portal_tenancy"
down_revision = "0043_client_portal_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ecosystem_portal_access_grants",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(), nullable=False),
        sa.Column("corporate_account_id", sa.Uuid(), nullable=False),
        sa.Column("audience_type", sa.String(), nullable=False),
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
        sa.ForeignKeyConstraint(["corporate_account_id"], ["corporate_accounts.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    for column in (
        "id",
        "token_hash",
        "corporate_account_id",
        "audience_type",
        "status",
        "expires_at",
        "created_by",
        "last_accessed_at",
        "revoked_by",
        "revoked_at",
        "created_at",
    ):
        op.create_index(
            f"ix_ecosystem_portal_access_grants_{column}",
            "ecosystem_portal_access_grants",
            [column],
        )


def downgrade() -> None:
    op.drop_table("ecosystem_portal_access_grants")
