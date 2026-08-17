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
    device_fingerprint: str | None = None
    device_label: str | None = None
    user_agent: str | None = None
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


class ClientPortalAppointment(BaseModel):
    id: UUID
    authority_name: str
    appointment_type: str
    location: str | None = None
    scheduled_at: datetime | None = None
    timezone: str
    status: str
    reference_number: str | None = None


class ClientPortalSubmission(BaseModel):
    id: UUID
    authority_name: str
    submission_channel: str
    submitted_at: datetime
    status: str
    reference_number: str | None = None
    tracking_url: str | None = None


class ClientPortalExternalAgencyAssignment(BaseModel):
    id: UUID
    agency_name: str
    status: str
    agency_reference_number: str | None = None
    handoff_at: datetime | None = None
    completed_at: datetime | None = None
    sla_due_at: datetime | None = None
    sla_status: str
    sla_breached_at: datetime | None = None


class ClientPortalAuthorityChecklistItem(BaseModel):
    id: UUID
    authority_name: str
    item_label: str
    category: str
    is_required: bool
    status: str


class ClientPortalPlanCost(BaseModel):
    currency: str | None = None
    government_application_fee: float | None = None
    government_application_fee_scope: str | None = None
    estimated_total_status: Literal["established", "not_established"] = "not_established"
    minimum_funds: float | None = None


class ClientPortalPlanRisk(BaseModel):
    level: Literal["low", "medium", "high"]
    declared_count: int = 0
    evidence_count: int = 0
    regulatory_count: int = 0


class ClientPortalJourneyMilestone(BaseModel):
    key: str
    title: str
    state: Literal["complete", "current", "upcoming", "attention"]
    due_at: datetime | None = None
    requires_human_approval: bool = False


class ClientPortalMobilityPlan(BaseModel):
    timeline_id: UUID
    comparison_assessment_id: UUID
    profile_version: int
    pathway_id: UUID
    pathway_version_id: UUID
    pathway_version_number: int
    pathway_name: str
    country: str
    domain: str
    plan_status: Literal["active", "completed"]
    current_stage_key: str | None = None
    activated_at: datetime
    published_at: datetime
    processing_evidence_status: Literal["established", "not_established"]
    cost: ClientPortalPlanCost
    risk: ClientPortalPlanRisk | None = None
    journey: list[ClientPortalJourneyMilestone] = Field(default_factory=list)


class ClientPortalEvidenceSummary(BaseModel):
    assessment_id: UUID
    requirement_source: str
    result_status: str
    review_status: Literal["approved"]
    required_count: int
    satisfied_count: int
    missing_count: int
    inconsistency_count: int
    reviewed_at: datetime


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
    appointments: list[ClientPortalAppointment] = Field(default_factory=list)
    submissions: list[ClientPortalSubmission] = Field(default_factory=list)
    external_agency_assignments: list[ClientPortalExternalAgencyAssignment] = Field(
        default_factory=list
    )
    authority_checklist: list[ClientPortalAuthorityChecklistItem] = Field(
        default_factory=list
    )
    mobility_plan: ClientPortalMobilityPlan | None = None
    evidence_summary: ClientPortalEvidenceSummary | None = None
    expires_at: datetime
    updated_at: datetime
