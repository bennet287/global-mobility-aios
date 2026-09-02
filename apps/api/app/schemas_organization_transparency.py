from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TransparencyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TransparencyRecordRead(TransparencyRead):
    activity_id: UUID
    role: str
    physical_activity_class: str
    constitutional_activity_class: str | None
    board_inspectable: bool
    requires_durable_record: bool | None
    requires_full_lineage: bool | None
    may_compact_after_policy_window: bool | None
    activity_type: str
    title: str
    summary: str
    actor_type: str
    actor_id: str
    department: str | None
    position_key: str | None
    authority_level: str | None
    source_object_type: str
    source_object_id: str
    source_object_version: str | None
    work_item_id: UUID | None
    trace_id: str | None
    causation_activity_id: UUID | None
    occurred_at: datetime


class GovernanceDecisionRead(TransparencyRead):
    activity_id: UUID
    trace_id: str
    action_type: str
    capability: str
    outcome: str
    reason: str
    effective_risk_tier: str
    consequence_class: str
    human_review_reason: str | None
    post_review_required: bool
    constitutional_activity_class: str
    actor_type: str
    actor_id: str
    department: str | None
    position_key: str | None
    authority_level: str | None
    work_item_id: UUID | None
    source_object_type: str
    source_object_id: str
    source_object_version: str | None
    action_fingerprint: str
    idempotency_key: str
    occurred_at: datetime


class GovernedTransparencyTraceRead(TransparencyRead):
    trace_id: str
    board_inspectable: bool
    governance: GovernanceDecisionRead
    records: list[TransparencyRecordRead]


class WorkItemTransparencyRead(TransparencyRead):
    work_item_id: UUID
    records: list[TransparencyRecordRead]


class AustriaLiveRuntimeQualityRead(TransparencyRead):
    contract_version: str
    execution_mode: str
    provider_outcome: str
    configured_provider: str | None
    configured_model: str | None
    response_provider: str | None
    response_model: str | None
    configured_runtime_matches_binding: bool | None
    provider_egress_occurred: bool | None
    fallback_to_template: bool
    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None
    estimated_cost_usd: float | None
    grounding_state: str
    evidence_ref_count: int
    verified_rule_ref_count: int
    source_snapshot_ref_count: int
    fresh_retrieval_provenance_present: bool
    provider_model_authority: bool
    warnings: list[str]


class AustriaLiveSpecialistRead(TransparencyRead):
    position_key: str
    work_item_id: UUID
    status: str
    evidence_valid: bool
    evidence_reason: str | None
    action_output_id: UUID | None
    execution_attempt_id: UUID | None
    agent_run_id: UUID | None
    context_hash: str | None
    runtime_binding_hash: str | None
    latency_ms: int | None
    retry_count: int | None
    confidence: float | None
    provider_model_authority: bool
    external_action_authorized: bool
    runtime_quality: AustriaLiveRuntimeQualityRead | None = None


class AustriaLiveBlockerRead(TransparencyRead):
    blocker_id: UUID
    work_item_id: UUID | None
    blocker_type: str
    severity: str
    status: str
    title: str
    description: str
    accountable_position_key: str | None
    requires_human_action: bool
    created_at: datetime


class AustriaOwnerSynthesisRead(TransparencyRead):
    action_output_id: UUID
    activity_id: UUID
    disposition: str
    recommendation: str
    confidence: float
    total_latency_ms: int
    max_latency_ms: int
    total_retry_count: int
    external_action_authorized: bool
    human_review_required: bool
    completed_at: datetime | None


class AustriaLiveOrganizationSnapshotRead(TransparencyRead):
    generated_at: datetime
    root_work_item_id: UUID
    objective_key: str
    owner_position_key: str
    root_status: str
    cycle_status: str
    owner_synthesis_state: str
    ready_for_owner_synthesis: bool
    readiness_reasons: list[str]
    authority_level: str
    authority_posture: str
    autonomy_profile_state: str | None
    provider_model_authority: bool
    external_action_authorized: bool
    specialist_outputs: list[AustriaLiveSpecialistRead]
    owner_synthesis: AustriaOwnerSynthesisRead | None
    blockers: list[AustriaLiveBlockerRead]
    total_latency_ms: int
    max_latency_ms: int
    total_retry_count: int
    activity_count: int
    activities: list[TransparencyRecordRead]
    domain_evidence_refs: list[str]
    verified_rule_refs: list[str]


class AustriaLiveOrganizationLatestRead(TransparencyRead):
    established: bool
    snapshot: AustriaLiveOrganizationSnapshotRead | None


class LivingSceneEmployeeRead(TransparencyRead):
    position_key: str
    title: str
    department: str
    reports_to_position_key: str | None
    authority_level: str
    organization_status: str
    work_item_id: UUID | None
    work_status: str | None
    semantic_state: str
    presence_state: str
    state_reason: str


