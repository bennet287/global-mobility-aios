"""Signed, expiring document access grants.

Revision ID: 0026_document_access_grants
Revises: 0025_document_fraud_risk_assessments
Create Date: 2026-07-14
"""

from alembic import op
import sqlalchemy as sa


revision = "0026_document_access_grants"
down_revision = "0025_document_fraud_risk_assessments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "document_access_grants",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("lead_id", sa.Uuid(), nullable=False),
        sa.Column("issued_to", sa.String(), nullable=False),
        sa.Column("issued_role", sa.String(), nullable=False),
        sa.Column("purpose", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("max_uses", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("use_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("document_file_hash", sa.String(), nullable=False),
        sa.Column("document_file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("storage_provider", sa.String(), nullable=False),
        sa.Column("storage_key_hash", sa.String(), nullable=False),
        sa.Column("mime_type", sa.String(), nullable=True),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("last_accessed_by", sa.String(), nullable=True),
        sa.Column("last_accessed_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_by", sa.String(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("revocation_reason", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"]),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "id",
        "document_id",
        "lead_id",
        "issued_to",
        "issued_role",
        "purpose",
        "status",
        "expires_at",
        "storage_provider",
        "created_by",
        "last_accessed_by",
        "last_accessed_at",
        "revoked_by",
        "revoked_at",
        "created_at",
    ):
        op.create_index(
            f"ix_document_access_grants_{column}",
            "document_access_grants",
            [column],
        )
    op.create_index(
        "ix_document_access_grants_token_hash",
        "document_access_grants",
        ["token_hash"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_table("document_access_grants")
