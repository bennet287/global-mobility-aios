from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from app.core.organization_constitution import OrganizationActivityClass as ConstitutionalActivityClass
from app.models.domain import (
    EligibilityAssessment,
    MobilityPathway,
    MobilityPathwayVersion,
    OrganizationActivity,
)
from app.models.eligibility_revision import EligibilityAssessmentRevision
from app.services.organization_command import canonical_fingerprint
from app.services.organization_eligibility_revision_precondition import eligibility_aggregate_key
from app.services.organization_transparency import TransparencyDataError, transparency_activity_record


INDEPENDENT_ELIGIBILITY_ACTIVITY_TYPE = "verification.eligibility.independent.v1"
ELIGIBILITY_VERIFICATION_FLOOR_ACTIVITY_TYPE = "governance.eligibility.verification_floor.v1"
ELIGIBILITY_CANONICAL_GOVERNANCE_ACTIVITY_TYPE = "governance.eligibility.transition.auto_execute"
ELIGIBILITY_CANONICAL_GOVERNANCE_RECORD_KIND = "eligibility_canonical_effect_authorization"
ELIGIBILITY_CANONICAL_GOVERNANCE_OUTCOME = "AUTO_EXECUTE"
ELIGIBILITY_CANONICAL_EFFECT_ACTIVITY_TYPE = "organization.eligibility.assessment_committed.v1"
ELIGIBILITY_CANONICAL_EFFECT_SCHEMA_VERSION = "eligibility-canonical-effect.v1"


