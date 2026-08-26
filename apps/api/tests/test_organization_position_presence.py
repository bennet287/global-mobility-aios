from __future__ import annotations

from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.domain import OrganizationExecutionAttempt, OrganizationalWorkItem, now_utc
from app.services.organization_command import DependencyConflict, InvalidTransition
from app.services.organization_execution_heartbeat import (
    HEARTBEAT_FRESH,
    HEARTBEAT_INACTIVE,
    HEARTBEAT_NOT_ESTABLISHED,
    HEARTBEAT_STALE,
    record_execution_heartbeat,
)
from app.services.organization_position_presence import (
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


def _running_attempt(
    db_session: Session,
    work_item: OrganizationalWorkItem,
) -> OrganizationExecutionAttempt:
    work_item.status = "running"
    work_item.execution_attempts = 1
    work_item.execution_token = "presence-test-token"
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
    db_session.refresh(work_item)
    db_session.refresh(attempt)
    return attempt


def _presence(
    db_session: Session,
    work_item: OrganizationalWorkItem,
    *,
    as_of=None,
):
    return organization_position_presence_snapshot(
        db_session,
        tenant_key="default",
        work_item_id=work_item.id,
        as_of=as_of,
    )


def test_presence_progresses_without_inventing_continuous_liveness(db_session: Session) -> None:
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

    attempt = _running_attempt(db_session, work_item)
    executing_without_checkpoint = _presence(db_session, work_item)
    assert executing_without_checkpoint.presence_state == "executing"
    assert executing_without_checkpoint.presence_basis == "durable_execution_attempt"
    assert executing_without_checkpoint.execution_attempt_id == attempt.id
    assert executing_without_checkpoint.execution_attempt_status == "running"
    assert executing_without_checkpoint.observed_at == attempt.started_at
    assert executing_without_checkpoint.heartbeat_state == HEARTBEAT_NOT_ESTABLISHED
    assert executing_without_checkpoint.authority_effect is False

    observed_at = now_utc()
    heartbeat = record_execution_heartbeat(
        db_session,
        tenant_key="default",
        work_item_id=work_item.id,
        execution_attempt_id=attempt.id,
        position_key=work_item.assigned_position_key,
        checkpoint="attempt_started",
        writer="pytest",
        observed_at=observed_at,
        lease_seconds=30,
    )

    fresh = _presence(db_session, work_item, as_of=observed_at + timedelta(seconds=5))
    assert fresh.presence_state == "executing"
    assert fresh.heartbeat_state == HEARTBEAT_FRESH
    assert fresh.heartbeat_observed_at == heartbeat.observed_at
    assert fresh.heartbeat_fresh_until == heartbeat.fresh_until
    assert fresh.authority_effect is False

    stale = _presence(db_session, work_item, as_of=observed_at + timedelta(seconds=31))
    assert stale.presence_state == "executing"
    assert stale.heartbeat_state == HEARTBEAT_STALE
    assert stale.heartbeat_observed_at == heartbeat.observed_at
    assert stale.authority_effect is False

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
    assert inactive.heartbeat_state == HEARTBEAT_INACTIVE
    assert inactive.heartbeat_observed_at is None
    assert inactive.heartbeat_fresh_until is None
    assert inactive.authority_effect is False


def test_heartbeat_writer_is_tenant_position_and_execution_scoped(db_session: Session) -> None:
    work_item = _work_item(db_session, key="heartbeat-scope")
    attempt = _running_attempt(db_session, work_item)

    with pytest.raises(DependencyConflict, match="not found for the tenant"):
        record_execution_heartbeat(
            db_session,
            tenant_key="different-tenant",
            work_item_id=work_item.id,
            execution_attempt_id=attempt.id,
            position_key=work_item.assigned_position_key,
            checkpoint="attempt_started",
        )

    with pytest.raises(DependencyConflict, match="position does not match"):
        record_execution_heartbeat(
            db_session,
            tenant_key="default",
            work_item_id=work_item.id,
            execution_attempt_id=attempt.id,
            position_key="different_position",
            checkpoint="attempt_started",
        )

    with pytest.raises(ValueError, match="between 15 and 300 seconds"):
        record_execution_heartbeat(
            db_session,
            tenant_key="default",
            work_item_id=work_item.id,
            execution_attempt_id=attempt.id,
            position_key=work_item.assigned_position_key,
            checkpoint="attempt_started",
            lease_seconds=1,
        )

    attempt.status = "completed"
    attempt.completed_at = now_utc()
    db_session.add(attempt)
    db_session.commit()
    with pytest.raises(InvalidTransition, match="require running WorkItem and execution attempt"):
        record_execution_heartbeat(
            db_session,
            tenant_key="default",
            work_item_id=work_item.id,
            execution_attempt_id=attempt.id,
            position_key=work_item.assigned_position_key,
            checkpoint="agent_completed",
        )


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
