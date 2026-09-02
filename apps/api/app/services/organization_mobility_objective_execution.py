from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Mapping
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    AgentRun,
    OrganizationExecutionAttempt,
    OrganizationalActionOutput,
    OrganizationalWorkItem,
    now_utc,
)
from app.schemas import ControlledAgentRunRequest
from app.services.audit_log import record_audit
from app.services.controlled_agents import run_controlled_agent
from app.services.organization_agent_runtime import (
    AgentRuntimeProfile,
    RuntimeBindingStale,
    bind_employee_runtime,
    runtime_profile_fingerprint,
)
from app.services.organization_command import (
    DependencyConflict,
    InvalidTransition,
    OrganizationCommandContext,
    canonical_fingerprint,
)
from app.services.organization_context_broker import (
    ContextPurpose,
    ContextReference,
    build_work_item_context_bundle,
)
from app.services.organization_mobility_objective_runtime import (
    AUSTRIA_MOBILITY_PATHWAY_POSITION,
    AUSTRIA_MOBILITY_REGULATORY_POSITION,
    AUSTRIA_MOBILITY_SPECIALIST_AGENT_NAMES,
    AUSTRIA_MOBILITY_SPECIALIST_EXECUTION_CONTRACT_VERSION,
    AUSTRIA_MOBILITY_SPECIALIST_POSITIONS,
    AustriaMobilityObjectivePlan,
    AustriaSpecialistRuntimeBinding,
    austria_completed_work_fingerprint,
    austria_specialist_output_key,
)
from app.services.organization_work import complete_work_item, start_work_item


SOURCE = "austria_mobility_k1_v1"
_REQUIRED_BLOCKED_EXTERNAL_ACTIONS = frozenset(
    {
        "authority_submission",
        "case_status_change",
        "client_send",
        "contract_signing",
        "external_provider_action",
        "payment_initiation",
        "policy_publication",
        "production_mutation",
    }
)
_GOVERNANCE_CHECKS = (
    "canonical_objective_topology",
    "current_context_hash",
    "runtime_binding_revalidation",
    "controlled_agent_guardrails",
    "durable_execution_provenance",
)


@dataclass(frozen=True, slots=True)
class AustriaSpecialistExecutionResult:
    position_key: str
    work_item_id: UUID
    context_hash: str
    runtime_binding_hash: str
    execution_attempt_id: UUID
    agent_run_id: UUID
    action_output_id: UUID
    attempt_number: int
    latency_ms: int
    replayed: bool


def _json_dump(value: object) -> str:
    return json.dumps(value, default=str, sort_keys=True, separators=(",", ":"))


def _json_object(value: str | None, *, label: str) -> dict[str, object]:
    try:
        parsed = json.loads(value or "{}")
    except json.JSONDecodeError as exc:
        raise DependencyConflict(f"{label} is invalid JSON") from exc
    if not isinstance(parsed, dict):
        raise DependencyConflict(f"{label} must be a JSON object")
    return parsed


def _context_reference_payloads(
    references: tuple[ContextReference, ...],
) -> list[dict[str, str]]:
    """Serialize the exact normalized ContextBundle authority references consumed by K.1."""

    payloads: list[dict[str, str]] = []
    for reference in references:
        payload = {
            "kind": reference.kind,
            "identifier": reference.identifier,
        }
        if reference.version is not None:
            payload["version"] = reference.version
        payloads.append(payload)
    return payloads


def _plan_work_id(plan: AustriaMobilityObjectivePlan, position_key: str) -> UUID:
    if position_key == AUSTRIA_MOBILITY_PATHWAY_POSITION:
        return plan.pathway_work_item.id
    if position_key == AUSTRIA_MOBILITY_REGULATORY_POSITION:
        return plan.regulatory_work_item.id
    raise DependencyConflict(f"unsupported Austria specialist position: {position_key}")


def _canonical_work(
    session: Session,
    plan: AustriaMobilityObjectivePlan,
    *,
    position_key: str,
) -> tuple[OrganizationalWorkItem, OrganizationalWorkItem]:
    root = session.get(OrganizationalWorkItem, plan.root_work_item.id)
    work = session.get(OrganizationalWorkItem, _plan_work_id(plan, position_key))
    if root is None or work is None:
        raise DependencyConflict("Austria objective or specialist WorkItem is unavailable")
    if root.tenant_key != work.tenant_key:
        raise DependencyConflict("Austria objective and specialist WorkItem cross tenant boundaries")
    expected_phase = {
        AUSTRIA_MOBILITY_PATHWAY_POSITION: "J.1.pathway",
        AUSTRIA_MOBILITY_REGULATORY_POSITION: "J.1.regulatory",
    }[position_key]
    if (
        work.parent_work_item_id != root.id
        or work.objective_key != root.objective_key
        or work.phase_key != expected_phase
        or work.work_type != "mobility_specialist_work"
        or work.assigned_position_key != position_key
    ):
        raise InvalidTransition(f"{position_key} work is outside the canonical Austria objective topology")
    return root, work


