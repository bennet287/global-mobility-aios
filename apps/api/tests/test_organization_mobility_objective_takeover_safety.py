from __future__ import annotations

from datetime import timedelta

import pytest
from sqlmodel import Session, select

import app.services.organization_mobility_objective_execution as execution_service
import app.services.organization_mobility_objective_takeover as takeover_service
from app.models.domain import (
    OrganizationActorType,
    OrganizationExecutionAttempt,
    OrganizationalActionOutput,
    OrganizationalWorkItem,
    now_utc,
)
from app.models.organization_presence import OrganizationExecutionHeartbeat
from app.services.organization_agent_runtime import AgentRuntimeProfile, RuntimeBindingStale, RuntimeClass
from app.services.organization_command import OrganizationCommandContext
from app.services.organization_governance import ensure_foundation_positions
from app.services.organization_mobility_objective_runtime import (
    AUSTRIA_MOBILITY_PATHWAY_POSITION,
    create_austria_mobility_objective,
)
from app.services.organization_work import start_work_item


def _human_context() -> OrganizationCommandContext:
    return OrganizationCommandContext(
        tenant_key="default",
        actor_id="human-owner",
        actor_type=OrganizationActorType.human,
        authenticated_user_id="human-owner",
        role="admin",
        department="Global Mobility Operations",
        position_key="board",
        authority_level="L4",
    )


def _runtime() -> AgentRuntimeProfile:
    return AgentRuntimeProfile(
        profile_key="takeover-safety-v1",
        runtime_class=RuntimeClass.HOSTED_API,
        adapter_key="takeover-safety-adapter",
        provider_key="takeover-safety-provider",
        model_key="takeover-safety-model",
        technical_capabilities=("reasoning", "structured_output"),
        available_tools=("browser",),
        independence_group="takeover-safety",
        profile_version=1,
        enabled=True,
    )


def _interrupted_attempt(db_session: Session, *, objective_key: str):
    ensure_foundation_positions(db_session, actor="pytest", repair_contracts=True)
    context = _human_context()
    plan = create_austria_mobility_objective(db_session, context, objective_key=objective_key)
    work = start_work_item(
        db_session,
        context,
        work_item_id=plan.pathway_work_item.id,
        reason="Start specialist work before takeover safety simulation.",
    )
    profile = _runtime()
    binding = execution_service._current_binding(
        db_session,
        work=work,
        position_key=AUSTRIA_MOBILITY_PATHWAY_POSITION,
        profile=profile,
        expected_binding=None,
    )
    attempt = execution_service._start_attempt(
        db_session,
        work=work,
        binding=binding,
        actor="worker-a",
    )
    heartbeat = db_session.exec(
        select(OrganizationExecutionHeartbeat)
        .where(OrganizationExecutionHeartbeat.execution_attempt_id == attempt.id)
        .order_by(OrganizationExecutionHeartbeat.sequence.desc())
    ).first()
    assert heartbeat is not None
    expired_at = now_utc()
    heartbeat.observed_at = expired_at - timedelta(seconds=2)
    heartbeat.fresh_until = expired_at - timedelta(seconds=1)
    db_session.add(heartbeat)
    db_session.commit()
    return context, plan, work, profile, attempt


def test_takeover_refuses_workitem_mutation_after_attempt_start(db_session: Session) -> None:
    context, plan, work, profile, attempt = _interrupted_attempt(
        db_session,
        objective_key="at-rwr-shortage-2026-k1-takeover-work-drift",
    )
    current = db_session.get(OrganizationalWorkItem, work.id)
    assert current is not None
    current.objective = f"{current.objective} changed after interruption"
    current.updated_at = now_utc()
    db_session.add(current)
    db_session.commit()

    with pytest.raises(RuntimeBindingStale, match="WorkItem changed"):
        takeover_service.resume_austria_specialist_work_with_takeover(
            db_session,
            context,
            plan,
            position_key=AUSTRIA_MOBILITY_PATHWAY_POSITION,
            runtime_profile=profile,
            execution_attempt_id=attempt.id,
            expected_execution_token=attempt.execution_token,
            expected_previous_fence_token=1,
            actor="worker-b",
        )

    heartbeats = db_session.exec(
        select(OrganizationExecutionHeartbeat).where(
            OrganizationExecutionHeartbeat.execution_attempt_id == attempt.id
        )
    ).all()
    assert len(heartbeats) == 1


def test_takeover_worker_failure_fails_same_attempt_without_output(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context, plan, work, profile, attempt = _interrupted_attempt(
        db_session,
        objective_key="at-rwr-shortage-2026-k1-takeover-failure",
    )

    def fail_controlled_agent(*args, **kwargs):
        raise RuntimeError("simulated takeover worker failure")

    monkeypatch.setattr(takeover_service, "run_controlled_agent", fail_controlled_agent)

    with pytest.raises(RuntimeError, match="simulated takeover worker failure"):
        takeover_service.resume_austria_specialist_work_with_takeover(
            db_session,
            context,
            plan,
            position_key=AUSTRIA_MOBILITY_PATHWAY_POSITION,
            runtime_profile=profile,
            execution_attempt_id=attempt.id,
            expected_execution_token=attempt.execution_token,
            expected_previous_fence_token=1,
            actor="worker-b",
        )

    failed_attempt = db_session.get(OrganizationExecutionAttempt, attempt.id)
    failed_work = db_session.get(OrganizationalWorkItem, work.id)
    assert failed_attempt is not None and failed_attempt.status == "failed"
    assert "simulated takeover worker failure" in (failed_attempt.error or "")
    assert failed_work is not None and failed_work.status == "running"
    assert failed_work.execution_started_at is None
    assert "simulated takeover worker failure" in (failed_work.last_error or "")
    assert db_session.exec(select(OrganizationalActionOutput)).all() == []
