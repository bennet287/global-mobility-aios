from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas_organization_autonomy_evidence import CapabilityAutonomyEvidenceProfileTransparencyRead


class AutonomyPromotionTransparencyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class AutonomyPromotionCriterionRead(AutonomyPromotionTransparencyRead):
    criterion_key: str
    comparison: str
    required_value: int | float
    observed_value: int | float | None
    sample_requirement: bool
    evaluable: bool
    passed: bool | None


class AutonomyPromotionEligibilityTransparencyRead(AutonomyPromotionTransparencyRead):
    profile_id: UUID
    profile_sequence: int
    position_key: str
    capability_key: str
    context_scope: str
    current_autonomy_level: str
    board_ceiling: str
    evidence_policy_version: str
    policy_id: UUID
    policy_sequence: int
    target_autonomy_level: str
    eligibility_state: str
    criteria: list[AutonomyPromotionCriterionRead]
    evidence_profile: CapabilityAutonomyEvidenceProfileTransparencyRead
