from __future__ import annotations

from dataclasses import dataclass, replace
from uuid import UUID

from sqlmodel import Session, select

from app.core.organization_constitution import OrganizationActivityClass as ConstitutionalActivityClass
from app.models.domain import (
    EligibilityAssessment,
    MobilityPathway,
    MobilityPathwayVersion,
    OrganizationActivity,
    OrganizationActivityClass,
    now_utc,
)
from app.models.eligibility_revision import EligibilityAssessmentRevision
from app.services.organization_activity import stage_activity
from app.services.organization_command import canonical_fingerprint, canonical_json
from app.services.organization_decision_readiness import EligibilityDecisionReadinessResult
from app.services.organization_eligibility_transition_intent import (
    EligibilityProposedState,
    GovernedEligibilityTransitionIntentResult,
)
from app.services.organization_eligibility_verification_floor import (
    ELIGIBILITY_VERIFICATION_FLOOR_SCHEMA_VERSION,
    EligibilityVerificationFloorIntegrityError,
    EligibilityVerificationFloorResult,
    _command_context,
    _original_e2_payload,
    _rebuild_action,
    integrate_eligibility_verification_floor,
)
from app.services.organization_governance_kernel import (
    CapabilityAuthority,
    GatewayEvaluation,
    GatewayOutcome,
    PolicyDisposition,
    evaluate_material_action,
    material_action_fingerprint,
    organization_activity_projection,
)
from app.services.organization_independent_eligibility_verification import (
    GovernedIndependentEligibilityVerificationResult,
    IndependentVerificationDisposition,
)
from app.services.organization_transparency import (
    TransparencyDataError,
    activities_for_trace,
    transparency_activity_record,
)


ELIGIBILITY_CANONICAL_EFFECT_SCHEMA_VERSION = "eligibility-canonical-effect.v1"
ELIGIBILITY_CANONICAL_EFFECT_ACTIVITY_TYPE = "organization.eligibility.assessment_committed.v1"


class EligibilityCanonicalEffectError(RuntimeError):
    """Base error for the bounded G.3 canonical eligibility-effect slice."""


class EligibilityCanonicalEffectIntegrityError(EligibilityCanonicalEffectError):
    """Accepted E.2/F.1/G.1/G.2 lineage or persisted effect state is inconsistent."""


class EligibilityCanonicalEffectNotAuthorized(EligibilityCanonicalEffectError):
    """The current Command Gateway result does not authorize the canonical effect."""


@dataclass(frozen=True)
class GovernedEligibilityCanonicalEffectResult:
    schema_version: str
    evaluation: GatewayEvaluation
    assessment: EligibilityAssessment
    revision: EligibilityAssessmentRevision
    governance_activity: OrganizationActivity
    semantic_activity: OrganizationActivity
    canonical_effect_committed: bool
    mutated: bool
    replayed: bool


def _canonical_governance_activity(
    session: Session,
    *,
    tenant_key: str,
    idempotency_key: str,
) -> OrganizationActivity | None:
    return session.exec(
        select(OrganizationActivity).where(
            OrganizationActivity.tenant_key == tenant_key,
            OrganizationActivity.activity_key == f"governance:{idempotency_key}",
        )
    ).first()


def _persisted_action_fingerprint(activity: OrganizationActivity | None) -> str | None:
    if activity is None:
        return None
    try:
        record = transparency_activity_record(activity)
    except TransparencyDataError as exc:
        raise EligibilityCanonicalEffectIntegrityError(
            "persisted canonical eligibility governance Activity is malformed"
        ) from exc
    fingerprint = record.payload.get("action_fingerprint")
    if not isinstance(fingerprint, str) or len(fingerprint) != 64:
        raise EligibilityCanonicalEffectIntegrityError(
            "persisted canonical eligibility governance Activity lacks a valid action fingerprint"
        )
    if record.payload.get("governance_record_kind") != "eligibility_canonical_effect_authorization":
        raise EligibilityCanonicalEffectIntegrityError(
            "persisted canonical eligibility governance Activity has the wrong record kind"
        )
    return fingerprint


