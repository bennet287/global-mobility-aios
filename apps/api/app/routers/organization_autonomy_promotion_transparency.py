from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.core.db import get_session
from app.routers.organization_records import organization_command_context
from app.schemas_organization_autonomy_promotion import (
    AutonomyPromotionEligibilityTransparencyRead,
)
from app.services.organization_autonomy_evidence_profile import AutonomyEvidenceProfileIntegrityError
from app.services.organization_autonomy_promotion_policy import (
    AutonomyPromotionPolicyIntegrityError,
    capability_autonomy_promotion_eligibility_snapshot,
)
from app.services.organization_command import OrganizationCommandContext, OrganizationCommandError


router = APIRouter(
    prefix="/api/v1/organization/transparency/autonomy",
    tags=["organization-autonomy-promotion-v1.3-i3"],
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Board transparency access required"},
        404: {"description": "Promotion eligibility resource not found"},
        409: {"description": "Durable autonomy evidence or policy data is inconsistent"},
    },
)


def _require_board(context: OrganizationCommandContext) -> None:
    if context.role != "admin" or context.position_key != "board":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Board transparency access is not permitted.",
        )


@router.get(
    "/profiles/{position_key}/{capability_key}/promotion-eligibility",
    response_model=AutonomyPromotionEligibilityTransparencyRead,
)
def read_capability_autonomy_promotion_eligibility(
    position_key: str,
    capability_key: str,
    context_scope: str = Query(..., min_length=1),
    context: OrganizationCommandContext = Depends(organization_command_context),
    session: Session = Depends(get_session),
) -> AutonomyPromotionEligibilityTransparencyRead:
    """Return deterministic Board promotion eligibility without changing autonomy."""

    _require_board(context)
    try:
        snapshot = capability_autonomy_promotion_eligibility_snapshot(
            session,
            tenant_key=context.tenant_key,
            position_key=position_key,
            capability_key=capability_key,
            context_scope=context_scope,
        )
        if snapshot is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization transparency resource not found.",
            )
        return AutonomyPromotionEligibilityTransparencyRead.model_validate(snapshot)
    except HTTPException:
        raise
    except (
        AutonomyPromotionPolicyIntegrityError,
        AutonomyEvidenceProfileIntegrityError,
        OrganizationCommandError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Organization transparency data is inconsistent.",
        ) from exc
