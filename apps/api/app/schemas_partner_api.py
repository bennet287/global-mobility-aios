from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


PartnerScope = Literal["account:read", "cases:read", "compliance:read"]


class PartnerApiCredentialCreate(BaseModel):
    corporate_account_id: UUID
    label: str = Field(min_length=2, max_length=120)
    scopes: list[PartnerScope] = Field(min_length=1, max_length=3)
    expires_in_days: int = Field(default=90, ge=1, le=365)


class PartnerApiCredentialRevoke(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


class PartnerApiCredentialRead(BaseModel):
    id: UUID
    corporate_account_id: UUID
    key_prefix: str
    label: str
    scopes: list[PartnerScope]
    status: Literal["active", "expired", "revoked"]
    expires_at: datetime
    created_by: str
    access_count: int
    last_used_at: datetime | None = None
    revoked_by: str | None = None
    revoked_at: datetime | None = None
    revocation_reason: str | None = None
    created_at: datetime
    updated_at: datetime
    expired: bool


class PartnerApiCredentialIssued(BaseModel):
    credential: PartnerApiCredentialRead
    api_key: str
    api_base_path: str = "/api/partner/v1"


class ApiPageMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class PartnerAccountProjection(BaseModel):
    account_reference: UUID
    name: str
    primary_country: str
    status: str
    updated_at: datetime


class PartnerCaseProjection(BaseModel):
    case_reference: str
    case_type: str
    status: str
    employee_name: str | None = None
    origin_country: str | None = None
    destination_country: str
    target_start_date: datetime | None = None
    compliance_due_date: datetime | None = None
    updated_at: datetime


class PartnerCasePage(BaseModel):
    data: list[PartnerCaseProjection] = Field(default_factory=list)
    meta: ApiPageMeta


class PartnerComplianceProjection(BaseModel):
    case_reference: str
    event_type: str
    title: str
    due_at: datetime
    status: str
    evidence_required: bool


class PartnerCompliancePage(BaseModel):
    data: list[PartnerComplianceProjection] = Field(default_factory=list)
    meta: ApiPageMeta
