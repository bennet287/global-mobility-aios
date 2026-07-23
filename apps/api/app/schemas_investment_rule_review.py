from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class InvestmentRuleInput(BaseModel):
    rule_key: str = Field(min_length=3, max_length=200, pattern=r"^[a-z0-9][a-z0-9_-]+$")
    statement: str = Field(min_length=10, max_length=5000)
    evidence_scope: str = Field(min_length=3, max_length=200)


class InvestmentRuleProposalCreate(BaseModel):
    pathway_version_id: UUID
    rules: list[InvestmentRuleInput] = Field(min_length=1, max_length=30)

    @model_validator(mode="after")
    def validate_rules(self):
        keys = [rule.rule_key for rule in self.rules]
        if len(keys) != len(set(keys)):
            raise ValueError("Rule keys must be unique within a proposal")
        serialized = " ".join(rule.statement for rule in self.rules).lower()
        prohibited = ("guaranteed approval", "100% approval", "guaranteed residence", "guaranteed citizenship")
        if any(value in serialized for value in prohibited):
            raise ValueError("Guaranteed authority-outcome claims are not allowed")
        return self


class InvestmentRuleProposalReview(BaseModel):
    decision: Literal["approved", "rejected"]
    reason: str = Field(min_length=10, max_length=5000)


class InvestmentRuleProposalRead(BaseModel):
    id: UUID
    pathway_version_id: UUID
    pathway_id: UUID
    pathway_name: str
    country: str
    domain: str
    official_source_id: UUID
    source_snapshot_id: UUID
    source_url: str
    source_content_hash: str
    rules: list[InvestmentRuleInput]
    status: str
    proposed_by: str
    reviewed_by: str | None
    reviewed_at: datetime | None
    review_notes: str | None
    created_verified_rule_ids: list[UUID]
    replacement_pathway_version_id: UUID | None
    created_at: datetime
    updated_at: datetime
