from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import EligibilityAssessment, OrganizationActivity
from app.models.eligibility_revision import EligibilityAssessmentRevision
from app.services.llm_client import LLMProvider
from app.services.organization_agent_runtime import AgentRuntimeProfile
from app.services.organization_decision_readiness import (
    DecisionReadinessError,
    DecisionReadinessState,
    assess_eligibility_decision_readiness,
)
from app.services.organization_eligibility_effect import (
    ELIGIBILITY_CANONICAL_EFFECT_ACTIVITY_TYPE,
    EligibilityCanonicalEffectError,
    commit_governed_eligibility_effect,
)
from app.services.organization_eligibility_transition_intent import (
    GOVERNED_ELIGIBILITY_CAPABILITY,
    EligibilityIntentError,
    governed_eligibility_transition_intent,
)
from app.services.organization_eligibility_verification_floor import (
    EligibilityVerificationFloorError,
    integrate_eligibility_verification_floor,
)
from app.services.organization_governance_kernel import CapabilityAuthority, GatewayOutcome
from app.services.organization_independent_eligibility_verification import (
    IndependentEligibilityVerificationError,
    IndependentVerificationDisposition,
    verify_eligibility_proposal_independently,
)
from app.services.organization_transparency import TransparencyDataError, transparency_activity_record


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
        governance_record = transparency_activity_record(governance)
    except TransparencyDataError as exc:
        raise GovernedEligibilityOrchestrationIntegrityError(
            "durable canonical eligibility governance is malformed"
        ) from exc
    if governance_record.payload.get("governance_record_kind") != "eligibility_canonical_effect_authorization":
        raise GovernedEligibilityOrchestrationIntegrityError(
            "orchestration idempotency key is already owned by a different governance record"
        )
    if governance.work_item_id != proposal_work_item_id:
        raise GovernedEligibilityOrchestrationIntegrityError(
            "completed canonical effect belongs to a different proposal WorkItem"
        )

    revisions = list(
        session.exec(
            select(EligibilityAssessmentRevision).where(
                EligibilityAssessmentRevision.tenant_key == tenant_key,
                EligibilityAssessmentRevision.governance_activity_id == governance.id,
            )
        ).all()
    )
    if len(revisions) != 1:
        raise GovernedEligibilityOrchestrationIntegrityError(
            "completed canonical governance does not resolve to exactly one eligibility revision"
        )
    revision = revisions[0]
    assessment = session.get(EligibilityAssessment, revision.assessment_id)
    semantic = (
        session.get(OrganizationActivity, revision.semantic_activity_id)
        if revision.semantic_activity_id is not None
        else None
    )
    verification = session.get(OrganizationActivity, revision.verification_activity_id)
    floor = session.get(OrganizationActivity, revision.verification_floor_activity_id)
    if assessment is None or semantic is None or verification is None or floor is None:
        raise GovernedEligibilityOrchestrationIntegrityError(
            "completed canonical eligibility effect has torn durable lineage"
        )
    if verification.work_item_id != verification_work_item_id:
        raise GovernedEligibilityOrchestrationIntegrityError(
            "completed canonical effect belongs to a different verification WorkItem"
        )
    if semantic.activity_type != ELIGIBILITY_CANONICAL_EFFECT_ACTIVITY_TYPE:
        raise GovernedEligibilityOrchestrationIntegrityError(
            "completed canonical eligibility effect has the wrong semantic Activity type"
        )
    if semantic.causation_activity_id != governance.id:
        raise GovernedEligibilityOrchestrationIntegrityError(
            "completed canonical eligibility effect lost governance causation"
        )
    if verification.causation_activity_id is None:
        raise GovernedEligibilityOrchestrationIntegrityError(
            "completed independent verification has no E.2 proposal cause"
        )
    if floor.causation_activity_id != verification.id or governance.causation_activity_id != floor.id:
        raise GovernedEligibilityOrchestrationIntegrityError(
            "completed canonical eligibility effect has broken E.2/G.1/G.2/G.3 causation"
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
        proposal_activity_id=verification.causation_activity_id,
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
) -> GovernedEligibilityOrchestrationResult:
    """Run the accepted E.2 → F.1 → G.1 → G.2 → G.3 eligibility vertical.

    The orchestration is intentionally domain-specific. It coordinates already-sealed
    services and does not create a generic workflow/effect framework. Runtime/provider
    and authority inputs arrive only through ``execution_plan``, which is a trusted
    server-side object rather than untrusted request data.

    Exact retries after a committed G.3 effect resolve directly from durable canonical
    governance/revision lineage and do not call either model again.
    """

    tenant = _required_text(tenant_key, label="tenant key")
    key = _required_text(idempotency_key, label="orchestration idempotency key")
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
    )
    if replay is not None:
        return replay

    try:
        proposal = governed_eligibility_transition_intent(
            session,
            tenant_key=tenant,
            position_key=execution_plan.producer_position_key,
            work_item_id=proposal_work_item_id,
            runtime_profile=execution_plan.producer_runtime_profile,
            authority=execution_plan.authority,
            provider=execution_plan.producer_provider,
            idempotency_key=key,
        )
    except EligibilityIntentError as exc:
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
    except IndependentEligibilityVerificationError as exc:
        raise GovernedEligibilityOrchestrationIntegrityError(
            "independent eligibility verification stage failed"
        ) from exc

    if verification.disposition is IndependentVerificationDisposition.DISAGREES:
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
