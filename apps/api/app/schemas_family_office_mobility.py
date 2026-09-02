from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


EvidenceStatus = Literal["unconfirmed", "documented", "independently_verified"]
ScreeningStatus = Literal["pending", "cleared", "escalated"]


class FamilyOfficeStructureInput(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    structure_type: Literal[
        "operating_company", "holding_company", "trust", "foundation",
        "partnership", "fund", "special_purpose_vehicle", "other",
    ]
    jurisdiction: str = Field(min_length=2, max_length=120)
    beneficial_ownership_disclosed: bool = False


class FamilyOfficeAssessmentCreate(BaseModel):
    lead_id: UUID
    business_advisory_assessment_id: UUID | None = None
    family_office_name: str | None = Field(default=None, max_length=200)
    primary_objectives: list[str] = Field(min_length=1, max_length=15)
    target_jurisdictions: list[str] = Field(min_length=1, max_length=10)
    current_tax_residencies: list[str] = Field(default_factory=list, max_length=10)
    citizenships: list[str] = Field(default_factory=list, max_length=10)
    family_members: int = Field(default=1, ge=1, le=100)
    structures: list[FamilyOfficeStructureInput] = Field(default_factory=list, max_length=50)
    asset_classes: list[str] = Field(default_factory=list, max_length=30)
    estimated_net_worth_minor: int | None = Field(default=None, ge=0)
    liquid_assets_minor: int | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    source_of_wealth_status: EvidenceStatus = "unconfirmed"
    source_of_funds_status: EvidenceStatus = "unconfirmed"
    beneficial_ownership_documented: bool = False
    screening_status: ScreeningStatus = "pending"
    pep_or_sanctions_exposure_disclosed: bool = False
    tax_adviser_engaged: bool = False
    legal_adviser_engaged: bool = False
    succession_plan_documented: bool = False
    banking_relationships_confirmed: bool = False
    disclosed_constraints: list[str] = Field(default_factory=list, max_length=30)
    document_record_ids: list[UUID] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def normalize(self):
        if (
            self.estimated_net_worth_minor is not None
            or self.liquid_assets_minor is not None
        ) and self.currency is None:
            raise ValueError("Currency is required when financial amounts are provided")
        if (
            self.liquid_assets_minor is not None
            and self.estimated_net_worth_minor is not None
            and self.liquid_assets_minor > self.estimated_net_worth_minor
        ):
            raise ValueError("Liquid assets cannot exceed estimated net worth")
        if self.currency:
            self.currency = self.currency.strip().upper()
        self.primary_objectives = list(dict.fromkeys(
            value.strip() for value in self.primary_objectives if value.strip()
        ))
        self.target_jurisdictions = list(dict.fromkeys(
            value.strip() for value in self.target_jurisdictions if value.strip()
        ))
        if not self.primary_objectives or not self.target_jurisdictions:
            raise ValueError("Objectives and target jurisdictions are required")
        return self


class FamilyOfficeWorkstream(BaseModel):
    workstream_key: str
    title: str
    readiness_score: float
    readiness_band: str
    findings: list[str]
    blockers: list[str]
    next_actions: list[str]


class FamilyOfficeAssessmentRead(BaseModel):
    id: UUID
    lead_id: UUID
    business_advisory_assessment_id: UUID | None
    family_office_name: str | None
    readiness_score: float
    readiness_band: str
    identity_score: float
    wealth_evidence_score: float
    ownership_transparency_score: float
    governance_score: float
    mobility_grounding_score: float
    workstreams: list[FamilyOfficeWorkstream]
    blockers: list[str]
    next_actions: list[str]
    evidence_basis: list[dict[str, Any]]
    grounded_pathway_versions: list[dict[str, Any]]
    grounded_program_versions: list[dict[str, Any]]
    escalation_flags: list[str]
    status: str
    human_review_required: bool
    generated_by: str
    reviewed_by: str | None
    reviewed_at: datetime | None
    review_notes: str | None
    score_semantics: str
    created_at: datetime
    updated_at: datetime


class FamilyOfficeReviewCreate(BaseModel):
    decision: Literal["approved", "revision_required"]
    reason: str = Field(min_length=10, max_length=5000)


class FamilyOfficeReviewRead(BaseModel):
    id: UUID
    assessment_id: UUID
    decision: str
    reason: str
    reviewer: str
    created_at: datetime
