from __future__ import annotations

from datetime import datetime, timedelta, timezone
from threading import Event
from time import sleep
from uuid import uuid4

import pytest
from sqlmodel import Session, select

from app.models.domain import OrganizationExecutionAttempt, OrganizationalWorkItem
from app.models.organization_presence import OrganizationExecutionHeartbeat
from app.services.organization_command import DependencyConflict, InvalidTransition
from app.services.organization_execution_heartbeat import (
    ExecutionRuntimeSessionLease,
    claim_execution_runtime_session,
    stage_execution_heartbeat,
)
from app.services.organization_runtime_session_supervisor import (
    ExecutionRuntimeSessionSupervisor,
    initial_runtime_session_or_fail,
    stage_fenced_agent_completion,
)


POSITION_KEY = "mobility.pathway_specialist"
EXECUTION_TOKEN = "d" * 64
BASE_TIME = datetime(2026, 8, 26, 10, 0, tzinfo=timezone.utc)


def _running_attempt(
    db_session: Session,
    *,
    suffix: str,
    writer: str = "worker-a",
    lease_seconds: int = 15,
) -> tuple[OrganizationalWorkItem, OrganizationExecutionAttempt]:
    work = OrganizationalWorkItem(
        idempotency_key=f"runtime-supervisor-work:{suffix}",
        tenant_key="default",
        work_type="mobility_specialist_work",
        objective_key=f"runtime-supervisor-objective:{suffix}",
        phase_key="J.1.pathway",
        title="Runtime supervisor test",
        objective="Prove bounded renewal and terminal fencing.",
        department="Global Mobility Operations",
        authority_level="L1",
        status="running",
        assigned_position_key=POSITION_KEY,
        execution_attempts=1,
        max_execution_attempts=3,
        execution_token=EXECUTION_TOKEN,
        execution_started_at=BASE_TIME,
        created_by="pytest",
    )
    db_session.add(work)
    db_session.flush()
    attempt = OrganizationExecutionAttempt(
        attempt_key=f"runtime-supervisor-attempt:{suffix}",
        work_item_id=work.id,
        attempt_number=1,
        execution_token=EXECUTION_TOKEN,
        actor=writer,
        started_at=BASE_TIME,
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
        observed_at=BASE_TIME,
        lease_seconds=lease_seconds,
    )
    db_session.commit()
    db_session.refresh(work)
    db_session.refresh(attempt)
    return work, attempt


def _lease(*, observed_at: datetime, fence_token: int = 1, writer: str = "worker-a") -> ExecutionRuntimeSessionLease:
    return ExecutionRuntimeSessionLease(
        execution_attempt_id=uuid4(),
        work_item_id=uuid4(),
        position_key=POSITION_KEY,
        execution_token=EXECUTION_TOKEN,
        fence_token=fence_token,
        writer=writer,
        observed_at=observed_at,
        fresh_until=observed_at + timedelta(seconds=15),
        last_heartbeat_id=uuid4(),
    )


def test_supervisor_renews_only_while_context_is_active() -> None:
    renewed = Event()
    calls = 0

    def renew_once() -> ExecutionRuntimeSessionLease:
        nonlocal calls
        calls += 1
        renewed.set()
        return _lease(observed_at=BASE_TIME + timedelta(seconds=calls))

    supervisor = ExecutionRuntimeSessionSupervisor(
        tenant_key="default",
        work_item_id=uuid4(),
        execution_attempt_id=uuid4(),
        position_key=POSITION_KEY,
        expected_execution_token=EXECUTION_TOKEN,
        expected_fence_token=1,
        writer="worker-a",
        lease_seconds=15,
        renewal_interval_seconds=0.01,
        renew_once=renew_once,
    )

    with supervisor:
        assert renewed.wait(timeout=1.0)
        snapshot = supervisor.snapshot()
        assert snapshot.healthy is True
        assert snapshot.renewal_count >= 1

    calls_after_exit = calls
    sleep(0.04)
    assert calls == calls_after_exit


