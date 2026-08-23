from __future__ import annotations

import json
from dataclasses import dataclass
from uuid import UUID

from sqlmodel import Session, select

from app.core.config import settings
from app.models.domain import AgentRun, OrganizationalActionOutput, OrganizationalWorkItem
from app.services.organization_agent_runtime import AgentRuntimeProfile, RuntimeClass
from app.services.organization_command import DependencyConflict, system_bound_agent_command_context
from app.services.organization_mobility_objective_execution import (
    AustriaSpecialistExecutionResult,
    execute_austria_specialists,
)
from app.services.organization_mobility_objective_runtime import (
    AUSTRIA_MOBILITY_OBJECTIVE_OWNER_POSITION,
    AUSTRIA_MOBILITY_PATHWAY_POSITION,
    AUSTRIA_MOBILITY_REGULATORY_POSITION,
    AUSTRIA_MOBILITY_SPECIALIST_POSITIONS,
    AustriaMobilityObjectivePlan,
    austria_specialist_output_key,
)
from app.services.organization_mobility_runtime_quality import (
    AustriaMobilityRuntimeQualityError,
    GroundingState,
    ModelExecutionMode,
    ProviderOutcome,
    evaluate_austria_specialist_runtime_quality,
)


AUSTRIA_LIVE_PROVIDER_EVALUATION_CONTRACT_VERSION = "austria-live-provider-evaluation.v1"
LIVE_PROVIDER_RESPONSE_MODEL_MATCH_POLICY = "exact-v1"
_SUPPORTED_PROVIDER_MODELS = {
    "deepseek": ("deepseek_api_key", "deepseek_model"),
    "moonshot": ("moonshot_api_key", "moonshot_model"),
}
_DURABLE_PROVENANCE_FIELDS = (
    "contract_version",
    "root_work_item_id",
    "work_item_id",
    "position_key",
    "context_hash",
    "context_evidence_refs",
    "context_verified_rule_refs",
    "context_source_snapshot_refs",
    "runtime_binding_hash",
    "runtime_profile_key",
    "runtime_profile_version",
    "runtime_profile_fingerprint",
    "runtime_class",
    "adapter_key",
    "provider_key",
    "model_key",
    "provider_model_authority",
    "allowed_tools",
    "execution_attempt_id",
    "execution_token",
)


@dataclass(frozen=True, slots=True)
class AustriaLiveProviderSelection:
    provider_key: str
    model_key: str


@dataclass(frozen=True, slots=True)
class AustriaLiveProviderSpecialistEvaluation:
    position_key: str
    work_item_id: UUID
    execution_attempt_id: UUID
    agent_run_id: UUID
    action_output_id: UUID
    latency_ms: int
    retry_count: int
    replayed: bool
    execution_mode: str
    provider_outcome: str
    configured_provider: str | None
    configured_model: str | None
    response_provider: str | None
    response_model: str | None
    configured_runtime_matches_binding: bool | None
    provider_egress_occurred: bool | None
    fallback_to_template: bool
    grounding_state: str
    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None
    estimated_cost_usd: float | None
    fresh_retrieval_provenance_present: bool
    provider_model_authority: bool
    live_provider_succeeded: bool
    warnings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AustriaLiveProviderEvaluation:
    contract_version: str
    root_work_item_id: UUID
    objective_key: str
    provider_key: str
    model_key: str
    specialist_evaluations: tuple[AustriaLiveProviderSpecialistEvaluation, ...]
    live_provider_success_count: int
    provider_failure_count: int
    configured_selection_matches_all_specialists: bool
    all_specialists_live_provider_succeeded: bool
    all_specialists_authority_grounded: bool
    fresh_retrieval_provenance_complete: bool
    live_provider_acceptance_candidate: bool
    full_l_reasoning_evidence_candidate: bool
    provider_model_authority: bool
    external_action_authorized: bool


def _json_object(value: str | None, *, label: str) -> dict[str, object]:
    try:
        parsed = json.loads(value or "{}")
    except (TypeError, json.JSONDecodeError) as exc:
        raise DependencyConflict(f"{label} is invalid JSON") from exc
    if not isinstance(parsed, dict):
        raise DependencyConflict(f"{label} must be a JSON object")
    return parsed


def configured_live_provider_selection(*, require_api_key: bool) -> AustriaLiveProviderSelection:
    provider = (settings.llm_provider or "").strip().casefold()
    config_fields = _SUPPORTED_PROVIDER_MODELS.get(provider)
    if config_fields is None:
        available = ", ".join(sorted(_SUPPORTED_PROVIDER_MODELS))
        raise DependencyConflict(
            f"live-provider evaluation requires one configured provider ({available})"
        )
    api_key_field, model_field = config_fields
    model = str(getattr(settings, model_field, "") or "").strip()
    if not model:
        raise DependencyConflict(f"configured {provider} model is unavailable")
    if require_api_key and not str(getattr(settings, api_key_field, "") or "").strip():
        raise DependencyConflict(f"configured {provider} API key is unavailable")
    return AustriaLiveProviderSelection(provider_key=provider, model_key=model)


