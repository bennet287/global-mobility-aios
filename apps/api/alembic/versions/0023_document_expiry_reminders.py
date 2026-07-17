"""Deduplicated document expiry reminder tasks.

Revision ID: 0023_document_expiry_reminders
Revises: 0022_pathway_regulatory_impacts
Create Date: 2026-07-14
"""

from alembic import op
import sqlalchemy as sa


revision = "0023_document_expiry_reminders"
down_revision = "0022_pathway_regulatory_impacts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "document_expiry_reminder_tasks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("reminder_key", sa.String(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("lead_id", sa.Uuid(), nullable=True),
        sa.Column("document_type", sa.String(), nullable=False),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("expiry_date", sa.DateTime(), nullable=False),
        sa.Column("reminder_type", sa.String(), nullable=False),
        sa.Column("threshold_days", sa.Integer(), nullable=False),
        sa.Column("due_at", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("priority", sa.String(), nullable=False, server_default="normal"),
        sa.Column("source", sa.String(), nullable=False, server_default="document_record_expiry_date"),
        sa.Column("human_review_required", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("external_delivery_status", sa.String(), nullable=False, server_default="not_sent"),
        sa.Column("generated_by", sa.String(), nullable=False, server_default="document-expiry-monitor"),
        sa.Column("reviewed_by", sa.String(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("review_notes", sa.String(), nullable=True),
        sa.Column("superseded_by_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"]),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.ForeignKeyConstraint(["superseded_by_id"], ["document_expiry_reminder_tasks.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "id",
        "document_id",
        "lead_id",
        "document_type",
        "expiry_date",
        "reminder_type",
        "due_at",
        "status",
        "priority",
        "source",
        "external_delivery_status",
        "reviewed_by",
        "reviewed_at",
        "superseded_by_id",
        "created_at",
    ):
        op.create_index(
            f"ix_document_expiry_reminder_tasks_{column}",
            "document_expiry_reminder_tasks",
            [column],
        )
    op.create_index(
        "ix_document_expiry_reminder_tasks_reminder_key",
        "document_expiry_reminder_tasks",
        ["reminder_key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_table("document_expiry_reminder_tasks")
