from datetime import datetime, timezone

from sqlmodel import select

from app.models.domain import AuditLog
from tests.conftest import create_lead


def _account(client):
    response = client.post(
        "/api/v1/corporate-mobility/accounts",
        json={
            "legal_name": "Northstar Mobility GmbH",
            "display_name": "Northstar",
            "primary_country": "Austria",
            "registration_number": "FN-TEST-1100",
            "contact_name": "Mara Klein",
            "contact_email": "mara@example.com",
            "compliance_owner": "Vienna Mobility Team",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_account_and_case_creation_are_audited(client, db_session):
    lead = create_lead(db_session, name="Corporate Employee", target_country="Germany")
    account = _account(client)

    case_response = client.post(
        f"/api/v1/corporate-mobility/accounts/{account['id']}/cases",
        json={
            "employee_lead_id": str(lead.id),
            "case_type": "employee_relocation",
            "origin_country": "Austria",
            "destination_country": "Germany",
            "sponsor_name": "Northstar Mobility GmbH",
            "compliance_due_date": "2026-08-01T00:00:00Z",
            "target_start_date": "2026-09-01T00:00:00Z",
        },
    )
    assert case_response.status_code == 201, case_response.text
    case = case_response.json()
    assert case["status"] == "draft"
    assert case["human_review_required"] is True
    assert case["case_reference"].startswith("CORP-")

    detail = client.get(f"/api/v1/corporate-mobility/accounts/{account['id']}")
    assert detail.status_code == 200
    assert [item["id"] for item in detail.json()["cases"]] == [case["id"]]

    logs = db_session.exec(
        select(AuditLog).where(AuditLog.source == "corporate_mobility_v11_0").order_by(AuditLog.created_at)
    ).all()
    assert [log.action for log in logs] == [
        "corporate_account_created",
        "corporate_mobility_case_created",
    ]
    assert all(log.actor == "pytest-admin" for log in logs)


def test_case_requires_existing_employee_and_active_account(client, db_session):
    account = _account(client)
    missing = client.post(
        f"/api/v1/corporate-mobility/accounts/{account['id']}/cases",
        json={
            "employee_lead_id": "00000000-0000-0000-0000-000000000001",
            "destination_country": "Germany",
        },
    )
    assert missing.status_code == 404
    assert missing.json()["detail"] == "Employee lead not found"

    suspended = client.patch(
        f"/api/v1/corporate-mobility/accounts/{account['id']}",
        json={"account_status": "suspended"},
    )
    assert suspended.status_code == 200
    blocked = client.post(
        f"/api/v1/corporate-mobility/accounts/{account['id']}/cases",
        json={"destination_country": "Germany"},
    )
    assert blocked.status_code == 400
    assert "active accounts" in blocked.json()["detail"]


def test_case_status_transitions_are_controlled(client):
    account = _account(client)
    created = client.post(
        f"/api/v1/corporate-mobility/accounts/{account['id']}/cases",
        json={"case_reference": "CORP-CONTROLLED-1", "destination_country": "Canada"},
    )
    case_id = created.json()["id"]

    invalid = client.patch(
        f"/api/v1/corporate-mobility/cases/{case_id}",
        json={"status": "completed"},
    )
    assert invalid.status_code == 400
    assert "cannot transition" in invalid.json()["detail"]

    active = client.patch(
        f"/api/v1/corporate-mobility/cases/{case_id}",
        json={"status": "active"},
    )
    assert active.status_code == 200
    completed = client.patch(
        f"/api/v1/corporate-mobility/cases/{case_id}",
        json={"status": "completed"},
    )
    assert completed.status_code == 200
    assert completed.json()["human_review_required"] is True


def test_compliance_due_date_must_precede_target_start(client):
    account = _account(client)
    response = client.post(
        f"/api/v1/corporate-mobility/accounts/{account['id']}/cases",
        json={
            "destination_country": "Singapore",
            "compliance_due_date": datetime(2026, 10, 1, tzinfo=timezone.utc).isoformat(),
            "target_start_date": datetime(2026, 9, 1, tzinfo=timezone.utc).isoformat(),
        },
    )
    assert response.status_code == 422


def test_closed_case_is_immutable(client):
    account = _account(client)
    created = client.post(
        f"/api/v1/corporate-mobility/accounts/{account['id']}/cases",
        json={"case_reference": "CORP-CLOSED-1", "destination_country": "Canada"},
    )
    case_id = created.json()["id"]
    closed = client.patch(
        f"/api/v1/corporate-mobility/cases/{case_id}",
        json={"status": "closed"},
    )
    assert closed.status_code == 200

    mutation = client.patch(
        f"/api/v1/corporate-mobility/cases/{case_id}",
        json={"destination_country": "Australia"},
    )
    assert mutation.status_code == 400
    assert mutation.json()["detail"] == "Closed corporate mobility cases are immutable"


def test_read_only_role_cannot_mutate_corporate_mobility(raw_client):
    raw_client.headers.update({"X-GMAI-Role": "read_only", "X-GMAI-User": "readonly-user"})
    response = raw_client.post(
        "/api/v1/corporate-mobility/accounts",
        json={"legal_name": "Blocked Corp", "primary_country": "Austria"},
    )
    assert response.status_code == 403
