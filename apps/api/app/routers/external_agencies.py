from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session

from app.core.db import get_session
from app.models.domain import ExternalAgency, ExternalAgencyAssignment
from app.schemas_external_agencies import (
    ExternalAgencyAssignmentCreate,
    ExternalAgencyAssignmentRead,
    ExternalAgencyAssignmentStatusUpdate,
    ExternalAgencyCreate,
    ExternalAgencyRead,
    ExternalAgencyStatusUpdate,
)
from app.services.audit_log import to_audit_dict
from app.services.external_agencies import (
    create_assignment,
    create_external_agency,
    list_assignments,
    list_assignments_for_application,
    list_external_agencies,
    update_assignment_status,
    update_external_agency_status,
)


router = APIRouter(tags=["external-agency-tracking"])


def _actor(request: Request) -> str:
    context = getattr(request.state, "auth", None)
    return str(getattr(context, "username", "api-operator"))


def _handle_value_error(exc: ValueError) -> HTTPException:
    message = str(exc)
    lowered = message.lower()
    if "not found" in lowered:
        return HTTPException(status_code=404, detail=message)
    if "terminal" in lowered or "transition" in lowered or "already has" in lowered:
        return HTTPException(status_code=409, detail=message)
    return HTTPException(status_code=400, detail=message)


@router.post("/api/v1/external-agencies", response_model=ExternalAgencyRead, status_code=201)
def api_create_external_agency(
    payload: ExternalAgencyCreate,
    request: Request,
    session: Session = Depends(get_session),
) -> ExternalAgencyRead:
    try:
        agency = create_external_agency(session, payload, actor=_actor(request))
    except ValueError as exc:
        session.rollback()
        raise _handle_value_error(exc) from exc
    return ExternalAgencyRead(**to_audit_dict(agency))


@router.get("/api/v1/external-agencies", response_model=list[ExternalAgencyRead])
def api_list_external_agencies(
    status: str | None = None,
    session: Session = Depends(get_session),
) -> list[ExternalAgencyRead]:
    agencies = list_external_agencies(session, status=status)
    return [ExternalAgencyRead(**to_audit_dict(a)) for a in agencies]


@router.post(
    "/api/v1/external-agencies/{agency_id}/status",
    response_model=ExternalAgencyRead,
)
def api_update_external_agency_status(
    agency_id: UUID,
    payload: ExternalAgencyStatusUpdate,
    request: Request,
    session: Session = Depends(get_session),
) -> ExternalAgencyRead:
    agency = session.get(ExternalAgency, agency_id)
    if agency is None:
        raise HTTPException(status_code=404, detail="External agency not found")
    try:
        updated = update_external_agency_status(
            session,
            agency,
            status=payload.status,
            reason=payload.reason,
            actor=_actor(request),
        )
    except ValueError as exc:
        session.rollback()
        raise _handle_value_error(exc) from exc
    return ExternalAgencyRead(**to_audit_dict(updated))


@router.post(
    "/api/v1/external-agency-assignments",
    response_model=ExternalAgencyAssignmentRead,
    status_code=201,
)
def api_create_assignment(
    payload: ExternalAgencyAssignmentCreate,
    request: Request,
    session: Session = Depends(get_session),
) -> ExternalAgencyAssignmentRead:
    try:
        assignment = create_assignment(session, payload, actor=_actor(request))
    except ValueError as exc:
        session.rollback()
        raise _handle_value_error(exc) from exc
    return ExternalAgencyAssignmentRead(**to_audit_dict(assignment))


@router.get(
    "/api/v1/external-agency-assignments",
    response_model=list[ExternalAgencyAssignmentRead],
)
def api_list_assignments(
    application_id: UUID | None = None,
    external_agency_id: UUID | None = None,
    status: str | None = None,
    session: Session = Depends(get_session),
) -> list[ExternalAgencyAssignmentRead]:
    assignments = list_assignments(
        session,
        application_id=application_id,
        external_agency_id=external_agency_id,
        status=status,
    )
    return [ExternalAgencyAssignmentRead(**to_audit_dict(a)) for a in assignments]


@router.get(
    "/api/v1/applications/{application_id}/external-agency-assignments",
    response_model=list[ExternalAgencyAssignmentRead],
)
def api_list_assignments_for_application(
    application_id: UUID,
    session: Session = Depends(get_session),
) -> list[ExternalAgencyAssignmentRead]:
    assignments = list_assignments_for_application(session, application_id)
    return [ExternalAgencyAssignmentRead(**to_audit_dict(a)) for a in assignments]


@router.get(
    "/api/v1/external-agency-assignments/{assignment_id}",
    response_model=ExternalAgencyAssignmentRead,
)
def api_get_assignment(
    assignment_id: UUID,
    session: Session = Depends(get_session),
) -> ExternalAgencyAssignmentRead:
    assignment = session.get(ExternalAgencyAssignment, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return ExternalAgencyAssignmentRead(**to_audit_dict(assignment))


@router.post(
    "/api/v1/external-agency-assignments/{assignment_id}/status",
    response_model=ExternalAgencyAssignmentRead,
)
def api_update_assignment_status(
    assignment_id: UUID,
    payload: ExternalAgencyAssignmentStatusUpdate,
    request: Request,
    session: Session = Depends(get_session),
) -> ExternalAgencyAssignmentRead:
    assignment = session.get(ExternalAgencyAssignment, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="Assignment not found")
    try:
        updated = update_assignment_status(
            session,
            assignment,
            payload=payload,
            actor=_actor(request),
        )
    except ValueError as exc:
        session.rollback()
        raise _handle_value_error(exc) from exc
    return ExternalAgencyAssignmentRead(**to_audit_dict(updated))
