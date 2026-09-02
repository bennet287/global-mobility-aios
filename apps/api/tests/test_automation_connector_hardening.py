from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import AuditLog, AutomationConnectorConfig, AutomationDelivery, AutomationEvent
from app.services.automation_connector import (
    AdapterSendError,
    check_connector_health,
    reconcile_automation_deliveries,
)
from app.services.automation_connector_encryption import (
    decrypt_credentials,
    encrypt_credentials,
)
from app.tasks.automation_tasks import reconcile_automation_deliveries_task


def _headers(role: str, user: str) -> dict[str, str]:
    return {"X-GMAI-Role": role, "X-GMAI-User": user}


def _account(client, name: str = "Hardening Employer") -> dict:
    response = client.post(
        "/api/v1/corporate-mobility/accounts",
        json={"legal_name": name, "primary_country": "Austria"},
    )
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


def _case(client, account_id: str, reference: str) -> dict:
    response = client.post(
        f"/api/v1/corporate-mobility/accounts/{account_id}/cases",
        json={
            "case_reference": reference,
            "destination_country": "Germany",
            "notes": "Note.",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _rule(client, account_id: str, **overrides) -> dict:
    payload = {
        "corporate_account_id": account_id,
        "name": "Case creation notifications",
        "event_type": "case.created",
        "channels": ["crm"],
        "destinations": {"crm": "mobility-team"},
        "subject_template": "{case_reference}: new mobility case",
        "body_template": "{case_reference} is {case_status}.",
        "requires_human_approval": False,
    }
    payload.update(overrides)
    response = client.post("/api/v1/automation/rules", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_connector_credentials_encrypted_at_rest_and_masked_in_api(client, db_session: Session) -> None:
    client.headers.update(_headers("admin", "security-auditor"))
    account = _account(client)
    credentials = {"host": "smtp.example.com", "port": 587, "username": "user", "password": "secret"}
    created = _connector(client, account["id"], "email", provider_type="smtp", credentials=credentials)

    # API never returns plaintext secrets.
    assert created["credentials"] == {"host": "***", "port": "***", "username": "***", "password": "***"}

    config_id = UUID(created["id"])
    config = db_session.get(AutomationConnectorConfig, config_id)
    assert config is not None
    # Storage is encrypted, not plaintext JSON.
    assert config.credentials_json != '{"host":"smtp.example.com","password":"secret","port":587,"username":"user"}'
    decrypted = decrypt_credentials(config.credentials_json)
    assert decrypted == credentials


def test_connector_health_check_console_succeeds(client, db_session: Session) -> None:
    client.headers.update(_headers("admin", "health-checker"))
    account = _account(client)
    connector = _connector(client, account["id"], "email", provider_type="console")

    response = client.post(f"/api/v1/automation/connectors/{connector['id']}/health-check")
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "healthy"
    assert response.json()["provider_type"] == "console"

    audit = db_session.exec(
        select(AuditLog)
        .where(AuditLog.action == "automation_connector_health_check_succeeded")
        .where(AuditLog.entity_id == connector["id"])
    ).first()
    assert audit is not None


def test_connector_health_check_smtp_missing_credentials_fails(client) -> None:
    client.headers.update(_headers("admin", "health-checker"))
    account = _account(client)
    connector = _connector(client, account["id"], "email", provider_type="smtp", credentials={})

    response = client.post(f"/api/v1/automation/connectors/{connector['id']}/health-check")
    assert response.status_code == 503
    assert "SMTP credentials" in response.json()["detail"]


def test_check_connector_health_raises_adapter_error_for_invalid_smtp(client, db_session: Session) -> None:
    client.headers.update(_headers("admin", "health-checker"))
    account = _account(client, "Direct Health Employer")
    connector = _connector(client, account["id"], "email", provider_type="smtp", credentials={})
    config = db_session.get(AutomationConnectorConfig, UUID(connector["id"]))
    assert config is not None

    try:
        check_connector_health(db_session, config, actor="test")
    except AdapterSendError as exc:
        assert "SMTP credentials" in str(exc)
    else:
        raise AssertionError("Expected AdapterSendError")

    audit = db_session.exec(
        select(AuditLog)
        .where(AuditLog.action == "automation_connector_health_check_failed")
        .where(AuditLog.entity_id == connector["id"])
    ).first()
    assert audit is not None


def test_reconcile_automation_deliveries_marks_old_console_dispatches(client, db_session: Session) -> None:
    client.headers.update(_headers("admin", "reconciliation-auditor"))
    account = _account(client)
    _connector(client, account["id"], "crm", provider_type="console")
    _rule(client, account["id"], channels=["crm"], destinations={"crm": "ops@example.com"})
    case = _case(client, account["id"], "RECON-001")

    delivery = db_session.exec(
        select(AutomationDelivery)
        .join(AutomationEvent)
        .where(AutomationEvent.corporate_account_id == UUID(account["id"]))
    ).first()
    assert delivery is not None

    # Simulate an old dispatched console delivery.
    delivery.status = "dispatched"
    delivery.dispatched_at = datetime.now(timezone.utc) - timedelta(hours=48)
    delivery.dispatched_by = "console-worker"
    delivery.provider_message_id = "console-old-123"
    db_session.add(delivery)
    db_session.commit()

    result = reconcile_automation_deliveries(db_session, max_age_hours=24, actor="reconciliation-test")
    assert result["reconciled"] == 1

    db_session.refresh(delivery)
    assert delivery.reconciled is True
    assert delivery.reconciled_at is not None

    audit = db_session.exec(
        select(AuditLog)
        .where(AuditLog.action == "automation_delivery_reconciled")
        .where(AuditLog.entity_id == str(delivery.id))
    ).first()
    assert audit is not None


def test_reconcile_automation_deliveries_task_runs(client, db_session: Session) -> None:
    client.headers.update(_headers("admin", "reconciliation-auditor"))
    account = _account(client)
    _connector(client, account["id"], "crm", provider_type="console")
    _rule(client, account["id"], channels=["crm"], destinations={"crm": "ops@example.com"})
    _case(client, account["id"], "RECON-TASK-001")

    delivery = db_session.exec(
        select(AutomationDelivery)
        .join(AutomationEvent)
        .where(AutomationEvent.corporate_account_id == UUID(account["id"]))
    ).first()
    assert delivery is not None
    delivery.status = "dispatched"
    delivery.dispatched_at = datetime.now(timezone.utc) - timedelta(hours=48)
    delivery.provider_message_id = "console-task-123"
    db_session.add(delivery)
    db_session.commit()

    result = reconcile_automation_deliveries_task.run(max_age_hours=24)
    assert result == {"reconciled": 1}
