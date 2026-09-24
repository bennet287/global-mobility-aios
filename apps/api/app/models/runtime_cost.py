from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Column, Numeric, UniqueConstraint
from sqlmodel import Field, SQLModel

from app.models.domain import now_utc


class RuntimeBudget(SQLModel, table=True):
    """Human-authorized runtime allocation used to gate paid provider calls."""

    __tablename__ = "runtime_budgets"
    __table_args__ = (
        UniqueConstraint("scope_type", "scope_key", name="uq_runtime_budget_scope"),
        CheckConstraint(
            "scope_type IN ('global','department','agent','work_item')",
            name="ck_runtime_budget_scope_type",
        ),
        CheckConstraint("currency = 'USD'", name="ck_runtime_budget_currency"),
        CheckConstraint("limit_usd > 0", name="ck_runtime_budget_limit_positive"),
        CheckConstraint(
            "reservation_usd_per_call > 0",
            name="ck_runtime_budget_reservation_positive",
        ),
        CheckConstraint(
            "reservation_usd_per_call <= limit_usd",
            name="ck_runtime_budget_reservation_within_limit",
        ),
        CheckConstraint(
            "status IN ('active','inactive')",
            name="ck_runtime_budget_status",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    scope_type: str = Field(index=True)
    scope_key: str = Field(index=True)
    currency: str = Field(default="USD", max_length=3)
    limit_usd: Decimal = Field(sa_column=Column(Numeric(18, 6), nullable=False))
    reservation_usd_per_call: Decimal = Field(
        sa_column=Column(Numeric(18, 6), nullable=False)
    )
    status: str = Field(default="active", index=True)
    created_by: str = Field(index=True)
    updated_by: str = Field(index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class RuntimeProviderCall(SQLModel, table=True):
    """One idempotent provider-call accounting record; not execution truth."""

    __tablename__ = "runtime_provider_calls"
    __table_args__ = (
        UniqueConstraint("call_key", name="uq_runtime_provider_call_key"),
        CheckConstraint("attempt_number >= 1", name="ck_runtime_provider_call_attempt_positive"),
        CheckConstraint(
            "status IN ('reserved','observed','actual','unattributed','released')",
            name="ck_runtime_provider_call_status",
        ),
        CheckConstraint(
            "authorized_amount_usd >= 0",
            name="ck_runtime_provider_call_authorized_nonnegative",
        ),
        CheckConstraint(
            "estimated_cost_usd IS NULL OR estimated_cost_usd >= 0",
            name="ck_runtime_provider_call_estimate_nonnegative",
        ),
        CheckConstraint(
            "actual_cost_usd IS NULL OR actual_cost_usd >= 0",
            name="ck_runtime_provider_call_actual_nonnegative",
        ),
        CheckConstraint(
            "(actual_cost_usd IS NULL AND billing_evidence = false) OR "
            "(actual_cost_usd IS NOT NULL AND billing_evidence = true)",
            name="ck_runtime_provider_call_actual_requires_evidence",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    call_key: str = Field(index=True)
    budget_id: UUID = Field(index=True, foreign_key="runtime_budgets.id")
    agent_run_id: Optional[UUID] = Field(
        default=None,
        index=True,
        foreign_key="agent_runs.id",
    )
    work_item_id: Optional[UUID] = Field(
        default=None,
        index=True,
        foreign_key="organizational_work_items.id",
    )
    agent_name: str = Field(index=True)
    department: str = Field(index=True)
    provider: str = Field(index=True)
    model: str = Field(index=True)
    attempt_number: int = Field(default=1, ge=1)
    status: str = Field(index=True)
    authorized_amount_usd: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(18, 6), nullable=False),
    )
    estimated_cost_usd: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(Numeric(18, 6), nullable=True),
    )
    actual_cost_usd: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(Numeric(18, 6), nullable=True),
    )
    billing_evidence: bool = False
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    error_class: Optional[str] = Field(default=None, index=True)
    started_at: datetime = Field(default_factory=now_utc, index=True)
    settled_at: Optional[datetime] = Field(default=None, index=True)
    updated_at: datetime = Field(default_factory=now_utc)
