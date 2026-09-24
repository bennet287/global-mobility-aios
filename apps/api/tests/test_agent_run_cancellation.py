from __future__ import annotations

from billiard.exceptions import SoftTimeLimitExceeded
from sqlmodel import Session, select

from app.models.domain import AgentRun, AgentRunStatus, AuditLog
from app.schemas import AgentRunDetailResponse, AgentRunRead
from app.services.agent_run_cancellation import (
    CANCEL_REQUESTED_STATUS,
    CANCELLED_STATUS,
    AgentRunCancellationConflict,
    AgentRunCancellationNotFound,
    request_agent_run_cancellation,
    request_agent_run_transport_revoke,
)
from app.services.audit_log import record_audit
from app.tasks.agent_tasks import run_agent_task
from .conftest import create_lead


def _run(db_session: Session, *, status: str) -> AgentRun:
    lead = create_lead(db_session)
    run = AgentRun(
        lead_id=lead.id,
        agent_name="sales_summary_agent",
        task="Cancellation test.",
        status=status,
        input_json="{}",
        output_json="{}",
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)
    return run


def test_queued_cancel_is_immediately_terminal_and_revoke_is_non_terminating(
    db_session: Session,
    monkeypatch,
) -> None:
    run = _run(db_session, status=AgentRunStatus.queued.value)
    calls: list[tuple[str, bool]] = []

    def _revoke(task_id: str, terminate: bool = False):
        calls.append((task_id, terminate))

    monkeypatch.setattr(
        "app.services.agent_run_cancellation.celery_app.control.revoke",
        _revoke,
    )

    run = request_agent_run_cancellation(
        db_session,
        run_id=run.id,
        actor="admin",
        reason="Operator stopped queued work.",
    )
    db_session.commit()
    db_session.refresh(run)
    revoke_requested, revoke_error = request_agent_run_transport_revoke(
        db_session,
        run=run,
        actor="admin",
    )

    assert run.status == CANCELLED_STATUS
    assert revoke_requested is True
    assert revoke_error is None
    assert calls == [(str(run.id), False)]

    cancellation_log = db_session.exec(
        select(AuditLog)
        .where(AuditLog.entity_id == str(run.id))
        .where(AuditLog.action == "agent_run_cancelled")
    ).first()
    assert cancellation_log is not None
    assert '"worker_termination_requested": false' in (cancellation_log.after_state_json or "")
    assert '"rollback_claimed": false' in (cancellation_log.after_state_json or "")


def test_running_cancel_records_request_without_claiming_termination(
    db_session: Session,
    monkeypatch,
) -> None:
    run = _run(db_session, status=AgentRunStatus.running.value)
    calls: list[tuple[str, bool]] = []

    def _revoke(task_id: str, terminate: bool = False):
        calls.append((task_id, terminate))

    monkeypatch.setattr(
        "app.services.agent_run_cancellation.celery_app.control.revoke",
        _revoke,
    )

    run = request_agent_run_cancellation(
        db_session,
        run_id=run.id,
        actor="admin",
        reason="Operator stopped running work.",
    )
    db_session.commit()
    db_session.refresh(run)
    revoke_requested, _ = request_agent_run_transport_revoke(
        db_session,
        run=run,
        actor="admin",
    )

    assert run.status == CANCEL_REQUESTED_STATUS
    assert revoke_requested is True
    assert calls == [(str(run.id), False)]

    request_log = db_session.exec(
        select(AuditLog)
        .where(AuditLog.entity_id == str(run.id))
        .where(AuditLog.action == "agent_run_cancel_requested")
    ).first()
    assert request_log is not None
    assert '"worker_termination_requested": false' in (request_log.after_state_json or "")
    assert '"rollback_claimed": false' in (request_log.after_state_json or "")


