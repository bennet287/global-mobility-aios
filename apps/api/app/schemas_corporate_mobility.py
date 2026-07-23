from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


CorporateAccountStatus = Literal["active", "suspended", "closed"]
CorporateCaseType = Literal["employee_relocation", "dependant", "sponsor_compliance", "entrepreneur_startup"]
CorporateCaseStatus = Literal["draft", "active", "on_hold", "completed", "closed"]


def _utc_naive(value: datetime | None) -> datetime | None:
    if value is None or value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


class CorporateAccountCreate(BaseModel):
    legal_name: str = Field(min_length=2, max_length=250)
    display_name: Optional[str] = Field(default=None, max_length=250)
    primary_country: str = Field(min_length=2, max_length=100)
    registration_number: Optional[str] = Field(default=None, max_length=120)
    contact_name: Optional[str] = Field(default=None, max_length=200)
    contact_email: Optional[EmailStr] = None
    compliance_owner: Optional[str] = Field(default=None, max_length=200)
    notes: Optional[str] = Field(default=None, max_length=5000)


class CorporateAccountUpdate(BaseModel):
    display_name: Optional[str] = Field(default=None, max_length=250)
    account_status: Optional[CorporateAccountStatus] = None
    primary_country: Optional[str] = Field(default=None, min_length=2, max_length=100)
    registration_number: Optional[str] = Field(default=None, max_length=120)
    contact_name: Optional[str] = Field(default=None, max_length=200)
    contact_email: Optional[EmailStr] = None
    compliance_owner: Optional[str] = Field(default=None, max_length=200)
    notes: Optional[str] = Field(default=None, max_length=5000)


class CorporateAccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    legal_name: str
    display_name: Optional[str]
    account_status: str
    primary_country: str
    registration_number: Optional[str]
    contact_name: Optional[str]
    contact_email: Optional[str]
    compliance_owner: Optional[str]
    notes: Optional[str]
    created_by: str
    updated_by: str
    created_at: datetime
    updated_at: datetime


class CorporateMobilityCaseCreate(BaseModel):
    employee_lead_id: Optional[UUID] = None
    case_reference: Optional[str] = Field(default=None, min_length=3, max_length=80)
    case_type: CorporateCaseType = "employee_relocation"
    origin_country: Optional[str] = Field(default=None, min_length=2, max_length=100)
    destination_country: str = Field(min_length=2, max_length=100)
    sponsor_name: Optional[str] = Field(default=None, max_length=250)
    target_start_date: Optional[datetime] = None
    compliance_due_date: Optional[datetime] = None
    notes: Optional[str] = Field(default=None, max_length=5000)

    @model_validator(mode="after")
    def validate_dates(self):
        if (
            self.target_start_date is not None
            and self.compliance_due_date is not None
            and _utc_naive(self.compliance_due_date) > _utc_naive(self.target_start_date)
        ):
            raise ValueError("Compliance due date cannot be later than the target start date")
        return self


class CorporateMobilityCaseUpdate(BaseModel):
    status: Optional[CorporateCaseStatus] = None
    employee_lead_id: Optional[UUID] = None
    origin_country: Optional[str] = Field(default=None, min_length=2, max_length=100)
    destination_country: Optional[str] = Field(default=None, min_length=2, max_length=100)
    sponsor_name: Optional[str] = Field(default=None, max_length=250)
    target_start_date: Optional[datetime] = None
    compliance_due_date: Optional[datetime] = None
    notes: Optional[str] = Field(default=None, max_length=5000)


class CorporateMobilityCaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    corporate_account_id: UUID
    employee_lead_id: Optional[UUID]
    case_reference: str
    case_type: str
    status: str
    origin_country: Optional[str]
    destination_country: str
    sponsor_name: Optional[str]
    target_start_date: Optional[datetime]
    compliance_due_date: Optional[datetime]
    human_review_required: bool
    notes: Optional[str]
    created_by: str
    updated_by: str
    created_at: datetime
    updated_at: datetime


