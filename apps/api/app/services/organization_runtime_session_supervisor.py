from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import Event, Lock, Thread
from typing import Callable
from uuid import UUID

from sqlmodel import Session, select

from app.core import db as db_module
from app.models.domain import OrganizationExecutionAttempt, OrganizationalWorkItem, now_utc
from app.models.organization_presence import OrganizationExecutionHeartbeat
from app.services.organization_command import DependencyConflict, InvalidTransition
from app.services.organization_execution_heartbeat import (
    DEFAULT_HEARTBEAT_LEASE_SECONDS,
    ExecutionRuntimeSessionLease,
    current_execution_runtime_session,
    renew_execution_runtime_session,
)


DEFAULT_RUNTIME_RENEWAL_INTERVAL_SECONDS = 40.0
_TERMINAL_CHECKPOINT = "agent_completed"


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _validate_fence_token(value: int) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError("runtime session fence token must be a positive integer")


def _validate_runtime_supervisor_timing(*, lease_seconds: int, renewal_interval_seconds: float) -> None:
    if not isinstance(lease_seconds, int) or isinstance(lease_seconds, bool) or lease_seconds < 1:
        raise ValueError("runtime session lease must be a positive integer number of seconds")
    if not isinstance(renewal_interval_seconds, (int, float)) or isinstance(
        renewal_interval_seconds, bool
    ):
        raise ValueError("runtime renewal interval must be a number of seconds")
    if renewal_interval_seconds <= 0:
        raise ValueError("runtime renewal interval must be positive")
    if renewal_interval_seconds >= (lease_seconds / 2):
        raise ValueError("runtime renewal interval must remain below half of the lease")


@dataclass(frozen=True, slots=True)
class RuntimeSessionSupervisorSnapshot:
    execution_attempt_id: UUID
    fence_token: int
    writer: str
    renewal_count: int
    last_observed_at: datetime | None
    last_fresh_until: datetime | None
    healthy: bool


RenewOnce = Callable[[], ExecutionRuntimeSessionLease]


class ExecutionRuntimeSessionSupervisor:
    """Renew one fenced execution lease only while a bounded worker call is active.

    This object is intentionally scoped to a caller-owned context. It is not a daemon
    presence service and it does not create an always-online employee signal. The
    supervisor stops as soon as the guarded execution section ends. Any renewal failure
    is retained and must be checked before terminal state is committed.
    """

    def __init__(
        self,
        *,
        tenant_key: str,
        work_item_id: UUID,
        execution_attempt_id: UUID,
        position_key: str,
        expected_execution_token: str,
        expected_fence_token: int,
        writer: str,
        lease_seconds: int = DEFAULT_HEARTBEAT_LEASE_SECONDS,
        renewal_interval_seconds: float = DEFAULT_RUNTIME_RENEWAL_INTERVAL_SECONDS,
        renew_once: RenewOnce | None = None,
    ) -> None:
        _validate_fence_token(expected_fence_token)
        _validate_runtime_supervisor_timing(
            lease_seconds=lease_seconds,
            renewal_interval_seconds=renewal_interval_seconds,
        )
        if not expected_execution_token.strip():
            raise ValueError("runtime supervisor execution token is required")
        if not writer.strip():
            raise ValueError("runtime supervisor writer is required")

        self.tenant_key = tenant_key
        self.work_item_id = work_item_id
        self.execution_attempt_id = execution_attempt_id
        self.position_key = position_key
        self.expected_execution_token = expected_execution_token
        self.expected_fence_token = expected_fence_token
        self.writer = writer
        self.lease_seconds = lease_seconds
        self.renewal_interval_seconds = float(renewal_interval_seconds)
        self._renew_once_override = renew_once

        self._stop_event = Event()
        self._lock = Lock()
        self._thread: Thread | None = None
        self._failure: Exception | None = None
        self._renewal_count = 0
        self._last_observed_at: datetime | None = None
        self._last_fresh_until: datetime | None = None

    def _renew_once(self) -> ExecutionRuntimeSessionLease:
        if self._renew_once_override is not None:
            return self._renew_once_override()
        with Session(db_module.engine) as session:
            return renew_execution_runtime_session(
                session,
                tenant_key=self.tenant_key,
                work_item_id=self.work_item_id,
                execution_attempt_id=self.execution_attempt_id,
                position_key=self.position_key,
                expected_execution_token=self.expected_execution_token,
                expected_fence_token=self.expected_fence_token,
                writer=self.writer,
                lease_seconds=self.lease_seconds,
            )

    def _run(self) -> None:
        while not self._stop_event.wait(self.renewal_interval_seconds):
            try:
                renewed = self._renew_once()
                if renewed.fence_token != self.expected_fence_token:
                    raise DependencyConflict("runtime renewal returned a different fencing generation")
                if renewed.writer != self.writer:
                    raise DependencyConflict("runtime renewal returned a different writer")
                with self._lock:
                    self._renewal_count += 1
                    self._last_observed_at = renewed.observed_at
                    self._last_fresh_until = renewed.fresh_until
            except Exception as exc:  # pragma: no branch - single fail-closed path
                with self._lock:
                    self._failure = exc
                self._stop_event.set()
                return

    def start(self) -> "ExecutionRuntimeSessionSupervisor":
        if self._thread is not None:
            raise RuntimeError("runtime session supervisor has already been started")
        self._stop_event.clear()
        self._thread = Thread(
            target=self._run,
            name=f"runtime-session-renewal:{self.execution_attempt_id}",
            daemon=True,
        )
        self._thread.start()
        return self

    def assert_healthy(self) -> None:
        with self._lock:
            failure = self._failure
        if failure is not None:
            raise DependencyConflict(
                f"runtime session renewal supervisor lost the current fence: {type(failure).__name__}: {failure}"
            ) from failure

    def stop(self) -> RuntimeSessionSupervisorSnapshot:
        self._stop_event.set()
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=max(1.0, min(5.0, self.renewal_interval_seconds * 2)))
        if thread is not None and thread.is_alive():
            raise RuntimeError("runtime session renewal supervisor did not stop cleanly")
        self.assert_healthy()
        return self.snapshot()

    def snapshot(self) -> RuntimeSessionSupervisorSnapshot:
        with self._lock:
            return RuntimeSessionSupervisorSnapshot(
                execution_attempt_id=self.execution_attempt_id,
                fence_token=self.expected_fence_token,
                writer=self.writer,
                renewal_count=self._renewal_count,
                last_observed_at=self._last_observed_at,
                last_fresh_until=self._last_fresh_until,
                healthy=self._failure is None,
            )

    def __enter__(self) -> "ExecutionRuntimeSessionSupervisor":
        return self.start()

    def __exit__(self, exc_type, exc, traceback) -> bool:
        self._stop_event.set()
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=max(1.0, min(5.0, self.renewal_interval_seconds * 2)))
        if exc_type is None:
            self.assert_healthy()
            if thread is not None and thread.is_alive():
                raise RuntimeError("runtime session renewal supervisor did not stop cleanly")
        return False


