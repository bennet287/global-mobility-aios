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
