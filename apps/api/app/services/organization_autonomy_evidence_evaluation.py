from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlmodel import Session, select

from app.core.organization_constitution import AutonomyLevel
from app.models.autonomy_evidence_profile import CapabilityAutonomyEvidenceObservation
from app.models.autonomy_profile import CapabilityAutonomyProfile
from app.models.domain import (
    OrganizationActivity,
    OrganizationActorType,
    OrganizationHumanAction,
    OrganizationHumanActionType,
    now_utc,
)
from app.models.eligibility_revision import EligibilityAssessmentRevision
from app.services.organization_autonomy_evidence_evaluation_contract import (
    I4_ALWAYS_UNAVAILABLE_DERIVATIONS,
    I4_MAX_CANDIDATE_OBSERVATIONS,
    I4_MAX_PROVENANCE_PAGE_SIZE,
    I4_SUMMARY_PROVENANCE_LIMIT,
    PROVENANCE_QUALIFIED,
    PROVENANCE_STALE_OBSERVATION,
    PROVENANCE_STALE_SOURCE,
    PROVENANCE_UNQUALIFIED_SOURCE,
    AutonomyEvidenceEvaluationBoundExceeded,
    AutonomyEvidenceEvaluationCriterionSnapshot,
    AutonomyEvidenceEvaluationIntegrityError,
    AutonomyEvidenceEvaluationUnsupported,
    AutonomyEvidenceProvenanceSnapshot,
    CapabilityAutonomyEvidenceEvaluationProvenancePage,
    CapabilityAutonomyEvidenceEvaluationSnapshot,
    QualifiedAutonomyEvidenceMetricsSnapshot,
)
from app.services.organization_autonomy_evidence_evaluation_policy import (
    capability_autonomy_evidence_evaluation_policy_snapshot,
)
from app.services.organization_autonomy_evidence_profile import (
    AutonomyEvidenceObservationSnapshot,
    AutonomyEvidenceProfileIntegrityError,
    _validated_observation_snapshot,
)
from app.services.organization_autonomy_profile import (
    AutonomyProfileIntegrityError,
    capability_autonomy_profile_snapshot,
)
from app.services.organization_autonomy_promotion_policy import (
    AutonomyPromotionPolicyIntegrityError,
    AutonomyPromotionPolicyRevisionSnapshot,
    capability_autonomy_promotion_policy_snapshot,
)
from app.services.organization_command import OrganizationCommandError, tenant_record
from app.services.organization_eligibility_lineage import (
    ELIGIBILITY_CANONICAL_EFFECT_ACTIVITY_TYPE,
    CanonicalEligibilityLineage,
    CanonicalEligibilityLineageError,
    validate_canonical_eligibility_lineage,
)


_CURSOR_VERSION = 1
_REVIEW_MAP = {
    OrganizationHumanActionType.approved: "accepted",
    OrganizationHumanActionType.requested_changes: "modified",
    OrganizationHumanActionType.rejected: "rejected",
}


@dataclass(frozen=True, slots=True)
class _QualifiedObservation:
    observation: AutonomyEvidenceObservationSnapshot
    provenance: AutonomyEvidenceProvenanceSnapshot


@dataclass(frozen=True, slots=True)
class _EvaluationComponents:
    snapshot: CapabilityAutonomyEvidenceEvaluationSnapshot
    provenance: tuple[AutonomyEvidenceProvenanceSnapshot, ...]


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _as_of(value: datetime | None) -> datetime:
    if value is not None and value.tzinfo is None:
        raise AutonomyEvidenceEvaluationUnsupported("evaluation_as_of must be timezone-aware")
    return _aware(value or now_utc())


