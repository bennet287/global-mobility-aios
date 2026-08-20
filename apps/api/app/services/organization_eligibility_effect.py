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
from app.services.organization_eligibility_lineage import (
    ELIGIBILITY_CANONICAL_EFFECT_ACTIVITY_TYPE,
    ELIGIBILITY_CANONICAL_EFFECT_SCHEMA_VERSION,
    CanonicalEligibilityLineageError,
    canonical_eligibility_lineage_for_governance,
)
from app.services.organization_eligibility_revision_precondition import (
    EligibilityRevisionPreconditionError,
    eligibility_aggregate_key,
    require_eligibility_revision_precondition_current,
)
from app.services.organization_eligibility_transition_intent import (
    EligibilityProposedState,
    GovernedEligibilityTransitionIntentResult,
)
from app.services.organization_eligibility_verification_floor import (
    ELIGIBILITY_VERIFICATION_FLOOR_SCHEMA_VERSION,
    EligibilityVerificationFloorIntegrityError,
    EligibilityVerificationFloorResult,
    eligibility_command_context,
    integrate_eligibility_verification_floor,
    original_eligibility_attempt_payload,
    rebuild_eligibility_action,
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


class EligibilityCanonicalEffectError(RuntimeError):
    """Base error for the bounded governed canonical eligibility-effect slice."""


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
    """Backward-compatible local name for the canonical eligibility aggregate key."""

    return eligibility_aggregate_key(
        tenant_key=tenant_key,
        lead_id=lead_id,
        pathway_id=pathway_id,
    )


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
    supersedes_revision_id: UUID | None,
) -> str:
    return canonical_json(
        {
            "schema_version": ELIGIBILITY_CANONICAL_EFFECT_SCHEMA_VERSION,
            "canonical_revision_version": revision_version,
            "supersedes_revision_id": (
                str(supersedes_revision_id) if supersedes_revision_id is not None else None
            ),
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
        eligibility_command_context(proposal),
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
            "supersedes_revision_id": (
                str(revision.supersedes_revision_id)
                if revision.supersedes_revision_id is not None
                else None
            ),
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
    """Validate a durable historical effect against the canonical lineage contract."""

    try:
        lineage = canonical_eligibility_lineage_for_governance(
            session,
            tenant_key=proposal.context.tenant_key,
            governance_activity_id=governance_activity.id,
        )
    except CanonicalEligibilityLineageError as exc:
        raise EligibilityCanonicalEffectIntegrityError(
            f"canonical eligibility replay failed durable lineage validation: {exc.code}"
        ) from exc

    revision = lineage.revision
    assessment = lineage.assessment
    semantic = lineage.semantic_activity
    _, pathway = _pathway_identity(session, proposal)
    expected_aggregate_key = _aggregate_key(
        tenant_key=proposal.context.tenant_key,
        lead_id=proposal.intent.lead_id,
        pathway_id=pathway.id,
    )
    precondition = proposal.eligibility_revision_precondition
    expected_effect_fingerprint = _effect_fingerprint(
        proposal=proposal,
        readiness=readiness,
        verification=verification,
        floor=floor,
        aggregate_key=expected_aggregate_key,
        version=revision.version,
    )
    if revision.aggregate_key != expected_aggregate_key:
        raise EligibilityCanonicalEffectIntegrityError("persisted revision has the wrong eligibility aggregate key")
    if revision.effect_fingerprint != expected_effect_fingerprint:
        raise EligibilityCanonicalEffectIntegrityError("persisted revision has the wrong effect fingerprint")
    if revision.version != precondition.next_revision_version:
        raise EligibilityCanonicalEffectIntegrityError("persisted revision has the wrong canonical revision version")
    if revision.supersedes_revision_id != precondition.supersedes_revision_id:
        raise EligibilityCanonicalEffectIntegrityError("persisted revision has the wrong supersession lineage")
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
    if lineage.verification_activity.id != verification.verification_activity.id:
        raise EligibilityCanonicalEffectIntegrityError("persisted revision names a different G.1 verification Activity")
    if lineage.verification_floor_activity.id != floor.reevaluation_activity.id:
        raise EligibilityCanonicalEffectIntegrityError("persisted revision names a different G.2 floor Activity")
    if assessment.lead_id != proposal.intent.lead_id:
        raise EligibilityCanonicalEffectIntegrityError("persisted assessment belongs to a different Lead")
    if assessment.profile_id != proposal.intent.profile_id or assessment.profile_version != proposal.intent.profile_version:
        raise EligibilityCanonicalEffectIntegrityError("persisted assessment belongs to a different Profile version")
    if assessment.status != proposal.intent.proposed_state.value:
        raise EligibilityCanonicalEffectIntegrityError("persisted assessment has a different eligibility state")
    if assessment.target_country != pathway.country or assessment.domain != pathway.domain:
        raise EligibilityCanonicalEffectIntegrityError("persisted assessment has the wrong pathway scope")

    return GovernedEligibilityCanonicalEffectResult(
        schema_version=ELIGIBILITY_CANONICAL_EFFECT_SCHEMA_VERSION,
        evaluation=evaluation,
        assessment=assessment,
        revision=revision,
        governance_activity=lineage.governance_activity,
        semantic_activity=semantic,
        canonical_effect_committed=True,
        mutated=False,
        replayed=True,
    )


def _fresh_revision_precondition(
    session: Session,
    *,
    proposal: GovernedEligibilityTransitionIntentResult,
    pathway: MobilityPathway,
):
    try:
        current = require_eligibility_revision_precondition_current(
            session,
            precondition=proposal.eligibility_revision_precondition,
            lead_id=proposal.intent.lead_id,
            pathway_id=pathway.id,
        )
    except EligibilityRevisionPreconditionError as exc:
        raise EligibilityCanonicalEffectIntegrityError(
            "canonical eligibility reassessment/supersession revision precondition is stale or missing"
        ) from exc
    if current.aggregate_key != _aggregate_key(
        tenant_key=proposal.context.tenant_key,
        lead_id=proposal.intent.lead_id,
        pathway_id=pathway.id,
    ):
        raise EligibilityCanonicalEffectIntegrityError(
            "eligibility reassessment/supersession resolved the wrong aggregate"
        )
    return current


def commit_governed_eligibility_effect(
    session: Session,
    *,
    proposal: GovernedEligibilityTransitionIntentResult,
    readiness: EligibilityDecisionReadinessResult,
    verification: GovernedIndependentEligibilityVerificationResult,
    floor: EligibilityVerificationFloorResult,
    authority: CapabilityAuthority,
) -> GovernedEligibilityCanonicalEffectResult:
    """Commit an initial or superseding canonical eligibility revision.

    Initial creation requires no active canonical revision and produces v1. Reassessment
    requires E.2 to carry the exact active canonical revision version and produces only
    the next revision while marking the prior revision SUPERSEDED in the same transaction.

    Exact retries prioritize durable ``governance:<idempotency_key>`` lineage and remain
    historical: retrying v1 after v2 exists still resolves the original v1 effect.
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
        e2_payload = original_eligibility_attempt_payload(session, proposal)
        idempotency_key = str(e2_payload["idempotency_key"])
        # Replay must not require the historical revision to remain current/ACTIVE.
        action, profile = rebuild_eligibility_action(
            session,
            proposal=proposal,
            idempotency_key=idempotency_key,
            require_current_revision=False,
        )
    except EligibilityVerificationFloorIntegrityError as exc:
        raise EligibilityCanonicalEffectIntegrityError(
            "accepted E.2 action can no longer be reconstructed for G.3"
        ) from exc

    command_context = eligibility_command_context(proposal)
    persisted_governance = _canonical_governance_activity(
        session,
        tenant_key=proposal.context.tenant_key,
        idempotency_key=idempotency_key,
    )
    existing_fingerprint = _persisted_action_fingerprint(persisted_governance)
    evaluation = evaluate_material_action(
        command_context,
        authority,
        action,
        current_version=(action.expected_version if existing_fingerprint is not None else profile.profile_version),
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

    pathway_version, pathway = _pathway_identity(session, proposal)
    # Fresh execution must still own the exact revision expectation carried by E.2.
    session.expire_all()
    revision_precondition = _fresh_revision_precondition(
        session,
        proposal=proposal,
        pathway=pathway,
    )

    try:
        action, profile = rebuild_eligibility_action(
            session,
            proposal=proposal,
            idempotency_key=idempotency_key,
            require_current_revision=True,
        )
        fresh_floor = integrate_eligibility_verification_floor(
            session,
            proposal=proposal,
            readiness=readiness,
            verification=verification,
            authority=authority,
        )
    except EligibilityVerificationFloorIntegrityError as exc:
        raise EligibilityCanonicalEffectIntegrityError(
            "accepted G.2 verification floor or eligibility revision precondition is no longer fresh for G.3"
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

    # Re-read the revision precondition after G.2 and immediately before final authorization.
    session.expire_all()
    revision_precondition = _fresh_revision_precondition(
        session,
        proposal=proposal,
        pathway=pathway,
    )

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

    aggregate_key = revision_precondition.aggregate_key
    revision_version = revision_precondition.next_revision_version
    supersedes_revision_id = revision_precondition.supersedes_revision_id
    superseded_revision = (
        session.get(EligibilityAssessmentRevision, supersedes_revision_id)
        if supersedes_revision_id is not None
        else None
    )
    if supersedes_revision_id is not None:
        if superseded_revision is None:
            raise EligibilityCanonicalEffectIntegrityError(
                "eligibility reassessment predecessor revision disappeared before commit"
            )
        if (
            superseded_revision.tenant_key != proposal.context.tenant_key
            or superseded_revision.aggregate_key != aggregate_key
            or superseded_revision.version != revision_precondition.current_revision_version
            or superseded_revision.lifecycle_status != "active"
        ):
            raise EligibilityCanonicalEffectIntegrityError(
                "eligibility reassessment predecessor is no longer the expected active revision"
            )

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
                "canonical_revision_version": revision_version,
                "expected_eligibility_revision_version": (
                    revision_precondition.expected_revision_version
                ),
                "supersedes_revision_id": (
                    str(supersedes_revision_id) if supersedes_revision_id is not None else None
                ),
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
                supersedes_revision_id=supersedes_revision_id,
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

        if superseded_revision is not None:
            superseded_revision.lifecycle_status = "superseded"
            session.add(superseded_revision)

        revision = EligibilityAssessmentRevision(
            assessment_id=assessment.id,
            tenant_key=proposal.context.tenant_key,
            aggregate_key=aggregate_key,
            version=revision_version,
            lifecycle_status="active",
            supersedes_revision_id=supersedes_revision_id,
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
        session.flush()

        trace = activities_for_trace(
            session,
            tenant_key=proposal.context.tenant_key,
            trace_id=proposal.evaluation.trace_id,
        )
        ids = [record.activity_id for record in trace]
        if governance_activity.id not in ids or semantic_activity.id not in ids:
            raise EligibilityCanonicalEffectIntegrityError(
                "staged canonical eligibility effect is missing from Board trace lineage"
            )
        if semantic_activity.causation_activity_id != governance_activity.id:
            raise EligibilityCanonicalEffectIntegrityError(
                "canonical eligibility semantic effect lost governance causation"
            )

        session.commit()
        session.refresh(assessment)
        session.refresh(revision)
        session.refresh(governance_activity)
        session.refresh(semantic_activity)
    except Exception:
        session.rollback()
        raise

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