def _require_floor_contract(
    *,
    proposal: GovernedEligibilityTransitionIntentResult,
    verification: GovernedIndependentEligibilityVerificationResult,
    floor: EligibilityVerificationFloorResult,
) -> None:
    if floor.schema_version != ELIGIBILITY_VERIFICATION_FLOOR_SCHEMA_VERSION:
        raise EligibilityCanonicalEffectIntegrityError("unsupported G.2 verification-floor schema")
    if floor.proposal_trace_id != proposal.evaluation.trace_id:
        raise EligibilityCanonicalEffectIntegrityError("G.2 floor belongs to a different E.2 proposal trace")
    if floor.verification_activity_id != verification.verification_activity.id:
        raise EligibilityCanonicalEffectIntegrityError("G.2 floor names a different G.1 verification Activity")
    if floor.verification_fingerprint != verification.verification_fingerprint:
        raise EligibilityCanonicalEffectIntegrityError("G.2 floor names a different G.1 verification fingerprint")
    if not floor.verification_floor_satisfied:
        raise EligibilityCanonicalEffectIntegrityError("G.2 verification floor is not satisfied")
    if floor.canonical_effect_committed or floor.mutated:
        raise EligibilityCanonicalEffectIntegrityError(
            "G.2 may not pre-claim a canonical eligibility effect"
        )


def _pathway_identity(
    session: Session,
    proposal: GovernedEligibilityTransitionIntentResult,
) -> tuple[MobilityPathwayVersion, MobilityPathway]:
    version = session.get(MobilityPathwayVersion, proposal.intent.pathway_version_id)
    if version is None:
        raise EligibilityCanonicalEffectIntegrityError("governed pathway version is unavailable")
    pathway = session.get(MobilityPathway, version.pathway_id)
    if pathway is None:
        raise EligibilityCanonicalEffectIntegrityError("governed pathway is unavailable")
    return version, pathway


def _aggregate_key(
    *,
    tenant_key: str,
    lead_id: UUID,
    pathway_id: UUID,
) -> str:
    return f"eligibility:{tenant_key}:{lead_id}:{pathway_id}"


def _active_canonical_revisions(
    session: Session,
    *,
    tenant_key: str,
    aggregate_key: str,
) -> list[EligibilityAssessmentRevision]:
    return list(
        session.exec(
            select(EligibilityAssessmentRevision).where(
                EligibilityAssessmentRevision.tenant_key == tenant_key,
                EligibilityAssessmentRevision.aggregate_key == aggregate_key,
                EligibilityAssessmentRevision.lifecycle_status == "active",
            )
        ).all()
    )


def _effect_fingerprint(
    *,
    proposal: GovernedEligibilityTransitionIntentResult,
    readiness: EligibilityDecisionReadinessResult,
    verification: GovernedIndependentEligibilityVerificationResult,
    floor: EligibilityVerificationFloorResult,
    aggregate_key: str,
    version: int,
) -> str:
    return canonical_fingerprint(
        {
            "schema_version": ELIGIBILITY_CANONICAL_EFFECT_SCHEMA_VERSION,
            "aggregate_key": aggregate_key,
            "version": version,
            "action_fingerprint": proposal.evaluation.action_fingerprint,
            "intent_fingerprint": proposal.intent_fingerprint,
            "readiness_fingerprint": readiness.readiness_fingerprint,
            "verification_fingerprint": verification.verification_fingerprint,
            "verification_floor_fingerprint": floor.verification_floor_fingerprint,
            "proposed_state": proposal.intent.proposed_state.value,
            "evidence_basis": tuple(proposal.intent.evidence_basis),
            "rule_basis": tuple(proposal.intent.rule_basis),
        }
    )


def _assessment_payload(
    *,
    proposal: GovernedEligibilityTransitionIntentResult,
    readiness: EligibilityDecisionReadinessResult,
    verification: GovernedIndependentEligibilityVerificationResult,
    floor: EligibilityVerificationFloorResult,
    revision_version: int,
) -> str:
    return canonical_json(
        {
            "schema_version": ELIGIBILITY_CANONICAL_EFFECT_SCHEMA_VERSION,
            "canonical_revision_version": revision_version,
            "proposed_state": proposal.intent.proposed_state.value,
            "pathway_version_id": str(proposal.intent.pathway_version_id),
            "evidence_basis": proposal.intent.evidence_basis,
            "rule_basis": proposal.intent.rule_basis,
            "rationale": proposal.intent.rationale,
            "context_hash": proposal.context.context_hash,
            "runtime_binding_hash": proposal.runtime_binding.binding_hash,
            "intent_fingerprint": proposal.intent_fingerprint,
            "readiness_fingerprint": readiness.readiness_fingerprint,
            "verification_fingerprint": verification.verification_fingerprint,
            "verification_disposition": verification.disposition.value,
            "verification_floor_fingerprint": floor.verification_floor_fingerprint,
            "governed": True,
        }
    )


