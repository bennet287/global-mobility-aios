from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

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
_ALLOWED_CHECKPOINTS = frozenset({"attempt_started", "agent_completed"})


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
    """

    _validate_lease_seconds(lease_seconds)
    if checkpoint not in _ALLOWED_CHECKPOINTS:
        raise ValueError("unsupported execution heartbeat checkpoint")
    if work.tenant_key != tenant_key:
        raise DependencyConflict("heartbeat WorkItem crosses the requested tenant boundary")
    if work.assigned_position_key != position_key:
        raise DependencyConflict("heartbeat position does not match the WorkItem assignment")
    if attempt.work_item_id != work.id:
        raise DependencyConflict("heartbeat execution attempt does not belong to the WorkItem")
    if work.status != "running" or attempt.status != "running":
        raise InvalidTransition("heartbeat checkpoints require running WorkItem and execution attempt")

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

    work = session.exec(
        select(OrganizationalWorkItem).where(
            OrganizationalWorkItem.id == work_item_id,
            OrganizationalWorkItem.tenant_key == tenant_key,
        )
    ).first()
    if work is None:
        raise DependencyConflict("heartbeat WorkItem was not found for the tenant")
    attempt = session.get(OrganizationExecutionAttempt, execution_attempt_id)
    if attempt is None:
        raise DependencyConflict("heartbeat execution attempt was not found")

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
        .where(
            OrganizationExecutionHeartbeat.tenant_key == tenant_key,
            OrganizationExecutionHeartbeat.work_item_id == work_item_id,
            OrganizationExecutionHeartbeat.execution_attempt_id == execution_attempt_id,
        )
        .order_by(
            OrganizationExecutionHeartbeat.sequence.desc(),
            OrganizationExecutionHeartbeat.observed_at.desc(),
        )
    ).first()
    if heartbeat is None:
        return None
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
