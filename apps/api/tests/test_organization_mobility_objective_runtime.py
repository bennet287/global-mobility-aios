from __future__ import annotations

from dataclasses import replace

import pytest
from sqlmodel import Session, select

from app.models.domain import OrganizationActorType, OrganizationPosition, OrganizationalWorkItem
from app.services.organization_agent_runtime import (
    AgentRuntimeProfile,
    RuntimeBindingStale,
    RuntimeClass,
    bind_employee_runtime,
)
from app.services.organization_command import OrganizationCommandContext
from app.services.organization_context_broker import build_work_item_context_bundle
from app.services.organization_governance import ensure_foundation_positions
from app.services.organization_mobility_objective_runtime import (
    AUSTRIA_MOBILITY_OBJECTIVE_OWNER_POSITION,
    AUSTRIA_MOBILITY_PATHWAY_POSITION,
    AUSTRIA_MOBILITY_REGULATORY_POSITION,
    AUSTRIA_MOBILITY_SPECIALIST_POSITIONS,
    austria_objective_readiness,
    bind_austria_specialist_runtimes,
    create_austria_mobility_objective,
    objective_activity_count,
)
from app.services.organization_work import complete_work_item, start_work_item


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


def _runtime(provider: str, *, profile_key: str | None = None) -> AgentRuntimeProfile:
    return AgentRuntimeProfile(
        profile_key=profile_key or f"{provider}-reasoning-v1",
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


def _foundation(db_session: Session) -> None:
    ensure_foundation_positions(db_session, actor="pytest", repair_contracts=True)


def test_j1_creates_one_root_and_two_persistent_specialist_work_items(db_session: Session) -> None:
    _foundation(db_session)
    context = _human_context()

    plan = create_austria_mobility_objective(
        db_session,
        context,
        objective_key="at-rwr-shortage-2026-case-001",
    )

    assert plan.root_work_item.status == "running"
    assert plan.root_work_item.assigned_position_key == AUSTRIA_MOBILITY_OBJECTIVE_OWNER_POSITION
    assert plan.pathway_work_item.parent_work_item_id == plan.root_work_item.id
    assert plan.regulatory_work_item.parent_work_item_id == plan.root_work_item.id
    assert {
        plan.pathway_work_item.assigned_position_key,
        plan.regulatory_work_item.assigned_position_key,
    } == set(AUSTRIA_MOBILITY_SPECIALIST_POSITIONS)

    for work in (plan.root_work_item, plan.pathway_work_item, plan.regulatory_work_item):
        position = db_session.exec(
            select(OrganizationPosition).where(
                OrganizationPosition.position_key == work.assigned_position_key
            )
        ).one()
        assert position.status == "active"
        assert work.department == position.department
        assert work.authority_level == position.authority_level

    # Three creations plus the root running transition are durably visible through the
    # existing Activity ledger; J.1 does not add a second Mission/event store.
    assert objective_activity_count(db_session, root_work_item_id=plan.root_work_item.id) >= 4


def test_j1_objective_creation_is_exactly_replayable_without_duplicate_topology(db_session: Session) -> None:
    _foundation(db_session)
    context = _human_context()
    objective_key = "at-rwr-shortage-2026-replay"

    first = create_austria_mobility_objective(db_session, context, objective_key=objective_key)
    activity_count = objective_activity_count(db_session, root_work_item_id=first.root_work_item.id)
    second = create_austria_mobility_objective(db_session, context, objective_key=objective_key)

    assert second.root_work_item.id == first.root_work_item.id
    assert second.pathway_work_item.id == first.pathway_work_item.id
    assert second.regulatory_work_item.id == first.regulatory_work_item.id
    assert objective_activity_count(db_session, root_work_item_id=first.root_work_item.id) == activity_count

    children = db_session.exec(
        select(OrganizationalWorkItem).where(
            OrganizationalWorkItem.parent_work_item_id == first.root_work_item.id
        )
    ).all()
    assert len(children) == 2


def test_j1_binds_each_specialist_through_fresh_context_without_runtime_authority(db_session: Session) -> None:
    _foundation(db_session)
    plan = create_austria_mobility_objective(
        db_session,
        _human_context(),
        objective_key="at-rwr-shortage-2026-bindings",
    )
    profiles = {
        AUSTRIA_MOBILITY_PATHWAY_POSITION: _runtime("provider-a"),
        AUSTRIA_MOBILITY_REGULATORY_POSITION: _runtime("provider-b"),
    }

    bindings = bind_austria_specialist_runtimes(
        db_session,
        plan,
        runtime_profiles=profiles,
    )

    assert tuple(item.position_key for item in bindings) == AUSTRIA_MOBILITY_SPECIALIST_POSITIONS
    for item in bindings:
        assert item.runtime.position_key == item.position_key
        assert item.runtime.context_hash == item.context.context_hash
        assert item.runtime.position_version == item.context.position.position_version
        assert item.context.position.authority_level == "L1"
        assert set(item.runtime.allowed_tools).issubset(set(item.context.allowed_tools))
        assert set(item.runtime.allowed_tools).issubset(set(profiles[item.position_key].available_tools))

    # Runtime identity is technical only. Rebinding the same employee/context to a
    # different provider changes binding identity but not employee/context authority.
    pathway_context = bindings[0].context
    alternate = bind_employee_runtime(
        db_session,
        context=pathway_context,
        profile=_runtime("provider-c", profile_key="alternate-provider-v1"),
        required_capability="reasoning",
    )
    assert alternate.position_key == bindings[0].runtime.position_key
    assert alternate.position_version == bindings[0].runtime.position_version
    assert alternate.context_hash == bindings[0].runtime.context_hash
    assert alternate.binding_hash != bindings[0].runtime.binding_hash
    assert alternate.provider_key != bindings[0].runtime.provider_key
    assert pathway_context.position.authority_level == "L1"


def test_j1_stale_specialist_context_cannot_be_rebound_after_work_state_change(db_session: Session) -> None:
    _foundation(db_session)
    context = _human_context()
    plan = create_austria_mobility_objective(
        db_session,
        context,
        objective_key="at-rwr-shortage-2026-stale-context",
    )
    stale_context = build_work_item_context_bundle(
        db_session,
        tenant_key="default",
        position_key=AUSTRIA_MOBILITY_PATHWAY_POSITION,
        work_item_id=plan.pathway_work_item.id,
    )

    start_work_item(
        db_session,
        context,
        work_item_id=plan.pathway_work_item.id,
        reason="Start pathway specialist work.",
    )

    with pytest.raises(RuntimeBindingStale):
        bind_employee_runtime(
            db_session,
            context=stale_context,
            profile=_runtime("provider-a"),
            required_capability="reasoning",
        )


def test_j1_owner_synthesis_readiness_requires_both_specialists_to_complete(db_session: Session) -> None:
    _foundation(db_session)
    context = _human_context()
    plan = create_austria_mobility_objective(
        db_session,
        context,
        objective_key="at-rwr-shortage-2026-readiness",
    )

    initial = austria_objective_readiness(
        db_session,
        tenant_key="default",
        root_work_item_id=plan.root_work_item.id,
    )
    assert initial.ready_for_owner_synthesis is False
    assert set(initial.pending_positions) == set(AUSTRIA_MOBILITY_SPECIALIST_POSITIONS)

    pathway = start_work_item(
        db_session,
        context,
        work_item_id=plan.pathway_work_item.id,
        reason="Start pathway specialist work.",
    )
    complete_work_item(
        db_session,
        context,
        work_item_id=pathway.id,
        reason="Pathway specialist bounded analysis completed.",
    )
    halfway = austria_objective_readiness(
        db_session,
        tenant_key="default",
        root_work_item_id=plan.root_work_item.id,
    )
    assert halfway.ready_for_owner_synthesis is False
    assert halfway.completed_positions == (AUSTRIA_MOBILITY_PATHWAY_POSITION,)
    assert halfway.pending_positions == (AUSTRIA_MOBILITY_REGULATORY_POSITION,)

    regulatory = start_work_item(
        db_session,
        context,
        work_item_id=plan.regulatory_work_item.id,
        reason="Start regulatory specialist work.",
    )
    complete_work_item(
        db_session,
        context,
        work_item_id=regulatory.id,
        reason="Regulatory specialist bounded analysis completed.",
    )
    ready = austria_objective_readiness(
        db_session,
        tenant_key="default",
        root_work_item_id=plan.root_work_item.id,
    )

    assert ready.ready_for_owner_synthesis is True
    assert ready.pending_positions == ()
    assert set(ready.completed_positions) == set(AUSTRIA_MOBILITY_SPECIALIST_POSITIONS)
    assert ready.reasons == ()


def test_j1_runtime_profile_cannot_forge_completed_specialist_work(db_session: Session) -> None:
    _foundation(db_session)
    plan = create_austria_mobility_objective(
        db_session,
        _human_context(),
        objective_key="at-rwr-shortage-2026-no-runtime-shortcut",
    )
    bindings = bind_austria_specialist_runtimes(
        db_session,
        plan,
        runtime_profiles={
            AUSTRIA_MOBILITY_PATHWAY_POSITION: _runtime("provider-a"),
            AUSTRIA_MOBILITY_REGULATORY_POSITION: _runtime("provider-b"),
        },
    )

    forged = replace(bindings[0].runtime, provider_key="authority-provider")
    assert forged.position_key == bindings[0].runtime.position_key
    assert forged.context_hash == bindings[0].runtime.context_hash

    readiness = austria_objective_readiness(
        db_session,
        tenant_key="default",
        root_work_item_id=plan.root_work_item.id,
    )
    assert readiness.ready_for_owner_synthesis is False
    assert set(readiness.pending_positions) == set(AUSTRIA_MOBILITY_SPECIALIST_POSITIONS)
