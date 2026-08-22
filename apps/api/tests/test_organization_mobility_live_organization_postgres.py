from __future__ import annotations

import os

import pytest
from sqlmodel import Session, select

from app.models.domain import OrganizationActivity, OrganizationActorType, OrganizationalActionOutput
from app.services.organization_agent_runtime import AgentRuntimeProfile, RuntimeClass
from app.services.organization_command import OrganizationCommandContext
from app.services.organization_governance import ensure_foundation_positions
from app.services.organization_mobility_live_organization import (
    austria_live_organization_snapshot,
    austria_owner_synthesis_activity_key,
    austria_owner_synthesis_output_key,
    synthesize_austria_objective_owner,
)
from app.services.organization_mobility_objective_execution import execute_austria_specialists
from app.services.organization_mobility_objective_runtime import (
    AUSTRIA_MOBILITY_PATHWAY_POSITION,
    AUSTRIA_MOBILITY_REGULATORY_POSITION,
    create_austria_mobility_objective,
)


pytestmark = pytest.mark.skipif(
    not os.getenv("GMAI_TEST_DATABASE_URL", "").startswith("postgresql"),
    reason="real PostgreSQL contract requires GMAI_TEST_DATABASE_URL",
)


def _human_context() -> OrganizationCommandContext:
    return OrganizationCommandContext(
        tenant_key="default",
        actor_id="postgres-l1-owner",
        actor_type=OrganizationActorType.human,
        authenticated_user_id="postgres-l1-owner",
        role="admin",
        department="Global Mobility Operations",
        position_key="board",
        authority_level="L4",
    )


def _runtime(provider: str) -> AgentRuntimeProfile:
    return AgentRuntimeProfile(
        profile_key=f"{provider}-postgres-l1-v1",
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


def test_postgres_l1_owner_cycle_survives_cross_session_exact_replay(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("app.services.controlled_agents.is_llm_enabled", lambda: False)
    ensure_foundation_positions(db_session, actor="postgres-l1", repair_contracts=True)
    context = _human_context()
    profiles = {
        AUSTRIA_MOBILITY_PATHWAY_POSITION: _runtime("provider-a"),
        AUSTRIA_MOBILITY_REGULATORY_POSITION: _runtime("provider-b"),
    }
    plan = create_austria_mobility_objective(
        db_session,
        context,
        objective_key="at-rwr-shortage-2026-l1-postgres",
    )
    execute_austria_specialists(
        db_session,
        context,
        plan,
        runtime_profiles=profiles,
    )

    first = synthesize_austria_objective_owner(
        db_session,
        tenant_key="default",
        root_work_item_id=plan.root_work_item.id,
    )
    assert first.replayed is False

    output_key = austria_owner_synthesis_output_key(plan.root_work_item.id)
    activity_key = austria_owner_synthesis_activity_key(plan.root_work_item.id)
    engine = db_session.get_bind()

    with Session(engine) as replay_session:
        snapshot = austria_live_organization_snapshot(
            replay_session,
            tenant_key="default",
            root_work_item_id=plan.root_work_item.id,
        )
        assert snapshot.root_status == "completed"
        assert snapshot.cycle_status == "completed"
        assert snapshot.owner_synthesis_state == "completed"
        assert snapshot.owner_synthesis is not None
        assert snapshot.owner_synthesis.action_output_id == first.action_output_id
        assert snapshot.owner_synthesis.activity_id == first.activity_id
        assert len(snapshot.specialist_outputs) == 2
        assert all(item.evidence_valid for item in snapshot.specialist_outputs)
        assert snapshot.external_action_authorized is False
        assert snapshot.provider_model_authority is False

        output_count_before = len(
            replay_session.exec(
                select(OrganizationalActionOutput).where(
                    OrganizationalActionOutput.output_key == output_key
                )
            ).all()
        )
        activity_count_before = len(
            replay_session.exec(
                select(OrganizationActivity).where(
                    OrganizationActivity.activity_key == activity_key
                )
            ).all()
        )
        assert output_count_before == 1
        assert activity_count_before == 1

        replay = synthesize_austria_objective_owner(
            replay_session,
            tenant_key="default",
            root_work_item_id=plan.root_work_item.id,
        )
        assert replay.replayed is True
        assert replay.action_output_id == first.action_output_id
        assert replay.activity_id == first.activity_id
        assert len(
            replay_session.exec(
                select(OrganizationalActionOutput).where(
                    OrganizationalActionOutput.output_key == output_key
                )
            ).all()
        ) == output_count_before
        assert len(
            replay_session.exec(
                select(OrganizationActivity).where(
                    OrganizationActivity.activity_key == activity_key
                )
            ).all()
        ) == activity_count_before
