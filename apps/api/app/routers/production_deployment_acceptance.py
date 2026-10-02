from __future__ import annotations

from typing import Callable, TypeVar
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlmodel import Session

from app.core.db import get_session
from app.models.production_deployment_acceptance import ProductionDeploymentAcceptanceRun
from app.routers.organization_records import organization_command_context
from app.schemas_production_deployment_acceptance import (
    ProductionDeploymentAcceptanceRunCreate,
    ProductionDeploymentAcceptanceRunRead,
)
from app.services.organization_command import (
    AuthorityDenied,
    DependencyConflict,
    IdempotencyConflict,
    InvalidHumanActor,
    InvalidReference,
    InvalidTransition,
    NotFound,
    OrganizationCommandContext,
    OrganizationCommandError,
    TenantMismatch,
    tenant_record,
)
from app.services.production_deployment_acceptance import (
    DeploymentAcceptanceIntegrityError,
    prepare_deployment_acceptance_run,
    project_deployment_acceptance_run,
)


router = APIRouter(
    prefix="/api/v1/production-operations/deployment-acceptance",
    tags=["production-deployment-acceptance-v1"],
)
ResultT = TypeVar("ResultT")


def _http_error(exc: OrganizationCommandError) -> HTTPException:
    if isinstance(exc, (TenantMismatch, NotFound)):
        return HTTPException(status_code=404, detail="Deployment acceptance resource was not found.")
    if isinstance(exc, (InvalidHumanActor, AuthorityDenied)):
        return HTTPException(status_code=403, detail="Deployment acceptance action is not permitted.")
    if isinstance(
        exc,
        (IdempotencyConflict, DependencyConflict, InvalidTransition, DeploymentAcceptanceIntegrityError),
    ):
        return HTTPException(status_code=409, detail="Deployment acceptance conflicts with current state.")
    if isinstance(exc, InvalidReference):
        return HTTPException(status_code=422, detail="Deployment acceptance reference is invalid.")
    return HTTPException(status_code=400, detail="Deployment acceptance command was rejected.")


def _command(call: Callable[[], ResultT]) -> ResultT:
    try:
        return call()
    except OrganizationCommandError as exc:
        raise _http_error(exc) from exc


def _no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"


@router.post(
    "/runs",
    response_model=ProductionDeploymentAcceptanceRunRead,
    status_code=status.HTTP_201_CREATED,
)
def prepare_deployment_acceptance_run_endpoint(
    payload: ProductionDeploymentAcceptanceRunCreate,
    response: Response,
    context: OrganizationCommandContext = Depends(organization_command_context),
    session: Session = Depends(get_session),
) -> ProductionDeploymentAcceptanceRunRead:
    _no_store(response)
    row = _command(
        lambda: prepare_deployment_acceptance_run(
            session,
            context,
            **payload.model_dump(),
        )
    )
    return _command(lambda: project_deployment_acceptance_run(session, context, row))


@router.get(
    "/runs/{run_id}",
    response_model=ProductionDeploymentAcceptanceRunRead,
)
def get_deployment_acceptance_run_endpoint(
    run_id: UUID,
    response: Response,
    context: OrganizationCommandContext = Depends(organization_command_context),
    session: Session = Depends(get_session),
) -> ProductionDeploymentAcceptanceRunRead:
    _no_store(response)
    row = _command(
        lambda: tenant_record(
            session,
            ProductionDeploymentAcceptanceRun,
            run_id,
            context.tenant_key,
            label="deployment acceptance run",
        )
    )
    return _command(lambda: project_deployment_acceptance_run(session, context, row))
