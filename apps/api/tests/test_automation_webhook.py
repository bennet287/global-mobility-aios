from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from sqlmodel import Session

from app.models.domain import AutomationDelivery, AutomationConnectorConfig, CorporateAccount
from app.services.automation import record_delivery_receipt
from app.services.automation_connector import (
    AdapterSendError,
    WebhookAdapter,
    reset_stale_dispatching_deliveries,
)
from app.tasks.automation_tasks import dispatch_automation_deliveries_task


def _delivery(payload: dict[str, Any] | None = None) -> AutomationDelivery:
    return AutomationDelivery(
        id=uuid4(),
        automation_event_id=uuid4(),
        automation_rule_id=uuid4(),
        channel="webhook",
        destination="ops-webhook",
        subject="case update",
        payload_json=json.dumps(payload or {"body": "test"}),
        status="ready",
        requires_human_approval=True,
    )


def _config(credentials: dict[str, Any]) -> AutomationConnectorConfig:
    return AutomationConnectorConfig(
        id=uuid4(),
        corporate_account_id=uuid4(),
        channel="webhook",
        provider_type="webhook",
        credentials_json=json.dumps(credentials),
        from_address="automation@example.com",
        sender_label="GMAI",
        status="active",
        created_by="pytest",
        updated_by="pytest",
    )


