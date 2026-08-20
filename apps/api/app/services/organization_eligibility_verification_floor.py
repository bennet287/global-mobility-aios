from __future__ import annotations

from dataclasses import dataclass, replace
from uuid import UUID

from sqlmodel import Session, select

from app.core.organization_constitution import (
    ConsequenceClass,
    MaterialActionType,
    OrganizationActivityClass as ConstitutionalActivityClass,
    RiskTier,
)
from app.models.domain import (
    MobilityPathway,
    MobilityPathwayVersion,
    OrganizationActivity,
    OrganizationActorType,
    Profile,
)
from app.services.organization_activity import stage_activity
from app.services.organization_command import OrganizationCommandContext, canonical_fingerprint
from app.services.organization_decision_readiness import (
    DecisionReadinessError,
    DecisionReadinessState,
    EligibilityDecisionReadinessResult,
    assess_eligibility_decision_readiness,
)
from app.services.organization_eligibility_transition_intent import (
    ELIGIBILITY_INTENT_SCHEMA_VERSION,
    GOVERNED_ELIGIBILITY_CAPABILITY,
    GovernedEligibilityTransitionIntentResult,
)
from app.services.organization_governance_kernel import (
    CapabilityAuthority,
    GatewayEvaluation,
    GatewayOutcome,
    MaterialAction,
    PolicyDisposition,
    evaluate_material_action,
    organization_activity_projection,
)
from app.services.organization_independent_eligibility_verification import (
    INDEPENDENT_ELIGIBILITY_VERIFICATION_SCHEMA_VERSION,
    GovernedIndependentEligibilityVerificationResult,
    IndependentVerificationDisposition,
)
from app.services.organization_transparency import (
    TransparencyDataError,
    activities_for_trace,
    transparency_activity_record,
)


ELIGIBILITY_VERIFICATION_FLOOR_SCHEMA_VERSION = "eligibility-verification-floor.v1"


class EligibilityVerificationFloorError(RuntimeError):
    """Base error for the bounded G.2 verification-floor integration slice."""


class EligibilityVerificationFloorIntegrityError(EligibilityVerificationFloorError):
    """Proposal/readiness/verification lineage is stale, forged, or inconsistent."""


@dataclass(frozen=True)
class EligibilityVerificationFloorResult:
    schema_version: str
    proposal_trace_id: UUID
    verification_activity_id: UUID
    verification_fingerprint: str
    verification_floor_fingerprint: str
    verification_floor_satisfied: bool
    evaluation: GatewayEvaluation
    reevaluation_activity: OrganizationActivity
    gateway_authorized_for_execution: bool
    eligible_for_effect_integration: bool
    canonical_effect_committed: bool = False
    mutated: bool = False


def _command_context(proposal: GovernedEligibilityTransitionIntentResult) -> OrganizationCommandContext:
    context = proposal.context
    return OrganizationCommandContext(
        tenant_key=context.tenant_key,
        actor_id=context.position.position_key,
        actor_type=OrganizationActorType.agent,
        authenticated_user_id="system",
        role="operator",
        department=context.position.department,
        position_key=context.position.position_key,
        authority_level=context.position.authority_level,
    )


def _fresh_readiness(
    session: Session,
    *,
    proposal: GovernedEligibilityTransitionIntentResult,
    readiness: EligibilityDecisionReadinessResult,
) -> EligibilityDecisionReadinessResult:
    if readiness.state is not DecisionReadinessState.READY_FOR_INDEPENDENT_VERIFICATION:
        raise EligibilityVerificationFloorIntegrityError(
            "G.2 accepts only F.1 READY_FOR_INDEPENDENT_VERIFICATION results"
        )
    try:
        current = assess_eligibility_decision_readiness(session, proposal=proposal)
    except DecisionReadinessError as exc:
        raise EligibilityVerificationFloorIntegrityError(
            "accepted eligibility proposal is no longer Decision-Readiness valid"
        ) from exc
    if current.readiness_fingerprint != readiness.readiness_fingerprint:
        raise EligibilityVerificationFloorIntegrityError(
            "Decision Readiness changed before verification-floor integration"
        )
    if not current.ready_for_independent_verification:
        raise EligibilityVerificationFloorIntegrityError(
            "proposal is no longer ready for independent verification"
        )
    return current


