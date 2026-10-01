from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


_TARGET_TYPE_PATTERN = (
    "^(organization_agent|native_skill|instruction_contract|workflow|context_policy|"
    "runtime_profile|evaluation_suite|tool_adapter|code_configuration|training_recipe)$"
)


class ImprovementProposalCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposal_key: str = Field(min_length=1, max_length=255)
    work_item_id: UUID
    target_type: str = Field(pattern=_TARGET_TYPE_PATTERN)
    target_reference: str = Field(min_length=1, max_length=2000)
    baseline_version: str = Field(min_length=1, max_length=255)
    baseline_fingerprint: str = Field(pattern="^[0-9a-f]{64}$")
    problem_statement: str = Field(min_length=1, max_length=4000)
    hypothesis: str = Field(min_length=1, max_length=4000)
    expected_improvement: str = Field(min_length=1, max_length=4000)
    acceptance_constraints: dict[str, Any] = Field(min_length=1)
    evidence_reference_ids: list[UUID] = Field(min_length=1, max_length=100)
    supersedes_proposal_id: UUID | None = None


class ImprovementCandidateCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_key: str = Field(min_length=1, max_length=255)
    parent_candidate_id: UUID | None = None
    candidate_version: str = Field(min_length=1, max_length=255)
    candidate_fingerprint: str = Field(pattern="^[0-9a-f]{64}$")
    artifact_reference: str = Field(min_length=1, max_length=4000)
    implementation_provenance: dict[str, Any] = Field(min_length=1)
    candidate_hypothesis: str = Field(min_length=1, max_length=4000)
    expected_improvement: str = Field(min_length=1, max_length=4000)
    acceptance_constraints: dict[str, Any] = Field(min_length=1)


class ImprovementWithdrawal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=1, max_length=4000)


class ImprovementProposalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_key: str
    proposal_key: str
    work_item_id: UUID
    target_type: str
    target_reference: str
    baseline_version: str
    baseline_fingerprint: str
    problem_statement: str
    hypothesis: str
    expected_improvement: str
    acceptance_constraints: dict[str, Any]
    evidence_reference_ids: tuple[UUID, ...]
    supersedes_proposal_id: UUID | None
    status: str
    record_fingerprint: str
    created_by: str
    created_at: datetime
    withdrawn_by: str | None
    withdrawn_reason: str | None
    withdrawn_at: datetime | None
    authority_conclusion: str = "none_granted"
    active_version_changed: bool = False
    autonomy_changed: bool = False
    permission_or_tool_access_changed: bool = False
    monetary_authority_changed: bool = False
    deployment_authorized: bool = False
    external_action_authorized: bool = False
    evaluation_conclusion: str = "not_assessed"
    limitations: tuple[str, ...] = (
        "Proposal presence records improvement intent only; it does not approve or activate a capability.",
        "Target references are lineage pointers and must be resolved by the artifact-specific canonical owner before later evaluation or promotion.",
        "Evaluation, promotion, deployment, autonomy, permission/tool access and monetary authority remain separate governed truths.",
    )


class ImprovementCandidateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_key: str
    candidate_key: str
    proposal_id: UUID
    parent_candidate_id: UUID | None
    target_type: str
    target_reference: str
    baseline_version: str
    baseline_fingerprint: str
    candidate_version: str
    candidate_fingerprint: str
    artifact_reference: str
    implementation_provenance: dict[str, Any]
    candidate_hypothesis: str
    expected_improvement: str
    acceptance_constraints: dict[str, Any]
    status: str
    record_fingerprint: str
    created_by: str
    created_at: datetime
    withdrawn_by: str | None
    withdrawn_reason: str | None
    withdrawn_at: datetime | None
    authority_conclusion: str = "none_granted"
    active_version_changed: bool = False
    autonomy_changed: bool = False
    permission_or_tool_access_changed: bool = False
    monetary_authority_changed: bool = False
    deployment_authorized: bool = False
    external_action_authorized: bool = False
    evaluation_conclusion: str = "not_assessed"
    limitations: tuple[str, ...] = (
        "Candidate presence records immutable artifact lineage only; it is not an approval or active-version record.",
        "A prepared candidate has not passed an independent evaluation campaign unless separate GRSI evaluation evidence says so.",
        "Promotion, rollback and active-version truth remain owned by the target artifact's canonical system and authorized decision/release boundaries.",
    )
