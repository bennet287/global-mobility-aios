from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.domain import AgencySubmission, ApplicationRecord, AuditLog
from tests.conftest import create_application, create_lead


SUBMITTED_AT = datetime(2026, 8, 1, 10, 0, 0, tzinfo=timezone.utc)


def _submission_payload(application_id: str) -> dict:
    return {
        "application_id": application_id,
        "authority_name": "German Consulate Mumbai",
        "submission_channel": "online",
        "submitted_at": SUBMITTED_AT.isoformat().replace("+00:00", "Z"),
        "reference_number": "SUB-12345",
        "tracking_url": "https://example.com/track/SUB-12345",
        "notes": "Submitted through the official portal.",
    }


def _create_application(session: Session) -> ApplicationRecord:
    lead = create_lead(session)
    return create_application(session, lead)


def test_create_submission_and_read_back(client: TestClient, db_session: Session) -> None:
    application = _create_application(db_session)
    payload = _submission_payload(str(application.id))

    response = client.post("/api/v1/agency-submissions", json=payload)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["authority_name"] == "German Consulate Mumbai"
    assert data["submission_channel"] == "online"
    assert data["status"] == "submitted"
    assert data["created_by"] == "pytest-admin"

    read = client.get(f"/api/v1/agency-submissions/{data['id']}")
    assert read.status_code == 200
    assert read.json()["id"] == data["id"]

    db_record = db_session.get(AgencySubmission, UUID(data["id"]))
    assert db_record is not None
    assert db_record.application_id == application.id


def test_list_submissions_for_application_and_filter_by_status(
    client: TestClient, db_session: Session
) -> None:
    application = _create_application(db_session)
    payload = _submission_payload(str(application.id))

    first = client.post("/api/v1/agency-submissions", json=payload)
    assert first.status_code == 201

    payload["submission_channel"] = "courier"
    payload["submitted_at"] = "2026-08-02T10:00:00Z"
    second = client.post("/api/v1/agency-submissions", json=payload)
    assert second.status_code == 201
    second_id = second.json()["id"]

    acknowledged = client.post(
        f"/api/v1/agency-submissions/{second_id}/status",
        json={"status": "acknowledged", "reason": "Receipt confirmed by consulate."},
    )
    assert acknowledged.status_code == 200

    listed = client.get(f"/api/v1/agency-submissions?application_id={application.id}")
    assert listed.status_code == 200
    items = listed.json()
    assert len(items) == 2

    filtered = client.get(
        f"/api/v1/agency-submissions?application_id={application.id}&status=acknowledged"
    )
    assert filtered.status_code == 200
    filtered_items = filtered.json()
    assert len(filtered_items) == 1
    assert filtered_items[0]["id"] == second_id


def test_status_lifecycle(client: TestClient, db_session: Session) -> None:
    application = _create_application(db_session)
    payload = _submission_payload(str(application.id))
    created = client.post("/api/v1/agency-submissions", json=payload)
    assert created.status_code == 201
    submission_id = created.json()["id"]

    for status, reason in [
        ("acknowledged", "Receipt email received."),
        ("under_review", "Status moved to under review."),
        ("decision_received", "Authority decision received."),
    ]:
        response = client.post(
            f"/api/v1/agency-submissions/{submission_id}/status",
            json={"status": status, "reason": reason},
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["status"] == status

    terminal = client.post(
        f"/api/v1/agency-submissions/{submission_id}/status",
        json={"status": "returned", "reason": "Mistake."},
    )
    assert terminal.status_code == 409
    assert "terminal" in terminal.json()["detail"].lower()


def test_reject_invalid_status_transition(client: TestClient, db_session: Session) -> None:
    application = _create_application(db_session)
    payload = _submission_payload(str(application.id))
    created = client.post("/api/v1/agency-submissions", json=payload)
    assert created.status_code == 201
    submission_id = created.json()["id"]

    skip = client.post(
        f"/api/v1/agency-submissions/{submission_id}/status",
        json={"status": "under_review", "reason": "Skipping acknowledged."},
    )
    assert skip.status_code == 409
    assert "transition" in skip.json()["detail"].lower()

    invalid = client.post(
        f"/api/v1/agency-submissions/{submission_id}/status",
        json={"status": "not_a_status", "reason": "Invalid."},
    )
    assert invalid.status_code == 422


def test_create_submission_for_missing_application(client: TestClient) -> None:
    payload = _submission_payload(str(uuid4()))
    response = client.post("/api/v1/agency-submissions", json=payload)
    assert response.status_code == 404


def test_audit_log_entries_are_created(client: TestClient, db_session: Session) -> None:
    application = _create_application(db_session)
    payload = _submission_payload(str(application.id))
    created = client.post("/api/v1/agency-submissions", json=payload)
    assert created.status_code == 201
    submission_id = created.json()["id"]

    updated = client.post(
        f"/api/v1/agency-submissions/{submission_id}/status",
        json={"status": "acknowledged", "reason": "Receipt confirmed."},
    )
    assert updated.status_code == 200

    actions = set(
        db_session.exec(
            select(AuditLog.action).where(
                AuditLog.entity_type == "agency_submission"
            )
        ).all()
    )
    assert "agency_submission_created" in actions
    assert "agency_submission_acknowledged" in actions
