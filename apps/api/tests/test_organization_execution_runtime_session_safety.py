from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlmodel import Session

from app.models.domain import OrganizationExecutionAttempt, OrganizationalWorkItem
from app.services.organization_command import DependencyConflict, InvalidTransition
from app.services.organization_execution_heartbeat import (
    claim_execution_runtime_session,
    stage_execution_heartbeat,
)


POSITION_KEY = "mobility.pathway_specialist"
EXECUTION_TOKEN = "c" * 64
BASE_TIME = datetime(2026, 8, 26, 9, 0, tzinfo=timezone.utc)


def _running_attempt(
    db_session: Session,
    *,
    suffix: str,
    lease_seconds: int = 30,
) -> tuple[OrganizationalWorkItem, OrganizationExecutionAttempt]:
    work = OrganizationalWorkItem(
        idempotency_key=f"runtime-session-safety-work:{suffix}",
        tenant_key="default",
        work_type="mobility_specialist_work",
        objective_key=f"runtime-session-safety:{suffix}",
        phase_key="J.1.pathway",
        title="Runtime session safety test",
        objective="Prove guarded runtime-session mutation boundaries.",
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
        attempt_key=f"runtime-session-safety-attempt:{suffix}",
        work_item_id=work.id,
        attempt_number=1,
        execution_token=EXECUTION_TOKEN,
        actor="worker-a",
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
        writer="worker-a",
        observed_at=BASE_TIME,
        lease_seconds=lease_seconds,
    )
    db_session.commit()
    db_session.refresh(work)
    db_session.refresh(attempt)
    return work, attempt


def test_generic_checkpoint_api_cannot_bypass_fenced_runtime_session_mutations(
    db_session: Session,
) -> None:
    work, attempt = _running_attempt(db_session, suffix="guarded")

    for checkpoint in ("runtime_session_claimed", "runtime_session_renewed"):
        with pytest.raises(ValueError, match="fenced runtime-session API"):
            stage_execution_heartbeat(
                db_session,
                tenant_key="default",
                work=work,
                attempt=attempt,
                position_key=POSITION_KEY,
                checkpoint=checkpoint,
                writer="worker-a",
                observed_at=BASE_TIME + timedelta(seconds=10),
                lease_seconds=30,
            )


def test_terminal_agent_checkpoint_is_fenced_after_explicit_takeover(db_session: Session) -> None:
    work, attempt = _running_attempt(db_session, suffix="terminal", lease_seconds=30)

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

    with pytest.raises(DependencyConflict, match="original runtime session was superseded"):
        stage_execution_heartbeat(
            db_session,
            tenant_key="default",
            work=work,
            attempt=attempt,
            position_key=POSITION_KEY,
            checkpoint="agent_completed",
            writer="worker-a",
            observed_at=BASE_TIME + timedelta(seconds=32),
            lease_seconds=60,
        )


def test_attempt_started_cannot_be_replayed_as_a_new_session_generation(db_session: Session) -> None:
    work, attempt = _running_attempt(db_session, suffix="duplicate-start")

    with pytest.raises(InvalidTransition, match="attempt_started must be the first heartbeat"):
        stage_execution_heartbeat(
            db_session,
            tenant_key="default",
            work=work,
            attempt=attempt,
            position_key=POSITION_KEY,
            checkpoint="attempt_started",
            writer="worker-a",
            observed_at=BASE_TIME + timedelta(seconds=1),
            lease_seconds=30,
        )
