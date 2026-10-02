from __future__ import annotations

from typing import Callable, TypeVar
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlmodel import Session

from app.core.db import get_session
from app.routers.organization_records import organization_command_context
from app.schemas_organization_improvement_review import (
    ImprovementReviewPackageCreate,
    ImprovementReviewPackageRead,
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
from app.services.organization_improvement_review import (
    create_review_package,
    get_review_package,
    list_review_packages,
    project_review_package,
)


router = APIRouter(
    prefix="/reviews",
    tags=["organization-grsi-cross-team-review-v1"],
)
ResultT = TypeVar("ResultT")


def _http_error(exc: OrganizationCommandError) -> HTTPException:
    if isinstance(exc, (TenantMismatch, NotFound)):
        return HTTPException(status_code=404, detail="Organization resource not found.")
    if isinstance(exc, (InvalidHumanActor, AuthorityDenied)):
        return HTTPException(status_code=403, detail="Organization action is not permitted.")
    if isinstance(exc, (IdempotencyConflict, InvalidTransition)):
        return HTTPException(status_code=409, detail="Improvement review package conflicts with current state.")
    if isinstance(exc, InvalidReference):
        return HTTPException(status_code=422, detail="Improvement review package reference is invalid.")
    return HTTPException(status_code=400, detail="Improvement review package command was rejected.")


def _command(call: Callable[[], ResultT]) -> ResultT:
    try:
        return call()
    except OrganizationCommandError as exc:
        raise _http_error(exc) from exc


def _no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"


@router.post(
    "/packages",
    response_model=ImprovementReviewPackageRead,
    status_code=status.HTTP_201_CREATED,
)
def create_review_package_endpoint(
    payload: ImprovementReviewPackageCreate,
    response: Response,
    context: OrganizationCommandContext = Depends(organization_command_context),
    session: Session = Depends(get_session),
) -> ImprovementReviewPackageRead:
    _no_store(response)
    row = _command(lambda: create_review_package(session, context, **payload.model_dump()))
    return _command(lambda: project_review_package(session, context, row))


@router.get("/packages", response_model=tuple[ImprovementReviewPackageRead, ...])
def list_review_packages_endpoint(
    response: Response,
    context: OrganizationCommandContext = Depends(organization_command_context),
    session: Session = Depends(get_session),
) -> tuple[ImprovementReviewPackageRead, ...]:
    _no_store(response)
    return _command(lambda: list_review_packages(session, context))


@router.get("/packages/{package_id}", response_model=ImprovementReviewPackageRead)
def get_review_package_endpoint(
    package_id: UUID,
    response: Response,
    context: OrganizationCommandContext = Depends(organization_command_context),
    session: Session = Depends(get_session),
) -> ImprovementReviewPackageRead:
    _no_store(response)
    return _command(lambda: get_review_package(session, context, package_id=package_id))
