"""Add deadline and emergency escalation tracking.

Revision ID: 0058_deadline_emergency_escalation
Revises: 0057_position_suspension_tracking
Create Date: 2026-08-02
"""

from alembic import op
import sqlalchemy as sa


revision = "0058_deadline_emergency_escalation"
down_revision = "0057_position_suspension_tracking"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("organizational_work_items", sa.Column("is_emergency", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("organizational_work_items", sa.Column("due_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("organizational_work_items", sa.Column("reminded_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("organizational_work_items", sa.Column("escalated_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_org_work_is_emergency", "organizational_work_items", ["is_emergency"])
    op.create_index("ix_org_work_due_at", "organizational_work_items", ["due_at"])
    op.create_index("ix_org_work_escalated_at", "organizational_work_items", ["escalated_at"])

    op.add_column("executive_decisions", sa.Column("due_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("executive_decisions", sa.Column("reminded_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_exec_decision_due_at", "executive_decisions", ["due_at"])

    op.add_column("risk_escalations", sa.Column("is_emergency", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_index("ix_risk_is_emergency", "risk_escalations", ["is_emergency"])


def downgrade() -> None:
    op.drop_index("ix_risk_is_emergency", table_name="risk_escalations")
    op.drop_column("risk_escalations", "is_emergency")

    op.drop_index("ix_exec_decision_due_at", table_name="executive_decisions")
    op.drop_column("executive_decisions", "reminded_at")
    op.drop_column("executive_decisions", "due_at")

    op.drop_index("ix_org_work_escalated_at", table_name="organizational_work_items")
    op.drop_index("ix_org_work_due_at", table_name="organizational_work_items")
    op.drop_index("ix_org_work_is_emergency", table_name="organizational_work_items")
    op.drop_column("organizational_work_items", "escalated_at")
    op.drop_column("organizational_work_items", "reminded_at")
    op.drop_column("organizational_work_items", "due_at")
    op.drop_column("organizational_work_items", "is_emergency")
