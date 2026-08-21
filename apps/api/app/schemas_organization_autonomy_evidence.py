from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AutonomyEvidenceObservationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    observation_id: UUID
    source_activity_id: UUID
    source_activity_fingerprint: str
    human_review_outcome: str
    evidence_grounded: bool
    verifier_contradiction: bool
    policy_compliant: bool
    freshness_compliant: bool
    critical_error: bool
    recovery_outcome: str
    sla_met: bool
    incident_count: int
    idempotency_key: str
    record_fingerprint: str
    created_by_actor_type: str
    created_by_actor_key: str
    created_at: datetime


class AutonomyEvidenceMetricsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    qualifying_execution_volume: int
    evidence_grounded_count: int
    evidence_grounding_rate: float | None
    human_accepted_count: int
    human_modified_count: int
    human_rejected_count: int
    human_not_reviewed_count: int
    human_acceptance_rate: float | None
    human_modification_rate: float | None
    human_rejection_rate: float | None
    verifier_contradiction_count: int
    verifier_contradiction_rate: float | None
    policy_compliant_count: int
    policy_compliance_rate: float | None
    freshness_compliant_count: int
    freshness_compliance_rate: float | None
    critical_error_count: int
    critical_error_rate: float | None
    recovery_applicable_count: int
    recovery_succeeded_count: int
    recovery_failed_count: int
    recovery_success_rate: float | None
    sla_met_count: int
    sla_met_rate: float | None
    incident_count: int


class CapabilityAutonomyEvidenceProfileTransparencyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    profile_id: UUID
    position_key: str
    capability_key: str
    context_scope: str
    profile_sequence: int
    current_autonomy_level: str
    board_ceiling: str
    evidence_policy_version: str
    metrics: AutonomyEvidenceMetricsRead
    observations: list[AutonomyEvidenceObservationRead]