def _current_outputs(session: Session, work_item_id: UUID) -> list[OrganizationalActionOutput]:
    return list(
        session.exec(
            select(OrganizationalActionOutput).where(
                OrganizationalActionOutput.output_key == austria_specialist_output_key(work_item_id)
            )
        ).all()
    )


def _replay_result(
    session: Session,
    *,
    root: OrganizationalWorkItem,
    work: OrganizationalWorkItem,
    position_key: str,
    profile: AgentRuntimeProfile,
    output: OrganizationalActionOutput,
) -> AustriaSpecialistExecutionResult:
    if work.status != "completed":
        raise DependencyConflict("a K.1 durable output exists for specialist work that is not completed")
    if output.work_item_id != work.id or output.accountable_position_key != position_key:
        raise DependencyConflict("persisted K.1 output is bound to the wrong WorkItem or position")
    if output.status != "completed":
        raise DependencyConflict("persisted K.1 output is not completed")
    payload = _json_object(output.output_json, label="persisted K.1 output")
    if payload.get("contract_version") != AUSTRIA_MOBILITY_SPECIALIST_EXECUTION_CONTRACT_VERSION:
        raise DependencyConflict("persisted specialist output has the wrong K.1 contract version")
    if (
        payload.get("root_work_item_id") != str(root.id)
        or payload.get("work_item_id") != str(work.id)
        or payload.get("position_key") != position_key
    ):
        raise DependencyConflict("persisted specialist output has conflicting objective provenance")
    if payload.get("completed_work_fingerprint") != austria_completed_work_fingerprint(work):
        raise DependencyConflict("persisted specialist output is stale for the current completed WorkItem")
    if payload.get("runtime_profile_fingerprint") != runtime_profile_fingerprint(profile):
        raise DependencyConflict("exact K.1 replay requires the original technical runtime profile")
    if payload.get("agent_name") != AUSTRIA_MOBILITY_SPECIALIST_AGENT_NAMES[position_key]:
        raise DependencyConflict("persisted specialist output used the wrong controlled agent")

    try:
        agent_run_id = UUID(str(payload["agent_run_id"]))
        attempt_id = UUID(str(payload["execution_attempt_id"]))
    except (KeyError, ValueError) as exc:
        raise DependencyConflict("persisted specialist output lacks valid execution identifiers") from exc
    agent_run = session.get(AgentRun, agent_run_id)
    attempt = session.get(OrganizationExecutionAttempt, attempt_id)
    if agent_run is None or agent_run.agent_name != AUSTRIA_MOBILITY_SPECIALIST_AGENT_NAMES[position_key]:
        raise DependencyConflict("persisted K.1 AgentRun provenance is unavailable")
    if attempt is None or attempt.work_item_id != work.id or attempt.status != "completed":
        raise DependencyConflict("persisted K.1 execution-attempt provenance is unavailable")
    if attempt.execution_token != payload.get("execution_token"):
        raise DependencyConflict("persisted K.1 execution token does not match its attempt")

    return AustriaSpecialistExecutionResult(
        position_key=position_key,
        work_item_id=work.id,
        context_hash=str(payload["context_hash"]),
        runtime_binding_hash=str(payload["runtime_binding_hash"]),
        execution_attempt_id=attempt.id,
        agent_run_id=agent_run.id,
        action_output_id=output.id,
        attempt_number=int(payload.get("attempt_number") or attempt.attempt_number),
        latency_ms=int(payload.get("latency_ms") or 0),
        replayed=True,
    )


