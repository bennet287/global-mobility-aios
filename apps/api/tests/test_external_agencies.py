from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.domain import AuditLog, ExternalAgency, ExternalAgencyAssignment
from app.services.external_agencies import (
    evaluate_assignment_sla,
    scan_assignment_sla_evaluations,
)
from tests.conftest import create_application, create_lead


def _agency_payload() -> dict:
    return {
        "name": "Mumbai Visa Services Pvt Ltd",
        "country": "India",
        "city": "Mumbai",
        "contact_email": "ops@mumbaivisas.example",
        "contact_phone": "+91-22-1234-5678",
        "website": "https://mumbaivisas.example",
        "notes": "Preferred courier partner.",
    }


def test_create_and_list_external_agency(client: TestClient, db_session: Session) -> None:
    response = client.post("/api/v1/external-agencies", json=_agency_payload())
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["name"] == "Mumbai Visa Services Pvt Ltd"
    assert data["status"] == "active"
    assert data["created_by"] == "pytest-admin"

    listed = client.get("/api/v1/external-agencies")
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_suspend_external_agency(client: TestClient, db_session: Session) -> None:
    created = client.post("/api/v1/external-agencies", json=_agency_payload())
    assert created.status_code == 201
    agency_id = created.json()["id"]

    suspended = client.post(
        f"/api/v1/external-agencies/{agency_id}/status",
        json={"status": "suspended", "reason": "Contract renewal pending."},
    )
    assert suspended.status_code == 200
    assert suspended.json()["status"] == "suspended"


def test_assign_application_to_agency(client: TestClient, db_session: Session) -> None:
    lead = create_lead(db_session)
    application = create_application(db_session, lead)
    agency = client.post("/api/v1/external-agencies", json=_agency_payload())
    assert agency.status_code == 201
    agency_id = agency.json()["id"]

    payload = {
        "application_id": str(application.id),
        "external_agency_id": agency_id,
        "agency_reference_number": "MVS-REF-001",
        "notes": "Handoff to local agency.",
    }
    assignment = client.post("/api/v1/external-agency-assignments", json=payload)
    assert assignment.status_code == 201, assignment.text
    data = assignment.json()
    assert data["status"] == "assigned"
    assert data["agency_reference_number"] == "MVS-REF-001"

    db_record = db_session.get(ExternalAgencyAssignment, UUID(data["id"]))
    assert db_record is not None


