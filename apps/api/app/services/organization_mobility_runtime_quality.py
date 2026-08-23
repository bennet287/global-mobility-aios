from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any


AUSTRIA_MOBILITY_RUNTIME_QUALITY_CONTRACT_VERSION = "austria-mobility-runtime-quality.v1"


class AustriaMobilityRuntimeQualityError(RuntimeError):
    """Persisted K/AgentRun runtime-quality provenance is malformed or inconsistent."""


class ModelExecutionMode(str, Enum):
    DETERMINISTIC_TEMPLATE = "deterministic_template"
    LIVE_MODEL_SUCCEEDED = "live_model_succeeded"
    LIVE_MODEL_FALLBACK = "live_model_fallback"


class ProviderOutcome(str, Enum):
    NOT_INVOKED = "not_invoked"
    SUCCEEDED = "succeeded"
    CONFIGURATION_OR_BINDING_FAILURE = "configuration_or_binding_failure"
    PROVIDER_TRANSPORT_FAILURE = "provider_transport_failure"
    PROVIDER_RESPONSE_CONTRACT_FAILURE = "provider_response_contract_failure"
    UNCLASSIFIED_FAILURE = "unclassified_failure"


class GroundingState(str, Enum):
    AUTHORITY_GROUNDED = "authority_grounded"
    PARTIAL_GROUNDING = "partial_grounding"
    UNGROUNDED = "ungrounded"


@dataclass(frozen=True, slots=True)
class AustriaSpecialistRuntimeQualitySnapshot:
    contract_version: str
    execution_mode: ModelExecutionMode
    provider_outcome: ProviderOutcome
    configured_provider: str | None
    configured_model: str | None
    response_provider: str | None
    response_model: str | None
    configured_runtime_matches_binding: bool | None
    provider_egress_occurred: bool | None
    fallback_to_template: bool
    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None
    estimated_cost_usd: float | None
    grounding_state: GroundingState
    evidence_ref_count: int
    verified_rule_ref_count: int
    source_snapshot_ref_count: int
    fresh_retrieval_provenance_present: bool
    provider_model_authority: bool
    warnings: tuple[str, ...]


def _json_object(value: str | None, *, label: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value or "{}")
    except (TypeError, json.JSONDecodeError) as exc:
        raise AustriaMobilityRuntimeQualityError(f"{label} is invalid JSON") from exc
    if not isinstance(parsed, dict):
        raise AustriaMobilityRuntimeQualityError(f"{label} must be a JSON object")
    return parsed


