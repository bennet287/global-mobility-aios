"""Agency submission tracking.

Revision ID: 0049_agency_submission_tracking
Revises: 0048_authority_appointment_tracking
Create Date: 2026-07-24
"""

from alembic import op
import sqlalchemy as sa


revision = "0049_agency_submission_tracking"
down_revision = "0048_authority_appointment_tracking"
branch_labels = None
depends_on = None


def _indexes(table: str, columns: tuple[str, ...]) -> None:
    for column in columns:
        op.create_index(f"ix_{table}_{column}", table, [column])


def upgrade() -> None:
    op.create_table(
        "agency_submissions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("application_id", sa.Uuid(), nullable=False),
        sa.Column("authority_name", sa.String(), nullable=False),
        sa.Column("submission_channel", sa.String(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(), nullable=False),
        sa.Column("reference_number", sa.String(), nullable=True),
        sa.Column("tracking_url", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("updated_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _indexes(
        "agency_submissions",
        (
            "id",
            "application_id",
            "submission_channel",
            "submitted_at",
            "status",
            "created_by",
            "updated_by",
            "created_at",
        ),
    )


def downgrade() -> None:
    op.drop_table("agency_submissions")
