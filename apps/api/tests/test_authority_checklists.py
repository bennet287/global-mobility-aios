from __future__ import annotations

from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.domain import (
    ApplicationAuthorityChecklistItem,
    AuditLog,
    AuthorityChecklistTemplate,
    AutomationEvent,
)
from app.services.authority_checklists import scan_checklist_reminders
from tests.conftest import create_application, create_lead


def _template_payload() -> dict:
    return {
        "authority_name": "German Consulate Mumbai",
        "country": "India",
        "item_key": "passport_copy",
        "item_label": "Copy of passport (data page)",
        "category": "document",
        "is_required": True,
        "sort_order": 10,
    }


def test_create_and_list_template(client: TestClient, db_session: Session) -> None:
    response = client.post(
        "/api/v1/authority-checklist-templates", json=_template_payload()
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["authority_name"] == "German Consulate Mumbai"
    assert data["item_key"] == "passport_copy"
    assert data["category"] == "document"

    listed = client.get("/api/v1/authority-checklist-templates")
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_apply_template_to_application(client: TestClient, db_session: Session) -> None:
    client.post("/api/v1/authority-checklist-templates", json=_template_payload())
    client.post(
        "/api/v1/authority-checklist-templates",
        json={
            **(_template_payload()),
            "item_key": "appointment_letter",
            "item_label": "Appointment confirmation letter",
            "category": "document",
            "sort_order": 20,
        },
    )

    lead = create_lead(db_session)
    application = create_application(db_session, lead)

    applied = client.post(
        "/api/v1/authority-checklist-templates/apply",
        json={
            "application_id": str(application.id),
            "authority_name": "German Consulate Mumbai",
        },
    )
    assert applied.status_code == 201, applied.text
    items = applied.json()
    assert len(items) == 2
    assert all(item["application_id"] == str(application.id) for item in items)
    assert all(item["status"] == "pending" for item in items)

    per_app = client.get(
        f"/api/v1/applications/{application.id}/authority-checklist"
    )
    assert per_app.status_code == 200
    assert len(per_app.json()) == 2


def test_create_manual_checklist_item(client: TestClient, db_session: Session) -> None:
    lead = create_lead(db_session)
    application = create_application(db_session, lead)

    item = client.post(
        "/api/v1/application-authority-checklist-items",
        json={
            "application_id": str(application.id),
            "authority_name": "German Consulate Mumbai",
            "item_key": "biometric_receipt",
            "item_label": "Biometric collection receipt",
            "category": "document",
            "is_required": False,
        },
    )
    assert item.status_code == 201, item.text
    data = item.json()
    assert data["item_key"] == "biometric_receipt"
    assert data["status"] == "pending"

    db_record = db_session.get(ApplicationAuthorityChecklistItem, UUID(data["id"]))
    assert db_record is not None


def test_update_checklist_item_status(client: TestClient, db_session: Session) -> None:
    lead = create_lead(db_session)
    application = create_application(db_session, lead)
    item = client.post(
        "/api/v1/application-authority-checklist-items",
        json={
            "application_id": str(application.id),
            "authority_name": "German Consulate Mumbai",
            "item_key": "passport_copy",
            "item_label": "Copy of passport",
            "category": "document",
        },
    )
    assert item.status_code == 201
    item_id = item.json()["id"]

    updated = client.post(
        f"/api/v1/application-authority-checklist-items/{item_id}/status",
        json={"status": "completed", "notes": "Uploaded and verified."},
    )
    assert updated.status_code == 200
    data = updated.json()
    assert data["status"] == "completed"
    assert data["notes"] == "Uploaded and verified."

    invalid = client.post(
        f"/api/v1/application-authority-checklist-items/{item_id}/status",
        json={"status": "not_a_status"},
    )
    assert invalid.status_code == 422


def test_delete_checklist_item(client: TestClient, db_session: Session) -> None:
    lead = create_lead(db_session)
    application = create_application(db_session, lead)
    item = client.post(
        "/api/v1/application-authority-checklist-items",
        json={
            "application_id": str(application.id),
            "authority_name": "German Consulate Mumbai",
            "item_key": "old_form",
            "item_label": "Old form no longer required",
            "category": "form",
        },
    )
    assert item.status_code == 201
    item_id = item.json()["id"]

    deleted = client.delete(f"/api/v1/application-authority-checklist-items/{item_id}")
    assert deleted.status_code == 204

    assert (
        db_session.get(ApplicationAuthorityChecklistItem, UUID(item_id)) is None
    )


def test_apply_template_is_idempotent(client: TestClient, db_session: Session) -> None:
    client.post("/api/v1/authority-checklist-templates", json=_template_payload())
    lead = create_lead(db_session)
    application = create_application(db_session, lead)

    first = client.post(
        "/api/v1/authority-checklist-templates/apply",
        json={
            "application_id": str(application.id),
            "authority_name": "German Consulate Mumbai",
        },
    )
    assert first.status_code == 201

    second = client.post(
        "/api/v1/authority-checklist-templates/apply",
        json={
            "application_id": str(application.id),
            "authority_name": "German Consulate Mumbai",
        },
    )
    assert second.status_code == 201
    assert len(second.json()) == 0

    per_app = client.get(
        f"/api/v1/applications/{application.id}/authority-checklist"
    )
    assert len(per_app.json()) == 1


def test_audit_log_entries_are_created(client: TestClient, db_session: Session) -> None:
    lead = create_lead(db_session)
    application = create_application(db_session, lead)
    item = client.post(
        "/api/v1/application-authority-checklist-items",
        json={
            "application_id": str(application.id),
            "authority_name": "German Consulate Mumbai",
            "item_key": "passport_copy",
            "item_label": "Copy of passport",
            "category": "document",
        },
    )
    assert item.status_code == 201
    item_id = item.json()["id"]

    client.post(
        f"/api/v1/application-authority-checklist-items/{item_id}/status",
        json={"status": "completed"},
    )

    actions = set(
        db_session.exec(
            select(AuditLog.action).where(
                AuditLog.entity_type == "application_authority_checklist_item"
            )
        ).all()
    )
    assert "application_checklist_item_created" in actions
    assert "application_checklist_item_completed" in actions


def _create_linked_application(
    client: TestClient, db_session: Session
) -> ApplicationRecord:
    lead = create_lead(db_session, name="Checklist Employee")
    account = client.post(
        "/api/v1/corporate-mobility/accounts",
        json={"legal_name": "Checklist Employer", "primary_country": "Austria"},
    )
    assert account.status_code == 201, account.text
    account_id = account.json()["id"]

    case = client.post(
        f"/api/v1/corporate-mobility/accounts/{account_id}/cases",
        json={
            "case_reference": "CHK-CASE-001",
            "destination_country": "Germany",
            "employee_lead_id": str(lead.id),
        },
    )
    assert case.status_code == 201, case.text

    return create_application(db_session, lead, status="approved")


def _submission_payload(application_id: str) -> dict:
    return {
        "application_id": application_id,
        "authority_name": "German Consulate Mumbai",
        "submission_channel": "online",
        "submitted_at": "2026-08-01T14:00:00Z",
        "reference_number": "SUB-123",
        "notes": "Submitted through portal.",
    }


def test_submission_blocked_by_pending_required_checklist_item(
    client: TestClient, db_session: Session
) -> None:
    client.post("/api/v1/authority-checklist-templates", json=_template_payload())
    lead = create_lead(db_session)
    application = create_application(db_session, lead)

    applied = client.post(
        "/api/v1/authority-checklist-templates/apply",
        json={
            "application_id": str(application.id),
            "authority_name": "German Consulate Mumbai",
        },
    )
    assert applied.status_code == 201, applied.text
    item_id = applied.json()[0]["id"]

    blocked = client.post(
        "/api/v1/agency-submissions", json=_submission_payload(str(application.id))
    )
    assert blocked.status_code == 409, blocked.text
    assert "blocked" in blocked.json()["detail"].lower()

    client.post(
        f"/api/v1/application-authority-checklist-items/{item_id}/status",
        json={"status": "completed", "notes": "Ready."},
    )
    allowed = client.post(
        "/api/v1/agency-submissions", json=_submission_payload(str(application.id))
    )
    assert allowed.status_code == 201, allowed.text


def test_submission_allowed_when_required_item_marked_not_applicable(
    client: TestClient, db_session: Session
) -> None:
    client.post("/api/v1/authority-checklist-templates", json=_template_payload())
    lead = create_lead(db_session)
    application = create_application(db_session, lead)

    applied = client.post(
        "/api/v1/authority-checklist-templates/apply",
        json={
            "application_id": str(application.id),
            "authority_name": "German Consulate Mumbai",
        },
    )
    assert applied.status_code == 201
    item_id = applied.json()[0]["id"]

    client.post(
        f"/api/v1/application-authority-checklist-items/{item_id}/status",
        json={"status": "not_applicable"},
    )
    allowed = client.post(
        "/api/v1/agency-submissions", json=_submission_payload(str(application.id))
    )
    assert allowed.status_code == 201, allowed.text


def test_checklist_reminder_creates_automation_event(
    client: TestClient, db_session: Session
) -> None:
    application = _create_linked_application(client, db_session)
    item = client.post(
        "/api/v1/application-authority-checklist-items",
        json={
            "application_id": str(application.id),
            "authority_name": "German Consulate Mumbai",
            "item_key": "passport_copy",
            "item_label": "Copy of passport",
            "category": "document",
            "is_required": True,
        },
    )
    assert item.status_code == 201, item.text

    reminders = client.post(
        f"/api/v1/applications/{application.id}/authority-checklist/reminders"
    )
    assert reminders.status_code == 201, reminders.text
    data = reminders.json()
    assert len(data) == 1
    assert data[0]["event_type"] == "authority_checklist.reminder"

    event = db_session.exec(
        select(AutomationEvent).where(
            AutomationEvent.event_type == "authority_checklist.reminder"
        )
    ).first()
    assert event is not None
    assert event.entity_id == item.json()["id"]
    assert event.payload_json is not None
    assert "application_id" in event.payload_json


def test_checklist_reminder_omitted_without_corporate_case(
    client: TestClient, db_session: Session
) -> None:
    lead = create_lead(db_session)
    application = create_application(db_session, lead)
    item = client.post(
        "/api/v1/application-authority-checklist-items",
        json={
            "application_id": str(application.id),
            "authority_name": "German Consulate Mumbai",
            "item_key": "passport_copy",
            "item_label": "Copy of passport",
            "category": "document",
            "is_required": True,
        },
    )
    assert item.status_code == 201, item.text

    reminders = client.post(
        f"/api/v1/applications/{application.id}/authority-checklist/reminders"
    )
    assert reminders.status_code == 201, reminders.text
    assert reminders.json() == []

    event = db_session.exec(
        select(AutomationEvent).where(
            AutomationEvent.event_type == "authority_checklist.reminder"
        )
    ).first()
    assert event is None


def test_scan_checklist_reminders_creates_event_for_pending_item(
    client: TestClient, db_session: Session
) -> None:
    application = _create_linked_application(client, db_session)
    item = client.post(
        "/api/v1/application-authority-checklist-items",
        json={
            "application_id": str(application.id),
            "authority_name": "German Consulate Mumbai",
            "item_key": "passport_copy",
            "item_label": "Copy of passport",
            "category": "document",
            "is_required": True,
        },
    )
    assert item.status_code == 201, item.text
    item_id = item.json()["id"]

    result = scan_checklist_reminders(db_session, actor="test")
    assert result == {"applications_scanned": 1, "events_created": 1}

    event = db_session.exec(
        select(AutomationEvent).where(
            AutomationEvent.event_type == "authority_checklist.reminder"
        )
    ).first()
    assert event is not None
    assert event.entity_id == item_id

    # Idempotency: second scan on the same day does not duplicate the event.
    result2 = scan_checklist_reminders(db_session, actor="test")
    assert result2 == {"applications_scanned": 1, "events_created": 0}


def test_scan_checklist_reminders_skips_completed_items(
    client: TestClient, db_session: Session
) -> None:
    application = _create_linked_application(client, db_session)
    item = client.post(
        "/api/v1/application-authority-checklist-items",
        json={
            "application_id": str(application.id),
            "authority_name": "German Consulate Mumbai",
            "item_key": "passport_copy",
            "item_label": "Copy of passport",
            "category": "document",
            "is_required": True,
        },
    )
    assert item.status_code == 201, item.text
    item_id = item.json()["id"]

    client.post(
        f"/api/v1/application-authority-checklist-items/{item_id}/status",
        json={"status": "completed"},
    )

    result = scan_checklist_reminders(db_session, actor="test")
    assert result == {"applications_scanned": 0, "events_created": 0}


def test_scan_checklist_reminders_omits_items_without_corporate_case(
    client: TestClient, db_session: Session
) -> None:
    lead = create_lead(db_session)
    application = create_application(db_session, lead)
    item = client.post(
        "/api/v1/application-authority-checklist-items",
        json={
            "application_id": str(application.id),
            "authority_name": "German Consulate Mumbai",
            "item_key": "passport_copy",
            "item_label": "Copy of passport",
            "category": "document",
            "is_required": True,
        },
    )
    assert item.status_code == 201, item.text

    result = scan_checklist_reminders(db_session, actor="test")
    assert result == {"applications_scanned": 1, "events_created": 0}
