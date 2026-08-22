from __future__ import annotations

import json

import pytest
from sqlmodel import Session, select

from app.models.domain import (
    OrganizationActivity,
    OrganizationActivityClass,
    OrganizationActorType,
    OrganizationBlockerType,
    OrganizationalActionOutput,
)
from app.services.organization_agent_runtime import AgentRuntimeProfile, RuntimeClass
from app.services.organization_command import DependencyConflict, OrganizationCommandContext
from app.services.organization_governance import ensure_foundation_positions
from app.services.organization_mobility_live_organization import (
    AUSTRIA_LIVE_ORGANIZATION_CONTRACT_VERSION,
    austria_live_organization_snapshot,
    austria_owner_synthesis_activity_key,
    austria_owner_synthesis_output_key,
    synthesize_austria_objective_owner,
)
from app.services.organization_mobility_objective_execution import execute_austria_specialists
from app.services.organization_mobility_objective_runtime import (
    AUSTRIA_MOBILITY_OBJECTIVE_OWNER_POSITION,
    AUSTRIA_MOBILITY_PATHWAY_POSITION,
    AUSTRIA_MOBILITY_REGULATORY_POSITION,
    austria_specialist_output_key,
    create_austria_mobility_objective,
)
from app.services.organization_work import open_blocker


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


