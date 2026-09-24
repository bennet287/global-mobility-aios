"""Record controlled AgentRun provider attempts independently of output success.

Revision ID: 0085_agent_run_provider_attempts
Revises: 0084_organization_agent_lifecycle
"""

from alembic import op
import sqlalchemy as sa


revision = "0085_agent_run_provider_attempts"
down_revision = "0084_organization_agent_lifecycle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_run_provider_attempts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("agent_run_id", sa.Uuid(), nullable=False),
        sa.Column("attempt_no", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("requested_model", sa.String(), nullable=True),
        sa.Column("model", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=True),
        sa.Column("estimated_cost_usd", sa.Numeric(18, 9), nullable=True),
        sa.Column("billed_cost_usd", sa.Numeric(18, 9), nullable=True),
        sa.Column("cost_basis", sa.String(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("settled_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("attempt_no > 0", name="ck_agent_run_provider_attempt_no"),
        sa.CheckConstraint("status IN ('started','observed','outcome_unknown')", name="ck_agent_run_provider_attempt_status"),
        sa.CheckConstraint("cost_basis IN ('unattributed','estimated','provider_billed')", name="ck_agent_run_provider_attempt_cost_basis"),
        sa.ForeignKeyConstraint(["agent_run_id"], ["agent_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("agent_run_id", "attempt_no", name="uq_agent_run_provider_attempt"),
    )
    op.create_index("ix_agent_run_provider_attempts_agent_run_id", "agent_run_provider_attempts", ["agent_run_id"])


def downgrade() -> None:
    op.drop_index("ix_agent_run_provider_attempts_agent_run_id", table_name="agent_run_provider_attempts")
    op.drop_table("agent_run_provider_attempts")
