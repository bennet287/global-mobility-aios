from __future__ import annotations

import json

import pytest

from app.services.organization_mobility_runtime_quality import (
    AUSTRIA_MOBILITY_RUNTIME_QUALITY_CONTRACT_VERSION,
    AustriaMobilityRuntimeQualityError,
    GroundingState,
    ModelExecutionMode,
    ProviderOutcome,
    evaluate_austria_specialist_runtime_quality,
)


def _ref(kind: str, identifier: str) -> dict[str, str]:
    return {"kind": kind, "identifier": identifier, "version": f"fp-{identifier}"}


def _agent_input(
    *,
    configured_provider: str | None,
    configured_model: str | None,
    bound_provider: str = "deepseek",
    bound_model: str = "deepseek-chat",
    grounding: str = "grounded",
) -> str:
    if grounding == "grounded":
        evidence = [_ref("mobility_pathway_version_evidence", "evidence-1")]
        rules = [_ref("verified_rule", "rule-1")]
        snapshots = [_ref("source_snapshot", "snapshot-1")]
    elif grounding == "partial":
        evidence = [_ref("mobility_pathway_version_evidence", "evidence-1")]
        rules = []
        snapshots = [_ref("source_snapshot", "snapshot-1")]
    else:
        evidence = []
        rules = []
        snapshots = []
    return json.dumps(
        {
            "agent_name": "operations_coordination_agent",
            "task": "bounded Austria specialist analysis",
            "context": {
                "k1_provenance": {
                    "provider_key": bound_provider,
                    "model_key": bound_model,
                    "provider_model_authority": False,
                    "context_evidence_refs": evidence,
                    "context_verified_rule_refs": rules,
                    "context_source_snapshot_refs": snapshots,
                }
            },
            "llm_provider": configured_provider,
            "llm_model": configured_model,
        },
        sort_keys=True,
    )


def _evaluate(agent_input_json: str, output: dict[str, object]):
    return evaluate_austria_specialist_runtime_quality(
        agent_input_json=agent_input_json,
        agent_output_json=json.dumps(output, sort_keys=True),
        durable_controlled_output=output,
    )


def test_deterministic_execution_is_truthfully_not_a_live_provider_call() -> None:
    snapshot = _evaluate(
        _agent_input(
            configured_provider=None,
            configured_model=None,
            bound_provider="provider-a",
            bound_model="provider-a-model",
            grounding="ungrounded",
        ),
        {"summary": "deterministic bounded output"},
    )

    assert snapshot.contract_version == AUSTRIA_MOBILITY_RUNTIME_QUALITY_CONTRACT_VERSION
    assert snapshot.execution_mode is ModelExecutionMode.DETERMINISTIC_TEMPLATE
    assert snapshot.provider_outcome is ProviderOutcome.NOT_INVOKED
    assert snapshot.provider_egress_occurred is False
    assert snapshot.fallback_to_template is False
    assert snapshot.configured_runtime_matches_binding is None
    assert snapshot.grounding_state is GroundingState.UNGROUNDED
    assert snapshot.source_snapshot_ref_count == 0
    assert snapshot.fresh_retrieval_provenance_present is False
    assert snapshot.provider_model_authority is False
    assert "no persisted authority grounding was consumed" in snapshot.warnings


def test_live_model_success_projects_provider_tokens_cost_and_grounding() -> None:
    output = {
        "summary": "live bounded output",
        "_llm_meta": {
            "provider": "deepseek",
            "model": "deepseek-chat",
            "finish_reason": "stop",
            "prompt_tokens": 100,
            "completion_tokens": 20,
            "total_tokens": 120,
            "estimated_cost_usd": 0.000032,
        },
    }
    snapshot = _evaluate(
        _agent_input(
            configured_provider="deepseek",
            configured_model="deepseek-chat",
        ),
        output,
    )

    assert snapshot.execution_mode is ModelExecutionMode.LIVE_MODEL_SUCCEEDED
    assert snapshot.provider_outcome is ProviderOutcome.SUCCEEDED
    assert snapshot.provider_egress_occurred is True
    assert snapshot.configured_provider == "deepseek"
    assert snapshot.configured_model == "deepseek-chat"
    assert snapshot.response_provider == "deepseek"
    assert snapshot.response_model == "deepseek-chat"
    assert snapshot.configured_runtime_matches_binding is True
    assert snapshot.prompt_tokens == 100
    assert snapshot.completion_tokens == 20
    assert snapshot.total_tokens == 120
    assert snapshot.estimated_cost_usd == pytest.approx(0.000032)
    assert snapshot.grounding_state is GroundingState.AUTHORITY_GROUNDED
    assert snapshot.evidence_ref_count == 1
    assert snapshot.verified_rule_ref_count == 1
    assert snapshot.source_snapshot_ref_count == 1
    assert snapshot.fresh_retrieval_provenance_present is False