def _rate(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return round(numerator / denominator, 6)


def _criterion(
    key: str,
    comparison: str,
    required: int | float,
    observed: int | float | None,
    *,
    sample: bool = False,
) -> AutonomyEvidenceEvaluationCriterionSnapshot:
    if observed is None:
        return AutonomyEvidenceEvaluationCriterionSnapshot(
            criterion_key=key,
            comparison=comparison,
            required_value=required,
            observed_value=None,
            sample_requirement=sample,
            evaluable=False,
            passed=None,
        )
    if comparison == ">=":
        passed = observed >= required
    elif comparison == "<=":
        passed = observed <= required
    else:
        raise AutonomyEvidenceEvaluationIntegrityError(
            f"unsupported I.4 criterion comparison: {comparison}"
        )
    return AutonomyEvidenceEvaluationCriterionSnapshot(
        criterion_key=key,
        comparison=comparison,
        required_value=required,
        observed_value=observed,
        sample_requirement=sample,
        evaluable=True,
        passed=bool(passed),
    )


def _autonomy_rank(level: str) -> int:
    try:
        return int(AutonomyLevel(level).value[1])
    except (ValueError, IndexError) as exc:
        raise AutonomyEvidenceEvaluationIntegrityError("I.4 encountered an invalid autonomy level") from exc


def _qualified_metrics(
    qualified: tuple[_QualifiedObservation, ...],
) -> QualifiedAutonomyEvidenceMetricsSnapshot:
    provenance = tuple(item.provenance for item in qualified)
    volume = len(provenance)
    grounding_values = tuple(item.evidence_grounded for item in provenance)
    grounded = sum(value is True for value in grounding_values)
    grounding_rate = None if any(value is None for value in grounding_values) else _rate(grounded, volume)
    accepted = sum(item.human_review_outcome == "accepted" for item in provenance)
    modified = sum(item.human_review_outcome == "modified" for item in provenance)
    rejected = sum(item.human_review_outcome == "rejected" for item in provenance)
    not_reviewed = sum(item.human_review_outcome == "not_reviewed" for item in provenance)
    reviewed = accepted + modified + rejected
    contradictions = sum(item.verifier_contradiction is True for item in provenance)
    compliant = sum(item.policy_compliant is True for item in provenance)
    return QualifiedAutonomyEvidenceMetricsSnapshot(
        qualifying_execution_volume=volume,
        evidence_grounded_count=grounded,
        evidence_grounding_rate=grounding_rate,
        human_accepted_count=accepted,
        human_modified_count=modified,
        human_rejected_count=rejected,
        human_not_reviewed_count=not_reviewed,
        human_reviewed_count=reviewed,
        human_acceptance_rate=_rate(accepted, reviewed),
        human_modification_rate=_rate(modified, reviewed),
        human_rejection_rate=_rate(rejected, reviewed),
        verifier_contradiction_count=contradictions,
        verifier_contradiction_rate=_rate(contradictions, volume),
        policy_compliant_count=compliant,
        policy_compliance_rate=_rate(compliant, volume),
        freshness_compliance_rate=None,
        critical_error_count=None,
        recovery_applicable_count=None,
        recovery_success_rate=None,
        sla_met_rate=None,
        incident_count=None,
    )


def _promotion_criteria(
    *,
    policy: AutonomyPromotionPolicyRevisionSnapshot | None,
    metrics: QualifiedAutonomyEvidenceMetricsSnapshot,
    board_ceiling: str,
) -> tuple[AutonomyEvidenceEvaluationCriterionSnapshot, ...]:
    if policy is None:
        return ()
    criteria = [
        _criterion("qualifying_execution_volume", ">=", policy.min_qualifying_execution_volume, metrics.qualifying_execution_volume, sample=True),
        _criterion("human_reviewed_count", ">=", policy.min_human_reviewed_count, metrics.human_reviewed_count, sample=True),
        _criterion("evidence_grounding_rate", ">=", policy.min_evidence_grounding_rate, metrics.evidence_grounding_rate),
        _criterion("human_acceptance_rate", ">=", policy.min_human_acceptance_rate, metrics.human_acceptance_rate),
        _criterion("human_modification_rate", "<=", policy.max_human_modification_rate, metrics.human_modification_rate),
        _criterion("human_rejection_rate", "<=", policy.max_human_rejection_rate, metrics.human_rejection_rate),
        _criterion("verifier_contradiction_rate", "<=", policy.max_verifier_contradiction_rate, metrics.verifier_contradiction_rate),
        _criterion("policy_compliance_rate", ">=", policy.min_policy_compliance_rate, metrics.policy_compliance_rate),
        _criterion("freshness_compliance_rate", ">=", policy.min_freshness_compliance_rate, metrics.freshness_compliance_rate),
        _criterion("critical_error_count", "<=", policy.max_critical_error_count, metrics.critical_error_count),
        _criterion("sla_met_rate", ">=", policy.min_sla_met_rate, metrics.sla_met_rate),
        _criterion("incident_count", "<=", policy.max_incident_count, metrics.incident_count),
        _criterion("target_within_board_ceiling", "<=", _autonomy_rank(board_ceiling), _autonomy_rank(policy.target_autonomy_level)),
    ]
    if policy.min_recovery_success_rate is not None:
        criteria.extend(
            (
                _criterion("recovery_applicable_count", ">=", policy.min_recovery_applicable_count, metrics.recovery_applicable_count, sample=True),
                _criterion("recovery_success_rate", ">=", policy.min_recovery_success_rate, metrics.recovery_success_rate),
            )
        )
    return tuple(criteria)


def _canonical_source(
    session: Session,
    *,
    tenant_key: str,
    activity: OrganizationActivity,
) -> CanonicalEligibilityLineage | None:
    if activity.activity_type != ELIGIBILITY_CANONICAL_EFFECT_ACTIVITY_TYPE:
        return None
    revisions = tuple(
        session.exec(
            select(EligibilityAssessmentRevision).where(
                EligibilityAssessmentRevision.tenant_key == tenant_key,
                EligibilityAssessmentRevision.semantic_activity_id == activity.id,
            )
        ).all()
    )
    if len(revisions) != 1:
        raise AutonomyEvidenceEvaluationIntegrityError(
            "canonical I.4 source Activity does not resolve to exactly one eligibility revision"
        )
    try:
        lineage = validate_canonical_eligibility_lineage(
            session,
            tenant_key=tenant_key,
            revision=revisions[0],
        )
    except CanonicalEligibilityLineageError as exc:
        raise AutonomyEvidenceEvaluationIntegrityError(
            "canonical I.4 eligibility source lineage is invalid"
        ) from exc
    if lineage.semantic_activity.id != activity.id:
        raise AutonomyEvidenceEvaluationIntegrityError("canonical I.4 eligibility source identity drifted")
    return lineage


def _derived_grounding(lineage: CanonicalEligibilityLineage) -> bool | None:
    try:
        payload = json.loads(lineage.assessment.assessment_json or "{}")
    except (TypeError, ValueError) as exc:
        raise AutonomyEvidenceEvaluationIntegrityError("canonical I.4 assessment payload is malformed") from exc
    if not isinstance(payload, dict):
        raise AutonomyEvidenceEvaluationIntegrityError("canonical I.4 assessment payload is malformed")
    evidence_basis = payload.get("evidence_basis")
    rule_basis = payload.get("rule_basis")
    if not isinstance(evidence_basis, list) or not isinstance(rule_basis, list):
        return None
    return bool(evidence_basis and rule_basis)


def _derived_human_review(
    session: Session,
    *,
    tenant_key: str,
    lineage: CanonicalEligibilityLineage,
    evaluation_as_of: datetime,
) -> str:
    rows = tuple(
        session.exec(
            select(OrganizationHumanAction)
            .where(
                OrganizationHumanAction.tenant_key == tenant_key,
                OrganizationHumanAction.source_object_type == "eligibility_assessment",
                OrganizationHumanAction.source_object_id == str(lineage.assessment.id),
                OrganizationHumanAction.source_object_version == str(lineage.revision.version),
                OrganizationHumanAction.occurred_at <= evaluation_as_of,
            )
            .order_by(OrganizationHumanAction.occurred_at.desc(), OrganizationHumanAction.id.desc())
        ).all()
    )
    terminal: list[tuple[OrganizationHumanAction, str]] = []
    for row in rows:
        if row.action_type not in _REVIEW_MAP:
            continue
        if row.actor_type is not OrganizationActorType.human:
            raise AutonomyEvidenceEvaluationIntegrityError(
                "I.4 human review outcome has non-human actor identity"
            )
        if not row.human_actor_id.strip() or len(row.record_fingerprint) != 64:
            raise AutonomyEvidenceEvaluationIntegrityError("I.4 human review outcome identity is invalid")
        terminal.append((row, _REVIEW_MAP[row.action_type]))
    if not terminal:
        return "not_reviewed"
    latest_time = _aware(terminal[0][0].occurred_at)
    same_time = {outcome for row, outcome in terminal if _aware(row.occurred_at) == latest_time}
    if len(same_time) != 1:
        raise AutonomyEvidenceEvaluationIntegrityError(
            "I.4 human review has ambiguous equal-time conflicting outcomes"
        )
    return terminal[0][1]


def _evaluate_components(
    session: Session,
    *,
    tenant_key: str,
    position_key: str,
    capability_key: str,
    context_scope: str,
    evaluation_as_of: datetime | None,
) -> _EvaluationComponents | None:
    as_of = _as_of(evaluation_as_of)
    try:
        profile_snapshot = capability_autonomy_profile_snapshot(
            session,
            tenant_key=tenant_key,
            position_key=position_key,
            capability_key=capability_key,
            context_scope=context_scope,
        )
    except AutonomyProfileIntegrityError as exc:
        raise AutonomyEvidenceEvaluationIntegrityError("I.1 autonomy profile integrity failed") from exc
    if profile_snapshot is None:
        return None
    try:
        profile = tenant_record(
            session,
            CapabilityAutonomyProfile,
            profile_snapshot.current_profile_id,
            tenant_key,
            label="current I.4 autonomy profile",
        )
    except OrganizationCommandError as exc:
        raise AutonomyEvidenceEvaluationIntegrityError("current I.4 autonomy profile is unavailable") from exc

    evaluation_policy = capability_autonomy_evidence_evaluation_policy_snapshot(
        session,
        tenant_key=tenant_key,
        position_key=position_key,
        capability_key=capability_key,
        context_scope=context_scope,
        profile_id=profile.id,
    )
    if evaluation_policy is None:
        return None
    current_evaluation_policy = evaluation_policy.revisions[-1]
    if as_of < _aware(current_evaluation_policy.effective_from):
        raise AutonomyEvidenceEvaluationUnsupported(
            "evaluation_as_of predates the current I.4 evaluation policy"
        )

    observation_cutoff = as_of - timedelta(seconds=evaluation_policy.max_observation_age_seconds)
    source_cutoff = as_of - timedelta(seconds=evaluation_policy.max_source_age_seconds)
    rows = tuple(
        session.exec(
            select(CapabilityAutonomyEvidenceObservation)
            .where(
                CapabilityAutonomyEvidenceObservation.tenant_key == tenant_key,
                CapabilityAutonomyEvidenceObservation.profile_id == profile.id,
                CapabilityAutonomyEvidenceObservation.created_at <= as_of,
            )
            .order_by(
                CapabilityAutonomyEvidenceObservation.created_at.desc(),
                CapabilityAutonomyEvidenceObservation.id.desc(),
            )
            .limit(evaluation_policy.max_candidate_observations + 1)
        ).all()
    )
    if len(rows) > evaluation_policy.max_candidate_observations:
        raise AutonomyEvidenceEvaluationBoundExceeded("I.4 candidate observation bound would be exceeded")

    seen_sources: set[UUID] = set()
    qualified: list[_QualifiedObservation] = []
    provenance: list[AutonomyEvidenceProvenanceSnapshot] = []
    stale_observation_count = 0
    stale_source_count = 0
    unqualified_source_count = 0

    for row in rows:
        if row.source_activity_id in seen_sources:
            raise AutonomyEvidenceEvaluationIntegrityError("I.4 evidence source was counted more than once")
        seen_sources.add(row.source_activity_id)
        try:
            observation = _validated_observation_snapshot(session, profile=profile, observation=row)
        except AutonomyEvidenceProfileIntegrityError as exc:
            raise AutonomyEvidenceEvaluationIntegrityError(
                "I.2 evidence integrity failed during I.4 evaluation"
            ) from exc
        try:
            source = tenant_record(
                session,
                OrganizationActivity,
                observation.source_activity_id,
                tenant_key,
                label="I.4 evidence source Activity",
            )
        except OrganizationCommandError as exc:
            raise AutonomyEvidenceEvaluationIntegrityError("I.4 evidence source Activity is unavailable") from exc
        source_occurred_at = _aware(source.occurred_at)
        observation_created_at = _aware(observation.created_at)
        canonical_revision_id: UUID | None = None
        effect_fingerprint: str | None = None
        human_review_outcome: str | None = None
        evidence_grounded: bool | None = None
        verifier_contradiction: bool | None = None
        policy_compliant: bool | None = None

        if observation_created_at < observation_cutoff:
            disposition = PROVENANCE_STALE_OBSERVATION
            stale_observation_count += 1
        elif source_occurred_at > as_of:
            raise AutonomyEvidenceEvaluationIntegrityError(
                "I.4 evidence source occurs after evaluation_as_of"
            )
        elif source_occurred_at < source_cutoff:
            disposition = PROVENANCE_STALE_SOURCE
            stale_source_count += 1
        else:
            lineage = _canonical_source(session, tenant_key=tenant_key, activity=source)
            if lineage is None:
                disposition = PROVENANCE_UNQUALIFIED_SOURCE
                unqualified_source_count += 1
            else:
                disposition = PROVENANCE_QUALIFIED
                canonical_revision_id = lineage.revision.id
                effect_fingerprint = lineage.revision.effect_fingerprint
                human_review_outcome = _derived_human_review(
                    session,
                    tenant_key=tenant_key,
                    lineage=lineage,
                    evaluation_as_of=as_of,
                )
                evidence_grounded = _derived_grounding(lineage)
                verifier_contradiction = False
                policy_compliant = True

        item = AutonomyEvidenceProvenanceSnapshot(
            observation_id=observation.observation_id,
            source_activity_id=observation.source_activity_id,
            source_activity_type=source.activity_type,
            observation_created_at=observation_created_at,
            source_occurred_at=source_occurred_at,
            disposition=disposition,
            canonical_revision_id=canonical_revision_id,
            effect_fingerprint=effect_fingerprint,
            human_review_outcome=human_review_outcome,
            evidence_grounded=evidence_grounded,
            verifier_contradiction=verifier_contradiction,
            policy_compliant=policy_compliant,
        )
        provenance.append(item)
        if disposition == PROVENANCE_QUALIFIED:
            qualified.append(_QualifiedObservation(observation=observation, provenance=item))

    metrics = _qualified_metrics(tuple(qualified))
    promotion_policy_snapshot = capability_autonomy_promotion_policy_snapshot(
        session,
        tenant_key=tenant_key,
        position_key=position_key,
        capability_key=capability_key,
        context_scope=context_scope,
        from_autonomy_level=profile.autonomy_level,
        evidence_policy_version=profile.evidence_policy_version,
        profile_id=profile.id,
    )
    promotion_policy = promotion_policy_snapshot.revisions[-1] if promotion_policy_snapshot is not None else None
    criteria = _promotion_criteria(policy=promotion_policy, metrics=metrics, board_ceiling=profile.board_ceiling)
    promotion_grade_ready = bool(criteria) and all(
        item.evaluable and item.passed is True for item in criteria
    )

    snapshot = CapabilityAutonomyEvidenceEvaluationSnapshot(
        profile_id=profile.id,
        profile_sequence=profile.profile_sequence,
        profile_record_fingerprint=profile.record_fingerprint,
        position_key=profile.position_key,
        capability_key=profile.capability_key,
        context_scope=profile.context_scope,
        current_autonomy_level=profile.autonomy_level,
        board_ceiling=profile.board_ceiling,
        evidence_policy_version=profile.evidence_policy_version,
        evaluation_policy_id=evaluation_policy.current_policy_id,
        evaluation_policy_sequence=evaluation_policy.current_policy_sequence,
        qualification_contract=evaluation_policy.qualification_contract,
        evaluation_as_of=as_of,
        observation_cutoff=observation_cutoff,
        source_cutoff=source_cutoff,
        candidate_count=len(rows),
        qualified_count=len(qualified),
        excluded_stale_observation_count=stale_observation_count,
        excluded_stale_source_count=stale_source_count,
        excluded_unqualified_source_count=unqualified_source_count,
        missing_derivation_fields=tuple(I4_ALWAYS_UNAVAILABLE_DERIVATIONS),
        promotion_policy_id=(promotion_policy.policy_id if promotion_policy else None),
        promotion_policy_sequence=(promotion_policy.policy_sequence if promotion_policy else None),
        target_autonomy_level=(promotion_policy.target_autonomy_level if promotion_policy else None),
        promotion_grade_ready=promotion_grade_ready,
        metrics=metrics,
        criteria=criteria,
        recent_provenance=tuple(provenance[:I4_SUMMARY_PROVENANCE_LIMIT]),
    )
    return _EvaluationComponents(snapshot=snapshot, provenance=tuple(provenance))


def capability_autonomy_evidence_evaluation_snapshot(
    session: Session,
    *,
    tenant_key: str,
    position_key: str,
    capability_key: str,
    context_scope: str,
    evaluation_as_of: datetime | None = None,
) -> CapabilityAutonomyEvidenceEvaluationSnapshot | None:
    """Return bounded, source-qualified and time-bounded I.4 evidence truth.

    This projection is read-only. `promotion_grade_ready` is transparency only;
    it grants no authority and does not mutate I.1 autonomy truth.
    """
    components = _evaluate_components(
        session,
        tenant_key=tenant_key,
        position_key=position_key,
        capability_key=capability_key,
        context_scope=context_scope,
        evaluation_as_of=evaluation_as_of,
    )
    return components.snapshot if components is not None else None


def _encode_cursor(
    *,
    evaluation_as_of: datetime,
    offset: int,
    profile_id: UUID,
    evaluation_policy_id: UUID,
) -> str:
    raw = json.dumps(
        {
            "v": _CURSOR_VERSION,
            "evaluation_as_of": _aware(evaluation_as_of).isoformat(),
            "offset": offset,
            "profile_id": str(profile_id),
            "evaluation_policy_id": str(evaluation_policy_id),
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _decode_cursor(cursor: str) -> tuple[datetime, int, UUID, UUID]:
    try:
        padding = "=" * (-len(cursor) % 4)
        payload = json.loads(base64.urlsafe_b64decode(cursor + padding).decode("utf-8"))
        if payload.get("v") != _CURSOR_VERSION:
            raise ValueError("unsupported cursor version")
        as_of = _aware(datetime.fromisoformat(payload["evaluation_as_of"]))
        offset = int(payload["offset"])
        profile_id = UUID(payload["profile_id"])
        policy_id = UUID(payload["evaluation_policy_id"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("invalid I.4 provenance cursor") from exc
    if offset < 0:
        raise ValueError("invalid I.4 provenance cursor")
    return as_of, offset, profile_id, policy_id


def capability_autonomy_evidence_evaluation_provenance_page(
    session: Session,
    *,
    tenant_key: str,
    position_key: str,
    capability_key: str,
    context_scope: str,
    page_limit: int = 50,
    cursor: str | None = None,
    evaluation_as_of: datetime | None = None,
) -> CapabilityAutonomyEvidenceEvaluationProvenancePage | None:
    """Return stable newest-first I.4 provenance without unbounded nesting."""
    if not 1 <= page_limit <= I4_MAX_PROVENANCE_PAGE_SIZE:
        raise ValueError("I.4 provenance page limit is invalid")
    offset = 0
    cursor_profile_id: UUID | None = None
    cursor_policy_id: UUID | None = None
    if cursor is not None:
        as_of, offset, cursor_profile_id, cursor_policy_id = _decode_cursor(cursor)
        if evaluation_as_of is not None and _aware(evaluation_as_of) != as_of:
            raise ValueError("I.4 provenance cursor conflicts with evaluation_as_of")
    else:
        as_of = _as_of(evaluation_as_of)

    components = _evaluate_components(
        session,
        tenant_key=tenant_key,
        position_key=position_key,
        capability_key=capability_key,
        context_scope=context_scope,
        evaluation_as_of=as_of,
    )
    if components is None:
        return None
    snapshot = components.snapshot
    if cursor_profile_id is not None and (
        cursor_profile_id != snapshot.profile_id or cursor_policy_id != snapshot.evaluation_policy_id
    ):
        raise ValueError("I.4 provenance cursor no longer matches current policy/profile")
    if offset > len(components.provenance):
        raise ValueError("I.4 provenance cursor offset is invalid")
    end = min(offset + page_limit, len(components.provenance))
    items = components.provenance[offset:end]
    next_cursor = (
        _encode_cursor(
            evaluation_as_of=snapshot.evaluation_as_of,
            offset=end,
            profile_id=snapshot.profile_id,
            evaluation_policy_id=snapshot.evaluation_policy_id,
        )
        if end < len(components.provenance)
        else None
    )
    return CapabilityAutonomyEvidenceEvaluationProvenancePage(
        profile_id=snapshot.profile_id,
        evaluation_policy_id=snapshot.evaluation_policy_id,
        evaluation_as_of=snapshot.evaluation_as_of,
        items=items,
        next_cursor=next_cursor,
        page_limit=page_limit,
    )


__all__ = [
    "I4_MAX_CANDIDATE_OBSERVATIONS",
    "I4_MAX_PROVENANCE_PAGE_SIZE",
    "AutonomyEvidenceEvaluationBoundExceeded",
    "AutonomyEvidenceEvaluationIntegrityError",
    "AutonomyEvidenceEvaluationUnsupported",
    "capability_autonomy_evidence_evaluation_provenance_page",
    "capability_autonomy_evidence_evaluation_snapshot",
]
