from __future__ import annotations

import json
from datetime import timedelta
from time import sleep

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
from app.services.organization_agent_runtime import (
    AgentRuntimeProfile,
    RuntimeBindingStale,
    RuntimeClass,
)
from app.services.organization_command import (
    DependencyConflict,
    InvalidTransition,
    OrganizationCommandContext,
)
from app.services.organization_execution_heartbeat import claim_execution_runtime_session
from app.services.organization_governance import ensure_foundation_positions
from app.services.organization_mobility_objective_runtime import (
    AUSTRIA_MOBILITY_PATHWAY_POSITION,
    create_austria_mobility_objective,
)
from app.services.organization_runtime_session_supervisor import ExecutionRuntimeSessionSupervisor
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


def _runtime(provider: str = "takeover-provider") -> AgentRuntimeProfile:
    return AgentRuntimeProfile(
        profile_key=f"{provider}-reasoning-v1",
        runtime_class=RuntimeClass.HOSTED_API,
        adapter_key=f"{provider}-adapter",
        provider_key=provider,
        model_key=f"{provider}-model",
        technical_capabilities=("reasoning", "structured_output"),
        available_tools=("browser",),
        independence_group=provider,
        profile_version=1,
        enabled=True,
    )


def _interrupted_attempt(
    db_session: Session,
    *,
    objective_key: str,
    actor: str = "worker-a",
):
    ensure_foundation_positions(db_session, actor="pytest", repair_contracts=True)
    context = _human_context()
    plan = create_austria_mobility_objective(
        db_session,
        context,
        objective_key=objective_key,
    )
    work = start_work_item(
        db_session,
        context,
        work_item_id=plan.pathway_work_item.id,
        reason="Start specialist work before simulating an interrupted K.1 worker.",
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
        actor=actor,
    )
    return context, plan, work, profile, attempt


def _expire_current_lease(db_session: Session, attempt_id) -> OrganizationExecutionHeartbeat:
    heartbeat = db_session.exec(
        select(OrganizationExecutionHeartbeat)
        .where(OrganizationExecutionHeartbeat.execution_attempt_id == attempt_id)
        .order_by(OrganizationExecutionHeartbeat.sequence.desc())
    ).first()
    assert heartbeat is not None
    expired_at = now_utc()
    heartbeat.observed_at = expired_at - timedelta(seconds=2)
    heartbeat.fresh_until = expired_at - timedelta(seconds=1)
    db_session.add(heartbeat)
    db_session.commit()
    db_session.refresh(heartbeat)
    return heartbeat