def _stage_semantic_effect(
    session: Session,
    *,
    proposal: GovernedEligibilityTransitionIntentResult,
    assessment: EligibilityAssessment,
    revision: EligibilityAssessmentRevision,
    governance_activity: OrganizationActivity,
    effect_fingerprint: str,
) -> OrganizationActivity:
    context = replace(
        _command_context(proposal),
        correlation_key=str(proposal.evaluation.trace_id),
    )
    return stage_activity(
        session,
        context,
        activity_key=(
            f"semantic:eligibility:{revision.aggregate_key}:v{revision.version}:{effect_fingerprint}"
        ),
        stream_key=f"eligibility:{revision.aggregate_key}",
        activity_class=OrganizationActivityClass.decision,
        activity_type=ELIGIBILITY_CANONICAL_EFFECT_ACTIVITY_TYPE,
        title="Canonical eligibility assessment committed",
        summary=(
            f"Committed governed eligibility state {assessment.status!r} as canonical revision "
            f"v{revision.version}."
        ),
        source_object_type="eligibility_assessment",
        source_object_id=str(assessment.id),
        source_object_version=str(revision.version),
        work_item_id=proposal.intent.work_item_id,
        lead_id=proposal.intent.lead_id,
        profile_id=proposal.intent.profile_id,
        causation_activity_id=governance_activity.id,
        occurred_at=now_utc(),
        payload={
            "constitutional_activity_class": ConstitutionalActivityClass.MATERIAL.value,
            "effect_contract": ELIGIBILITY_CANONICAL_EFFECT_SCHEMA_VERSION,
            "effect_fingerprint": effect_fingerprint,
            "assessment_id": str(assessment.id),
            "revision_id": str(revision.id),
            "aggregate_key": revision.aggregate_key,
            "revision_version": revision.version,
            "lifecycle_status": revision.lifecycle_status,
            "status": assessment.status,
            "profile_version": revision.profile_version,
            "pathway_version_id": str(revision.pathway_version_id),
            "original_action_fingerprint": revision.original_action_fingerprint,
            "intent_fingerprint": revision.intent_fingerprint,
            "readiness_fingerprint": revision.readiness_fingerprint,
            "verification_fingerprint": revision.verification_fingerprint,
            "verification_floor_fingerprint": revision.verification_floor_fingerprint,
            "post_review_required": revision.post_review_required,
            "client_facing": False,
            "external_action_authorized": False,
        },
        correlation_key=str(proposal.evaluation.trace_id),
    )


