"""Add evidence-grounded organizational action outputs.

Revision ID: 0059_org_action_outputs
Revises: 0058_deadline_emergency_escalation
Create Date: 2026-08-02
"""

from alembic import op
import sqlalchemy as sa


revision = "0059_org_action_outputs"
down_revision = "0058_deadline_emergency_escalation"
branch_labels = None
depends_on = None


def _uuid() -> sa.Uuid:
    return sa.Uuid()


def upgrade() -> None:
    op.create_table(
        "organizational_action_outputs",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("output_key", sa.String(), nullable=False),
        sa.Column("work_item_id", _uuid(), nullable=False),
        sa.Column("delegation_record_id", _uuid(), nullable=True),
        sa.Column("accountable_position_key", sa.String(), nullable=False),
        sa.Column("authority_basis", sa.String(), nullable=False),
        sa.Column("evidence_json", sa.String(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("confidence_basis", sa.String(), nullable=False),
        sa.Column("impact_json", sa.String(), nullable=False),
        sa.Column("rollback_posture", sa.String(), nullable=False),
        sa.Column("output_json", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["delegation_record_id"], ["delegation_records.id"]),
        sa.ForeignKeyConstraint(["work_item_id"], ["organizational_work_items.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("output_key", name="uq_organizational_action_output_key"),
    )
    for column in (
        "work_item_id",
        "delegation_record_id",
        "accountable_position_key",
        "status",
        "created_at",
    ):
        op.create_index(
            f"ix_organizational_action_output_{column}",
            "organizational_action_outputs",
            [column],
        )


def downgrade() -> None:
    op.drop_table("organizational_action_outputs")
