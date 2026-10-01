from __future__ import annotations

from typing import Callable, TypeVar
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlmodel import Session

from app.core.db import get_session
from app.routers.organization_records import organization_command_context
from app.schemas_organization_improvement_evaluation import (
    ImprovementEvaluationCampaignCreate,
    ImprovementEvaluationCampaignRead,
    ImprovementEvaluationReportCreate,
    ImprovementEvaluationReportRead,
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
from app.services.organization_improvement_evaluation import (
    close_evaluation_campaign,
    create_evaluation_campaign,
    list_evaluation_campaigns,
    list_evaluation_reports,
    project_evaluation_campaign,
    project_evaluation_report,
    record_evaluation_report,
)


router = APIRouter(
    prefix="/evaluations",
    tags=["organization-grsi-independent-evaluation-v1"],
)
ResultT = TypeVar("ResultT")


def _http_error(exc: OrganizationCommandError) -> HTTPException:
    if isinstance(exc, (TenantMismatch, NotFound)):
        return HTTPException(status_code=404, detail="Organization resource not found.")
    if isinstance(exc, (InvalidHumanActor, AuthorityDenied)):
        return HTTPException(status_code=403, detail="Organization action is not permitted.")
    if isinstance(exc, (IdempotencyConflict, InvalidTransition)):
        return HTTPException(status_code=409, detail="Improvement evaluation conflicts with current state.")
    if isinstance(exc, InvalidReference):
        return HTTPException(status_code=422, detail="Improvement evaluation reference is invalid.")
    return HTTPException(status_code=400, detail="Improvement evaluation command was rejected.")


def _command(call: Callable[[], ResultT]) -> ResultT:
    try:
        return call()
    except OrganizationCommandError as exc:
        raise _http_error(exc) from exc


def _no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"


@router.post(
    "/campaigns",
    response_model=ImprovementEvaluationCampaignRead,
    status_code=status.HTTP_201_CREATED,
)
def create_campaign_endpoint(
    payload: ImprovementEvaluationCampaignCreate,
    response: Response,
    context: OrganizationCommandContext = Depends(organization_command_context),
    session: Session = Depends(get_session),
) -> ImprovementEvaluationCampaignRead:
    _no_store(response)
    row = _command(lambda: create_evaluation_campaign(session, context, **payload.model_dump()))
    return project_evaluation_campaign(row)


@router.get("/campaigns", response_model=tuple[ImprovementEvaluationCampaignRead, ...])
def list_campaigns_endpoint(
    response: Response,
    context: OrganizationCommandContext = Depends(organization_command_context),
    session: Session = Depends(get_session),
) -> tuple[ImprovementEvaluationCampaignRead, ...]:
    _no_store(response)
    return _command(lambda: list_evaluation_campaigns(session, context))


@router.post(
    "/campaigns/{campaign_id}/reports",
    response_model=ImprovementEvaluationReportRead,
    status_code=status.HTTP_201_CREATED,
)
def record_report_endpoint(
    campaign_id: UUID,
    payload: ImprovementEvaluationReportCreate,
    response: Response,
    context: OrganizationCommandContext = Depends(organization_command_context),
    session: Session = Depends(get_session),
) -> ImprovementEvaluationReportRead:
    _no_store(response)
    row = _command(
        lambda: record_evaluation_report(
            session,
            context,
            campaign_id=campaign_id,
            **payload.model_dump(),
        )
    )
    return project_evaluation_report(row)


@router.get(
    "/campaigns/{campaign_id}/reports",
    response_model=tuple[ImprovementEvaluationReportRead, ...],
)
def list_reports_endpoint(
    campaign_id: UUID,
    response: Response,
    context: OrganizationCommandContext = Depends(organization_command_context),
    session: Session = Depends(get_session),
) -> tuple[ImprovementEvaluationReportRead, ...]:
    _no_store(response)
    return _command(
        lambda: list_evaluation_reports(
            session,
            context,
            campaign_id=campaign_id,
        )
    )


@router.post(
    "/campaigns/{campaign_id}/close",
    response_model=ImprovementEvaluationCampaignRead,
)
def close_campaign_endpoint(
    campaign_id: UUID,
    response: Response,
    context: OrganizationCommandContext = Depends(organization_command_context),
    session: Session = Depends(get_session),
) -> ImprovementEvaluationCampaignRead:
    _no_store(response)
    row = _command(
        lambda: close_evaluation_campaign(
            session,
            context,
            campaign_id=campaign_id,
        )
    )
    return project_evaluation_campaign(row)
