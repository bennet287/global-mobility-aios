from __future__ import annotations

from typing import Callable, TypeVar
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlmodel import Session

from app.core.db import get_session
from app.routers.organization_records import organization_command_context
from app.schemas_organization_improvement_lineage import (
    ImprovementCandidateCreate,
    ImprovementCandidateRead,
    ImprovementProposalCreate,
    ImprovementProposalRead,
    ImprovementWithdrawal,
)
from app.services.organization_command import (
    AuthorityDenied,
    IdempotencyConflict,
    InvalidHumanActor,
    InvalidReference,
    InvalidTransition,
    NotFound,
    OrganizationCommandContext,
    OrganizationCommandError,
    TenantMismatch,
)
from app.services.organization_improvement_lineage import (
    create_improvement_candidate,
    create_improvement_proposal,
    list_improvement_candidates,
    list_improvement_proposals,
    project_improvement_candidate,
    project_improvement_proposal,
    withdraw_improvement_candidate,
    withdraw_improvement_proposal,
)


router = APIRouter(
    prefix="/api/v1/organization/improvements",
    tags=["organization-grsi-improvement-lineage-v1"],
    responses={
        401: {"description": "Authentication required."},
        403: {"description": "Human admin authority is required."},
        404: {"description": "Organization resource not found."},
        409: {"description": "Improvement lineage conflicts with current state."},
        422: {"description": "Improvement lineage reference is invalid."},
    },
)


ResultT = TypeVar("ResultT")


def _http_error(exc: OrganizationCommandError) -> HTTPException:
    if isinstance(exc, (TenantMismatch, NotFound)):
        return HTTPException(status_code=404, detail="Organization resource not found.")
    if isinstance(exc, (InvalidHumanActor, AuthorityDenied)):
        return HTTPException(status_code=403, detail="Organization action is not permitted.")
    if isinstance(exc, (IdempotencyConflict, InvalidTransition)):
        return HTTPException(status_code=409, detail="Improvement lineage conflicts with current state.")
    if isinstance(exc, InvalidReference):
        return HTTPException(status_code=422, detail="Improvement lineage reference is invalid.")
    return HTTPException(status_code=400, detail="Improvement lineage command was rejected.")


def _command(call: Callable[[], ResultT]) -> ResultT:
    try:
        return call()
    except OrganizationCommandError as exc:
        raise _http_error(exc) from exc


def _no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"


@router.post(
    "/proposals",
    response_model=ImprovementProposalRead,
    status_code=status.HTTP_201_CREATED,
)
def create_proposal_endpoint(
    payload: ImprovementProposalCreate,
    response: Response,
    context: OrganizationCommandContext = Depends(organization_command_context),
    session: Session = Depends(get_session),
) -> ImprovementProposalRead:
    _no_store(response)
    row = _command(
        lambda: create_improvement_proposal(
            session,
            context,
            **payload.model_dump(),
        )
    )
    return project_improvement_proposal(row)


@router.get("/proposals", response_model=tuple[ImprovementProposalRead, ...])
def list_proposals_endpoint(
    response: Response,
    context: OrganizationCommandContext = Depends(organization_command_context),
    session: Session = Depends(get_session),
) -> tuple[ImprovementProposalRead, ...]:
    _no_store(response)
    return _command(lambda: list_improvement_proposals(session, context))


@router.post(
    "/proposals/{proposal_id}/candidates",
    response_model=ImprovementCandidateRead,
    status_code=status.HTTP_201_CREATED,
)
def create_candidate_endpoint(
    proposal_id: UUID,
    payload: ImprovementCandidateCreate,
    response: Response,
    context: OrganizationCommandContext = Depends(organization_command_context),
    session: Session = Depends(get_session),
) -> ImprovementCandidateRead:
    _no_store(response)
    row = _command(
        lambda: create_improvement_candidate(
            session,
            context,
            proposal_id=proposal_id,
            **payload.model_dump(),
        )
    )
    return project_improvement_candidate(row)


@router.get(
    "/proposals/{proposal_id}/candidates",
    response_model=tuple[ImprovementCandidateRead, ...],
)
def list_candidates_endpoint(
    proposal_id: UUID,
    response: Response,
    context: OrganizationCommandContext = Depends(organization_command_context),
    session: Session = Depends(get_session),
) -> tuple[ImprovementCandidateRead, ...]:
    _no_store(response)
    return _command(
        lambda: list_improvement_candidates(
            session,
            context,
            proposal_id=proposal_id,
        )
    )


@router.post(
    "/proposals/{proposal_id}/withdraw",
    response_model=ImprovementProposalRead,
)
def withdraw_proposal_endpoint(
    proposal_id: UUID,
    payload: ImprovementWithdrawal,
    response: Response,
    context: OrganizationCommandContext = Depends(organization_command_context),
    session: Session = Depends(get_session),
) -> ImprovementProposalRead:
    _no_store(response)
    row = _command(
        lambda: withdraw_improvement_proposal(
            session,
            context,
            proposal_id=proposal_id,
            reason=payload.reason,
        )
    )
    return project_improvement_proposal(row)


@router.post(
    "/candidates/{candidate_id}/withdraw",
    response_model=ImprovementCandidateRead,
)
def withdraw_candidate_endpoint(
    candidate_id: UUID,
    payload: ImprovementWithdrawal,
    response: Response,
    context: OrganizationCommandContext = Depends(organization_command_context),
    session: Session = Depends(get_session),
) -> ImprovementCandidateRead:
    _no_store(response)
    row = _command(
        lambda: withdraw_improvement_candidate(
            session,
            context,
            candidate_id=candidate_id,
            reason=payload.reason,
        )
    )
    return project_improvement_candidate(row)

# GRSI.C–E remain sub-capabilities of the canonical organization-improvements owner.
from app.routers.organization_improvement_evaluations import router as evaluation_router
from app.routers.organization_improvement_reviews import router as review_router
from app.routers.organization_improvement_shadows import router as shadow_router
from app.routers.organization_improvement_admission_policies import router as admission_policy_router

router.include_router(evaluation_router)
router.include_router(review_router)
router.include_router(shadow_router)
router.include_router(admission_policy_router)