def _current_binding(
    session: Session,
    *,
    work: OrganizationalWorkItem,
    position_key: str,
    profile: AgentRuntimeProfile,
    expected_binding: AustriaSpecialistRuntimeBinding | None,
) -> AustriaSpecialistRuntimeBinding:
    context = build_work_item_context_bundle(
        session,
        tenant_key=work.tenant_key,
        position_key=position_key,
        work_item_id=work.id,
        purpose=ContextPurpose.COLLABORATION,
    )
    runtime = bind_employee_runtime(
        session,
        context=context,
        profile=profile,
        required_capability="reasoning",
    )
    current = AustriaSpecialistRuntimeBinding(
        position_key=position_key,
        work_item_id=work.id,
        context=context,
        runtime=runtime,
    )
    if expected_binding is not None and (
        expected_binding.position_key != current.position_key
        or expected_binding.work_item_id != current.work_item_id
        or expected_binding.context.context_hash != current.context.context_hash
        or expected_binding.runtime.context_hash != current.runtime.context_hash
        or expected_binding.runtime.binding_hash != current.runtime.binding_hash
    ):
        raise RuntimeBindingStale("supplied Austria specialist runtime binding is not current")
    return current


def _start_attempt(
    session: Session,
    *,
    work: OrganizationalWorkItem,
    binding: AustriaSpecialistRuntimeBinding,
    actor: str,
) -> OrganizationExecutionAttempt:
    if work.execution_attempts >= work.max_execution_attempts:
        raise InvalidTransition("specialist WorkItem has exhausted its bounded execution attempts")
    attempt_number = work.execution_attempts + 1
    started_at = now_utc()
    execution_token = canonical_fingerprint(
        {
            "contract_version": AUSTRIA_MOBILITY_SPECIALIST_EXECUTION_CONTRACT_VERSION,
            "work_item_id": work.id,
            "attempt_number": attempt_number,
            "context_hash": binding.context.context_hash,
            "runtime_binding_hash": binding.runtime.binding_hash,
        }
    )
    attempt = OrganizationExecutionAttempt(
        attempt_key=f"k1:austria-attempt:{work.id}:{attempt_number}",
        work_item_id=work.id,
        attempt_number=attempt_number,
        execution_token=execution_token,
        actor=actor,
    )
    work.execution_attempts = attempt_number
    work.execution_token = execution_token
    work.execution_started_at = started_at
    work.last_error = None
    work.updated_at = started_at
    session.add(work)
    session.add(attempt)
    record_audit(
        session,
        action="austria_specialist_execution_started",
        entity_type="organizational_work_item",
        entity_id=work.id,
        after_state={
            "position_key": binding.position_key,
            "attempt_number": attempt_number,
            "context_hash": binding.context.context_hash,
            "runtime_binding_hash": binding.runtime.binding_hash,
            "external_action_authorized": False,
        },
        actor=actor,
        source=SOURCE,
    )
    session.commit()
    session.refresh(attempt)
    session.refresh(work)
    return attempt


def _mark_attempt_failed(
    session: Session,
    *,
    work_item_id: UUID,
    attempt_id: UUID,
    error: Exception,
) -> None:
    session.rollback()
    attempt = session.get(OrganizationExecutionAttempt, attempt_id)
    work = session.get(OrganizationalWorkItem, work_item_id)
    completed_at = now_utc()
    error_text = f"{type(error).__name__}: {error}"[:2000]
    if attempt is not None:
        attempt.status = "failed"
        attempt.completed_at = completed_at
        attempt.error = error_text
        session.add(attempt)
    if work is not None:
        work.execution_started_at = None
        work.last_error = error_text
        work.updated_at = completed_at
        session.add(work)
    session.commit()


