"""Add recorded monetary allocation authority.

Revision ID: 0093_monetary_allocation
Revises: 0092_grc_standards_mapping
"""
from alembic import op
import sqlalchemy as sa

revision = "0093_monetary_allocation"
down_revision = "0092_grc_standards_mapping"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "monetary_allocations",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("authorized_usd", sa.Numeric(18, 2), nullable=False),
        sa.Column("authority_label", sa.String(), nullable=False),
        sa.Column("authorization_reference", sa.String(), nullable=False),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("supersedes_allocation_id", sa.Uuid(), nullable=True),
        sa.Column("recorded_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("authorized_usd > 0", name="ck_monetary_allocation_positive"),
        sa.CheckConstraint("status IN ('active','superseded','withdrawn')", name="ck_monetary_allocation_status"),
        sa.UniqueConstraint("supersedes_allocation_id", name="uq_monetary_allocation_supersedes"),
        sa.ForeignKeyConstraint(["supersedes_allocation_id"], ["monetary_allocations.id"], name="fk_monetary_allocation_supersedes"),
    )

def downgrade() -> None:
    connection = op.get_bind()
    if connection.execute(sa.text("SELECT COUNT(*) FROM monetary_allocations")).scalar_one():
        raise RuntimeError("Cannot discard governed monetary allocations")
    op.drop_table("monetary_allocations")
