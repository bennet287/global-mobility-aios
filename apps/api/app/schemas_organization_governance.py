from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class OrganizationControlUpdate(BaseModel):
    status: Literal["active", "paused"]
    reason: str = Field(min_length=8, max_length=1000)


class PositionSuspensionRequest(BaseModel):
    reason: str = Field(min_length=8, max_length=1000)


class PositionResumeRequest(BaseModel):
    reason: str = Field(min_length=8, max_length=1000)


class GovernanceDecisionRequest(BaseModel):
    decision: Literal["approved", "rejected", "returned"]
    reason: str = Field(min_length=8, max_length=2000)


class BoardPacketCreateRequest(BaseModel):
    packet_type: Literal["on_demand", "daily", "weekly", "incident"] = "on_demand"


class DeadlineRequest(BaseModel):
    due_at: datetime


class EmergencyRequest(BaseModel):
    reason: str = Field(min_length=8, max_length=1000)


class EscalationRequest(BaseModel):
    reason: str = Field(min_length=8, max_length=1000)


class WorkCancellationRequest(BaseModel):
    reason: str = Field(min_length=8, max_length=1000)


class WorkRetryRequest(BaseModel):
    reason: str = Field(min_length=8, max_length=1000)


class WorkEvidenceAmendmentRequest(BaseModel):
    evidence: dict = Field(default_factory=dict)
    facts: dict = Field(default_factory=dict)
    reason: str = Field(min_length=8, max_length=1000)


class WorkItemCreate(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=200)
    title: str = Field(min_length=3, max_length=300)
    objective: str = Field(min_length=8, max_length=2000)
    department: str = Field(default="Operations", min_length=2, max_length=100)
    action: str = Field(default="internal.analysis", min_length=3, max_length=100)
    risk_level: str = Field(default="routine", max_length=50)
    requires_board_approval: bool = False
    max_execution_attempts: int = Field(default=3, ge=1, le=5)
    context: dict = Field(default_factory=dict)