def execute_austria_specialist_work(
    session: Session,
    context: OrganizationCommandContext,
    plan: AustriaMobilityObjectivePlan,
    *,
    position_key: str,
    runtime_profile: AgentRuntimeProfile,
    expected_binding: AustriaSpecialistRuntimeBinding | None = None,
    actor: str = "organization-worker",
) -> AustriaSpecialistExecutionResult:
    """Execute one J.1 specialist through the native controlled-agent path.

    The slice is internal-analysis-only. It re-resolves canonical context, revalidates the
    technical runtime binding, records a native OrganizationExecutionAttempt, invokes the
    existing controlled-agent runner, and persists exactly one stable current-work
    OrganizationalActionOutput. Provider/model identity is recorded as provenance but is
    never treated as organizational authority.
    """

    if position_key not in AUSTRIA_MOBILITY_SPECIALIST_POSITIONS:
        raise DependencyConflict(f"unsupported Austria specialist position: {position_key}")
    root, work = _canonical_work(session, plan, position_key=position_key)
    if context.tenant_key != work.tenant_key:
        raise DependencyConflict("execution context does not match the specialist tenant")

    outputs = _current_outputs(session, work.id)
    if len(outputs) > 1:
        raise DependencyConflict("multiple current K.1 outputs exist for one specialist WorkItem")
    if len(outputs) == 1:
        return _replay_result(
            session,
            root=root,
            work=work,
            position_key=position_key,
            profile=runtime_profile,
            output=outputs[0],
        )
    if work.status == "completed":
        raise InvalidTransition("completed specialist WorkItem lacks current K.1 execution evidence")
    if work.status == "queued":
        work = start_work_item(
            session,
            context,
            work_item_id=work.id,
            reason=f"Start bounded K.1 execution for {position_key}.",
        )
    elif work.status != "running":
        raise InvalidTransition(f"specialist WorkItem is {work.status}, not executable by K.1")

    binding = _current_binding(
        session,
        work=work,
        position_key=position_key,
        profile=runtime_profile,
        expected_binding=expected_binding,
    )
    attempt = _start_attempt(session, work=work, binding=binding, actor=actor)
    run_started_at = now_utc()
    try:
        raw_context = _json_object(work.context_json, label="specialist WorkItem context")
        facts = dict(raw_context)
        facts.update(
            {
                "status": work.status,
                "work_item_id": str(work.id),
                "objective": work.objective,
                "position_key": position_key,
            }
        )
        context_reference_provenance = {
            "context_evidence_refs": _context_reference_payloads(binding.context.evidence_refs),
            "context_verified_rule_refs": _context_reference_payloads(
                binding.context.verified_rule_refs
            ),
            "context_source_snapshot_refs": _context_reference_payloads(
                binding.context.source_snapshot_refs
            ),
        }
        provenance = {
            "contract_version": AUSTRIA_MOBILITY_SPECIALIST_EXECUTION_CONTRACT_VERSION,
            "root_work_item_id": str(root.id),
            "work_item_id": str(work.id),
            "position_key": position_key,
            "context_hash": binding.context.context_hash,
            **context_reference_provenance,
            "runtime_binding_hash": binding.runtime.binding_hash,
            "runtime_profile_key": binding.runtime.runtime_profile_key,
            "runtime_profile_version": binding.runtime.runtime_profile_version,
            "runtime_profile_fingerprint": runtime_profile_fingerprint(runtime_profile),
            "runtime_class": binding.runtime.runtime_class.value,
            "adapter_key": binding.runtime.adapter_key,
            "provider_key": binding.runtime.provider_key,
            "model_key": binding.runtime.model_key,
            "provider_model_authority": False,
            "allowed_tools": list(binding.runtime.allowed_tools),
            "execution_attempt_id": str(attempt.id),
            "execution_token": attempt.execution_token,
        }
        response = run_controlled_agent(
            session,
            ControlledAgentRunRequest(
                agent_name=AUSTRIA_MOBILITY_SPECIALIST_AGENT_NAMES[position_key],
                task=work.objective,
                context={
                    "facts": facts,
                    "k1_provenance": provenance,
                },
                actor=actor,
            ),
        )
        run_completed_at = now_utc()
        latency_ms = max(0, int((run_completed_at - run_started_at).total_seconds() * 1000))

        controlled_output = response.output if isinstance(response.output, dict) else {}
        blocked_actions = sorted(
            _REQUIRED_BLOCKED_EXTERNAL_ACTIONS.union(
                str(item) for item in controlled_output.get("blocked_actions", [])
            )
        )
        raw_confidence = controlled_output.get("confidence")
        confidence = (
            max(0.0, min(1.0, float(raw_confidence)))
            if isinstance(raw_confidence, (int, float)) and not isinstance(raw_confidence, bool)
            else 0.5
        )
        output_payload: dict[str, object] = {
            **provenance,
            "agent_name": response.agent_name,
            "agent_run_id": str(response.run_id),
            "attempt_number": attempt.attempt_number,
            "latency_ms": latency_ms,
            "retry_count": max(0, attempt.attempt_number - 1),
            "governance_checks": list(_GOVERNANCE_CHECKS),
            "governance_check_count": len(_GOVERNANCE_CHECKS),
            "controlled_output": controlled_output,
            "completed_work_fingerprint": None,
        }
        evidence = [
            {
                "type": "organizational_work_item",
                "id": str(work.id),
                "root_work_item_id": str(root.id),
            },
            {
                "type": "context_bundle",
                "context_hash": binding.context.context_hash,
                "purpose": binding.context.purpose.value,
                **context_reference_provenance,
            },
            {
                "type": "runtime_binding",
                "binding_hash": binding.runtime.binding_hash,
                "profile_key": binding.runtime.runtime_profile_key,
                "profile_version": binding.runtime.runtime_profile_version,
                "provider_model_authority": False,
            },
            {
                "type": "organization_execution_attempt",
                "id": str(attempt.id),
                "execution_token": attempt.execution_token,
            },
            {
                "type": "agent_run",
                "id": str(response.run_id),
                "review_state": "human_review_required",
            },
        ]
        impact = {
            "client_facing": False,
            "external_action_authorized": False,
            "human_review_required": True,
            "workflow_effect": "internal_specialist_analysis_recorded",
            "blocked_actions": blocked_actions,
        }
        output = OrganizationalActionOutput(
            output_key=austria_specialist_output_key(work.id),
            work_item_id=work.id,
            accountable_position_key=position_key,
            authority_basis=(
                "K.1 bounded internal specialist analysis on canonical AIOS WorkItem/Context authority; "
                "provider/model identity is technical provenance only and non-authorizing."
            ),
            evidence_json=_json_dump(evidence),
            confidence=confidence,
            confidence_basis="Bounded controlled-agent confidence; output remains review-gated.",
            impact_json=_json_dump(impact),
            rollback_posture="Discard this internal output and rerun the bounded specialist WorkItem; no external side effect occurred.",
            output_json=_json_dump(output_payload),
            status="completed",
        )
        session.add(output)
        session.flush()

        attempt.status = "completed"
        attempt.completed_at = run_completed_at
        session.add(attempt)
        work.output_json = _json_dump(
            {
                "contract_version": AUSTRIA_MOBILITY_SPECIALIST_EXECUTION_CONTRACT_VERSION,
                "action_output_id": str(output.id),
                "agent_run_id": str(response.run_id),
            }
        )
        session.add(work)
        record_audit(
            session,
            action="austria_specialist_action_output_recorded",
            entity_type="organizational_action_output",
            entity_id=output.id,
            after_state={
                "work_item_id": str(work.id),
                "position_key": position_key,
                "agent_run_id": str(response.run_id),
                "execution_attempt_id": str(attempt.id),
                "context_hash": binding.context.context_hash,
                "runtime_binding_hash": binding.runtime.binding_hash,
                "external_action_authorized": False,
                "latency_ms": latency_ms,
                "retry_count": max(0, attempt.attempt_number - 1),
            },
            actor=actor,
            source=SOURCE,
        )
        completed_work = complete_work_item(
            session,
            context,
            work_item_id=work.id,
            reason=f"K.1 bounded controlled-agent execution completed for {position_key}.",
        )

        output = session.get(OrganizationalActionOutput, output.id)
        if output is None:
            raise DependencyConflict("K.1 action output disappeared after WorkItem completion")
        final_payload = _json_object(output.output_json, label="K.1 action output")
        final_payload["completed_work_fingerprint"] = austria_completed_work_fingerprint(completed_work)
        final_payload["work_completed_at"] = (
            completed_work.completed_at.isoformat() if completed_work.completed_at is not None else None
        )
        output.output_json = _json_dump(final_payload)
        output.updated_at = now_utc()
        completed_work.execution_started_at = None
        completed_work.last_error = None
        completed_work.updated_at = now_utc()
        session.add(output)
        session.add(completed_work)
        session.commit()
        session.refresh(output)
        session.refresh(completed_work)
        session.refresh(attempt)

        return AustriaSpecialistExecutionResult(
            position_key=position_key,
            work_item_id=work.id,
            context_hash=binding.context.context_hash,
            runtime_binding_hash=binding.runtime.binding_hash,
            execution_attempt_id=attempt.id,
            agent_run_id=response.run_id,
            action_output_id=output.id,
            attempt_number=attempt.attempt_number,
            latency_ms=latency_ms,
            replayed=False,
        )
    except Exception as exc:
        _mark_attempt_failed(
            session,
            work_item_id=work.id,
            attempt_id=attempt.id,
            error=exc,
        )
        raise


def execute_austria_specialists(
    session: Session,
    context: OrganizationCommandContext,
    plan: AustriaMobilityObjectivePlan,
    *,
    runtime_profiles: Mapping[str, AgentRuntimeProfile],
    actor: str = "organization-worker",
) -> tuple[AustriaSpecialistExecutionResult, ...]:
    """Execute/replay the complete two-specialist K.1 slice in canonical position order."""

    results: list[AustriaSpecialistExecutionResult] = []
    for position_key in AUSTRIA_MOBILITY_SPECIALIST_POSITIONS:
        profile = runtime_profiles.get(position_key)
        if profile is None:
            raise DependencyConflict(f"runtime profile is required for {position_key}")
        results.append(
            execute_austria_specialist_work(
                session,
                context,
                plan,
                position_key=position_key,
                runtime_profile=profile,
                actor=actor,
            )
        )
    return tuple(results)
