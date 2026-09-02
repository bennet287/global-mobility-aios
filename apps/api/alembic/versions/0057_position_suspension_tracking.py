"""Add position suspension tracking.

Revision ID: 0057_position_suspension_tracking
Revises: 0056_ai_organization_governance
Create Date: 2026-08-02
"""

from alembic import op
import sqlalchemy as sa


revision = "0057_position_suspension_tracking"
down_revision = "0056_ai_organization_governance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("organization_positions", sa.Column("suspended_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("organization_positions", sa.Column("suspended_by", sa.String(), nullable=True))
    op.add_column("organization_positions", sa.Column("suspended_reason", sa.String(), nullable=True))
    op.create_index("ix_org_positions_suspended_at", "organization_positions", ["suspended_at"])
    op.create_index("ix_org_positions_suspended_by", "organization_positions", ["suspended_by"])


def downgrade() -> None:
    op.drop_index("ix_org_positions_suspended_by", table_name="organization_positions")
    op.drop_index("ix_org_positions_suspended_at", table_name="organization_positions")
    op.drop_column("organization_positions", "suspended_reason")
    op.drop_column("organization_positions", "suspended_by")
    op.drop_column("organization_positions", "suspended_at")
