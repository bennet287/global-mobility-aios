from __future__ import annotations

from sqlmodel import Session

from app.schemas_organization_autonomy import CapabilityAutonomyProfileRevisionRead
from app.schemas_organization_autonomy_evidence import CapabilityAutonomyEvidenceProfileTransparencyRead
from app.schemas_organization_autonomy_promotion import AutonomyPromotionEligibilityTransparencyRead
from app.schemas_organization_grc_capability_review import GRCCapabilityAuthorizationReviewRead
from app.services.organization_autonomy_evidence_profile import (
    capability_autonomy_evidence_profile_snapshot,
)
from app.services.organization_autonomy_profile import capability_autonomy_profile_snapshot
from app.services.organization_autonomy_promotion_policy import (
    capability_autonomy_promotion_eligibility_snapshot,
)
from app.services.organization_command import (
    NotFound,
    OrganizationCommandContext,
    require_human,
)


def project_grc_capability_authorization_review(
    session: Session,
    context: OrganizationCommandContext,
    *,
    position_key: str,
    capability_key: str,
    context_scope: str,
) -> GRCCapabilityAuthorizationReviewRead:
    """Project canonical capability review evidence without creating authority."""

    require_human(context, admin=True)
    profile = capability_autonomy_profile_snapshot(
        session,
        tenant_key=context.tenant_key,
        position_key=position_key,
        capability_key=capability_key,
        context_scope=context_scope,
    )
    if profile is None:
        raise NotFound("capability autonomy profile was not found in this tenant")

    current = next(
        (revision for revision in profile.revisions if revision.profile_id == profile.current_profile_id),
        None,
    )
    if current is None or current.lifecycle_status != "CURRENT":
        raise RuntimeError("current capability autonomy profile revision is inconsistent")

    evidence = capability_autonomy_evidence_profile_snapshot(
        session,
        tenant_key=context.tenant_key,
        position_key=position_key,
        capability_key=capability_key,
        context_scope=context_scope,
    )
    eligibility = capability_autonomy_promotion_eligibility_snapshot(
        session,
        tenant_key=context.tenant_key,
        position_key=position_key,
        capability_key=capability_key,
        context_scope=context_scope,
    )

    return GRCCapabilityAuthorizationReviewRead(
        tenant_key=context.tenant_key,
        position_key=profile.position_key,
        capability_key=profile.capability_key,
        context_scope=profile.context_scope,
        current_profile_id=profile.current_profile_id,
        current_autonomy_level=profile.current_autonomy_level,
        board_ceiling=current.board_ceiling,
        authority_requirement=current.authority_requirement,
        risk_ceiling=current.risk_ceiling,
        evidence_policy_version=current.evidence_policy_version,
        current_profile=CapabilityAutonomyProfileRevisionRead.model_validate(current),
        evidence_profile=(
            CapabilityAutonomyEvidenceProfileTransparencyRead.model_validate(evidence)
            if evidence is not None else None
        ),
        promotion_eligibility=(
            AutonomyPromotionEligibilityTransparencyRead.model_validate(eligibility)
            if eligibility is not None else None
        ),
    )
