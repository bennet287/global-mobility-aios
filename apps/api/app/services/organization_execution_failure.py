from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.models.domain import OrganizationExecutionAttempt, OrganizationalWorkItem, now_utc
from app.models.organization_presence import OrganizationExecutionHeartbeat
from app.services.organization_command import DependencyConflict, InvalidTransition
from app.services.organization_execution_heartbeat import (
    DEFAULT_HEARTBEAT_LEASE_SECONDS,
    current_execution_runtime_session,
)


RUNTIME_SESSION_FAILED = "runtime_session_failed"
_MAX_FINALIZATION_ATTEMPTS = 2


@dataclass(frozen=True, slots=True)
class ExecutionFailureFinalizationResult:
    """Outcome of a fence-aware attempt to persist one worker failure.

    ``applied`` is true only when the caller still owned the exact execution token,
    fencing generation, and writer identity at commit time. A false result deliberately
    means no canonical attempt/work failure mutation was persisted.
    """

    applied: bool
    reason: str
    failure_sequence: int | None = None


def _next_sequence(session: Session, execution_attempt_id: UUID) -> int:
    latest = session.exec(
        select(OrganizationExecutionHeartbeat)
        .where(OrganizationExecutionHeartbeat.execution_attempt_id == execution_attempt_id)
        .order_by(OrganizationExecutionHeartbeat.sequence.desc())
    ).first()
    return 1 if latest is None else latest.sequence + 1


def _canonical_running_execution(
    session: Session,
    *,
    tenant_key: str,
    work_item_id: UUID,
    execution_attempt_id: UUID,
    position_key: str,
    expected_execution_token: str,
) -> tuple[OrganizationalWorkItem, OrganizationExecutionAttempt] | None:
    work = session.exec(
        select(OrganizationalWorkItem).where(
            OrganizationalWorkItem.id == work_item_id,
            OrganizationalWorkItem.tenant_key == tenant_key,
        )
    ).first()
    attempt = session.get(OrganizationExecutionAttempt, execution_attempt_id)
    if work is None or attempt is None:
        return None
    if attempt.work_item_id != work.id or work.assigned_position_key != position_key:
        return None
    if work.status != "running" or attempt.status != "running":
        return None
    if (
        not work.execution_token
        or work.execution_token != attempt.execution_token
        or attempt.execution_token != expected_execution_token
    ):
        return None
    return work, attempt


def finalize_execution_failure_if_fence_owned(
    session: Session,
    *,
    tenant_key: str,
    work_item_id: UUID,
    execution_attempt_id: UUID,
    position_key: str,
    expected_execution_token: str,
    expected_fence_token: int,
    writer: str,
    error: Exception,
) -> ExecutionFailureFinalizationResult:
    """Persist a worker failure only while that worker still owns the current fence.

    The caller enters this helper after an execution exception, so any uncommitted output
    is rolled back first. Failure finalization itself appends a durable terminal runtime
    checkpoint in the same transaction as the attempt/work mutation. That heartbeat
    sequence is the concurrency fence: a concurrent takeover or renewal that chose the
    same next sequence can win, but both transactions cannot commit.

    Lease freshness is intentionally *not* required. An expired worker that has not been
    superseded still owns its current generation and may accurately record its own
    failure. Once a newer claim exists, an older worker is permanently unable to mutate
    canonical failure state.
    """

    if not expected_execution_token.strip():
        raise ValueError("failure finalization execution token is required")
    if (
        not isinstance(expected_fence_token, int)
        or isinstance(expected_fence_token, bool)
        or expected_fence_token < 1
    ):
        raise ValueError("failure finalization fence token must be a positive integer")
    if not writer.strip():
        raise ValueError("failure finalization writer is required")

    error_text = f"{type(error).__name__}: {error}"[:2000]

    for attempt_index in range(_MAX_FINALIZATION_ATTEMPTS):
        session.rollback()
        canonical = _canonical_running_execution(
            session,
            tenant_key=tenant_key,
            work_item_id=work_item_id,
            execution_attempt_id=execution_attempt_id,
            position_key=position_key,
            expected_execution_token=expected_execution_token,
        )
        if canonical is None:
            return ExecutionFailureFinalizationResult(False, "canonical_execution_not_running")
        work, execution_attempt = canonical

        try:
            current = current_execution_runtime_session(
                session,
                tenant_key=tenant_key,
                work_item_id=work.id,
                execution_attempt_id=execution_attempt.id,
                position_key=position_key,
            )
        except (DependencyConflict, InvalidTransition):
            session.rollback()
            return ExecutionFailureFinalizationResult(False, "runtime_session_not_provable")

        if current is None:
            session.rollback()
            return ExecutionFailureFinalizationResult(False, "runtime_session_not_established")
        if (
            current.execution_token != expected_execution_token
            or current.fence_token != expected_fence_token
            or current.writer != writer
        ):
            session.rollback()
            return ExecutionFailureFinalizationResult(False, "runtime_session_ownership_lost")

        failed_at = now_utc()
        sequence = _next_sequence(session, execution_attempt.id)
        failure_heartbeat = OrganizationExecutionHeartbeat(
            heartbeat_key=f"execution-heartbeat:{execution_attempt.id}:{sequence}",
            tenant_key=tenant_key,
            position_key=position_key,
            work_item_id=work.id,
            execution_attempt_id=execution_attempt.id,
            sequence=sequence,
            checkpoint=RUNTIME_SESSION_FAILED,
            writer=writer,
            observed_at=failed_at,
            fresh_until=failed_at + timedelta(seconds=DEFAULT_HEARTBEAT_LEASE_SECONDS),
        )
        execution_attempt.status = "failed"
        execution_attempt.completed_at = failed_at
        execution_attempt.error = error_text
        work.execution_started_at = None
        work.last_error = error_text
        work.updated_at = failed_at
        session.add(failure_heartbeat)
        session.add(execution_attempt)
        session.add(work)

        try:
            session.commit()
            return ExecutionFailureFinalizationResult(True, "failure_finalized", sequence)
        except IntegrityError:
            session.rollback()
            if attempt_index + 1 >= _MAX_FINALIZATION_ATTEMPTS:
                return ExecutionFailureFinalizationResult(False, "concurrent_runtime_event")

    return ExecutionFailureFinalizationResult(False, "concurrent_runtime_event")
