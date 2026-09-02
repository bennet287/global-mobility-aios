"""Server-side document extraction and structured schemas.

Revision ID: 0015_document_intelligence_foundation
Revises: 0014_mobility_timeline_engine
Create Date: 2026-07-14
"""

from alembic import op
import sqlalchemy as sa


revision = "0015_document_intelligence_foundation"
down_revision = "0014_mobility_timeline_engine"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "document_schema_definitions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("schema_key", sa.String(), nullable=False),
        sa.Column("document_type", sa.String(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("lifecycle_status", sa.String(), nullable=False, server_default="draft"),
        sa.Column("supersedes_schema_id", sa.Uuid(), nullable=True),
        sa.Column("json_schema_json", sa.String(), nullable=False),
        sa.Column("extraction_rules_json", sa.String(), nullable=False),
        sa.Column("human_review_required", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("approved_by", sa.String(), nullable=True),
        sa.Column("review_notes", sa.String(), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.String(), nullable=False, server_default="system"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["supersedes_schema_id"], ["document_schema_definitions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("schema_key", "version_number", name="uq_document_schema_key_version"),
    )
    for column in ("id", "schema_key", "document_type", "version_number", "lifecycle_status", "supersedes_schema_id"):
        op.create_index(f"ix_document_schema_definitions_{column}", "document_schema_definitions", [column])

    op.create_table(
        "document_extraction_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("lead_id", sa.Uuid(), nullable=True),
        sa.Column("schema_definition_id", sa.Uuid(), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="queued"),
        sa.Column("engine", sa.String(), nullable=False, server_default="server_tesseract_pypdf_v1"),
        sa.Column("language", sa.String(), nullable=False, server_default="eng"),
        sa.Column("task_id", sa.String(), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("input_file_hash", sa.String(), nullable=True),
        sa.Column("extracted_text", sa.String(), nullable=True),
        sa.Column("structured_data_json", sa.String(), nullable=True),
        sa.Column("field_confidence_json", sa.String(), nullable=True),
        sa.Column("warnings_json", sa.String(), nullable=True),
        sa.Column("error_code", sa.String(), nullable=True),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("requested_by", sa.String(), nullable=False, server_default="system"),
        sa.Column("reviewed_by", sa.String(), nullable=True),
        sa.Column("review_notes", sa.String(), nullable=True),
        sa.Column("queued_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"]),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.ForeignKeyConstraint(["schema_definition_id"], ["document_schema_definitions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "id", "document_id", "lead_id", "schema_definition_id", "status", "engine", "task_id",
        "error_code", "queued_at",
    ):
        op.create_index(f"ix_document_extraction_jobs_{column}", "document_extraction_jobs", [column])


def downgrade() -> None:
    op.drop_table("document_extraction_jobs")
    op.drop_table("document_schema_definitions")
