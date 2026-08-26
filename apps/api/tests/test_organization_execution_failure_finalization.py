from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select

from app.models.domain import OrganizationExecutionAttempt, OrganizationalWorkItem
from app.models.organization_presence import OrganizationExecutionHeartbeat
from app.services.organization_execution_failure import (
    RUNTIME_SESSION_FAILED,
    finalize_execution_failure_if_fence_owned,
)
from app.services.organization_execution_heartbeat import (
    RUNTIME_SESSION_CLAIMED,
    claim_execution_runtime_session,
    stage_execution_heartbeat,
)


POSITION_KEY = "mobility.pathway_specialist"
EXECUTION_TOKEN = "f" * 64
BASE_TIME = datetime(2026, 8, 26, 12, 0, tzinfo=timezone.utc)


def _running_attempt(
    db_session: Session,
    *,
    suffix: str,
    writer: str = "worker-a",
    observed_at: datetime = BASE_TIME,
    lease_seconds: int = 60,
) -> tuple[OrganizationalWorkItem, OrganizationExecutionAttempt]:
    work = OrganizationalWorkItem(
        idempotency_key=f"failure-finalization-work:{suffix}",
        tenant_key="default",
        work_type="mobility_specialist_work",
        objective_key=f"failure-finalization-objective:{suffix}",
        phase_key="M.6.failure",
        title="Fenced failure finalization test",
        objective="Prove stale workers cannot mutate canonical failure state.",
        department="Global Mobility Operations",
        authority_level="L1",
        status="running",
        assigned_position_key=POSITION_KEY,
        execution_attempts=1,
        max_execution_attempts=3,
        execution_token=EXECUTION_TOKEN,
        execution_started_at=observed_at,
        created_by="pytest",
    )
    db_session.add(work)
    db_session.flush()

    attempt = OrganizationExecutionAttempt(
        attempt_key=f"failure-finalization-attempt:{suffix}",
        work_item_id=work.id,
        attempt_number=1,
        execution_token=EXECUTION_TOKEN,
        actor=writer,
        started_at=observed_at,
    )
    db_session.add(attempt)
    db_session.flush()
    stage_execution_heartbeat(
        db_session,
        tenant_key="default",
        work=work,
        attempt=attempt,
        position_key=POSITION_KEY,
        checkpoint="attempt_started",
        writer=writer,
        observed_at=observed_at,
        lease_seconds=lease_seconds,
    )
    db_session.commit()
    db_session.refresh(work)
    db_session.refresh(attempt)
    return work, attempt


def _events(db_session: Session, attempt_id) -> list[OrganizationExecutionHeartbeat]:
    return list(
        db_session.exec(
            select(OrganizationExecutionHeartbeat)
            .where(OrganizationExecutionHeartbeat.execution_attempt_id == attempt_id)
            .order_by(OrganizationExecutionHeartbeat.sequence)
        ).all()
    )


def test_current_fence_owner_can_finalize_failure(db_session: Session) -> None:
    work, attempt = _running_attempt(db_session, suffix="current")

    result = finalize_execution_failure_if_fence_owned(
        db_session,
        tenant_key="default",
        work_item_id=work.id,
        execution_attempt_id=attempt.id,
        position_key=POSITION_KEY,
        expected_execution_token=EXECUTION_TOKEN,
        expected_fence_token=1,
        writer="worker-a",
        error=RuntimeError("provider failed"),
    )

    assert result.applied is True
    assert result.reason == "failure_finalized"
    assert result.failure_sequence == 2
    db_session.refresh(work)
    db_session.refresh(attempt)
    assert attempt.status == "failed"
    assert attempt.completed_at is not None
    assert attempt.error == "RuntimeError: provider failed"
    assert work.status == "running"
    assert work.execution_started_at is None
    assert work.last_error == "RuntimeError: provider failed"
    events = _events(db_session, attempt.id)
    assert [event.checkpoint for event in events] == ["attempt_started", RUNTIME_SESSION_FAILED]
    assert events[-1].writer == "worker-a"


def test_expired_but_unsuperseded_owner_can_finalize_its_own_failure(db_session: Session) -> None:
    stale_start = BASE_TIME - timedelta(minutes=5)
    work, attempt = _running_attempt(
        db_session,
        suffix="expired-owner",
        observed_at=stale_start,
        lease_seconds=30,
    )

    result = finalize_execution_failure_if_fence_owned(
        db_session,
        tenant_key="default",
        work_item_id=work.id,
        execution_attempt_id=attempt.id,
        position_key=POSITION_KEY,
        expected_execution_token=EXECUTION_TOKEN,
        expected_fence_token=1,
        writer="worker-a",
        error=TimeoutError("runtime timed out"),
    )

    assert result.applied is True
    db_session.refresh(attempt)
    assert attempt.status == "failed"
    assert _events(db_session, attempt.id)[-1].checkpoint == RUNTIME_SESSION_FAILED


def test_superseded_original_worker_cannot_finalize_failure(db_session: Session) -> None:
    stale_start = BASE_TIME - timedelta(minutes=5)
    work, attempt = _running_attempt(
        db_session,
        suffix="superseded",
        observed_at=stale_start,
        lease_seconds=30,
    )
    takeover = claim_execution_runtime_session(
        db_session,
        tenant_key="default",
        work_item_id=work.id,
        execution_attempt_id=attempt.id,
        position_key=POSITION_KEY,
        expected_execution_token=EXECUTION_TOKEN,
        writer="worker-b",
        observed_at=BASE_TIME,
        lease_seconds=60,
    )
    assert takeover.fence_token == 2

    result = finalize_execution_failure_if_fence_owned(
        db_session,
        tenant_key="default",
        work_item_id=work.id,
        execution_attempt_id=attempt.id,
        position_key=POSITION_KEY,
        expected_execution_token=EXECUTION_TOKEN,
        expected_fence_token=1,
        writer="worker-a",
        error=RuntimeError("late stale worker error"),
    )

    assert result.applied is False
    assert result.reason == "runtime_session_ownership_lost"
    db_session.refresh(work)
    db_session.refresh(attempt)
    assert attempt.status == "running"
    assert attempt.error is None
    assert work.execution_started_at is not None
    assert work.last_error is None
    events = _events(db_session, attempt.id)
    assert [event.checkpoint for event in events] == ["attempt_started", RUNTIME_SESSION_CLAIMED]
    assert events[-1].writer == "worker-b"


def test_terminal_attempt_cannot_be_overwritten_by_late_failure(db_session: Session) -> None:
    work, attempt = _running_attempt(db_session, suffix="terminal")
    attempt.status = "completed"
    attempt.completed_at = BASE_TIME + timedelta(seconds=10)
    work.status = "completed"
    work.execution_started_at = None
    db_session.add(attempt)
    db_session.add(work)
    db_session.commit()

    result = finalize_execution_failure_if_fence_owned(
        db_session,
        tenant_key="default",
        work_item_id=work.id,
        execution_attempt_id=attempt.id,
        position_key=POSITION_KEY,
        expected_execution_token=EXECUTION_TOKEN,
        expected_fence_token=1,
        writer="worker-a",
        error=RuntimeError("late terminal error"),
    )

    assert result.applied is False
    assert result.reason == "canonical_execution_not_running"
    db_session.refresh(work)
    db_session.refresh(attempt)
    assert attempt.status == "completed"
    assert attempt.error is None
    assert work.status == "completed"
    assert work.last_error is None
    assert [event.checkpoint for event in _events(db_session, attempt.id)] == ["attempt_started"]
