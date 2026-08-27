from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    OrganizationExecutionAttempt,
    OrganizationPosition,
    OrganizationalWorkItem,
    now_utc,
)
from app.services.llm_client import LLMProvider
from app.services.organization_agent_runtime import (
    AgentRuntimeError,
    AgentRuntimeProfile,
    EmployeeRuntimeBinding,
    bind_employee_runtime,
)
from app.services.organization_command import (
    DependencyConflict,
    InvalidTransition,
    canonical_fingerprint,
    system_bound_agent_command_context,
)
from app.services.organization_context_broker import ContextPurpose, build_work_item_context_bundle
from app.services.organization_eligibility_transition_intent import (
    GovernedEligibilityTransitionIntentResult,
    governed_eligibility_transition_intent,
)
from app.services.organization_execution_failure import finalize_execution_failure_if_fence_owned
from app.services.organization_execution_heartbeat import (
    DEFAULT_HEARTBEAT_LEASE_SECONDS,
    stage_execution_heartbeat,
)
from app.services.organization_governance_kernel import CapabilityAuthority
from app.services.organization_runtime_session_supervisor import (
    DEFAULT_RUNTIME_RENEWAL_INTERVAL_SECONDS,
    ExecutionRuntimeSessionSupervisor,
    initial_runtime_session_or_fail,
    stage_fenced_agent_completion,
)
from app.services.organization_work import complete_work_item, start_work_item


ELIGIBILITY_RUNTIME_SESSION_CONTRACT_VERSION = "eligibility-e2-runtime-session.v1"
DEFAULT_ELIGIBILITY_RUNTIME_WRITER = "eligibility-runtime-worker"


@dataclass(frozen=True, slots=True)
class FencedEligibilityRuntimeResult:
    result: GovernedEligibilityTransitionIntentResult
    execution_attempt_id: UUID
    execution_token: str
    fence_token: int
    writer: str
    renewal_count: int


def _canonical_work(
    session: Session,
    *,
    tenant_key: str,
    work_item_id: UUID,
    position_key: str,
) -> OrganizationalWorkItem:
    work = session.exec(
        select(OrganizationalWorkItem).where(
            OrganizationalWorkItem.id == work_item_id,
            OrganizationalWorkItem.tenant_key == tenant_key,
        )
    ).first()
    if work is None:
        raise DependencyConflict("eligibility runtime WorkItem was not found for the tenant")
    if work.assigned_position_key != position_key:
        raise DependencyConflict("eligibility runtime position does not match the WorkItem assignment")
    return work


def _active_position(session: Session, *, position_key: str) -> OrganizationPosition:
    rows = list(
        session.exec(
            select(OrganizationPosition)
            .where(
                OrganizationPosition.position_key == position_key,
                OrganizationPosition.status == "active",
            )
            .order_by(OrganizationPosition.version.desc())
        ).all()
    )
    if len(rows) != 1:
        raise DependencyConflict("eligibility runtime requires exactly one active OrganizationPosition")
    return rows[0]


def _agent_context(
    session: Session,
    *,
    work: OrganizationalWorkItem,
    position_key: str,
):
    position = _active_position(session, position_key=position_key)
    return system_bound_agent_command_context(
        tenant_key=work.tenant_key,
        position_key=position_key,
        department=position.department,
        authority_level=position.authority_level,
        correlation_key=f"eligibility-runtime:{work.id}",
    )


def _current_binding(
    session: Session,
    *,
    work: OrganizationalWorkItem,
    position_key: str,
    runtime_profile: AgentRuntimeProfile,
) -> EmployeeRuntimeBinding:
    context = build_work_item_context_bundle(
        session,
        tenant_key=work.tenant_key,
        position_key=position_key,
        work_item_id=work.id,
        purpose=ContextPurpose.REVIEW,
    )
    try:
        return bind_employee_runtime(
            session,
            context=context,
            profile=runtime_profile,
            required_capability="structured_output",
        )
    except AgentRuntimeError as exc:
        raise DependencyConflict("eligibility runtime binding could not be established") from exc


