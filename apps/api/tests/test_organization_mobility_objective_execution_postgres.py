from __future__ import annotations

import os

import pytest
from sqlmodel import Session

from app.models.domain import OrganizationActorType
from app.services.organization_agent_runtime import AgentRuntimeProfile, RuntimeClass
from app.services.organization_command import OrganizationCommandContext
from app.services.organization_governance import ensure_foundation_positions
from app.services.organization_mobility_objective_execution import execute_austria_specialists
from app.services.organization_mobility_objective_runtime import (
    AUSTRIA_MOBILITY_PATHWAY_POSITION,
    AUSTRIA_MOBILITY_REGULATORY_POSITION,
    AustriaMobilityObjectivePlan,
    austria_objective_readiness,
    create_austria_mobility_objective,
)


pytestmark = pytest.mark.skipif(
    not os.getenv("GMAI_TEST_DATABASE_URL", "").startswith("postgresql"),
    reason="real PostgreSQL contract requires GMAI_TEST_DATABASE_URL",
)


def _human_context() -> OrganizationCommandContext:
    return OrganizationCommandContext(
        tenant_key="default",
        actor_id="postgres-k1-owner",
        actor_type=OrganizationActorType.human,
        authenticated_user_id="postgres-k1-owner",
        role="admin",
        department="Global Mobility Operations",
        position_key="board",
        authority_level="L4",
    )


def _runtime(provider: str) -> AgentRuntimeProfile:
    return AgentRuntimeProfile(
        profile_key=f"{provider}-postgres-k1-v1",
        runtime_class=RuntimeClass.HOSTED_API,
        adapter_key=f"{provider}-adapter",
        provider_key=provider,
        model_key=f"{provider}-model",
        technical_capabilities=("reasoning", "structured_output"),
        available_tools=("browser", "shell"),
        independence_group=provider,
        profile_version=1,
        enabled=True,
    )


def test_postgres_k1_specialist_outputs_survive_cross_session_exact_replay(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("app.services.controlled_agents.is_llm_enabled", lambda: False)
    ensure_foundation_positions(db_session, actor="postgres-k1", repair_contracts=True)
    context = _human_context()
    profiles = {
        AUSTRIA_MOBILITY_PATHWAY_POSITION: _runtime("provider-a"),
        AUSTRIA_MOBILITY_REGULATORY_POSITION: _runtime("provider-b"),
    }
    plan = create_austria_mobility_objective(
        db_session,
        context,
        objective_key="at-rwr-shortage-2026-k1-postgres",
    )

    first = execute_austria_specialists(
        db_session,
        context,
        plan,
        runtime_profiles=profiles,
    )
    assert all(item.replayed is False for item in first)
    assert austria_objective_readiness(
        db_session,
        tenant_key="default",
        root_work_item_id=plan.root_work_item.id,
    ).ready_for_owner_synthesis is True

    first_output_ids = {item.action_output_id for item in first}
    first_run_ids = {item.agent_run_id for item in first}
    first_attempt_ids = {item.execution_attempt_id for item in first}
    engine = db_session.get_bind()

    with Session(engine) as replay_session:
        replay_plan = AustriaMobilityObjectivePlan(
            root_work_item=replay_session.get(type(plan.root_work_item), plan.root_work_item.id),
            pathway_work_item=replay_session.get(type(plan.pathway_work_item), plan.pathway_work_item.id),
            regulatory_work_item=replay_session.get(type(plan.regulatory_work_item), plan.regulatory_work_item.id),
        )
        assert replay_plan.root_work_item is not None
        assert replay_plan.pathway_work_item is not None
        assert replay_plan.regulatory_work_item is not None
        replay = execute_austria_specialists(
            replay_session,
            context,
            replay_plan,
            runtime_profiles=profiles,
        )
        assert all(item.replayed is True for item in replay)
        assert {item.action_output_id for item in replay} == first_output_ids
        assert {item.agent_run_id for item in replay} == first_run_ids
        assert {item.execution_attempt_id for item in replay} == first_attempt_ids
        assert austria_objective_readiness(
            replay_session,
            tenant_key="default",
            root_work_item_id=plan.root_work_item.id,
        ).ready_for_owner_synthesis is True
