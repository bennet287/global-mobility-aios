from __future__ import annotations

from uuid import UUID

from sqlmodel import Session, func, select

from app.models.domain import (
    AuditLog,
    AutomationDelivery,
    AutomationEvent,
)
from app.tasks.automation_tasks import dispatch_automation_deliveries_task


def _headers(role: str, user: str) -> dict[str, str]:
    return {"X-GMAI-Role": role, "X-GMAI-User": user}


def _account(client, name: str = "Automation Employer") -> dict:
    response = client.post(
        "/api/v1/corporate-mobility/accounts",
        json={"legal_name": name, "primary_country": "Austria"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _case(client, account_id: str, reference: str) -> dict:
    response = client.post(
        f"/api/v1/corporate-mobility/accounts/{account_id}/cases",
        json={
            "case_reference": reference,
            "destination_country": "Germany",
            "notes": "Internal case note must never enter an automation payload.",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _rule(client, account_id: str, **overrides) -> dict:
    payload = {
        "corporate_account_id": account_id,
        "name": "Case creation notifications",
        "event_type": "case.created",
        "channels": ["email", "messaging", "calendar", "crm"],
        "destinations": {
            "email": "mobility-team",
            "messaging": "case-operations",
            "calendar": "mobility-calendar",
            "crm": "corporate-case-sync",
        },
        "subject_template": "{case_reference}: new mobility case",
        "body_template": "{case_reference} is {case_status} for {destination_country}.",
        "requires_human_approval": True,
    }
    payload.update(overrides)
    response = client.post("/api/v1/automation/rules", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _connector(client, account_id: str, channel: str, provider_type: str = "console", **overrides) -> dict:
    payload = {
        "corporate_account_id": account_id,
        "channel": channel,
        "provider_type": provider_type,
        "credentials": {},
        "from_address": "automation@example.com",
        "sender_label": "GMAI Automation",
    }
    payload.update(overrides)
    response = client.post("/api/v1/automation/connectors", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_case_event_creates_review_gated_multichannel_outbox(
    raw_client,
    db_session: Session,
) -> None:
    raw_client.headers.update(_headers("admin", "automation-author"))
    account = _account(raw_client)
    _rule(raw_client, account["id"])
    case = _case(raw_client, account["id"], "AUTO-CASE-001")

    events = raw_client.get(
        f"/api/v1/automation/events?corporate_account_id={account['id']}"
    )
    assert events.status_code == 200
    created_event = next(
        item for item in events.json() if item["event_type"] == "case.created"
    )
    assert created_event["delivery_count"] == 4
    assert "notes" not in created_event["payload"]

    deliveries = raw_client.get(
        f"/api/v1/automation/deliveries?corporate_account_id={account['id']}"
    )
    assert deliveries.status_code == 200
    payload = deliveries.json()
    assert {item["channel"] for item in payload} == {
        "email",
        "messaging",
        "calendar",
        "crm",
    }
    assert {item["status"] for item in payload} == {"pending_review"}
    assert all(item["requires_human_approval"] for item in payload)
    assert all(case["case_reference"] in item["subject"] for item in payload)

    delivery_id = payload[0]["id"]
    same_actor = raw_client.post(
        f"/api/v1/automation/deliveries/{delivery_id}/decision",
        json={"decision": "approved", "reason": "Reviewed against the case event."},
    )
    assert same_actor.status_code == 400
    assert "different reviewer" in same_actor.json()["detail"]

    raw_client.headers.update(_headers("reviewer", "automation-reviewer"))
    approved = raw_client.post(
        f"/api/v1/automation/deliveries/{delivery_id}/decision",
        json={"decision": "approved", "reason": "Content and destination verified."},
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "ready"
    assert approved.json()["reviewed_by"] == "automation-reviewer"

    raw_client.headers.update(_headers("operator", "connector-worker"))
    dispatched = raw_client.post(
        f"/api/v1/automation/deliveries/{delivery_id}/dispatch-record",
        json={"provider_message_id": "provider-0001"},
    )
    assert dispatched.status_code == 200, dispatched.text
    assert dispatched.json()["status"] == "dispatched"
    assert dispatched.json()["attempt_count"] == 1

    actions = set(
        db_session.exec(
            select(AuditLog.action).where(AuditLog.source == "automation_v12_3")
        ).all()
    )
    assert {
        "automation_rule_created",
        "automation_event_captured",
        "automation_delivery_approved",
        "automation_delivery_dispatched",
    }.issubset(actions)


def test_event_ingest_is_idempotent_and_key_conflicts_fail_closed(
    client,
    db_session: Session,
) -> None:
    account = _account(client, "Idempotent Employer")
    _rule(
        client,
        account["id"],
        event_type="case.status_changed",
        channels=["crm"],
        destinations={"crm": "external-crm"},
        requires_human_approval=False,
    )
    case = _case(client, account["id"], "AUTO-CASE-002")
    event_payload = {
        "corporate_account_id": account["id"],
        "corporate_mobility_case_id": case["id"],
        "event_type": "case.status_changed",
        "idempotency_key": "crm-event-0000001",
        "payload": {"previous_status": "draft", "status": "active"},
    }
    first = client.post("/api/v1/automation/events", json=event_payload)
    second = client.post("/api/v1/automation/events", json=event_payload)
    assert first.status_code == second.status_code == 202
    assert first.json()["id"] == second.json()["id"]
    assert first.json()["delivery_count"] == 1

    event_count = db_session.exec(
        select(func.count())
        .select_from(AutomationEvent)
        .where(AutomationEvent.idempotency_key == "crm-event-0000001")
    ).one()
    assert event_count == 1
    deliveries = db_session.exec(
        select(AutomationDelivery).where(
            AutomationDelivery.automation_event_id == UUID(first.json()["id"])
        )
    ).all()
    assert len(deliveries) == 1
    assert deliveries[0].status == "ready"

    conflict_payload = {
        **event_payload,
        "event_type": "compliance.created",
    }
    conflict = client.post("/api/v1/automation/events", json=conflict_payload)
    assert conflict.status_code == 409


def test_rules_are_account_scoped_and_pause_stops_new_deliveries(
    client,
    db_session: Session,
) -> None:
    account_a = _account(client, "Tenant A")
    account_b = _account(client, "Tenant B")
    rule = _rule(client, account_a["id"])

    _case(client, account_b["id"], "AUTO-TENANT-B")
    delivery_count = db_session.exec(
        select(func.count()).select_from(AutomationDelivery)
    ).one()
    assert delivery_count == 0

    paused = client.post(
        f"/api/v1/automation/rules/{rule['id']}/status",
        json={"status": "paused", "reason": "Pause during connector maintenance."},
    )
    assert paused.status_code == 200
    assert paused.json()["status"] == "paused"
    _case(client, account_a["id"], "AUTO-TENANT-A")
    delivery_count = db_session.exec(
        select(func.count()).select_from(AutomationDelivery)
    ).one()
    assert delivery_count == 0


def test_external_channels_cannot_bypass_review_and_require_destinations(client) -> None:
    account = _account(client, "Safety Employer")
    bypass = client.post(
        "/api/v1/automation/rules",
        json={
            "corporate_account_id": account["id"],
            "name": "Unsafe automatic email",
            "event_type": "case.created",
            "channels": ["email"],
            "destinations": {"email": "client-email"},
            "requires_human_approval": False,
        },
    )
    assert bypass.status_code == 400
    assert "requires human approval" in bypass.json()["detail"]

    missing = client.post(
        "/api/v1/automation/rules",
        json={
            "corporate_account_id": account["id"],
            "name": "Missing destination",
            "event_type": "case.created",
            "channels": ["messaging"],
            "destinations": {},
        },
    )
    assert missing.status_code == 400
    assert "named destination" in missing.json()["detail"]


def test_case_compliance_and_task_transitions_write_domain_events(
    client,
    db_session: Session,
) -> None:
    account = _account(client, "Domain Event Employer")
    case = _case(client, account["id"], "AUTO-DOMAIN-EVENTS")
    activated = client.patch(
        f"/api/v1/corporate-mobility/cases/{case['id']}",
        json={"status": "active"},
    )
    assert activated.status_code == 200, activated.text

    compliance = client.post(
        f"/api/v1/corporate-mobility/cases/{case['id']}/compliance-events",
        json={
            "event_type": "registration",
            "title": "Complete destination registration",
            "due_at": "2026-09-01T09:00:00Z",
        },
    )
    assert compliance.status_code == 201, compliance.text
    completed = client.patch(
        f"/api/v1/corporate-mobility/compliance-events/{compliance.json()['id']}",
        json={"status": "completed", "completion_notes": "Registration receipt checked."},
    )
    assert completed.status_code == 200, completed.text

    task = client.post(
        f"/api/v1/corporate-mobility/cases/{case['id']}/relocation-tasks",
        json={
            "title": "Prepare arrival briefing",
            "category": "onboarding",
            "owner_role": "mobility_operator",
        },
    )
    assert task.status_code == 201, task.text
    transitioned = client.patch(
        f"/api/v1/corporate-mobility/relocation-tasks/{task.json()['id']}",
        json={"status": "ready"},
    )
    assert transitioned.status_code == 200, transitioned.text

    event_types = db_session.exec(
        select(AutomationEvent.event_type).where(
            AutomationEvent.corporate_account_id == UUID(account["id"])
        )
    ).all()
    assert {
        "case.created",
        "case.status_changed",
        "compliance.created",
        "compliance.status_changed",
        "task.status_changed",
    }.issubset(set(event_types))

    status_event = next(
        item for item in client.get(
            f"/api/v1/automation/events?corporate_account_id={account['id']}&event_type=case.status_changed"
        ).json()
    )
    assert status_event["payload"]["previous_status"] == "draft"
    assert status_event["payload"]["status"] == "active"

    compliance_event = next(
        item for item in client.get(
            f"/api/v1/automation/events?corporate_account_id={account['id']}&event_type=compliance.created"
        ).json()
    )
    assert compliance_event["payload"]["title"] == "Complete destination registration"

    task_event = next(
        item for item in client.get(
            f"/api/v1/automation/events?corporate_account_id={account['id']}&event_type=task.status_changed"
        ).json()
    )
    assert task_event["payload"]["previous_status"] == "planned"
    assert task_event["payload"]["status"] == "ready"


def test_reject_delivery_prevents_dispatch(
    client,
    db_session: Session,
) -> None:
    account = _account(client, "Reject Delivery Employer")
    _rule(
        client,
        account["id"],
        channels=["email"],
        destinations={"email": "ops@example.com"},
        subject_template="Case {case_reference}",
        body_template="Status: {case_status}",
    )
    case = _case(client, account["id"], "AUTO-REJECT-001")

    pending = client.get(
        f"/api/v1/automation/deliveries?corporate_account_id={account['id']}&status=pending_review"
    )
    assert pending.status_code == 200, pending.text
    delivery_id = pending.json()[0]["id"]

    client.headers.update(_headers("admin", "reviewer-2"))
    rejection = client.post(
        f"/api/v1/automation/deliveries/{delivery_id}/decision",
        json={"decision": "rejected", "reason": "Wrong recipient and channel."},
    )
    assert rejection.status_code == 200, rejection.text
    rejected = rejection.json()
    assert rejected["status"] == "rejected"
    assert rejected["review_reason"] == "Wrong recipient and channel."

    dispatch_blocked = client.post(
        f"/api/v1/automation/deliveries/{delivery_id}/dispatch-record",
        json={"provider_message_id": "should-fail"},
    )
    assert dispatch_blocked.status_code == 400


def test_connector_config_crud_and_status_lifecycle(client) -> None:
    account = _account(client, "Connector Employer")
    created = _connector(client, account["id"], "email", provider_type="smtp", credentials={"host": "smtp.example.com", "port": 587, "username": "user", "password": "pass"})
    assert created["channel"] == "email"
    assert created["provider_type"] == "smtp"
    assert created["from_address"] == "automation@example.com"
    assert created["status"] == "active"
    assert created["credentials"] == {"host": "smtp.example.com", "port": 587, "username": "user", "password": "pass"}

    listed = client.get(f"/api/v1/automation/connectors?corporate_account_id={account['id']}")
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    duplicate = client.post(
        "/api/v1/automation/connectors",
        json={
            "corporate_account_id": account["id"],
            "channel": "email",
            "provider_type": "console",
            "credentials": {},
        },
    )
    assert duplicate.status_code == 400
    assert "active connector config already exists" in duplicate.json()["detail"]

    paused = client.post(
        f"/api/v1/automation/connectors/{created['id']}/status",
        json={"status": "paused", "reason": "SMTP maintenance window."},
    )
    assert paused.status_code == 200
    assert paused.json()["status"] == "paused"

    replacement = _connector(client, account["id"], "email", provider_type="console")
    assert replacement["provider_type"] == "console"
    assert replacement["status"] == "active"


def test_console_adapter_dispatch_via_api(
    client,
    db_session: Session,
) -> None:
    account = _account(client, "Console Dispatch Employer")
    connector = _connector(client, account["id"], "crm")
    _rule(
        client,
        account["id"],
        channels=["crm"],
        destinations={"crm": "external-crm"},
        requires_human_approval=False,
    )
    case = _case(client, account["id"], "AUTO-DISPATCH-001")

    deliveries = db_session.exec(
        select(AutomationDelivery).where(
            AutomationDelivery.automation_event_id.in_(
                select(AutomationEvent.id).where(
                    AutomationEvent.corporate_account_id == UUID(account["id"])
                )
            )
        )
    ).all()
    assert len(deliveries) == 1
    delivery = deliveries[0]
    assert delivery.status == "ready"
    assert delivery.connector_config_id == UUID(connector["id"])

    raw_client = client
    raw_client.headers.update(_headers("operator", "connector-dispatcher"))
    response = raw_client.post(f"/api/v1/automation/deliveries/{delivery.id}/dispatch")
    assert response.status_code == 200, response.text
    dispatched = response.json()
    assert dispatched["status"] == "dispatched"
    assert dispatched["attempt_count"] == 1
    assert dispatched["provider_message_id"].startswith("console-")
    assert dispatched["dispatched_by"] == "connector-dispatcher"
    assert dispatched["last_error"] is None
    assert dispatched["next_attempt_at"] is None

    actions = set(
        db_session.exec(
            select(AuditLog.action).where(AuditLog.source == "automation_v12_4")
        ).all()
    )
    assert {
        "automation_connector_config_created",
        "automation_delivery_dispatched",
    }.issubset(actions)


def test_delivery_retries_when_connector_missing(
    client,
    db_session: Session,
) -> None:
    account = _account(client, "Retry Employer")
    _rule(
        client,
        account["id"],
        channels=["crm"],
        destinations={"crm": "external-crm"},
        requires_human_approval=False,
    )
    case = _case(client, account["id"], "AUTO-RETRY-001")

    delivery = db_session.exec(
        select(AutomationDelivery)
        .join(AutomationEvent)
        .where(AutomationEvent.corporate_account_id == UUID(account["id"]))
    ).one()
    assert delivery.status == "ready"
    assert delivery.connector_config_id is None

    raw_client = client
    raw_client.headers.update(_headers("operator", "connector-dispatcher"))

    for _ in range(2):
        response = raw_client.post(f"/api/v1/automation/deliveries/{delivery.id}/dispatch")
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["status"] == "retry"
        assert "No active connector config for channel" in data["last_error"]
        assert data["next_attempt_at"] is not None

    db_session.refresh(delivery)
    final = raw_client.post(f"/api/v1/automation/deliveries/{delivery.id}/dispatch")
    assert final.status_code == 200, final.text
    final_data = final.json()
    assert final_data["status"] == "failed"
    assert final_data["attempt_count"] == 3
    assert final_data["next_attempt_at"] is None


def test_celery_task_processes_ready_deliveries(
    client,
    db_session: Session,
) -> None:
    account = _account(client, "Celery Task Employer")
    _connector(client, account["id"], "crm")
    _rule(
        client,
        account["id"],
        channels=["crm"],
        destinations={"crm": "external-crm"},
        requires_human_approval=False,
    )
    _case(client, account["id"], "AUTO-TASK-001")

    result = dispatch_automation_deliveries_task.run(batch_size=100)
    assert result["processed"] == 1
    assert result["dispatched"] == 1
    assert result["failed"] == 0

    delivery = db_session.exec(
        select(AutomationDelivery)
        .join(AutomationEvent)
        .where(AutomationEvent.corporate_account_id == UUID(account["id"]))
    ).one()
    assert delivery.status == "dispatched"
    assert delivery.dispatched_by == "automation-worker"
    assert delivery.provider_message_id.startswith("console-")
