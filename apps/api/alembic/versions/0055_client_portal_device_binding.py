"""Add device binding columns to client portal access grants.

Revision ID: 0055_client_portal_device_binding
Revises: 0054_business_advisory_strategic_memo
Create Date: 2026-08-01
"""

from alembic import op
import sqlalchemy as sa


revision = "0055_client_portal_device_binding"
down_revision = "0054_business_advisory_strategic_memo"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("client_portal_access_grants") as batch_op:
        batch_op.add_column(sa.Column("device_fingerprint", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("device_label", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("user_agent", sa.String(), nullable=True))
        batch_op.create_index("ix_client_portal_access_grants_device_fingerprint", ["device_fingerprint"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("client_portal_access_grants") as batch_op:
        batch_op.drop_index("ix_client_portal_access_grants_device_fingerprint")
        batch_op.drop_column("user_agent")
        batch_op.drop_column("device_label")
        batch_op.drop_column("device_fingerprint")
