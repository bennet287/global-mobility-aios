from __future__ import annotations

import json
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
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
    runtime_profile_fingerprint,
)
from app.services.organization_command import (
    DependencyConflict,
    InvalidTransition,
    OrganizationCommandContext,
    canonical_fingerprint,
)
from app.services.organization_execution_heartbeat import (
    HEARTBEAT_STALE,
    claim_execution_runtime_session,
    current_execution_runtime_session,
    runtime_session_freshness_state,
)
from app.services.organization_mobility_objective_execution import (
    SOURCE,
    AustriaSpecialistExecutionResult,
    _canonical_work,
    _context_reference_payloads,
    _current_binding,
    _current_outputs,
    _json_dump,
    _json_object,
    _mark_attempt_failed,
)
from app.services.organization_mobility_objective_runtime import (
    AUSTRIA_MOBILITY_SPECIALIST_AGENT_NAMES,
    AUSTRIA_MOBILITY_SPECIALIST_EXECUTION_CONTRACT_VERSION,
    AUSTRIA_MOBILITY_SPECIALIST_POSITIONS,
    AustriaMobilityObjectivePlan,
    AustriaSpecialistRuntimeBinding,
    austria_completed_work_fingerprint,
    austria_specialist_output_key,
)
from app.services.organization_runtime_session_supervisor import (
    ExecutionRuntimeSessionSupervisor,
    stage_fenced_agent_completion,
)
from app.services.organization_work import complete_work_item


TAKEOVER_SOURCE = "austria_mobility_k1_takeover_resume_v1"
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
    "runtime_session_fencing",
    "stale_session_takeover",
)


def _execution_token_for(
    *,
    work: OrganizationalWorkItem,
    binding: AustriaSpecialistRuntimeBinding,
    attempt_number: int,
) -> str:
    return canonical_fingerprint(
        {
            "contract_version": AUSTRIA_MOBILITY_SPECIALIST_EXECUTION_CONTRACT_VERSION,
            "work_item_id": work.id,
            "attempt_number": attempt_number,
            "context_hash": binding.context.context_hash,
            "runtime_binding_hash": binding.runtime.binding_hash,
        }
    )