def live_provider_runtime_profiles(
    selection: AustriaLiveProviderSelection,
) -> dict[str, AgentRuntimeProfile]:
    return {
        position_key: AgentRuntimeProfile(
            profile_key=f"l-live-provider-evaluation-{position_key}",
            runtime_class=RuntimeClass.HOSTED_API,
            adapter_key=f"{selection.provider_key}-chat-completions",
            provider_key=selection.provider_key,
            model_key=selection.model_key,
            technical_capabilities=("reasoning", "structured_output"),
            available_tools=(),
            independence_group=f"provider:{selection.provider_key}",
            profile_version=1,
            enabled=True,
        )
        for position_key in AUSTRIA_MOBILITY_SPECIALIST_POSITIONS
    }


def load_austria_mobility_objective_plan(
    session: Session,
    *,
    tenant_key: str,
    root_work_item_id: UUID,
) -> AustriaMobilityObjectivePlan:
    root = session.exec(
        select(OrganizationalWorkItem).where(
            OrganizationalWorkItem.id == root_work_item_id,
            OrganizationalWorkItem.tenant_key == tenant_key,
        )
    ).first()
    if root is None:
        raise DependencyConflict("Austria mobility objective root was not found")
    if (
        root.assigned_position_key != AUSTRIA_MOBILITY_OBJECTIVE_OWNER_POSITION
        or root.work_type != "mobility_objective"
        or root.phase_key != "J.1"
        or not root.objective_key
    ):
        raise DependencyConflict("work item is not the canonical Austria mobility objective root")

    children = list(
        session.exec(
            select(OrganizationalWorkItem).where(
                OrganizationalWorkItem.tenant_key == tenant_key,
                OrganizationalWorkItem.parent_work_item_id == root.id,
            )
        ).all()
    )
    expected_phase = {
        AUSTRIA_MOBILITY_PATHWAY_POSITION: "J.1.pathway",
        AUSTRIA_MOBILITY_REGULATORY_POSITION: "J.1.regulatory",
    }
    resolved: dict[str, OrganizationalWorkItem] = {}
    for position_key in AUSTRIA_MOBILITY_SPECIALIST_POSITIONS:
        matches = [item for item in children if item.assigned_position_key == position_key]
        if len(matches) != 1:
            raise DependencyConflict(
                f"{position_key} requires exactly one child WorkItem; found {len(matches)}"
            )
        child = matches[0]
        if (
            child.objective_key != root.objective_key
            or child.phase_key != expected_phase[position_key]
            or child.work_type != "mobility_specialist_work"
        ):
            raise DependencyConflict(
                f"{position_key} is outside the canonical Austria objective topology"
            )
        resolved[position_key] = child

    return AustriaMobilityObjectivePlan(
        root_work_item=root,
        pathway_work_item=resolved[AUSTRIA_MOBILITY_PATHWAY_POSITION],
        regulatory_work_item=resolved[AUSTRIA_MOBILITY_REGULATORY_POSITION],
    )


def _specialist_work(plan: AustriaMobilityObjectivePlan, position_key: str) -> OrganizationalWorkItem:
    if position_key == AUSTRIA_MOBILITY_PATHWAY_POSITION:
        return plan.pathway_work_item
    if position_key == AUSTRIA_MOBILITY_REGULATORY_POSITION:
        return plan.regulatory_work_item
    raise DependencyConflict(f"unsupported Austria specialist position: {position_key}")


def _require_fresh_live_execution_candidate(
    session: Session,
    plan: AustriaMobilityObjectivePlan,
) -> None:
    if plan.root_work_item.status in {"completed", "cancelled", "failed", "rejected", "returned"}:
        raise DependencyConflict("live-provider evaluation requires a non-terminal Austria objective")
    conflicts: list[str] = []
    for position_key in AUSTRIA_MOBILITY_SPECIALIST_POSITIONS:
        work = _specialist_work(plan, position_key)
        output_exists = session.exec(
            select(OrganizationalActionOutput.id).where(
                OrganizationalActionOutput.output_key == austria_specialist_output_key(work.id)
            )
        ).first() is not None
        if output_exists:
            conflicts.append(f"{position_key}:current_k1_output_exists")
        if work.status not in {"queued", "running"}:
            conflicts.append(f"{position_key}:status={work.status}")
        if work.execution_attempts >= work.max_execution_attempts:
            conflicts.append(f"{position_key}:execution_attempts_exhausted")
    if conflicts:
        raise DependencyConflict(
            "live-provider evaluation requires both specialists to be fresh executable candidates: "
            + ", ".join(conflicts)
        )


