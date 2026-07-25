from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


AudienceType = Literal["employer", "partner"]


class EcosystemPortalGrantCreate(BaseModel):
    corporate_account_id: UUID
    audience_type: AudienceType
    label: str = Field(min_length=2, max_length=120)
    expires_in_days: int = Field(default=30, ge=1, le=90)


class EcosystemPortalGrantRevoke(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


class EcosystemPortalGrantRead(BaseModel):
    id: UUID
    corporate_account_id: UUID
    audience_type: AudienceType
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


class EcosystemPortalGrantIssued(BaseModel):
    grant: EcosystemPortalGrantRead
    token: str
    portal_path: str


class EcosystemPortalCase(BaseModel):
    case_reference: str
    case_type: str
    status: str
    employee_name: str | None = None
    origin_country: str | None = None
    destination_country: str
    target_start_date: datetime | None = None
    compliance_due_date: datetime | None = None
    open_compliance_items: int
    open_tasks: int
    next_action: str
    updated_at: datetime


class EcosystemPortalComplianceItem(BaseModel):
    case_reference: str
    title: str
    event_type: str
    due_at: datetime
    status: str
    evidence_required: bool


class EcosystemPortalDashboard(BaseModel):
    grant_id: UUID
    audience_type: AudienceType
    account_name: str
    primary_country: str
    account_status: str
    case_counts: dict[str, int] = Field(default_factory=dict)
    cases: list[EcosystemPortalCase] = Field(default_factory=list)
    upcoming_compliance: list[EcosystemPortalComplianceItem] = Field(default_factory=list)
    expires_at: datetime
    updated_at: datetime
