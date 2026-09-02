"""Add bounded organization execution controls.

Revision ID: 0060_org_execution_controls
Revises: 0059_org_action_outputs
Create Date: 2026-08-03
"""

from alembic import op
import sqlalchemy as sa


revision = "0060_org_execution_controls"
down_revision = "0059_org_action_outputs"
branch_labels = None
depends_on = None


def _uuid() -> sa.Uuid:
    return sa.Uuid()


def upgrade() -> None:
    with op.batch_alter_table("organizational_work_items") as batch_op:
        batch_op.add_column(sa.Column("execution_attempts", sa.Integer(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("max_execution_attempts", sa.Integer(), nullable=False, server_default="3"))
        batch_op.add_column(sa.Column("execution_token", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("execution_started_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("last_error", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("cancel_requested_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("cancelled_by", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("cancellation_reason", sa.String(), nullable=True))
        for column in (
            "execution_token",
            "execution_started_at",
            "next_retry_at",
            "cancel_requested_at",
            "cancelled_at",
            "cancelled_by",
        ):
            batch_op.create_index(f"ix_org_work_{column}", [column])

    op.create_table(
        "organization_execution_attempts",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("attempt_key", sa.String(), nullable=False),
        sa.Column("work_item_id", _uuid(), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("execution_token", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("actor", sa.String(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["work_item_id"], ["organizational_work_items.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("attempt_key", name="uq_org_execution_attempt_key"),
        sa.UniqueConstraint("execution_token", name="uq_org_execution_token"),
    )
    for column in ("work_item_id", "status", "actor", "started_at", "completed_at"):
        op.create_index(f"ix_org_execution_attempt_{column}", "organization_execution_attempts", [column])


def downgrade() -> None:
    op.drop_table("organization_execution_attempts")
    with op.batch_alter_table("organizational_work_items") as batch_op:
        for column in (
            "cancelled_by",
            "cancelled_at",
            "cancel_requested_at",
            "next_retry_at",
            "execution_started_at",
            "execution_token",
        ):
            batch_op.drop_index(f"ix_org_work_{column}")
        for column in (
            "cancellation_reason",
            "cancelled_by",
            "cancelled_at",
            "cancel_requested_at",
            "last_error",
            "next_retry_at",
            "execution_started_at",
            "execution_token",
            "max_execution_attempts",
            "execution_attempts",
        ):
            batch_op.drop_column(column)
