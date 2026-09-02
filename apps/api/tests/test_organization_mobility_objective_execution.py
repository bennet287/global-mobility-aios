from __future__ import annotations

import json
from dataclasses import replace

import pytest
from sqlmodel import Session, select

from app.models.domain import (
    AgentRun,
    OrganizationActorType,
    OrganizationExecutionAttempt,
    OrganizationalActionOutput,
)
from app.services.organization_agent_runtime import (
    AgentRuntimeProfile,
    RuntimeBindingStale,
    RuntimeClass,
)
from app.services.organization_command import DependencyConflict, OrganizationCommandContext
from app.services.organization_governance import ensure_foundation_positions
from app.services.organization_mobility_objective_execution import (
    execute_austria_specialist_work,
    execute_austria_specialists,
)
from app.services.organization_mobility_objective_runtime import (
    AUSTRIA_MOBILITY_PATHWAY_POSITION,
    AUSTRIA_MOBILITY_REGULATORY_POSITION,
    AUSTRIA_MOBILITY_SPECIALIST_EXECUTION_CONTRACT_VERSION,
    AUSTRIA_MOBILITY_SPECIALIST_POSITIONS,
    austria_objective_readiness,
    austria_specialist_output_key,
    bind_austria_specialist_runtimes,
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


def _profiles() -> dict[str, AgentRuntimeProfile]:
    return {
        AUSTRIA_MOBILITY_PATHWAY_POSITION: _runtime("provider-a"),
        AUSTRIA_MOBILITY_REGULATORY_POSITION: _runtime("provider-b"),
    }


def _foundation(db_session: Session) -> None:
    ensure_foundation_positions(db_session, actor="pytest", repair_contracts=True)


def _force_deterministic(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.services.controlled_agents.is_llm_enabled", lambda: False)


def test_k1_executes_both_specialists_and_requires_both_current_outputs_for_readiness(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _foundation(db_session)
    _force_deterministic(monkeypatch)
    context = _human_context()
    plan = create_austria_mobility_objective(
        db_session,
        context,
        objective_key="at-rwr-shortage-2026-k1-full",
    )
    profiles = _profiles()

    pathway = execute_austria_specialist_work(
        db_session,
        context,
        plan,
        position_key=AUSTRIA_MOBILITY_PATHWAY_POSITION,
        runtime_profile=profiles[AUSTRIA_MOBILITY_PATHWAY_POSITION],
    )
    assert pathway.replayed is False
    halfway = austria_objective_readiness(
        db_session,
        tenant_key="default",
        root_work_item_id=plan.root_work_item.id,
    )
    assert halfway.ready_for_owner_synthesis is False
    assert halfway.completed_positions == (AUSTRIA_MOBILITY_PATHWAY_POSITION,)
    assert halfway.pending_positions == (AUSTRIA_MOBILITY_REGULATORY_POSITION,)

    regulatory = execute_austria_specialist_work(
        db_session,
        context,
        plan,
        position_key=AUSTRIA_MOBILITY_REGULATORY_POSITION,
        runtime_profile=profiles[AUSTRIA_MOBILITY_REGULATORY_POSITION],
    )
    assert regulatory.replayed is False

    ready = austria_objective_readiness(
        db_session,
        tenant_key="default",
        root_work_item_id=plan.root_work_item.id,
    )
    assert ready.ready_for_owner_synthesis is True
    assert set(ready.completed_positions) == set(AUSTRIA_MOBILITY_SPECIALIST_POSITIONS)
    assert ready.pending_positions == ()
    assert ready.reasons == ()

    outputs = db_session.exec(
        select(OrganizationalActionOutput).where(
            OrganizationalActionOutput.work_item_id.in_(
                [plan.pathway_work_item.id, plan.regulatory_work_item.id]
            )
        )
    ).all()
    assert len(outputs) == 2
    for output in outputs:
        payload = json.loads(output.output_json)
        impact = json.loads(output.impact_json)
        assert payload["contract_version"] == AUSTRIA_MOBILITY_SPECIALIST_EXECUTION_CONTRACT_VERSION
        assert payload["completed_work_fingerprint"]
        assert payload["context_hash"]
        assert payload["runtime_binding_hash"]
        assert payload["execution_attempt_id"]
        assert payload["agent_run_id"]
        assert payload["provider_model_authority"] is False
        assert payload["governance_check_count"] >= 5
        assert payload["retry_count"] == 0
        assert payload["latency_ms"] >= 0
        assert impact["client_facing"] is False
        assert impact["external_action_authorized"] is False
        assert impact["human_review_required"] is True
        assert {
            "authority_submission",
            "client_send",
            "external_provider_action",
            "payment_initiation",
        }.issubset(set(impact["blocked_actions"]))


def test_k1_exact_replay_reuses_outputs_agent_runs_and_attempts(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _foundation(db_session)
    _force_deterministic(monkeypatch)
    context = _human_context()
    plan = create_austria_mobility_objective(
        db_session,
        context,
        objective_key="at-rwr-shortage-2026-k1-replay",
    )
    profiles = _profiles()

    first = execute_austria_specialists(
        db_session,
        context,
        plan,
        runtime_profiles=profiles,
    )
    output_ids = {item.action_output_id for item in first}
    run_ids = {item.agent_run_id for item in first}
    attempt_ids = {item.execution_attempt_id for item in first}
    counts = (
        len(db_session.exec(select(OrganizationalActionOutput)).all()),
        len(db_session.exec(select(AgentRun)).all()),
        len(db_session.exec(select(OrganizationExecutionAttempt)).all()),
    )

    replay = execute_austria_specialists(
        db_session,
        context,
        plan,
        runtime_profiles=profiles,
    )

    assert all(item.replayed for item in replay)
    assert {item.action_output_id for item in replay} == output_ids
    assert {item.agent_run_id for item in replay} == run_ids
    assert {item.execution_attempt_id for item in replay} == attempt_ids
    assert (
        len(db_session.exec(select(OrganizationalActionOutput)).all()),
        len(db_session.exec(select(AgentRun)).all()),
        len(db_session.exec(select(OrganizationExecutionAttempt)).all()),
    ) == counts


def test_k1_rejects_stale_binding_after_specialist_work_state_changes(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _foundation(db_session)
    _force_deterministic(monkeypatch)
    context = _human_context()
    plan = create_austria_mobility_objective(
        db_session,
        context,
        objective_key="at-rwr-shortage-2026-k1-stale-binding",
    )
    profiles = _profiles()
    stale = bind_austria_specialist_runtimes(
        db_session,
        plan,
        runtime_profiles=profiles,
    )[0]

    with pytest.raises(RuntimeBindingStale):
        execute_austria_specialist_work(
            db_session,
            context,
            plan,
            position_key=AUSTRIA_MOBILITY_PATHWAY_POSITION,
            runtime_profile=profiles[AUSTRIA_MOBILITY_PATHWAY_POSITION],
            expected_binding=stale,
        )

    assert db_session.exec(select(AgentRun)).all() == []
    assert db_session.exec(select(OrganizationalActionOutput)).all() == []
    assert db_session.exec(select(OrganizationExecutionAttempt)).all() == []


def test_k1_rejects_binding_that_points_at_wrong_workitem(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _foundation(db_session)
    _force_deterministic(monkeypatch)
    context = _human_context()
    plan = create_austria_mobility_objective(
        db_session,
        context,
        objective_key="at-rwr-shortage-2026-k1-wrong-work",
    )
    profiles = _profiles()
    start_work_item(
        db_session,
        context,
        work_item_id=plan.pathway_work_item.id,
        reason="Start pathway before constructing current K.1 binding.",
    )
    current_binding = bind_austria_specialist_runtimes(
        db_session,
        plan,
        runtime_profiles=profiles,
    )[0]
    wrong = replace(current_binding, work_item_id=plan.regulatory_work_item.id)

    with pytest.raises(RuntimeBindingStale):
        execute_austria_specialist_work(
            db_session,
            context,
            plan,
            position_key=AUSTRIA_MOBILITY_PATHWAY_POSITION,
            runtime_profile=profiles[AUSTRIA_MOBILITY_PATHWAY_POSITION],
            expected_binding=wrong,
        )


def test_k1_completed_output_cannot_be_replayed_under_different_runtime_profile(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _foundation(db_session)
    _force_deterministic(monkeypatch)
    context = _human_context()
    plan = create_austria_mobility_objective(
        db_session,
        context,
        objective_key="at-rwr-shortage-2026-k1-runtime-provenance",
    )
    original = _runtime("provider-a")

    execute_austria_specialist_work(
        db_session,
        context,
        plan,
        position_key=AUSTRIA_MOBILITY_PATHWAY_POSITION,
        runtime_profile=original,
    )

    with pytest.raises(DependencyConflict, match="original technical runtime profile"):
        execute_austria_specialist_work(
            db_session,
            context,
            plan,
            position_key=AUSTRIA_MOBILITY_PATHWAY_POSITION,
            runtime_profile=_runtime("provider-c"),
        )

    assert len(db_session.exec(select(AgentRun)).all()) == 1
    assert len(db_session.exec(select(OrganizationalActionOutput)).all()) == 1


def test_k1_readiness_fails_closed_when_durable_provenance_is_tampered(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _foundation(db_session)
    _force_deterministic(monkeypatch)
    context = _human_context()
    plan = create_austria_mobility_objective(
        db_session,
        context,
        objective_key="at-rwr-shortage-2026-k1-tamper",
    )
    execute_austria_specialists(
        db_session,
        context,
        plan,
        runtime_profiles=_profiles(),
    )
    assert austria_objective_readiness(
        db_session,
        tenant_key="default",
        root_work_item_id=plan.root_work_item.id,
    ).ready_for_owner_synthesis is True

    output = db_session.exec(
        select(OrganizationalActionOutput).where(
            OrganizationalActionOutput.output_key
            == austria_specialist_output_key(plan.regulatory_work_item.id)
        )
    ).one()
    payload = json.loads(output.output_json)
    payload["context_hash"] = "forged-context-hash"
    output.output_json = json.dumps(payload, sort_keys=True)
    db_session.add(output)
    db_session.commit()

    readiness = austria_objective_readiness(
        db_session,
        tenant_key="default",
        root_work_item_id=plan.root_work_item.id,
    )
    assert readiness.ready_for_owner_synthesis is False
    assert AUSTRIA_MOBILITY_REGULATORY_POSITION in readiness.pending_positions
    assert any("AgentRun provenance does not match" in reason for reason in readiness.reasons)
