"""Preserve the optional provider completion identity for later invoice matching.

Revision ID: 0088_provider_response_identity
Revises: 0087_provider_call_capacity
"""

from alembic import op
import sqlalchemy as sa


revision = "0088_provider_response_identity"
down_revision = "0087_provider_call_capacity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("provider_call_attempts", reflect_kwargs={"resolve_fks": False}) as batch:
        batch.add_column(sa.Column("provider_response_id", sa.String(), nullable=True))
    op.create_index(
        "ix_provider_call_attempts_provider_response_id",
        "provider_call_attempts", ["provider_response_id"],
    )


def downgrade() -> None:
    connection = op.get_bind()
    if connection.execute(sa.text(
        "SELECT COUNT(*) FROM provider_call_attempts WHERE provider_response_id IS NOT NULL"
    )).scalar_one():
        raise RuntimeError("Cannot discard observed provider response identities")
    op.drop_index("ix_provider_call_attempts_provider_response_id", table_name="provider_call_attempts")
    with op.batch_alter_table("provider_call_attempts", reflect_kwargs={"resolve_fks": False}) as batch:
        batch.drop_column("provider_response_id")
