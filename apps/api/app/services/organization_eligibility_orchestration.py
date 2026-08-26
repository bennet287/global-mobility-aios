from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import OrganizationActivity
from app.services.llm_client import LLMProvider
from app.services.organization_agent_runtime import AgentRuntimeProfile
from app.services.organization_decision_readiness import (
    DecisionReadinessError,
    DecisionReadinessState,
    assess_eligibility_decision_readiness,
)
from app.services.organization_eligibility_effect import (
    EligibilityCanonicalEffectError,
    commit_governed_eligibility_effect,
)
from app.services.organization_eligibility_immune_system import (
    EligibilityCircuitOpen,
    EligibilityImmuneIncidentKind,
    EligibilityImmuneSystemError,
    eligibility_circuit_scope_for_work_item,
    record_eligibility_immune_incident,
    require_eligibility_circuit_closed,
)
from app.services.organization_eligibility_lineage import (
    CanonicalEligibilityLineageError,
    canonical_eligibility_lineage_for_governance,
)
from app.services.organization_eligibility_revision_conflict import (
    EligibilityRevisionConflictAttributionError,
    record_attributed_eligibility_revision_conflict,
)
from app.services.organization_eligibility_revision_precondition import (
    EligibilityRevisionPostResolutionAdvance,
    EligibilityRevisionPreconditionConflict,
)
from app.services.organization_eligibility_revision_runtime_race import (
    EligibilityRevisionRuntimeRaceAttributionError,
    record_attributed_eligibility_revision_runtime_race,
)
from app.services.organization_eligibility_runtime_health import (
    EligibilityRuntimeExecutionRole,
    record_attributed_eligibility_runtime_health_incident,
)
from app.services.organization_eligibility_runtime_session import (
    execute_fenced_governed_eligibility_transition_intent,
)
from app.services.organization_eligibility_transition_intent import (
    GOVERNED_ELIGIBILITY_CAPABILITY,
    EligibilityIntentError,
    EligibilityIntentRuntimeError,
)
from app.services.organization_eligibility_verification_floor import (
    EligibilityVerificationFloorError,
    integrate_eligibility_verification_floor,
)
from app.services.organization_governance_kernel import CapabilityAuthority, GatewayOutcome
from app.services.organization_independent_eligibility_verification import (
    IndependentEligibilityVerificationError,
    IndependentEligibilityVerificationRuntimeError,
    IndependentVerificationDisposition,
    verify_eligibility_proposal_independently,
)


ELIGIBILITY_ORCHESTRATION_SCHEMA_VERSION = "governed-eligibility-orchestration.v1"


class GovernedEligibilityOrchestrationError(RuntimeError):
    """Base error for the bounded G.4 governed eligibility orchestration slice."""


class GovernedEligibilityOrchestrationIntegrityError(GovernedEligibilityOrchestrationError):
    """Trusted orchestration inputs or durable stage lineage are inconsistent."""


class GovernedEligibilityOrchestrationState(str, Enum):
    PROPOSAL_BLOCKED = "proposal_blocked"
    NOT_READY = "not_ready"
    HUMAN_INPUT_REQUIRED = "human_input_required"
    VERIFICATION_DISAGREES = "verification_disagrees"
    VERIFICATION_INSUFFICIENT_BASIS = "verification_insufficient_basis"
    AWAITING_AUTHORITY = "awaiting_authority"
    CANONICAL_EFFECT_COMMITTED = "canonical_effect_committed"


@dataclass(frozen=True)
class GovernedEligibilityExecutionPlan:
    """Trusted server-side execution dependencies for one governed eligibility run.

    This object is deliberately not an HTTP/request schema. Callers must resolve it
    from trusted server configuration or an internal policy/runtime registry. It owns
    technical provider/runtime selection and CapabilityAuthority; request JSON never
    gets to choose those values.
    """

    producer_position_key: str
    producer_runtime_profile: AgentRuntimeProfile
    producer_provider: LLMProvider
    verifier_position_key: str
    verifier_runtime_profile: AgentRuntimeProfile
    verifier_provider: LLMProvider
    authority: CapabilityAuthority


