from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Column, Numeric, UniqueConstraint
from sqlmodel import Field, SQLModel

from app.models.domain import now_utc


MONEY_SQL_TYPE = Numeric(18, 6)


class AgentRunBudget(SQLModel, table=True):
    """Authorized real-money-equivalent envelope for one AgentRun.

    This is economic authority only. It does not duplicate AgentRun execution state.
    """

    __tablename__ = "agent_run_budgets"
    __table_args__ = (
        CheckConstraint(
            "authorized_budget_usd >= 0",
            name="ck_agent_run_budget_authorized_nonnegative",
        ),
        CheckConstraint(
            "attempt_reservation_usd > 0",
            name="ck_agent_run_budget_reservation_positive",
        ),
        UniqueConstraint("agent_run_id", name="uq_agent_run_budget_agent_run_id"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    agent_run_id: UUID = Field(index=True, foreign_key="agent_runs.id")
    authorized_budget_usd: Decimal = Field(
        sa_column=Column(MONEY_SQL_TYPE, nullable=False)
    )
    attempt_reservation_usd: Decimal = Field(
        sa_column=Column(MONEY_SQL_TYPE, nullable=False)
    )
    allocation_source: str = Field(default="runtime_policy", index=True)
    allocated_by: str = Field(default="system", index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)


class AgentRunCostEntry(SQLModel, table=True):
    """Per-attempt durable runtime cost evidence for an AgentRun.

    A reservation is authorized exposure, not a claim about provider billing. Actual
    cost is populated only when the adapter carries explicit billing evidence.
    Otherwise the reservation remains unattributed exposure and any token-derived
    amount stays an estimate.
    """

    __tablename__ = "agent_run_cost_entries"
    __table_args__ = (
        UniqueConstraint(
            "agent_run_id",
            "attempt_number",
            name="uq_agent_run_cost_entry_attempt",
        ),
        CheckConstraint(
            "attempt_number >= 1",
            name="ck_agent_run_cost_entry_attempt_positive",
        ),
        CheckConstraint(
            "reserved_usd >= 0",
            name="ck_agent_run_cost_entry_reserved_nonnegative",
        ),
        CheckConstraint(
            "actual_cost_usd IS NULL OR actual_cost_usd >= 0",
            name="ck_agent_run_cost_entry_actual_nonnegative",
        ),
        CheckConstraint(
            "estimated_cost_usd IS NULL OR estimated_cost_usd >= 0",
            name="ck_agent_run_cost_entry_estimated_nonnegative",
        ),
        CheckConstraint(
            "unattributed_cost_usd >= 0",
            name="ck_agent_run_cost_entry_unattributed_nonnegative",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    agent_run_id: UUID = Field(index=True, foreign_key="agent_runs.id")
    attempt_number: int = Field(index=True, ge=1)
    agent_name: str = Field(index=True)
    department: Optional[str] = Field(default=None, index=True)
    provider: str = Field(index=True)
    model: Optional[str] = Field(default=None, index=True)
    status: str = Field(default="reserved", index=True)
    reserved_usd: Decimal = Field(sa_column=Column(MONEY_SQL_TYPE, nullable=False))
    actual_cost_usd: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(MONEY_SQL_TYPE, nullable=True),
    )
    estimated_cost_usd: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(MONEY_SQL_TYPE, nullable=True),
    )
    unattributed_cost_usd: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(MONEY_SQL_TYPE, nullable=False),
    )
    billing_evidence: bool = Field(default=False, index=True)
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    created_at: datetime = Field(default_factory=now_utc, index=True)
    settled_at: Optional[datetime] = Field(default=None, index=True)
