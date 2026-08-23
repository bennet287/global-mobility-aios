from __future__ import annotations

import json

import pytest
from sqlmodel import Session

from app.core.config import settings
from app.models.domain import AgentRun
from app.services.organization_agent_runtime import RuntimeClass
from app.services.organization_command import DependencyConflict
from app.services.organization_governance import ensure_foundation_positions
from app.services.organization_mobility_live_provider_evaluation import (
    AustriaLiveProviderSelection,
    compile_austria_live_provider_evaluation,
    configured_live_provider_selection,
    live_provider_runtime_profiles,
)
from app.services.organization_mobility_objective_execution import execute_austria_specialists
from app.services.organization_mobility_objective_runtime import (
    AUSTRIA_MOBILITY_SPECIALIST_POSITIONS,
    create_austria_mobility_objective,
)
from tests.test_organization_mobility_context_provenance import (
    _authority_graph,
    _force_deterministic,
    _human_context,
    _profiles,
)


def _grounded_deterministic_execution(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
    *,
    objective_key: str,
):
    ensure_foundation_positions(
        db_session,
        actor="pytest-live-provider-evaluation",
        repair_contracts=True,
    )
    _force_deterministic(monkeypatch)
    graph = _authority_graph(db_session)
    plan = create_austria_mobility_objective(
        db_session,
        _human_context(),
        objective_key=objective_key,
        pathway_version_id=graph["pathway_version"].id,
    )
    results = execute_austria_specialists(
        db_session,
        _human_context(),
        plan,
        runtime_profiles=_profiles(),
    )
    return plan, results


def test_live_provider_evaluation_does_not_promote_deterministic_grounded_execution(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan, results = _grounded_deterministic_execution(
        db_session,
        monkeypatch,
        objective_key="at-rwr-shortage-2026-live-provider-negative-control",
    )

    evaluation = compile_austria_live_provider_evaluation(
        db_session,
        plan=plan,
        selection=AustriaLiveProviderSelection(
            provider_key="deepseek",
            model_key="deepseek-chat",
        ),
        results=results,
    )

    assert evaluation.live_provider_success_count == 0
    assert evaluation.provider_failure_count == 0
    assert evaluation.configured_selection_matches_all_specialists is False
    assert evaluation.all_specialists_live_provider_succeeded is False
    assert evaluation.all_specialists_authority_grounded is True
    assert evaluation.fresh_retrieval_provenance_complete is False
    assert evaluation.live_provider_acceptance_candidate is False
    assert evaluation.full_l_reasoning_evidence_candidate is False
    assert evaluation.provider_model_authority is False
    assert evaluation.external_action_authorized is False
    assert len(evaluation.specialist_evaluations) == len(AUSTRIA_MOBILITY_SPECIALIST_POSITIONS)
    assert all(
        item.execution_mode == "deterministic_template"
        and item.provider_outcome == "not_invoked"
        and item.live_provider_succeeded is False
        and item.grounding_state == "authority_grounded"
        and item.fresh_retrieval_provenance_present is False
        for item in evaluation.specialist_evaluations
    )


def test_configured_live_provider_selection_requires_key_and_builds_bounded_profiles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "llm_provider", "deepseek")
    monkeypatch.setattr(settings, "deepseek_model", "deepseek-chat")
    monkeypatch.setattr(settings, "deepseek_api_key", "")

    with pytest.raises(DependencyConflict, match="configured deepseek API key is unavailable"):
        configured_live_provider_selection(require_api_key=True)

    monkeypatch.setattr(settings, "deepseek_api_key", "test-only-key")
    selection = configured_live_provider_selection(require_api_key=True)
    assert selection == AustriaLiveProviderSelection(
        provider_key="deepseek",
        model_key="deepseek-chat",
    )

    profiles = live_provider_runtime_profiles(selection)
    assert set(profiles) == set(AUSTRIA_MOBILITY_SPECIALIST_POSITIONS)
    for profile in profiles.values():
        assert profile.runtime_class is RuntimeClass.HOSTED_API
        assert profile.provider_key == "deepseek"
        assert profile.model_key == "deepseek-chat"
        assert profile.technical_capabilities == ("reasoning", "structured_output")
        assert profile.available_tools == ()
        assert profile.enabled is True


def test_live_provider_evaluation_rejects_agent_run_provenance_tampering(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan, results = _grounded_deterministic_execution(
        db_session,
        monkeypatch,
        objective_key="at-rwr-shortage-2026-live-provider-provenance-tamper",
    )
    first = results[0]
    run = db_session.get(AgentRun, first.agent_run_id)
    assert run is not None
    run_input = json.loads(run.input_json)
    run_input["context"]["k1_provenance"]["provider_key"] = "forged-provider"
    run.input_json = json.dumps(run_input, sort_keys=True)
    db_session.add(run)
    db_session.commit()

    with pytest.raises(
        DependencyConflict,
        match="live-provider ActionOutput/AgentRun provenance diverged",
    ):
        compile_austria_live_provider_evaluation(
            db_session,
            plan=plan,
            selection=AustriaLiveProviderSelection(
                provider_key="deepseek",
                model_key="deepseek-chat",
            ),
            results=results,
        )
