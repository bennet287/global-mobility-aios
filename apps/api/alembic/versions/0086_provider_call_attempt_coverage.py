"""Extend the existing controlled-AgentRun ledger to other paid-call contexts.

Revision ID: 0086_provider_call_attempt_coverage
Revises: 0085_agent_run_provider_attempts
"""

from alembic import op
import sqlalchemy as sa


revision = "0086_provider_call_attempt_coverage"
down_revision = "0085_agent_run_provider_attempts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.rename_table("agent_run_provider_attempts", "provider_call_attempts")
    op.drop_index("ix_agent_run_provider_attempts_agent_run_id", table_name="provider_call_attempts")
    with op.batch_alter_table("provider_call_attempts", reflect_kwargs={"resolve_fks": False}) as batch:
        batch.add_column(sa.Column("operation_key", sa.String(), nullable=True))
        batch.add_column(sa.Column("context_kind", sa.String(), nullable=True))
        batch.add_column(sa.Column("context_id", sa.String(), nullable=True))
        batch.alter_column("agent_run_id", existing_type=sa.Uuid(), nullable=True)
        batch.create_check_constraint(
            "ck_provider_call_attempt_identity",
            "(agent_run_id IS NOT NULL AND operation_key IS NULL) OR "
            "(agent_run_id IS NULL AND operation_key IS NOT NULL)",
        )
    op.create_index("ix_provider_call_attempts_agent_run_id", "provider_call_attempts", ["agent_run_id"])
    op.create_index("ix_provider_call_attempts_operation_key", "provider_call_attempts", ["operation_key"], unique=True)


def downgrade() -> None:
    # A downgrade must not silently erase provider-call accounting outside AgentRuns.
    connection = op.get_bind()
    external_count = connection.execute(
        sa.text("SELECT COUNT(*) FROM provider_call_attempts WHERE agent_run_id IS NULL")
    ).scalar_one()
    if external_count:
        raise RuntimeError("Cannot downgrade while non-AgentRun paid-call evidence exists")
    op.drop_index("ix_provider_call_attempts_operation_key", table_name="provider_call_attempts")
    op.drop_index("ix_provider_call_attempts_agent_run_id", table_name="provider_call_attempts")
    with op.batch_alter_table("provider_call_attempts", reflect_kwargs={"resolve_fks": False}) as batch:
        batch.drop_constraint("ck_provider_call_attempt_identity", type_="check")
        batch.alter_column("agent_run_id", existing_type=sa.Uuid(), nullable=False)
        batch.drop_column("context_id")
        batch.drop_column("context_kind")
        batch.drop_column("operation_key")
    op.rename_table("provider_call_attempts", "agent_run_provider_attempts")
    op.create_index(
        "ix_agent_run_provider_attempts_agent_run_id",
        "agent_run_provider_attempts",
        ["agent_run_id"],
    )
