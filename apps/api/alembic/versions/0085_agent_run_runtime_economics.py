"""Add AgentRun runtime budget and cost evidence.

Revision ID: 0085_agent_run_runtime_economics
Revises: 0084_organization_agent_lifecycle
Create Date: 2026-09-24
"""

from alembic import op
import sqlalchemy as sa


revision = "0085_agent_run_runtime_economics"
down_revision = "0084_organization_agent_lifecycle"
branch_labels = None
depends_on = None


def _uuid() -> sa.Uuid:
    return sa.Uuid()


def _money() -> sa.Numeric:
    return sa.Numeric(18, 6)


def upgrade() -> None:
    op.create_table(
        "agent_run_budgets",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("agent_run_id", _uuid(), nullable=False),
        sa.Column("authorized_budget_usd", _money(), nullable=False),
        sa.Column("attempt_reservation_usd", _money(), nullable=False),
        sa.Column("allocation_source", sa.String(), nullable=False),
        sa.Column("allocated_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "authorized_budget_usd >= 0",
            name="ck_agent_run_budget_authorized_nonnegative",
        ),
        sa.CheckConstraint(
            "attempt_reservation_usd > 0",
            name="ck_agent_run_budget_reservation_positive",
        ),
        sa.ForeignKeyConstraint(["agent_run_id"], ["agent_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("agent_run_id", name="uq_agent_run_budget_agent_run_id"),
    )
    for column in (
        "id",
        "agent_run_id",
        "allocation_source",
        "allocated_by",
        "created_at",
    ):
        op.create_index(f"ix_agent_run_budgets_{column}", "agent_run_budgets", [column])

    op.create_table(
        "agent_run_cost_entries",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("agent_run_id", _uuid(), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("agent_name", sa.String(), nullable=False),
        sa.Column("department", sa.String(), nullable=True),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("model", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("reserved_usd", _money(), nullable=False),
        sa.Column("actual_cost_usd", _money(), nullable=True),
        sa.Column("estimated_cost_usd", _money(), nullable=True),
        sa.Column("unattributed_cost_usd", _money(), nullable=False),
        sa.Column("billing_evidence", sa.Boolean(), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("settled_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "attempt_number >= 1",
            name="ck_agent_run_cost_entry_attempt_positive",
        ),
        sa.CheckConstraint(
            "reserved_usd >= 0",
            name="ck_agent_run_cost_entry_reserved_nonnegative",
        ),
        sa.CheckConstraint(
            "actual_cost_usd IS NULL OR actual_cost_usd >= 0",
            name="ck_agent_run_cost_entry_actual_nonnegative",
        ),
        sa.CheckConstraint(
            "estimated_cost_usd IS NULL OR estimated_cost_usd >= 0",
            name="ck_agent_run_cost_entry_estimated_nonnegative",
        ),
        sa.CheckConstraint(
            "unattributed_cost_usd >= 0",
            name="ck_agent_run_cost_entry_unattributed_nonnegative",
        ),
        sa.ForeignKeyConstraint(["agent_run_id"], ["agent_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "agent_run_id",
            "attempt_number",
            name="uq_agent_run_cost_entry_attempt",
        ),
    )
    for column in (
        "id",
        "agent_run_id",
        "attempt_number",
        "agent_name",
        "department",
        "provider",
        "model",
        "status",
        "billing_evidence",
        "created_at",
        "settled_at",
    ):
        op.create_index(
            f"ix_agent_run_cost_entries_{column}",
            "agent_run_cost_entries",
            [column],
        )


def downgrade() -> None:
    op.drop_table("agent_run_cost_entries")
    op.drop_table("agent_run_budgets")
