from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Sequence
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    ApplicationRecord,
    ExternalAgency,
    ExternalAgencyAssignment,
)
from app.schemas_external_agencies import (
    ExternalAgencyAssignmentCreate,
    ExternalAgencyAssignmentStatusUpdate,
    ExternalAgencyCreate,
)
from app.services.audit_log import record_audit, to_audit_dict
from app.services.automation_bridge import capture_application_status_event


AGENCY_STATUSES = {"active", "suspended", "retired"}
ASSIGNMENT_STATUSES = {
    "assigned",
    "in_progress",
    "handed_off",
    "completed",
    "cancelled",
}
TERMINAL_ASSIGNMENT_STATUSES = {"completed", "cancelled"}
SLA_STATUSES = {"on_track", "due_soon", "breached", "completed"}
_DUE_SOON_HOURS = 12

# Forward-only transitions.
_ALLOWED_ASSIGNMENT_TRANSITIONS: dict[str, set[str]] = {
    "assigned": {"in_progress", "cancelled"},
    "in_progress": {"handed_off", "cancelled"},
    "handed_off": {"completed", "cancelled"},
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def evaluate_assignment_sla(
    assignment: ExternalAgencyAssignment,
    as_of: datetime | None = None,
) -> None:
    """Update the assignment's SLA status based on its current state and the
    provided timestamp (defaults to now)."""
    if assignment.status in TERMINAL_ASSIGNMENT_STATUSES:
        if assignment.status == "completed":
            completed_at = _as_utc(assignment.completed_at) if assignment.completed_at else None
            due_at = _as_utc(assignment.sla_due_at) if assignment.sla_due_at else None
            if completed_at and due_at and completed_at > due_at:
                assignment.sla_status = "breached"
                if assignment.sla_breached_at is None:
                    assignment.sla_breached_at = assignment.completed_at
            else:
                assignment.sla_status = "completed"
        else:
            assignment.sla_status = "completed"
        return

    if assignment.sla_due_at is None:
        return

    now = _as_utc(as_of or _now())
    due_at = _as_utc(assignment.sla_due_at)
    if now > due_at:
        assignment.sla_status = "breached"
        if assignment.sla_breached_at is None:
            assignment.sla_breached_at = as_of or _now()
    elif now > due_at - timedelta(hours=_DUE_SOON_HOURS):
        assignment.sla_status = "due_soon"
    else:
        assignment.sla_status = "on_track"


def scan_assignment_sla_evaluations(
    session: Session,
    *,
    actor: str = "external-agency-sla-monitor",
) -> dict[str, int]:
    """Re-evaluate SLA status for every non-terminal assignment and commit changes."""
    assignments = session.exec(
        select(ExternalAgencyAssignment).where(
            ExternalAgencyAssignment.status.notin_(TERMINAL_ASSIGNMENT_STATUSES)  # type: ignore[arg-type]
        )
    ).all()
    changed = 0
    for assignment in assignments:
        before_status = assignment.sla_status
        evaluate_assignment_sla(assignment)
        if assignment.sla_status != before_status:
            assignment.updated_at = _now()
            session.add(assignment)
            changed += 1

    if changed:
        session.commit()

    return {"assignments_evaluated": len(assignments), "sla_status_changes": changed}


def create_external_agency(
    session: Session,
    payload: ExternalAgencyCreate,
    *,
    actor: str,
) -> ExternalAgency:
    agency = ExternalAgency(
        name=payload.name.strip(),
        country=payload.country.strip() if payload.country else None,
        city=payload.city.strip() if payload.city else None,
        contact_email=payload.contact_email.strip() if payload.contact_email else None,
        contact_phone=payload.contact_phone.strip() if payload.contact_phone else None,
        website=payload.website.strip() if payload.website else None,
        sla_due_hours=payload.sla_due_hours,
        notes=payload.notes.strip() if payload.notes else None,
        status="active",
        created_by=actor,
        updated_by=actor,
    )
    session.add(agency)
    session.flush()
    record_audit(
        session,
        action="external_agency_created",
        entity_type="external_agency",
        entity_id=agency.id,
        after_state=to_audit_dict(agency),
        actor=actor,
        source="external_agency_v12_7",
    )
    session.commit()
    session.refresh(agency)
    return agency


def update_external_agency_status(
    session: Session,
    agency: ExternalAgency,
    *,
    status: str,
    reason: str,
    actor: str,
) -> ExternalAgency:
    normalized_status = status.strip().lower()
    if normalized_status not in AGENCY_STATUSES:
        raise ValueError(f"Invalid agency status: {status}")

    before = to_audit_dict(agency)
    now = _now()
    agency.status = normalized_status
    agency.updated_by = actor
    agency.updated_at = now
    session.add(agency)
    record_audit(
        session,
        action=f"external_agency_{normalized_status}",
        entity_type="external_agency",
        entity_id=agency.id,
        before_state=before,
        after_state=to_audit_dict(agency),
        reason=reason.strip(),
        actor=actor,
        source="external_agency_v12_7",
    )
    session.commit()
    session.refresh(agency)
    return agency


def list_external_agencies(
    session: Session,
    *,
    status: str | None = None,
    limit: int = 100,
) -> Sequence[ExternalAgency]:
    statement = select(ExternalAgency).order_by(ExternalAgency.name)
    if status is not None:
        statement = statement.where(ExternalAgency.status == status.strip().lower())
    return session.exec(statement.limit(limit)).all()


def create_assignment(
    session: Session,
    payload: ExternalAgencyAssignmentCreate,
    *,
    actor: str,
) -> ExternalAgencyAssignment:
    application = session.get(ApplicationRecord, payload.application_id)
    if application is None:
        raise ValueError("Application not found")
    agency = session.get(ExternalAgency, payload.external_agency_id)
    if agency is None:
        raise ValueError("External agency not found")
    if agency.status != "active":
        raise ValueError("External agency must be active to receive assignments")

    existing = session.exec(
        select(ExternalAgencyAssignment).where(
            ExternalAgencyAssignment.application_id == application.id,
            ExternalAgencyAssignment.status.notin_(TERMINAL_ASSIGNMENT_STATUSES),  # type: ignore[arg-type]
        )
    ).first()
    if existing is not None:
        raise ValueError("Application already has an active external agency assignment")

    now = _now()
    assignment = ExternalAgencyAssignment(
        application_id=application.id,
        external_agency_id=agency.id,
        status="assigned",
        agency_reference_number=payload.agency_reference_number.strip()
        if payload.agency_reference_number
        else None,
        notes=payload.notes.strip() if payload.notes else None,
        sla_due_at=now + timedelta(hours=agency.sla_due_hours),
        created_by=actor,
        updated_by=actor,
        created_at=now,
        updated_at=now,
    )
    evaluate_assignment_sla(assignment, as_of=now)
    session.add(assignment)
    session.flush()
    record_audit(
        session,
        action="external_agency_assignment_created",
        entity_type="external_agency_assignment",
        entity_id=assignment.id,
        after_state=to_audit_dict(assignment),
        actor=actor,
        source="external_agency_v12_7",
    )
    session.commit()
    session.refresh(assignment)
    return assignment


def update_assignment_status(
    session: Session,
    assignment: ExternalAgencyAssignment,
    *,
    payload: ExternalAgencyAssignmentStatusUpdate,
    actor: str,
) -> ExternalAgencyAssignment:
    normalized_status = payload.status.strip().lower()
    if normalized_status not in ASSIGNMENT_STATUSES:
        raise ValueError(f"Invalid assignment status: {payload.status}")

    if assignment.status in TERMINAL_ASSIGNMENT_STATUSES:
        raise ValueError(
            f"Cannot change status from terminal state {assignment.status}"
        )

    allowed = _ALLOWED_ASSIGNMENT_TRANSITIONS.get(assignment.status, set())
    if normalized_status not in allowed:
        raise ValueError(
            f"Cannot transition from {assignment.status} to {normalized_status}"
        )

    before = to_audit_dict(assignment)
    application = session.get(ApplicationRecord, assignment.application_id)
    now = _now()
    assignment.status = normalized_status
    assignment.updated_by = actor
    assignment.updated_at = now
    if normalized_status == "handed_off":
        assignment.handoff_at = now
    if normalized_status == "completed":
        assignment.completed_at = now
    if payload.agency_reference_number is not None:
        assignment.agency_reference_number = payload.agency_reference_number.strip()
    evaluate_assignment_sla(assignment, as_of=now)
    session.add(assignment)

    record_audit(
        session,
        action=f"external_agency_assignment_{normalized_status}",
        entity_type="external_agency_assignment",
        entity_id=assignment.id,
        before_state=before,
        after_state=to_audit_dict(assignment),
        reason=payload.reason.strip(),
        actor=actor,
        source="external_agency_v12_7",
    )
    session.commit()
    session.refresh(assignment)

    if application is not None:
        capture_application_status_event(
            session,
            application=application,
            event_type="external_agency_assignment.status_changed",
            entity_type="external_agency_assignment",
            entity_id=assignment.id,
            status=normalized_status,
            actor=actor,
        )

    return assignment


def list_assignments_for_application(
    session: Session,
    application_id: UUID,
) -> Sequence[ExternalAgencyAssignment]:
    return session.exec(
        select(ExternalAgencyAssignment)
        .where(ExternalAgencyAssignment.application_id == application_id)
        .order_by(ExternalAgencyAssignment.created_at.desc())
    ).all()


def list_assignments(
    session: Session,
    *,
    application_id: UUID | None = None,
    external_agency_id: UUID | None = None,
    status: str | None = None,
    limit: int = 100,
) -> Sequence[ExternalAgencyAssignment]:
    statement = select(ExternalAgencyAssignment).order_by(
        ExternalAgencyAssignment.created_at.desc()
    )
    if application_id is not None:
        statement = statement.where(ExternalAgencyAssignment.application_id == application_id)
    if external_agency_id is not None:
        statement = statement.where(
            ExternalAgencyAssignment.external_agency_id == external_agency_id
        )
    if status is not None:
        statement = statement.where(ExternalAgencyAssignment.status == status.strip().lower())
    return session.exec(statement.limit(limit)).all()