def _durable_verification(
    session: Session,
    *,
    proposal: GovernedEligibilityTransitionIntentResult,
    readiness: EligibilityDecisionReadinessResult,
    verification: GovernedIndependentEligibilityVerificationResult,
) -> OrganizationActivity:
    if verification.schema_version != INDEPENDENT_ELIGIBILITY_VERIFICATION_SCHEMA_VERSION:
        raise EligibilityVerificationFloorIntegrityError("unsupported G.1 verification schema")
    if verification.disposition is not IndependentVerificationDisposition.AGREES:
        raise EligibilityVerificationFloorIntegrityError(
            "G.2 requires an accepted G.1 AGREES verification"
        )
    if not verification.independent_verification_completed:
        raise EligibilityVerificationFloorIntegrityError("independent verification is not complete")
    if not verification.eligible_for_verification_floor_integration:
        raise EligibilityVerificationFloorIntegrityError(
            "G.1 verification is not eligible for floor integration"
        )
    if verification.command_gateway_floor_satisfied:
        raise EligibilityVerificationFloorIntegrityError(
            "G.1 may not pre-claim Command Gateway verification-floor satisfaction"
        )
    if verification.authorization_effect or verification.canonical_commit_allowed:
        raise EligibilityVerificationFloorIntegrityError(
            "G.1 verification may not carry authorization or commit authority"
        )
    if verification.proposer_trace_id != proposal.evaluation.trace_id:
        raise EligibilityVerificationFloorIntegrityError("G.1 verification belongs to a different proposal trace")
    if verification.proposer_activity_id != proposal.attempt_activity.id:
        raise EligibilityVerificationFloorIntegrityError("G.1 verification has a different proposer cause")
    if verification.proposer_position_key != proposal.context.position.position_key:
        raise EligibilityVerificationFloorIntegrityError("G.1 verification names a different proposer employee")
    if verification.proposer_runtime_binding_hash != proposal.runtime_binding.binding_hash:
        raise EligibilityVerificationFloorIntegrityError("G.1 verification names a different proposer runtime binding")
    if verification.readiness_fingerprint != readiness.readiness_fingerprint:
        raise EligibilityVerificationFloorIntegrityError("G.1 verification names a different readiness result")

    activity = session.get(OrganizationActivity, verification.verification_activity.id)
    if activity is None:
        raise EligibilityVerificationFloorIntegrityError("durable G.1 verification Activity was not found")
    try:
        record = transparency_activity_record(activity)
    except TransparencyDataError as exc:
        raise EligibilityVerificationFloorIntegrityError("durable G.1 verification Activity is malformed") from exc

    if record.activity_type != "verification.eligibility.independent.v1":
        raise EligibilityVerificationFloorIntegrityError("durable G.1 Activity has the wrong verification type")
    if record.constitutional_activity_class is not ConstitutionalActivityClass.MATERIAL:
        raise EligibilityVerificationFloorIntegrityError("durable G.1 verification is not MATERIAL lineage")
    if record.causation_activity_id != proposal.attempt_activity.id:
        raise EligibilityVerificationFloorIntegrityError("durable G.1 verification has the wrong causal proposal")
    if record.trace_id != str(proposal.evaluation.trace_id):
        raise EligibilityVerificationFloorIntegrityError("durable G.1 verification has the wrong trace")

    payload = record.payload
    expected = {
        "verification_schema_version": INDEPENDENT_ELIGIBILITY_VERIFICATION_SCHEMA_VERSION,
        "verification_mode": "PRE_COMMIT",
        "verification_kind": "independent_eligibility_verification",
        "verification_fingerprint": verification.verification_fingerprint,
        "disposition": IndependentVerificationDisposition.AGREES.value,
        "proposer_trace_id": str(proposal.evaluation.trace_id),
        "proposer_activity_id": str(proposal.attempt_activity.id),
        "proposer_position_key": proposal.context.position.position_key,
        "proposer_runtime_binding_hash": proposal.runtime_binding.binding_hash,
        "readiness_fingerprint": readiness.readiness_fingerprint,
        "verifier_position_key": verification.verifier_context.position.position_key,
        "verifier_context_hash": verification.verifier_context.context_hash,
        "verifier_runtime_binding_hash": verification.verifier_runtime_binding.binding_hash,
        "blind_review": True,
        "proposer_conclusion_exposed": False,
        "independent_verification_completed": True,
        "eligible_for_verification_floor_integration": True,
        "command_gateway_floor_satisfied": False,
        "authorization_effect": False,
        "canonical_commit_allowed": False,
    }
    for key, value in expected.items():
        if payload.get(key) != value:
            raise EligibilityVerificationFloorIntegrityError(
                f"durable G.1 verification does not match field {key!r}"
            )
    return activity


