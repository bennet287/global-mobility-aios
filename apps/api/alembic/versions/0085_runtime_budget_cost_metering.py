"""Add governed runtime budgets and provider-call cost records.

Revision ID: 0085_runtime_budget_cost_metering
Revises: 0084_organization_agent_lifecycle
Create Date: 2026-09-24
"""

from alembic import op
import sqlalchemy as sa


revision = "0085_runtime_budget_cost_metering"
down_revision = "0084_organization_agent_lifecycle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "runtime_budgets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("scope_type", sa.String(), nullable=False),
        sa.Column("scope_key", sa.String(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("limit_usd", sa.Numeric(18, 6), nullable=False),
        sa.Column("reservation_usd_per_call", sa.Numeric(18, 6), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("updated_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "scope_type IN ('global','department','agent','work_item')",
            name="ck_runtime_budget_scope_type",
        ),
        sa.CheckConstraint("currency = 'USD'", name="ck_runtime_budget_currency"),
        sa.CheckConstraint("limit_usd > 0", name="ck_runtime_budget_limit_positive"),
        sa.CheckConstraint(
            "reservation_usd_per_call > 0",
            name="ck_runtime_budget_reservation_positive",
        ),
        sa.CheckConstraint(
            "reservation_usd_per_call <= limit_usd",
            name="ck_runtime_budget_reservation_within_limit",
        ),
        sa.CheckConstraint(
            "status IN ('active','inactive')",
            name="ck_runtime_budget_status",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scope_type", "scope_key", name="uq_runtime_budget_scope"),
    )
    for column in (
        "id",
        "scope_type",
        "scope_key",
        "status",
        "created_by",
        "updated_by",
        "created_at",
    ):
        op.create_index(f"ix_runtime_budgets_{column}", "runtime_budgets", [column])

    op.create_table(
        "runtime_provider_calls",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("call_key", sa.String(), nullable=False),
        sa.Column("budget_id", sa.Uuid(), nullable=False),
        sa.Column("agent_run_id", sa.Uuid(), nullable=True),
        sa.Column("work_item_id", sa.Uuid(), nullable=True),
        sa.Column("agent_name", sa.String(), nullable=False),
        sa.Column("department", sa.String(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("authorized_amount_usd", sa.Numeric(18, 6), nullable=False),
        sa.Column("estimated_cost_usd", sa.Numeric(18, 6), nullable=True),
        sa.Column("actual_cost_usd", sa.Numeric(18, 6), nullable=True),
        sa.Column("billing_evidence", sa.Boolean(), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=True),
        sa.Column("error_class", sa.String(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("settled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "attempt_number >= 1",
            name="ck_runtime_provider_call_attempt_positive",
        ),
        sa.CheckConstraint(
            "status IN ('reserved','observed','actual','unattributed','released')",
            name="ck_runtime_provider_call_status",
        ),
        sa.CheckConstraint(
            "authorized_amount_usd >= 0",
            name="ck_runtime_provider_call_authorized_nonnegative",
        ),
        sa.CheckConstraint(
            "estimated_cost_usd IS NULL OR estimated_cost_usd >= 0",
            name="ck_runtime_provider_call_estimate_nonnegative",
        ),
        sa.CheckConstraint(
            "actual_cost_usd IS NULL OR actual_cost_usd >= 0",
            name="ck_runtime_provider_call_actual_nonnegative",
        ),
        sa.CheckConstraint(
            "(actual_cost_usd IS NULL AND billing_evidence = false) OR "
            "(actual_cost_usd IS NOT NULL AND billing_evidence = true)",
            name="ck_runtime_provider_call_actual_requires_evidence",
        ),
        sa.ForeignKeyConstraint(["budget_id"], ["runtime_budgets.id"]),
        sa.ForeignKeyConstraint(["agent_run_id"], ["agent_runs.id"]),
        sa.ForeignKeyConstraint(["work_item_id"], ["organizational_work_items.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("call_key", name="uq_runtime_provider_call_key"),
    )
    for column in (
        "id",
        "call_key",
        "budget_id",
        "agent_run_id",
        "work_item_id",
        "agent_name",
        "department",
        "provider",
        "model",
        "status",
        "error_class",
        "started_at",
        "settled_at",
    ):
        op.create_index(
            f"ix_runtime_provider_calls_{column}",
            "runtime_provider_calls",
            [column],
        )


def downgrade() -> None:
    op.drop_table("runtime_provider_calls")
    op.drop_table("runtime_budgets")