def test_supervisor_fails_closed_when_renewal_loses_fence() -> None:
    attempted = Event()

    def renew_once() -> ExecutionRuntimeSessionLease:
        attempted.set()
        raise DependencyConflict("runtime session fence token is stale")

    supervisor = ExecutionRuntimeSessionSupervisor(
        tenant_key="default",
        work_item_id=uuid4(),
        execution_attempt_id=uuid4(),
        position_key=POSITION_KEY,
        expected_execution_token=EXECUTION_TOKEN,
        expected_fence_token=1,
        writer="worker-a",
        lease_seconds=15,
        renewal_interval_seconds=0.01,
        renew_once=renew_once,
    )

    supervisor.start()
    assert attempted.wait(timeout=1.0)
    with pytest.raises(DependencyConflict, match="renewal supervisor lost the current fence"):
        supervisor.stop()


def test_initial_runtime_session_requires_current_writer_and_execution_token(db_session: Session) -> None:
    work, attempt = _running_attempt(db_session, suffix="initial")

    current = initial_runtime_session_or_fail(
        db_session,
        tenant_key="default",
        work_item_id=work.id,
        execution_attempt_id=attempt.id,
        position_key=POSITION_KEY,
        expected_execution_token=EXECUTION_TOKEN,
        writer="worker-a",
    )
    assert current.fence_token == 1

    with pytest.raises(DependencyConflict, match="execution token is stale"):
        initial_runtime_session_or_fail(
            db_session,
            tenant_key="default",
            work_item_id=work.id,
            execution_attempt_id=attempt.id,
            position_key=POSITION_KEY,
            expected_execution_token="e" * 64,
            writer="worker-a",
        )

    with pytest.raises(DependencyConflict, match="writer does not own"):
        initial_runtime_session_or_fail(
            db_session,
            tenant_key="default",
            work_item_id=work.id,
            execution_attempt_id=attempt.id,
            position_key=POSITION_KEY,
            expected_execution_token=EXECUTION_TOKEN,
            writer="worker-b",
        )


def test_takeover_owner_can_stage_terminal_completion_and_old_fence_cannot(db_session: Session) -> None:
    work, attempt = _running_attempt(db_session, suffix="takeover", lease_seconds=15)

    takeover = claim_execution_runtime_session(
        db_session,
        tenant_key="default",
        work_item_id=work.id,
        execution_attempt_id=attempt.id,
        position_key=POSITION_KEY,
        expected_execution_token=EXECUTION_TOKEN,
        writer="worker-b",
        observed_at=BASE_TIME + timedelta(seconds=16),
        lease_seconds=60,
    )
    assert takeover.fence_token == 2

    with pytest.raises(DependencyConflict, match="fence token is stale"):
        stage_fenced_agent_completion(
            db_session,
            tenant_key="default",
            work=work,
            attempt=attempt,
            position_key=POSITION_KEY,
            expected_execution_token=EXECUTION_TOKEN,
            expected_fence_token=1,
            writer="worker-a",
            observed_at=BASE_TIME + timedelta(seconds=17),
        )

    completion = stage_fenced_agent_completion(
        db_session,
        tenant_key="default",
        work=work,
        attempt=attempt,
        position_key=POSITION_KEY,
        expected_execution_token=EXECUTION_TOKEN,
        expected_fence_token=takeover.fence_token,
        writer="worker-b",
        observed_at=BASE_TIME + timedelta(seconds=17),
    )
    db_session.commit()
    db_session.refresh(completion)

    events = list(
        db_session.exec(
            select(OrganizationExecutionHeartbeat)
            .where(OrganizationExecutionHeartbeat.execution_attempt_id == attempt.id)
            .order_by(OrganizationExecutionHeartbeat.sequence)
        ).all()
    )
    assert [event.checkpoint for event in events] == [
        "attempt_started",
        "runtime_session_claimed",
        "agent_completed",
    ]
    assert events[-1].writer == "worker-b"


def test_terminal_completion_requires_fresh_current_fence(db_session: Session) -> None:
    work, attempt = _running_attempt(db_session, suffix="expired", lease_seconds=15)

    with pytest.raises(InvalidTransition, match="requires a fresh fenced session"):
        stage_fenced_agent_completion(
            db_session,
            tenant_key="default",
            work=work,
            attempt=attempt,
            position_key=POSITION_KEY,
            expected_execution_token=EXECUTION_TOKEN,
            expected_fence_token=1,
            writer="worker-a",
            observed_at=BASE_TIME + timedelta(seconds=16),
        )
