from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import ApplicationRecord, AuthorityAppointment
from app.schemas_authority_appointments import AuthorityAppointmentCreate
from app.services.audit_log import record_audit, to_audit_dict
from app.services.automation_bridge import capture_application_status_event


APPOINTMENT_TYPES = {"biometric", "interview", "document_submission", "other"}
APPOINTMENT_STATUSES = {"scheduled", "completed", "cancelled", "no_show"}
TERMINAL_STATUSES = {"completed", "cancelled", "no_show"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _appointment_to_dict(appointment: AuthorityAppointment) -> dict:
    return to_audit_dict(appointment)


def create_appointment(
    session: Session,
    payload: AuthorityAppointmentCreate,
    *,
    actor: str,
) -> AuthorityAppointment:
    application = session.get(ApplicationRecord, payload.application_id)
    if application is None:
        raise ValueError("Application not found")

    appointment_type = payload.appointment_type.strip().lower()
    if appointment_type not in APPOINTMENT_TYPES:
        raise ValueError(f"Invalid appointment type: {payload.appointment_type}")

    appointment = AuthorityAppointment(
        application_id=application.id,
        appointment_type=appointment_type,
        authority_name=payload.authority_name.strip(),
        location=payload.location.strip() if payload.location else None,
        scheduled_at=payload.scheduled_at,
        timezone=payload.timezone.strip() if payload.timezone else "UTC",
        reference_number=payload.reference_number.strip() if payload.reference_number else None,
        notes=payload.notes.strip() if payload.notes else None,
        created_by=actor,
        updated_by=actor,
        status="scheduled",
    )
    session.add(appointment)
    session.flush()

    record_audit(
        session,
        action="authority_appointment_created",
        entity_type="authority_appointment",
        entity_id=appointment.id,
        after_state=_appointment_to_dict(appointment),
        actor=actor,
        source="authority_appointment_v12_5",
    )
    session.commit()
    session.refresh(appointment)
    return appointment


def update_appointment_status(
    session: Session,
    appointment: AuthorityAppointment,
    *,
    status: str,
    reason: str,
    actor: str,
) -> AuthorityAppointment:
    normalized_status = status.strip().lower()
    if normalized_status not in APPOINTMENT_STATUSES:
        raise ValueError(f"Invalid appointment status: {status}")

    if appointment.status in TERMINAL_STATUSES:
        raise ValueError(
            f"Cannot change status from terminal state {appointment.status}"
        )

    if appointment.status != "scheduled":
        raise ValueError(
            f"Cannot change status from {appointment.status} to {normalized_status}"
        )

    if normalized_status == "scheduled":
        raise ValueError(
            f"Cannot transition from {appointment.status} to {normalized_status}"
        )

    before = _appointment_to_dict(appointment)
    application = session.get(ApplicationRecord, appointment.application_id)
    now = _now()
    appointment.status = normalized_status
    appointment.updated_by = actor
    appointment.updated_at = now
    session.add(appointment)

    record_audit(
        session,
        action=f"authority_appointment_{normalized_status}",
        entity_type="authority_appointment",
        entity_id=appointment.id,
        before_state=before,
        after_state=_appointment_to_dict(appointment),
        reason=reason.strip(),
        actor=actor,
        source="authority_appointment_v12_5",
    )
    session.commit()
    session.refresh(appointment)

    if application is not None:
        capture_application_status_event(
            session,
            application=application,
            event_type="appointment.status_changed",
            entity_type="authority_appointment",
            entity_id=appointment.id,
            status=normalized_status,
            actor=actor,
        )

    return appointment


def list_appointments_for_application(
    session: Session,
    application_id: UUID,
    *,
    status: str | None = None,
) -> Sequence[AuthorityAppointment]:
    statement = (
        select(AuthorityAppointment)
        .where(AuthorityAppointment.application_id == application_id)
        .order_by(AuthorityAppointment.scheduled_at.desc())
    )
    if status is not None:
        statement = statement.where(AuthorityAppointment.status == status.strip().lower())
    return session.exec(statement).all()


def list_appointments(
    session: Session,
    *,
    application_id: UUID | None = None,
    status: str | None = None,
    limit: int = 100,
) -> Sequence[AuthorityAppointment]:
    statement = select(AuthorityAppointment).order_by(
        AuthorityAppointment.scheduled_at.desc()
    )
    if application_id is not None:
        statement = statement.where(
            AuthorityAppointment.application_id == application_id
        )
    if status is not None:
        statement = statement.where(AuthorityAppointment.status == status.strip().lower())
    return session.exec(statement.limit(limit)).all()
