from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


ComparisonOperator = Literal[
    "candidate_gte_baseline_plus",
    "candidate_lte_baseline_plus",
    "candidate_gte",
    "candidate_lte",
]
EvaluatorActorType = Literal["human", "agent", "worker", "system", "external_human"]


class ImprovementEvaluationConstraint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metric_key: str = Field(min_length=1, max_length=255)
    operator: ComparisonOperator
    value: float


class ImprovementEvaluationCampaignCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    campaign_key: str = Field(min_length=1, max_length=255)
    campaign_version: int = Field(ge=1)
    candidate_id: UUID
    candidate_author_identities: list[str] = Field(min_length=1, max_length=20)
    candidate_author_evidence_reference_ids: list[UUID] = Field(min_length=1, max_length=100)
    evaluation_set_key: str = Field(min_length=1, max_length=255)
    evaluation_set_version: str = Field(min_length=1, max_length=255)
    evaluation_set_fingerprint: str = Field(pattern="^[0-9a-f]{64}$")
    evaluation_set_reference_ids: list[UUID] = Field(min_length=1, max_length=100)
    regression_constraints: list[ImprovementEvaluationConstraint] = Field(min_length=1, max_length=100)
    required_structurally_separate_evaluators: int = Field(default=1, ge=1, le=20)


class ImprovementEvaluationReportCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    report_key: str = Field(min_length=1, max_length=255)
    evaluator_actor_type: EvaluatorActorType
    evaluator_identity: str = Field(min_length=1, max_length=255)
    evaluator_independence_group: str = Field(min_length=1, max_length=255)
    independence_evidence_reference_ids: list[UUID] = Field(min_length=1, max_length=100)
    baseline_measurements: dict[str, float] = Field(min_length=1, max_length=200)
    candidate_measurements: dict[str, float] = Field(min_length=1, max_length=200)
    evaluation_evidence_reference_ids: list[UUID] = Field(min_length=1, max_length=100)
    reproducibility_reference_ids: list[UUID] = Field(min_length=1, max_length=100)


class ImprovementEvaluationConstraintResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metric_key: str
    operator: ComparisonOperator
    value: float
    baseline_value: float | None
    candidate_value: float
    passed: bool


class ImprovementEvaluationCampaignRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_key: str
    campaign_key: str
    campaign_version: int
    candidate_id: UUID
    proposal_id: UUID
    target_type: str
    target_reference: str
    baseline_version: str
    baseline_fingerprint: str
    candidate_version: str
    candidate_fingerprint: str
    candidate_author_identities: tuple[str, ...]
    candidate_author_evidence_reference_ids: tuple[UUID, ...]
    evaluation_set_key: str
    evaluation_set_version: str
    evaluation_set_fingerprint: str
    evaluation_set_reference_ids: tuple[UUID, ...]
    regression_constraints: tuple[ImprovementEvaluationConstraint, ...]
    required_structurally_separate_evaluators: int
    status: str
    comparison_conclusion: str
    record_fingerprint: str
    created_by: str
    created_at: datetime
    closed_by: str | None
    closed_at: datetime | None
    authority_conclusion: str = "none_granted"
    promotion_conclusion: str = "not_assessed"
    active_version_changed: bool = False
    autonomy_changed: bool = False
    permission_or_tool_access_changed: bool = False
    monetary_authority_changed: bool = False
    deployment_authorized: bool = False
    external_action_authorized: bool = False
    evaluator_independence_conclusion: str = "structural_separation_with_evidence_refs_not_independently_verified"
    reproducibility_conclusion: str = "evidence_referenced_not_recomputed"
    limitations: tuple[str, ...] = (
        "Campaign conclusions apply only to the declared comparison metrics and constraints.",
        "Candidate-author and evaluator identity evidence is recorded but its semantic independence is not independently certified by this campaign.",
        "Evaluator identity separation and evidence references do not prove model-provider or reasoning independence.",
        "Closing a campaign does not approve, promote, activate, deploy or authorize the candidate.",
    )


class ImprovementEvaluationReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_key: str
    report_key: str
    campaign_id: UUID
    evaluator_actor_type: str
    evaluator_identity: str
    evaluator_independence_group: str
    independence_evidence_reference_ids: tuple[UUID, ...]
    baseline_measurements: dict[str, float]
    candidate_measurements: dict[str, float]
    constraint_results: tuple[ImprovementEvaluationConstraintResult, ...]
    evaluation_evidence_reference_ids: tuple[UUID, ...]
    reproducibility_reference_ids: tuple[UUID, ...]
    constraints_satisfied: bool
    record_fingerprint: str
    recorded_by: str
    recorded_at: datetime
    authority_conclusion: str = "none_granted"
    promotion_conclusion: str = "not_assessed"
    active_version_changed: bool = False
    evaluator_independence_conclusion: str = "recorded_not_independently_verified"
    limitations: tuple[str, ...] = (
        "A report records comparison evidence; it is not a promotion or activation decision.",
        "The evaluator independence group is technical metadata and is not itself proof of independence.",
        "Reproducibility references point to existing evidence owners; this report does not recreate or certify their semantics.",
    )