def test_assignment_status_lifecycle(client: TestClient, db_session: Session) -> None:
    lead = create_lead(db_session)
    application = create_application(db_session, lead)
    agency = client.post("/api/v1/external-agencies", json=_agency_payload())
    assert agency.status_code == 201
    agency_id = agency.json()["id"]

    assignment = client.post(
        "/api/v1/external-agency-assignments",
        json={
            "application_id": str(application.id),
            "external_agency_id": agency_id,
        },
    )
    assert assignment.status_code == 201
    assignment_id = assignment.json()["id"]

    for status, reason in [
        ("in_progress", "Agency started processing."),
        ("handed_off", "Documents handed to authority."),
        ("completed", "Authority decision received."),
    ]:
        response = client.post(
            f"/api/v1/external-agency-assignments/{assignment_id}/status",
            json={"status": status, "reason": reason},
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["status"] == status
        if status == "handed_off":
            assert data["handoff_at"] is not None
        if status == "completed":
            assert data["completed_at"] is not None

    terminal = client.post(
        f"/api/v1/external-agency-assignments/{assignment_id}/status",
        json={"status": "cancelled", "reason": "Mistake."},
    )
    assert terminal.status_code == 409
    assert "terminal" in terminal.json()["detail"].lower()


def test_reject_duplicate_active_assignment(client: TestClient, db_session: Session) -> None:
    lead = create_lead(db_session)
    application = create_application(db_session, lead)
    agency = client.post("/api/v1/external-agencies", json=_agency_payload())
    assert agency.status_code == 201
    agency_id = agency.json()["id"]

    first = client.post(
        "/api/v1/external-agency-assignments",
        json={"application_id": str(application.id), "external_agency_id": agency_id},
    )
    assert first.status_code == 201

    second = client.post(
        "/api/v1/external-agency-assignments",
        json={
            "application_id": str(application.id),
            "external_agency_id": agency_id,
            "agency_reference_number": "SECOND",
        },
    )
    assert second.status_code == 409
    assert "already has an active" in second.json()["detail"].lower()


def test_cannot_assign_to_inactive_agency(client: TestClient, db_session: Session) -> None:
    lead = create_lead(db_session)
    application = create_application(db_session, lead)
    agency = client.post("/api/v1/external-agencies", json=_agency_payload())
    assert agency.status_code == 201
    agency_id = agency.json()["id"]

    client.post(
        f"/api/v1/external-agencies/{agency_id}/status",
        json={"status": "suspended", "reason": "Contract renewal pending."},
    )

    assignment = client.post(
        "/api/v1/external-agency-assignments",
        json={"application_id": str(application.id), "external_agency_id": agency_id},
    )
    assert assignment.status_code == 400
    assert "active" in assignment.json()["detail"].lower()


def test_audit_log_entries_are_created(client: TestClient, db_session: Session) -> None:
    lead = create_lead(db_session)
    application = create_application(db_session, lead)
    agency = client.post("/api/v1/external-agencies", json=_agency_payload())
    assert agency.status_code == 201
    agency_id = agency.json()["id"]

    assignment = client.post(
        "/api/v1/external-agency-assignments",
        json={
            "application_id": str(application.id),
            "external_agency_id": agency_id,
        },
    )
    assert assignment.status_code == 201
    assignment_id = assignment.json()["id"]

    client.post(
        f"/api/v1/external-agency-assignments/{assignment_id}/status",
        json={"status": "in_progress", "reason": "Started."},
    )

    actions = set(
        db_session.exec(
            select(AuditLog.action).where(
                AuditLog.entity_type == "external_agency_assignment"
            )
        ).all()
    )
    assert "external_agency_assignment_created" in actions
    assert "external_agency_assignment_in_progress" in actions


def test_agency_create_includes_default_sla_due_hours(
    client: TestClient, db_session: Session
) -> None:
    response = client.post("/api/v1/external-agencies", json=_agency_payload())
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["sla_due_hours"] == 72


def test_assignment_creation_sets_sla_due_at_and_on_track(
    client: TestClient, db_session: Session
) -> None:
    lead = create_lead(db_session)
    application = create_application(db_session, lead)
    agency = client.post("/api/v1/external-agencies", json=_agency_payload())
    assert agency.status_code == 201
    agency_id = agency.json()["id"]

    assignment = client.post(
        "/api/v1/external-agency-assignments",
        json={"application_id": str(application.id), "external_agency_id": agency_id},
    )
    assert assignment.status_code == 201, assignment.text
    data = assignment.json()
    assert data["sla_due_at"] is not None
    assert data["sla_status"] == "on_track"
    assert data["sla_breached_at"] is None


def test_assignment_completed_before_due_is_completed_sla(
    client: TestClient, db_session: Session
) -> None:
    lead = create_lead(db_session)
    application = create_application(db_session, lead)
    agency = client.post("/api/v1/external-agencies", json=_agency_payload())
    assert agency.status_code == 201
    agency_id = agency.json()["id"]

    assignment = client.post(
        "/api/v1/external-agency-assignments",
        json={"application_id": str(application.id), "external_agency_id": agency_id},
    )
    assert assignment.status_code == 201
    assignment_id = assignment.json()["id"]

    for status, reason in [
        ("in_progress", "Agency started processing."),
        ("handed_off", "Documents handed to authority."),
        ("completed", "Decision received."),
    ]:
        response = client.post(
            f"/api/v1/external-agency-assignments/{assignment_id}/status",
            json={"status": status, "reason": reason},
        )
        assert response.status_code == 200, response.text

    assert response.json()["sla_status"] == "completed"


def test_scan_marks_breached_assignment(
    client: TestClient, db_session: Session
) -> None:
    lead = create_lead(db_session)
    application = create_application(db_session, lead)
    agency = client.post("/api/v1/external-agencies", json=_agency_payload())
    assert agency.status_code == 201
    agency_id = agency.json()["id"]

    assignment_response = client.post(
        "/api/v1/external-agency-assignments",
        json={"application_id": str(application.id), "external_agency_id": agency_id},
    )
    assert assignment_response.status_code == 201
    assignment_id = UUID(assignment_response.json()["id"])
    assignment = db_session.get(ExternalAgencyAssignment, assignment_id)
    assert assignment is not None

    # Force the SLA due date into the past.
    assignment.sla_due_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db_session.add(assignment)
    db_session.commit()

    result = scan_assignment_sla_evaluations(db_session, actor="test")
    assert result["sla_status_changes"] >= 1

    db_session.refresh(assignment)
    assert assignment.sla_status == "breached"
    assert assignment.sla_breached_at is not None


def test_assignment_completed_after_due_is_breached(
    client: TestClient, db_session: Session
) -> None:
    lead = create_lead(db_session)
    application = create_application(db_session, lead)
    agency_record = ExternalAgency(
        name="Late Agency",
        status="active",
        sla_due_hours=1,
        created_by="pytest",
        updated_by="pytest",
    )
    db_session.add(agency_record)
    db_session.commit()
    db_session.refresh(agency_record)

    assignment = ExternalAgencyAssignment(
        application_id=application.id,
        external_agency_id=agency_record.id,
        status="assigned",
        sla_due_at=datetime.now(timezone.utc) - timedelta(hours=2),
        created_by="pytest",
        updated_by="pytest",
    )
    db_session.add(assignment)
    db_session.commit()
    db_session.refresh(assignment)

    evaluate_assignment_sla(assignment)
    assert assignment.sla_status == "breached"

    assignment.status = "completed"
    assignment.completed_at = datetime.now(timezone.utc) - timedelta(hours=1)
    evaluate_assignment_sla(assignment)
    assert assignment.sla_status == "breached"