def test_cancellation_states_remain_valid_in_shared_agent_run_read_contract(
    db_session: Session,
) -> None:
    for status in (
        AgentRunStatus.cancel_requested.value,
        AgentRunStatus.cancelled.value,
    ):
        run = _run(db_session, status=status)
        shared_read = AgentRunRead.model_validate(run, from_attributes=True)
        detail = AgentRunDetailResponse(
            run=shared_read,
            audit_history=[],
            latest_review_note=None,
        )

        assert detail.run.status.value == status


def test_terminal_run_cannot_be_cancelled(db_session: Session) -> None:
    run = _run(db_session, status=AgentRunStatus.pending_review.value)

    try:
        request_agent_run_cancellation(
            db_session,
            run_id=run.id,
            actor="admin",
            reason="Too late.",
        )
    except AgentRunCancellationConflict as exc:
        assert "cannot be cancelled" in str(exc)
    else:
        raise AssertionError("Expected AgentRunCancellationConflict")


def test_missing_run_cannot_be_cancelled(db_session: Session) -> None:
    from uuid import UUID

    try:
        request_agent_run_cancellation(
            db_session,
            run_id=UUID("00000000-0000-0000-0000-000000000000"),
            actor="admin",
            reason="Missing run.",
        )
    except AgentRunCancellationNotFound as exc:
        assert "was not found" in str(exc)
    else:
        raise AssertionError("Expected AgentRunCancellationNotFound")


def test_transport_revoke_failure_does_not_undo_canonical_cancellation(
    db_session: Session,
    monkeypatch,
) -> None:
    run = _run(db_session, status=AgentRunStatus.queued.value)

    run = request_agent_run_cancellation(
        db_session,
        run_id=run.id,
        actor="admin",
        reason="Operator stopped queued work.",
    )
    db_session.commit()

    def _revoke(*args, **kwargs):
        raise RuntimeError("broker unavailable")

    monkeypatch.setattr(
        "app.services.agent_run_cancellation.celery_app.control.revoke",
        _revoke,
    )

    revoke_requested, revoke_error = request_agent_run_transport_revoke(
        db_session,
        run=run,
        actor="admin",
    )

    db_session.refresh(run)
    assert run.status == CANCELLED_STATUS
    assert revoke_requested is False
    assert "broker unavailable" in (revoke_error or "")
    failure_log = db_session.exec(
        select(AuditLog)
        .where(AuditLog.entity_id == str(run.id))
        .where(AuditLog.action == "agent_run_transport_revoke_failed")
    ).first()
    assert failure_log is not None


def test_running_cancellation_wins_at_soft_timeout_boundary(
    db_session: Session,
    monkeypatch,
) -> None:
    lead = create_lead(db_session)
    run = AgentRun(
        lead_id=lead.id,
        agent_name="sales_summary_agent",
        task="Cancel before timeout classification.",
        status=AgentRunStatus.queued.value,
        input_json='{"agent_name": "sales_summary_agent", "task": "Cancel before timeout classification.", "context": {}, "actor": "pytest"}',
        output_json="{}",
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)

    def _cancel_then_timeout(session, payload, existing_run=None):
        assert existing_run is not None
        record_audit(
            session,
            actor="admin",
            action="agent_run_cancel_requested",
            entity_type="agent_run",
            entity_id=str(existing_run.id),
            before_state={"status": AgentRunStatus.running.value},
            after_state={"status": CANCEL_REQUESTED_STATUS},
            reason="Operator cancelled before the timeout boundary.",
            source="phase_16_runtime_cancellation",
        )
        session.commit()
        raise SoftTimeLimitExceeded()

    monkeypatch.setattr(
        "app.tasks.agent_tasks.run_controlled_agent",
        _cancel_then_timeout,
    )

    result = run_agent_task.run(str(run.id))

    assert result["status"] == CANCELLED_STATUS
    assert result["cancellation_observed_at_timeout"] is True
    assert result["rollback_claimed"] is False
    db_session.refresh(run)
    assert run.status == CANCELLED_STATUS
    timeout_log = db_session.exec(
        select(AuditLog)
        .where(AuditLog.entity_id == str(run.id))
        .where(AuditLog.action == "agent_run_runtime_timeout")
    ).first()
    assert timeout_log is None
