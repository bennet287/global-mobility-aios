from __future__ import annotations

import json

import pytest
from sqlmodel import Session

from app.models.domain import AgentRun, OrganizationActorType, OrganizationalActionOutput
from app.services.organization_agent_runtime import AgentRuntimeProfile, RuntimeClass
from app.services.organization_command import OrganizationCommandContext
from app.services.organization_context_broker import ContextReference, PriorWorkContext
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
        profile_key="history-consumer-reasoning-v1",
        runtime_class=RuntimeClass.HOSTED_API,
        adapter_key="history-consumer-adapter",
        provider_key="provider-a",
        model_key="provider-a-model",
        technical_capabilities=("reasoning", "structured_output"),
        available_tools=("browser", "shell"),
        independence_group="provider-a",
        profile_version=1,
        enabled=True,
    )


def test_k1_consumes_cited_history_only_as_non_authoritative_observation(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ensure_foundation_positions(db_session, actor="pytest", repair_contracts=True)
    monkeypatch.setattr("app.services.controlled_agents.is_llm_enabled", lambda: False)

    recalled = PriorWorkContext(
        work_item_ref=ContextReference(
            kind="organizational_work_item",
            identifier="prior-work-123",
            version="prior-work-fingerprint",
        ),
        contribution_ref=ContextReference(
            kind="organization_contribution",
            identifier="contribution-456",
            version="contribution-fingerprint",
        ),
        source_ref=ContextReference(
            kind="mobility_pathway_version",
            identifier="source-789",
            version="7",
        ),
    )

    def fake_recall(session: Session, *, context, limit: int = 5):
        assert session is db_session
        assert context.evidence_refs == ()
        assert context.verified_rule_refs == ()
        assert limit == 5
        return (recalled,)

    monkeypatch.setattr(
        "app.services.organization_mobility_objective_execution.recall_prior_work_context",
        fake_recall,
    )

    command_context = _human_context()
    plan = create_austria_mobility_objective(
        db_session,
        command_context,
        objective_key="at-rwr-shortage-2026-k1-history-consumer",
    )
    result = execute_austria_specialist_work(
        db_session,
        command_context,
        plan,
        position_key=AUSTRIA_MOBILITY_PATHWAY_POSITION,
        runtime_profile=_runtime(),
    )

    agent_run = db_session.get(AgentRun, result.agent_run_id)
    assert agent_run is not None
    run_input = json.loads(agent_run.input_json)
    run_context = run_input["context"]
    history = run_context["historical_observations"]
    assert history["epistemic_status"] == "historical_observation"
    assert history["authority"] is False
    assert "not verified facts" in history["instruction"]
    assert len(history["items"]) == 1
    recalled_item = history["items"][0]
    assert recalled_item["epistemic_status"] == "historical_observation"
    assert recalled_item["authority"] is False
    assert recalled_item["work_item_ref"]["identifier"] == "prior-work-123"
    assert recalled_item["contribution_ref"]["identifier"] == "contribution-456"
    assert recalled_item["source_ref"]["identifier"] == "source-789"

    # History remains outside the K.1 authority/provenance channel.
    provenance = run_context["k1_provenance"]
    assert "historical_observations" not in provenance
    assert provenance["context_evidence_refs"] == []
    assert provenance["context_verified_rule_refs"] == []
    assert provenance["context_source_snapshot_refs"] == []

    output = db_session.get(OrganizationalActionOutput, result.action_output_id)
    assert output is not None
    durable_payload = json.loads(output.output_json)
    assert durable_payload["historical_observation_count"] == 1
    assert durable_payload["historical_observations"] == history["items"]

    # Recalled citations are audit provenance only; they never become Evidence.
    evidence_payload = json.loads(output.evidence_json)
    evidence_text = json.dumps(evidence_payload, sort_keys=True)
    assert "prior-work-123" not in evidence_text
    assert "contribution-456" not in evidence_text
    assert "source-789" not in evidence_text
