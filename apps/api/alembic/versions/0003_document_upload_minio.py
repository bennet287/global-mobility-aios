"""Document upload and object storage metadata v3.5

Revision ID: 0003_document_upload_minio
Revises: 0002_official_source_truth_engine
Create Date: 2026-07-09
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_document_upload_minio"
down_revision = "0002_official_source_truth_engine"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("storage_provider", sa.String(), nullable=True))
    op.add_column("documents", sa.Column("file_hash", sa.String(), nullable=True))
    op.add_column("documents", sa.Column("mime_type", sa.String(), nullable=True))
    op.add_column("documents", sa.Column("file_size_bytes", sa.Integer(), nullable=True))
    op.add_column("documents", sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("documents", sa.Column("verified_by", sa.String(), nullable=True))
    op.add_column("documents", sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("documents", sa.Column("expiry_date", sa.DateTime(timezone=True), nullable=True))
    op.add_column("documents", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_documents_storage_provider", "documents", ["storage_provider"])
    op.create_index("ix_documents_file_hash", "documents", ["file_hash"])


def downgrade() -> None:
    op.drop_index("ix_documents_file_hash", table_name="documents")
    op.drop_index("ix_documents_storage_provider", table_name="documents")
    op.drop_column("documents", "updated_at")
    op.drop_column("documents", "expiry_date")
    op.drop_column("documents", "verified_at")
    op.drop_column("documents", "verified_by")
    op.drop_column("documents", "uploaded_at")
    op.drop_column("documents", "file_size_bytes")
    op.drop_column("documents", "mime_type")
    op.drop_column("documents", "file_hash")
    op.drop_column("documents", "storage_provider")
