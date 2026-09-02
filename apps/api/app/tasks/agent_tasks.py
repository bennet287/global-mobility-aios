from __future__ import annotations

import json
import traceback
from uuid import UUID

from sqlmodel import Session

from app.core import db as db_module
from app.core.celery_app import celery_app
from app.models.domain import AgentRun, AgentRunStatus
from app.schemas import ControlledAgentRunRequest
from app.services.audit_log import record_audit
from app.services.controlled_agents import (
    DuplicatePendingControlledAgentOutput,
    run_controlled_agent,
)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=30)
def run_agent_task(self, agent_run_id: str) -> dict:
    """Celery task that executes a single AgentRun in the background."""
    run_id = UUID(agent_run_id)

    with Session(db_module.engine) as session:
        run = session.get(AgentRun, run_id)
        if run is None:
            raise ValueError(f"AgentRun {agent_run_id} not found")

        _transition_run(session, run, AgentRunStatus.running)

        try:
            input_data = json.loads(run.input_json or "{}")
            payload = ControlledAgentRunRequest(
                agent_name=input_data.get("agent_name", run.agent_name),
                task=input_data.get("task", run.task),
                lead_id=run.lead_id,
                workflow_run_id=run.workflow_run_id,
                context=input_data.get("context", {}),
                actor=input_data.get("actor", "system"),
            )

            response = run_controlled_agent(session, payload, existing_run=run)
            return {
                "run_id": str(response.run_id),
                "agent_name": response.agent_name,
                "status": run.status,
            }

        except DuplicatePendingControlledAgentOutput as exc:
            _transition_run(session, run, AgentRunStatus.failed, error=str(exc))
            return {"run_id": str(run.id), "status": run.status, "error": str(exc)}

        except Exception as exc:
            if self.request.retries < self.max_retries:
                _transition_run(session, run, AgentRunStatus.queued, error=str(exc))
                raise self.retry(exc=exc)

            _transition_run(session, run, AgentRunStatus.failed, error=traceback.format_exc())
            return {
                "run_id": str(run.id),
                "status": run.status,
                "error": str(exc),
                "traceback": traceback.format_exc(),
            }


def _transition_run(
    session: Session,
    run: AgentRun,
    status: AgentRunStatus,
    error: str | None = None,
) -> None:
    run.status = status.value
    output = json.loads(run.output_json or "{}")
    output["_status_history"] = output.get("_status_history", []) + [
        {"status": status.value, "error": error}
    ]
    if error:
        output["_last_error"] = error
    run.output_json = json.dumps(output, default=str, sort_keys=True)
    session.add(run)
    session.flush()

    record_audit(
        session,
        actor="worker",
        action="agent_run_status_changed",
        entity_type="agent_run",
        entity_id=str(run.id),
        after_state={
            "agent_name": run.agent_name,
            "status": status.value,
            "lead_id": str(run.lead_id) if run.lead_id else None,
            "error": error,
        },
        reason=f"Agent run transitioned to {status.value} by background worker.",
        source="celery_worker_v1.0",
    )
    session.commit()
