from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.domain import OrganizationExecutionAttempt, OrganizationalWorkItem, now_utc
from app.services.organization_command import DependencyConflict
from app.services.organization_position_presence import (
    HEARTBEAT_NOT_ESTABLISHED,
    ORGANIZATION_POSITION_PRESENCE_CONTRACT_VERSION,
    organization_position_presence_snapshot,
)


def _work_item(db_session: Session, *, key: str, status: str = "queued") -> OrganizationalWorkItem:
    work_item = OrganizationalWorkItem(
        idempotency_key=f"presence:{key}",
        work_type="presence-test",
        title="Presence projection test",
        objective="Exercise bounded durable execution presence.",
        department="Global Mobility Operations",
        authority_level="L1",
        assigned_position_key="mobility_pathway_specialist",
        status=status,
        created_by="pytest",
    )
    db_session.add(work_item)
    db_session.commit()
    db_session.refresh(work_item)
    return work_item


def _presence(db_session: Session, work_item: OrganizationalWorkItem):
    return organization_position_presence_snapshot(
        db_session,
        tenant_key="default",
        work_item_id=work_item.id,
    )


def test_presence_progresses_without_inventing_heartbeat(db_session: Session) -> None:
    work_item = _work_item(db_session, key="progression")

    missing = _presence(db_session, work_item)
    assert missing.contract_version == ORGANIZATION_POSITION_PRESENCE_CONTRACT_VERSION
    assert missing.presence_state == "not_established"
    assert missing.presence_basis == "none"
    assert missing.observed_at is None
    assert missing.execution_attempt_id is None
    assert missing.heartbeat_state == HEARTBEAT_NOT_ESTABLISHED
    assert missing.heartbeat_observed_at is None
    assert missing.heartbeat_fresh_until is None
    assert missing.authority_effect is False

    work_item.status = "running"
    work_item.execution_attempts = 1
    attempt = OrganizationExecutionAttempt(
        attempt_key=f"presence-test:{work_item.id}:1",
        work_item_id=work_item.id,
        attempt_number=1,
        execution_token="presence-test-token",
        actor="pytest",
    )
    db_session.add(work_item)
    db_session.add(attempt)
    db_session.commit()
    db_session.refresh(attempt)

    executing = _presence(db_session, work_item)
    assert executing.presence_state == "executing"
    assert executing.presence_basis == "durable_execution_attempt"
    assert executing.execution_attempt_id == attempt.id
    assert executing.execution_attempt_status == "running"
    assert executing.observed_at == attempt.started_at
    assert executing.heartbeat_state == HEARTBEAT_NOT_ESTABLISHED
    assert executing.authority_effect is False

    completed_at = now_utc()
    attempt.status = "completed"
    attempt.completed_at = completed_at
    work_item.status = "completed"
    work_item.completed_at = completed_at
    db_session.add(attempt)
    db_session.add(work_item)
    db_session.commit()
    db_session.refresh(attempt)

    inactive = _presence(db_session, work_item)
    assert inactive.presence_state == "not_executing"
    assert inactive.execution_attempt_id == attempt.id
    assert inactive.execution_attempt_status == "completed"
    assert inactive.observed_at == attempt.completed_at
    assert inactive.heartbeat_state == HEARTBEAT_NOT_ESTABLISHED
    assert inactive.authority_effect is False


def test_presence_fails_closed_for_running_work_without_attempt(db_session: Session) -> None:
    work_item = _work_item(db_session, key="missing-attempt", status="running")

    with pytest.raises(DependencyConflict, match="without a running execution attempt"):
        _presence(db_session, work_item)


def test_presence_fails_closed_for_multiple_running_attempts(db_session: Session) -> None:
    work_item = _work_item(db_session, key="multiple-running", status="running")
    for attempt_number in (1, 2):
        db_session.add(
            OrganizationExecutionAttempt(
                attempt_key=f"presence-test:{work_item.id}:{attempt_number}",
                work_item_id=work_item.id,
                attempt_number=attempt_number,
                execution_token=f"presence-test-token-{attempt_number}",
                actor="pytest",
            )
        )
    db_session.commit()

    with pytest.raises(DependencyConflict, match="multiple running execution attempts"):
        _presence(db_session, work_item)


def test_presence_is_tenant_scoped(db_session: Session) -> None:
    work_item = _work_item(db_session, key="tenant-scope")

    with pytest.raises(DependencyConflict, match="not found for the tenant"):
        organization_position_presence_snapshot(
            db_session,
            tenant_key="different-tenant",
            work_item_id=work_item.id,
        )


def test_presence_latest_endpoint_is_registered_and_truthfully_empty(client: TestClient) -> None:
    response = client.get("/api/v1/organization/transparency/presence/austria/latest")

    assert response.status_code == 200
    assert response.json() == {"established": False, "snapshot": None}
