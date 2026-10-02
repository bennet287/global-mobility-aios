from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


ShadowCiEvidenceStatus = Literal["absent", "pending", "satisfied", "failed", "unknown"]
ShadowCiAggregateStatus = Literal["complete", "partial", "pending", "failed", "unknown"]


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
    grsi_e_qualified: bool = False
    grsi_e_admission_conclusion: str = "not_assessed_existing_authority_and_dependency_gates_required"
    cross_team_review_conclusion: str = "not_assessed_use_grsi_d"
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
        "This projection verifies repository CI evidence for the exact non-active code/configuration candidate commit; it does not authorize or admit GRSI.E execution.",
        "A linked WorkItem proves bounded experiment identity only. Existing Decision/HumanAction and roadmap risk-class dependency gates remain separate authority prerequisites.",
        "Repository CI is shadow-style engineering evidence, not production activation, production outcome evidence, live-host canary evidence, or deployment acceptance.",
        "The GitHub Actions owner remains authoritative for workflow execution state; this projection stores no duplicate CI execution truth.",
    )
