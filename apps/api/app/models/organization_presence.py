from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Index, UniqueConstraint
from sqlmodel import Field, SQLModel

from app.models.domain import now_utc


class OrganizationExecutionHeartbeat(SQLModel, table=True):
    """Durable AIOS-owned execution-checkpoint lease observation.

    A heartbeat records only that a trusted AIOS worker reached a bounded execution
    checkpoint. It never grants authority and it must not be interpreted as a human,
    provider, or model being continuously online.
    """

    __tablename__ = "organization_execution_heartbeats"
    __table_args__ = (
        UniqueConstraint("heartbeat_key", name="uq_org_execution_heartbeat_key"),
        UniqueConstraint(
            "execution_attempt_id",
            "sequence",
            name="uq_org_execution_heartbeat_attempt_sequence",
        ),
        CheckConstraint("sequence >= 1", name="ck_org_execution_heartbeat_sequence_positive"),
        CheckConstraint(
            "fresh_until > observed_at",
            name="ck_org_execution_heartbeat_fresh_after_observed",
        ),
        Index(
            "ix_org_execution_heartbeat_tenant_position_observed",
            "tenant_key",
            "position_key",
            "observed_at",
        ),
        Index(
            "ix_org_execution_heartbeat_attempt_sequence",
            "execution_attempt_id",
            "sequence",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    heartbeat_key: str = Field(index=True)
    tenant_key: str = Field(index=True)
    position_key: str = Field(index=True)
    work_item_id: UUID = Field(index=True, foreign_key="organizational_work_items.id")
    execution_attempt_id: UUID = Field(index=True, foreign_key="organization_execution_attempts.id")
    sequence: int = Field(ge=1)
    checkpoint: str = Field(index=True)
    writer: str = Field(default="organization-worker", index=True)
    observed_at: datetime = Field(default_factory=now_utc, index=True)
    fresh_until: datetime = Field(index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)