class CanonicalEligibilityLineageError(RuntimeError):
    """Durable canonical eligibility lineage is incomplete or internally inconsistent."""

    def __init__(
        self,
        message: str,
        *,
        code: str,
        integrity_scope: str = "durable",
        source_activity_id: UUID | None = None,
        details: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.integrity_scope = integrity_scope
        self.source_activity_id = source_activity_id
        self.details = dict(details or {})
        self.fingerprint = canonical_fingerprint(
            {
                "code": code,
                "integrity_scope": integrity_scope,
                "source_activity_id": source_activity_id,
                "details": self.details,
            }
        )


@dataclass(frozen=True)
class CanonicalEligibilityLineage:
    revision: EligibilityAssessmentRevision
    assessment: EligibilityAssessment
    pathway_version: MobilityPathwayVersion
    pathway: MobilityPathway
    verification_activity: OrganizationActivity
    verification_floor_activity: OrganizationActivity
    governance_activity: OrganizationActivity
    semantic_activity: OrganizationActivity
    predecessor_revision: EligibilityAssessmentRevision | None

    @property
    def proposal_activity_id(self) -> UUID:
        proposal_activity_id = self.verification_activity.causation_activity_id
        if proposal_activity_id is None:
            raise CanonicalEligibilityLineageError(
                "validated eligibility verification unexpectedly lacks its proposal cause",
                code="validated_lineage_missing_proposal_cause",
                source_activity_id=self.governance_activity.id,
            )
        return proposal_activity_id


def _fail(
    message: str,
    *,
    code: str,
    integrity_scope: str = "durable",
    source_activity_id: UUID | None = None,
    **details: object,
) -> None:
    raise CanonicalEligibilityLineageError(
        message,
        code=code,
        integrity_scope=integrity_scope,
        source_activity_id=source_activity_id,
        details=details,
    )


def _record(activity: OrganizationActivity, *, label: str, source_activity_id: UUID | None):
    try:
        return transparency_activity_record(activity)
    except TransparencyDataError as exc:
        raise CanonicalEligibilityLineageError(
            f"canonical eligibility {label} Activity is malformed",
            code=f"malformed_{label}_activity",
            source_activity_id=source_activity_id or activity.id,
            details={"activity_id": str(activity.id)},
        ) from exc


def _require_activity_identity(
    activity: OrganizationActivity,
    *,
    tenant_key: str,
    revision: EligibilityAssessmentRevision,
    label: str,
    expected_activity_type: str,
) -> None:
    if activity.tenant_key != tenant_key:
        _fail(
            f"canonical eligibility {label} Activity crosses tenant boundaries",
            code=f"{label}_tenant_mismatch",
            source_activity_id=revision.governance_activity_id,
            activity_id=str(activity.id),
            activity_tenant_key=activity.tenant_key,
            expected_tenant_key=tenant_key,
        )
    if activity.lead_id != revision.lead_id or activity.profile_id != revision.profile_id:
        _fail(
            f"canonical eligibility {label} Activity names a different subject",
            code=f"{label}_subject_mismatch",
            source_activity_id=revision.governance_activity_id,
            activity_id=str(activity.id),
            activity_lead_id=str(activity.lead_id),
            revision_lead_id=str(revision.lead_id),
            activity_profile_id=str(activity.profile_id),
            revision_profile_id=str(revision.profile_id),
        )
    if activity.activity_type != expected_activity_type:
        _fail(
            f"canonical eligibility {label} Activity has the wrong type",
            code=f"{label}_activity_type_mismatch",
            source_activity_id=revision.governance_activity_id,
            activity_id=str(activity.id),
            actual_activity_type=activity.activity_type,
            expected_activity_type=expected_activity_type,
        )


def _require_payload_fields(
    *,
    label: str,
    payload: dict[str, Any],
    expected: dict[str, object],
    revision: EligibilityAssessmentRevision,
) -> None:
    mismatches = {
        key: {"actual": payload.get(key), "expected": value}
        for key, value in expected.items()
        if payload.get(key) != value
    }
    if mismatches:
        _fail(
            f"canonical eligibility {label} payload conflicts with its revision",
            code=f"{label}_payload_mismatch",
            source_activity_id=revision.governance_activity_id,
            mismatches=mismatches,
        )


def _assessment_payload(
    assessment: EligibilityAssessment,
    *,
    governance_activity_id: UUID,
) -> dict[str, Any]:
    try:
        payload = json.loads(assessment.assessment_json or "{}")
    except json.JSONDecodeError as exc:
        raise CanonicalEligibilityLineageError(
            "canonical eligibility assessment payload is malformed",
            code="malformed_assessment_payload",
            source_activity_id=governance_activity_id,
            details={"assessment_id": str(assessment.id)},
        ) from exc
    if not isinstance(payload, dict):
        _fail(
            "canonical eligibility assessment payload must be an object",
            code="assessment_payload_not_object",
            source_activity_id=governance_activity_id,
            assessment_id=str(assessment.id),
        )
    return payload


def validate_canonical_eligibility_lineage(
    session: Session,
    *,
    tenant_key: str,
    revision: EligibilityAssessmentRevision,
) -> CanonicalEligibilityLineage:
    """Validate one committed eligibility revision against the single canonical contract.

    G.3 replay, G.4 replay and H.1 preflight all depend on this read-only,
    domain-specific contract so durable identity cannot drift between callers.
    """

    tenant = str(tenant_key or "").strip()
    if not tenant:
        _fail("tenant_key is required for canonical eligibility lineage", code="missing_tenant")
    if revision.tenant_key != tenant:
        _fail(
            "canonical eligibility revision belongs to a different tenant",
            code="revision_tenant_mismatch",
            integrity_scope="aggregate",
            source_activity_id=revision.governance_activity_id,
            revision_id=str(revision.id),
            revision_tenant_key=revision.tenant_key,
            expected_tenant_key=tenant,
        )
    if revision.version < 1 or revision.lifecycle_status not in {"active", "superseded"}:
        _fail(
            "canonical eligibility revision lifecycle identity is invalid",
            code="revision_lifecycle_invalid",
            integrity_scope="aggregate",
            source_activity_id=revision.governance_activity_id,
            revision_id=str(revision.id),
            version=revision.version,
            lifecycle_status=revision.lifecycle_status,
        )

    pathway_version = session.get(MobilityPathwayVersion, revision.pathway_version_id)
    if pathway_version is None:
        _fail(
            "canonical eligibility pathway-version lineage is missing",
            code="missing_pathway_version",
            source_activity_id=revision.governance_activity_id,
            pathway_version_id=str(revision.pathway_version_id),
        )
    pathway = session.get(MobilityPathway, pathway_version.pathway_id)
    if pathway is None:
        _fail(
            "canonical eligibility pathway lineage is missing",
            code="missing_pathway",
            source_activity_id=revision.governance_activity_id,
            pathway_id=str(pathway_version.pathway_id),
        )

    expected_aggregate = eligibility_aggregate_key(
        tenant_key=tenant,
        lead_id=revision.lead_id,
        pathway_id=pathway.id,
    )
    if revision.aggregate_key != expected_aggregate:
        _fail(
            "canonical eligibility revision identity does not match its aggregate",
            code="revision_aggregate_identity_mismatch",
            integrity_scope="aggregate",
            source_activity_id=revision.governance_activity_id,
            revision_id=str(revision.id),
            aggregate_key=revision.aggregate_key,
            expected_aggregate_key=expected_aggregate,
        )

    predecessor: EligibilityAssessmentRevision | None = None
    if revision.version == 1:
        if revision.supersedes_revision_id is not None:
            _fail(
                "first canonical eligibility revision cannot supersede another revision",
                code="revision_v1_has_predecessor",
                integrity_scope="aggregate",
                source_activity_id=revision.governance_activity_id,
                revision_id=str(revision.id),
                supersedes_revision_id=str(revision.supersedes_revision_id),
            )
    else:
        if revision.supersedes_revision_id is None:
            _fail(
                "canonical eligibility reassessment lacks supersession lineage",
                code="revision_missing_predecessor",
                integrity_scope="aggregate",
                source_activity_id=revision.governance_activity_id,
                revision_id=str(revision.id),
                version=revision.version,
            )
        predecessor = session.get(EligibilityAssessmentRevision, revision.supersedes_revision_id)
        if predecessor is None:
            _fail(
                "canonical eligibility predecessor revision is missing",
                code="missing_predecessor_revision",
                integrity_scope="aggregate",
                source_activity_id=revision.governance_activity_id,
                revision_id=str(revision.id),
                supersedes_revision_id=str(revision.supersedes_revision_id),
            )
        if (
            predecessor.tenant_key != tenant
            or predecessor.aggregate_key != revision.aggregate_key
            or predecessor.version != revision.version - 1
            or predecessor.lifecycle_status != "superseded"
        ):
            _fail(
                "canonical eligibility supersession lineage is inconsistent",
                code="predecessor_revision_mismatch",
                integrity_scope="aggregate",
                source_activity_id=revision.governance_activity_id,
                revision_id=str(revision.id),
                predecessor_revision_id=str(predecessor.id),
                predecessor_tenant_key=predecessor.tenant_key,
                predecessor_aggregate_key=predecessor.aggregate_key,
                predecessor_version=predecessor.version,
                predecessor_lifecycle_status=predecessor.lifecycle_status,
            )

    assessment = session.get(EligibilityAssessment, revision.assessment_id)
    verification = session.get(OrganizationActivity, revision.verification_activity_id)
    floor = session.get(OrganizationActivity, revision.verification_floor_activity_id)
    governance = session.get(OrganizationActivity, revision.governance_activity_id)
    semantic = (
        session.get(OrganizationActivity, revision.semantic_activity_id)
        if revision.semantic_activity_id is not None
        else None
    )
    missing = tuple(
        label
        for label, row in {
            "assessment": assessment,
            "verification": verification,
            "verification_floor": floor,
            "governance": governance,
            "semantic": semantic,
        }.items()
        if row is None
    )
    if missing:
        _fail(
            "canonical eligibility durable lineage is torn",
            code="missing_durable_lineage",
            source_activity_id=revision.governance_activity_id,
            revision_id=str(revision.id),
            missing=missing,
        )

    assert assessment is not None
    assert verification is not None
    assert floor is not None
    assert governance is not None
    assert semantic is not None

    if (
        assessment.lead_id != revision.lead_id
        or assessment.profile_id != revision.profile_id
        or assessment.profile_version != revision.profile_version
        or assessment.target_country != pathway.country
        or assessment.domain != pathway.domain
    ):
        _fail(
            "canonical eligibility assessment identity conflicts with its revision",
            code="assessment_revision_identity_mismatch",
            source_activity_id=governance.id,
            assessment_id=str(assessment.id),
            assessment_lead_id=str(assessment.lead_id),
            revision_lead_id=str(revision.lead_id),
            assessment_profile_id=str(assessment.profile_id),
            revision_profile_id=str(revision.profile_id),
            assessment_profile_version=assessment.profile_version,
            revision_profile_version=revision.profile_version,
            assessment_country=assessment.target_country,
            pathway_country=pathway.country,
            assessment_domain=assessment.domain,
            pathway_domain=pathway.domain,
        )

    assessment_payload = _assessment_payload(
        assessment,
        governance_activity_id=governance.id,
    )
    expected_previous_version = None if revision.version == 1 else revision.version - 1
    supersedes_id = (
        str(revision.supersedes_revision_id)
        if revision.supersedes_revision_id is not None
        else None
    )
    _require_payload_fields(
        label="assessment",
        payload=assessment_payload,
        expected={
            "schema_version": ELIGIBILITY_CANONICAL_EFFECT_SCHEMA_VERSION,
            "canonical_revision_version": revision.version,
            "supersedes_revision_id": supersedes_id,
            "pathway_version_id": str(revision.pathway_version_id),
            "intent_fingerprint": revision.intent_fingerprint,
            "readiness_fingerprint": revision.readiness_fingerprint,
            "verification_fingerprint": revision.verification_fingerprint,
            "verification_floor_fingerprint": revision.verification_floor_fingerprint,
            "governed": True,
        },
        revision=revision,
    )
    if assessment_payload.get("proposed_state") != assessment.status:
        _fail(
            "canonical eligibility assessment state conflicts with its durable payload",
            code="assessment_state_mismatch",
            source_activity_id=governance.id,
            assessment_status=assessment.status,
            payload_state=assessment_payload.get("proposed_state"),
        )

    expected_activity_types = {
        "verification": (verification, INDEPENDENT_ELIGIBILITY_ACTIVITY_TYPE),
        "verification_floor": (floor, ELIGIBILITY_VERIFICATION_FLOOR_ACTIVITY_TYPE),
        "governance": (governance, ELIGIBILITY_CANONICAL_GOVERNANCE_ACTIVITY_TYPE),
        "semantic": (semantic, ELIGIBILITY_CANONICAL_EFFECT_ACTIVITY_TYPE),
    }
    for label, (activity, expected_type) in expected_activity_types.items():
        _require_activity_identity(
            activity,
            tenant_key=tenant,
            revision=revision,
            label=label,
            expected_activity_type=expected_type,
        )

    for label, activity in {
        "verification": verification,
        "verification_floor": floor,
        "governance": governance,
    }.items():
        if (
            activity.source_object_type != "lead_eligibility"
            or activity.source_object_id != str(revision.lead_id)
            or activity.source_object_version != str(revision.profile_version)
        ):
            _fail(
                f"canonical eligibility {label} source identity conflicts with its revision",
                code=f"{label}_source_identity_mismatch",
                source_activity_id=governance.id,
                source_object_type=activity.source_object_type,
                source_object_id=activity.source_object_id,
                source_object_version=activity.source_object_version,
                expected_source_object_type="lead_eligibility",
                expected_source_object_id=str(revision.lead_id),
                expected_source_object_version=str(revision.profile_version),
            )
    if (
        semantic.source_object_type != "eligibility_assessment"
        or semantic.source_object_id != str(assessment.id)
        or semantic.source_object_version != str(revision.version)
    ):
        _fail(
            "canonical eligibility semantic source identity conflicts with its revision",
            code="semantic_source_identity_mismatch",
            source_activity_id=governance.id,
            source_object_type=semantic.source_object_type,
            source_object_id=semantic.source_object_id,
            source_object_version=semantic.source_object_version,
            assessment_id=str(assessment.id),
            revision_version=revision.version,
        )

    verification_record = _record(
        verification,
        label="verification",
        source_activity_id=governance.id,
    )
    floor_record = _record(
        floor,
        label="verification_floor",
        source_activity_id=governance.id,
    )
    governance_record = _record(
        governance,
        label="governance",
        source_activity_id=governance.id,
    )
    semantic_record = _record(
        semantic,
        label="semantic",
        source_activity_id=governance.id,
    )

    for label, record in {
        "verification": verification_record,
        "verification_floor": floor_record,
        "governance": governance_record,
        "semantic": semantic_record,
    }.items():
        if record.constitutional_activity_class is not ConstitutionalActivityClass.MATERIAL:
            _fail(
                f"canonical eligibility {label} Activity is not MATERIAL lineage",
                code=f"{label}_constitutional_class_mismatch",
                source_activity_id=governance.id,
                constitutional_activity_class=(
                    record.constitutional_activity_class.value
                    if record.constitutional_activity_class is not None
                    else None
                ),
            )

    _require_payload_fields(
        label="verification",
        payload=dict(verification_record.payload),
        expected={
            "verification_fingerprint": revision.verification_fingerprint,
            "readiness_fingerprint": revision.readiness_fingerprint,
            "disposition": "agrees",
        },
        revision=revision,
    )
    _require_payload_fields(
        label="verification_floor",
        payload=dict(floor_record.payload),
        expected={
            "verification_floor_fingerprint": revision.verification_floor_fingerprint,
            "verification_fingerprint": revision.verification_fingerprint,
            "readiness_fingerprint": revision.readiness_fingerprint,
            "eligibility_aggregate_key": revision.aggregate_key,
            "next_eligibility_revision_version": revision.version,
            "expected_eligibility_revision_version": expected_previous_version,
            "expected_eligibility_revision_id": supersedes_id,
            "original_e2_action_fingerprint": revision.original_action_fingerprint,
        },
        revision=revision,
    )
    _require_payload_fields(
        label="governance",
        payload=dict(governance_record.payload),
        expected={
            "governance_record_kind": ELIGIBILITY_CANONICAL_GOVERNANCE_RECORD_KIND,
            "outcome": ELIGIBILITY_CANONICAL_GOVERNANCE_OUTCOME,
            "action_fingerprint": revision.original_action_fingerprint,
            "verification_floor_fingerprint": revision.verification_floor_fingerprint,
            "effect_fingerprint": revision.effect_fingerprint,
            "canonical_revision_version": revision.version,
            "expected_eligibility_revision_version": expected_previous_version,
            "supersedes_revision_id": supersedes_id,
        },
        revision=revision,
    )
    _require_payload_fields(
        label="semantic",
        payload=dict(semantic_record.payload),
        expected={
            "effect_fingerprint": revision.effect_fingerprint,
            "assessment_id": str(assessment.id),
            "revision_id": str(revision.id),
            "aggregate_key": revision.aggregate_key,
            "revision_version": revision.version,
            "supersedes_revision_id": supersedes_id,
            "status": assessment.status,
            "profile_version": revision.profile_version,
            "pathway_version_id": str(revision.pathway_version_id),
            "original_action_fingerprint": revision.original_action_fingerprint,
            "intent_fingerprint": revision.intent_fingerprint,
            "readiness_fingerprint": revision.readiness_fingerprint,
            "verification_fingerprint": revision.verification_fingerprint,
            "verification_floor_fingerprint": revision.verification_floor_fingerprint,
        },
        revision=revision,
    )

    if verification.causation_activity_id is None:
        _fail(
            "canonical eligibility verification has no E.2 proposal cause",
            code="verification_missing_proposal_cause",
            source_activity_id=governance.id,
            verification_activity_id=str(verification.id),
        )
    if floor.causation_activity_id != verification.id:
        _fail(
            "canonical eligibility verification-floor causation is inconsistent",
            code="verification_floor_causation_mismatch",
            source_activity_id=governance.id,
            verification_activity_id=str(verification.id),
            verification_floor_cause=str(floor.causation_activity_id),
        )
    if governance.causation_activity_id != floor.id:
        _fail(
            "canonical eligibility governance causation is inconsistent",
            code="governance_causation_mismatch",
            source_activity_id=governance.id,
            verification_floor_activity_id=str(floor.id),
            governance_cause=str(governance.causation_activity_id),
        )
    if semantic.causation_activity_id != governance.id:
        _fail(
            "canonical eligibility semantic causation is inconsistent",
            code="semantic_causation_mismatch",
            source_activity_id=governance.id,
            governance_activity_id=str(governance.id),
            semantic_cause=str(semantic.causation_activity_id),
        )

    return CanonicalEligibilityLineage(
        revision=revision,
        assessment=assessment,
        pathway_version=pathway_version,
        pathway=pathway,
        verification_activity=verification,
        verification_floor_activity=floor,
        governance_activity=governance,
        semantic_activity=semantic,
        predecessor_revision=predecessor,
    )


def canonical_eligibility_lineage_for_governance(
    session: Session,
    *,
    tenant_key: str,
    governance_activity_id: UUID,
) -> CanonicalEligibilityLineage:
    revisions = tuple(
        session.exec(
            select(EligibilityAssessmentRevision).where(
                EligibilityAssessmentRevision.tenant_key == tenant_key,
                EligibilityAssessmentRevision.governance_activity_id == governance_activity_id,
            )
        ).all()
    )
    if len(revisions) != 1:
        _fail(
            "canonical eligibility governance does not resolve to exactly one revision",
            code="governance_revision_cardinality",
            integrity_scope="aggregate",
            source_activity_id=governance_activity_id,
            governance_activity_id=str(governance_activity_id),
            revision_count=len(revisions),
        )
    return validate_canonical_eligibility_lineage(
        session,
        tenant_key=tenant_key,
        revision=revisions[0],
    )


def validate_canonical_eligibility_aggregate_lineage(
    session: Session,
    *,
    tenant_key: str,
    aggregate_key: str,
) -> tuple[CanonicalEligibilityLineage, ...]:
    """Validate the complete ordered revision chain for one canonical eligibility aggregate."""

    revisions = tuple(
        session.exec(
            select(EligibilityAssessmentRevision)
            .where(
                EligibilityAssessmentRevision.tenant_key == tenant_key,
                EligibilityAssessmentRevision.aggregate_key == aggregate_key,
            )
            .order_by(EligibilityAssessmentRevision.version)
        ).all()
    )
    if not revisions:
        return ()

    expected_versions = tuple(range(1, len(revisions) + 1))
    actual_versions = tuple(row.version for row in revisions)
    if actual_versions != expected_versions:
        _fail(
            "canonical eligibility revision sequence is inconsistent",
            code="aggregate_revision_sequence_mismatch",
            integrity_scope="aggregate",
            source_activity_id=revisions[-1].governance_activity_id,
            aggregate_key=aggregate_key,
            actual_versions=actual_versions,
            expected_versions=expected_versions,
        )

    active = tuple(row for row in revisions if row.lifecycle_status == "active")
    if len(active) != 1 or active[0].id != revisions[-1].id:
        _fail(
            "canonical eligibility revision lifecycle is inconsistent",
            code="aggregate_active_revision_mismatch",
            integrity_scope="aggregate",
            source_activity_id=revisions[-1].governance_activity_id,
            aggregate_key=aggregate_key,
            active_revision_ids=tuple(str(row.id) for row in active),
            latest_revision_id=str(revisions[-1].id),
        )

    validated: list[CanonicalEligibilityLineage] = []
    for index, revision in enumerate(revisions):
        expected_status = "active" if index == len(revisions) - 1 else "superseded"
        expected_supersedes = None if index == 0 else revisions[index - 1].id
        if revision.lifecycle_status != expected_status or revision.supersedes_revision_id != expected_supersedes:
            _fail(
                "canonical eligibility supersession chain is inconsistent",
                code="aggregate_supersession_chain_mismatch",
                integrity_scope="aggregate",
                source_activity_id=revision.governance_activity_id,
                aggregate_key=aggregate_key,
                revision_id=str(revision.id),
                lifecycle_status=revision.lifecycle_status,
                expected_lifecycle_status=expected_status,
                supersedes_revision_id=(
                    str(revision.supersedes_revision_id)
                    if revision.supersedes_revision_id is not None
                    else None
                ),
                expected_supersedes_revision_id=(
                    str(expected_supersedes) if expected_supersedes is not None else None
                ),
            )
        if revision.aggregate_key != aggregate_key:
            _fail(
                "canonical eligibility revision belongs to a different aggregate",
                code="aggregate_revision_key_mismatch",
                integrity_scope="aggregate",
                source_activity_id=revision.governance_activity_id,
                aggregate_key=aggregate_key,
                revision_id=str(revision.id),
                revision_aggregate_key=revision.aggregate_key,
            )
        validated.append(
            validate_canonical_eligibility_lineage(
                session,
                tenant_key=tenant_key,
                revision=revision,
            )
        )
    return tuple(validated)
