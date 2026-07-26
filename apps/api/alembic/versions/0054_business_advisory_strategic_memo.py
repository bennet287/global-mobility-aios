"""Add strategic_memo to business mobility advisory assessments.

Revision ID: 0054_business_advisory_strategic_memo
Revises: 0053_automation_delivery_reconciliation
Create Date: 2026-07-25
"""

from alembic import op
import sqlalchemy as sa


revision = "0054_business_advisory_strategic_memo"
down_revision = "0053_automation_delivery_reconciliation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("business_mobility_advisory_assessments") as batch_op:
        batch_op.add_column(sa.Column("strategic_memo", sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("business_mobility_advisory_assessments") as batch_op:
        batch_op.drop_column("strategic_memo")
