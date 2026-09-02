"""Audited corporate relocation task orchestration.

Revision ID: 0035_relocation_tasks
Revises: 0034_corp_relationships
Create Date: 2026-07-23
"""
from alembic import op
import sqlalchemy as sa


revision = "0035_relocation_tasks"
down_revision = "0034_corp_relationships"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "corporate_relocation_tasks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("corporate_mobility_case_id", sa.Uuid(), nullable=False),
        sa.Column("depends_on_task_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("owner_role", sa.String(), nullable=False),
        sa.Column("due_at", sa.DateTime(), nullable=True),
        sa.Column("requires_human_approval", sa.Boolean(), nullable=False),
        sa.Column("approval_status", sa.String(), nullable=False),
        sa.Column("work_notes", sa.String(), nullable=True),
        sa.Column("submitted_by", sa.String(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(), nullable=True),
        sa.Column("completed_by", sa.String(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("updated_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["corporate_mobility_case_id"], ["corporate_mobility_cases.id"]),
        sa.ForeignKeyConstraint(["depends_on_task_id"], ["corporate_relocation_tasks.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "id", "corporate_mobility_case_id", "depends_on_task_id", "category", "status",
        "owner_role", "due_at", "approval_status", "submitted_by", "submitted_at",
        "completed_by", "completed_at", "created_by", "updated_by", "created_at",
    ):
        op.create_index(f"ix_corporate_relocation_tasks_{column}", "corporate_relocation_tasks", [column])

    op.create_table(
        "corporate_relocation_task_decisions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("corporate_relocation_task_id", sa.Uuid(), nullable=False),
        sa.Column("decision", sa.String(), nullable=False),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column("reviewer", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["corporate_relocation_task_id"], ["corporate_relocation_tasks.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_corp_task_decisions_task_id", "corporate_relocation_task_decisions", ["corporate_relocation_task_id"])
    for column in ("id", "decision", "reviewer", "created_at"):
        op.create_index(
            f"ix_corporate_relocation_task_decisions_{column}",
            "corporate_relocation_task_decisions",
            [column],
        )


def downgrade() -> None:
    op.drop_table("corporate_relocation_task_decisions")
    op.drop_table("corporate_relocation_tasks")
