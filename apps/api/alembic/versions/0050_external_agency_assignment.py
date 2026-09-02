"""External agency and assignment tracking.

Revision ID: 0050_external_agency_assignment
Revises: 0049_agency_submission_tracking
Create Date: 2026-07-24
"""

from alembic import op
import sqlalchemy as sa


revision = "0050_external_agency_assignment"
down_revision = "0049_agency_submission_tracking"
branch_labels = None
depends_on = None


def _indexes(table: str, columns: tuple[str, ...]) -> None:
    for column in columns:
        op.create_index(f"ix_{table}_{column}", table, [column])


def upgrade() -> None:
    op.create_table(
        "external_agencies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("country", sa.String(), nullable=True),
        sa.Column("city", sa.String(), nullable=True),
        sa.Column("contact_email", sa.String(), nullable=True),
        sa.Column("contact_phone", sa.String(), nullable=True),
        sa.Column("website", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("updated_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    _indexes(
        "external_agencies",
        (
            "id",
            "name",
            "country",
            "status",
            "created_by",
            "updated_by",
            "created_at",
        ),
    )

    op.create_table(
        "external_agency_assignments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("application_id", sa.Uuid(), nullable=False),
        sa.Column("external_agency_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("agency_reference_number", sa.String(), nullable=True),
        sa.Column("handoff_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("updated_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"]),
        sa.ForeignKeyConstraint(["external_agency_id"], ["external_agencies.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    _indexes(
        "external_agency_assignments",
        (
            "id",
            "application_id",
            "external_agency_id",
            "status",
            "created_by",
            "updated_by",
            "created_at",
        ),
    )


def downgrade() -> None:
    op.drop_table("external_agency_assignments")
    op.drop_table("external_agencies")