def _original_e2_payload(
    session: Session,
    proposal: GovernedEligibilityTransitionIntentResult,
) -> dict[str, object]:
    if proposal.schema_version != ELIGIBILITY_INTENT_SCHEMA_VERSION:
        raise EligibilityVerificationFloorIntegrityError("unsupported E.2 eligibility-intent schema")
    activity = session.get(OrganizationActivity, proposal.attempt_activity.id)
    if activity is None:
        raise EligibilityVerificationFloorIntegrityError("durable E.2 governance attempt was not found")
    try:
        record = transparency_activity_record(activity)
    except TransparencyDataError as exc:
        raise EligibilityVerificationFloorIntegrityError("durable E.2 governance attempt is malformed") from exc
    payload = dict(record.payload)
    if payload.get("governance_record_kind") != "eligibility_intent_attempt":
        raise EligibilityVerificationFloorIntegrityError("durable E.2 record is not an eligibility intent attempt")
    if payload.get("action_fingerprint") != proposal.evaluation.action_fingerprint:
        raise EligibilityVerificationFloorIntegrityError("durable E.2 action fingerprint changed")
    idempotency_key = payload.get("idempotency_key")
    if not isinstance(idempotency_key, str) or not idempotency_key.strip():
        raise EligibilityVerificationFloorIntegrityError("durable E.2 attempt lacks its idempotency key")
    return payload


def _rebuild_action(
    session: Session,
    *,
    proposal: GovernedEligibilityTransitionIntentResult,
    idempotency_key: str,
) -> tuple[MaterialAction, Profile]:
    profile = session.get(Profile, proposal.intent.profile_id)
    if profile is None or profile.profile_version != proposal.intent.profile_version:
        raise EligibilityVerificationFloorIntegrityError("eligibility Profile precondition is stale")
    pathway_version = session.get(MobilityPathwayVersion, proposal.intent.pathway_version_id)
    if pathway_version is None:
        raise EligibilityVerificationFloorIntegrityError("governed pathway version is unavailable")
    pathway = session.get(MobilityPathway, pathway_version.pathway_id)
    if pathway is None:
        raise EligibilityVerificationFloorIntegrityError("governed pathway is unavailable")

    action = MaterialAction(
        action_type=MaterialActionType.ELIGIBILITY_TRANSITION,
        capability=GOVERNED_ELIGIBILITY_CAPABILITY,
        subject_type="lead_eligibility",
        subject_id=str(proposal.intent.lead_id),
        idempotency_key=idempotency_key,
        expected_version=proposal.intent.profile_version,
        proposed_change={
            "proposed_state": proposal.intent.proposed_state.value,
            "profile_id": str(proposal.intent.profile_id),
            "profile_version": proposal.intent.profile_version,
            "pathway_version_id": str(proposal.intent.pathway_version_id),
            "context_hash": proposal.context.context_hash,
            "runtime_binding_hash": proposal.runtime_binding.binding_hash,
            "intent_fingerprint": proposal.intent_fingerprint,
        },
        scope_key=f"{pathway.country.casefold()}:{pathway.domain.casefold()}",
        evidence_refs=tuple(sorted((*proposal.intent.evidence_basis, *proposal.intent.rule_basis))),
        rationale=proposal.intent.rationale,
        consequence_class=ConsequenceClass.APPEND_ONLY_CORRECTION,
        trace_id=proposal.evaluation.trace_id,
        requested_at=proposal.attempt_activity.occurred_at,
    )
    return action, profile