@dataclass(frozen=True)
class GovernedEligibilityOrchestrationResult:
    schema_version: str
    state: GovernedEligibilityOrchestrationState
    trace_id: UUID
    proposal_activity_id: UUID
    readiness_state: str | None
    verification_activity_id: UUID | None
    verification_disposition: str | None
    verification_floor_activity_id: UUID | None
    gateway_outcome: str
    assessment_id: UUID | None
    revision_id: UUID | None
    semantic_activity_id: UUID | None
    canonical_effect_committed: bool
    replayed: bool


def _required_text(value: str, *, label: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise GovernedEligibilityOrchestrationIntegrityError(f"{label} is required")
    return normalized


def _validate_plan(*, tenant_key: str, plan: GovernedEligibilityExecutionPlan) -> None:
    producer_position = _required_text(plan.producer_position_key, label="producer position key")
    verifier_position = _required_text(plan.verifier_position_key, label="verifier position key")
    if producer_position == verifier_position:
        raise GovernedEligibilityOrchestrationIntegrityError(
            "producer and verifier must be different OrganizationPositions"
        )
    if plan.authority.tenant_key != tenant_key:
        raise GovernedEligibilityOrchestrationIntegrityError(
            "CapabilityAuthority belongs to a different tenant"
        )
    if plan.authority.actor_id != producer_position:
        raise GovernedEligibilityOrchestrationIntegrityError(
            "CapabilityAuthority actor must be the producer OrganizationPosition"
        )
    if plan.authority.capability != GOVERNED_ELIGIBILITY_CAPABILITY:
        raise GovernedEligibilityOrchestrationIntegrityError(
            "CapabilityAuthority does not grant the governed eligibility capability"
        )
    if plan.producer_provider.name != plan.producer_runtime_profile.provider_key:
        raise GovernedEligibilityOrchestrationIntegrityError(
            "producer provider does not match the trusted producer runtime profile"
        )
    if plan.verifier_provider.name != plan.verifier_runtime_profile.provider_key:
        raise GovernedEligibilityOrchestrationIntegrityError(
            "verifier provider does not match the trusted verifier runtime profile"
        )
    if plan.producer_runtime_profile.model_key is None or plan.verifier_runtime_profile.model_key is None:
        raise GovernedEligibilityOrchestrationIntegrityError(
            "governed R3 orchestration requires pinned producer and verifier models"
        )
    if plan.producer_runtime_profile.independence_group == plan.verifier_runtime_profile.independence_group:
        raise GovernedEligibilityOrchestrationIntegrityError(
            "producer and verifier must use different independence groups"
        )
    if plan.producer_runtime_profile.provider_key == plan.verifier_runtime_profile.provider_key:
        raise GovernedEligibilityOrchestrationIntegrityError(
            "producer and verifier must use different providers for the first R3 orchestration contract"
        )
    if plan.producer_runtime_profile.model_key == plan.verifier_runtime_profile.model_key:
        raise GovernedEligibilityOrchestrationIntegrityError(
            "producer and verifier must use different models for the first R3 orchestration contract"
        )


def _completed_effect_replay(
    session: Session,
    *,
    tenant_key: str,
    proposal_work_item_id: UUID,
    verification_work_item_id: UUID,
    idempotency_key: str,
    expected_eligibility_revision_version: int | None,
) -> GovernedEligibilityOrchestrationResult | None:
    governance = session.exec(
        select(OrganizationActivity).where(
            OrganizationActivity.tenant_key == tenant_key,
            OrganizationActivity.activity_key == f"governance:{idempotency_key}",
        )
    ).first()
    if governance is None:
        return None

    try:
        lineage = canonical_eligibility_lineage_for_governance(
            session,
            tenant_key=tenant_key,
            governance_activity_id=governance.id,
        )
    except CanonicalEligibilityLineageError as exc:
        raise GovernedEligibilityOrchestrationIntegrityError(
            f"completed canonical eligibility effect failed durable lineage validation: {exc.code}"
        ) from exc

    revision = lineage.revision
    assessment = lineage.assessment
    verification = lineage.verification_activity
    floor = lineage.verification_floor_activity
    semantic = lineage.semantic_activity

    if governance.work_item_id != proposal_work_item_id:
        raise GovernedEligibilityOrchestrationIntegrityError(
            "completed canonical effect belongs to a different proposal WorkItem"
        )
    if verification.work_item_id != verification_work_item_id:
        raise GovernedEligibilityOrchestrationIntegrityError(
            "completed canonical effect belongs to a different verification WorkItem"
        )

    replay_expectation = None if revision.version == 1 else revision.version - 1
    if expected_eligibility_revision_version != replay_expectation:
        raise GovernedEligibilityOrchestrationIntegrityError(
            "orchestration replay eligibility revision expectation conflicts with durable effect"
        )
    try:
        trace_id = UUID(str(governance.correlation_key))
    except (TypeError, ValueError) as exc:
        raise GovernedEligibilityOrchestrationIntegrityError(
            "completed canonical eligibility governance has an invalid trace identity"
        ) from exc

    return GovernedEligibilityOrchestrationResult(
        schema_version=ELIGIBILITY_ORCHESTRATION_SCHEMA_VERSION,
        state=GovernedEligibilityOrchestrationState.CANONICAL_EFFECT_COMMITTED,
        trace_id=trace_id,
        proposal_activity_id=lineage.proposal_activity_id,
        readiness_state=DecisionReadinessState.READY_FOR_INDEPENDENT_VERIFICATION.value,
        verification_activity_id=verification.id,
        verification_disposition=IndependentVerificationDisposition.AGREES.value,
        verification_floor_activity_id=floor.id,
        gateway_outcome=GatewayOutcome.IDEMPOTENT_REPLAY.value,
        assessment_id=assessment.id,
        revision_id=revision.id,
        semantic_activity_id=semantic.id,
        canonical_effect_committed=True,
        replayed=True,
    )


def orchestrate_governed_eligibility(
    session: Session,
    *,
    tenant_key: str,
    proposal_work_item_id: UUID,
    verification_work_item_id: UUID,
    idempotency_key: str,
    execution_plan: GovernedEligibilityExecutionPlan,
    expected_eligibility_revision_version: int | None = None,
) -> GovernedEligibilityOrchestrationResult:
    """Run the governed E.2 → F.1 → G.1 → G.2 → canonical-effect eligibility vertical.

    The orchestration is intentionally domain-specific. It coordinates already-sealed
    services and does not create a generic workflow/effect framework. Runtime/provider
    and authority inputs arrive only through ``execution_plan``, which is a trusted
    server-side object rather than untrusted request data.

    G.5 adds a caller-supplied canonical eligibility revision expectation. It is an
    optimistic-concurrency assertion, not authority: initial v1 creation omits it,
    while reassessment must name the active revision it expects to supersede.

    H.1 adds an aggregate-scoped restrictive circuit preflight after durable replay
    resolution and before E.2/provider execution. A CLOSED circuit grants nothing; it
    only means the Immune System is not adding an extra restriction. An OPEN circuit
    blocks fresh execution before either provider is called. Exact replay of a durable
    committed effect remains historical and does not perform new execution.

    H.2.3 attributes only a genuine stale reassessment expectation discovered at E.2's
    initial G.5 precondition boundary. That warning is observation-only. Missing/future
    expectations and revision races discovered after provider latency are intentionally
    excluded from this attribution contract.

    H.2.4 attributes one distinct race: a valid reassessment revision advances during
    producer runtime. The producer call has happened, but verifier egress and canonical
    effect integration have not. The warning remains observation-only and grants nothing.

    Exact retries after a committed effect resolve directly from durable canonical
    governance/revision lineage and do not call either model again. Replay still checks
    that the caller supplied the same revision expectation as the committed operation.
    """

    tenant = _required_text(tenant_key, label="tenant key")
    key = _required_text(idempotency_key, label="orchestration idempotency key")
    if expected_eligibility_revision_version is not None and expected_eligibility_revision_version < 1:
        raise GovernedEligibilityOrchestrationIntegrityError(
            "expected eligibility revision version must be at least 1"
        )
    if proposal_work_item_id == verification_work_item_id:
        raise GovernedEligibilityOrchestrationIntegrityError(
            "proposal and verification must use different WorkItems"
        )
    _validate_plan(tenant_key=tenant, plan=execution_plan)

    replay = _completed_effect_replay(
        session,
        tenant_key=tenant,
        proposal_work_item_id=proposal_work_item_id,
        verification_work_item_id=verification_work_item_id,
        idempotency_key=key,
        expected_eligibility_revision_version=expected_eligibility_revision_version,
    )
    if replay is not None:
        return replay

    try:
        circuit_scope = eligibility_circuit_scope_for_work_item(
            session,
            tenant_key=tenant,
            proposal_work_item_id=proposal_work_item_id,
            producer_position_key=execution_plan.producer_position_key,
        )
        require_eligibility_circuit_closed(
            session,
            tenant_key=tenant,
            aggregate_key=circuit_scope.aggregate_key,
        )
    except EligibilityCircuitOpen as exc:
        raise GovernedEligibilityOrchestrationIntegrityError(
            "governed eligibility circuit is open for the canonical aggregate"
        ) from exc
    except EligibilityImmuneSystemError as exc:
        raise GovernedEligibilityOrchestrationIntegrityError(
            "governed eligibility circuit preflight could not resolve canonical scope"
        ) from exc

    try:
        producer_runtime = execute_fenced_governed_eligibility_transition_intent(
            session,
            tenant_key=tenant,
            position_key=execution_plan.producer_position_key,
            work_item_id=proposal_work_item_id,
            runtime_profile=execution_plan.producer_runtime_profile,
            authority=execution_plan.authority,
            provider=execution_plan.producer_provider,
            idempotency_key=key,
            expected_eligibility_revision_version=expected_eligibility_revision_version,
        )
        proposal = producer_runtime.result
    except EligibilityIntentRuntimeError as exc:
        try:
            record_attributed_eligibility_runtime_health_incident(
                session,
                tenant_key=tenant,
                aggregate_key=circuit_scope.aggregate_key,
                incident_key=f"{key}:producer-runtime-health",
                execution_role=EligibilityRuntimeExecutionRole.PRODUCER,
                position_key=execution_plan.producer_position_key,
                runtime_profile=execution_plan.producer_runtime_profile,
                summary="Eligibility producer runtime failed before a governed proposal could complete.",
                failure_provenance=exc.failure_provenance,
            )
        except (EligibilityImmuneSystemError, RuntimeError) as incident_exc:
            raise GovernedEligibilityOrchestrationIntegrityError(
                "producer runtime failure could not be persisted as an immune-system incident"
            ) from incident_exc
        raise GovernedEligibilityOrchestrationIntegrityError(
            "governed eligibility proposal runtime failed"
        ) from exc
    except EligibilityIntentError as exc:
        cause = exc.__cause__
        if isinstance(cause, EligibilityRevisionPostResolutionAdvance):
            try:
                record_attributed_eligibility_revision_runtime_race(
                    session,
                    tenant_key=tenant,
                    aggregate_key=circuit_scope.aggregate_key,
                    incident_key=f"{key}:revision-runtime-race",
                    race=cause,
                    position_key=execution_plan.producer_position_key,
                    runtime_profile=execution_plan.producer_runtime_profile,
                    summary=(
                        "Eligibility reassessment became stale after producer egress because "
                        "a newer canonical revision committed during producer runtime."
                    ),
                )
            except (
                EligibilityRevisionRuntimeRaceAttributionError,
                EligibilityImmuneSystemError,
                RuntimeError,
            ) as incident_exc:
                raise GovernedEligibilityOrchestrationIntegrityError(
                    "post-producer revision race could not be persisted as an immune-system incident"
                ) from incident_exc
            raise GovernedEligibilityOrchestrationIntegrityError(
                "governed eligibility revision advanced during producer runtime"
            ) from exc
        if isinstance(cause, EligibilityRevisionPreconditionConflict):
            try:
                record_attributed_eligibility_revision_conflict(
                    session,
                    tenant_key=tenant,
                    aggregate_key=circuit_scope.aggregate_key,
                    incident_key=f"{key}:revision-conflict",
                    conflict=cause,
                    summary=(
                        "Eligibility reassessment supplied a superseded canonical revision "
                        "expectation before provider execution."
                    ),
                )
            except (
                EligibilityRevisionConflictAttributionError,
                EligibilityImmuneSystemError,
                RuntimeError,
            ) as incident_exc:
                raise GovernedEligibilityOrchestrationIntegrityError(
                    "revision conflict could not be persisted as an immune-system incident"
                ) from incident_exc
            raise GovernedEligibilityOrchestrationIntegrityError(
                "governed eligibility revision precondition conflicted with the current canonical revision"
            ) from exc
        raise GovernedEligibilityOrchestrationIntegrityError(
            "governed eligibility proposal stage failed"
        ) from exc

    if proposal.evaluation.outcome is GatewayOutcome.BLOCK:
        return GovernedEligibilityOrchestrationResult(
            schema_version=ELIGIBILITY_ORCHESTRATION_SCHEMA_VERSION,
            state=GovernedEligibilityOrchestrationState.PROPOSAL_BLOCKED,
            trace_id=proposal.evaluation.trace_id,
            proposal_activity_id=proposal.attempt_activity.id,
            readiness_state=None,
            verification_activity_id=None,
            verification_disposition=None,
            verification_floor_activity_id=None,
            gateway_outcome=proposal.evaluation.outcome.value,
            assessment_id=None,
            revision_id=None,
            semantic_activity_id=None,
            canonical_effect_committed=False,
            replayed=False,
        )

    try:
        readiness = assess_eligibility_decision_readiness(session, proposal=proposal)
    except DecisionReadinessError as exc:
        raise GovernedEligibilityOrchestrationIntegrityError(
            "eligibility Decision Readiness stage failed"
        ) from exc

    if readiness.state is DecisionReadinessState.NOT_READY:
        return GovernedEligibilityOrchestrationResult(
            schema_version=ELIGIBILITY_ORCHESTRATION_SCHEMA_VERSION,
            state=GovernedEligibilityOrchestrationState.NOT_READY,
            trace_id=proposal.evaluation.trace_id,
            proposal_activity_id=proposal.attempt_activity.id,
            readiness_state=readiness.state.value,
            verification_activity_id=None,
            verification_disposition=None,
            verification_floor_activity_id=None,
            gateway_outcome=proposal.evaluation.outcome.value,
            assessment_id=None,
            revision_id=None,
            semantic_activity_id=None,
            canonical_effect_committed=False,
            replayed=False,
        )
    if readiness.state is DecisionReadinessState.HUMAN_INPUT_REQUIRED:
        return GovernedEligibilityOrchestrationResult(
            schema_version=ELIGIBILITY_ORCHESTRATION_SCHEMA_VERSION,
            state=GovernedEligibilityOrchestrationState.HUMAN_INPUT_REQUIRED,
            trace_id=proposal.evaluation.trace_id,
            proposal_activity_id=proposal.attempt_activity.id,
            readiness_state=readiness.state.value,
            verification_activity_id=None,
            verification_disposition=None,
            verification_floor_activity_id=None,
            gateway_outcome=proposal.evaluation.outcome.value,
            assessment_id=None,
            revision_id=None,
            semantic_activity_id=None,
            canonical_effect_committed=False,
            replayed=False,
        )

    try:
        verification = verify_eligibility_proposal_independently(
            session,
            proposal=proposal,
            readiness=readiness,
            verification_work_item_id=verification_work_item_id,
            verifier_position_key=execution_plan.verifier_position_key,
            verifier_runtime_profile=execution_plan.verifier_runtime_profile,
            provider=execution_plan.verifier_provider,
            idempotency_key=f"{key}:independent-verification",
        )
    except IndependentEligibilityVerificationRuntimeError as exc:
        try:
            record_attributed_eligibility_runtime_health_incident(
                session,
                tenant_key=tenant,
                aggregate_key=circuit_scope.aggregate_key,
                incident_key=f"{key}:verifier-runtime-health",
                execution_role=EligibilityRuntimeExecutionRole.VERIFIER,
                position_key=execution_plan.verifier_position_key,
                runtime_profile=execution_plan.verifier_runtime_profile,
                summary="Eligibility verifier runtime failed before independent verification could complete.",
                failure_provenance=exc.failure_provenance,
                source_activity_id=proposal.attempt_activity.id,
                correlation_key=str(proposal.evaluation.trace_id),
            )
        except (EligibilityImmuneSystemError, RuntimeError) as incident_exc:
            raise GovernedEligibilityOrchestrationIntegrityError(
                "verifier runtime failure could not be persisted as an immune-system incident"
            ) from incident_exc
        raise GovernedEligibilityOrchestrationIntegrityError(
            "independent eligibility verification runtime failed"
        ) from exc
    except IndependentEligibilityVerificationError as exc:
        raise GovernedEligibilityOrchestrationIntegrityError(
            "independent eligibility verification stage failed"
        ) from exc

    if verification.disposition is IndependentVerificationDisposition.DISAGREES:
        try:
            record_eligibility_immune_incident(
                session,
                tenant_key=tenant,
                aggregate_key=circuit_scope.aggregate_key,
                incident_key=f"{key}:verifier-disagreement",
                kind=EligibilityImmuneIncidentKind.VERIFIER_DISAGREEMENT,
                summary=(
                    "Independent eligibility verification disagreed with the proposer; "
                    "the governed vertical stopped before verification-floor or canonical effect integration."
                ),
                source_activity_id=verification.verification_activity.id,
                correlation_key=str(proposal.evaluation.trace_id),
            )
        except EligibilityImmuneSystemError as exc:
            raise GovernedEligibilityOrchestrationIntegrityError(
                "verifier disagreement could not be persisted as an immune-system incident"
            ) from exc
        state = GovernedEligibilityOrchestrationState.VERIFICATION_DISAGREES
    elif verification.disposition is IndependentVerificationDisposition.INSUFFICIENT_BASIS:
        state = GovernedEligibilityOrchestrationState.VERIFICATION_INSUFFICIENT_BASIS
    else:
        state = None
    if state is not None:
        return GovernedEligibilityOrchestrationResult(
            schema_version=ELIGIBILITY_ORCHESTRATION_SCHEMA_VERSION,
            state=state,
            trace_id=proposal.evaluation.trace_id,
            proposal_activity_id=proposal.attempt_activity.id,
            readiness_state=readiness.state.value,
            verification_activity_id=verification.verification_activity.id,
            verification_disposition=verification.disposition.value,
            verification_floor_activity_id=None,
            gateway_outcome=proposal.evaluation.outcome.value,
            assessment_id=None,
            revision_id=None,
            semantic_activity_id=None,
            canonical_effect_committed=False,
            replayed=False,
        )

    try:
        floor = integrate_eligibility_verification_floor(
            session,
            proposal=proposal,
            readiness=readiness,
            verification=verification,
            authority=execution_plan.authority,
        )
    except EligibilityVerificationFloorError as exc:
        raise GovernedEligibilityOrchestrationIntegrityError(
            "eligibility verification-floor integration failed"
        ) from exc

    if not floor.eligible_for_effect_integration:
        return GovernedEligibilityOrchestrationResult(
            schema_version=ELIGIBILITY_ORCHESTRATION_SCHEMA_VERSION,
            state=GovernedEligibilityOrchestrationState.AWAITING_AUTHORITY,
            trace_id=proposal.evaluation.trace_id,
            proposal_activity_id=proposal.attempt_activity.id,
            readiness_state=readiness.state.value,
            verification_activity_id=verification.verification_activity.id,
            verification_disposition=verification.disposition.value,
            verification_floor_activity_id=floor.reevaluation_activity.id,
            gateway_outcome=floor.evaluation.outcome.value,
            assessment_id=None,
            revision_id=None,
            semantic_activity_id=None,
            canonical_effect_committed=False,
            replayed=False,
        )

    try:
        effect = commit_governed_eligibility_effect(
            session,
            proposal=proposal,
            readiness=readiness,
            verification=verification,
            floor=floor,
            authority=execution_plan.authority,
        )
    except EligibilityCanonicalEffectError as exc:
        raise GovernedEligibilityOrchestrationIntegrityError(
            "canonical eligibility effect stage failed"
        ) from exc

    return GovernedEligibilityOrchestrationResult(
        schema_version=ELIGIBILITY_ORCHESTRATION_SCHEMA_VERSION,
        state=GovernedEligibilityOrchestrationState.CANONICAL_EFFECT_COMMITTED,
        trace_id=proposal.evaluation.trace_id,
        proposal_activity_id=proposal.attempt_activity.id,
        readiness_state=readiness.state.value,
        verification_activity_id=verification.verification_activity.id,
        verification_disposition=verification.disposition.value,
        verification_floor_activity_id=floor.reevaluation_activity.id,
        gateway_outcome=effect.evaluation.outcome.value,
        assessment_id=effect.assessment.id,
        revision_id=effect.revision.id,
        semantic_activity_id=effect.semantic_activity.id,
        canonical_effect_committed=effect.canonical_effect_committed,
        replayed=effect.replayed,
    )
