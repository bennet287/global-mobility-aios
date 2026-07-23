from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


TreatyTopic = Literal[
    "residency_definition",
    "residency_tie_breaker",
    "permanent_establishment",
    "employment_income",
    "business_profits",
    "dividends_interest_royalties",
    "capital_gains",
    "pensions",
    "elimination_of_double_taxation",
    "mutual_agreement",
    "other",
]


class TaxTreatyEvidenceCreate(BaseModel):
    evidence_key: str = Field(min_length=3, max_length=200, pattern=r"^[a-z0-9][a-z0-9_-]+$")
    jurisdiction_a: str = Field(min_length=2, max_length=120)
    jurisdiction_b: str = Field(min_length=2, max_length=120)
    topic: TreatyTopic
    title: str = Field(min_length=5, max_length=300)
    statement: str = Field(min_length=20, max_length=8000)
    official_source_id: UUID
    source_snapshot_id: UUID
    effective_from: datetime | None = None
    effective_to: datetime | None = None

    @model_validator(mode="after")
    def validate_record(self):
        self.jurisdiction_a = self.jurisdiction_a.strip()
        self.jurisdiction_b = self.jurisdiction_b.strip()
        if self.jurisdiction_a.lower() == self.jurisdiction_b.lower():
            raise ValueError("Treaty evidence requires two different jurisdictions")
        if self.effective_from and self.effective_to and self.effective_to < self.effective_from:
            raise ValueError("Treaty evidence effective_to cannot precede effective_from")
        statement = self.statement.lower()
        prohibited = (
            "the client is tax resident",
            "guaranteed tax residence",
            "guaranteed treaty relief",
            "no tax will be due",
            "tax free guarantee",
        )
        if any(value in statement for value in prohibited):
            raise ValueError("Treaty evidence cannot contain a client conclusion or guaranteed tax outcome")
        return self


class TaxTreatyEvidenceDecisionCreate(BaseModel):
    decision: Literal["approved", "rejected"]
    reason: str = Field(min_length=10, max_length=5000)


class TaxTreatyEvidenceRead(BaseModel):
    id: UUID
    evidence_key: str
    jurisdiction_a: str
    jurisdiction_b: str
    topic: str
    title: str
    statement: str
    official_source_id: UUID
    source_snapshot_id: UUID
    source_url: str
    source_content_hash: str
    effective_from: datetime | None
    effective_to: datetime | None
    status: str
    proposed_by: str
    reviewed_by: str | None
    reviewed_at: datetime | None
    review_notes: str | None
    created_at: datetime
    updated_at: datetime


class TaxTreatyEvidenceDecisionRead(BaseModel):
    id: UUID
    tax_treaty_evidence_id: UUID
    decision: str
    reason: str
    reviewer: str
    created_at: datetime


class PresencePeriod(BaseModel):
    jurisdiction: str = Field(min_length=2, max_length=120)
    days: int = Field(ge=0, le=366)
    period_start: date | None = None
    period_end: date | None = None

    @model_validator(mode="after")
    def validate_period(self):
        self.jurisdiction = self.jurisdiction.strip()
        if self.period_start and self.period_end and self.period_end < self.period_start:
            raise ValueError("Presence period end cannot precede its start")
        return self


class AvailableHome(BaseModel):
    jurisdiction: str = Field(min_length=2, max_length=120)
    home_type: Literal["owned", "leased", "family_home", "employer_provided", "other"]
    continuously_available: bool = False


class TaxResidencyAssessmentCreate(BaseModel):
    lead_id: UUID
    family_office_assessment_id: UUID | None = None
    business_advisory_assessment_id: UUID | None = None
    tax_year: int = Field(ge=2000, le=2200)
    current_residencies: list[str] = Field(default_factory=list, max_length=10)
    target_residencies: list[str] = Field(min_length=1, max_length=10)
    citizenships: list[str] = Field(default_factory=list, max_length=10)
    presence_periods: list[PresencePeriod] = Field(min_length=1, max_length=30)
    available_homes: list[AvailableHome] = Field(default_factory=list, max_length=20)
    spouse_or_dependant_jurisdictions: list[str] = Field(default_factory=list, max_length=20)
    employment_jurisdictions: list[str] = Field(default_factory=list, max_length=20)
    director_or_control_jurisdictions: list[str] = Field(default_factory=list, max_length=20)
    business_structure_jurisdictions: list[str] = Field(default_factory=list, max_length=30)
    income_categories: list[str] = Field(default_factory=list, max_length=30)
    planned_arrival_date: date | None = None
    planned_departure_date: date | None = None
    objectives: list[str] = Field(min_length=1, max_length=20)
    disclosed_constraints: list[str] = Field(default_factory=list, max_length=30)
    tax_adviser_engaged: bool = False
    home_jurisdiction_adviser_engaged: bool = False
    destination_adviser_engaged: bool = False
    document_record_ids: list[UUID] = Field(default_factory=list, max_length=100)
    treaty_evidence_ids: list[UUID] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def normalize(self):
        if sum(period.days for period in self.presence_periods) > 366:
            raise ValueError("Recorded jurisdiction presence exceeds one tax year")
        if self.planned_arrival_date and self.planned_departure_date:
            if self.planned_arrival_date < self.planned_departure_date:
                raise ValueError("Planned arrival cannot precede planned departure in a relocation sequence")
        self.current_residencies = list(dict.fromkeys(
            value.strip() for value in self.current_residencies if value.strip()
        ))
        self.target_residencies = list(dict.fromkeys(
            value.strip() for value in self.target_residencies if value.strip()
        ))
        if not self.target_residencies:
            raise ValueError("At least one target residence jurisdiction is required")
        return self


class TaxIssue(BaseModel):
    issue_key: str
    title: str
    jurisdictions: list[str]
    severity: Literal["information_gap", "specialist_review", "material"]
    rationale: str
    evidence_state: str


class TaxResidencyWorkstream(BaseModel):
    workstream_key: str
    title: str
    readiness_score: float
    readiness_band: str
    blockers: list[str]
    next_actions: list[str]


class TaxResidencyAssessmentRead(BaseModel):
    id: UUID
    lead_id: UUID
    family_office_assessment_id: UUID | None
    business_advisory_assessment_id: UUID | None
    tax_year: int
    readiness_score: float
    readiness_band: str
    fact_completeness_score: float
    controlled_evidence_score: float
    treaty_grounding_score: float
    specialist_coordination_score: float
    issue_matrix: list[TaxIssue]
    workstreams: list[TaxResidencyWorkstream]
    blockers: list[str]
    next_actions: list[str]
    evidence_basis: list[dict[str, Any]]
    treaty_evidence_ids: list[UUID]
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


class TaxResidencyReviewCreate(BaseModel):
    decision: Literal["specialist_reviewed", "revision_required"]
    reason: str = Field(min_length=10, max_length=5000)


class TaxResidencyReviewRead(BaseModel):
    id: UUID
    assessment_id: UUID
    decision: str
    reason: str
    reviewer: str
    created_at: datetime
