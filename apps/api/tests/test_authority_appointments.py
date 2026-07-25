from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.domain import (
    ApplicationRecord,
    AuditLog,
    AuthorityAppointment,
    AutomationEvent,
    Lead,
)
from app.services.authority_appointments import scan_appointment_reminders
from tests.conftest import create_application, create_lead


SCHEDULED_AT = datetime(2026, 8, 1, 10, 0, 0, tzinfo=timezone.utc)


def _appointment_payload(application_id: str) -> dict:
    return {
        "application_id": application_id,
        "appointment_type": "interview",
        "authority_name": "German Consulate Mumbai",
        "location": "Mumbai",
        "scheduled_at": SCHEDULED_AT.isoformat().replace("+00:00", "Z"),
        "timezone": "Asia/Kolkata",
        "reference_number": "REF-123",
        "notes": "Bring original passport and appointment confirmation.",
    }


def _create_application(session: Session) -> ApplicationRecord:
    lead = create_lead(session)
    return create_application(session, lead)


def test_create_appointment_and_read_back(client: TestClient, db_session: Session) -> None:
    application = _create_application(db_session)
    payload = _appointment_payload(str(application.id))

    response = client.post("/api/v1/authority-appointments", json=payload)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["appointment_type"] == "interview"
    assert data["authority_name"] == "German Consulate Mumbai"
    assert data["status"] == "scheduled"
    assert data["created_by"] == "pytest-admin"
    assert data["updated_by"] == "pytest-admin"
    assert data["timezone"] == "Asia/Kolkata"

    read = client.get(f"/api/v1/authority-appointments/{data['id']}")
    assert read.status_code == 200
    assert read.json()["id"] == data["id"]

    db_record = db_session.get(AuthorityAppointment, UUID(data["id"]))
    assert db_record is not None
    assert db_record.application_id == application.id


def test_list_appointments_for_application_and_filter_by_status(
    client: TestClient, db_session: Session
) -> None:
    application = _create_application(db_session)
    payload = _appointment_payload(str(application.id))

    first = client.post("/api/v1/authority-appointments", json=payload)
    assert first.status_code == 201

    payload["appointment_type"] = "biometric"
    payload["scheduled_at"] = "2026-08-02T10:00:00Z"
    second = client.post("/api/v1/authority-appointments", json=payload)
    assert second.status_code == 201
    second_id = second.json()["id"]

    completed = client.post(
        f"/api/v1/authority-appointments/{second_id}/status",
        json={"status": "completed", "reason": "Attended on time."},
    )
    assert completed.status_code == 200

    listed = client.get(
        f"/api/v1/authority-appointments?application_id={application.id}"
    )
    assert listed.status_code == 200
    items = listed.json()
    assert len(items) == 2

    filtered = client.get(
        f"/api/v1/authority-appointments?application_id={application.id}&status=completed"
    )
    assert filtered.status_code == 200
    filtered_items = filtered.json()
    assert len(filtered_items) == 1
    assert filtered_items[0]["id"] == second_id
    assert filtered_items[0]["status"] == "completed"


