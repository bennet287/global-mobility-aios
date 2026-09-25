"""Record durable request-local provider operation completion evidence.

Revision ID: 0090_request_local_operation_completion
Revises: 0089_provider_circuit_breaker
"""

from alembic import op
import sqlalchemy as sa


revision = "0090_request_local_operation_completion"
down_revision = "0089_provider_circuit_breaker"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("provider_call_attempts") as batch:
        batch.add_column(sa.Column("operation_finished_at", sa.DateTime(timezone=True), nullable=True))
        batch.create_check_constraint(
            "ck_provider_call_attempt_request_finish",
            "operation_finished_at IS NULL OR agent_run_id IS NULL",
        )


def downgrade() -> None:
    connection = op.get_bind()
    if connection.execute(sa.text(
        "SELECT COUNT(*) FROM provider_call_attempts WHERE operation_finished_at IS NOT NULL"
    )).scalar_one():
        raise RuntimeError("Cannot discard request-local execution-end evidence")
    with op.batch_alter_table("provider_call_attempts") as batch:
        batch.drop_constraint("ck_provider_call_attempt_request_finish", type_="check")
        batch.drop_column("operation_finished_at")