def test_gemini_missing_generic_audit_model_recovers_exact_bound_model_only() -> None:
    output = {
        "summary": "live bounded Gemini output",
        "_llm_meta": {
            "provider": "gemini",
            "model": "gemini-3.7-flash",
            "finish_reason": "stop",
            "prompt_tokens": 100,
            "completion_tokens": 20,
            "total_tokens": 120,
            "estimated_cost_usd": None,
        },
    }
    snapshot = _evaluate(
        _agent_input(
            configured_provider="gemini",
            configured_model=None,
            bound_provider="gemini",
            bound_model="gemini-3.7-flash",
        ),
        output,
    )

    assert snapshot.execution_mode is ModelExecutionMode.LIVE_MODEL_SUCCEEDED
    assert snapshot.configured_provider == "gemini"
    assert snapshot.configured_model == "gemini-3.7-flash"
    assert snapshot.response_provider == "gemini"
    assert snapshot.response_model == "gemini-3.7-flash"
    assert snapshot.configured_runtime_matches_binding is True
    assert snapshot.estimated_cost_usd is None
    assert (
        "Gemini configured model provenance recovered from exact K.1 bound runtime"
        in snapshot.warnings
    )


def test_missing_generic_audit_model_is_not_recovered_for_other_providers() -> None:
    output = {
        "summary": "live bounded output",
        "_llm_meta": {
            "provider": "deepseek",
            "model": "deepseek-chat",
        },
    }
    snapshot = _evaluate(
        _agent_input(
            configured_provider="deepseek",
            configured_model=None,
            bound_provider="deepseek",
            bound_model="deepseek-chat",
        ),
        output,
    )

    assert snapshot.configured_model is None
    assert snapshot.configured_runtime_matches_binding is False
    assert (
        "configured LLM provider/model does not match the bound runtime profile"
        in snapshot.warnings
    )


@pytest.mark.parametrize(
    ("reason", "expected_outcome", "expected_egress"),
    [
        (
            "LLMProviderConfigurationError: deepseek API key is not configured.",
            ProviderOutcome.CONFIGURATION_OR_BINDING_FAILURE,
            False,
        ),
        (
            "LLMProviderTransportError: deepseek API request failed: timeout",
            ProviderOutcome.PROVIDER_TRANSPORT_FAILURE,
            True,
        ),
        (
            "LLMProviderResponseContractError: Unexpected deepseek response structure",
            ProviderOutcome.PROVIDER_RESPONSE_CONTRACT_FAILURE,
            True,
        ),
        (
            "RuntimeError: unexpected local adapter failure",
            ProviderOutcome.UNCLASSIFIED_FAILURE,
            None,
        ),
    ],
)
def test_live_model_fallback_is_classified_without_granting_authority(
    reason: str,
    expected_outcome: ProviderOutcome,
    expected_egress: bool | None,
) -> None:
    output = {
        "summary": "deterministic fallback output",
        "_llm_meta": {
            "provider": "deepseek",
            "fallback_reason": reason,
            "fallback_to_template": True,
        },
    }
    snapshot = _evaluate(
        _agent_input(
            configured_provider="deepseek",
            configured_model="deepseek-chat",
        ),
        output,
    )

    assert snapshot.execution_mode is ModelExecutionMode.LIVE_MODEL_FALLBACK
    assert snapshot.provider_outcome is expected_outcome
    assert snapshot.provider_egress_occurred is expected_egress
    assert snapshot.fallback_to_template is True
    assert snapshot.provider_model_authority is False
    assert f"provider fallback: {expected_outcome.value}" in snapshot.warnings


def test_runtime_binding_mismatch_is_observed_not_authorized() -> None:
    output = {
        "summary": "live bounded output",
        "_llm_meta": {
            "provider": "moonshot",
            "model": "kimi-k1-5",
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15,
            "estimated_cost_usd": 0.0001,
        },
    }
    snapshot = _evaluate(
        _agent_input(
            configured_provider="moonshot",
            configured_model="kimi-k1-5",
            bound_provider="deepseek",
            bound_model="deepseek-chat",
        ),
        output,
    )

    assert snapshot.configured_runtime_matches_binding is False
    assert snapshot.provider_model_authority is False
    assert (
        "configured LLM provider/model does not match the bound runtime profile"
        in snapshot.warnings
    )


def test_partial_grounding_is_not_promoted_to_authority_grounded() -> None:
    snapshot = _evaluate(
        _agent_input(
            configured_provider=None,
            configured_model=None,
            grounding="partial",
        ),
        {"summary": "deterministic bounded output"},
    )

    assert snapshot.grounding_state is GroundingState.PARTIAL_GROUNDING
    assert "authority grounding is incomplete" in snapshot.warnings


def test_durable_controlled_output_must_match_agent_run_output() -> None:
    agent_input = _agent_input(
        configured_provider=None,
        configured_model=None,
    )
    with pytest.raises(
        AustriaMobilityRuntimeQualityError,
        match="durable K controlled output does not match the persisted AgentRun output",
    ):
        evaluate_austria_specialist_runtime_quality(
            agent_input_json=agent_input,
            agent_output_json=json.dumps({"summary": "canonical"}),
            durable_controlled_output={"summary": "tampered"},
        )


def test_successful_live_metadata_rejects_provider_conflict_and_invalid_usage() -> None:
    agent_input = _agent_input(
        configured_provider="deepseek",
        configured_model="deepseek-chat",
    )
    with pytest.raises(
        AustriaMobilityRuntimeQualityError,
        match="provider metadata conflicts",
    ):
        _evaluate(
            agent_input,
            {
                "_llm_meta": {
                    "provider": "moonshot",
                    "model": "deepseek-chat",
                }
            },
        )

    with pytest.raises(
        AustriaMobilityRuntimeQualityError,
        match="total_tokens must be a non-negative integer",
    ):
        _evaluate(
            agent_input,
            {
                "_llm_meta": {
                    "provider": "deepseek",
                    "model": "deepseek-chat",
                    "total_tokens": -1,
                }
            },
        )