def _response_matches_configured_selection(quality) -> bool:
    """Fail closed unless the provider-reported identity exactly matches configured selection.

    No alias/version normalization is accepted yet. If a provider introduces a documented
    alias, that mapping must be reviewed and added explicitly rather than inferred here.
    """

    return (
        quality.configured_provider is not None
        and quality.configured_model is not None
        and quality.response_provider is not None
        and quality.response_model is not None
        and quality.response_provider.casefold() == quality.configured_provider.casefold()
        and quality.response_model == quality.configured_model
    )


def _specialist_evaluation(
    session: Session,
    result: AustriaSpecialistExecutionResult,
) -> AustriaLiveProviderSpecialistEvaluation:
    output = session.get(OrganizationalActionOutput, result.action_output_id)
    agent_run = session.get(AgentRun, result.agent_run_id)
    if output is None or agent_run is None:
        raise DependencyConflict(
            f"{result.position_key} live-provider evaluation lineage is unavailable"
        )
    if (
        output.work_item_id != result.work_item_id
        or output.accountable_position_key != result.position_key
        or output.status != "completed"
    ):
        raise DependencyConflict(
            f"{result.position_key} live-provider evaluation output lineage is invalid"
        )

    payload = _json_object(
        output.output_json,
        label=f"{result.position_key} live-provider ActionOutput",
    )
    expected_retry_count = max(0, result.attempt_number - 1)
    if (
        payload.get("work_item_id") != str(result.work_item_id)
        or payload.get("position_key") != result.position_key
        or payload.get("execution_attempt_id") != str(result.execution_attempt_id)
        or payload.get("agent_run_id") != str(result.agent_run_id)
        or payload.get("agent_run_id") != str(agent_run.id)
        or payload.get("attempt_number") != result.attempt_number
        or payload.get("latency_ms") != result.latency_ms
        or payload.get("retry_count") != expected_retry_count
    ):
        raise DependencyConflict(
            f"{result.position_key} live-provider execution identifiers/metrics diverged"
        )

    agent_input = _json_object(
        agent_run.input_json,
        label=f"{result.position_key} live-provider AgentRun input",
    )
    run_context = agent_input.get("context")
    provenance = run_context.get("k1_provenance") if isinstance(run_context, dict) else None
    if not isinstance(provenance, dict):
        raise DependencyConflict(
            f"{result.position_key} live-provider AgentRun lacks K.1 provenance"
        )
    for field in _DURABLE_PROVENANCE_FIELDS:
        if payload.get(field) != provenance.get(field):
            raise DependencyConflict(
                f"{result.position_key} live-provider ActionOutput/AgentRun provenance diverged"
            )

    controlled_output = payload.get("controlled_output")
    if not isinstance(controlled_output, dict):
        raise DependencyConflict(
            f"{result.position_key} live-provider evaluation lacks controlled output"
        )
    try:
        quality = evaluate_austria_specialist_runtime_quality(
            agent_input_json=agent_run.input_json,
            agent_output_json=agent_run.output_json,
            durable_controlled_output=controlled_output,
        )
    except AustriaMobilityRuntimeQualityError as exc:
        raise DependencyConflict(
            f"{result.position_key} live-provider runtime-quality provenance is inconsistent"
        ) from exc

    response_selection_matches = _response_matches_configured_selection(quality)
    live_provider_succeeded = (
        quality.execution_mode is ModelExecutionMode.LIVE_MODEL_SUCCEEDED
        and quality.provider_outcome is ProviderOutcome.SUCCEEDED
        and quality.configured_runtime_matches_binding is True
        and quality.provider_egress_occurred is True
        and quality.fallback_to_template is False
        and quality.provider_model_authority is False
        and response_selection_matches
    )
    warnings = quality.warnings
    if quality.execution_mode is ModelExecutionMode.LIVE_MODEL_SUCCEEDED and not response_selection_matches:
        warnings = (
            *warnings,
            "provider response identity does not satisfy exact configured provider/model match policy",
        )
    return AustriaLiveProviderSpecialistEvaluation(
        position_key=result.position_key,
        work_item_id=result.work_item_id,
        execution_attempt_id=result.execution_attempt_id,
        agent_run_id=result.agent_run_id,
        action_output_id=result.action_output_id,
        latency_ms=result.latency_ms,
        retry_count=expected_retry_count,
        replayed=result.replayed,
        execution_mode=quality.execution_mode.value,
        provider_outcome=quality.provider_outcome.value,
        configured_provider=quality.configured_provider,
        configured_model=quality.configured_model,
        response_provider=quality.response_provider,
        response_model=quality.response_model,
        configured_runtime_matches_binding=quality.configured_runtime_matches_binding,
        provider_egress_occurred=quality.provider_egress_occurred,
        fallback_to_template=quality.fallback_to_template,
        grounding_state=quality.grounding_state.value,
        prompt_tokens=quality.prompt_tokens,
        completion_tokens=quality.completion_tokens,
        total_tokens=quality.total_tokens,
        estimated_cost_usd=quality.estimated_cost_usd,
        fresh_retrieval_provenance_present=quality.fresh_retrieval_provenance_present,
        provider_model_authority=quality.provider_model_authority,
        live_provider_succeeded=live_provider_succeeded,
        warnings=warnings,
    )


