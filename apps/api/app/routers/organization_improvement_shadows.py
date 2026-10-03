from __future__ import annotations

from typing import Callable, TypeVar
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlmodel import Session

from app.core.db import get_session
from app.routers.organization_records import organization_command_context
from app.schemas_organization_improvement_shadow import (
    ImprovementCodeCanaryEvidenceRead,
    ImprovementCodeShadowCiProofRead,
)
from app.services.organization_command import (
    AuthorityDenied,
    InvalidHumanActor,
    InvalidReference,
    InvalidTransition,
    NotFound,
    OrganizationCommandContext,
    OrganizationCommandError,
    TenantMismatch,
)
from app.services.organization_improvement_shadow import (
    ShadowCiProofUnavailable,
    project_code_canary_evidence,
    project_code_shadow_ci_proof,
)


router = APIRouter(
    prefix="/shadow",
    tags=["organization-grsi-shadow-code-ci-v1"],
)
ResultT = TypeVar("ResultT")


def _http_error(exc: OrganizationCommandError) -> HTTPException:
    if isinstance(exc, ShadowCiProofUnavailable):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="External shadow CI evidence is temporarily unavailable.",
        )
    if isinstance(exc, (TenantMismatch, NotFound)):
        return HTTPException(status_code=404, detail="Organization resource not found.")
    if isinstance(exc, (InvalidHumanActor, AuthorityDenied)):
        return HTTPException(status_code=403, detail="Organization action is not permitted.")
    if isinstance(exc, InvalidTransition):
        return HTTPException(status_code=409, detail="Improvement shadow proof conflicts with current state.")
    if isinstance(exc, InvalidReference):
        return HTTPException(status_code=422, detail="Improvement shadow proof reference is invalid.")
    return HTTPException(status_code=400, detail="Improvement shadow proof was rejected.")


def _command(call: Callable[[], ResultT]) -> ResultT:
    try:
        return call()
    except OrganizationCommandError as exc:
        raise _http_error(exc) from exc


def _no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"


@router.get(
    "/code-ci/candidates/{candidate_id}",
    response_model=ImprovementCodeShadowCiProofRead,
)
def get_code_shadow_ci_proof_endpoint(
    candidate_id: UUID,
    response: Response,
    work_item_id: UUID = Query(...),
    context: OrganizationCommandContext = Depends(organization_command_context),
    session: Session = Depends(get_session),
) -> ImprovementCodeShadowCiProofRead:
    _no_store(response)
    return _command(
        lambda: project_code_shadow_ci_proof(
            session,
            context,
            candidate_id=candidate_id,
            work_item_id=work_item_id,
        )
    )

@router.get(
    "/code-canary/candidates/{candidate_id}",
    response_model=ImprovementCodeCanaryEvidenceRead,
)
def get_code_canary_evidence_endpoint(
    candidate_id: UUID,
    response: Response,
    shadow_work_item_id: UUID = Query(...),
    deployment_run_id: UUID = Query(...),
    context: OrganizationCommandContext = Depends(organization_command_context),
    session: Session = Depends(get_session),
) -> ImprovementCodeCanaryEvidenceRead:
    _no_store(response)
    return _command(
        lambda: project_code_canary_evidence(
            session,
            context,
            candidate_id=candidate_id,
            shadow_work_item_id=shadow_work_item_id,
            deployment_run_id=deployment_run_id,
        )
    )
