from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.models.domain import OrganizationExecutionAttempt, OrganizationalWorkItem, now_utc
from app.models.organization_presence import OrganizationExecutionHeartbeat
from app.services.organization_command import DependencyConflict, InvalidTransition


HEARTBEAT_CAPABILITY_CHECKPOINT_LEASE = "execution_checkpoint_lease"
HEARTBEAT_FRESH = "fresh"
HEARTBEAT_STALE = "stale"
HEARTBEAT_NOT_ESTABLISHED = "not_established"
HEARTBEAT_INACTIVE = "inactive"

DEFAULT_HEARTBEAT_LEASE_SECONDS = 120
MIN_HEARTBEAT_LEASE_SECONDS = 15
MAX_HEARTBEAT_LEASE_SECONDS = 300

RUNTIME_SESSION_CLAIMED = "runtime_session_claimed"
RUNTIME_SESSION_RENEWED = "runtime_session_renewed"
_RUNTIME_SESSION_CLAIM_CHECKPOINTS = frozenset({"attempt_started", RUNTIME_SESSION_CLAIMED})
_RUNTIME_SESSION_EVENT_CHECKPOINTS = frozenset(
    {*_RUNTIME_SESSION_CLAIM_CHECKPOINTS, RUNTIME_SESSION_RENEWED}
)
_ALLOWED_CHECKPOINTS = frozenset(
    {"attempt_started", "agent_completed", RUNTIME_SESSION_CLAIMED, RUNTIME_SESSION_RENEWED}
)


@dataclass(frozen=True, slots=True)
class ExecutionRuntimeSessionLease:
    """Derived, fenced worker-session lease backed only by durable heartbeat events.

    ``fence_token`` is the sequence number of the latest durable claim event for the
    execution attempt. Renewals preserve that fence. A later claim therefore invalidates
    every writer still holding an older fence without introducing a parallel authority
    or canonical-work state model.
    """

    execution_attempt_id: UUID
    work_item_id: UUID
    position_key: str
    execution_token: str
    fence_token: int
    writer: str
    observed_at: datetime
    fresh_until: datetime
    last_heartbeat_id: UUID


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _validate_lease_seconds(lease_seconds: int) -> None:
    if not isinstance(lease_seconds, int) or isinstance(lease_seconds, bool):
        raise ValueError("heartbeat lease must be an integer number of seconds")
    if not MIN_HEARTBEAT_LEASE_SECONDS <= lease_seconds <= MAX_HEARTBEAT_LEASE_SECONDS:
        raise ValueError(
            f"heartbeat lease must be between {MIN_HEARTBEAT_LEASE_SECONDS} and "
            f"{MAX_HEARTBEAT_LEASE_SECONDS} seconds"
        )


def _next_sequence(session: Session, execution_attempt_id: UUID) -> int:
    latest = session.exec(
        select(OrganizationExecutionHeartbeat)
        .where(OrganizationExecutionHeartbeat.execution_attempt_id == execution_attempt_id)
        .order_by(OrganizationExecutionHeartbeat.sequence.desc())
    ).first()
    return 1 if latest is None else latest.sequence + 1


def _resolve_execution_state(
    session: Session,
    *,
    tenant_key: str,
    work_item_id: UUID,
    execution_attempt_id: UUID,
    position_key: str,
    expected_execution_token: str | None = None,
    require_running: bool,
) -> tuple[OrganizationalWorkItem, OrganizationExecutionAttempt]:
    work = session.exec(
        select(OrganizationalWorkItem).where(
            OrganizationalWorkItem.id == work_item_id,
            OrganizationalWorkItem.tenant_key == tenant_key,
        )
    ).first()
    if work is None:
        raise DependencyConflict("runtime session WorkItem was not found for the tenant")
    attempt = session.get(OrganizationExecutionAttempt, execution_attempt_id)
    if attempt is None:
        raise DependencyConflict("runtime session execution attempt was not found")
    if attempt.work_item_id != work.id:
        raise DependencyConflict("runtime session execution attempt does not belong to the WorkItem")
    if work.assigned_position_key != position_key:
        raise DependencyConflict("runtime session position does not match the WorkItem assignment")
    if not work.execution_token or work.execution_token != attempt.execution_token:
        raise DependencyConflict("runtime session execution token conflicts with canonical work state")
    if expected_execution_token is not None and attempt.execution_token != expected_execution_token:
        raise DependencyConflict("runtime session caller holds a stale execution token")
    if require_running and (work.status != "running" or attempt.status != "running"):
        raise InvalidTransition("runtime session operations require running WorkItem and execution attempt")
    return work, attempt


