from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import ApplicationRecord, CorporateMobilityCase, Lead
from app.services.automation import capture_event


APPLICATION_EVENT_TYPES = {
    "appointment.status_changed",
    "submission.status_changed",
    "external_agency_assignment.status_changed",
}


def _find_corporate_case_for_lead(
    session: Session,
    lead_id: UUID,
) -> CorporateMobilityCase | None:
    return session.exec(
        select(CorporateMobilityCase)
        .where(CorporateMobilityCase.employee_lead_id == lead_id)
        .where(CorporateMobilityCase.status != "closed")
        .order_by(CorporateMobilityCase.updated_at.desc())
    ).first()


def capture_application_status_event(
    session: Session,
    *,
    application: ApplicationRecord,
    event_type: str,
    entity_type: str,
    entity_id: UUID,
    status: str,
    actor: str,
) -> Any | None:
    """Create a governed automation event for an application-level status change
    when the application's lead is linked to an active corporate mobility case.

    Returns the created AutomationEvent or None when no corporate link exists.
    """
    if event_type not in APPLICATION_EVENT_TYPES:
        raise ValueError(f"Unsupported application event type: {event_type}")

    lead_id = application.lead_id
    if lead_id is None:
        return None

    lead = session.get(Lead, lead_id)
    if lead is None:
        return None

    corporate_case = _find_corporate_case_for_lead(session, lead_id)
    if corporate_case is None:
        return None

    idempotency_key = f"{event_type}:{entity_id}:{status}"
    event, _ = capture_event(
        session,
        idempotency_key=idempotency_key,
        corporate_account_id=corporate_case.corporate_account_id,
        case_id=corporate_case.id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        payload={
            "application_id": str(application.id),
            "lead_id": str(lead_id),
            "lead_name": lead.full_name,
            "case_reference": corporate_case.case_reference,
            "status": status,
        },
        actor=actor,
        source="application_status_bridge",
    )
    return event