def _claim_resumable_attempt(
    session: Session,
    *,
    work: OrganizationalWorkItem,
    binding: AustriaSpecialistRuntimeBinding,
    execution_attempt_id: UUID,
    expected_execution_token: str,
    expected_previous_fence_token: int,
    actor: str,
) -> tuple[OrganizationExecutionAttempt, int]:
    if not actor.strip():
        raise ValueError("takeover resume actor is required")
    if not expected_execution_token.strip():
        raise ValueError("takeover resume execution token is required")
    if (
        not isinstance(expected_previous_fence_token, int)
        or isinstance(expected_previous_fence_token, bool)
        or expected_previous_fence_token < 1
    ):
        raise ValueError("takeover resume previous fence token must be a positive integer")

    if work.status != "running":
        raise InvalidTransition("takeover resume requires a running specialist WorkItem")
    attempt = session.get(OrganizationExecutionAttempt, execution_attempt_id)
    if attempt is None:
        raise DependencyConflict("takeover resume execution attempt was not found")
    if attempt.work_item_id != work.id:
        raise DependencyConflict("takeover resume execution attempt belongs to another WorkItem")
    if attempt.status != "running":
        raise InvalidTransition("takeover resume requires a running execution attempt")
    if attempt.attempt_number != work.execution_attempts:
        raise DependencyConflict("takeover resume requires the latest bounded execution attempt")
    if (
        not work.execution_token
        or work.execution_token != attempt.execution_token
        or attempt.execution_token != expected_execution_token
    ):
        raise DependencyConflict("takeover resume execution token conflicts with canonical work state")

    expected_current_token = _execution_token_for(
        work=work,
        binding=binding,
        attempt_number=attempt.attempt_number,
    )
    if expected_current_token != attempt.execution_token:
        raise RuntimeBindingStale(
            "takeover resume refused because context/runtime binding changed since the interrupted attempt"
        )

    running_attempts = list(
        session.exec(
            select(OrganizationExecutionAttempt).where(
                OrganizationExecutionAttempt.work_item_id == work.id,
                OrganizationExecutionAttempt.status == "running",
            )
        ).all()
    )
    if len(running_attempts) != 1 or running_attempts[0].id != attempt.id:
        raise DependencyConflict("takeover resume requires exactly one canonical running execution attempt")

    current = current_execution_runtime_session(
        session,
        tenant_key=work.tenant_key,
        work_item_id=work.id,
        execution_attempt_id=attempt.id,
        position_key=binding.position_key,
    )
    if current is None:
        raise DependencyConflict("takeover resume requires an established runtime session")
    if current.fence_token != expected_previous_fence_token:
        raise DependencyConflict("takeover resume caller observed a stale previous fence token")
    if runtime_session_freshness_state(current) != HEARTBEAT_STALE:
        raise InvalidTransition("takeover resume requires an expired runtime session")

    takeover = claim_execution_runtime_session(
        session,
        tenant_key=work.tenant_key,
        work_item_id=work.id,
        execution_attempt_id=attempt.id,
        position_key=binding.position_key,
        expected_execution_token=expected_execution_token,
        writer=actor,
    )
    if takeover.fence_token <= current.fence_token:
        raise DependencyConflict("takeover resume did not advance the runtime fencing generation")

    record_audit(
        session,
        action="austria_specialist_execution_takeover_claimed",
        entity_type="organization_execution_attempt",
        entity_id=attempt.id,
        after_state={
            "work_item_id": str(work.id),
            "position_key": binding.position_key,
            "attempt_number": attempt.attempt_number,
            "execution_token": attempt.execution_token,
            "previous_fence_token": current.fence_token,
            "runtime_fence_token": takeover.fence_token,
            "runtime_writer": actor,
            "external_action_authorized": False,
        },
        actor=actor,
        source=TAKEOVER_SOURCE,
    )
    session.commit()
    session.refresh(attempt)
    session.refresh(work)
    return attempt, takeover.fence_token