def _runtime(provider: str) -> AgentRuntimeProfile:
    return AgentRuntimeProfile(
        profile_key=f"{provider}-l1-v1",
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


def _profiles() -> dict[str, AgentRuntimeProfile]:
    return {
        AUSTRIA_MOBILITY_PATHWAY_POSITION: _runtime("provider-a"),
        AUSTRIA_MOBILITY_REGULATORY_POSITION: _runtime("provider-b"),
    }


def _foundation(db_session: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    ensure_foundation_positions(db_session, actor="pytest", repair_contracts=True)
    monkeypatch.setattr("app.services.controlled_agents.is_llm_enabled", lambda: False)


def test_l1_owner_synthesis_completes_real_persisted_organization_cycle(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _foundation(db_session, monkeypatch)
    context = _human_context()
    plan = create_austria_mobility_objective(
        db_session,
        context,
        objective_key="at-rwr-shortage-2026-l1-live-cycle",
    )
    execute_austria_specialists(db_session, context, plan, runtime_profiles=_profiles())

    result = synthesize_austria_objective_owner(
        db_session,
        tenant_key="default",
        root_work_item_id=plan.root_work_item.id,
    )
    assert result.replayed is False
    assert result.disposition == "ready_for_human_review"

    root = db_session.get(type(plan.root_work_item), plan.root_work_item.id)
    assert root is not None
    assert root.status == "completed"

    output = db_session.exec(
        select(OrganizationalActionOutput).where(
            OrganizationalActionOutput.output_key == austria_owner_synthesis_output_key(root.id)
        )
    ).one()
    assert output.id == result.action_output_id
    assert output.work_item_id == root.id
    assert output.accountable_position_key == AUSTRIA_MOBILITY_OBJECTIVE_OWNER_POSITION
    payload = json.loads(output.output_json)
    impact = json.loads(output.impact_json)
    assert payload["contract_version"] == AUSTRIA_LIVE_ORGANIZATION_CONTRACT_VERSION
    assert [item["position_key"] for item in payload["specialist_outputs"]] == [
        AUSTRIA_MOBILITY_PATHWAY_POSITION,
        AUSTRIA_MOBILITY_REGULATORY_POSITION,
    ]
    assert all(item["lineage_fingerprint"] for item in payload["specialist_outputs"])
    assert payload["provider_model_authority"] is False
    assert payload["external_action_authorized"] is False
    assert impact["human_review_required"] is True
    assert impact["external_action_authorized"] is False

    activity = db_session.exec(
        select(OrganizationActivity).where(
            OrganizationActivity.activity_key == austria_owner_synthesis_activity_key(root.id)
        )
    ).one()
    assert activity.id == result.activity_id
    assert activity.activity_class is OrganizationActivityClass.decision
    assert activity.actor_type is OrganizationActorType.agent
    assert activity.actor_id == AUSTRIA_MOBILITY_OBJECTIVE_OWNER_POSITION
    assert activity.position_key == AUSTRIA_MOBILITY_OBJECTIVE_OWNER_POSITION
    assert json.loads(activity.payload_json)["constitutional_activity_class"] == "MATERIAL"

    snapshot = austria_live_organization_snapshot(
        db_session,
        tenant_key="default",
        root_work_item_id=root.id,
    )
    assert snapshot.cycle_status == "completed"
    assert snapshot.owner_synthesis_state == "completed"
    assert snapshot.root_status == "completed"
    assert snapshot.owner_synthesis is not None
    assert snapshot.owner_synthesis.action_output_id == output.id
    assert len(snapshot.specialist_outputs) == 2
    assert all(item.evidence_valid for item in snapshot.specialist_outputs)
    assert snapshot.provider_model_authority is False
    assert snapshot.external_action_authorized is False
    assert snapshot.activity_count >= 1
    assert any(record.activity_id == activity.id for record in snapshot.activities)


def test_l1_exact_replay_reuses_owner_output_and_activity(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _foundation(db_session, monkeypatch)
    context = _human_context()
    plan = create_austria_mobility_objective(
        db_session,
        context,
        objective_key="at-rwr-shortage-2026-l1-replay",
    )
    execute_austria_specialists(db_session, context, plan, runtime_profiles=_profiles())
    first = synthesize_austria_objective_owner(
        db_session,
        tenant_key="default",
        root_work_item_id=plan.root_work_item.id,
    )
    output_count = len(db_session.exec(select(OrganizationalActionOutput)).all())
    activity_count = len(db_session.exec(select(OrganizationActivity)).all())

    replay = synthesize_austria_objective_owner(
        db_session,
        tenant_key="default",
        root_work_item_id=plan.root_work_item.id,
    )
    assert replay.replayed is True
    assert replay.action_output_id == first.action_output_id
    assert replay.activity_id == first.activity_id
    assert len(db_session.exec(select(OrganizationalActionOutput)).all()) == output_count
    assert len(db_session.exec(select(OrganizationActivity)).all()) == activity_count


def test_l1_refuses_owner_synthesis_before_k1_and_when_active_blocker_exists(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _foundation(db_session, monkeypatch)
    context = _human_context()
    plan = create_austria_mobility_objective(
        db_session,
        context,
        objective_key="at-rwr-shortage-2026-l1-gates",
    )
    with pytest.raises(DependencyConflict, match="not ready"):
        synthesize_austria_objective_owner(
            db_session,
            tenant_key="default",
            root_work_item_id=plan.root_work_item.id,
        )

    execute_austria_specialists(db_session, context, plan, runtime_profiles=_profiles())
    blocker = open_blocker(
        db_session,
        context,
        blocker_key=f"l1-test-blocker:{plan.root_work_item.id}",
        blocker_type=OrganizationBlockerType.evidence,
        severity="high",
        title="Professional review evidence missing",
        description="Bounded L.1 test blocker.",
        work_item_id=plan.root_work_item.id,
        department=plan.root_work_item.department,
        accountable_position_key=AUSTRIA_MOBILITY_OBJECTIVE_OWNER_POSITION,
        authority_level=plan.root_work_item.authority_level,
        requires_human_action=True,
    )
    snapshot = austria_live_organization_snapshot(
        db_session,
        tenant_key="default",
        root_work_item_id=plan.root_work_item.id,
    )
    assert snapshot.cycle_status == "blocked"
    assert snapshot.blockers[0].blocker_id == blocker.id
    assert snapshot.blockers[0].requires_human_action is True

    with pytest.raises(DependencyConflict, match="active blocker"):
        synthesize_austria_objective_owner(
            db_session,
            tenant_key="default",
            root_work_item_id=plan.root_work_item.id,
        )


def test_l1_replay_fails_closed_if_specialist_lineage_is_tampered(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _foundation(db_session, monkeypatch)
    context = _human_context()
    plan = create_austria_mobility_objective(
        db_session,
        context,
        objective_key="at-rwr-shortage-2026-l1-tamper",
    )
    execute_austria_specialists(db_session, context, plan, runtime_profiles=_profiles())
    synthesize_austria_objective_owner(
        db_session,
        tenant_key="default",
        root_work_item_id=plan.root_work_item.id,
    )

    specialist = db_session.exec(
        select(OrganizationalActionOutput).where(
            OrganizationalActionOutput.output_key == austria_specialist_output_key(plan.pathway_work_item.id)
        )
    ).one()
    payload = json.loads(specialist.output_json)
    payload["context_hash"] = "tampered-after-owner-synthesis"
    specialist.output_json = json.dumps(payload, sort_keys=True)
    db_session.add(specialist)
    db_session.commit()

    with pytest.raises(DependencyConflict):
        synthesize_austria_objective_owner(
            db_session,
            tenant_key="default",
            root_work_item_id=plan.root_work_item.id,
        )
