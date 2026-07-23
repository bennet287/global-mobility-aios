from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


ProgramType = Literal[
    "residence_by_investment",
    "citizenship_by_investment",
    "investor_entrepreneur",
]


class InvestmentProgramVersionInput(BaseModel):
    pathway_version_id: UUID
    official_source_id: UUID
    source_snapshot_id: UUID
    minimum_commitment_minor: int = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)
    investment_options: list[dict[str, Any]] = Field(min_length=1, max_length=20)
    holding_period_text: str | None = Field(default=None, max_length=2000)
    physical_presence_text: str | None = Field(default=None, max_length=2000)
    family_scope: list[str] = Field(default_factory=list, max_length=30)
    due_diligence: list[str] = Field(min_length=1, max_length=50)
    fees: dict[str, Any] = Field(default_factory=dict)
    benefits: list[str] = Field(default_factory=list, max_length=50)
    risks: list[str] = Field(min_length=1, max_length=50)
    effective_from: datetime | None = None
    effective_to: datetime | None = None

    @model_validator(mode="after")
    def normalize_and_validate(self):
        self.currency = self.currency.strip().upper()
        if self.effective_from and self.effective_to and self.effective_to <= self.effective_from:
            raise ValueError("Effective end must be after effective start")
        serialized = " ".join([
            str(self.investment_options), str(self.holding_period_text), str(self.physical_presence_text),
            str(self.family_scope), str(self.due_diligence), str(self.fees), str(self.benefits), str(self.risks),
        ]).lower()
        prohibited_claims = ("guaranteed approval", "100% approval", "guaranteed citizenship", "guaranteed residence")
        if any(claim in serialized for claim in prohibited_claims):
            raise ValueError("Guaranteed authority-outcome claims are not allowed")
        return self


class InvestmentProgramCreate(InvestmentProgramVersionInput):
    program_key: str = Field(min_length=3, max_length=160, pattern=r"^[a-z0-9][a-z0-9_-]+$")
    name: str = Field(min_length=3, max_length=250)
    country: str = Field(min_length=2, max_length=100)
    program_type: ProgramType
    pathway_id: UUID
    description: str | None = Field(default=None, max_length=3000)


class InvestmentProgramPublish(BaseModel):
    review_notes: str = Field(min_length=10, max_length=5000)


class InvestmentProgramVersionRead(BaseModel):
    id: UUID
    program_id: UUID
    version_number: int
    lifecycle_status: str
    supersedes_version_id: UUID | None
    pathway_version_id: UUID
    official_source_id: UUID
    source_snapshot_id: UUID
    minimum_commitment_minor: int
    currency: str
    investment_options: list[dict[str, Any]]
    holding_period_text: str | None
    physical_presence_text: str | None
    family_scope: list[str]
    due_diligence: list[str]
    fees: dict[str, Any]
    benefits: list[str]
    risks: list[str]
    effective_from: datetime | None
    effective_to: datetime | None
    human_review_required: bool
    created_by: str
    approved_by: str | None
    review_notes: str | None
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime


class InvestmentProgramRead(BaseModel):
    id: UUID
    program_key: str
    name: str
    country: str
    program_type: str
    pathway_id: UUID
    description: str | None
    catalogue_status: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    current_version: InvestmentProgramVersionRead | None
    versions: list[InvestmentProgramVersionRead] = Field(default_factory=list)


class InvestmentProgramOnboardingItem(BaseModel):
    country: str
    readiness_state: str
    active_official_sources: int
    content_addressed_snapshots: int
    active_verified_rules: int
    draft_pathways: int
    published_pathways: int
    draft_programs: int
    published_programs: int
    blockers: list[str] = Field(default_factory=list)
    next_action: str


class InvestmentProgramOnboardingReadiness(BaseModel):
    total_jurisdictions: int
    source_ready: int
    pathway_ready: int
    awaiting_independent_review: int
    published: int
    blocked: int
    items: list[InvestmentProgramOnboardingItem] = Field(default_factory=list)
