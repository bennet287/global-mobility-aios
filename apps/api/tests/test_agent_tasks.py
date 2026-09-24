from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import UUID

from celery import Task
from sqlmodel import Session, select

from app.models.domain import AgentRun, AgentRunStatus, AuditLog
from app.services.audit_log import record_audit
from app.services.agent_run_cancellation import (
    CANCEL_REQUESTED_STATUS,
    CANCELLED_STATUS,
)
from app.tasks.agent_tasks import (
    _transition_run,
    reconcile_stale_agent_runs,
    run_agent_task,
)

from billiard.exceptions import SoftTimeLimitExceeded

from app.services.llm_client import LLMProviderConfigurationError, LLMProviderTransportError
from .conftest import create_lead


def test_run_agent_task_transport_id_defaults_to_agent_run_id(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _apply_async(self, args=None, kwargs=None, task_id=None, **options):
        captured["args"] = args
        captured["task_id"] = task_id
        return SimpleNamespace(id=task_id)

    monkeypatch.setattr(Task, "apply_async", _apply_async)
    run_id = "00000000-0000-0000-0000-000000000123"

    result = run_agent_task.apply_async(args=[run_id])

    assert captured["task_id"] == run_id
    assert result.id == run_id


def test_run_agent_task_executes_queued_run(db_session: Session) -> None:
    lead = create_lead(db_session)
    run = AgentRun(
        lead_id=lead.id,
        agent_name="sales_summary_agent",
        task="Prepare sales summary.",
        status=AgentRunStatus.queued.value,
        input_json='{"agent_name": "sales_summary_agent", "task": "Prepare sales summary.", "context": {}, "actor": "pytest"}',
        output_json='{}',
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)

    result = run_agent_task.run(str(run.id))

    assert result["status"] == AgentRunStatus.pending_review.value
    db_session.refresh(run)
    assert run.status == AgentRunStatus.pending_review.value
    assert "summary" in run.output_json
    lifecycle_logs = db_session.exec(
        select(AuditLog)
        .where(AuditLog.entity_id == str(run.id))
        .where(AuditLog.action == "agent_run_status_changed")
        .order_by(AuditLog.created_at.asc())
    ).all()
    assert [log.source for log in lifecycle_logs] == [
        "celery_worker_v1.0",
        "phase_15_runtime_signals",
    ]
    assert '"status": "running"' in (lifecycle_logs[0].after_state_json or "")
    assert '"status": "pending_review"' in (lifecycle_logs[1].after_state_json or "")


def test_run_agent_task_does_not_resurrect_cancelled_queued_run(db_session: Session) -> None:
    lead = create_lead(db_session)
    run = AgentRun(
        lead_id=lead.id,
        agent_name="sales_summary_agent",
        task="Do not execute.",
        status=CANCELLED_STATUS,
        input_json="{}",
        output_json="{}",
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)

    result = run_agent_task.run(str(run.id))

    assert result["status"] == CANCELLED_STATUS
    assert result["skipped"] is True
    db_session.refresh(run)
    assert run.status == CANCELLED_STATUS
    assert db_session.exec(
        select(AuditLog)
        .where(AuditLog.entity_id == str(run.id))
        .where(AuditLog.action == "controlled_agent_run")
    ).first() is None


def test_run_agent_task_finalizes_cancel_request_before_worker_claim(db_session: Session) -> None:
    lead = create_lead(db_session)
    run = AgentRun(
        lead_id=lead.id,
        agent_name="sales_summary_agent",
        task="Do not claim.",
        status=CANCEL_REQUESTED_STATUS,
        input_json="{}",
        output_json="{}",
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)

    result = run_agent_task.run(str(run.id))

    assert result["status"] == CANCELLED_STATUS
    assert result["skipped"] is True
    db_session.refresh(run)
    assert run.status == CANCELLED_STATUS


def test_run_agent_task_suppresses_output_when_running_cancel_was_requested(
    db_session: Session,
    monkeypatch,
) -> None:
    lead = create_lead(db_session)
    run = AgentRun(
        lead_id=lead.id,
        agent_name="sales_summary_agent",
        task="Prepare sales summary.",
        status=AgentRunStatus.queued.value,
        input_json='{"agent_name": "sales_summary_agent", "task": "Prepare sales summary.", "context": {}, "actor": "pytest"}',
        output_json="{}",
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)

    def _complete_after_cancel(session, payload, existing_run=None, **kwargs):
        assert existing_run is not None
        record_audit(
            session,
            actor="admin",
            action="agent_run_cancel_requested",
            entity_type="agent_run",
            entity_id=str(existing_run.id),
            before_state={"status": AgentRunStatus.running.value},
            after_state={"status": CANCEL_REQUESTED_STATUS},
            reason="Stop this run.",
            source="phase_16_runtime_cancellation",
        )
        existing_run.status = AgentRunStatus.pending_review.value
        existing_run.output_json = '{"summary": "should be suppressed"}'
        session.add(existing_run)
        session.commit()
        return SimpleNamespace(
            run_id=existing_run.id,
            agent_name=existing_run.agent_name,
        )

    monkeypatch.setattr("app.tasks.agent_tasks.run_controlled_agent", _complete_after_cancel)

    result = run_agent_task.run(str(run.id))

    assert result["status"] == CANCELLED_STATUS
    assert result["cancellation_observed_after_execution"] is True
    assert result["rollback_claimed"] is False
    db_session.refresh(run)
    assert run.status == CANCELLED_STATUS


def test_run_agent_task_fails_for_missing_run(db_session: Session) -> None:
    try:
        run_agent_task.run("00000000-0000-0000-0000-000000000000")
    except ValueError as exc:
        assert "not found" in str(exc)


def test_failure_classifier_retries_transport_only() -> None:
    from app.tasks.agent_tasks import _classify_failure

    assert _classify_failure(LLMProviderTransportError("temporary")) == (
        "provider_transport",
        True,
    )
    assert _classify_failure(LLMProviderConfigurationError("bad config")) == (
        "provider_configuration",
        False,
    )
    assert _classify_failure(SoftTimeLimitExceeded()) == ("runtime_timeout", False)
    assert _classify_failure(RuntimeError("unknown")) == ("unknown", False)


def test_run_agent_task_records_soft_timeout_as_terminal_failure(
    db_session: Session, monkeypatch
) -> None:
    lead = create_lead(db_session)
    run = AgentRun(
        lead_id=lead.id,
        agent_name="sales_summary_agent",
        task="Prepare sales summary.",
        status=AgentRunStatus.queued.value,
        input_json='{"agent_name": "sales_summary_agent", "task": "Prepare sales summary.", "context": {}, "actor": "pytest"}',
        output_json='{}',
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)

    def _timeout(*args, **kwargs):
        raise SoftTimeLimitExceeded()

    monkeypatch.setattr("app.tasks.agent_tasks.run_controlled_agent", _timeout)

    result = run_agent_task.run(str(run.id))

    assert result["status"] == AgentRunStatus.failed.value
    assert "soft time limit" in result["error"]
    db_session.refresh(run)
    assert run.status == AgentRunStatus.failed.value

    timeout_logs = db_session.exec(
        select(AuditLog)
        .where(AuditLog.entity_id == str(run.id))
        .where(AuditLog.action == "agent_run_runtime_timeout")
    ).all()
    assert len(timeout_logs) == 1
    assert '"failure_class": "runtime_timeout"' in (timeout_logs[0].after_state_json or "")
    assert '"retryable": false' in (timeout_logs[0].after_state_json or "")

    lifecycle_logs = db_session.exec(
        select(AuditLog)
        .where(AuditLog.entity_id == str(run.id))
        .where(AuditLog.action == "agent_run_status_changed")
        .order_by(AuditLog.created_at.asc())
    ).all()
    assert [log.source for log in lifecycle_logs] == [
        "celery_worker_v1.0",
        "celery_worker_v1.0",
    ]
    assert '"status": "running"' in (lifecycle_logs[0].after_state_json or "")
    assert '"status": "failed"' in (lifecycle_logs[1].after_state_json or "")


def test_reconcile_stale_agent_runs_fails_only_overdue_running_run(
    db_session: Session,
) -> None:
    lead = create_lead(db_session)
    stale = AgentRun(
        lead_id=lead.id,
        agent_name="sales_summary_agent",
        task="Stale run.",
        status=AgentRunStatus.queued.value,
        input_json="{}",
        output_json="{}",
    )
    fresh = AgentRun(
        lead_id=lead.id,
        agent_name="sales_summary_agent",
        task="Fresh run.",
        status=AgentRunStatus.queued.value,
        input_json="{}",
        output_json="{}",
    )
    db_session.add(stale)
    db_session.add(fresh)
    db_session.commit()
    db_session.refresh(stale)
    db_session.refresh(fresh)

    _transition_run(db_session, stale, AgentRunStatus.running)
    _transition_run(db_session, fresh, AgentRunStatus.running)

    now = datetime.now(timezone.utc)
    stale_running_log = db_session.exec(
        select(AuditLog)
        .where(AuditLog.entity_id == str(stale.id))
        .where(AuditLog.action == "agent_run_status_changed")
        .order_by(AuditLog.created_at.desc())
    ).first()
    assert stale_running_log is not None
    stale_running_log.created_at = (now - timedelta(seconds=361)).replace(tzinfo=None)
    db_session.add(stale_running_log)
    db_session.commit()

    result = reconcile_stale_agent_runs(db_session, now=now)

    assert result == {
        "scanned": 2,
        "reconciled": 1,
        "skipped_missing_running_evidence": 0,
        "stale_after_seconds": 360,
    }
    db_session.refresh(stale)
    db_session.refresh(fresh)
    assert stale.status == AgentRunStatus.failed.value
    assert fresh.status == AgentRunStatus.running.value

    reconciliation_logs = db_session.exec(
        select(AuditLog)
        .where(AuditLog.entity_id == str(stale.id))
        .where(AuditLog.action == "agent_run_stale_running_reconciled")
    ).all()
    assert len(reconciliation_logs) == 1
    after_state = reconciliation_logs[0].after_state_json or ""
    assert '"failure_class": "runtime_stale_running"' in after_state
    assert '"retryable": false' in after_state
    assert '"cause_inferred": false' in after_state
    assert '"hard_time_limit_seconds": 300' in after_state
    assert '"grace_seconds": 60' in after_state


def test_reconcile_stale_agent_runs_finalizes_overdue_cancel_request(
    db_session: Session,
) -> None:
    lead = create_lead(db_session)
    run = AgentRun(
        lead_id=lead.id,
        agent_name="sales_summary_agent",
        task="Cancel stale run.",
        status=CANCEL_REQUESTED_STATUS,
        input_json="{}",
        output_json="{}",
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)

    now = datetime.now(timezone.utc)
    record_audit(
        db_session,
        actor="admin",
        action="agent_run_cancel_requested",
        entity_type="agent_run",
        entity_id=str(run.id),
        before_state={"status": AgentRunStatus.running.value},
        after_state={"status": CANCEL_REQUESTED_STATUS},
        reason="Cancel stale run.",
        source="phase_16_runtime_cancellation",
    )
    db_session.flush()
    cancel_log = db_session.exec(
        select(AuditLog)
        .where(AuditLog.entity_id == str(run.id))
        .where(AuditLog.action == "agent_run_cancel_requested")
    ).first()
    assert cancel_log is not None
    cancel_log.created_at = (now - timedelta(seconds=361)).replace(tzinfo=None)
    db_session.add(cancel_log)
    db_session.commit()

    result = reconcile_stale_agent_runs(db_session, now=now)

    assert result["reconciled"] == 1
    db_session.refresh(run)
    assert run.status == CANCELLED_STATUS


def test_reconcile_stale_agent_runs_requires_running_audit_evidence(
    db_session: Session,
) -> None:
    lead = create_lead(db_session)
    run = AgentRun(
        lead_id=lead.id,
        agent_name="sales_summary_agent",
        task="Missing evidence.",
        status=AgentRunStatus.running.value,
        input_json="{}",
        output_json="{}",
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)

    result = reconcile_stale_agent_runs(
        db_session,
        now=datetime.now(timezone.utc) + timedelta(hours=1),
    )

    assert result["reconciled"] == 0
    assert result["skipped_missing_running_evidence"] == 1
    db_session.refresh(run)
    assert run.status == AgentRunStatus.running.value
