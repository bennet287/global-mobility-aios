from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


DeploymentAcceptanceEvidenceStatus = Literal[
    "absent",
    "partial",
    "satisfied",
    "failed",
    "blocked",
    "unknown",
]
DeploymentAcceptanceGateStatus = Literal[
    "absent",
    "satisfied",
    "failed",
    "blocked",
    "unknown",
]


class ProductionDeploymentAcceptanceRunCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    deployment_run_key: str = Field(min_length=1, max_length=255)
    environment_key: str = Field(min_length=1, max_length=255)
    target_environment_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    release_commit_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    release_configuration_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    rollback_release_commit_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    rollback_configuration_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    work_item_id: UUID
    admission_decision_id: UUID
    reason: str = Field(min_length=1, max_length=4000)


class ProductionDeploymentAcceptanceGateRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    gate_key: str
    gate_version: int
    label: str
    status: DeploymentAcceptanceGateStatus
    receipt_id: UUID | None
    evidence_digest: str | None
    evidence_reference: str | None
    redacted_details: dict[str, Any]
    observed_at: datetime | None


class ProductionDeploymentAcceptanceRunRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    tenant_key: str
    deployment_run_key: str
    execution_mode: Literal["canary"]
    environment_key: str
    environment_class: Literal["canary"]
    target_environment_fingerprint: str
    environment_constraints: dict[str, Any]
    release_commit_sha: str
    release_configuration_fingerprint: str
    rollback_release_commit_sha: str
    rollback_configuration_fingerprint: str
    acceptance_contract_key: str
    acceptance_contract_version: int
    acceptance_contract_fingerprint: str
    work_item_id: UUID
    admission_decision_id: UUID
    reason: str
    record_fingerprint: str
    prepared_activity_id: UUID
    prepared_activity_fingerprint: str
    created_by: str
    created_at: datetime
    gates: tuple[ProductionDeploymentAcceptanceGateRead, ...]
    deployment_observed: bool
    checks_complete: bool
    canary_evidence_status: DeploymentAcceptanceEvidenceStatus
    canary_evidence_satisfied: bool
    authority_conclusion: str = "none_granted"
    deployment_authorized_by_receipt: bool = False
    promotion_authorized: bool = False
    production_ready: bool = False
    active_version_changed: bool = False
    real_client_data_admitted: bool = False
    consequential_external_actions_enabled: bool = False
    paid_autonomous_execution_enabled: bool = False
    limitations: tuple[str, ...] = (
        "A prepared run pins intended release/environment/rollback identity only; it is not evidence that deployment occurred.",
        "Foundation v1 exposes no public endpoint for creating check receipts or marking a gate passed.",
        "Canary evidence can be satisfied only by immutable target-host receipts for every versioned acceptance gate.",
        "A satisfied canary receipt never grants promotion, production readiness, real-client-data admission, external-action authority, autonomy, tools, credentials or budget.",
    )
