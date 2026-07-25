"""Authority submission checklist.

Revision ID: 0051_authority_submission_checklist
Revises: 0050_external_agency_assignment
Create Date: 2026-07-24
"""

from alembic import op
import sqlalchemy as sa


revision = "0051_authority_submission_checklist"
down_revision = "0050_external_agency_assignment"
branch_labels = None
depends_on = None


def _indexes(table: str, columns: tuple[str, ...]) -> None:
    for column in columns:
        op.create_index(f"ix_{table}_{column}", table, [column])


def upgrade() -> None:
    op.create_table(
        "authority_checklist_templates",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("authority_name", sa.String(), nullable=False),
        sa.Column("country", sa.String(), nullable=True),
        sa.Column("item_key", sa.String(), nullable=False),
        sa.Column("item_label", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("is_required", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("updated_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    _indexes(
        "authority_checklist_templates",
        (
            "id",
            "authority_name",
            "country",
            "item_key",
            "category",
            "created_by",
            "updated_by",
            "created_at",
        ),
    )

    op.create_table(
        "application_authority_checklist_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("application_id", sa.Uuid(), nullable=False),
        sa.Column("template_item_id", sa.Uuid(), nullable=True),
        sa.Column("authority_name", sa.String(), nullable=False),
        sa.Column("item_key", sa.String(), nullable=False),
        sa.Column("item_label", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("is_required", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("updated_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"]),
        sa.ForeignKeyConstraint(
            ["template_item_id"], ["authority_checklist_templates.id"]
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    _indexes(
        "application_authority_checklist_items",
        (
            "id",
            "application_id",
            "template_item_id",
            "authority_name",
            "item_key",
            "category",
            "status",
            "created_by",
            "updated_by",
            "created_at",
        ),
    )


def downgrade() -> None:
    op.drop_table("application_authority_checklist_items")
    op.drop_table("authority_checklist_templates")