class CorporateAccountDetail(CorporateAccountRead):
    cases: list[CorporateMobilityCaseRead] = Field(default_factory=list)


SponsorType = Literal["employing_entity", "host_entity", "authorized_agent"]
SponsorStatus = Literal["active", "suspended", "retired"]
RelationshipType = Literal["spouse", "partner", "child", "parent", "other"]
ComplianceEventType = Literal[
    "filing_deadline", "document_expiry", "permit_renewal", "registration",
    "sponsor_report", "payroll", "tax", "custom",
]
ComplianceEventStatus = Literal["open", "completed", "waived"]


class CorporateSponsorEntityCreate(BaseModel):
    legal_name: str = Field(min_length=2, max_length=250)
    sponsor_type: SponsorType
    country: str = Field(min_length=2, max_length=100)
    registration_number: Optional[str] = Field(default=None, max_length=120)
    contact_name: Optional[str] = Field(default=None, max_length=200)
    contact_email: Optional[EmailStr] = None


class CorporateSponsorEntityUpdate(BaseModel):
    legal_name: Optional[str] = Field(default=None, min_length=2, max_length=250)
    sponsor_type: Optional[SponsorType] = None
    country: Optional[str] = Field(default=None, min_length=2, max_length=100)
    registration_number: Optional[str] = Field(default=None, max_length=120)
    contact_name: Optional[str] = Field(default=None, max_length=200)
    contact_email: Optional[EmailStr] = None
    status: Optional[SponsorStatus] = None


class CorporateSponsorEntityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    corporate_account_id: UUID
    legal_name: str
    sponsor_type: str
    country: str
    registration_number: Optional[str]
    contact_name: Optional[str]
    contact_email: Optional[str]
    status: str
    created_by: str
    updated_by: str
    created_at: datetime
    updated_at: datetime


class CorporateCaseSponsorAssignmentCreate(BaseModel):
    sponsor_entity_id: UUID


class CorporateCaseSponsorAssignmentUpdate(BaseModel):
    status: Literal["removed"]


class CorporateCaseSponsorAssignmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    corporate_mobility_case_id: UUID
    sponsor_entity_id: UUID
    status: str
    created_by: str
    updated_by: str
    created_at: datetime
    updated_at: datetime


class CorporateCaseDependantCreate(BaseModel):
    dependant_lead_id: UUID
    relationship_to_employee: RelationshipType
    sponsorship_required: bool = False


class CorporateCaseDependantUpdate(BaseModel):
    status: Literal["removed"]


class CorporateCaseDependantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    corporate_mobility_case_id: UUID
    dependant_lead_id: UUID
    relationship_to_employee: str
    sponsorship_required: bool
    status: str
    created_by: str
    updated_by: str
    created_at: datetime
    updated_at: datetime


class CorporateComplianceEventCreate(BaseModel):
    event_type: ComplianceEventType
    title: str = Field(min_length=2, max_length=250)
    due_at: datetime
    evidence_required: bool = True


class CorporateComplianceEventUpdate(BaseModel):
    status: ComplianceEventStatus
    completion_notes: Optional[str] = Field(default=None, max_length=5000)


class CorporateComplianceEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    corporate_mobility_case_id: UUID
    event_type: str
    title: str
    due_at: datetime
    status: str
    evidence_required: bool
    human_review_required: bool
    completion_notes: Optional[str]
    completed_by: Optional[str]
    completed_at: Optional[datetime]
    created_by: str
    updated_by: str
    created_at: datetime
    updated_at: datetime


RelocationTaskCategory = Literal[
    "immigration", "relocation", "payroll", "tax", "housing", "travel", "onboarding", "custom",
]
RelocationTaskStatus = Literal[
    "planned", "ready", "in_progress", "blocked", "awaiting_approval", "completed", "cancelled",
]


