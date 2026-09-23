from __future__ import annotations

import json
import traceback
from datetime import datetime, timezone
from uuid import UUID

from billiard.exceptions import SoftTimeLimitExceeded

from sqlmodel import Session, select

from app.core import db as db_module
from app.core.celery_app import celery_app
from app.models.domain import AgentRun, AgentRunStatus, AuditLog
from app.schemas import ControlledAgentRunRequest
from app.services.audit_log import record_audit
from app.services.controlled_agents import (
    DuplicatePendingControlledAgentOutput,
    run_controlled_agent,
)
from app.services.llm_client import (
    LLMProviderConfigurationError,
    LLMProviderResponseContractError,
    LLMProviderTransportError,
)


DEFAULT_STALE_AGENT_RUN_GRACE_SECONDS = 60


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

        except SoftTimeLimitExceeded:
            error = "AgentRun exceeded the worker soft time limit."
            record_audit(
                session,
                actor="worker",
                action="agent_run_runtime_timeout",
                entity_type="agent_run",
                entity_id=str(run.id),
                after_state={
                    "failure_class": "runtime_timeout",
                    "retryable": False,
                    "soft_time_limit_seconds": celery_app.conf.task_soft_time_limit,
                    "hard_time_limit_seconds": celery_app.conf.task_time_limit,
                },
                reason=error,
                source="phase_16_runtime_timeout",
            )
            session.commit()
            _transition_run(session, run, AgentRunStatus.failed, error=error)
            return {
                "run_id": str(run.id),
                "status": run.status,
                "error": error,
            }

        except Exception as exc:
            failure_class, retryable = _classify_failure(exc)
            record_audit(
                session,
                actor="worker",
                action="agent_run_failure_classified",
                entity_type="agent_run",
                entity_id=str(run.id),
                after_state={
                    "failure_class": failure_class,
                    "retryable": retryable,
                    "attempt": self.request.retries + 1,
                    "max_retries": self.max_retries,
                },
                reason=str(exc),
                source="phase_16_runtime_reliability",
            )
            session.commit()

            if retryable and self.request.retries < self.max_retries:
                _transition_run(session, run, AgentRunStatus.queued, error=str(exc))
                raise self.retry(exc=exc)

            _transition_run(session, run, AgentRunStatus.failed, error=traceback.format_exc())
            return {
                "run_id": str(run.id),
                "status": run.status,
                "error": str(exc),
                "traceback": traceback.format_exc(),
            }


@celery_app.task(name="app.tasks.agent_tasks.reconcile_stale_agent_runs")
def reconcile_stale_agent_runs_task(
    limit: int = 100,
    grace_seconds: int = DEFAULT_STALE_AGENT_RUN_GRACE_SECONDS,
) -> dict:
    """Fail closed AgentRuns stranded in running after the worker hard limit."""
    with Session(db_module.engine) as session:
        return reconcile_stale_agent_runs(
            session,
            limit=limit,
            grace_seconds=grace_seconds,
        )


def reconcile_stale_agent_runs(
    session: Session,
    *,
    limit: int = 100,
    grace_seconds: int = DEFAULT_STALE_AGENT_RUN_GRACE_SECONDS,
    now: datetime | None = None,
) -> dict:
    """Reconcile stale running state without guessing why the worker disappeared."""
    hard_limit_seconds = int(celery_app.conf.task_time_limit or 0)
    if hard_limit_seconds <= 0:
        return {
            "scanned": 0,
            "reconciled": 0,
            "skipped_missing_running_evidence": 0,
            "stale_after_seconds": None,
        }

    grace_seconds = max(0, int(grace_seconds))
    stale_after_seconds = hard_limit_seconds + grace_seconds
    observed_at = now or datetime.now(timezone.utc)
    if observed_at.tzinfo is None:
        observed_at = observed_at.replace(tzinfo=timezone.utc)

    runs = session.exec(
        select(AgentRun)
        .where(AgentRun.status == AgentRunStatus.running.value)
        .order_by(AgentRun.created_at.asc())
        .limit(max(1, min(int(limit), 500)))
    ).all()

    reconciled = 0
    skipped_missing_running_evidence = 0
    for run in runs:
        latest_status_log = session.exec(
            select(AuditLog)
            .where(AuditLog.entity_type == "agent_run")
            .where(AuditLog.entity_id == str(run.id))
            .where(AuditLog.action == "agent_run_status_changed")
            .order_by(AuditLog.created_at.desc())
        ).first()
        if latest_status_log is None:
            skipped_missing_running_evidence += 1
            continue

        try:
            latest_state = json.loads(latest_status_log.after_state_json or "{}")
        except json.JSONDecodeError:
            skipped_missing_running_evidence += 1
            continue
        if latest_state.get("status") != AgentRunStatus.running.value:
            skipped_missing_running_evidence += 1
            continue

        running_since = latest_status_log.created_at
        if running_since.tzinfo is None:
            running_since = running_since.replace(tzinfo=timezone.utc)
        observed_age_seconds = max(0, int((observed_at - running_since).total_seconds()))
        if observed_age_seconds <= stale_after_seconds:
            continue

        session.refresh(run)
        if run.status != AgentRunStatus.running.value:
            continue

        error = (
            "AgentRun remained running beyond the configured worker hard time limit plus grace; "
            "the underlying cause is not inferred."
        )
        record_audit(
            session,
            actor="worker",
            action="agent_run_stale_running_reconciled",
            entity_type="agent_run",
            entity_id=str(run.id),
            after_state={
                "failure_class": "runtime_stale_running",
                "retryable": False,
                "cause_inferred": False,
                "observed_age_seconds": observed_age_seconds,
                "hard_time_limit_seconds": hard_limit_seconds,
                "grace_seconds": grace_seconds,
                "stale_after_seconds": stale_after_seconds,
            },
            reason=error,
            source="phase_16_runtime_reconciliation",
        )
        session.commit()
        _transition_run(session, run, AgentRunStatus.failed, error=error)
        reconciled += 1

    return {
        "scanned": len(runs),
        "reconciled": reconciled,
        "skipped_missing_running_evidence": skipped_missing_running_evidence,
        "stale_after_seconds": stale_after_seconds,
    }


def _classify_failure(exc: Exception) -> tuple[str, bool]:
    """Classify before retry without pretending unknown failures are safe to repeat."""
    if isinstance(exc, SoftTimeLimitExceeded):
        return "runtime_timeout", False
    if isinstance(exc, LLMProviderTransportError):
        return "provider_transport", True
    if isinstance(exc, LLMProviderConfigurationError):
        return "provider_configuration", False
    if isinstance(exc, LLMProviderResponseContractError):
        return "provider_response_contract", False
    return "unknown", False


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