def _optional_text(value: object, *, label: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise AustriaMobilityRuntimeQualityError(f"{label} must be a non-empty string or null")
    return value.strip()


def _optional_nonnegative_int(value: object, *, label: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise AustriaMobilityRuntimeQualityError(f"{label} must be a non-negative integer or null")
    return value


def _optional_nonnegative_float(value: object, *, label: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or float(value) < 0:
        raise AustriaMobilityRuntimeQualityError(f"{label} must be a non-negative number or null")
    return float(value)


def _reference_count(value: object, *, label: str) -> int:
    if value is None:
        return 0
    if not isinstance(value, list):
        raise AustriaMobilityRuntimeQualityError(f"{label} must be a list")
    seen: set[tuple[str, str, str | None]] = set()
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise AustriaMobilityRuntimeQualityError(f"{label}[{index}] must be an object")
        kind = _optional_text(item.get("kind"), label=f"{label}[{index}].kind")
        identifier = _optional_text(
            item.get("identifier"), label=f"{label}[{index}].identifier"
        )
        version = _optional_text(item.get("version"), label=f"{label}[{index}].version")
        if kind is None or identifier is None:
            raise AustriaMobilityRuntimeQualityError(
                f"{label}[{index}] requires non-empty kind and identifier"
            )
        key = (kind, identifier, version)
        if key in seen:
            raise AustriaMobilityRuntimeQualityError(f"{label} contains a duplicate reference")
        seen.add(key)
    return len(seen)


def _fallback_outcome(reason: str) -> tuple[ProviderOutcome, bool | None]:
    error_type = reason.split(":", 1)[0].strip()
    if error_type == "LLMProviderConfigurationError":
        return ProviderOutcome.CONFIGURATION_OR_BINDING_FAILURE, False
    if error_type == "LLMProviderTransportError":
        return ProviderOutcome.PROVIDER_TRANSPORT_FAILURE, True
    if error_type == "LLMProviderResponseContractError":
        return ProviderOutcome.PROVIDER_RESPONSE_CONTRACT_FAILURE, True
    return ProviderOutcome.UNCLASSIFIED_FAILURE, None


def _binding_match(
    *,
    configured_provider: str | None,
    configured_model: str | None,
    bound_provider: str | None,
    bound_model: str | None,
) -> bool | None:
    if configured_provider is None and configured_model is None:
        return None
    if configured_provider is None or configured_model is None:
        return False
    if bound_provider is None or bound_model is None:
        return False
    return configured_provider.casefold() == bound_provider.casefold() and configured_model == bound_model


def evaluate_austria_specialist_runtime_quality(
    *,
    agent_input_json: str,
    agent_output_json: str,
    durable_controlled_output: object,
) -> AustriaSpecialistRuntimeQualitySnapshot:
    """Compile a non-authorizing L runtime-quality view from already-durable K/AgentRun data.

    This function performs no provider call and no retrieval. It intentionally distinguishes
    persisted authority grounding from fresh retrieval provenance. K.1 currently persists
    Evidence/VerifiedRule/SourceSnapshot references, but does not persist a SourceRetrievalRun
    reference; therefore this v1 contract never claims that fresh retrieval occurred.
    """

    agent_input = _json_object(agent_input_json, label="AgentRun input")
    agent_output = _json_object(agent_output_json, label="AgentRun output")
    if durable_controlled_output != agent_output:
        raise AustriaMobilityRuntimeQualityError(
            "durable K controlled output does not match the persisted AgentRun output"
        )

    run_context = agent_input.get("context")
    provenance = run_context.get("k1_provenance") if isinstance(run_context, dict) else None
    if not isinstance(provenance, dict):
        raise AustriaMobilityRuntimeQualityError("AgentRun lacks K.1 provenance")

    bound_provider = _optional_text(
        provenance.get("provider_key"), label="K.1 runtime provider_key"
    )
    bound_model = _optional_text(provenance.get("model_key"), label="K.1 runtime model_key")
    if provenance.get("provider_model_authority") is not False:
        raise AustriaMobilityRuntimeQualityError(
            "K.1 runtime provenance must explicitly deny provider/model authority"
        )

    configured_provider = _optional_text(
        agent_input.get("llm_provider"), label="AgentRun llm_provider"
    )
    configured_model = _optional_text(agent_input.get("llm_model"), label="AgentRun llm_model")
    configured_match = _binding_match(
        configured_provider=configured_provider,
        configured_model=configured_model,
        bound_provider=bound_provider,
        bound_model=bound_model,
    )

    evidence_count = _reference_count(
        provenance.get("context_evidence_refs"), label="K.1 context_evidence_refs"
    )
    rule_count = _reference_count(
        provenance.get("context_verified_rule_refs"), label="K.1 context_verified_rule_refs"
    )
    snapshot_count = _reference_count(
        provenance.get("context_source_snapshot_refs"),
        label="K.1 context_source_snapshot_refs",
    )
    grounding_presence = (evidence_count > 0, rule_count > 0, snapshot_count > 0)
    if all(grounding_presence):
        grounding_state = GroundingState.AUTHORITY_GROUNDED
    elif any(grounding_presence):
        grounding_state = GroundingState.PARTIAL_GROUNDING
    else:
        grounding_state = GroundingState.UNGROUNDED

    meta = agent_output.get("_llm_meta")
    warnings: list[str] = []
    response_provider: str | None = None
    response_model: str | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    estimated_cost_usd: float | None = None

    if meta is None:
        execution_mode = ModelExecutionMode.DETERMINISTIC_TEMPLATE
        provider_outcome = ProviderOutcome.NOT_INVOKED
        provider_egress_occurred: bool | None = False
        fallback_to_template = False
    else:
        if not isinstance(meta, dict):
            raise AustriaMobilityRuntimeQualityError("AgentRun _llm_meta must be an object")
        fallback_to_template = meta.get("fallback_to_template") is True
        meta_provider = _optional_text(meta.get("provider"), label="_llm_meta.provider")
        if meta_provider is not None and configured_provider is not None:
            if meta_provider.casefold() != configured_provider.casefold():
                raise AustriaMobilityRuntimeQualityError(
                    "AgentRun provider metadata conflicts with configured provider provenance"
                )

        if fallback_to_template:
            execution_mode = ModelExecutionMode.LIVE_MODEL_FALLBACK
            reason = _optional_text(
                meta.get("fallback_reason"), label="_llm_meta.fallback_reason"
            )
            if reason is None:
                raise AustriaMobilityRuntimeQualityError(
                    "fallback metadata requires a fallback_reason"
                )
            provider_outcome, provider_egress_occurred = _fallback_outcome(reason)
            warnings.append(f"provider fallback: {provider_outcome.value}")
        else:
            execution_mode = ModelExecutionMode.LIVE_MODEL_SUCCEEDED
            provider_outcome = ProviderOutcome.SUCCEEDED
            provider_egress_occurred = True
            response_provider = meta_provider
            response_model = _optional_text(meta.get("model"), label="_llm_meta.model")
            if response_provider is None or response_model is None:
                raise AustriaMobilityRuntimeQualityError(
                    "successful live-model metadata requires provider and model"
                )
            prompt_tokens = _optional_nonnegative_int(
                meta.get("prompt_tokens"), label="_llm_meta.prompt_tokens"
            )
            completion_tokens = _optional_nonnegative_int(
                meta.get("completion_tokens"), label="_llm_meta.completion_tokens"
            )
            total_tokens = _optional_nonnegative_int(
                meta.get("total_tokens"), label="_llm_meta.total_tokens"
            )
            estimated_cost_usd = _optional_nonnegative_float(
                meta.get("estimated_cost_usd"), label="_llm_meta.estimated_cost_usd"
            )

    if configured_match is False:
        warnings.append("configured LLM provider/model does not match the bound runtime profile")
    if grounding_state is GroundingState.PARTIAL_GROUNDING:
        warnings.append("authority grounding is incomplete")
    elif grounding_state is GroundingState.UNGROUNDED:
        warnings.append("no persisted authority grounding was consumed")
    warnings.append("fresh retrieval provenance is not present in the K.1 execution contract")

    return AustriaSpecialistRuntimeQualitySnapshot(
        contract_version=AUSTRIA_MOBILITY_RUNTIME_QUALITY_CONTRACT_VERSION,
        execution_mode=execution_mode,
        provider_outcome=provider_outcome,
        configured_provider=configured_provider,
        configured_model=configured_model,
        response_provider=response_provider,
        response_model=response_model,
        configured_runtime_matches_binding=configured_match,
        provider_egress_occurred=provider_egress_occurred,
        fallback_to_template=fallback_to_template,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        estimated_cost_usd=estimated_cost_usd,
        grounding_state=grounding_state,
        evidence_ref_count=evidence_count,
        verified_rule_ref_count=rule_count,
        source_snapshot_ref_count=snapshot_count,
        fresh_retrieval_provenance_present=False,
        provider_model_authority=False,
        warnings=tuple(warnings),
    )
