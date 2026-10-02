from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


ImprovementRiskClass = Literal["low", "medium", "high", "critical"]
ImprovementReviewKind = Literal["security_red_team", "qa", "domain", "platform_sre", "governance"]
ImprovementReviewArtifactType = Literal[
    "human_action_request",
    "human_action",
    "decision",
    "work_item",
    "blocker",
]
ImprovementReviewEvidenceStatus = Literal["absent", "pending", "satisfied", "failed", "unknown"]


class ImprovementReviewBindingCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_kind: ImprovementReviewKind
    artifact_type: ImprovementReviewArtifactType
    artifact_id: UUID
    reviewer_position_key: str = Field(min_length=1, max_length=255)


class ImprovementReviewPackageCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    package_key: str = Field(min_length=1, max_length=255)
    package_version: int = Field(ge=1)
    candidate_id: UUID
    evaluation_campaign_id: UUID
    risk_class: ImprovementRiskClass
    risk_basis_reference_ids: list[UUID] = Field(min_length=1, max_length=100)
    review_bindings: list[ImprovementReviewBindingCreate] = Field(default_factory=list, max_length=100)
    supersedes_package_id: UUID | None = None


class ImprovementReviewArtifactRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_kind: ImprovementReviewKind
    artifact_type: ImprovementReviewArtifactType
    artifact_id: UUID
    reviewer_position_key: str
    canonical_status: str
    evidence_status: ImprovementReviewEvidenceStatus
    evidence_reference_ids: tuple[UUID, ...]


class ImprovementReviewRequirementRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_kind: ImprovementReviewKind
    status: ImprovementReviewEvidenceStatus
    artifacts: tuple[ImprovementReviewArtifactRead, ...]


class ImprovementReviewPackageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_key: str
    package_key: str
    package_version: int
    candidate_id: UUID
    proposal_id: UUID
    evaluation_campaign_id: UUID
    candidate_fingerprint: str
    risk_class: ImprovementRiskClass
    risk_basis_reference_ids: tuple[UUID, ...]
    review_policy_key: str
    review_policy_version: int
    review_policy_fingerprint: str
    required_review_kinds: tuple[ImprovementReviewKind, ...]
    review_requirements: tuple[ImprovementReviewRequirementRead, ...]
    evaluation_status: ImprovementReviewEvidenceStatus
    supersedes_package_id: UUID | None
    is_current: bool
    promotion_evidence_complete_for_decision: bool
    record_fingerprint: str
    created_by: str
    created_at: datetime
    authority_conclusion: str = "none_granted"
    authorization_conclusion: str = "not_assessed"
    promotion_conclusion: str = "not_authorized"
    active_version_changed: bool = False
    autonomy_changed: bool = False
    permission_or_tool_access_changed: bool = False
    monetary_authority_changed: bool = False
    deployment_authorized: bool = False
    external_action_authorized: bool = False
    limitations: tuple[str, ...] = (
        "Review-package completeness is evidence readiness only; it is not an approval, promotion, activation or deployment decision.",
        "Underlying review outcomes remain owned by canonical HumanAction, Decision, WorkItem and Blocker records.",
        "A satisfied review requirement means an explicit canonical disposition was found; neutral completed work is reported as unknown rather than treated as approval.",
        "Risk classification is recorded with evidence references under the declared review policy; this package does not independently certify the correctness of that classification.",
        "Even when promotion evidence is complete, GRSI.F must still use the authorized decision and artifact-specific promotion/release boundary.",
    )