def stage_execution_heartbeat(
    session: Session,
    *,
    tenant_key: str,
    work: OrganizationalWorkItem,
    attempt: OrganizationExecutionAttempt,
    position_key: str,
    checkpoint: str,
    writer: str = "organization-worker",
    observed_at: datetime | None = None,
    lease_seconds: int = DEFAULT_HEARTBEAT_LEASE_SECONDS,
) -> OrganizationExecutionHeartbeat:
    """Stage one trusted execution-checkpoint lease in the caller's transaction.

    The caller owns commit/rollback. The checkpoint is deliberately narrow: it proves
    only that an AIOS worker reached this execution point. It does not prove continuous
    liveness and has no authority, autonomy, evidence, or external-action effect.

    ``attempt_started`` is also the initial runtime-session claim. Later explicit
    ``runtime_session_claimed`` events create a new fencing generation, while
    ``runtime_session_renewed`` extends only the current generation through the guarded
    APIs below.
    """

    _validate_lease_seconds(lease_seconds)
    if checkpoint not in _ALLOWED_CHECKPOINTS:
        raise ValueError("unsupported execution heartbeat checkpoint")
    if not writer.strip():
        raise ValueError("heartbeat writer is required")
    if work.tenant_key != tenant_key:
        raise DependencyConflict("heartbeat WorkItem crosses the requested tenant boundary")
    if work.assigned_position_key != position_key:
        raise DependencyConflict("heartbeat position does not match the WorkItem assignment")
    if attempt.work_item_id != work.id:
        raise DependencyConflict("heartbeat execution attempt does not belong to the WorkItem")
    if work.status != "running" or attempt.status != "running":
        raise InvalidTransition("heartbeat checkpoints require running WorkItem and execution attempt")
    if not work.execution_token or work.execution_token != attempt.execution_token:
        raise DependencyConflict("heartbeat execution token conflicts with canonical work state")

    sequence = _next_sequence(session, attempt.id)
    recorded_at = _as_utc(observed_at or now_utc())
    heartbeat = OrganizationExecutionHeartbeat(
        heartbeat_key=f"execution-heartbeat:{attempt.id}:{sequence}",
        tenant_key=tenant_key,
        position_key=position_key,
        work_item_id=work.id,
        execution_attempt_id=attempt.id,
        sequence=sequence,
        checkpoint=checkpoint,
        writer=writer,
        observed_at=recorded_at,
        fresh_until=recorded_at + timedelta(seconds=lease_seconds),
    )
    session.add(heartbeat)
    return heartbeat


def record_execution_heartbeat(
    session: Session,
    *,
    tenant_key: str,
    work_item_id: UUID,
    execution_attempt_id: UUID,
    position_key: str,
    checkpoint: str,
    writer: str = "organization-worker",
    observed_at: datetime | None = None,
    lease_seconds: int = DEFAULT_HEARTBEAT_LEASE_SECONDS,
) -> OrganizationExecutionHeartbeat:
    """Persist one heartbeat checkpoint after re-resolving tenant and execution state."""

    work, attempt = _resolve_execution_state(
        session,
        tenant_key=tenant_key,
        work_item_id=work_item_id,
        execution_attempt_id=execution_attempt_id,
        position_key=position_key,
        require_running=True,
    )
    heartbeat = stage_execution_heartbeat(
        session,
        tenant_key=tenant_key,
        work=work,
        attempt=attempt,
        position_key=position_key,
        checkpoint=checkpoint,
        writer=writer,
        observed_at=observed_at,
        lease_seconds=lease_seconds,
    )
    session.commit()
    session.refresh(heartbeat)
    return heartbeat


def latest_execution_heartbeat(
    session: Session,
    *,
    tenant_key: str,
    work_item_id: UUID,
    execution_attempt_id: UUID,
    position_key: str,
) -> OrganizationExecutionHeartbeat | None:
    """Return the latest checkpoint only when its durable bindings remain consistent."""

    heartbeat = session.exec(
        select(OrganizationExecutionHeartbeat)
        .where(OrganizationExecutionHeartbeat.execution_attempt_id == execution_attempt_id)
        .order_by(
            OrganizationExecutionHeartbeat.sequence.desc(),
            OrganizationExecutionHeartbeat.observed_at.desc(),
        )
    ).first()
    if heartbeat is None:
        return None
    if heartbeat.tenant_key != tenant_key:
        raise DependencyConflict("heartbeat tenant conflicts with the presence projection")
    if heartbeat.work_item_id != work_item_id:
        raise DependencyConflict("heartbeat WorkItem conflicts with the execution attempt")
    if heartbeat.position_key != position_key:
        raise DependencyConflict("heartbeat position conflicts with the WorkItem assignment")
    return heartbeat