class CorporateRelocationTaskCreate(BaseModel):
    title: str = Field(min_length=2, max_length=250)
    category: RelocationTaskCategory
    owner_role: str = Field(default="mobility_operator", min_length=2, max_length=100)
    due_at: Optional[datetime] = None
    depends_on_task_id: Optional[UUID] = None
    requires_human_approval: bool = False


class CorporateRelocationTaskTransition(BaseModel):
    status: Literal["ready", "in_progress", "blocked", "completed", "cancelled"]
    work_notes: Optional[str] = Field(default=None, max_length=5000)


class CorporateRelocationTaskDecisionCreate(BaseModel):
    decision: Literal["approved", "rejected"]
    reason: str = Field(min_length=3, max_length=5000)


class CorporateRelocationTaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    corporate_mobility_case_id: UUID
    depends_on_task_id: Optional[UUID]
    title: str
    category: str
    status: str
    owner_role: str
    due_at: Optional[datetime]
    requires_human_approval: bool
    approval_status: str
    work_notes: Optional[str]
    submitted_by: Optional[str]
    submitted_at: Optional[datetime]
    completed_by: Optional[str]
    completed_at: Optional[datetime]
    created_by: str
    updated_by: str
    created_at: datetime
    updated_at: datetime


class CorporateRelocationTaskDecisionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    corporate_relocation_task_id: UUID
    decision: str
    reason: str
    reviewer: str
    created_at: datetime


VentureStage = Literal["idea", "pre_seed", "seed", "growth", "established"]
VentureEvidenceType = Literal[
    "business_plan", "incorporation", "bank_statement", "investment_commitment",
    "grant", "revenue", "capitalization", "intellectual_property", "other",
]


class EntrepreneurVentureProfileCreate(BaseModel):
    founder_lead_id: UUID
    venture_name: str = Field(min_length=2, max_length=250)
    venture_stage: VentureStage
    sector: str = Field(min_length=2, max_length=150)
    target_country: str = Field(min_length=2, max_length=100)
    incorporation_country: Optional[str] = Field(default=None, min_length=2, max_length=100)
    founder_role: str = Field(min_length=2, max_length=150)
    business_model_summary: str = Field(min_length=20, max_length=5000)


class EntrepreneurVentureProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    corporate_mobility_case_id: UUID
    founder_lead_id: UUID
    venture_name: str
    venture_stage: str
    sector: str
    target_country: str
    incorporation_country: Optional[str]
    founder_role: str
    business_model_summary: str
    status: str
    human_review_required: bool
    submitted_by: Optional[str]
    submitted_at: Optional[datetime]
    reviewed_by: Optional[str]
    reviewed_at: Optional[datetime]
    review_notes: Optional[str]
    created_by: str
    updated_by: str
    created_at: datetime
    updated_at: datetime


class VentureEvidenceItemCreate(BaseModel):
    evidence_type: VentureEvidenceType
    title: str = Field(min_length=2, max_length=250)
    declared_amount_minor: Optional[int] = Field(default=None, ge=0)
    currency: Optional[str] = Field(default=None, min_length=3, max_length=3)
    document_record_id: Optional[UUID] = None
    notes: Optional[str] = Field(default=None, max_length=5000)

    @model_validator(mode="after")
    def validate_amount_currency(self):
        if (self.declared_amount_minor is None) != (self.currency is None):
            raise ValueError("Declared amount and currency must be provided together")
        return self


class VentureEvidenceItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    venture_profile_id: UUID
    evidence_type: str
    title: str
    declared_amount_minor: Optional[int]
    currency: Optional[str]
    document_record_id: Optional[UUID]
    notes: Optional[str]
    created_by: str
    created_at: datetime


class VentureReviewSubmission(BaseModel):
    evidence_complete_attestation: bool


class VentureReviewDecisionCreate(BaseModel):
    decision: Literal["approved", "rejected"]
    reason: str = Field(min_length=3, max_length=5000)


class VentureReviewDecisionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    venture_profile_id: UUID
    decision: str
    reason: str
    reviewer: str
    created_at: datetime
