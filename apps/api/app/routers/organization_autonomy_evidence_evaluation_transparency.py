from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.core.db import get_session
from app.models.domain import now_utc
from app.routers.organization_records import organization_command_context
from app.schemas_organization_autonomy_evidence_evaluation import (
    CapabilityAutonomyEvidenceEvaluationProvenancePageRead,
    CapabilityAutonomyEvidenceEvaluationTransparencyRead,
)
from app.services.organization_autonomy_evidence_evaluation import (
    I4_MAX_PROVENANCE_PAGE_SIZE,
    AutonomyEvidenceEvaluationBoundExceeded,
    AutonomyEvidenceEvaluationIntegrityError,
    AutonomyEvidenceEvaluationUnsupported,
    capability_autonomy_evidence_evaluation_provenance_page,
    capability_autonomy_evidence_evaluation_snapshot,
)
from app.services.organization_autonomy_evidence_profile import AutonomyEvidenceProfileIntegrityError
from app.services.organization_autonomy_promotion_policy import AutonomyPromotionPolicyIntegrityError
from app.services.organization_command import OrganizationCommandContext, OrganizationCommandError


router = APIRouter(
    prefix="/api/v1/organization/transparency/autonomy",
    tags=["organization-autonomy-evidence-evaluation-v1.3-i4"],
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Board transparency access required"},
        404: {"description": "Qualified autonomy evidence resource not found"},
        409: {"description": "Qualified autonomy evidence cannot be evaluated safely"},
    },
)


def _require_board(context: OrganizationCommandContext) -> None:
    if context.role != "admin" or context.position_key != "board":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Board transparency access is not permitted.",
        )


@router.get(
    "/profiles/{position_key}/{capability_key}/evidence-evaluation",
    response_model=CapabilityAutonomyEvidenceEvaluationTransparencyRead,
)
def read_capability_autonomy_evidence_evaluation(
    position_key: str,
    capability_key: str,
    context_scope: str = Query(..., min_length=1),
    context: OrganizationCommandContext = Depends(organization_command_context),
    session: Session = Depends(get_session),
) -> CapabilityAutonomyEvidenceEvaluationTransparencyRead:
    """Return the bounded I.4 promotion-grade evidence projection at server time."""

    _require_board(context)
    try:
        snapshot = capability_autonomy_evidence_evaluation_snapshot(
            session,
            tenant_key=context.tenant_key,
            position_key=position_key,
            capability_key=capability_key,
            context_scope=context_scope,
            evaluation_as_of=now_utc(),
        )
        if snapshot is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization transparency resource not found.",
            )
        return CapabilityAutonomyEvidenceEvaluationTransparencyRead.model_validate(snapshot)
    except HTTPException:
        raise
    except (
        AutonomyEvidenceEvaluationIntegrityError,
        AutonomyEvidenceEvaluationBoundExceeded,
        AutonomyEvidenceEvaluationUnsupported,
        AutonomyEvidenceProfileIntegrityError,
        AutonomyPromotionPolicyIntegrityError,
        OrganizationCommandError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Organization transparency data cannot be evaluated safely.",
        ) from exc


@router.get(
    "/profiles/{position_key}/{capability_key}/evidence-evaluation/provenance",
    response_model=CapabilityAutonomyEvidenceEvaluationProvenancePageRead,
)
def read_capability_autonomy_evidence_evaluation_provenance(
    position_key: str,
    capability_key: str,
    context_scope: str = Query(..., min_length=1),
    limit: int = Query(50, ge=1, le=I4_MAX_PROVENANCE_PAGE_SIZE),
    cursor: str | None = Query(default=None, min_length=1),
    context: OrganizationCommandContext = Depends(organization_command_context),
    session: Session = Depends(get_session),
) -> CapabilityAutonomyEvidenceEvaluationProvenancePageRead:
    """Return stable, capped, newest-first I.4 evidence provenance."""

    _require_board(context)
    try:
        page = capability_autonomy_evidence_evaluation_provenance_page(
            session,
            tenant_key=context.tenant_key,
            position_key=position_key,
            capability_key=capability_key,
            context_scope=context_scope,
            page_limit=limit,
            cursor=cursor,
            evaluation_as_of=None if cursor else now_utc(),
        )
        if page is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization transparency resource not found.",
            )
        return CapabilityAutonomyEvidenceEvaluationProvenancePageRead.model_validate(page)
    except HTTPException:
        raise
    except (
        AutonomyEvidenceEvaluationIntegrityError,
        AutonomyEvidenceEvaluationBoundExceeded,
        AutonomyEvidenceEvaluationUnsupported,
        AutonomyEvidenceProfileIntegrityError,
        AutonomyPromotionPolicyIntegrityError,
        OrganizationCommandError,
        ValueError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Organization transparency data cannot be evaluated safely.",
        ) from exc
