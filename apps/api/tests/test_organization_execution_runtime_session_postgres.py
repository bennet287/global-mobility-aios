from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

import pytest
from sqlmodel import Session, select

import app.services.organization_execution_heartbeat as heartbeat_service
from app.models.domain import OrganizationExecutionAttempt, OrganizationalWorkItem, now_utc
from app.models.organization_presence import OrganizationExecutionHeartbeat
from app.services.organization_command import DependencyConflict
from app.services.organization_execution_heartbeat import (
    RUNTIME_SESSION_CLAIMED,
    RUNTIME_SESSION_RENEWED,
    claim_execution_runtime_session,
    current_execution_runtime_session,
    renew_execution_runtime_session,
    stage_execution_heartbeat,
)


pytestmark = pytest.mark.skipif(
    not os.getenv("GMAI_TEST_DATABASE_URL", "").startswith("postgresql"),
    reason="real PostgreSQL runtime-fencing contract requires GMAI_TEST_DATABASE_URL",
)

POSITION_KEY = "mobility.pathway_specialist"
EXECUTION_TOKEN = "c" * 64


def _running_attempt(
    db_session: Session,
    *,
    suffix: str,
    writer: str = "worker-a",
    lease_seconds: int = 30,
    stale: bool = False,
) -> tuple[OrganizationalWorkItem, OrganizationExecutionAttempt]:
    observed_at = now_utc() - timedelta(minutes=2) if stale else now_utc()
    work = OrganizationalWorkItem(
        idempotency_key=f"postgres-runtime-session-work:{suffix}",
        tenant_key="default",
        work_type="mobility_specialist_work",
        objective_key=f"postgres-runtime-session-objective:{suffix}",
        phase_key="M.6.runtime",
        title="PostgreSQL runtime-session fencing proof",
        objective="Prove one durable runtime-session mutation winner under a real database race.",
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
        attempt_key=f"postgres-runtime-session-attempt:{suffix}",
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


def _heartbeat_events(session: Session, attempt_id) -> list[OrganizationExecutionHeartbeat]:
    return list(
        session.exec(
            select(OrganizationExecutionHeartbeat)
            .where(OrganizationExecutionHeartbeat.execution_attempt_id == attempt_id)
            .order_by(OrganizationExecutionHeartbeat.sequence)
        ).all()
    )


def test_postgres_two_workers_racing_for_stale_session_produce_one_new_fence(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    work, attempt = _running_attempt(
        db_session,
        suffix="claim-race",
        stale=True,
    )
    engine = db_session.get_bind()
    race_time = now_utc()
    barrier = Barrier(2)
    original_next_sequence = heartbeat_service._next_sequence

    def synchronized_next_sequence(session: Session, execution_attempt_id):
        sequence = original_next_sequence(session, execution_attempt_id)
        if execution_attempt_id == attempt.id:
            barrier.wait(timeout=10)
        return sequence

    monkeypatch.setattr(heartbeat_service, "_next_sequence", synchronized_next_sequence)

    def race_claim(writer: str) -> tuple[str, str, int | str]:
        with Session(engine) as session:
            try:
                lease = claim_execution_runtime_session(
                    session,
                    tenant_key="default",
                    work_item_id=work.id,
                    execution_attempt_id=attempt.id,
                    position_key=POSITION_KEY,
                    expected_execution_token=EXECUTION_TOKEN,
                    writer=writer,
                    observed_at=race_time,
                    lease_seconds=60,
                )
                return "won", writer, lease.fence_token
            except DependencyConflict as exc:
                return "conflict", writer, str(exc)

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(race_claim, ("worker-b", "worker-c")))

    winners = [result for result in results if result[0] == "won"]
    conflicts = [result for result in results if result[0] == "conflict"]
    assert len(winners) == 1
    assert len(conflicts) == 1
    assert winners[0][2] == 2
    assert "concurrent fencing race" in str(conflicts[0][2])

    with Session(engine) as verification_session:
        events = _heartbeat_events(verification_session, attempt.id)
        assert [event.sequence for event in events] == [1, 2]
        assert [event.checkpoint for event in events] == [
            "attempt_started",
            RUNTIME_SESSION_CLAIMED,
        ]
        assert events[1].writer == winners[0][1]

        current = current_execution_runtime_session(
            verification_session,
            tenant_key="default",
            work_item_id=work.id,
            execution_attempt_id=attempt.id,
            position_key=POSITION_KEY,
        )
        assert current is not None
        assert current.fence_token == 2
        assert current.writer == winners[0][1]

        losing_writer = conflicts[0][1]
        with pytest.raises(DependencyConflict, match="fence token is stale"):
            renew_execution_runtime_session(
                verification_session,
                tenant_key="default",
                work_item_id=work.id,
                execution_attempt_id=attempt.id,
                position_key=POSITION_KEY,
                expected_execution_token=EXECUTION_TOKEN,
                expected_fence_token=1,
                writer=losing_writer,
                observed_at=race_time + timedelta(seconds=1),
                lease_seconds=60,
            )


def test_postgres_two_renewals_on_same_fence_commit_exactly_one_heartbeat(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    work, attempt = _running_attempt(
        db_session,
        suffix="renew-race",
        writer="worker-a",
        lease_seconds=120,
    )
    engine = db_session.get_bind()
    race_time = now_utc() + timedelta(seconds=1)
    barrier = Barrier(2)
    original_next_sequence = heartbeat_service._next_sequence

    def synchronized_next_sequence(session: Session, execution_attempt_id):
        sequence = original_next_sequence(session, execution_attempt_id)
        if execution_attempt_id == attempt.id:
            barrier.wait(timeout=10)
        return sequence

    monkeypatch.setattr(heartbeat_service, "_next_sequence", synchronized_next_sequence)

    def race_renew() -> tuple[str, int | str]:
        with Session(engine) as session:
            try:
                lease = renew_execution_runtime_session(
                    session,
                    tenant_key="default",
                    work_item_id=work.id,
                    execution_attempt_id=attempt.id,
                    position_key=POSITION_KEY,
                    expected_execution_token=EXECUTION_TOKEN,
                    expected_fence_token=1,
                    writer="worker-a",
                    observed_at=race_time,
                    lease_seconds=120,
                )
                return "won", lease.fence_token
            except DependencyConflict as exc:
                return "conflict", str(exc)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(race_renew) for _ in range(2)]
        results = [future.result(timeout=20) for future in futures]

    winners = [result for result in results if result[0] == "won"]
    conflicts = [result for result in results if result[0] == "conflict"]
    assert winners == [("won", 1)]
    assert len(conflicts) == 1
    assert "concurrent heartbeat race" in str(conflicts[0][1])

    with Session(engine) as verification_session:
        events = _heartbeat_events(verification_session, attempt.id)
        assert [event.sequence for event in events] == [1, 2]
        assert [event.checkpoint for event in events] == [
            "attempt_started",
            RUNTIME_SESSION_RENEWED,
        ]
        assert all(event.writer == "worker-a" for event in events)

        current = current_execution_runtime_session(
            verification_session,
            tenant_key="default",
            work_item_id=work.id,
            execution_attempt_id=attempt.id,
            position_key=POSITION_KEY,
        )
        assert current is not None
        assert current.fence_token == 1
        assert current.writer == "worker-a"
        assert current.last_heartbeat_id == events[1].id
