"""Fence CEO coordination leases with durable claim tokens.

Revision ID: 0062_ceo_coordination_fencing
Revises: 0061_exec_council_consultations
Create Date: 2026-08-03
"""

from alembic import op
import sqlalchemy as sa


revision = "0062_ceo_coordination_fencing"
down_revision = "0061_exec_council_consultations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("executive_decisions") as batch_op:
        batch_op.add_column(sa.Column("coordination_token", sa.String(), nullable=True))
        batch_op.add_column(
            sa.Column("coordination_claimed_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.create_index(
            "ix_executive_decisions_coordination_token",
            ["coordination_token"],
            unique=False,
        )
        batch_op.create_index(
            "ix_executive_decisions_coordination_claimed_at",
            ["coordination_claimed_at"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("executive_decisions") as batch_op:
        batch_op.drop_index("ix_executive_decisions_coordination_claimed_at")
        batch_op.drop_index("ix_executive_decisions_coordination_token")
        batch_op.drop_column("coordination_claimed_at")
        batch_op.drop_column("coordination_token")