def test_update_status_to_completed_with_reason(
    client: TestClient, db_session: Session
) -> None:
    application = _create_application(db_session)
    payload = _appointment_payload(str(application.id))
    created = client.post("/api/v1/authority-appointments", json=payload)
    assert created.status_code == 201
    appointment_id = created.json()["id"]

    response = client.post(
        f"/api/v1/authority-appointments/{appointment_id}/status",
        json={"status": "completed", "reason": "Client attended and submitted biometrics."},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "completed"
    assert data["updated_by"] == "pytest-admin"


def test_reject_invalid_status_transition(client: TestClient, db_session: Session) -> None:
    application = _create_application(db_session)
    payload = _appointment_payload(str(application.id))
    created = client.post("/api/v1/authority-appointments", json=payload)
    assert created.status_code == 201
    appointment_id = created.json()["id"]

    completed = client.post(
        f"/api/v1/authority-appointments/{appointment_id}/status",
        json={"status": "completed", "reason": "Attended."},
    )
    assert completed.status_code == 200

    back_to_scheduled = client.post(
        f"/api/v1/authority-appointments/{appointment_id}/status",
        json={"status": "scheduled", "reason": "Mistake."},
    )
    assert back_to_scheduled.status_code == 409
    assert "terminal" in back_to_scheduled.json()["detail"].lower()

    invalid_type = client.post(
        f"/api/v1/authority-appointments/{appointment_id}/status",
        json={"status": "not_a_status", "reason": "Invalid."},
    )
    assert invalid_type.status_code == 422


def test_create_appointment_for_missing_application(client: TestClient) -> None:
    payload = _appointment_payload(str(uuid4()))
    response = client.post("/api/v1/authority-appointments", json=payload)
    assert response.status_code == 404


def test_audit_log_entries_are_created(client: TestClient, db_session: Session) -> None:
    application = _create_application(db_session)
    payload = _appointment_payload(str(application.id))
    created = client.post("/api/v1/authority-appointments", json=payload)
    assert created.status_code == 201
    appointment_id = created.json()["id"]

    completed = client.post(
        f"/api/v1/authority-appointments/{appointment_id}/status",
        json={"status": "completed", "reason": "Attended."},
    )
    assert completed.status_code == 200

    actions = set(
        db_session.exec(
            select(AuditLog.action).where(
                AuditLog.entity_type == "authority_appointment"
            )
        ).all()
    )
    assert "authority_appointment_created" in actions
    assert "authority_appointment_completed" in actions


def _create_linked_application(
    client: TestClient, db_session: Session
) -> ApplicationRecord:
    lead = create_lead(db_session, name="Appointment Employee")
    account = client.post(
        "/api/v1/corporate-mobility/accounts",
        json={"legal_name": "Appointment Employer", "primary_country": "Austria"},
    )
    assert account.status_code == 201, account.text
    account_id = account.json()["id"]

    case = client.post(
        f"/api/v1/corporate-mobility/accounts/{account_id}/cases",
        json={
            "case_reference": "APT-CASE-001",
            "destination_country": "Germany",
            "employee_lead_id": str(lead.id),
        },
    )
    assert case.status_code == 201, case.text

    return create_application(db_session, lead, status="approved")


def test_scan_appointment_reminders_creates_event_for_upcoming_appointment(
    client: TestClient, db_session: Session
) -> None:
    application = _create_linked_application(client, db_session)
    scheduled_at = datetime.now(timezone.utc) + timedelta(hours=2)
    appointment = AuthorityAppointment(
        application_id=application.id,
        appointment_type="interview",
        authority_name="German Consulate Mumbai",
        location="Mumbai",
        scheduled_at=scheduled_at,
        timezone="Asia/Kolkata",
        status="scheduled",
        created_by="pytest",
        updated_by="pytest",
    )
    db_session.add(appointment)
    db_session.commit()
    db_session.refresh(appointment)

    result = scan_appointment_reminders(db_session, actor="test")
    assert result["appointments_scanned"] == 1
    assert result["events_created"] == 1

    event = db_session.exec(
        select(AutomationEvent).where(
            AutomationEvent.event_type == "appointment.reminder"
        )
    ).first()
    assert event is not None
    assert event.entity_id == str(appointment.id)

    # Idempotency: a second scan on the same day does not duplicate the event.
    result2 = scan_appointment_reminders(db_session, actor="test")
    assert result2["events_created"] == 0


def test_scan_appointment_reminders_skips_appointments_outside_window(
    client: TestClient, db_session: Session
) -> None:
    application = _create_linked_application(client, db_session)
    scheduled_at = datetime.now(timezone.utc) + timedelta(hours=48)
    appointment = AuthorityAppointment(
        application_id=application.id,
        appointment_type="interview",
        authority_name="German Consulate Mumbai",
        location="Mumbai",
        scheduled_at=scheduled_at,
        timezone="Asia/Kolkata",
        status="scheduled",
        created_by="pytest",
        updated_by="pytest",
    )
    db_session.add(appointment)
    db_session.commit()

    result = scan_appointment_reminders(db_session, actor="test")
    assert result["appointments_scanned"] == 0
    assert result["events_created"] == 0


def test_scan_appointment_reminders_skips_non_scheduled_appointments(
    client: TestClient, db_session: Session
) -> None:
    application = _create_linked_application(client, db_session)
    scheduled_at = datetime.now(timezone.utc) + timedelta(hours=2)
    appointment = AuthorityAppointment(
        application_id=application.id,
        appointment_type="interview",
        authority_name="German Consulate Mumbai",
        location="Mumbai",
        scheduled_at=scheduled_at,
        timezone="Asia/Kolkata",
        status="completed",
        created_by="pytest",
        updated_by="pytest",
    )
    db_session.add(appointment)
    db_session.commit()

    result = scan_appointment_reminders(db_session, actor="test")
    assert result["appointments_scanned"] == 0
    assert result["events_created"] == 0


def test_scan_appointment_reminders_omits_appointments_without_corporate_case(
    client: TestClient, db_session: Session
) -> None:
    lead = create_lead(db_session)
    application = create_application(db_session, lead)
    scheduled_at = datetime.now(timezone.utc) + timedelta(hours=2)
    appointment = AuthorityAppointment(
        application_id=application.id,
        appointment_type="interview",
        authority_name="German Consulate Mumbai",
        location="Mumbai",
        scheduled_at=scheduled_at,
        timezone="Asia/Kolkata",
        status="scheduled",
        created_by="pytest",
        updated_by="pytest",
    )
    db_session.add(appointment)
    db_session.commit()

    result = scan_appointment_reminders(db_session, actor="test")
    assert result["appointments_scanned"] == 1
    assert result["events_created"] == 0
