from __future__ import annotations

import hashlib
import json
from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    MobilityPathway,
    MobilityPathwayVersion,
    PathwayComparisonAssessment,
    PathwayRegulatoryImpact,
    Profile,
    ReassessmentAcceptance,
    now_utc,
)
from app.schemas import (
    PathwayComparisonRead,
    ReassessmentAcceptanceCreate,
    ReassessmentAcceptanceRead,
    ReassessmentCandidateRead,
    ReassessmentRegulatoryChangeRead,
)
from app.services.audit_log import record_audit
from app.services.mobility_profiles import current_mobility_profile
from app.services.pathway_catalogue import generate_pathway_comparison, pathway_comparison_read


def _dump(value: Any) -> str:
    return json.dumps(value, default=str, sort_keys=True)


def _load(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def _latest_assessment(session: Session, lead_id: UUID) -> PathwayComparisonAssessment | None:
    return session.exec(
        select(PathwayComparisonAssessment)
        .where(PathwayComparisonAssessment.lead_id == lead_id)
        .order_by(PathwayComparisonAssessment.created_at.desc())
    ).first()


def _baseline_version_ids(assessment: PathwayComparisonAssessment) -> list[UUID]:
    comparison = _load(assessment.comparison_json, {})
    raw_items = [comparison.get("primary"), *comparison.get("alternatives", [])]
    version_ids: list[UUID] = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        version_id = item.get("pathway", {}).get("current_version", {}).get("id")
        if not version_id:
            continue
        parsed = UUID(str(version_id))
        if parsed not in version_ids:
            version_ids.append(parsed)
    if not version_ids and assessment.primary_pathway_version_id:
        version_ids.append(assessment.primary_pathway_version_id)
    return version_ids


def _eligible_impact(session: Session, impact: PathwayRegulatoryImpact) -> ReassessmentRegulatoryChangeRead | None:
    if (
        impact.status != "resolved"
        or impact.replacement_pathway_version_id is None
        or not impact.reviewed_by
        or not impact.reviewed_at
        or not impact.review_notes
    ):
        return None
    affected = session.get(MobilityPathwayVersion, impact.pathway_version_id)
    replacement = session.get(MobilityPathwayVersion, impact.replacement_pathway_version_id)
    pathway = session.get(MobilityPathway, impact.pathway_id)
    if affected is None or replacement is None or pathway is None:
        return None
    if replacement.pathway_id != pathway.id or replacement.version_number <= affected.version_number:
        return None
    if replacement.lifecycle_status not in {"published", "superseded"}:
        return None
    if not replacement.approved_by or not replacement.published_at:
        return None
    return ReassessmentRegulatoryChangeRead(
        impact_id=impact.id,
        pathway_id=pathway.id,
        pathway_name=pathway.name,
        affected_pathway_version_id=affected.id,
        affected_pathway_version_number=affected.version_number,
        replacement_pathway_version_id=replacement.id,
        replacement_pathway_version_number=replacement.version_number,
        verified_rule_id=impact.verified_rule_id,
        materiality=impact.materiality,
        reviewed_by=impact.reviewed_by,
        reviewed_at=impact.reviewed_at,
        review_notes=impact.review_notes,
    )


def get_reassessment_candidate(session: Session, lead_id: UUID, *, baseline_assessment_id: UUID | None = None) -> ReassessmentCandidateRead:
    baseline = session.get(PathwayComparisonAssessment, baseline_assessment_id) if baseline_assessment_id else _latest_assessment(session, lead_id)
    if baseline is None or baseline.lead_id != lead_id:
        raise ValueError("No pathway comparison found for this lead")
    current_profile = current_mobility_profile(session, lead_id)
    profile_update = bool(current_profile and (current_profile.id != baseline.profile_id or current_profile.profile_version != baseline.profile_version))
    version_ids = _baseline_version_ids(baseline)
    regulatory_changes: list[ReassessmentRegulatoryChangeRead] = []
    if version_ids:
        impacts = session.exec(
            select(PathwayRegulatoryImpact)
            .where(PathwayRegulatoryImpact.pathway_version_id.in_(version_ids))
            .order_by(PathwayRegulatoryImpact.reviewed_at.desc())
        ).all()
        for impact in impacts:
            read = _eligible_impact(session, impact)
            if read is not None:
                regulatory_changes.append(read)
    requires = profile_update or bool(regulatory_changes)
    parts: list[str] = []
    if profile_update:
        parts.append(f"profile v{baseline.profile_version or 'none'} → v{current_profile.profile_version}")
    if regulatory_changes:
        parts.append(f"{len(regulatory_changes)} reviewed regulatory replacement(s)")
    summary = (
        "Explicit user acceptance is required before reassessment applies " + " and ".join(parts) + "."
        if parts
        else "The latest assessment remains aligned with its accepted profile and regulatory versions."
    )
    return ReassessmentCandidateRead(
        lead_id=lead_id,
        baseline_assessment_id=baseline.id,
        baseline_profile_id=baseline.profile_id,
        baseline_profile_version=baseline.profile_version,
        current_profile_id=current_profile.id if current_profile else None,
        current_profile_version=current_profile.profile_version if current_profile else None,
        profile_update_available=profile_update,
        regulatory_changes=regulatory_changes,
        requires_acceptance=requires,
        pinned_assessment_unchanged=True,
        summary=summary,
    )


def ensure_direct_comparison_allowed(session: Session, lead_id: UUID) -> None:
    baseline = _latest_assessment(session, lead_id)
    if baseline is None:
        return
    candidate = get_reassessment_candidate(session, lead_id, baseline_assessment_id=baseline.id)
    if candidate.requires_acceptance:
        raise ValueError("Reassessment acceptance required: record the user's explicit acceptance before applying a newer profile or reviewed regulatory version")


def reassessment_acceptance_read(row: ReassessmentAcceptance) -> ReassessmentAcceptanceRead:
    return ReassessmentAcceptanceRead(
        id=row.id,
        lead_id=row.lead_id,
        baseline_assessment_id=row.baseline_assessment_id,
        accepted_profile_id=row.accepted_profile_id,
        accepted_profile_version=row.accepted_profile_version,
        regulatory_impact_ids=[UUID(str(value)) for value in _load(row.regulatory_impact_ids_json, [])],
        accepted_pathway_version_ids=[UUID(str(value)) for value in _load(row.accepted_pathway_version_ids_json, [])],
        explicit_user_acceptance=row.explicit_user_acceptance,
        user_attestation=row.user_attestation,
        notes=row.notes,
        status=row.status,
        recorded_by=row.recorded_by,
        accepted_at=row.accepted_at,
        consumed_at=row.consumed_at,
        generated_assessment_id=row.generated_assessment_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def create_reassessment_acceptance(session: Session, lead_id: UUID, payload: ReassessmentAcceptanceCreate, *, actor: str) -> ReassessmentAcceptance:
    if payload.explicit_user_acceptance is not True:
        raise ValueError("Explicit user acceptance must be affirmed")
    latest = _latest_assessment(session, lead_id)
    if latest is None or latest.id != payload.baseline_assessment_id:
        raise ValueError("Acceptance must reference the latest immutable pathway comparison")
    current_profile = current_mobility_profile(session, lead_id)
    if current_profile is None or current_profile.consent_status != "granted":
        raise ValueError("Current profile consent must be granted before recording reassessment acceptance")
    candidate = get_reassessment_candidate(session, lead_id, baseline_assessment_id=payload.baseline_assessment_id)
    accepted_profile: Profile | None = None
    if payload.accept_profile_version:
        if not candidate.profile_update_available:
            raise ValueError("No newer profile version is available for acceptance")
        accepted_profile = current_profile
    eligible = {item.impact_id: item for item in candidate.regulatory_changes}
    selected_ids = list(dict.fromkeys(payload.regulatory_impact_ids))
    if any(impact_id not in eligible for impact_id in selected_ids):
        raise ValueError("Only reviewed regulatory replacements affecting the pinned assessment can be accepted")
    if accepted_profile is None and not selected_ids:
        raise ValueError("Select a newer profile or at least one reviewed regulatory replacement")
    replacement_ids = [eligible[impact_id].replacement_pathway_version_id for impact_id in selected_ids]
    key_payload = {
        "lead_id": str(lead_id),
        "baseline_assessment_id": str(latest.id),
        "profile_id": str(accepted_profile.id) if accepted_profile else None,
        "profile_version": accepted_profile.profile_version if accepted_profile else None,
        "regulatory_impact_ids": sorted(str(value) for value in selected_ids),
        "replacement_pathway_version_ids": sorted(str(value) for value in replacement_ids),
    }
    acceptance_key = hashlib.sha256(_dump(key_payload).encode("utf-8")).hexdigest()
    existing = session.exec(select(ReassessmentAcceptance).where(ReassessmentAcceptance.acceptance_key == acceptance_key)).first()
    if existing is not None:
        return existing
    now = now_utc()
    row = ReassessmentAcceptance(
        acceptance_key=acceptance_key,
        lead_id=lead_id,
        baseline_assessment_id=latest.id,
        accepted_profile_id=accepted_profile.id if accepted_profile else None,
        accepted_profile_version=accepted_profile.profile_version if accepted_profile else None,
        regulatory_impact_ids_json=_dump([str(value) for value in selected_ids]),
        accepted_pathway_version_ids_json=_dump([str(value) for value in replacement_ids]),
        explicit_user_acceptance=True,
        user_attestation=payload.user_attestation.strip(),
        notes=payload.notes.strip(),
        status="accepted",
        recorded_by=actor,
        accepted_at=now,
        created_at=now,
        updated_at=now,
    )
    session.add(row)
    session.flush()
    record_audit(
        session,
        action="reassessment_acceptance_recorded",
        entity_type="reassessment_acceptance",
        entity_id=row.id,
        after_state={**key_payload, "explicit_user_acceptance": True, "pinned_assessment_unchanged": True},
        reason=payload.notes,
        actor=actor,
        source="reassessment_acceptance_v10_12",
    )
    session.commit()
    session.refresh(row)
    return row


def list_reassessment_acceptances(session: Session, lead_id: UUID, *, limit: int = 100) -> list[ReassessmentAcceptanceRead]:
    rows = session.exec(
        select(ReassessmentAcceptance)
        .where(ReassessmentAcceptance.lead_id == lead_id)
        .order_by(ReassessmentAcceptance.accepted_at.desc())
        .limit(max(1, min(limit, 200)))
    ).all()
    return [reassessment_acceptance_read(row) for row in rows]


def execute_reassessment_acceptance(session: Session, acceptance_id: UUID, *, actor: str, limit: int = 5) -> PathwayComparisonRead:
    row = session.get(ReassessmentAcceptance, acceptance_id)
    if row is None:
        raise ValueError("Reassessment acceptance not found")
    if row.generated_assessment_id:
        generated = session.get(PathwayComparisonAssessment, row.generated_assessment_id)
        if generated is None:
            raise ValueError("Accepted reassessment provenance is incomplete")
        return pathway_comparison_read(generated)
    if row.status != "accepted":
        raise ValueError("Only an unconsumed acceptance can trigger reassessment")
    latest = _latest_assessment(session, row.lead_id)
    if latest is None or latest.id != row.baseline_assessment_id:
        raise ValueError("A newer comparison already exists; record a new explicit acceptance")
    current_profile = current_mobility_profile(session, row.lead_id)
    if current_profile is None or current_profile.consent_status != "granted":
        raise ValueError("Current profile consent must remain granted for reassessment")
    if row.accepted_profile_id:
        if current_profile.id != row.accepted_profile_id or current_profile.profile_version != row.accepted_profile_version:
            raise ValueError("The accepted profile is no longer current; record a new explicit acceptance")
        profile = current_profile
    else:
        profile = session.get(Profile, latest.profile_id) if latest.profile_id else None
    version_ids = _baseline_version_ids(latest)
    selected_impact_ids = [UUID(str(value)) for value in _load(row.regulatory_impact_ids_json, [])]
    replacement_map: dict[UUID, UUID] = {}
    for impact_id in selected_impact_ids:
        impact = session.get(PathwayRegulatoryImpact, impact_id)
        read = _eligible_impact(session, impact) if impact else None
        if read is None:
            raise ValueError("An accepted regulatory replacement is no longer valid for reassessment")
        existing = replacement_map.get(read.affected_pathway_version_id)
        if existing and existing != read.replacement_pathway_version_id:
            raise ValueError("Accepted regulatory replacements conflict for the same pathway version")
        replacement_map[read.affected_pathway_version_id] = read.replacement_pathway_version_id
    final_version_ids = [replacement_map.get(version_id, version_id) for version_id in version_ids]
    before = {"status": row.status, "generated_assessment_id": None}
    now = now_utc()
    row.status = "consumed"
    row.consumed_at = now
    row.updated_at = now
    session.add(row)
    comparison = generate_pathway_comparison(
        session,
        row.lead_id,
        actor=actor,
        limit=limit,
        profile_override=profile,
        pathway_version_ids=final_version_ids,
        reassessment_acceptance_id=row.id,
    )
    row.generated_assessment_id = comparison.assessment_id
    row.updated_at = now_utc()
    session.add(row)
    record_audit(
        session,
        action="reassessment_acceptance_consumed",
        entity_type="reassessment_acceptance",
        entity_id=row.id,
        before_state=before,
        after_state={
            "status": row.status,
            "generated_assessment_id": str(row.generated_assessment_id),
            "accepted_profile_version": row.accepted_profile_version,
            "accepted_pathway_version_ids": [str(value) for value in final_version_ids],
            "baseline_assessment_unchanged": True,
        },
        reason="Executed reassessment only after recorded explicit user acceptance",
        actor=actor,
        source="reassessment_acceptance_v10_12",
    )
    session.commit()
    session.refresh(row)
    return comparison