def heartbeat_freshness_state(
    heartbeat: OrganizationExecutionHeartbeat | None,
    *,
    as_of: datetime | None = None,
) -> str:
    if heartbeat is None:
        return HEARTBEAT_NOT_ESTABLISHED
    current = _as_utc(as_of or now_utc())
    return HEARTBEAT_FRESH if _as_utc(heartbeat.fresh_until) > current else HEARTBEAT_STALE


def current_execution_runtime_session(
    session: Session,
    *,
    tenant_key: str,
    work_item_id: UUID,
    execution_attempt_id: UUID,
    position_key: str,
) -> ExecutionRuntimeSessionLease | None:
    """Derive the latest fenced worker session from the durable heartbeat ledger.

    The initial ``attempt_started`` event is generation one. A later explicit claim is a
    takeover and its heartbeat sequence becomes the new fence token. Renewals never
    change the fence. Binding drift or a renewal written by a different worker fails
    closed rather than being interpreted as liveness.
    """

    work, attempt = _resolve_execution_state(
        session,
        tenant_key=tenant_key,
        work_item_id=work_item_id,
        execution_attempt_id=execution_attempt_id,
        position_key=position_key,
        require_running=False,
    )
    events = list(
        session.exec(
            select(OrganizationExecutionHeartbeat)
            .where(
                OrganizationExecutionHeartbeat.execution_attempt_id == execution_attempt_id,
                OrganizationExecutionHeartbeat.checkpoint.in_(
                    tuple(_RUNTIME_SESSION_EVENT_CHECKPOINTS)
                ),
            )
            .order_by(OrganizationExecutionHeartbeat.sequence)
        ).all()
    )
    if not events:
        return None

    claim: OrganizationExecutionHeartbeat | None = None
    latest: OrganizationExecutionHeartbeat | None = None
    for event in events:
        if (
            event.tenant_key != tenant_key
            or event.work_item_id != work.id
            or event.position_key != position_key
        ):
            raise DependencyConflict("runtime session heartbeat binding conflicts with canonical execution")
        if event.checkpoint in _RUNTIME_SESSION_CLAIM_CHECKPOINTS:
            claim = event
            latest = event
            continue
        if event.checkpoint == RUNTIME_SESSION_RENEWED:
            if claim is None:
                raise DependencyConflict("runtime session renewal exists without a durable claim")
            if event.writer != claim.writer:
                raise DependencyConflict("runtime session renewal writer conflicts with the current claim")
            latest = event

    if claim is None or latest is None:
        raise DependencyConflict("runtime session ledger does not contain a valid claim")
    return ExecutionRuntimeSessionLease(
        execution_attempt_id=attempt.id,
        work_item_id=work.id,
        position_key=position_key,
        execution_token=attempt.execution_token,
        fence_token=claim.sequence,
        writer=claim.writer,
        observed_at=latest.observed_at,
        fresh_until=latest.fresh_until,
        last_heartbeat_id=latest.id,
    )


def runtime_session_freshness_state(
    runtime_session: ExecutionRuntimeSessionLease | None,
    *,
    as_of: datetime | None = None,
) -> str:
    if runtime_session is None:
        return HEARTBEAT_NOT_ESTABLISHED
    current = _as_utc(as_of or now_utc())
    return HEARTBEAT_FRESH if _as_utc(runtime_session.fresh_until) > current else HEARTBEAT_STALE