def _validate_replay(
    session: Session,
    *,
    proposal: GovernedEligibilityTransitionIntentResult,
    readiness: EligibilityDecisionReadinessResult,
    verification: GovernedIndependentEligibilityVerificationResult,
    floor: EligibilityVerificationFloorResult,
    evaluation: GatewayEvaluation,
    governance_activity: OrganizationActivity,
) -> GovernedEligibilityCanonicalEffectResult:
    revisions = list(
        session.exec(
            select(EligibilityAssessmentRevision).where(
                EligibilityAssessmentRevision.tenant_key == proposal.context.tenant_key,
                EligibilityAssessmentRevision.governance_activity_id == governance_activity.id,
            )
        ).all()
    )
    if len(revisions) != 1:
        raise EligibilityCanonicalEffectIntegrityError(
            "canonical governance replay does not resolve to exactly one EligibilityAssessment revision"
        )
    revision = revisions[0]
    assessment = session.get(EligibilityAssessment, revision.assessment_id)
    semantic = (
        session.get(OrganizationActivity, revision.semantic_activity_id)
        if revision.semantic_activity_id is not None
        else None
    )
    if assessment is None or semantic is None:
        raise EligibilityCanonicalEffectIntegrityError(
            "canonical eligibility replay is missing its assessment or semantic Activity"
        )
    if revision.original_action_fingerprint != proposal.evaluation.action_fingerprint:
        raise EligibilityCanonicalEffectIntegrityError("persisted revision belongs to a different E.2 action")
    if revision.intent_fingerprint != proposal.intent_fingerprint:
        raise EligibilityCanonicalEffectIntegrityError("persisted revision belongs to a different E.2 intent")
    if revision.readiness_fingerprint != readiness.readiness_fingerprint:
        raise EligibilityCanonicalEffectIntegrityError("persisted revision belongs to a different F.1 result")
    if revision.verification_fingerprint != verification.verification_fingerprint:
        raise EligibilityCanonicalEffectIntegrityError("persisted revision belongs to a different G.1 verification")
    if revision.verification_floor_fingerprint != floor.verification_floor_fingerprint:
        raise EligibilityCanonicalEffectIntegrityError("persisted revision belongs to a different G.2 floor")
    if revision.lifecycle_status != "active" or revision.version != 1 or revision.supersedes_revision_id is not None:
        raise EligibilityCanonicalEffectIntegrityError("persisted G.3 first revision violates the v1 aggregate contract")
    if assessment.lead_id != proposal.intent.lead_id:
        raise EligibilityCanonicalEffectIntegrityError("persisted assessment belongs to a different Lead")
    if assessment.profile_id != proposal.intent.profile_id or assessment.profile_version != proposal.intent.profile_version:
        raise EligibilityCanonicalEffectIntegrityError("persisted assessment belongs to a different Profile version")
    if assessment.status != proposal.intent.proposed_state.value:
        raise EligibilityCanonicalEffectIntegrityError("persisted assessment has a different eligibility state")
    try:
        semantic_record = transparency_activity_record(semantic)
    except TransparencyDataError as exc:
        raise EligibilityCanonicalEffectIntegrityError("persisted semantic eligibility Activity is malformed") from exc
    if semantic_record.activity_type != ELIGIBILITY_CANONICAL_EFFECT_ACTIVITY_TYPE:
        raise EligibilityCanonicalEffectIntegrityError("persisted semantic eligibility Activity has the wrong type")
    if semantic_record.causation_activity_id != governance_activity.id:
        raise EligibilityCanonicalEffectIntegrityError("persisted semantic eligibility Activity has the wrong cause")
    if semantic_record.constitutional_activity_class is not ConstitutionalActivityClass.MATERIAL:
        raise EligibilityCanonicalEffectIntegrityError("persisted semantic eligibility Activity is not MATERIAL")
    if semantic_record.payload.get("effect_fingerprint") != revision.effect_fingerprint:
        raise EligibilityCanonicalEffectIntegrityError("persisted semantic eligibility Activity fingerprint conflicts")
    return GovernedEligibilityCanonicalEffectResult(
        schema_version=ELIGIBILITY_CANONICAL_EFFECT_SCHEMA_VERSION,
        evaluation=evaluation,
        assessment=assessment,
        revision=revision,
        governance_activity=governance_activity,
        semantic_activity=semantic,
        canonical_effect_committed=True,
        mutated=False,
        replayed=True,
    )


