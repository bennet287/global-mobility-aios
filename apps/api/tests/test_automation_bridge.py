from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.domain import ApplicationRecord, AutomationEvent, Lead
from tests.conftest import create_application, create_lead


SCHEDULED_AT = datetime(2026, 8, 1, 10, 0, 0, tzinfo=timezone.utc)
SUBMITTED_AT = datetime(2026, 8, 1, 14, 0, 0, tzinfo=timezone.utc)


def _create_linked_application(client: TestClient, db_session: Session) -> ApplicationRecord:
    lead = create_lead(db_session, name="Bridge Employee")
    account = client.post(
        "/api/v1/corporate-mobility/accounts",
        json={"legal_name": "Bridge Employer", "primary_country": "Austria"},
    )
    assert account.status_code == 201, account.text
    account_id = account.json()["id"]

    case = client.post(
        f"/api/v1/corporate-mobility/accounts/{account_id}/cases",
        json={
            "case_reference": "BRIDGE-CASE-001",
            "destination_country": "Germany",
            "employee_lead_id": str(lead.id),
        },
    )
    assert case.status_code == 201, case.text

    return create_application(db_session, lead, status="approved")


def _appointment_payload(application_id: str) -> dict:
    return {
        "application_id": application_id,
        "appointment_type": "interview",
        "authority_name": "German Consulate Mumbai",
        "location": "Mumbai",
        "scheduled_at": SCHEDULED_AT.isoformat().replace("+00:00", "Z"),
        "timezone": "Asia/Kolkata",
        "reference_number": "APT-123",
        "notes": "Bring original passport.",
    }


def _submission_payload(application_id: str) -> dict:
    return {
        "application_id": application_id,
        "authority_name": "German Consulate Mumbai",
        "submission_channel": "online",
        "submitted_at": SUBMITTED_AT.isoformat().replace("+00:00", "Z"),
        "reference_number": "SUB-123",
        "notes": "Submitted through portal.",
    }


def test_appointment_status_change_creates_automation_event(
    client: TestClient, db_session: Session
) -> None:
    application = _create_linked_application(client, db_session)
    appointment = client.post(
        "/api/v1/authority-appointments", json=_appointment_payload(str(application.id))
    )
    assert appointment.status_code == 201
    appointment_id = appointment.json()["id"]

    completed = client.post(
        f"/api/v1/authority-appointments/{appointment_id}/status",
        json={"status": "completed", "reason": "Attended on time."},
    )
    assert completed.status_code == 200

    event = db_session.exec(
        select(AutomationEvent).where(
            AutomationEvent.event_type == "appointment.status_changed"
        )
    ).first()
    assert event is not None
    assert event.entity_id == appointment_id
    assert event.payload_json is not None
    assert "application_id" in event.payload_json


def test_submission_status_change_creates_automation_event(
    client: TestClient, db_session: Session
) -> None:
    application = _create_linked_application(client, db_session)
    submission = client.post(
        "/api/v1/agency-submissions", json=_submission_payload(str(application.id))
    )
    assert submission.status_code == 201
    submission_id = submission.json()["id"]

    acknowledged = client.post(
        f"/api/v1/agency-submissions/{submission_id}/status",
        json={"status": "acknowledged", "reason": "Receipt confirmed."},
    )
    assert acknowledged.status_code == 200

    event = db_session.exec(
        select(AutomationEvent).where(
            AutomationEvent.event_type == "submission.status_changed"
        )
    ).first()
    assert event is not None
    assert event.entity_id == submission_id


def test_no_automation_event_without_corporate_case(
    client: TestClient, db_session: Session
) -> None:
    lead = create_lead(db_session, name="Solo Applicant")
    application = create_application(db_session, lead)
    appointment = client.post(
        "/api/v1/authority-appointments", json=_appointment_payload(str(application.id))
    )
    assert appointment.status_code == 201
    appointment_id = appointment.json()["id"]

    completed = client.post(
        f"/api/v1/authority-appointments/{appointment_id}/status",
        json={"status": "completed", "reason": "Attended."},
    )
    assert completed.status_code == 200

    event = db_session.exec(
        select(AutomationEvent).where(
            AutomationEvent.event_type == "appointment.status_changed"
        )
    ).first()
    assert event is None


def _agency_payload() -> dict:
    return {
        "name": "Bridge Partner Agency",
        "country": "India",
        "city": "Mumbai",
        "contact_email": "partner@example.com",
        "contact_phone": "+91-9999999999",
        "website": "https://partner.example.com",
        "notes": "Test agency for automation bridge.",
    }


def _assignment_payload(application_id: str, agency_id: str) -> dict:
    return {
        "application_id": application_id,
        "external_agency_id": agency_id,
        "agency_reference_number": "AGY-123",
        "notes": "Hand off to external partner.",
    }


def test_external_agency_assignment_status_change_creates_automation_event(
    client: TestClient, db_session: Session
) -> None:
    application = _create_linked_application(client, db_session)

    agency = client.post("/api/v1/external-agencies", json=_agency_payload())
    assert agency.status_code == 201, agency.text
    agency_id = agency.json()["id"]

    assignment = client.post(
        "/api/v1/external-agency-assignments",
        json=_assignment_payload(str(application.id), agency_id),
    )
    assert assignment.status_code == 201, assignment.text
    assignment_id = assignment.json()["id"]

    in_progress = client.post(
        f"/api/v1/external-agency-assignments/{assignment_id}/status",
        json={"status": "in_progress", "reason": "Agency started processing."},
    )
    assert in_progress.status_code == 200, in_progress.text

    event = db_session.exec(
        select(AutomationEvent).where(
            AutomationEvent.event_type == "external_agency_assignment.status_changed"
        )
    ).first()
    assert event is not None
    assert event.entity_id == assignment_id
    assert event.payload_json is not None
    assert "application_id" in event.payload_json