def claim_execution_runtime_session(
    session: Session,
    *,
    tenant_key: str,
    work_item_id: UUID,
    execution_attempt_id: UUID,
    position_key: str,
    expected_execution_token: str,
    writer: str,
    observed_at: datetime | None = None,
    lease_seconds: int = DEFAULT_HEARTBEAT_LEASE_SECONDS,
) -> ExecutionRuntimeSessionLease:
    """Claim or take over one stale runtime session and return its fencing token.

    A fresh claim cannot be stolen. An expired claim may be taken over by appending a new
    durable claim event; the new event sequence is the new fence token. Callers must pass
    that token back on every renewal, so a stale worker cannot resume silently after a
    takeover.
    """

    _validate_lease_seconds(lease_seconds)
    if not writer.strip():
        raise ValueError("runtime session writer is required")
    work, attempt = _resolve_execution_state(
        session,
        tenant_key=tenant_key,
        work_item_id=work_item_id,
        execution_attempt_id=execution_attempt_id,
        position_key=position_key,
        expected_execution_token=expected_execution_token,
        require_running=True,
    )
    current_time = _as_utc(observed_at or now_utc())
    current = current_execution_runtime_session(
        session,
        tenant_key=tenant_key,
        work_item_id=work.id,
        execution_attempt_id=attempt.id,
        position_key=position_key,
    )
    if current is not None and _as_utc(current.fresh_until) > current_time:
        if current.writer == writer:
            return current
        raise DependencyConflict("runtime session is already held by a fresh fenced writer")

    heartbeat = stage_execution_heartbeat(
        session,
        tenant_key=tenant_key,
        work=work,
        attempt=attempt,
        position_key=position_key,
        checkpoint=RUNTIME_SESSION_CLAIMED,
        writer=writer,
        observed_at=current_time,
        lease_seconds=lease_seconds,
    )
    try:
        session.commit()
        session.refresh(heartbeat)
    except IntegrityError as exc:
        session.rollback()
        raced = current_execution_runtime_session(
            session,
            tenant_key=tenant_key,
            work_item_id=work.id,
            execution_attempt_id=attempt.id,
            position_key=position_key,
        )
        if (
            raced is not None
            and raced.writer == writer
            and _as_utc(raced.fresh_until) > current_time
        ):
            return raced
        raise DependencyConflict("runtime session claim lost a concurrent fencing race") from exc

    return ExecutionRuntimeSessionLease(
        execution_attempt_id=attempt.id,
        work_item_id=work.id,
        position_key=position_key,
        execution_token=attempt.execution_token,
        fence_token=heartbeat.sequence,
        writer=writer,
        observed_at=heartbeat.observed_at,
        fresh_until=heartbeat.fresh_until,
        last_heartbeat_id=heartbeat.id,
    )


def renew_execution_runtime_session(
    session: Session,
    *,
    tenant_key: str,
    work_item_id: UUID,
    execution_attempt_id: UUID,
    position_key: str,
    expected_execution_token: str,
    expected_fence_token: int,
    writer: str,
    observed_at: datetime | None = None,
    lease_seconds: int = DEFAULT_HEARTBEAT_LEASE_SECONDS,
) -> ExecutionRuntimeSessionLease:
    """Renew only the current, unexpired fenced runtime session generation."""

    _validate_lease_seconds(lease_seconds)
    if not isinstance(expected_fence_token, int) or isinstance(expected_fence_token, bool):
        raise ValueError("runtime session fence token must be an integer")
    if expected_fence_token < 1:
        raise ValueError("runtime session fence token must be positive")
    if not writer.strip():
        raise ValueError("runtime session writer is required")
    work, attempt = _resolve_execution_state(
        session,
        tenant_key=tenant_key,
        work_item_id=work_item_id,
        execution_attempt_id=execution_attempt_id,
        position_key=position_key,
        expected_execution_token=expected_execution_token,
        require_running=True,
    )
    current_time = _as_utc(observed_at or now_utc())
    current = current_execution_runtime_session(
        session,
        tenant_key=tenant_key,
        work_item_id=work.id,
        execution_attempt_id=attempt.id,
        position_key=position_key,
    )
    if current is None:
        raise InvalidTransition("runtime session must be claimed before it can be renewed")
    if current.fence_token != expected_fence_token:
        raise DependencyConflict("runtime session fence token is stale")
    if current.writer != writer:
        raise DependencyConflict("runtime session writer does not own the current fence")
    if _as_utc(current.fresh_until) <= current_time:
        raise InvalidTransition("expired runtime session must be reclaimed before renewal")

    heartbeat = stage_execution_heartbeat(
        session,
        tenant_key=tenant_key,
        work=work,
        attempt=attempt,
        position_key=position_key,
        checkpoint=RUNTIME_SESSION_RENEWED,
        writer=writer,
        observed_at=current_time,
        lease_seconds=lease_seconds,
    )
    try:
        session.commit()
        session.refresh(heartbeat)
    except IntegrityError as exc:
        session.rollback()
        raise DependencyConflict("runtime session renewal lost a concurrent heartbeat race") from exc

    return ExecutionRuntimeSessionLease(
        execution_attempt_id=attempt.id,
        work_item_id=work.id,
        position_key=position_key,
        execution_token=attempt.execution_token,
        fence_token=expected_fence_token,
        writer=writer,
        observed_at=heartbeat.observed_at,
        fresh_until=heartbeat.fresh_until,
        last_heartbeat_id=heartbeat.id,
    )