def initial_runtime_session_or_fail(
    session: Session,
    *,
    tenant_key: str,
    work_item_id: UUID,
    execution_attempt_id: UUID,
    position_key: str,
    expected_execution_token: str,
    writer: str,
) -> ExecutionRuntimeSessionLease:
    current = current_execution_runtime_session(
        session,
        tenant_key=tenant_key,
        work_item_id=work_item_id,
        execution_attempt_id=execution_attempt_id,
        position_key=position_key,
    )
    if current is None:
        raise DependencyConflict("runtime supervisor requires an established execution session")
    if current.execution_token != expected_execution_token:
        raise DependencyConflict("runtime supervisor execution token is stale")
    if current.writer != writer:
        raise DependencyConflict("runtime supervisor writer does not own the current session")
    return current


def stage_fenced_agent_completion(
    session: Session,
    *,
    tenant_key: str,
    work: OrganizationalWorkItem,
    attempt: OrganizationExecutionAttempt,
    position_key: str,
    expected_execution_token: str,
    expected_fence_token: int,
    writer: str,
    observed_at: datetime | None = None,
) -> OrganizationExecutionHeartbeat:
    """Stage terminal agent completion only for the current fresh fenced owner.

    This is the terminal companion to the renewal supervisor. A takeover worker can
    legitimately complete by presenting its current fence; an older worker cannot commit
    a late result after a newer claim exists.
    """

    _validate_fence_token(expected_fence_token)
    if not writer.strip():
        raise ValueError("runtime completion writer is required")
    if work.tenant_key != tenant_key:
        raise DependencyConflict("runtime completion WorkItem crosses the tenant boundary")
    if work.assigned_position_key != position_key:
        raise DependencyConflict("runtime completion position does not match the WorkItem assignment")
    if attempt.work_item_id != work.id:
        raise DependencyConflict("runtime completion attempt does not belong to the WorkItem")
    if work.status != "running" or attempt.status != "running":
        raise InvalidTransition("runtime completion requires running WorkItem and execution attempt")
    if not work.execution_token or work.execution_token != attempt.execution_token:
        raise DependencyConflict("runtime completion execution token conflicts with canonical work state")
    if attempt.execution_token != expected_execution_token:
        raise DependencyConflict("runtime completion caller holds a stale execution token")

    current = current_execution_runtime_session(
        session,
        tenant_key=tenant_key,
        work_item_id=work.id,
        execution_attempt_id=attempt.id,
        position_key=position_key,
    )
    if current is None:
        raise DependencyConflict("runtime completion requires an established fenced session")
    if current.fence_token != expected_fence_token:
        raise DependencyConflict("runtime completion fence token is stale")
    if current.writer != writer:
        raise DependencyConflict("runtime completion writer does not own the current fence")

    completed_at = _as_utc(observed_at or now_utc())
    if _as_utc(current.fresh_until) <= completed_at:
        raise InvalidTransition("runtime completion requires a fresh fenced session")

    latest = session.exec(
        select(OrganizationExecutionHeartbeat)
        .where(OrganizationExecutionHeartbeat.execution_attempt_id == attempt.id)
        .order_by(OrganizationExecutionHeartbeat.sequence.desc())
    ).first()
    sequence = 1 if latest is None else latest.sequence + 1
    heartbeat = OrganizationExecutionHeartbeat(
        heartbeat_key=f"execution-heartbeat:{attempt.id}:{sequence}",
        tenant_key=tenant_key,
        position_key=position_key,
        work_item_id=work.id,
        execution_attempt_id=attempt.id,
        sequence=sequence,
        checkpoint=_TERMINAL_CHECKPOINT,
        writer=writer,
        observed_at=completed_at,
        fresh_until=completed_at + timedelta(seconds=DEFAULT_HEARTBEAT_LEASE_SECONDS),
    )
    session.add(heartbeat)
    return heartbeat
