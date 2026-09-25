"""Track provider-scoped circuit admission on the existing call allocation.

Revision ID: 0089_provider_circuit_breaker
Revises: 0088_provider_response_identity
"""

from alembic import op
import sqlalchemy as sa


revision = "0089_provider_circuit_breaker"
down_revision = "0088_provider_response_identity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("provider_call_allocations") as batch:
        batch.add_column(sa.Column("breaker_open", sa.Boolean(), nullable=False,
                                   server_default=sa.false()))
        batch.add_column(sa.Column("breaker_failures", sa.Integer(), nullable=False,
                                   server_default="0"))
        batch.add_column(sa.Column("breaker_opened_at", sa.DateTime(timezone=True), nullable=True))
        batch.create_check_constraint(
            "ck_provider_call_allocation_breaker_failures", "breaker_failures >= 0",
        )


def downgrade() -> None:
    connection = op.get_bind()
    if connection.execute(sa.text(
        "SELECT COUNT(*) FROM provider_call_allocations "
        "WHERE breaker_open OR breaker_failures > 0 OR breaker_opened_at IS NOT NULL"
    )).scalar_one():
        raise RuntimeError("Cannot discard active provider circuit evidence")
    with op.batch_alter_table("provider_call_allocations") as batch:
        batch.drop_constraint("ck_provider_call_allocation_breaker_failures", type_="check")
        batch.drop_column("breaker_opened_at")
        batch.drop_column("breaker_failures")
        batch.drop_column("breaker_open")
