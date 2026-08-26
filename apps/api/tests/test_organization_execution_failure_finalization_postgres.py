from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

import pytest
from sqlmodel import Session, select

import app.services.organization_execution_failure as failure_service
import app.services.organization_execution_heartbeat as heartbeat_service
from app.models.domain import OrganizationExecutionAttempt, OrganizationalWorkItem, now_utc
from app.models.organization_presence import OrganizationExecutionHeartbeat
from app.services.organization_command import DependencyConflict
from app.services.organization_execution_failure import (
    RUNTIME_SESSION_FAILED,
    finalize_execution_failure_if_fence_owned,
)
from app.services.organization_execution_heartbeat import (
    RUNTIME_SESSION_CLAIMED,
    claim_execution_runtime_session,
    stage_execution_heartbeat,
)


pytestmark = pytest.mark.skipif(
    not os.getenv("GMAI_TEST_DATABASE_URL", "").startswith("postgresql"),
    reason="real PostgreSQL failure-finalization contract requires GMAI_TEST_DATABASE_URL",
)

POSITION_KEY = "mobility.pathway_specialist"
EXECUTION_TOKEN = "d" * 64


def _stale_running_attempt(
    db_session: Session,
) -> tuple[OrganizationalWorkItem, OrganizationExecutionAttempt]:
    observed_at = now_utc() - timedelta(minutes=2)
    work = OrganizationalWorkItem(
        idempotency_key="postgres-failure-finalization-work",
        tenant_key="default",
        work_type="mobility_specialist_work",
        objective_key="postgres-failure-finalization-objective",
        phase_key="M.6.failure",
        title="PostgreSQL fenced failure finalization proof",
        objective="Prove takeover and stale failure cannot both mutate the same generation.",
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
        attempt_key="postgres-failure-finalization-attempt",
        work_item_id=work.id,
        attempt_number=1,
        execution_token=EXECUTION_TOKEN,
        actor="worker-a",
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
        writer="worker-a",
        observed_at=observed_at,
        lease_seconds=30,
    )
    db_session.commit()
    db_session.refresh(work)
    db_session.refresh(attempt)
    return work, attempt


def test_postgres_takeover_and_stale_failure_have_one_durable_winner(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    work, attempt = _stale_running_attempt(db_session)
    engine = db_session.get_bind()
    race_time = now_utc()
    barrier = Barrier(2)
    original_failure_next = failure_service._next_sequence
    original_heartbeat_next = heartbeat_service._next_sequence
    failure_sequence_calls = 0

    def synchronized_failure_next(session: Session, execution_attempt_id):
        nonlocal failure_sequence_calls
        sequence = original_failure_next(session, execution_attempt_id)
        if execution_attempt_id == attempt.id:
            failure_sequence_calls += 1
            if failure_sequence_calls == 1:
                barrier.wait(timeout=10)
        return sequence

    def synchronized_heartbeat_next(session: Session, execution_attempt_id):
        sequence = original_heartbeat_next(session, execution_attempt_id)
        if execution_attempt_id == attempt.id:
            barrier.wait(timeout=10)
        return sequence

    monkeypatch.setattr(failure_service, "_next_sequence", synchronized_failure_next)
    monkeypatch.setattr(heartbeat_service, "_next_sequence", synchronized_heartbeat_next)

    def finalize_original_failure() -> tuple[str, str]:
        with Session(engine) as session:
            result = finalize_execution_failure_if_fence_owned(
                session,
                tenant_key="default",
                work_item_id=work.id,
                execution_attempt_id=attempt.id,
                position_key=POSITION_KEY,
                expected_execution_token=EXECUTION_TOKEN,
                expected_fence_token=1,
                writer="worker-a",
                error=RuntimeError("original worker returned late failure"),
            )
            return "failure", result.reason

    def claim_takeover() -> tuple[str, str]:
        with Session(engine) as session:
            try:
                lease = claim_execution_runtime_session(
                    session,
                    tenant_key="default",
                    work_item_id=work.id,
                    execution_attempt_id=attempt.id,
                    position_key=POSITION_KEY,
                    expected_execution_token=EXECUTION_TOKEN,
                    writer="worker-b",
                    observed_at=race_time,
                    lease_seconds=60,
                )
                return "takeover", f"won:{lease.fence_token}"
            except DependencyConflict as exc:
                return "takeover", f"conflict:{exc}"

    with ThreadPoolExecutor(max_workers=2) as executor:
        failure_future = executor.submit(finalize_original_failure)
        takeover_future = executor.submit(claim_takeover)
        failure_result = failure_future.result(timeout=20)
        takeover_result = takeover_future.result(timeout=20)

    with Session(engine) as verification_session:
        persisted_attempt = verification_session.get(OrganizationExecutionAttempt, attempt.id)
        persisted_work = verification_session.get(OrganizationalWorkItem, work.id)
        assert persisted_attempt is not None and persisted_work is not None
        events = list(
            verification_session.exec(
                select(OrganizationExecutionHeartbeat)
                .where(OrganizationExecutionHeartbeat.execution_attempt_id == attempt.id)
                .order_by(OrganizationExecutionHeartbeat.sequence)
            ).all()
        )
        assert [event.sequence for event in events] == [1, 2]
        assert events[0].checkpoint == "attempt_started"

        if events[1].checkpoint == RUNTIME_SESSION_CLAIMED:
            assert events[1].writer == "worker-b"
            assert failure_result == ("failure", "runtime_session_ownership_lost")
            assert takeover_result == ("takeover", "won:2")
            assert persisted_attempt.status == "running"
            assert persisted_attempt.error is None
            assert persisted_work.last_error is None
        else:
            assert events[1].checkpoint == RUNTIME_SESSION_FAILED
            assert events[1].writer == "worker-a"
            assert failure_result == ("failure", "failure_finalized")
            assert takeover_result[0] == "takeover"
            assert takeover_result[1].startswith("conflict:")
            assert persisted_attempt.status == "failed"
            assert persisted_attempt.error == "RuntimeError: original worker returned late failure"
            assert persisted_work.last_error == "RuntimeError: original worker returned late failure"