def _floor_fingerprint(
    *,
    proposal: GovernedEligibilityTransitionIntentResult,
    readiness: EligibilityDecisionReadinessResult,
    verification: GovernedIndependentEligibilityVerificationResult,
    authority: CapabilityAuthority,
) -> str:
    return canonical_fingerprint(
        {
            "schema_version": ELIGIBILITY_VERIFICATION_FLOOR_SCHEMA_VERSION,
            "proposal_trace_id": str(proposal.evaluation.trace_id),
            "proposal_action_fingerprint": proposal.evaluation.action_fingerprint,
            "readiness_fingerprint": readiness.readiness_fingerprint,
            "verification_fingerprint": verification.verification_fingerprint,
            "authority": {
                "tenant_key": authority.tenant_key,
                "actor_id": authority.actor_id,
                "capability": authority.capability,
                "allowed_action_types": tuple(sorted(item.value for item in authority.allowed_action_types)),
                "max_risk_tier": authority.max_risk_tier.value,
                "autonomy_level": authority.autonomy_level.value,
                "allowed_scopes": tuple(sorted(authority.allowed_scopes)),
            },
        }
    )


def _existing_floor_activity(
    session: Session,
    *,
    tenant_key: str,
    floor_fingerprint: str,
) -> OrganizationActivity | None:
    return session.exec(
        select(OrganizationActivity).where(
            OrganizationActivity.tenant_key == tenant_key,
            OrganizationActivity.activity_key == f"governance:verification-floor:{floor_fingerprint}",
        )
    ).first()


def _persist_floor_reevaluation(
    session: Session,
    *,
    proposal: GovernedEligibilityTransitionIntentResult,
    verification: GovernedIndependentEligibilityVerificationResult,
    action: MaterialAction,
    evaluation: GatewayEvaluation,
    floor_fingerprint: str,
) -> OrganizationActivity:
    existing = _existing_floor_activity(
        session,
        tenant_key=proposal.context.tenant_key,
        floor_fingerprint=floor_fingerprint,
    )
    if existing is not None:
        try:
            record = transparency_activity_record(existing)
        except TransparencyDataError as exc:
            raise EligibilityVerificationFloorIntegrityError("persisted G.2 floor record is malformed") from exc
        if record.payload.get("verification_floor_fingerprint") != floor_fingerprint:
            raise EligibilityVerificationFloorIntegrityError("persisted G.2 floor record fingerprint conflicts")
        return existing

    command_context = _command_context(proposal)
    projection = organization_activity_projection(command_context, action, evaluation)
    trace_context = replace(command_context, correlation_key=str(evaluation.trace_id))
    activity = stage_activity(
        session,
        trace_context,
        activity_key=f"governance:verification-floor:{floor_fingerprint}",
        stream_key=projection.stream_key,
        activity_class=projection.activity_class,
        activity_type="governance.eligibility.verification_floor.v1",
        title="Eligibility verification floor re-evaluated",
        summary=(
            f"Independent verification floor satisfied; Gateway outcome={evaluation.outcome.value}; "
            "no canonical eligibility effect committed."
        ),
        source_object_type=projection.source_object_type,
        source_object_id=projection.source_object_id,
        source_object_version=projection.source_object_version,
        work_item_id=proposal.intent.work_item_id,
        lead_id=proposal.intent.lead_id,
        profile_id=proposal.intent.profile_id,
        causation_activity_id=verification.verification_activity.id,
        occurred_at=action.requested_at,
        payload={
            **dict(projection.payload),
            "governance_record_kind": "eligibility_verification_floor_reevaluation",
            "verification_floor_schema_version": ELIGIBILITY_VERIFICATION_FLOOR_SCHEMA_VERSION,
            "verification_floor_fingerprint": floor_fingerprint,
            "verification_floor_satisfied": True,
            "verification_fingerprint": verification.verification_fingerprint,
            "verification_activity_id": str(verification.verification_activity.id),
            "readiness_fingerprint": verification.readiness_fingerprint,
            "original_e2_action_fingerprint": proposal.evaluation.action_fingerprint,
            "gateway_authorized_for_execution": evaluation.authorized_for_execution,
            "eligible_for_effect_integration": evaluation.authorized_for_execution,
            "canonical_effect_committed": False,
            "mutated": False,
        },
        correlation_key=str(evaluation.trace_id),
    )
    session.commit()
    session.refresh(activity)
    return activity


