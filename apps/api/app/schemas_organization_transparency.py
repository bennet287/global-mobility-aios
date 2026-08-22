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
