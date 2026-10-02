from __future__ import annotations

from typing import Callable, TypeVar

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlmodel import Session

from app.core.db import get_session
from app.routers.organization_records import organization_command_context
from app.schemas_organization_improvement_admission_policy import (
    ImprovementAdmissionDependencyPolicyCreate,
    ImprovementAdmissionDependencyPolicyRead,
    ImprovementAdmissionExecutionMode,
    ImprovementAdmissionRiskClass,
    ImprovementAdmissionTargetType,
)
from app.services.organization_command import (
    AuthorityDenied,
    DependencyConflict,
    IdempotencyConflict,
    InvalidHumanActor,
    InvalidReference,
    InvalidTransition,
    OrganizationCommandContext,
    OrganizationCommandError,
)
from app.services.organization_improvement_admission_policy import (
    ImprovementAdmissionPolicyIntegrityError,
    current_improvement_admission_dependency_policy,
    establish_improvement_admission_dependency_policy,
    project_improvement_admission_dependency_policy,
)


router = APIRouter(
    prefix="/admission-policies",
    tags=["organization-grsi-admission-dependency-policy-v1"],
)
ResultT = TypeVar("ResultT")


def _http_error(exc: OrganizationCommandError) -> HTTPException:
    if isinstance(exc, (InvalidHumanActor, AuthorityDenied)):
        return HTTPException(status_code=403, detail="Organization action is not permitted.")
    if isinstance(
        exc,
        (
            IdempotencyConflict,
            DependencyConflict,
            InvalidTransition,
            ImprovementAdmissionPolicyIntegrityError,
        ),
    ):
        return HTTPException(status_code=409, detail="GRSI admission dependency policy conflicts with current state.")
    if isinstance(exc, InvalidReference):
        return HTTPException(status_code=422, detail="GRSI admission dependency policy reference is invalid.")
    return HTTPException(status_code=400, detail="GRSI admission dependency policy command was rejected.")


def _command(call: Callable[[], ResultT]) -> ResultT:
    try:
        return call()
    except OrganizationCommandError as exc:
        raise _http_error(exc) from exc


def _no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"


@router.post(
    "",
    response_model=ImprovementAdmissionDependencyPolicyRead,
    status_code=status.HTTP_201_CREATED,
)
def establish_admission_dependency_policy_endpoint(
    payload: ImprovementAdmissionDependencyPolicyCreate,
    response: Response,
    context: OrganizationCommandContext = Depends(organization_command_context),
    session: Session = Depends(get_session),
) -> ImprovementAdmissionDependencyPolicyRead:
    _no_store(response)
    row = _command(
        lambda: establish_improvement_admission_dependency_policy(
            session,
            context,
            **payload.model_dump(),
        )
    )
    return _command(
        lambda: project_improvement_admission_dependency_policy(session, context, row)
    )


@router.get(
    "/current",
    response_model=ImprovementAdmissionDependencyPolicyRead,
)
def get_current_admission_dependency_policy_endpoint(
    response: Response,
    target_type: ImprovementAdmissionTargetType = Query(...),
    execution_mode: ImprovementAdmissionExecutionMode = Query(...),
    candidate_risk_class: ImprovementAdmissionRiskClass = Query(...),
    context: OrganizationCommandContext = Depends(organization_command_context),
    session: Session = Depends(get_session),
) -> ImprovementAdmissionDependencyPolicyRead:
    _no_store(response)
    return _command(
        lambda: current_improvement_admission_dependency_policy(
            session,
            context,
            target_type=target_type,
            execution_mode=execution_mode,
            candidate_risk_class=candidate_risk_class,
        )
    )