class LivingSceneDepartmentRead(TransparencyRead):
    department_key: str
    label: str
    employee_count: int
    work_item_count: int
    active_blocker_count: int
    canonical_basis: str


class LivingSceneMissionRead(TransparencyRead):
    mission_key: str
    objective_key: str
    root_work_item_id: UUID
    title: str
    state: str
    phase_key: str | None
    participant_position_keys: list[str]
    work_item_ids: list[UUID]
    blocker_count: int
    decision_count: int
    projection_only: bool
    canonical_basis: str


class LivingSceneConversationRead(TransparencyRead):
    conversation_id: str
    participant_position_keys: list[str]
    work_item_id: UUID
    status: str
    summary: str
    opened_activity_id: UUID
    latest_activity_id: UUID
    opened_at: datetime
    lifecycle_at: datetime
    authority_effect: str
    transcript_persisted: bool
    canonical_basis: str


class LivingSceneHandoffRead(TransparencyRead):
    activity_id: UUID
    work_item_id: UUID
    previous_position_key: str
    assigned_position_key: str
    status: str
    occurred_at: datetime
    causation_activity_id: UUID | None
    canonical_basis: str


class LivingSceneIncidentRead(TransparencyRead):
    incident_id: str
    title: str
    severity: str
    status: str
    work_item_id: UUID | None


class LivingSceneSmartObjectRead(TransparencyRead):
    object_key: str
    object_type: str
    label: str
    state: str
    metric_label: str
    metric_value: int
    projection_only: bool
    canonical_basis: str


class LivingSceneCoverageRead(TransparencyRead):
    departments: str
    missions: str
    conversations: str
    handoffs: str
    incidents: str
    smart_objects: str
    presence: str


class LivingSceneWorkItemRead(TransparencyRead):
    work_item_id: UUID
    parent_work_item_id: UUID | None
    title: str
    objective_key: str | None
    phase_key: str | None
    status: str
    priority: str
    risk_level: str
    assigned_position_key: str
    department: str
    authority_level: str


class LivingSceneBlockerRead(TransparencyRead):
    blocker_id: UUID
    work_item_id: UUID | None
    title: str
    severity: str
    status: str
    requires_human_action: bool


class LivingSceneDecisionRead(TransparencyRead):
    decision_id: UUID
    decision_key: str
    title: str
    status: str
    authority_level: str
    decision_owner_position: str
    work_item_id: UUID | None
    supersedes_decision_id: UUID | None
    superseded_by_decision_id: UUID | None
    is_current: bool
    decided_at: datetime | None


class LivingSceneRoomRead(TransparencyRead):
    room_key: str
    room_type: str
    label: str
    state: str
    metric_label: str
    metric_value: int
    projection_only: bool
    canonical_basis: str


class LivingSceneRelationshipRead(TransparencyRead):
    relationship_key: str
    relationship_type: str
    source_type: str
    source_id: str
    target_type: str
    target_id: str
    canonical_basis: str


class LivingSceneDeterministicPlaneRead(TransparencyRead):
    canonical_projection: bool
    authoritative: bool
    departments: list[LivingSceneDepartmentRead]
    missions: list[LivingSceneMissionRead]
    employees: list[LivingSceneEmployeeRead]
    work_items: list[LivingSceneWorkItemRead]
    conversations: list[LivingSceneConversationRead]
    handoffs: list[LivingSceneHandoffRead]
    blockers: list[LivingSceneBlockerRead]
    decisions: list[LivingSceneDecisionRead]
    incidents: list[LivingSceneIncidentRead]
    smart_objects: list[LivingSceneSmartObjectRead]
    rooms: list[LivingSceneRoomRead]
    relationships: list[LivingSceneRelationshipRead]


class LivingSceneNonCanonicalPlaneRead(TransparencyRead):
    enabled: bool
    canonical_projection: bool
    authoritative: bool
    status: str
    items: list[dict[str, object]]


class LivingSceneTruthPostureRead(TransparencyRead):
    canonical_authority: str
    scene_authoritative: bool
    renderer_authoritative: bool
    prediction_authoritative: bool
    environmental_authoritative: bool
    scene_mutations_allowed: bool


class LivingOrganizationSceneRead(TransparencyRead):
    contract_version: str
    generated_at: datetime
    scope: str
    root_work_item_id: UUID
    objective_key: str
    coverage: LivingSceneCoverageRead
    deterministic: LivingSceneDeterministicPlaneRead
    predictive: LivingSceneNonCanonicalPlaneRead
    environmental: LivingSceneNonCanonicalPlaneRead
    truth: LivingSceneTruthPostureRead


class LivingOrganizationSceneLatestRead(TransparencyRead):
    established: bool
    scene: LivingOrganizationSceneRead | None
