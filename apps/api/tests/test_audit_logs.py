from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.domain import AuditLog
from app.services.audit_log import record_audit


def test_audit_log_api_filters_by_action(client: TestClient, db_session: Session) -> None:
    record_audit(
        db_session,
        action="pytest_event",
        entity_type="lead",
        entity_id="lead-1",
        before_state={"status": "before"},
        after_state={"status": "after"},
        reason="Testing audit API.",
        source="pytest",
        commit=True,
    )

    response = client.get("/api/v1/audit-logs", params={"action": "pytest_event", "include_states": True})

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_returned"] == 1
    assert payload["logs"][0]["action"] == "pytest_event"
    assert payload["logs"][0]["after_state"]["status"] == "after"

    audit = db_session.exec(select(AuditLog).where(AuditLog.action == "pytest_event")).first()
    assert audit is not None