def resume_austria_specialist_work_with_takeover(
    session: Session,
    context: OrganizationCommandContext,
    plan: AustriaMobilityObjectivePlan,
    *,
    position_key: str,
    runtime_profile: AgentRuntimeProfile,
    execution_attempt_id: UUID,
    expected_execution_token: str,
    expected_previous_fence_token: int,
    expected_binding: AustriaSpecialistRuntimeBinding | None = None,
    actor: str,
) -> AustriaSpecialistExecutionResult:
    """Re-execute one interrupted K.1 specialist under a newly claimed stale-session fence.

    This entry point never creates a new OrganizationExecutionAttempt. It requires the
    caller to identify the exact running attempt, execution token, and previously observed
    fence. The current ContextBundle/runtime binding must still reproduce the interrupted
    attempt's execution token before a stale runtime session can be reclaimed.

    The resulting controlled-agent output remains internal, review-gated, and
    non-authorizing. A superseded worker cannot commit a late result because terminal
    completion is staged only against the newly claimed fence.
    """

    if position_key not in AUSTRIA_MOBILITY_SPECIALIST_POSITIONS:
        raise DependencyConflict(f"unsupported Austria specialist position: {position_key}")
    root, work = _canonical_work(session, plan, position_key=position_key)
    if context.tenant_key != work.tenant_key:
        raise DependencyConflict("takeover execution context does not match the specialist tenant")

    outputs = _current_outputs(session, work.id)
    if outputs:
        raise DependencyConflict("takeover resume refuses specialist work with a current K.1 output")
    if work.status != "running":
        raise InvalidTransition("takeover resume requires specialist work to remain running")

    binding = _current_binding(
        session,
        work=work,
        position_key=position_key,
        profile=runtime_profile,
        expected_binding=expected_binding,
    )
    attempt, runtime_fence_token = _claim_resumable_attempt(
        session,
        work=work,
        binding=binding,
        execution_attempt_id=execution_attempt_id,
        expected_execution_token=expected_execution_token,
        expected_previous_fence_token=expected_previous_fence_token,
        actor=actor,
    )

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
                "runtime_takeover_resume": True,
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
            "runtime_takeover_resume": True,
            "runtime_previous_fence_token": expected_previous_fence_token,
            "runtime_fence_token": runtime_fence_token,
        }

        with ExecutionRuntimeSessionSupervisor(
            tenant_key=work.tenant_key,
            work_item_id=work.id,
            execution_attempt_id=attempt.id,
            position_key=position_key,
            expected_execution_token=attempt.execution_token,
            expected_fence_token=runtime_fence_token,
            writer=actor,
        ) as runtime_supervisor:
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
        runtime_snapshot = runtime_supervisor.snapshot()
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
            "runtime_renewal_count": runtime_snapshot.renewal_count,
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
                "attempt_reused_after_takeover": True,
            },
            {
                "type": "execution_runtime_session",
                "previous_fence_token": expected_previous_fence_token,
                "fence_token": runtime_snapshot.fence_token,
                "writer": runtime_snapshot.writer,
                "renewal_count": runtime_snapshot.renewal_count,
                "takeover_resume": True,
                "authority_effect": False,
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
            "workflow_effect": "internal_specialist_analysis_recorded_after_runtime_takeover",
            "blocked_actions": blocked_actions,
        }
        output = OrganizationalActionOutput(
            output_key=austria_specialist_output_key(work.id),
            work_item_id=work.id,
            accountable_position_key=position_key,
            authority_basis=(
                "K.1 bounded internal specialist re-execution on the same canonical AIOS attempt "
                "after a fenced stale-session takeover; runtime health and provider/model identity "
                "remain technical provenance only and non-authorizing."
            ),
            evidence_json=_json_dump(evidence),
            confidence=confidence,
            confidence_basis="Bounded controlled-agent confidence; output remains review-gated.",
            impact_json=_json_dump(impact),
            rollback_posture=(
                "Discard this internal output and reopen through governed bounded execution; "
                "the takeover path performed no external side effect."
            ),
            output_json=_json_dump(output_payload),
            status="completed",
        )
        session.add(output)
        session.flush()

        stage_fenced_agent_completion(
            session,
            tenant_key=work.tenant_key,
            work=work,
            attempt=attempt,
            position_key=position_key,
            expected_execution_token=attempt.execution_token,
            expected_fence_token=runtime_snapshot.fence_token,
            writer=actor,
            observed_at=run_completed_at,
        )
        attempt.status = "completed"
        attempt.completed_at = run_completed_at
        session.add(attempt)
        work.output_json = _json_dump(
            {
                "contract_version": AUSTRIA_MOBILITY_SPECIALIST_EXECUTION_CONTRACT_VERSION,
                "action_output_id": str(output.id),
                "agent_run_id": str(response.run_id),
                "runtime_takeover_resume": True,
                "runtime_fence_token": runtime_snapshot.fence_token,
            }
        )
        session.add(work)
        record_audit(
            session,
            action="austria_specialist_action_output_recorded_after_takeover",
            entity_type="organizational_action_output",
            entity_id=output.id,
            after_state={
                "work_item_id": str(work.id),
                "position_key": position_key,
                "agent_run_id": str(response.run_id),
                "execution_attempt_id": str(attempt.id),
                "context_hash": binding.context.context_hash,
                "runtime_binding_hash": binding.runtime.binding_hash,
                "previous_fence_token": expected_previous_fence_token,
                "runtime_fence_token": runtime_snapshot.fence_token,
                "runtime_renewal_count": runtime_snapshot.renewal_count,
                "external_action_authorized": False,
                "latency_ms": latency_ms,
                "heartbeat_checkpoint": "agent_completed",
            },
            actor=actor,
            source=TAKEOVER_SOURCE,
        )
        completed_work = complete_work_item(
            session,
            context,
            work_item_id=work.id,
            reason=f"K.1 takeover re-execution completed for {position_key}.",
        )

        output = session.get(OrganizationalActionOutput, output.id)
        if output is None:
            raise DependencyConflict("takeover K.1 action output disappeared after WorkItem completion")
        final_payload = _json_object(output.output_json, label="takeover K.1 action output")
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
