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


def _case(client, account, reference="CORP-V111-CASE"):
    response = client.post(
        f"/api/v1/corporate-mobility/accounts/{account['id']}/cases",
        json={"case_reference": reference, "destination_country": "Germany"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _sponsor(client, account, name="Northstar Austria GmbH"):
    response = client.post(
        f"/api/v1/corporate-mobility/accounts/{account['id']}/sponsors",
        json={"legal_name": name, "sponsor_type": "employing_entity", "country": "Austria"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_sponsor_assignment_is_account_scoped_and_audited(client, db_session):
    account = _account(client)
    other_account = client.post(
        "/api/v1/corporate-mobility/accounts",
        json={"legal_name": "Other Sponsor AG", "primary_country": "Switzerland"},
    ).json()
    case = _case(client, account)
    sponsor = _sponsor(client, account)
    foreign_sponsor = _sponsor(client, other_account, "Other Sponsor Zurich AG")

    blocked = client.post(
        f"/api/v1/corporate-mobility/cases/{case['id']}/sponsors",
        json={"sponsor_entity_id": foreign_sponsor["id"]},
    )
    assert blocked.status_code == 400
    assert "case corporate account" in blocked.json()["detail"]

    assigned = client.post(
        f"/api/v1/corporate-mobility/cases/{case['id']}/sponsors",
        json={"sponsor_entity_id": sponsor["id"]},
    )
    assert assigned.status_code == 201, assigned.text
    duplicate = client.post(
        f"/api/v1/corporate-mobility/cases/{case['id']}/sponsors",
        json={"sponsor_entity_id": sponsor["id"]},
    )
    assert duplicate.status_code == 400

    actions = db_session.exec(select(AuditLog.action).where(AuditLog.source == "corporate_mobility_v11_1")).all()
    assert "corporate_sponsor_entity_created" in actions
    assert "corporate_case_sponsor_assigned" in actions


def test_dependant_links_are_unique_removable_and_audited(client, db_session):
    account = _account(client)
    case = _case(client, account, "CORP-V111-DEPENDANT")
    dependant_lead = create_lead(db_session, name="Corporate Dependant", target_country="Germany")
    payload = {
        "dependant_lead_id": str(dependant_lead.id),
        "relationship_to_employee": "partner",
        "sponsorship_required": True,
    }
    created = client.post(f"/api/v1/corporate-mobility/cases/{case['id']}/dependants", json=payload)
    assert created.status_code == 201, created.text
    assert created.json()["status"] == "active"
    assert client.post(f"/api/v1/corporate-mobility/cases/{case['id']}/dependants", json=payload).status_code == 400

    removed = client.patch(
        f"/api/v1/corporate-mobility/dependants/{created.json()['id']}", json={"status": "removed"}
    )
    assert removed.status_code == 200
    assert removed.json()["status"] == "removed"
    assert client.patch(
        f"/api/v1/corporate-mobility/dependants/{created.json()['id']}", json={"status": "removed"}
    ).status_code == 400

    actions = db_session.exec(select(AuditLog.action).where(AuditLog.source == "corporate_mobility_v11_1")).all()
    assert "corporate_case_dependant_added" in actions
    assert "corporate_case_dependant_removed" in actions


def test_compliance_events_are_human_reviewed_and_terminal(client):
    account = _account(client)
    case = _case(client, account, "CORP-V111-EVENT")
    created = client.post(
        f"/api/v1/corporate-mobility/cases/{case['id']}/compliance-events",
        json={
            "event_type": "filing_deadline",
            "title": "Submit residence filing",
            "due_at": "2026-09-01T09:00:00Z",
            "evidence_required": True,
        },
    )
    assert created.status_code == 201, created.text
    assert created.json()["human_review_required"] is True
    assert created.json()["status"] == "open"

    missing_reason = client.patch(
        f"/api/v1/corporate-mobility/compliance-events/{created.json()['id']}", json={"status": "waived"}
    )
    assert missing_reason.status_code == 400
    waived = client.patch(
        f"/api/v1/corporate-mobility/compliance-events/{created.json()['id']}",
        json={"status": "waived", "completion_notes": "Human reviewer confirmed not applicable."},
    )
    assert waived.status_code == 200
    assert waived.json()["completed_by"] == "pytest-admin"
    assert client.patch(
        f"/api/v1/corporate-mobility/compliance-events/{created.json()['id']}",
        json={"status": "completed"},
    ).status_code == 400


def test_closed_case_blocks_new_relationships_and_events(client, db_session):
    account = _account(client)
    case = _case(client, account, "CORP-V111-CLOSED")
    sponsor = _sponsor(client, account)
    dependant = create_lead(db_session, name="Blocked Dependant", target_country="Germany")
    assert client.patch(
        f"/api/v1/corporate-mobility/cases/{case['id']}", json={"status": "closed"}
    ).status_code == 200

    assert client.post(
        f"/api/v1/corporate-mobility/cases/{case['id']}/sponsors",
        json={"sponsor_entity_id": sponsor["id"]},
    ).status_code == 400
    assert client.post(
        f"/api/v1/corporate-mobility/cases/{case['id']}/dependants",
        json={"dependant_lead_id": str(dependant.id), "relationship_to_employee": "child"},
    ).status_code == 400
    assert client.post(
        f"/api/v1/corporate-mobility/cases/{case['id']}/compliance-events",
        json={"event_type": "tax", "title": "Tax review", "due_at": "2026-10-01T00:00:00Z"},
    ).status_code == 400


def _task(client, case, **overrides):
    payload = {
        "title": "Prepare employee arrival pack",
        "category": "onboarding",
        "owner_role": "mobility_operator",
        "requires_human_approval": False,
        **overrides,
    }
    response = client.post(
        f"/api/v1/corporate-mobility/cases/{case['id']}/relocation-tasks", json=payload
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_relocation_task_lifecycle_is_controlled_and_audited(client, db_session):
    account = _account(client)
    case = _case(client, account, "CORP-V112-TASK")
    task = _task(client, case)
    assert task["status"] == "planned"

    invalid = client.patch(
        f"/api/v1/corporate-mobility/relocation-tasks/{task['id']}", json={"status": "completed"}
    )
    assert invalid.status_code == 400
    for status in ("ready", "in_progress", "completed"):
        response = client.patch(
            f"/api/v1/corporate-mobility/relocation-tasks/{task['id']}", json={"status": status}
        )
        assert response.status_code == 200, response.text
    assert response.json()["completed_by"] == "pytest-admin"

    terminal = client.patch(
        f"/api/v1/corporate-mobility/relocation-tasks/{task['id']}", json={"status": "cancelled", "work_notes": "Late"}
    )
    assert terminal.status_code == 400
    actions = db_session.exec(select(AuditLog.action).where(AuditLog.source == "corporate_mobility_v11_2")).all()
    assert actions.count("corporate_relocation_task_created") == 1
    assert actions.count("corporate_relocation_task_transitioned") == 3


def test_relocation_task_dependency_must_complete_first(client):
    account = _account(client)
    case = _case(client, account, "CORP-V112-DEPENDENCY")
    predecessor = _task(client, case, title="Secure work authorization", category="immigration")
    dependent = _task(
        client, case, title="Book employee travel", category="travel", depends_on_task_id=predecessor["id"]
    )
    blocked = client.patch(
        f"/api/v1/corporate-mobility/relocation-tasks/{dependent['id']}", json={"status": "ready"}
    )
    assert blocked.status_code == 400
    assert "dependency must be completed" in blocked.json()["detail"]

    for status in ("ready", "in_progress", "completed"):
        assert client.patch(
            f"/api/v1/corporate-mobility/relocation-tasks/{predecessor['id']}", json={"status": status}
        ).status_code == 200
    assert client.patch(
        f"/api/v1/corporate-mobility/relocation-tasks/{dependent['id']}", json={"status": "ready"}
    ).status_code == 200


def test_sensitive_relocation_task_requires_independent_review(client):
    account = _account(client)
    case = _case(client, account, "CORP-V112-REVIEW")
    task = _task(
        client, case, title="Confirm sponsor filing pack", category="immigration", requires_human_approval=True
    )
    for status in ("ready", "in_progress", "completed"):
        response = client.patch(
            f"/api/v1/corporate-mobility/relocation-tasks/{task['id']}",
            json={"status": status, "work_notes": "Evidence pack checked."},
        )
        assert response.status_code == 200, response.text
    assert response.json()["status"] == "awaiting_approval"
    assert response.json()["completed_at"] is None

    self_review = client.post(
        f"/api/v1/corporate-mobility/relocation-tasks/{task['id']}/decisions",
        json={"decision": "approved", "reason": "Looks complete."},
    )
    assert self_review.status_code == 400
    assert "different reviewer" in self_review.json()["detail"]

    decision = client.post(
        f"/api/v1/corporate-mobility/relocation-tasks/{task['id']}/decisions",
        json={"decision": "approved", "reason": "Evidence independently reviewed and accepted."},
        headers={"X-GMAI-Role": "admin", "X-GMAI-User": "independent-reviewer"},
    )
    assert decision.status_code == 201, decision.text
    assert decision.json()["reviewer"] == "independent-reviewer"
    refreshed = client.get(f"/api/v1/corporate-mobility/cases/{case['id']}/relocation-tasks")
    assert refreshed.json()[0]["status"] == "completed"
    assert refreshed.json()[0]["approval_status"] == "approved"


def test_relocation_task_notes_and_closed_case_controls(client):
    account = _account(client)
    case = _case(client, account, "CORP-V112-CONTROLS")
    task = _task(client, case)
    assert client.patch(
        f"/api/v1/corporate-mobility/relocation-tasks/{task['id']}", json={"status": "cancelled"}
    ).status_code == 400
    assert client.patch(
        f"/api/v1/corporate-mobility/cases/{case['id']}", json={"status": "closed"}
    ).status_code == 200
    blocked = client.post(
        f"/api/v1/corporate-mobility/cases/{case['id']}/relocation-tasks",
        json={"title": "Blocked task", "category": "custom"},
    )
    assert blocked.status_code == 400
    assert blocked.json()["detail"] == "Closed corporate mobility cases are immutable"
