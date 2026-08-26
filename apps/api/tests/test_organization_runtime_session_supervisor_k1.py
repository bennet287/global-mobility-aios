from __future__ import annotations

import json
from time import sleep
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlmodel import Session, select

import app.services.organization_mobility_objective_execution as execution_service
from app.models.domain import OrganizationActorType, OrganizationalActionOutput
from app.models.organization_presence import OrganizationExecutionHeartbeat
from app.services.organization_agent_runtime import AgentRuntimeProfile, RuntimeClass
from app.services.organization_command import OrganizationCommandContext
from app.services.organization_governance import ensure_foundation_positions
from app.services.organization_mobility_objective_runtime import (
    AUSTRIA_MOBILITY_PATHWAY_POSITION,
    create_austria_mobility_objective,
)
from app.services.organization_runtime_session_supervisor import ExecutionRuntimeSessionSupervisor


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
        profile_key="runtime-supervisor-provider-v1",
        runtime_class=RuntimeClass.HOSTED_API,
        adapter_key="runtime-supervisor-adapter",
        provider_key="runtime-supervisor-provider",
        model_key="runtime-supervisor-model",
        technical_capabilities=("reasoning", "structured_output"),
        available_tools=("browser",),
        independence_group="runtime-supervisor-provider",
        profile_version=1,
        enabled=True,
    )


def test_k1_renews_current_fence_only_while_controlled_agent_is_running(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ensure_foundation_positions(db_session, actor="pytest", repair_contracts=True)
    context = _human_context()
    plan = create_austria_mobility_objective(
        db_session,
        context,
        objective_key="at-rwr-shortage-2026-k1-runtime-supervisor",
    )

    def fast_supervisor(**kwargs):
        return ExecutionRuntimeSessionSupervisor(
            **kwargs,
            lease_seconds=15,
            renewal_interval_seconds=0.01,
        )

    def delayed_controlled_agent(session, payload, existing_run=None):
        del session, existing_run
        sleep(0.08)
        return SimpleNamespace(
            agent_name=payload.agent_name,
            run_id=uuid4(),
            output={
                "summary": "Delayed bounded internal analysis.",
                "confidence": 0.6,
                "blocked_actions": ["client_send"],
            },
        )

    monkeypatch.setattr(execution_service, "ExecutionRuntimeSessionSupervisor", fast_supervisor)
    monkeypatch.setattr(execution_service, "run_controlled_agent", delayed_controlled_agent)

    result = execution_service.execute_austria_specialist_work(
        db_session,
        context,
        plan,
        position_key=AUSTRIA_MOBILITY_PATHWAY_POSITION,
        runtime_profile=_runtime(),
    )

    heartbeats = list(
        db_session.exec(
            select(OrganizationExecutionHeartbeat)
            .where(
                OrganizationExecutionHeartbeat.execution_attempt_id
                == result.execution_attempt_id
            )
            .order_by(OrganizationExecutionHeartbeat.sequence)
        ).all()
    )
    checkpoints = [heartbeat.checkpoint for heartbeat in heartbeats]
    assert checkpoints[0] == "attempt_started"
    assert checkpoints[-1] == "agent_completed"
    assert checkpoints.count("runtime_session_renewed") >= 1
    assert all(heartbeat.writer == "organization-worker" for heartbeat in heartbeats)

    output = db_session.get(OrganizationalActionOutput, result.action_output_id)
    assert output is not None
    payload = json.loads(output.output_json)
    evidence = json.loads(output.evidence_json)
    assert payload["runtime_fence_token"] == 1
    assert payload["runtime_renewal_count"] >= 1
    runtime_evidence = [item for item in evidence if item.get("type") == "execution_runtime_session"]
    assert len(runtime_evidence) == 1
    assert runtime_evidence[0]["fence_token"] == 1
    assert runtime_evidence[0]["renewal_count"] >= 1
    assert runtime_evidence[0]["authority_effect"] is False
