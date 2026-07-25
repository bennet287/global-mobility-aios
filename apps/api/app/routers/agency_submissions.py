from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session

from app.core.db import get_session
from app.models.domain import AgencySubmission
from app.schemas_agency_submissions import (
    AgencySubmissionCreate,
    AgencySubmissionRead,
    AgencySubmissionStatusUpdate,
)
from app.services.audit_log import to_audit_dict
from app.services.agency_submissions import (
    create_submission,
    list_submissions,
    list_submissions_for_application,
    update_submission_status,
)


router = APIRouter(
    prefix="/api/v1/agency-submissions",
    tags=["agency-submission-tracking"],
)


def _actor(request: Request) -> str:
    context = getattr(request.state, "auth", None)
    return str(getattr(context, "username", "api-operator"))


def _handle_value_error(exc: ValueError) -> HTTPException:
    message = str(exc)
    lowered = message.lower()
    if "not found" in lowered:
        return HTTPException(status_code=404, detail=message)
    if "terminal" in lowered or "transition" in lowered or "cannot" in lowered:
        return HTTPException(status_code=409, detail=message)
    return HTTPException(status_code=400, detail=message)


@router.post("", response_model=AgencySubmissionRead, status_code=201)
def api_create_submission(
    payload: AgencySubmissionCreate,
    request: Request,
    session: Session = Depends(get_session),
) -> AgencySubmissionRead:
    try:
        submission = create_submission(session, payload, actor=_actor(request))
    except ValueError as exc:
        session.rollback()
        raise _handle_value_error(exc) from exc
    return AgencySubmissionRead(**to_audit_dict(submission))


@router.get("", response_model=list[AgencySubmissionRead])
def api_list_submissions(
    application_id: UUID | None = None,
    status: str | None = None,
    session: Session = Depends(get_session),
) -> list[AgencySubmissionRead]:
    appointments = list_submissions_for_application(
        session, application_id, status=status
    ) if application_id is not None else list_submissions(
        session, application_id=application_id, status=status
    )
    return [AgencySubmissionRead(**to_audit_dict(a)) for a in appointments]


@router.get("/{submission_id}", response_model=AgencySubmissionRead)
def api_get_submission(
    submission_id: UUID,
    session: Session = Depends(get_session),
) -> AgencySubmissionRead:
    submission = session.get(AgencySubmission, submission_id)
    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    return AgencySubmissionRead(**to_audit_dict(submission))


@router.post("/{submission_id}/status", response_model=AgencySubmissionRead)
def api_update_submission_status(
    submission_id: UUID,
    payload: AgencySubmissionStatusUpdate,
    request: Request,
    session: Session = Depends(get_session),
) -> AgencySubmissionRead:
    submission = session.get(AgencySubmission, submission_id)
    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    try:
        updated = update_submission_status(
            session,
            submission,
            status=payload.status,
            reason=payload.reason,
            actor=_actor(request),
        )
    except ValueError as exc:
        session.rollback()
        raise _handle_value_error(exc) from exc
    return AgencySubmissionRead(**to_audit_dict(updated))
