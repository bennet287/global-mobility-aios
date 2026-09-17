from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlmodel import Field, SQLModel


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class OrganizationAgent(SQLModel, table=True):
    """Durable governed identity for an AI employee.

    This record is lifecycle truth only. It does not grant authority, permissions,
    credentials, autonomy, tool access, work assignment, or execution rights.
    Static implementation definitions remain in CONTROLLED_AGENT_REGISTRY and
    execution history remains in AgentRun.
    """

    __tablename__ = "organization_agents"
    __table_args__ = (
        CheckConstraint(
            "status IN ('created','onboarding','inactive','active','restricted','suspended','retired')",
            name="ck_organization_agent_status",
        ),
        UniqueConstraint("agent_key", name="uq_organization_agent_key"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    agent_key: str = Field(index=True)
    registry_key: str = Field(index=True)
    registry_version: str
    display_name: str
    department: str = Field(index=True)
    position_key: Optional[str] = Field(default=None, index=True)
    status: str = Field(default="created", index=True)
    lifecycle_reason: str = "initial creation"
    created_by: str = Field(index=True)
    created_at: datetime = Field(default_factory=now_utc, index=True)
    updated_at: datetime = Field(default_factory=now_utc)
    activated_at: Optional[datetime] = None
    suspended_at: Optional[datetime] = None
    retired_at: Optional[datetime] = None
