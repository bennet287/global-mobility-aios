from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AutonomyEvidenceEvaluationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class AutonomyEvidenceEvaluationCriterionRead(AutonomyEvidenceEvaluationRead):
    criterion_key: str
    comparison: str
    required_value: int | float
    observed_value: int | float | None
    sample_requirement: bool
    evaluable: bool
    passed: bool | None


class QualifiedAutonomyEvidenceMetricsRead(AutonomyEvidenceEvaluationRead):
    qualifying_execution_volume: int
    evidence_grounded_count: int
    evidence_grounding_rate: float | None
    human_accepted_count: int
    human_modified_count: int
    human_rejected_count: int
    human_not_reviewed_count: int
    human_reviewed_count: int
    human_acceptance_rate: float | None
    human_modification_rate: float | None
    human_rejection_rate: float | None
    verifier_contradiction_count: int
    verifier_contradiction_rate: float | None
    policy_compliant_count: int
    policy_compliance_rate: float | None
    freshness_compliance_rate: float | None
    critical_error_count: int | None
    recovery_applicable_count: int | None
    recovery_success_rate: float | None
    sla_met_rate: float | None
    incident_count: int | None


class AutonomyEvidenceProvenanceRead(AutonomyEvidenceEvaluationRead):
    observation_id: UUID
    source_activity_id: UUID
    source_activity_type: str
    observation_created_at: datetime
    source_occurred_at: datetime
    disposition: str
    canonical_revision_id: UUID | None
    effect_fingerprint: str | None
    human_review_outcome: str | None
    evidence_grounded: bool | None
    verifier_contradiction: bool | None
    policy_compliant: bool | None


class CapabilityAutonomyEvidenceEvaluationTransparencyRead(AutonomyEvidenceEvaluationRead):
    profile_id: UUID
    profile_sequence: int
    profile_record_fingerprint: str
    position_key: str
    capability_key: str
    context_scope: str
    current_autonomy_level: str
    board_ceiling: str
    evidence_policy_version: str
    evaluation_policy_id: UUID
    evaluation_policy_sequence: int
    qualification_contract: str
    evaluation_as_of: datetime
    observation_cutoff: datetime
    source_cutoff: datetime
    candidate_count: int
    qualified_count: int
    excluded_stale_observation_count: int
    excluded_stale_source_count: int
    excluded_unqualified_source_count: int
    missing_derivation_fields: list[str]
    promotion_policy_id: UUID | None
    promotion_policy_sequence: int | None
    target_autonomy_level: str | None
    promotion_grade_ready: bool
    metrics: QualifiedAutonomyEvidenceMetricsRead
    criteria: list[AutonomyEvidenceEvaluationCriterionRead]
    recent_provenance: list[AutonomyEvidenceProvenanceRead]


class CapabilityAutonomyEvidenceEvaluationProvenancePageRead(AutonomyEvidenceEvaluationRead):
    profile_id: UUID
    evaluation_policy_id: UUID
    evaluation_as_of: datetime
    items: list[AutonomyEvidenceProvenanceRead]
    next_cursor: str | None
    page_limit: int
