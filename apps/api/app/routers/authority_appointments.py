from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session

from app.core.db import get_session
from app.models.domain import AuthorityAppointment
from app.schemas_authority_appointments import (
    AuthorityAppointmentCreate,
    AuthorityAppointmentRead,
    AuthorityAppointmentStatusUpdate,
)
from app.services.audit_log import to_audit_dict
from app.services.authority_appointments import (
    create_appointment,
    list_appointments,
    list_appointments_for_application,
    update_appointment_status,
)


router = APIRouter(
    prefix="/api/v1/authority-appointments",
    tags=["authority-appointment-tracking"],
)


def _actor(request: Request) -> str:
    context = getattr(request.state, "auth", None)
    return str(getattr(context, "username", "api-operator"))


def _handle_value_error(exc: ValueError) -> HTTPException:
    message = str(exc)
    lowered = message.lower()
    if "not found" in lowered:
        return HTTPException(status_code=404, detail=message)
    if "terminal" in lowered or "transition" in lowered or "cannot change" in lowered:
        return HTTPException(status_code=409, detail=message)
    return HTTPException(status_code=400, detail=message)


@router.post("", response_model=AuthorityAppointmentRead, status_code=201)
def api_create_appointment(
    payload: AuthorityAppointmentCreate,
    request: Request,
    session: Session = Depends(get_session),
) -> AuthorityAppointmentRead:
    try:
        appointment = create_appointment(session, payload, actor=_actor(request))
    except ValueError as exc:
        session.rollback()
        raise _handle_value_error(exc) from exc
    return AuthorityAppointmentRead(**to_audit_dict(appointment))


@router.get("", response_model=list[AuthorityAppointmentRead])
def api_list_appointments(
    application_id: UUID | None = None,
    status: str | None = None,
    session: Session = Depends(get_session),
) -> list[AuthorityAppointmentRead]:
    appointments = list_appointments_for_application(
        session, application_id, status=status
    ) if application_id is not None else list_appointments(
        session, application_id=application_id, status=status
    )
    return [AuthorityAppointmentRead(**to_audit_dict(a)) for a in appointments]


@router.get("/{appointment_id}", response_model=AuthorityAppointmentRead)
def api_get_appointment(
    appointment_id: UUID,
    session: Session = Depends(get_session),
) -> AuthorityAppointmentRead:
    appointment = session.get(AuthorityAppointment, appointment_id)
    if appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return AuthorityAppointmentRead(**to_audit_dict(appointment))


@router.post("/{appointment_id}/status", response_model=AuthorityAppointmentRead)
def api_update_appointment_status(
    appointment_id: UUID,
    payload: AuthorityAppointmentStatusUpdate,
    request: Request,
    session: Session = Depends(get_session),
) -> AuthorityAppointmentRead:
    appointment = session.get(AuthorityAppointment, appointment_id)
    if appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    try:
        updated = update_appointment_status(
            session,
            appointment,
            status=payload.status,
            reason=payload.reason,
            actor=_actor(request),
        )
    except ValueError as exc:
        session.rollback()
        raise _handle_value_error(exc) from exc
    return AuthorityAppointmentRead(**to_audit_dict(updated))
