from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Numeric, UniqueConstraint
from sqlmodel import Field, SQLModel


class ProviderCallAttempt(SQLModel, table=True):
    """One durable paid-call boundary, linked to its real execution context."""

    __tablename__ = "provider_call_attempts"
    __table_args__ = (
        UniqueConstraint("agent_run_id", "attempt_no", name="uq_agent_run_provider_attempt"),
        CheckConstraint(
            "(agent_run_id IS NOT NULL AND operation_key IS NULL) OR "
            "(agent_run_id IS NULL AND operation_key IS NOT NULL)",
            name="ck_provider_call_attempt_identity",
        ),
        CheckConstraint("attempt_no > 0", name="ck_agent_run_provider_attempt_no"),
        CheckConstraint(
            "status IN ('started','observed','outcome_unknown')",
            name="ck_agent_run_provider_attempt_status",
        ),
        CheckConstraint(
            "cost_basis IN ('unattributed','estimated','provider_billed')",
            name="ck_agent_run_provider_attempt_cost_basis",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    agent_run_id: Optional[UUID] = Field(default=None, foreign_key="agent_runs.id", index=True)
    operation_key: Optional[str] = Field(default=None, index=True, unique=True)
    context_kind: Optional[str] = None
    context_id: Optional[str] = None
    attempt_no: int
    provider: str
    requested_model: Optional[str] = None
    model: Optional[str] = None
    status: str = "started"
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    estimated_cost_usd: Optional[Decimal] = Field(default=None, sa_type=Numeric(18, 9))
    billed_cost_usd: Optional[Decimal] = Field(default=None, sa_type=Numeric(18, 9))
    cost_basis: str = "unattributed"
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    settled_at: Optional[datetime] = None


# Preserve the Python import for existing Phase 16.3A readers and tests.
AgentRunProviderAttempt = ProviderCallAttempt
