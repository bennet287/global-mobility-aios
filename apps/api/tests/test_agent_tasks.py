from __future__ import annotations

from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import AgentRun, AgentRunStatus, AuditLog
from app.tasks.agent_tasks import run_agent_task

from billiard.exceptions import SoftTimeLimitExceeded

from app.services.llm_client import LLMProviderConfigurationError, LLMProviderTransportError
from .conftest import create_lead


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
