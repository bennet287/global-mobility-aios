from __future__ import annotations

import pytest
from sqlmodel import Session, select

from app.models.domain import OrganizationActorType
from app.models.organization_presence import OrganizationExecutionHeartbeat
from app.services.organization_agent_runtime import AgentRuntimeProfile, RuntimeClass
from app.services.organization_command import OrganizationCommandContext
from app.services.organization_governance import ensure_foundation_positions
from app.services.organization_mobility_objective_execution import execute_austria_specialist_work
from app.services.organization_mobility_objective_runtime import (
    AUSTRIA_MOBILITY_PATHWAY_POSITION,
    create_austria_mobility_objective,
)


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
        profile_key="heartbeat-provider-reasoning-v1",
        runtime_class=RuntimeClass.HOSTED_API,
        adapter_key="heartbeat-provider-adapter",
        provider_key="heartbeat-provider",
        model_key="heartbeat-model",
        technical_capabilities=("reasoning", "structured_output"),
        available_tools=("browser", "shell"),
        independence_group="heartbeat-provider",
        profile_version=1,
        enabled=True,
    )


def test_k1_records_start_and_agent_completed_heartbeat_checkpoints(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ensure_foundation_positions(db_session, actor="pytest", repair_contracts=True)
    monkeypatch.setattr("app.services.controlled_agents.is_llm_enabled", lambda: False)
    context = _human_context()
    plan = create_austria_mobility_objective(
        db_session,
        context,
        objective_key="at-rwr-shortage-2026-heartbeat-checkpoints",
    )

    result = execute_austria_specialist_work(
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
    assert [heartbeat.sequence for heartbeat in heartbeats] == [1, 2]
    assert [heartbeat.checkpoint for heartbeat in heartbeats] == [
        "attempt_started",
        "agent_completed",
    ]
    assert all(heartbeat.tenant_key == "default" for heartbeat in heartbeats)
    assert all(
        heartbeat.position_key == AUSTRIA_MOBILITY_PATHWAY_POSITION
        for heartbeat in heartbeats
    )
    assert all(heartbeat.work_item_id == plan.pathway_work_item.id for heartbeat in heartbeats)
    assert all(heartbeat.fresh_until > heartbeat.observed_at for heartbeat in heartbeats)
