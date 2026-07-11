from __future__ import annotations

from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import AgentRun, AgentRunStatus, AuditLog
from app.tasks.agent_tasks import run_agent_task

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
    assert any(log.action == "agent_run_status_changed" for log in db_session.exec(select(AuditLog).where(AuditLog.entity_id == str(run.id))).all())


def test_run_agent_task_fails_for_missing_run(db_session: Session) -> None:
    try:
        run_agent_task.run("00000000-0000-0000-0000-000000000000")
    except ValueError as exc:
        assert "not found" in str(exc)