def compile_austria_live_provider_evaluation(
    session: Session,
    *,
    plan: AustriaMobilityObjectivePlan,
    selection: AustriaLiveProviderSelection,
    results: tuple[AustriaSpecialistExecutionResult, ...],
) -> AustriaLiveProviderEvaluation:
    by_position = {result.position_key: result for result in results}
    if set(by_position) != set(AUSTRIA_MOBILITY_SPECIALIST_POSITIONS):
        raise DependencyConflict("live-provider evaluation requires both Austria specialists")
    specialist_evaluations = tuple(
        _specialist_evaluation(session, by_position[position_key])
        for position_key in AUSTRIA_MOBILITY_SPECIALIST_POSITIONS
    )
    live_success_count = sum(item.live_provider_succeeded for item in specialist_evaluations)
    provider_failure_count = sum(
        item.provider_outcome
        not in {ProviderOutcome.SUCCEEDED.value, ProviderOutcome.NOT_INVOKED.value}
        for item in specialist_evaluations
    )
    selection_matches = all(
        item.configured_provider is not None
        and item.configured_provider.casefold() == selection.provider_key.casefold()
        and item.configured_model == selection.model_key
        and item.response_provider is not None
        and item.response_provider.casefold() == selection.provider_key.casefold()
        and item.response_model == selection.model_key
        for item in specialist_evaluations
    )
    all_live = (
        live_success_count == len(AUSTRIA_MOBILITY_SPECIALIST_POSITIONS)
        and selection_matches
    )
    all_grounded = all(
        item.grounding_state == GroundingState.AUTHORITY_GROUNDED.value
        for item in specialist_evaluations
    )
    fresh_complete = all(
        item.fresh_retrieval_provenance_present for item in specialist_evaluations
    )
    return AustriaLiveProviderEvaluation(
        contract_version=AUSTRIA_LIVE_PROVIDER_EVALUATION_CONTRACT_VERSION,
        root_work_item_id=plan.root_work_item.id,
        objective_key=plan.root_work_item.objective_key or "",
        provider_key=selection.provider_key,
        model_key=selection.model_key,
        specialist_evaluations=specialist_evaluations,
        live_provider_success_count=live_success_count,
        provider_failure_count=provider_failure_count,
        configured_selection_matches_all_specialists=selection_matches,
        all_specialists_live_provider_succeeded=all_live,
        all_specialists_authority_grounded=all_grounded,
        fresh_retrieval_provenance_complete=fresh_complete,
        live_provider_acceptance_candidate=all_live and all_grounded,
        full_l_reasoning_evidence_candidate=all_live and all_grounded and fresh_complete,
        provider_model_authority=False,
        external_action_authorized=False,
    )


def execute_austria_live_provider_evaluation(
    session: Session,
    *,
    tenant_key: str,
    root_work_item_id: UUID,
    actor: str = "l-live-provider-evaluation",
) -> AustriaLiveProviderEvaluation:
    if settings.llm_fallback_to_template:
        raise DependencyConflict(
            "live-provider acceptance execution requires llm_fallback_to_template=false"
        )
    selection = configured_live_provider_selection(require_api_key=True)
    plan = load_austria_mobility_objective_plan(
        session,
        tenant_key=tenant_key,
        root_work_item_id=root_work_item_id,
    )
    _require_fresh_live_execution_candidate(session, plan)
    context = system_bound_agent_command_context(
        tenant_key=tenant_key,
        position_key=AUSTRIA_MOBILITY_OBJECTIVE_OWNER_POSITION,
        department=plan.root_work_item.department,
        authority_level=plan.root_work_item.authority_level,
        correlation_key=f"l-live-provider-evaluation:{root_work_item_id}",
    )
    results = execute_austria_specialists(
        session,
        context,
        plan,
        runtime_profiles=live_provider_runtime_profiles(selection),
        actor=actor,
    )
    return compile_austria_live_provider_evaluation(
        session,
        plan=plan,
        selection=selection,
        results=results,
    )
