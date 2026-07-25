from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ClientPortalGrantCreate(BaseModel):
    lead_id: UUID
    label: str = Field(default="Client portal", min_length=2, max_length=120)
    expires_in_days: int = Field(default=30, ge=1, le=90)


class ClientPortalGrantRevoke(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


class ClientPortalGrantRead(BaseModel):
    id: UUID
    lead_id: UUID
    label: str
    status: Literal["active", "expired", "revoked"]
    expires_at: datetime
    created_by: str
    access_count: int
    last_accessed_at: datetime | None = None
    revoked_by: str | None = None
    revoked_at: datetime | None = None
    revocation_reason: str | None = None
    created_at: datetime
    updated_at: datetime
    expired: bool


class ClientPortalGrantIssued(BaseModel):
    grant: ClientPortalGrantRead
    token: str
    portal_path: str


class ClientPortalDocument(BaseModel):
    id: UUID
    document_type: str
    filename: str
    status: str
    uploaded_at: datetime | None = None
    expiry_date: datetime | None = None


class ClientPortalMilestone(BaseModel):
    key: str
    label: str
    state: Literal["complete", "current", "upcoming"]


class ClientPortalDashboard(BaseModel):
    grant_id: UUID
    client_name: str
    target_country: str | None = None
    intent: str
    case_status: str
    application_stage: str | None = None
    next_action: str
    documents: list[ClientPortalDocument] = Field(default_factory=list)
    document_counts: dict[str, int] = Field(default_factory=dict)
    milestones: list[ClientPortalMilestone] = Field(default_factory=list)
    expires_at: datetime
    updated_at: datetime
