from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


ShadowCiEvidenceStatus = Literal["absent", "pending", "satisfied", "failed", "unknown"]
ShadowCiAggregateStatus = Literal["complete", "partial", "pending", "failed", "unknown"]
ShadowReviewStatus = Literal["absent", "incomplete", "complete", "failed", "unknown"]
ShadowAdmissionDecisionStatus = Literal["absent", "pending", "approved", "denied", "unknown"]
ShadowDependencyEvidenceStatus = Literal[
    "not_required",
    "satisfied",
    "unsatisfied",
    "pending",
    "absent",
    "failed",
    "unknown",
]


class ImprovementCodeShadowDependencyContractRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract_key: str
    evidence_status: ShadowDependencyEvidenceStatus
    reasons: tuple[str, ...] = ()


class ImprovementCodeShadowDependencyPhaseRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phase_key: str
    disposition: str
    evidence_status: ShadowDependencyEvidenceStatus
    rationale: str
    contracts: tuple[ImprovementCodeShadowDependencyContractRead, ...] = ()


class ImprovementCodeShadowCiWorkflowRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workflow_name: str
    workflow_path: str
    run_id: int | None
    run_number: int | None
    run_attempt: int | None
    status: str | None
    conclusion: str | None
    evidence_status: ShadowCiEvidenceStatus
    head_sha: str | None
    event: str | None
    html_url: str | None


class ImprovementCodeShadowCiProofRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_id: UUID
    proposal_id: UUID
    work_item_id: UUID
    candidate_version: str
    candidate_fingerprint: str
    artifact_commit_sha: str
    repository: str
    work_item_status: str
    ci_evidence_status: ShadowCiAggregateStatus
    workflows: tuple[ImprovementCodeShadowCiWorkflowRead, ...]
    shadow_execution_observed: bool
    shadow_ci_evidence_complete: bool
    review_package_id: UUID | None
    candidate_risk_class: str | None
    cross_team_review_status: ShadowReviewStatus
    admission_decision_id: UUID | None
    admission_decision_status: ShadowAdmissionDecisionStatus
    pre_dependency_admission_ready: bool
    admission_policy_id: UUID | None
    admission_policy_version: int | None
    dependency_phases: tuple[ImprovementCodeShadowDependencyPhaseRead, ...]
    roadmap_dependency_gate_status: str
    admission_blockers: tuple[str, ...]
    grsi_e_qualified: bool = False
    grsi_e_admission_conclusion: str
    cross_team_review_conclusion: str
    authority_conclusion: str = "none_granted"
    promotion_conclusion: str = "not_assessed"
    active_version_changed: bool = False
    autonomy_changed: bool = False
    permission_or_tool_access_changed: bool = False
    monetary_authority_changed: bool = False
    deployment_authorized: bool = False
    external_action_authorized: bool = False
    canary_conclusion: str = "not_assessed_target_host_acceptance_required"
    limitations: tuple[str, ...] = (
        "This projection can qualify exact non-active code/configuration shadow evidence only when current review, Decision, CI and Board-authored dependency policy requirements are all satisfied.",
        "GRSI.E shadow qualification is evidence readiness for this bounded candidate/work scope; it is not canary, promotion, activation, deployment, tool, credential, budget or external-action authority.",
        "Repository CI is shadow-style engineering evidence, not production activation, production outcome evidence, live-host canary evidence, or deployment acceptance.",
        "The GitHub Actions owner remains authoritative for workflow execution state; this projection stores no duplicate CI execution truth.",
    )
