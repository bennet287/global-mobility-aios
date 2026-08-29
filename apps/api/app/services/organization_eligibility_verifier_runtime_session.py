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
    HEARTBEAT_STALE,
    claim_execution_runtime_session,
    current_execution_runtime_session,
    runtime_session_freshness_state,
    stage_execution_heartbeat,
)
from app.services.organization_eligibility_transition_intent import (
    GovernedEligibilityTransitionIntentResult,
)
from app.services.organization_independent_eligibility_verification import (
    GovernedIndependentEligibilityVerificationResult,
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
    "eligibility-g1-verifier-runtime-session.v2"
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
    takeover_resume: bool = False
    previous_fence_token: int | None = None


def _verification_idempotency_fingerprint(idempotency_key: str) -> str:
    if not isinstance(idempotency_key, str) or not idempotency_key.strip():
        raise ValueError("eligibility verifier idempotency key is required")
    return canonical_fingerprint({"idempotency_key": idempotency_key})


def _execution_token(
    *,
    proposal: GovernedEligibilityTransitionIntentResult,
    readiness: EligibilityDecisionReadinessResult,
    work_item_id: UUID,
    position_key: str,
    attempt_number: int,
    binding: EmployeeRuntimeBinding,
    idempotency_key: str,
) -> str:
    return canonical_fingerprint(
        {
            "contract_version": ELIGIBILITY_VERIFIER_RUNTIME_SESSION_CONTRACT_VERSION,
            "work_item_id": work_item_id,
            "position_key": position_key,
            "attempt_number": attempt_number,
            "context_hash": binding.context_hash,
            "runtime_binding_hash": binding.binding_hash,
            "proposal_trace_id": proposal.evaluation.trace_id,
            "proposal_activity_id": proposal.attempt_activity.id,
            "proposal_intent_fingerprint": proposal.intent_fingerprint,
            "readiness_fingerprint": readiness.readiness_fingerprint,
            "verification_idempotency_fingerprint": (
                _verification_idempotency_fingerprint(idempotency_key)
            ),
        }
    )


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
    proposal: GovernedEligibilityTransitionIntentResult,
    readiness: EligibilityDecisionReadinessResult,
    work: OrganizationalWorkItem,
    position_key: str,
    binding: EmployeeRuntimeBinding,
    idempotency_key: str,
    actor: str,
) -> OrganizationExecutionAttempt:
    if work.execution_attempts >= work.max_execution_attempts:
        raise InvalidTransition(
            "eligibility verifier WorkItem has exhausted its bounded execution attempts"
        )

    attempt_number = work.execution_attempts + 1
    started_at = now_utc()
    execution_token = _execution_token(
        proposal=proposal,
        readiness=readiness,
        work_item_id=work.id,
        position_key=position_key,
        attempt_number=attempt_number,
        binding=binding,
        idempotency_key=idempotency_key,
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
        proposal=proposal,
        readiness=readiness,
        work=work,
        position_key=verifier_position_key,
        binding=binding,
        idempotency_key=idempotency_key,
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
                commit_verification=False,
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


def _claim_resumable_attempt(
    session: Session,
    *,
    proposal: GovernedEligibilityTransitionIntentResult,
    readiness: EligibilityDecisionReadinessResult,
    work: OrganizationalWorkItem,
    position_key: str,
    runtime_profile: AgentRuntimeProfile,
    execution_attempt_id: UUID,
    expected_execution_token: str,
    expected_previous_fence_token: int,
    idempotency_key: str,
    actor: str,
    lease_seconds: int,
) -> tuple[OrganizationExecutionAttempt, EmployeeRuntimeBinding, int]:
    if not actor.strip():
        raise ValueError("eligibility verifier takeover writer is required")
    if not expected_execution_token.strip():
        raise ValueError("eligibility verifier takeover execution token is required")
    if (
        not isinstance(expected_previous_fence_token, int)
        or isinstance(expected_previous_fence_token, bool)
        or expected_previous_fence_token < 1
    ):
        raise ValueError(
            "eligibility verifier takeover previous fence token must be a positive integer"
        )
    if work.status != "running":
        raise InvalidTransition(
            "eligibility verifier takeover requires a running verification WorkItem"
        )

    attempt = session.get(OrganizationExecutionAttempt, execution_attempt_id)
    if attempt is None:
        raise DependencyConflict(
            "eligibility verifier takeover execution attempt was not found"
        )
    if attempt.work_item_id != work.id:
        raise DependencyConflict(
            "eligibility verifier takeover execution attempt belongs to another WorkItem"
        )
    if attempt.status != "running":
        raise InvalidTransition(
            "eligibility verifier takeover requires a running execution attempt"
        )
    if attempt.attempt_number != work.execution_attempts:
        raise DependencyConflict(
            "eligibility verifier takeover requires the latest bounded execution attempt"
        )
    if (
        not work.execution_token
        or work.execution_token != attempt.execution_token
        or attempt.execution_token != expected_execution_token
    ):
        raise DependencyConflict(
            "eligibility verifier takeover execution token conflicts with canonical work state"
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
        raise DependencyConflict(
            "eligibility verifier takeover requires exactly one canonical running attempt"
        )

    _, _, binding = resolve_independent_eligibility_verifier_execution(
        session,
        proposal=proposal,
        readiness=readiness,
        verification_work_item_id=work.id,
        verifier_position_key=position_key,
        verifier_runtime_profile=runtime_profile,
    )
    reconstructed_token = _execution_token(
        proposal=proposal,
        readiness=readiness,
        work_item_id=work.id,
        position_key=position_key,
        attempt_number=attempt.attempt_number,
        binding=binding,
        idempotency_key=idempotency_key,
    )
    if reconstructed_token != expected_execution_token:
        raise DependencyConflict(
            "eligibility verifier takeover inputs do not match the interrupted G.1 identity"
        )

    current = current_execution_runtime_session(
        session,
        tenant_key=work.tenant_key,
        work_item_id=work.id,
        execution_attempt_id=attempt.id,
        position_key=position_key,
    )
    if current is None:
        raise DependencyConflict(
            "eligibility verifier takeover requires an established runtime session"
        )
    if current.fence_token != expected_previous_fence_token:
        raise DependencyConflict(
            "eligibility verifier takeover caller observed a stale previous fence token"
        )
    if runtime_session_freshness_state(current) != HEARTBEAT_STALE:
        raise InvalidTransition(
            "eligibility verifier takeover requires an expired runtime session"
        )

    claimed = claim_execution_runtime_session(
        session,
        tenant_key=work.tenant_key,
        work_item_id=work.id,
        execution_attempt_id=attempt.id,
        position_key=position_key,
        expected_execution_token=expected_execution_token,
        writer=actor,
        lease_seconds=lease_seconds,
    )
    if claimed.fence_token <= current.fence_token:
        raise DependencyConflict(
            "eligibility verifier takeover did not advance the runtime fencing generation"
        )
    return attempt, binding, claimed.fence_token


def resume_fenced_independent_eligibility_verification_with_takeover(
    session: Session,
    *,
    proposal: GovernedEligibilityTransitionIntentResult,
    readiness: EligibilityDecisionReadinessResult,
    verification_work_item_id: UUID,
    verifier_position_key: str,
    verifier_runtime_profile: AgentRuntimeProfile,
    provider: LLMProvider,
    idempotency_key: str,
    execution_attempt_id: UUID,
    expected_execution_token: str,
    expected_previous_fence_token: int,
    actor: str,
    lease_seconds: int = DEFAULT_HEARTBEAT_LEASE_SECONDS,
    renewal_interval_seconds: float = DEFAULT_RUNTIME_RENEWAL_INTERVAL_SECONDS,
) -> FencedEligibilityVerifierRuntimeResult:
    """Re-execute one interrupted G.1 attempt under a newly claimed stale-session fence.

    The caller must identify the exact running attempt, execution token, and previously
    observed fence. Current G.1 readiness/context/runtime identity plus proposal and
    idempotency identity must reproduce the v2 execution token before takeover. No new
    execution attempt is created.

    Verification Activity, terminal heartbeat, attempt completion, and WorkItem
    completion commit atomically. A superseded worker therefore cannot persist late G.1
    lineage after another writer claims the stale session.
    """

    writer = str(actor or "").strip()
    if not writer:
        raise ValueError("eligibility verifier takeover writer is required")

    tenant_key = proposal.context.tenant_key
    work = _canonical_work(
        session,
        tenant_key=tenant_key,
        work_item_id=verification_work_item_id,
        position_key=verifier_position_key,
    )
    attempt, _binding, fence_token = _claim_resumable_attempt(
        session,
        proposal=proposal,
        readiness=readiness,
        work=work,
        position_key=verifier_position_key,
        runtime_profile=verifier_runtime_profile,
        execution_attempt_id=execution_attempt_id,
        expected_execution_token=expected_execution_token,
        expected_previous_fence_token=expected_previous_fence_token,
        idempotency_key=idempotency_key,
        actor=writer,
        lease_seconds=lease_seconds,
    )

    try:
        with ExecutionRuntimeSessionSupervisor(
            tenant_key=tenant_key,
            work_item_id=work.id,
            execution_attempt_id=attempt.id,
            position_key=verifier_position_key,
            expected_execution_token=attempt.execution_token,
            expected_fence_token=fence_token,
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
                commit_verification=False,
            )
        runtime_snapshot = runtime_supervisor.snapshot()
        _complete_attempt(
            session,
            work=work,
            attempt=attempt,
            position_key=verifier_position_key,
            expected_fence_token=fence_token,
            actor=writer,
        )
        return FencedEligibilityVerifierRuntimeResult(
            result=result,
            execution_attempt_id=attempt.id,
            execution_token=attempt.execution_token,
            fence_token=fence_token,
            writer=writer,
            renewal_count=runtime_snapshot.renewal_count,
            takeover_resume=True,
            previous_fence_token=expected_previous_fence_token,
        )
    except Exception as exc:
        finalize_execution_failure_if_fence_owned(
            session,
            tenant_key=tenant_key,
            work_item_id=work.id,
            execution_attempt_id=attempt.id,
            position_key=verifier_position_key,
            expected_execution_token=attempt.execution_token,
            expected_fence_token=fence_token,
            writer=writer,
            error=exc,
        )
        raise

