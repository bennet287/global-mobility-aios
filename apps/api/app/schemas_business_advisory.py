from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


BusinessMobilityIntent = Literal[
    "launch_startup",
    "expand_existing_business",
    "founder_relocation",
    "passive_investment",
    "family_office_relocation",
    "tax_residency_planning",
    "asset_and_family_mobility",
]


class BusinessAdvisoryCreate(BaseModel):
    lead_id: UUID | None = None
    corporate_mobility_case_id: UUID | None = None
    primary_intent: BusinessMobilityIntent
    situation: str = Field(min_length=30, max_length=12000)
    target_countries: list[str] = Field(min_length=1, max_length=5)
    capital_available_minor: int | None = Field(default=None, ge=0)
    net_worth_minor: int | None = Field(default=None, ge=0)
    annual_revenue_minor: int | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    employees: int | None = Field(default=None, ge=0, le=1_000_000)
    business_age_years: float | None = Field(default=None, ge=0, le=500)
    founder_experience_years: float | None = Field(default=None, ge=0, le=100)
    timeline_months: int | None = Field(default=None, ge=1, le=240)
    family_relocation: bool = False
    lawful_source_of_funds_confirmed: bool = False
    risk_disclosures: list[str] = Field(default_factory=list, max_length=20)
    document_record_ids: list[UUID] = Field(default_factory=list, max_length=50)

    @model_validator(mode="after")
    def validate_financial_currency(self):
        has_financials = any(
            value is not None
            for value in (self.capital_available_minor, self.net_worth_minor, self.annual_revenue_minor)
        )
        if has_financials and self.currency is None:
            raise ValueError("Currency is required when financial amounts are provided")
        self.target_countries = list(dict.fromkeys(country.strip() for country in self.target_countries if country.strip()))
        if not self.target_countries:
            raise ValueError("At least one target country is required")
        return self


class BusinessStrategyOption(BaseModel):
    strategy_key: str
    title: str
    fit_score: float
    fit_band: str
    rationale: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    published_pathways: list[dict[str, Any]] = Field(default_factory=list)
    verification_state: str


class BusinessAdvisoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    lead_id: UUID | None
    corporate_mobility_case_id: UUID | None
    primary_intent: str
    situation_text: str
    feasibility_score: float
    feasibility_band: str
    information_score: float
    evidence_score: float
    commercial_fit_score: float
    pathway_grounding_score: float
    strategy_options: list[BusinessStrategyOption]
    blockers: list[str]
    next_actions: list[str]
    evidence_basis: list[dict[str, Any]]
    risk_flags: list[str]
    escalation_required: bool
    status: str
    human_review_required: bool
    generated_by: str
    reviewed_by: str | None
    reviewed_at: datetime | None
    review_notes: str | None
    score_semantics: str
    created_at: datetime
    updated_at: datetime


class BusinessAdvisoryReviewCreate(BaseModel):
    decision: Literal["approved", "revision_required"]
    reason: str = Field(min_length=5, max_length=5000)


class BusinessAdvisoryReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    assessment_id: UUID
    decision: str
    reason: str
    reviewer: str
    created_at: datetime
