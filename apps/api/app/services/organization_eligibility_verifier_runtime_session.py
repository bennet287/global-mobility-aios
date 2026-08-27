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
from app.services.organization_agent_runtime import AgentRuntimeProfile, EmployeeRuntimeBinding
from app.services.organization_command import (
    DependencyConflict,
    InvalidTransition,
    canonical_fingerprint,
    system_bound_agent_command_context,
)
from app.services.organization_decision_readiness import EligibilityDecisionReadinessResult
from app.services.organization_execution_failure import finalize_execution_failure_if_fence_owned
from app.services.organization_execution_heartbeat import (
    DEFAULT_HEARTBEAT_LEASE_SECONDS,
    stage_execution_heartbeat,
)
from app.services.organization_independent_eligibility_verification import (
    GovernedIndependentEligibilityVerificationResult,
    GovernedEligibilityTransitionIntentResult,
    resolve_independent_eligibility_verifier_execution,
    verify_eligibility_proposal_independently,
)
from app.services.organization_runtime_session_supervisor import (
    DEFAULT_RUNTIME_RENEWAL_INTERVAL_SECONDS,
    ExecutionRuntimeSessionSupervisor,
    initial_runtime_session_or_fail,
    stage_fenced_agent_completion,
)
from app.services.organization_work import complete_work_item, start_work_item


ELIGIBILITY_VERIFIER_RUNTIME_SESSION_CONTRACT_VERSION = (
    "eligibility-g1-verifier-runtime-session.v1"
)
DEFAULT_ELIGIBILITY_VERIFIER_RUNTIME_WRITER = "eligibility-verifier-runtime-worker"


@dataclass(frozen=True, slots=True)
class FencedEligibilityVerifierRuntimeResult:
    result: GovernedIndependentEligibilityVerificationResult
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
        raise DependencyConflict(
            "eligibility verifier runtime WorkItem was not found for the tenant"
        )
    if work.assigned_position_key != position_key:
        raise DependencyConflict(
            "eligibility verifier runtime position does not match the WorkItem assignment"
        )
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
        raise DependencyConflict(
            "eligibility verifier runtime requires exactly one active OrganizationPosition"
        )
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
        correlation_key=f"eligibility-verifier-runtime:{work.id}",
    )


def _ensure_running_work(
    session: Session,
    *,
    proposal: GovernedEligibilityTransitionIntentResult,
    readiness: EligibilityDecisionReadinessResult,
    work: OrganizationalWorkItem,
    position_key: str,
    runtime_profile: AgentRuntimeProfile,
) -> tuple[OrganizationalWorkItem, EmployeeRuntimeBinding]:
    if work.status != "queued":
        raise InvalidTransition(
            f"eligibility verifier runtime WorkItem is {work.status}, not a fresh queued G.1 operation"
        )

    # Validate the complete G.1 readiness/case/independence/runtime basis before
    # mutating the WorkItem. Starting the WorkItem changes its ContextBundle hash, so
    # resolve the exact same basis again after the transition and bind the execution
    # token to that running-state context.
    resolve_independent_eligibility_verifier_execution(
        session,
        proposal=proposal,
        readiness=readiness,
        verification_work_item_id=work.id,
        verifier_position_key=position_key,
        verifier_runtime_profile=runtime_profile,
    )
    work = start_work_item(
        session,
        _agent_context(session, work=work, position_key=position_key),
        work_item_id=work.id,
        reason="Start bounded independent eligibility verifier runtime.",
    )
    _, _, binding = resolve_independent_eligibility_verifier_execution(
        session,
        proposal=proposal,
        readiness=readiness,
        verification_work_item_id=work.id,
        verifier_position_key=position_key,
        verifier_runtime_profile=runtime_profile,
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
        raise InvalidTransition(
            "eligibility verifier WorkItem has exhausted its bounded execution attempts"
        )

    attempt_number = work.execution_attempts + 1
    started_at = now_utc()
    execution_token = canonical_fingerprint(
        {
            "contract_version": ELIGIBILITY_VERIFIER_RUNTIME_SESSION_CONTRACT_VERSION,
            "work_item_id": work.id,
            "position_key": position_key,
            "attempt_number": attempt_number,
            "context_hash": binding.context_hash,
            "runtime_binding_hash": binding.binding_hash,
        }
    )
    attempt = OrganizationExecutionAttempt(
        attempt_key=f"g1:eligibility-verifier-attempt:{work.id}:{attempt_number}",
        work_item_id=work.id,
        attempt_number=attempt_number,
        execution_token=execution_token,
        actor=actor,
    )
    work.execution_attempts = attempt_number
    work.execution_token = execution_token
    work.execution_started_at = started_at
    work.last_error = None

    # Keep generic WorkItem updated_at stable after the queued->running transition.
    # The attempt timestamp and heartbeat ledger are the execution clock; changing
    # updated_at here would make the execution token describe a context that G.1
    # immediately stops consuming.
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
        reason="Complete bounded independent eligibility verifier runtime.",
    )