def test_takeover_resume_reexecutes_same_attempt_under_new_fence(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context, plan, work, profile, attempt = _interrupted_attempt(
        db_session,
        objective_key="at-rwr-shortage-2026-k1-takeover-resume",
    )
    _expire_current_lease(db_session, attempt.id)

    monkeypatch.setattr("app.services.controlled_agents.is_llm_enabled", lambda: False)
    real_run_controlled_agent = takeover_service.run_controlled_agent

    def delayed_controlled_agent(session, payload, existing_run=None):
        sleep(0.08)
        return real_run_controlled_agent(session, payload, existing_run)

    def fast_supervisor(**kwargs):
        return ExecutionRuntimeSessionSupervisor(
            **kwargs,
            lease_seconds=15,
            renewal_interval_seconds=0.01,
        )

    monkeypatch.setattr(takeover_service, "run_controlled_agent", delayed_controlled_agent)
    monkeypatch.setattr(takeover_service, "ExecutionRuntimeSessionSupervisor", fast_supervisor)

    result = takeover_service.resume_austria_specialist_work_with_takeover(
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

    assert result.execution_attempt_id == attempt.id
    assert result.attempt_number == 1
    attempts = list(
        db_session.exec(
            select(OrganizationExecutionAttempt).where(
                OrganizationExecutionAttempt.work_item_id == work.id
            )
        ).all()
    )
    assert len(attempts) == 1
    assert attempts[0].status == "completed"

    completed_work = db_session.get(OrganizationalWorkItem, work.id)
    assert completed_work is not None
    assert completed_work.status == "completed"
    assert completed_work.execution_attempts == 1

    heartbeats = list(
        db_session.exec(
            select(OrganizationExecutionHeartbeat)
            .where(OrganizationExecutionHeartbeat.execution_attempt_id == attempt.id)
            .order_by(OrganizationExecutionHeartbeat.sequence)
        ).all()
    )
    checkpoints = [heartbeat.checkpoint for heartbeat in heartbeats]
    assert checkpoints[0] == "attempt_started"
    assert checkpoints[1] == "runtime_session_claimed"
    assert checkpoints[-1] == "agent_completed"
    assert checkpoints.count("runtime_session_renewed") >= 1
    assert heartbeats[0].writer == "worker-a"
    assert all(heartbeat.writer == "worker-b" for heartbeat in heartbeats[1:])

    output = db_session.get(OrganizationalActionOutput, result.action_output_id)
    assert output is not None
    payload = json.loads(output.output_json)
    evidence = json.loads(output.evidence_json)
    assert payload["runtime_takeover_resume"] is True
    assert payload["runtime_previous_fence_token"] == 1
    assert payload["runtime_fence_token"] == 2
    assert payload["runtime_renewal_count"] >= 1
    assert payload["execution_attempt_id"] == str(attempt.id)
    runtime_evidence = [item for item in evidence if item.get("type") == "execution_runtime_session"]
    assert len(runtime_evidence) == 1
    assert runtime_evidence[0]["previous_fence_token"] == 1
    assert runtime_evidence[0]["fence_token"] == 2
    assert runtime_evidence[0]["takeover_resume"] is True
    assert runtime_evidence[0]["authority_effect"] is False


def test_takeover_resume_refuses_a_fresh_original_session(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context, plan, _work, profile, attempt = _interrupted_attempt(
        db_session,
        objective_key="at-rwr-shortage-2026-k1-takeover-fresh",
    )
    monkeypatch.setattr("app.services.controlled_agents.is_llm_enabled", lambda: False)

    with pytest.raises(InvalidTransition, match="requires an expired runtime session"):
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

    assert db_session.exec(select(OrganizationalActionOutput)).all() == []


def test_takeover_resume_rejects_blind_takeover_after_fence_advanced(
    db_session: Session,
) -> None:
    context, plan, work, profile, attempt = _interrupted_attempt(
        db_session,
        objective_key="at-rwr-shortage-2026-k1-takeover-stale-fence",
    )
    _expire_current_lease(db_session, attempt.id)

    claimed = claim_execution_runtime_session(
        db_session,
        tenant_key=work.tenant_key,
        work_item_id=work.id,
        execution_attempt_id=attempt.id,
        position_key=AUSTRIA_MOBILITY_PATHWAY_POSITION,
        expected_execution_token=attempt.execution_token,
        writer="worker-b",
    )
    assert claimed.fence_token == 2

    with pytest.raises(DependencyConflict, match="observed a stale previous fence token"):
        takeover_service.resume_austria_specialist_work_with_takeover(
            db_session,
            context,
            plan,
            position_key=AUSTRIA_MOBILITY_PATHWAY_POSITION,
            runtime_profile=profile,
            execution_attempt_id=attempt.id,
            expected_execution_token=attempt.execution_token,
            expected_previous_fence_token=1,
            actor="worker-c",
        )


def test_takeover_resume_rejects_context_or_runtime_binding_drift(
    db_session: Session,
) -> None:
    context, plan, _work, _profile, attempt = _interrupted_attempt(
        db_session,
        objective_key="at-rwr-shortage-2026-k1-takeover-runtime-drift",
    )
    _expire_current_lease(db_session, attempt.id)

    with pytest.raises(RuntimeBindingStale, match="binding changed"):
        takeover_service.resume_austria_specialist_work_with_takeover(
            db_session,
            context,
            plan,
            position_key=AUSTRIA_MOBILITY_PATHWAY_POSITION,
            runtime_profile=_runtime("different-provider"),
            execution_attempt_id=attempt.id,
            expected_execution_token=attempt.execution_token,
            expected_previous_fence_token=1,
            actor="worker-b",
        )

    heartbeats = list(
        db_session.exec(
            select(OrganizationExecutionHeartbeat).where(
                OrganizationExecutionHeartbeat.execution_attempt_id == attempt.id
            )
        ).all()
    )
    assert len(heartbeats) == 1


def test_takeover_resume_rejects_wrong_execution_token_before_claim(db_session: Session) -> None:
    context, plan, _work, profile, attempt = _interrupted_attempt(
        db_session,
        objective_key="at-rwr-shortage-2026-k1-takeover-token",
    )
    _expire_current_lease(db_session, attempt.id)

    with pytest.raises(DependencyConflict, match="execution token conflicts"):
        takeover_service.resume_austria_specialist_work_with_takeover(
            db_session,
            context,
            plan,
            position_key=AUSTRIA_MOBILITY_PATHWAY_POSITION,
            runtime_profile=profile,
            execution_attempt_id=attempt.id,
            expected_execution_token="f" * 64,
            expected_previous_fence_token=1,
            actor="worker-b",
        )