def test_webhook_adapter_sends_post_with_signature(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_post(url: str, *, content: bytes, headers: dict[str, str], timeout: int, follow_redirects: bool):
        captured["url"] = url
        captured["content"] = content
        captured["headers"] = headers
        response = MagicMock()
        response.raise_for_status.return_value = None
        return response

    monkeypatch.setattr("httpx.post", fake_post)

    adapter = WebhookAdapter()
    delivery = _delivery({"event_type": "case.created"})
    config = _config({"url": "https://hooks.example.com/gmai", "secret": "shhh"})
    message_id = adapter.send(delivery, config)

    assert message_id.startswith("webhook-")
    assert captured["url"] == "https://hooks.example.com/gmai"
    assert captured["content"] == delivery.payload_json.encode("utf-8")
    assert captured["headers"]["Content-Type"] == "application/json"
    assert "X-GMAI-Signature" in captured["headers"]
    assert captured["headers"]["User-Agent"] == "gmai-automation/1.0"


def test_webhook_adapter_send_without_signature(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_post(url: str, *, content: bytes, headers: dict[str, str], timeout: int, follow_redirects: bool):
        captured["headers"] = headers
        response = MagicMock()
        response.raise_for_status.return_value = None
        return response

    monkeypatch.setattr("httpx.post", fake_post)

    adapter = WebhookAdapter()
    delivery = _delivery({"event_type": "case.created"})
    config = _config({"url": "https://hooks.example.com/gmai"})
    adapter.send(delivery, config)

    assert "X-GMAI-Signature" not in captured["headers"]


def test_webhook_adapter_send_raises_on_missing_url() -> None:
    adapter = WebhookAdapter()
    delivery = _delivery()
    config = _config({})
    with pytest.raises(AdapterSendError, match="url"):
        adapter.send(delivery, config)


def test_webhook_adapter_health_check(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, *, timeout: int, follow_redirects: bool):
        response = MagicMock()
        response.raise_for_status.return_value = None
        return response

    monkeypatch.setattr("httpx.get", fake_get)

    adapter = WebhookAdapter()
    config = _config({"url": "https://hooks.example.com/gmai"})
    assert adapter.health_check(config) == "healthy"


def test_webhook_adapter_health_check_raises_on_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, *, timeout: int, follow_redirects: bool):
        raise RuntimeError("connection refused")

    monkeypatch.setattr("httpx.get", fake_get)

    adapter = WebhookAdapter()
    config = _config({"url": "https://hooks.example.com/gmai"})
    with pytest.raises(AdapterSendError, match="health check failed"):
        adapter.health_check(config)


def _headers(role: str, user: str) -> dict[str, str]:
    return {"X-GMAI-Role": role, "X-GMAI-User": user}


def _account(client, name: str = "Webhook Employer") -> dict:
    response = client.post(
        "/api/v1/corporate-mobility/accounts",
        json={"legal_name": name, "primary_country": "Austria"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _rule(client, account_id: str) -> dict:
    response = client.post(
        "/api/v1/automation/rules",
        json={
            "corporate_account_id": account_id,
            "name": "Webhook case notifications",
            "event_type": "case.created",
            "channels": ["webhook"],
            "destinations": {"webhook": "https://hooks.example.com/gmai"},
            "subject_template": "{case_reference}: new case",
            "body_template": "{case_reference} created.",
            "requires_human_approval": True,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _connector(client, account_id: str) -> dict:
    response = client.post(
        "/api/v1/automation/connectors",
        json={
            "corporate_account_id": account_id,
            "channel": "webhook",
            "provider_type": "webhook",
            "credentials": {"url": "https://hooks.example.com/gmai", "secret": "shhh"},
            "from_address": "automation@example.com",
            "sender_label": "GMAI",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _case(client, account_id: str) -> dict:
    response = client.post(
        f"/api/v1/corporate-mobility/accounts/{account_id}/cases",
        json={"case_reference": "WEB-CASE-001", "destination_country": "Germany"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_inbound_webhook_requires_secret(client) -> None:
    account = _account(client)
    case = _case(client, account["id"])
    response = client.post(
        "/api/v1/automation/webhooks/ingest",
        json={
            "corporate_account_id": str(account["id"]),
            "corporate_mobility_case_id": str(case["id"]),
            "event_type": "case.created",
            "idempotency_key": "webhook-test-1",
            "payload": {"source": "n8n"},
        },
    )
    assert response.status_code == 401


def test_inbound_webhook_creates_event_and_deliveries(client, db_session: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core.config import settings

    monkeypatch.setattr(settings, "automation_webhook_secret", "webhook-secret")
    account = _account(client)
    _rule(client, account["id"])
    _connector(client, account["id"])
    case = _case(client, account["id"])

    response = client.post(
        "/api/v1/automation/webhooks/ingest",
        headers={"X-GMAI-Webhook-Secret": "webhook-secret"},
        json={
            "corporate_account_id": str(account["id"]),
            "corporate_mobility_case_id": str(case["id"]),
            "event_type": "case.created",
            "idempotency_key": "webhook-test-2",
            "payload": {"source": "n8n"},
        },
    )
    assert response.status_code == 202, response.text
    event = response.json()
    assert event["source"] == "webhook"
    assert event["delivery_count"] == 1

    # Idempotent replay returns the same event.
    response2 = client.post(
        "/api/v1/automation/webhooks/ingest",
        headers={"X-GMAI-Webhook-Secret": "webhook-secret"},
        json={
            "corporate_account_id": str(account["id"]),
            "corporate_mobility_case_id": str(case["id"]),
            "event_type": "case.created",
            "idempotency_key": "webhook-test-2",
            "payload": {"source": "n8n"},
        },
    )
    assert response2.status_code == 202
    assert response2.json()["id"] == event["id"]


def test_delivery_receipt_idempotent(client, db_session: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core.config import settings

    monkeypatch.setattr(settings, "automation_webhook_secret", "webhook-secret")
    account = _account(client)
    _rule(client, account["id"])
    _connector(client, account["id"])
    case = _case(client, account["id"])

    deliveries = client.get(
        f"/api/v1/automation/deliveries?corporate_account_id={account['id']}"
    ).json()
    delivery_id = deliveries[0]["id"]

    client.headers.update(_headers("reviewer", "automation-reviewer"))
    approved = client.post(
        f"/api/v1/automation/deliveries/{delivery_id}/decision",
        json={"decision": "approved", "reason": "Looks good"},
    )
    assert approved.status_code == 200
    client.headers.update(_headers("admin", "pytest-admin"))

    receipt = client.post(
        f"/api/v1/automation/deliveries/{delivery_id}/receipt",
        json={
            "provider_message_id": "webhook-abc123",
            "status": "delivered",
            "reason": "200 OK from provider",
        },
    )
    assert receipt.status_code == 200
    assert receipt.json()["status"] == "delivered"
    assert receipt.json()["provider_message_id"] == "webhook-abc123"
    assert receipt.json()["reconciled"] is True

    # Replay is idempotent.
    receipt2 = client.post(
        f"/api/v1/automation/deliveries/{delivery_id}/receipt",
        json={
            "provider_message_id": "webhook-abc123",
            "status": "delivered",
            "reason": "200 OK from provider",
        },
    )
    assert receipt2.status_code == 200
    assert receipt2.json()["status"] == "delivered"


def test_worker_does_not_double_dispatch_dispatching_rows(
    client, db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.core.config import settings

    monkeypatch.setattr(settings, "automation_webhook_secret", "webhook-secret")
    account = _account(client)
    _rule(client, account["id"])
    _connector(client, account["id"])
    _case(client, account["id"])

    deliveries = client.get(
        f"/api/v1/automation/deliveries?corporate_account_id={account['id']}"
    ).json()
    delivery_id = deliveries[0]["id"]

    # Approve the delivery.
    client.headers.update(_headers("reviewer", "automation-reviewer"))
    decision = client.post(
        f"/api/v1/automation/deliveries/{delivery_id}/decision",
        json={"decision": "approved", "reason": "Approved"},
    )
    assert decision.status_code == 200
    client.headers.update(_headers("admin", "pytest-admin"))

    # Manually mark it as dispatching with a future lock timeout.
    delivery = db_session.get(AutomationDelivery, UUID(delivery_id))
    assert delivery is not None
    delivery.status = "dispatching"
    delivery.next_attempt_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    db_session.add(delivery)
    db_session.commit()

    # Worker should skip it because it is dispatching.
    result = dispatch_automation_deliveries_task(batch_size=10)
    assert result["processed"] == 0


def test_worker_resets_stale_dispatching_rows(client, db_session: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core.config import settings

    monkeypatch.setattr(settings, "automation_webhook_secret", "webhook-secret")
    account = _account(client)
    _rule(client, account["id"])
    _connector(client, account["id"])
    _case(client, account["id"])

    deliveries = client.get(
        f"/api/v1/automation/deliveries?corporate_account_id={account['id']}"
    ).json()
    delivery_id = deliveries[0]["id"]

    client.headers.update(_headers("reviewer", "automation-reviewer"))
    decision = client.post(
        f"/api/v1/automation/deliveries/{delivery_id}/decision",
        json={"decision": "approved", "reason": "Approved"},
    )
    assert decision.status_code == 200
    client.headers.update(_headers("admin", "pytest-admin"))

    delivery = db_session.get(AutomationDelivery, UUID(delivery_id))
    assert delivery is not None
    delivery.status = "dispatching"
    delivery.updated_at = datetime.now(timezone.utc) - timedelta(minutes=10)
    db_session.add(delivery)
    db_session.commit()

    count = reset_stale_dispatching_deliveries(db_session, actor="pytest")
    assert count == 1
    db_session.refresh(delivery)
    assert delivery.status in {"ready", "retry"}
