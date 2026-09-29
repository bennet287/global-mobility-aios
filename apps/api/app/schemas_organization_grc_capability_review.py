from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel

from app.schemas_organization_autonomy import CapabilityAutonomyProfileRevisionRead
from app.schemas_organization_autonomy_evidence import CapabilityAutonomyEvidenceProfileTransparencyRead
from app.schemas_organization_autonomy_promotion import AutonomyPromotionEligibilityTransparencyRead


class GRCCapabilityAuthorizationReviewRead(BaseModel):
    schema_version: str = "grc-capability-authorization-review-v1"
    tenant_key: str
    position_key: str
    capability_key: str
    context_scope: str
    current_profile_id: UUID
    current_autonomy_level: str
    board_ceiling: str
    authority_requirement: str
    risk_ceiling: str
    evidence_policy_version: str
    current_profile: CapabilityAutonomyProfileRevisionRead
    evidence_profile: CapabilityAutonomyEvidenceProfileTransparencyRead | None = None
    promotion_eligibility: AutonomyPromotionEligibilityTransparencyRead | None = None
    authorization_conclusion: str = "not_assessed"
    limitations: tuple[str, ...] = (
        "Capability autonomy is Board-governed operating scope; it is not executable permission or tool authority.",
        "Promotion eligibility is review evidence only and does not promote, authorize, dispatch, or execute a capability.",
        "Absence of shadow evidence or promotion policy is reported as absence, not as approval or denial.",
        "This projection does not prove that a governed runtime allowance is consumed at an agent-to-tool execution boundary.",
    )
