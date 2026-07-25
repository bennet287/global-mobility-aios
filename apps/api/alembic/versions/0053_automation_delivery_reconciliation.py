"""Automation delivery reconciliation columns.

Revision ID: 0053_automation_delivery_reconciliation
Revises: 0052_external_agency_assignment_sla
Create Date: 2026-07-25
"""

from alembic import op
import sqlalchemy as sa


revision = "0053_automation_delivery_reconciliation"
down_revision = "0052_external_agency_assignment_sla"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("automation_deliveries") as batch_op:
        batch_op.add_column(sa.Column("reconciled", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column("reconciled_at", sa.DateTime(), nullable=True))
        batch_op.create_index("ix_automation_deliveries_reconciled", ["reconciled"])
        batch_op.create_index("ix_automation_deliveries_reconciled_at", ["reconciled_at"])


def downgrade() -> None:
    with op.batch_alter_table("automation_deliveries") as batch_op:
        batch_op.drop_index("ix_automation_deliveries_reconciled_at")
        batch_op.drop_index("ix_automation_deliveries_reconciled")
        batch_op.drop_column("reconciled_at")
        batch_op.drop_column("reconciled")
