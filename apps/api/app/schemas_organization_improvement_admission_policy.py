from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


ImprovementAdmissionPhaseKey = Literal["phase16", "phase17", "phase19", "phase20"]
ImprovementAdmissionDisposition = Literal["required", "not_required"]
ImprovementAdmissionRiskClass = Literal["low", "medium", "high", "critical"]
ImprovementAdmissionTargetType = Literal["code_configuration"]
ImprovementAdmissionExecutionMode = Literal["shadow", "canary"]


class ImprovementAdmissionPhaseRequirementCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phase_key: ImprovementAdmissionPhaseKey
    disposition: ImprovementAdmissionDisposition
    dependency_contract_keys: list[str] = Field(default_factory=list, max_length=20)
    rationale: str = Field(min_length=1, max_length=2000)

    @model_validator(mode="after")
    def validate_disposition(self):
        if not self.rationale.strip():
            raise ValueError("phase requirement rationale is required")
        if self.disposition == "required" and not self.dependency_contract_keys:
            raise ValueError("required phase must declare at least one dependency contract key")
        if self.disposition == "not_required" and self.dependency_contract_keys:
            raise ValueError("not_required phase cannot declare dependency contract keys")
        if len(set(self.dependency_contract_keys)) != len(self.dependency_contract_keys):
            raise ValueError("dependency contract keys must be unique")
        return self


class ImprovementAdmissionDependencyPolicyCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_type: ImprovementAdmissionTargetType
    execution_mode: ImprovementAdmissionExecutionMode
    candidate_risk_class: ImprovementAdmissionRiskClass
    phase_requirements: list[ImprovementAdmissionPhaseRequirementCreate] = Field(
        min_length=4,
        max_length=4,
    )
    policy_reason: str = Field(min_length=1, max_length=4000)
    idempotency_key: str = Field(min_length=1, max_length=255)
    expected_policy_version: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_phase_coverage(self):
        phases = [item.phase_key for item in self.phase_requirements]
        required = {"phase16", "phase17", "phase19", "phase20"}
        if len(set(phases)) != len(phases) or set(phases) != required:
            raise ValueError("policy must address phase16, phase17, phase19 and phase20 exactly once")
        return self


class ImprovementAdmissionPhaseRequirementRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phase_key: ImprovementAdmissionPhaseKey
    disposition: ImprovementAdmissionDisposition
    dependency_contract_keys: tuple[str, ...]
    rationale: str


class ImprovementAdmissionDependencyPolicyRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_key: str
    target_type: ImprovementAdmissionTargetType
    execution_mode: ImprovementAdmissionExecutionMode
    candidate_risk_class: ImprovementAdmissionRiskClass
    policy_version: int
    phase_requirements: tuple[ImprovementAdmissionPhaseRequirementRead, ...]
    policy_reason: str
    supersedes_policy_id: UUID | None
    decision_activity_id: UUID
    decision_activity_fingerprint: str
    idempotency_key: str
    record_fingerprint: str
    lifecycle_status: Literal["CURRENT", "HISTORICAL"]
    created_by: str
    created_at: datetime
    authority_conclusion: str = "none_granted"
    qualification_conclusion: str = "not_evaluated"
    active_version_changed: bool = False
    autonomy_changed: bool = False
    permission_or_tool_access_changed: bool = False
    monetary_authority_changed: bool = False
    deployment_authorized: bool = False
    external_action_authorized: bool = False
    limitations: tuple[str, ...] = (
        "This policy declares which roadmap dependency contracts are required; it does not prove that any dependency is satisfied.",
        "A not_required phase is an explicit Board-authored policy disposition, not inferred absence of evidence.",
        "Required dependency keys must be resolver-backed contracts known to AIOS; caller-supplied completion booleans are not accepted.",
        "Policy establishment grants no candidate admission, promotion, autonomy, tools, credentials, budget, deployment or external-action authority.",
    )
