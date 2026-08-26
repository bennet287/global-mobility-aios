from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlmodel import Session, select

from app.models.domain import OrganizationExecutionAttempt, OrganizationalWorkItem
from app.models.organization_presence import OrganizationExecutionHeartbeat
from app.services.organization_command import DependencyConflict, InvalidTransition
from app.services.organization_execution_heartbeat import (
    RUNTIME_SESSION_CLAIMED,
    RUNTIME_SESSION_RENEWED,
    claim_execution_runtime_session,
    current_execution_runtime_session,
    renew_execution_runtime_session,
    stage_execution_heartbeat,
)


POSITION_KEY = "mobility.pathway_specialist"
EXECUTION_TOKEN = "a" * 64
BASE_TIME = datetime(2026, 8, 26, 8, 0, tzinfo=timezone.utc)


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _running_attempt(
    db_session: Session,
    *,
    suffix: str,
    writer: str = "worker-a",
    lease_seconds: int = 60,
) -> tuple[OrganizationalWorkItem, OrganizationExecutionAttempt]:
    work = OrganizationalWorkItem(
        idempotency_key=f"runtime-session-work:{suffix}",
        tenant_key="default",
        work_type="mobility_specialist_work",
        objective_key=f"runtime-session-objective:{suffix}",
        phase_key="J.1.pathway",
        title="Runtime session fencing test",
        objective="Prove durable runtime-session fencing semantics.",
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
        attempt_key=f"runtime-session-attempt:{suffix}",
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


def test_attempt_started_is_generation_one_runtime_session_claim(db_session: Session) -> None:
    work, attempt = _running_attempt(db_session, suffix="initial")

    runtime_session = current_execution_runtime_session(
        db_session,
        tenant_key="default",
        work_item_id=work.id,
        execution_attempt_id=attempt.id,
        position_key=POSITION_KEY,
    )

    assert runtime_session is not None
    assert runtime_session.fence_token == 1
    assert runtime_session.writer == "worker-a"
    assert runtime_session.execution_token == EXECUTION_TOKEN
    assert _utc(runtime_session.observed_at) == BASE_TIME
    assert _utc(runtime_session.fresh_until) == BASE_TIME + timedelta(seconds=60)


def test_runtime_session_renewal_preserves_fence_and_extends_lease(db_session: Session) -> None:
    work, attempt = _running_attempt(db_session, suffix="renew")

    renewed = renew_execution_runtime_session(
        db_session,
        tenant_key="default",
        work_item_id=work.id,
        execution_attempt_id=attempt.id,
        position_key=POSITION_KEY,
        expected_execution_token=EXECUTION_TOKEN,
        expected_fence_token=1,
        writer="worker-a",
        observed_at=BASE_TIME + timedelta(seconds=30),
        lease_seconds=60,
    )

    assert renewed.fence_token == 1
    assert renewed.writer == "worker-a"
    assert _utc(renewed.observed_at) == BASE_TIME + timedelta(seconds=30)
    assert _utc(renewed.fresh_until) == BASE_TIME + timedelta(seconds=90)

    events = list(
        db_session.exec(
            select(OrganizationExecutionHeartbeat)
            .where(OrganizationExecutionHeartbeat.execution_attempt_id == attempt.id)
            .order_by(OrganizationExecutionHeartbeat.sequence)
        ).all()
    )
    assert [event.sequence for event in events] == [1, 2]
    assert [event.checkpoint for event in events] == ["attempt_started", RUNTIME_SESSION_RENEWED]


def test_stale_session_takeover_increments_fence_and_rejects_old_worker(db_session: Session) -> None:
    work, attempt = _running_attempt(
        db_session,
        suffix="takeover",
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
        observed_at=BASE_TIME + timedelta(seconds=31),
        lease_seconds=60,
    )

    assert takeover.fence_token == 2
    assert takeover.writer == "worker-b"

    with pytest.raises(DependencyConflict, match="fence token is stale"):
        renew_execution_runtime_session(
            db_session,
            tenant_key="default",
            work_item_id=work.id,
            execution_attempt_id=attempt.id,
            position_key=POSITION_KEY,
            expected_execution_token=EXECUTION_TOKEN,
            expected_fence_token=1,
            writer="worker-a",
            observed_at=BASE_TIME + timedelta(seconds=32),
            lease_seconds=60,
        )

    renewed = renew_execution_runtime_session(
        db_session,
        tenant_key="default",
        work_item_id=work.id,
        execution_attempt_id=attempt.id,
        position_key=POSITION_KEY,
        expected_execution_token=EXECUTION_TOKEN,
        expected_fence_token=takeover.fence_token,
        writer="worker-b",
        observed_at=BASE_TIME + timedelta(seconds=32),
        lease_seconds=60,
    )
    assert renewed.fence_token == 2
    assert renewed.writer == "worker-b"

    events = list(
        db_session.exec(
            select(OrganizationExecutionHeartbeat)
            .where(OrganizationExecutionHeartbeat.execution_attempt_id == attempt.id)
            .order_by(OrganizationExecutionHeartbeat.sequence)
        ).all()
    )
    assert [event.checkpoint for event in events] == [
        "attempt_started",
        RUNTIME_SESSION_CLAIMED,
        RUNTIME_SESSION_RENEWED,
    ]


def test_fresh_session_cannot_be_stolen_and_same_writer_claim_is_idempotent(
    db_session: Session,
) -> None:
    work, attempt = _running_attempt(db_session, suffix="fresh")

    same = claim_execution_runtime_session(
        db_session,
        tenant_key="default",
        work_item_id=work.id,
        execution_attempt_id=attempt.id,
        position_key=POSITION_KEY,
        expected_execution_token=EXECUTION_TOKEN,
        writer="worker-a",
        observed_at=BASE_TIME + timedelta(seconds=10),
        lease_seconds=60,
    )
    assert same.fence_token == 1

    with pytest.raises(DependencyConflict, match="already held by a fresh fenced writer"):
        claim_execution_runtime_session(
            db_session,
            tenant_key="default",
            work_item_id=work.id,
            execution_attempt_id=attempt.id,
            position_key=POSITION_KEY,
            expected_execution_token=EXECUTION_TOKEN,
            writer="worker-b",
            observed_at=BASE_TIME + timedelta(seconds=10),
            lease_seconds=60,
        )

    events = list(
        db_session.exec(
            select(OrganizationExecutionHeartbeat).where(
                OrganizationExecutionHeartbeat.execution_attempt_id == attempt.id
            )
        ).all()
    )
    assert len(events) == 1


def test_expired_session_requires_reclaim_and_execution_token_mismatch_fails_closed(
    db_session: Session,
) -> None:
    work, attempt = _running_attempt(
        db_session,
        suffix="expired",
        lease_seconds=30,
    )

    with pytest.raises(InvalidTransition, match="must be reclaimed"):
        renew_execution_runtime_session(
            db_session,
            tenant_key="default",
            work_item_id=work.id,
            execution_attempt_id=attempt.id,
            position_key=POSITION_KEY,
            expected_execution_token=EXECUTION_TOKEN,
            expected_fence_token=1,
            writer="worker-a",
            observed_at=BASE_TIME + timedelta(seconds=31),
            lease_seconds=60,
        )

    with pytest.raises(DependencyConflict, match="stale execution token"):
        claim_execution_runtime_session(
            db_session,
            tenant_key="default",
            work_item_id=work.id,
            execution_attempt_id=attempt.id,
            position_key=POSITION_KEY,
            expected_execution_token="b" * 64,
            writer="worker-b",
            observed_at=BASE_TIME + timedelta(seconds=31),
            lease_seconds=60,
        )