def execute_fenced_independent_eligibility_verification(
    session: Session,
    *,
    proposal: GovernedEligibilityTransitionIntentResult,
    readiness: EligibilityDecisionReadinessResult,
    verification_work_item_id: UUID,
    verifier_position_key: str,
    verifier_runtime_profile: AgentRuntimeProfile,
    provider: LLMProvider,
    idempotency_key: str,
    actor: str = DEFAULT_ELIGIBILITY_VERIFIER_RUNTIME_WRITER,
    lease_seconds: int = DEFAULT_HEARTBEAT_LEASE_SECONDS,
    renewal_interval_seconds: float = DEFAULT_RUNTIME_RENEWAL_INTERVAL_SECONDS,
) -> FencedEligibilityVerifierRuntimeResult:
    """Execute G.1 inside the AIOS fenced runtime contract.

    G.1 remains authoritative for blind-review independence, governed case/pathway
    inputs, provider/model identity, typed verifier output, durable verification
    lineage, and its strictly non-authorizing semantics. This adapter adds only
    operational execution provenance: queued->running lifecycle, one bounded attempt,
    generation-one heartbeat, lease renewal while the verifier provider is active,
    fenced terminal completion, and shared fence-aware failure finalization.

    Runtime-session state remains technical execution health only. It grants no
    authority/autonomy and does not imply that a human, provider, model, or employee is
    online.
    """

    writer = str(actor or "").strip()
    if not writer:
        raise ValueError("eligibility verifier runtime writer is required")

    tenant_key = proposal.context.tenant_key
    work = _canonical_work(
        session,
        tenant_key=tenant_key,
        work_item_id=verification_work_item_id,
        position_key=verifier_position_key,
    )
    work, binding = _ensure_running_work(
        session,
        proposal=proposal,
        readiness=readiness,
        work=work,
        position_key=verifier_position_key,
        runtime_profile=verifier_runtime_profile,
    )
    attempt = _start_attempt(
        session,
        work=work,
        position_key=verifier_position_key,
        binding=binding,
        actor=writer,
    )
    runtime_session = initial_runtime_session_or_fail(
        session,
        tenant_key=tenant_key,
        work_item_id=work.id,
        execution_attempt_id=attempt.id,
        position_key=verifier_position_key,
        expected_execution_token=attempt.execution_token,
        writer=writer,
    )

    try:
        with ExecutionRuntimeSessionSupervisor(
            tenant_key=tenant_key,
            work_item_id=work.id,
            execution_attempt_id=attempt.id,
            position_key=verifier_position_key,
            expected_execution_token=attempt.execution_token,
            expected_fence_token=runtime_session.fence_token,
            writer=writer,
            lease_seconds=lease_seconds,
            renewal_interval_seconds=renewal_interval_seconds,
        ) as runtime_supervisor:
            result = verify_eligibility_proposal_independently(
                session,
                proposal=proposal,
                readiness=readiness,
                verification_work_item_id=work.id,
                verifier_position_key=verifier_position_key,
                verifier_runtime_profile=verifier_runtime_profile,
                provider=provider,
                idempotency_key=idempotency_key,
            )
        runtime_snapshot = runtime_supervisor.snapshot()
        _complete_attempt(
            session,
            work=work,
            attempt=attempt,
            position_key=verifier_position_key,
            expected_fence_token=runtime_session.fence_token,
            actor=writer,
        )
        return FencedEligibilityVerifierRuntimeResult(
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
            position_key=verifier_position_key,
            expected_execution_token=attempt.execution_token,
            expected_fence_token=runtime_session.fence_token,
            writer=writer,
            error=exc,
        )
        raise
