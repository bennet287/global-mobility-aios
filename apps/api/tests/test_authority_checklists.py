from __future__ import annotations

from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.domain import (
    ApplicationAuthorityChecklistItem,
    AuditLog,
    AuthorityChecklistTemplate,
)
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
