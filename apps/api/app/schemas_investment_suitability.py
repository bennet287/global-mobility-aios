from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class InvestmentSuitabilityCreate(BaseModel):
    lead_id: UUID
    business_advisory_assessment_id: UUID | None = None
    target_countries: list[str] = Field(default_factory=list, max_length=10)
    program_ids: list[UUID] = Field(default_factory=list, max_length=20)
    available_capital_minor: int = Field(ge=0)
    liquid_capital_minor: int | None = Field(default=None, ge=0)
    net_worth_minor: int | None = Field(default=None, ge=0)
    currency: str = Field(min_length=3, max_length=3)
    risk_tolerance: Literal["conservative", "balanced", "growth"] = "balanced"
    family_members: int = Field(default=1, ge=1, le=50)
    timeline_months: int = Field(ge=1, le=240)
    capital_preservation_required: bool = False
    lawful_source_of_funds_confirmed: bool = False
    disclosed_constraints: list[str] = Field(default_factory=list, max_length=30)
    document_record_ids: list[UUID] = Field(default_factory=list, max_length=50)

    @model_validator(mode="after")
    def normalize(self):
        self.currency = self.currency.strip().upper()
        self.target_countries = list(dict.fromkeys(item.strip() for item in self.target_countries if item.strip()))
        if not self.target_countries and not self.program_ids:
            raise ValueError("Select at least one target country or published program")
        return self


class InvestmentProgramSuitabilityResult(BaseModel):
    program_id: UUID
    program_version_id: UUID
    name: str
    country: str
    program_type: str
    minimum_commitment_minor: int
    currency: str
    readiness_score: float
    readiness_band: str
    capital_coverage_score: float
    evidence_score: float
    family_fit_score: float
    risk_alignment_score: float
    findings: list[str]
    blockers: list[str]
    next_actions: list[str]
    official_source_id: UUID
    source_snapshot_id: UUID
    pathway_version_id: UUID


class InvestmentSuitabilityRead(BaseModel):
    id: UUID
    lead_id: UUID
    business_advisory_assessment_id: UUID | None
    candidate_program_version_ids: list[UUID]
    ranked_programs: list[InvestmentProgramSuitabilityResult]
    blockers: list[str]
    next_actions: list[str]
    evidence_basis: list[dict[str, Any]]
    overall_readiness_score: float
    readiness_band: str
    status: str
    human_review_required: bool
    generated_by: str
    reviewed_by: str | None
    reviewed_at: datetime | None
    review_notes: str | None
    score_semantics: str
    created_at: datetime
    updated_at: datetime


class InvestmentSuitabilityReviewCreate(BaseModel):
    decision: Literal["approved", "revision_required"]
    reason: str = Field(min_length=10, max_length=5000)


class InvestmentSuitabilityReviewRead(BaseModel):
    id: UUID
    assessment_id: UUID
    decision: str
    reason: str
    reviewer: str
    created_at: datetime