def _ensure_running_work(
    session: Session,
    *,
    work: OrganizationalWorkItem,
    position_key: str,
    runtime_profile: AgentRuntimeProfile,
) -> tuple[OrganizationalWorkItem, EmployeeRuntimeBinding]:
    # Validate the queued WorkItem against current context/runtime before mutating its
    # operational lifecycle. Starting the WorkItem changes its ContextBundle hash, so
    # the binding is resolved again after the transition and that running-state binding
    # becomes the execution-token input.
    if work.status == "queued":
        _current_binding(
            session,
            work=work,
            position_key=position_key,
            runtime_profile=runtime_profile,
        )
        work = start_work_item(
            session,
            _agent_context(session, work=work, position_key=position_key),
            work_item_id=work.id,
            reason="Start bounded governed eligibility producer runtime.",
        )
    elif work.status != "running":
        raise InvalidTransition(
            f"eligibility runtime WorkItem is {work.status}, not executable by the fenced E.2 envelope"
        )

    binding = _current_binding(
        session,
        work=work,
        position_key=position_key,
        runtime_profile=runtime_profile,
    )
    return work, binding


def _start_attempt(
    session: Session,
    *,
    work: OrganizationalWorkItem,
    position_key: str,
    binding: EmployeeRuntimeBinding,
    actor: str,
) -> OrganizationExecutionAttempt:
    if work.execution_attempts >= work.max_execution_attempts:
        raise InvalidTransition("eligibility WorkItem has exhausted its bounded execution attempts")
    attempt_number = work.execution_attempts + 1
    started_at = now_utc()
    execution_token = canonical_fingerprint(
        {
            "contract_version": ELIGIBILITY_RUNTIME_SESSION_CONTRACT_VERSION,
            "work_item_id": work.id,
            "position_key": position_key,
            "attempt_number": attempt_number,
            "context_hash": binding.context_hash,
            "runtime_binding_hash": binding.binding_hash,
        }
    )
    attempt = OrganizationExecutionAttempt(
        attempt_key=f"e2:eligibility-attempt:{work.id}:{attempt_number}",
        work_item_id=work.id,
        attempt_number=attempt_number,
        execution_token=execution_token,
        actor=actor,
    )
    work.execution_attempts = attempt_number
    work.execution_token = execution_token
    work.execution_started_at = started_at
    work.last_error = None
    # Do not advance the generic WorkItem updated_at here. The durable
    # OrganizationExecutionAttempt.started_at and heartbeat ledger are the runtime
    # clock. Advancing updated_at would change the governed ContextBundle hash
    # between the pre-attempt runtime binding and the E.2 function that immediately
    # re-resolves that same running WorkItem, making the execution token describe a
    # context E.2 never actually consumed.
    session.add(work)
    session.add(attempt)
    stage_execution_heartbeat(
        session,
        tenant_key=work.tenant_key,
        work=work,
        attempt=attempt,
        position_key=position_key,
        checkpoint="attempt_started",
        writer=actor,
        observed_at=started_at,
    )
    session.commit()
    session.refresh(attempt)
    session.refresh(work)
    return attempt


def _complete_attempt(
    session: Session,
    *,
    work: OrganizationalWorkItem,
    attempt: OrganizationExecutionAttempt,
    position_key: str,
    expected_fence_token: int,
    actor: str,
) -> None:
    completed_at = now_utc()
    stage_fenced_agent_completion(
        session,
        tenant_key=work.tenant_key,
        work=work,
        attempt=attempt,
        position_key=position_key,
        expected_execution_token=attempt.execution_token,
        expected_fence_token=expected_fence_token,
        writer=actor,
        observed_at=completed_at,
    )
    attempt.status = "completed"
    attempt.completed_at = completed_at
    attempt.error = None
    work.execution_started_at = None
    work.last_error = None
    work.updated_at = completed_at
    session.add(attempt)
    session.add(work)
    complete_work_item(
        session,
        _agent_context(session, work=work, position_key=position_key),
        work_item_id=work.id,
        reason="Complete bounded governed eligibility producer runtime.",
    )


