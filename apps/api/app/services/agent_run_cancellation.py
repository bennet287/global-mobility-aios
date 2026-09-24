from __future__ import annotations

import json
from uuid import UUID

from sqlmodel import Session, select

from app.core.celery_app import celery_app
from app.models.domain import AgentRun, AgentRunStatus, AuditLog
from app.services.audit_log import record_audit


CANCEL_REQUESTED_STATUS = AgentRunStatus.cancel_requested.value
CANCELLED_STATUS = AgentRunStatus.cancelled.value
CANCELLABLE_STATUSES = {
    AgentRunStatus.queued.value,
    AgentRunStatus.running.value,
}
CANCELLATION_AUDIT_ACTIONS = {
    "agent_run_cancel_requested",
    "agent_run_cancelled",
}


class AgentRunCancellationNotFound(LookupError):
    """Raised when the requested AgentRun does not exist."""


class AgentRunCancellationConflict(ValueError):
    """Raised when cancellation is requested outside the cancellable runtime states."""


def _append_status_history(run: AgentRun, *, status: str, reason: str) -> None:
    try:
        output = json.loads(run.output_json or "{}")
    except json.JSONDecodeError:
        output = {}
    if not isinstance(output, dict):
        output = {}
    output["_status_history"] = output.get("_status_history", []) + [
        {
            "status": status,
            "reason": reason,
            "source": "phase_16_runtime_cancellation",
        }
    ]
    run.output_json = json.dumps(output, default=str, sort_keys=True)


def request_agent_run_cancellation(
    session: Session,
    *,
    run_id: UUID,
    actor: str,
    reason: str,
) -> AgentRun:
    """Serialize and persist cancellation intent before transport revoke is attempted."""
    clean_actor = actor.strip()
    clean_reason = reason.strip()
    if not clean_actor:
        raise ValueError("cancellation actor is required")
    if not clean_reason:
        raise ValueError("cancellation reason is required")

    # The worker claim takes the same row lock. Whichever command wins observes and
    # commits canonical AgentRun truth before the other can decide its transition.
    run = session.exec(
        select(AgentRun)
        .where(AgentRun.id == run_id)
        .with_for_update()
    ).one_or_none()
    if run is None:
        raise AgentRunCancellationNotFound(f"AgentRun {run_id} was not found")
    if run.status not in CANCELLABLE_STATUSES:
        raise AgentRunCancellationConflict(
            f"AgentRun {run.id} cannot be cancelled from status {run.status}"
        )

    before_status = run.status
    target_status = (
        CANCELLED_STATUS
        if before_status == AgentRunStatus.queued.value
        else CANCEL_REQUESTED_STATUS
    )
    run.status = target_status
    _append_status_history(run, status=target_status, reason=clean_reason)
    session.add(run)
    session.flush()

    action = (
        "agent_run_cancelled"
        if target_status == CANCELLED_STATUS
        else "agent_run_cancel_requested"
    )
    record_audit(
        session,
        actor=clean_actor,
        action=action,
        entity_type="agent_run",
        entity_id=str(run.id),
        before_state={"status": before_status},
        after_state={
            "status": target_status,
            "transport_task_id": str(run.id),
            "transport_identity": "agent_run_id",
            "transport_revoke_requested": False,
            "worker_termination_requested": False,
            "rollback_claimed": False,
        },
        reason=clean_reason,
        source="phase_16_runtime_cancellation",
        commit=False,
    )
    session.flush()
    return run


def request_agent_run_transport_revoke(
    session: Session,
    *,
    run: AgentRun,
    actor: str,
) -> tuple[bool, str | None]:
    """Best-effort non-terminating revoke after cancellation truth has been committed."""
    try:
        celery_app.control.revoke(str(run.id), terminate=False)
    except Exception as exc:  # transport failure must not roll back canonical DB truth
        error = f"{type(exc).__name__}: {exc}"
        record_audit(
            session,
            actor=actor,
            action="agent_run_transport_revoke_failed",
            entity_type="agent_run",
            entity_id=str(run.id),
            after_state={
                "transport_task_id": str(run.id),
                "terminate": False,
                "error": error,
            },
            reason="Cancellation remained canonical, but the Celery revoke broadcast failed.",
            source="phase_16_runtime_cancellation",
        )
        session.commit()
        return False, error

    record_audit(
        session,
        actor=actor,
        action="agent_run_transport_revoke_requested",
        entity_type="agent_run",
        entity_id=str(run.id),
        after_state={
            "transport_task_id": str(run.id),
            "terminate": False,
            "worker_termination_requested": False,
        },
        reason="Requested Celery to skip this task if it has not started; active work is not process-killed.",
        source="phase_16_runtime_cancellation",
    )
    session.commit()
    return True, None


def agent_run_cancellation_requested(session: Session, run_id: UUID) -> bool:
    """Audit evidence remains durable even if another transition rewrites row status."""
    return (
        session.exec(
            select(AuditLog.id)
            .where(AuditLog.entity_type == "agent_run")
            .where(AuditLog.entity_id == str(run_id))
            .where(AuditLog.action.in_(CANCELLATION_AUDIT_ACTIONS))
            .limit(1)
        ).first()
        is not None
    )
