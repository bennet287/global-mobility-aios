from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


AUTONOMY_EVIDENCE_EVALUATION_CONTRACT_VERSION = "v1.3-i.4"
AUTONOMY_EVIDENCE_EVALUATION_POLICY_ACTIVITY_TYPE = (
    "organization.autonomy_evidence_evaluation_policy.established.v1"
)
AUTONOMY_EVIDENCE_EVALUATION_POLICY_SOURCE_TYPE = (
    "capability_autonomy_evidence_evaluation_policy"
)
AUTONOMY_EVIDENCE_EVALUATION_GOVERNANCE_SOURCE = "human_board"
AUTONOMY_EVIDENCE_EVALUATION_CONSTITUTIONAL_ACTIVITY_CLASS = "AUTHORITY"

I4_SUPPORTED_CAPABILITY = "eligibility.proposal"
I4_QUALIFICATION_CONTRACT = "governed-eligibility-canonical-effect.v1"
I4_MAX_CANDIDATE_OBSERVATIONS = 5000
I4_MAX_PROVENANCE_PAGE_SIZE = 100
I4_SUMMARY_PROVENANCE_LIMIT = 10

PROVENANCE_QUALIFIED = "QUALIFIED"
PROVENANCE_STALE_OBSERVATION = "STALE_OBSERVATION"
PROVENANCE_STALE_SOURCE = "STALE_SOURCE"
PROVENANCE_UNQUALIFIED_SOURCE = "UNQUALIFIED_SOURCE"

I4_ALWAYS_UNAVAILABLE_DERIVATIONS = (
    "freshness_compliance_rate",
    "critical_error_count",
    "sla_met_rate",
    "incident_count",
)


class AutonomyEvidenceEvaluationIntegrityError(RuntimeError):
    """Durable I.4 policy/evidence truth cannot be reconciled."""


class AutonomyEvidenceEvaluationUnsupported(RuntimeError):
    """I.4 has no accepted qualification adapter for the requested scope."""


class AutonomyEvidenceEvaluationBoundExceeded(RuntimeError):
    """The Board-authored I.4 evaluation bound would be exceeded."""


@dataclass(frozen=True, slots=True)
class AutonomyEvidenceEvaluationPolicyRevisionSnapshot:
    policy_id: UUID
    profile_id: UUID
    profile_sequence: int
    profile_record_fingerprint: str
    policy_sequence: int
    lifecycle_status: str
    qualification_contract: str
    max_observation_age_seconds: int
    max_source_age_seconds: int
    max_candidate_observations: int
    policy_reason: str
    supersedes_policy_id: UUID | None
    decision_activity_id: UUID
    decision_activity_fingerprint: str
    record_fingerprint: str
    effective_from: datetime
    created_at: datetime
    created_by: str


@dataclass(frozen=True, slots=True)
class CapabilityAutonomyEvidenceEvaluationPolicySnapshot:
    profile_id: UUID
    profile_sequence: int
    profile_record_fingerprint: str
    position_key: str
    capability_key: str
    context_scope: str
    current_policy_id: UUID
    current_policy_sequence: int
    qualification_contract: str
    max_observation_age_seconds: int
    max_source_age_seconds: int
    max_candidate_observations: int
    revisions: tuple[AutonomyEvidenceEvaluationPolicyRevisionSnapshot, ...]


@dataclass(frozen=True, slots=True)
class QualifiedAutonomyEvidenceMetricsSnapshot:
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


@dataclass(frozen=True, slots=True)
class AutonomyEvidenceEvaluationCriterionSnapshot:
    criterion_key: str
    comparison: str
    required_value: int | float
    observed_value: int | float | None
    sample_requirement: bool
    evaluable: bool
    passed: bool | None


@dataclass(frozen=True, slots=True)
class AutonomyEvidenceProvenanceSnapshot:
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


@dataclass(frozen=True, slots=True)
class CapabilityAutonomyEvidenceEvaluationSnapshot:
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
    missing_derivation_fields: tuple[str, ...]
    promotion_policy_id: UUID | None
    promotion_policy_sequence: int | None
    target_autonomy_level: str | None
    promotion_grade_ready: bool
    metrics: QualifiedAutonomyEvidenceMetricsSnapshot
    criteria: tuple[AutonomyEvidenceEvaluationCriterionSnapshot, ...]
    recent_provenance: tuple[AutonomyEvidenceProvenanceSnapshot, ...]


@dataclass(frozen=True, slots=True)
class CapabilityAutonomyEvidenceEvaluationProvenancePage:
    profile_id: UUID
    evaluation_policy_id: UUID
    evaluation_as_of: datetime
    items: tuple[AutonomyEvidenceProvenanceSnapshot, ...]
    next_cursor: str | None
    page_limit: int