def integrate_eligibility_verification_floor(
    session: Session,
    *,
    proposal: GovernedEligibilityTransitionIntentResult,
    readiness: EligibilityDecisionReadinessResult,
    verification: GovernedIndependentEligibilityVerificationResult,
    authority: CapabilityAuthority,
) -> EligibilityVerificationFloorResult:
    """Run G.2: accepted G.1 agreement → verified policy floor → Gateway re-evaluation.

    G.2 does not mutate eligibility state and deliberately does not occupy the canonical
    `governance:<idempotency_key>` success record. It proves only that a durable,
    agreeing independent verification may remove E.2's domain-specific HUMAN_REQUIRED
    policy floor. The existing Command Gateway still decides authority, scope, risk,
    version and autonomy outcomes from scratch.
    """

    current_readiness = _fresh_readiness(session, proposal=proposal, readiness=readiness)
    verification_activity = _durable_verification(
        session,
        proposal=proposal,
        readiness=current_readiness,
        verification=verification,
    )
    e2_payload = _original_e2_payload(session, proposal)
    idempotency_key = str(e2_payload["idempotency_key"])
    action, profile = _rebuild_action(
        session,
        proposal=proposal,
        idempotency_key=idempotency_key,
    )
    command_context = _command_context(proposal)

    evaluation = evaluate_material_action(
        command_context,
        authority,
        action,
        current_version=profile.profile_version,
        policy_disposition=PolicyDisposition.ALLOW,
    )
    if evaluation.action_fingerprint != proposal.evaluation.action_fingerprint:
        raise EligibilityVerificationFloorIntegrityError(
            "G.2 did not reconstruct the exact accepted E.2 MaterialAction"
        )
    if evaluation.effective_risk_tier is not RiskTier.R3:
        raise EligibilityVerificationFloorIntegrityError("eligibility transition lost its R3 risk floor")
    if evaluation.constitutional_activity_class is not ConstitutionalActivityClass.MATERIAL:
        raise EligibilityVerificationFloorIntegrityError("eligibility transition lost MATERIAL classification")

    floor_fingerprint = _floor_fingerprint(
        proposal=proposal,
        readiness=current_readiness,
        verification=verification,
        authority=authority,
    )
    activity = _persist_floor_reevaluation(
        session,
        proposal=proposal,
        verification=verification,
        action=action,
        evaluation=evaluation,
        floor_fingerprint=floor_fingerprint,
    )

    trace = activities_for_trace(
        session,
        tenant_key=proposal.context.tenant_key,
        trace_id=proposal.evaluation.trace_id,
    )
    if not any(record.activity_id == verification_activity.id for record in trace):
        raise EligibilityVerificationFloorIntegrityError("accepted G.1 verification is missing from trace lineage")
    if not any(record.activity_id == activity.id for record in trace):
        raise EligibilityVerificationFloorIntegrityError("G.2 re-evaluation is missing from trace lineage")

    authorized = evaluation.outcome is GatewayOutcome.AUTO_EXECUTE
    return EligibilityVerificationFloorResult(
        schema_version=ELIGIBILITY_VERIFICATION_FLOOR_SCHEMA_VERSION,
        proposal_trace_id=proposal.evaluation.trace_id,
        verification_activity_id=verification_activity.id,
        verification_fingerprint=verification.verification_fingerprint,
        verification_floor_fingerprint=floor_fingerprint,
        verification_floor_satisfied=True,
        evaluation=evaluation,
        reevaluation_activity=activity,
        gateway_authorized_for_execution=authorized,
        eligible_for_effect_integration=authorized,
        canonical_effect_committed=False,
        mutated=False,
    )
