from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AutonomyTransparencyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CapabilityAutonomyEvidenceRead(AutonomyTransparencyRead):
    evidence_sequence: int
    source_activity_id: UUID
    source_activity_fingerprint: str
    record_fingerprint: str


class CapabilityAutonomyProfileRevisionRead(AutonomyTransparencyRead):
    profile_id: UUID
    profile_sequence: int
    lifecycle_status: str
    autonomy_level: str
    board_ceiling: str
    authority_requirement: str
    risk_ceiling: str
    evidence_policy_version: str
    governance_source: str
    decision_activity_id: UUID
    supersedes_profile_id: UUID | None
    record_fingerprint: str
    effective_from: datetime
    created_at: datetime
    evidence: list[CapabilityAutonomyEvidenceRead]


class CapabilityAutonomyProfileTransparencyRead(AutonomyTransparencyRead):
    position_key: str
    capability_key: str
    context_scope: str
    current_profile_id: UUID
    current_autonomy_level: str
    revisions: list[CapabilityAutonomyProfileRevisionRead]