def execute_fenced_governed_eligibility_transition_intent(
    session: Session,
    *,
    tenant_key: str,
    position_key: str,
    work_item_id: UUID,
    runtime_profile: AgentRuntimeProfile,
    authority: CapabilityAuthority,
    provider: LLMProvider,
    idempotency_key: str,
    expected_eligibility_revision_version: int | None = None,
    actor: str = DEFAULT_ELIGIBILITY_RUNTIME_WRITER,
    lease_seconds: int = DEFAULT_HEARTBEAT_LEASE_SECONDS,
    renewal_interval_seconds: float = DEFAULT_RUNTIME_RENEWAL_INTERVAL_SECONDS,
) -> FencedEligibilityRuntimeResult:
    """Execute the existing E.2 producer inside the AIOS fenced runtime contract.

    This adapter is intentionally domain-specific. It does not replace E.2's governed
    context, provider, typed-output, revision-precondition, or Command Gateway logic.
    It adds operational execution provenance around that already-governed function:
    queued->running WorkItem transition, durable OrganizationExecutionAttempt, heartbeat
    generation one, bounded renewal while E.2 executes, fenced terminal completion, and
    shared fence-aware failure finalization.

    Runtime-session state is technical execution health only. It grants no authority,
    does not change Evidence/VerifiedRule truth, and does not imply that a person,
    provider, model, or AI employee is online.
    """

    writer = str(actor or "").strip()
    if not writer:
        raise ValueError("eligibility runtime writer is required")

    work = _canonical_work(
        session,
        tenant_key=tenant_key,
        work_item_id=work_item_id,
        position_key=position_key,
    )
    work, binding = _ensure_running_work(
        session,
        work=work,
        position_key=position_key,
        runtime_profile=runtime_profile,
    )
    attempt = _start_attempt(
        session,
        work=work,
        position_key=position_key,
        binding=binding,
        actor=writer,
    )
    runtime_session = initial_runtime_session_or_fail(
        session,
        tenant_key=tenant_key,
        work_item_id=work.id,
        execution_attempt_id=attempt.id,
        position_key=position_key,
        expected_execution_token=attempt.execution_token,
        writer=writer,
    )

    try:
        with ExecutionRuntimeSessionSupervisor(
            tenant_key=tenant_key,
            work_item_id=work.id,
            execution_attempt_id=attempt.id,
            position_key=position_key,
            expected_execution_token=attempt.execution_token,
            expected_fence_token=runtime_session.fence_token,
            writer=writer,
            lease_seconds=lease_seconds,
            renewal_interval_seconds=renewal_interval_seconds,
        ) as runtime_supervisor:
            result = governed_eligibility_transition_intent(
                session,
                tenant_key=tenant_key,
                position_key=position_key,
                work_item_id=work.id,
                runtime_profile=runtime_profile,
                authority=authority,
                provider=provider,
                idempotency_key=idempotency_key,
                expected_eligibility_revision_version=expected_eligibility_revision_version,
            )
        runtime_snapshot = runtime_supervisor.snapshot()
        _complete_attempt(
            session,
            work=work,
            attempt=attempt,
            position_key=position_key,
            expected_fence_token=runtime_session.fence_token,
            actor=writer,
        )
        return FencedEligibilityRuntimeResult(
            result=result,
            execution_attempt_id=attempt.id,
            execution_token=attempt.execution_token,
            fence_token=runtime_session.fence_token,
            writer=writer,
            renewal_count=runtime_snapshot.renewal_count,
        )
    except Exception as exc:
        finalize_execution_failure_if_fence_owned(
            session,
            tenant_key=tenant_key,
            work_item_id=work.id,
            execution_attempt_id=attempt.id,
            position_key=position_key,
            expected_execution_token=attempt.execution_token,
            expected_fence_token=runtime_session.fence_token,
            writer=writer,
            error=exc,
        )
        raise