def commit_governed_eligibility_effect(
    session: Session,
    *,
    proposal: GovernedEligibilityTransitionIntentResult,
    readiness: EligibilityDecisionReadinessResult,
    verification: GovernedIndependentEligibilityVerificationResult,
    floor: EligibilityVerificationFloorResult,
    authority: CapabilityAuthority,
) -> GovernedEligibilityCanonicalEffectResult:
    """Commit the first canonical eligibility effect after accepted E.2/F.1/G.1/G.2.

    This first G.3 slice creates only canonical revision ``v1``. If a canonical active
    revision already exists for the same Lead/pathway aggregate, G.3 fails closed rather
    than inventing reassessment/supersession semantics that E.2 does not yet version.

    Exact retries prioritize the durable ``governance:<idempotency_key>`` record and
    return the already-committed effect even if later case state has moved on.
    """

    _require_floor_contract(proposal=proposal, verification=verification, floor=floor)
    if verification.disposition is not IndependentVerificationDisposition.AGREES:
        raise EligibilityCanonicalEffectIntegrityError("G.3 requires an accepted G.1 AGREES verification")
    if proposal.intent.proposed_state not in {
        EligibilityProposedState.POTENTIALLY_ELIGIBLE,
        EligibilityProposedState.POTENTIALLY_INELIGIBLE,
    }:
        raise EligibilityCanonicalEffectIntegrityError("G.3 accepts only actionable eligibility states")

    try:
        e2_payload = _original_e2_payload(session, proposal)
        idempotency_key = str(e2_payload["idempotency_key"])
        action, profile = _rebuild_action(
            session,
            proposal=proposal,
            idempotency_key=idempotency_key,
        )
    except EligibilityVerificationFloorIntegrityError as exc:
        raise EligibilityCanonicalEffectIntegrityError(
            "accepted E.2 action can no longer be reconstructed for G.3"
        ) from exc

    command_context = _command_context(proposal)
    persisted_governance = _canonical_governance_activity(
        session,
        tenant_key=proposal.context.tenant_key,
        idempotency_key=idempotency_key,
    )
    existing_fingerprint = _persisted_action_fingerprint(persisted_governance)
    evaluation_version = (
        action.expected_version
        if existing_fingerprint is not None and action.expected_version is not None
        else profile.profile_version
    )
    evaluation = evaluate_material_action(
        command_context,
        authority,
        action,
        current_version=evaluation_version,
        existing_idempotency_fingerprint=existing_fingerprint,
        policy_disposition=PolicyDisposition.ALLOW,
    )
    if evaluation.action_fingerprint != proposal.evaluation.action_fingerprint:
        raise EligibilityCanonicalEffectIntegrityError("G.3 did not reconstruct the exact accepted E.2 action")

    if evaluation.outcome is GatewayOutcome.IDEMPOTENT_REPLAY:
        if persisted_governance is None:
            raise EligibilityCanonicalEffectIntegrityError("Gateway replay lacks durable canonical governance")
        return _validate_replay(
            session,
            proposal=proposal,
            readiness=readiness,
            verification=verification,
            floor=floor,
            evaluation=evaluation,
            governance_activity=persisted_governance,
        )
    if existing_fingerprint is not None:
        raise EligibilityCanonicalEffectIntegrityError(
            f"canonical eligibility idempotency key cannot be reused: {evaluation.reason.value}"
        )

    try:
        fresh_floor = integrate_eligibility_verification_floor(
            session,
            proposal=proposal,
            readiness=readiness,
            verification=verification,
            authority=authority,
        )
    except EligibilityVerificationFloorIntegrityError as exc:
        raise EligibilityCanonicalEffectIntegrityError(
            "accepted G.2 verification floor is no longer fresh for G.3"
        ) from exc
    if (
        fresh_floor.verification_floor_fingerprint != floor.verification_floor_fingerprint
        or fresh_floor.reevaluation_activity.id != floor.reevaluation_activity.id
    ):
        raise EligibilityCanonicalEffectIntegrityError(
            "G.2 verification-floor identity changed before canonical effect integration"
        )
    if not fresh_floor.eligible_for_effect_integration:
        raise EligibilityCanonicalEffectNotAuthorized(
            f"verification floor is satisfied but Gateway outcome is {fresh_floor.evaluation.outcome.value}"
        )
    if fresh_floor.evaluation.action_fingerprint != material_action_fingerprint(command_context, action):
        raise EligibilityCanonicalEffectIntegrityError("fresh G.2 action fingerprint changed before G.3")

    # Re-evaluate immediately before staging the real effect. G.2 proves the R3 floor;
    # this evaluation remains the authorization committed atomically with the effect.
    evaluation = evaluate_material_action(
        command_context,
        authority,
        action,
        current_version=profile.profile_version,
        policy_disposition=PolicyDisposition.ALLOW,
    )
    if evaluation.outcome is not GatewayOutcome.AUTO_EXECUTE:
        raise EligibilityCanonicalEffectNotAuthorized(
            f"final Command Gateway outcome is {evaluation.outcome.value}: {evaluation.reason.value}"
        )

    pathway_version, pathway = _pathway_identity(session, proposal)
    aggregate_key = _aggregate_key(
        tenant_key=proposal.context.tenant_key,
        lead_id=proposal.intent.lead_id,
        pathway_id=pathway.id,
    )
    active = _active_canonical_revisions(
        session,
        tenant_key=proposal.context.tenant_key,
        aggregate_key=aggregate_key,
    )
    if active:
        raise EligibilityCanonicalEffectIntegrityError(
            "canonical eligibility aggregate already has an active revision; reassessment/supersession is not yet defined"
        )

    revision_version = 1
    effect_fingerprint = _effect_fingerprint(
        proposal=proposal,
        readiness=readiness,
        verification=verification,
        floor=fresh_floor,
        aggregate_key=aggregate_key,
        version=revision_version,
    )
    projection = organization_activity_projection(command_context, action, evaluation)
    trace_context = replace(command_context, correlation_key=str(evaluation.trace_id))

    try:
        governance_activity = stage_activity(
            session,
            trace_context,
            activity_key=projection.activity_key,
            stream_key=projection.stream_key,
            activity_class=projection.activity_class,
            activity_type=projection.activity_type,
            title=projection.title,
            summary=projection.summary,
            source_object_type=projection.source_object_type,
            source_object_id=projection.source_object_id,
            source_object_version=projection.source_object_version,
            work_item_id=proposal.intent.work_item_id,
            lead_id=proposal.intent.lead_id,
            profile_id=proposal.intent.profile_id,
            causation_activity_id=fresh_floor.reevaluation_activity.id,
            occurred_at=now_utc(),
            payload={
                **dict(projection.payload),
                "governance_record_kind": "eligibility_canonical_effect_authorization",
                "eligibility_effect_schema_version": ELIGIBILITY_CANONICAL_EFFECT_SCHEMA_VERSION,
                "verification_floor_fingerprint": fresh_floor.verification_floor_fingerprint,
                "effect_fingerprint": effect_fingerprint,
            },
            correlation_key=str(evaluation.trace_id),
        )

        assessment = EligibilityAssessment(
            lead_id=proposal.intent.lead_id,
            agent_run_id=None,
            profile_id=proposal.intent.profile_id,
            profile_version=proposal.intent.profile_version,
            target_country=pathway.country,
            domain=pathway.domain,
            overall_score=0.0,
            confidence=proposal.intent.confidence,
            status=proposal.intent.proposed_state.value,
            summary=proposal.intent.rationale,
            assessment_json=_assessment_payload(
                proposal=proposal,
                readiness=readiness,
                verification=verification,
                floor=fresh_floor,
                revision_version=revision_version,
            ),
            risks_json="[]",
            required_documents_json="[]",
            pathways_json=canonical_json(
                [
                    {
                        "pathway_id": str(pathway.id),
                        "pathway_version_id": str(pathway_version.id),
                    }
                ]
            ),
        )
        session.add(assessment)
        session.flush()

        revision = EligibilityAssessmentRevision(
            assessment_id=assessment.id,
            tenant_key=proposal.context.tenant_key,
            aggregate_key=aggregate_key,
            version=revision_version,
            lifecycle_status="active",
            supersedes_revision_id=None,
            lead_id=proposal.intent.lead_id,
            profile_id=proposal.intent.profile_id,
            profile_version=proposal.intent.profile_version,
            pathway_version_id=proposal.intent.pathway_version_id,
            governance_activity_id=governance_activity.id,
            verification_activity_id=verification.verification_activity.id,
            verification_floor_activity_id=fresh_floor.reevaluation_activity.id,
            semantic_activity_id=None,
            original_action_fingerprint=evaluation.action_fingerprint,
            intent_fingerprint=proposal.intent_fingerprint,
            readiness_fingerprint=readiness.readiness_fingerprint,
            verification_fingerprint=verification.verification_fingerprint,
            verification_floor_fingerprint=fresh_floor.verification_floor_fingerprint,
            effect_fingerprint=effect_fingerprint,
            post_review_required=evaluation.post_review_required,
        )
        session.add(revision)
        session.flush()

        semantic_activity = _stage_semantic_effect(
            session,
            proposal=proposal,
            assessment=assessment,
            revision=revision,
            governance_activity=governance_activity,
            effect_fingerprint=effect_fingerprint,
        )
        revision.semantic_activity_id = semantic_activity.id
        session.add(revision)
        session.commit()
        session.refresh(assessment)
        session.refresh(revision)
        session.refresh(governance_activity)
        session.refresh(semantic_activity)
    except Exception:
        session.rollback()
        raise

    trace = activities_for_trace(
        session,
        tenant_key=proposal.context.tenant_key,
        trace_id=proposal.evaluation.trace_id,
    )
    ids = [record.activity_id for record in trace]
    if governance_activity.id not in ids or semantic_activity.id not in ids:
        raise EligibilityCanonicalEffectIntegrityError(
            "committed canonical eligibility effect is missing from Board trace lineage"
        )
    if semantic_activity.causation_activity_id != governance_activity.id:
        raise EligibilityCanonicalEffectIntegrityError(
            "canonical eligibility semantic effect lost governance causation"
        )

    return GovernedEligibilityCanonicalEffectResult(
        schema_version=ELIGIBILITY_CANONICAL_EFFECT_SCHEMA_VERSION,
        evaluation=evaluation,
        assessment=assessment,
        revision=revision,
        governance_activity=governance_activity,
        semantic_activity=semantic_activity,
        canonical_effect_committed=True,
        mutated=True,
        replayed=False,
    )
