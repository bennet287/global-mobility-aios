from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Numeric, UniqueConstraint
from sqlmodel import Field, SQLModel


class AgentRunProviderAttempt(SQLModel, table=True):
    """One provider-call boundary for a controlled AgentRun attempt."""

    __tablename__ = "agent_run_provider_attempts"
    __table_args__ = (
        UniqueConstraint("agent_run_id", "attempt_no", name="uq_agent_run_provider_attempt"),
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
    agent_run_id: UUID = Field(foreign_key="agent_runs.id", index=True)
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
