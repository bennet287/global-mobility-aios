from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    Lead,
    MobilityPathway,
    MobilityPathwayVersion,
    MobilityTimeline,
    MobilityTimelineMilestone,
    PathwayComparisonAssessment,
    now_utc,
)
from app.schemas import MobilityTimelineMilestoneRead, MobilityTimelineRead
from app.services.audit_log import record_audit
from app.services.mobility_profiles import current_mobility_profile


def _dump(value: Any) -> str:
    return json.dumps(value, default=str, sort_keys=True)


def _load(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return fallback


def _milestones(session: Session, timeline_id: UUID) -> list[MobilityTimelineMilestone]:
    return list(session.exec(
        select(MobilityTimelineMilestone)
        .where(MobilityTimelineMilestone.timeline_id == timeline_id)
        .order_by(MobilityTimelineMilestone.stage_order)
    ).all())


def timeline_read(session: Session, timeline: MobilityTimeline) -> MobilityTimelineRead:
    milestones = _milestones(session, timeline.id)
    return MobilityTimelineRead(
        **timeline.model_dump(exclude={"schedule_json"}),
        schedule=_load(timeline.schedule_json, {}),
        milestones=[
            MobilityTimelineMilestoneRead(
                **row.model_dump(exclude={"dependencies_json", "required_evidence_json", "blockers_json"}),
                dependencies=_load(row.dependencies_json, []),
                required_evidence=_load(row.required_evidence_json, []),
                blockers=_load(row.blockers_json, []),
            )
            for row in milestones
        ],
    )


def _route_stage(domain: str) -> tuple[str, str, str, str]:
    return {
        "study": ("admission_or_enrolment", "Admission or enrolment", "Secure and verify the institution decision.", "education_specialist"),
        "work": ("employment_or_sponsorship", "Employment or sponsorship", "Secure and verify the employment or sponsor basis.", "recruitment_specialist"),
        "scholarship": ("scholarship_application", "Scholarship application", "Prepare and verify the scholarship application.", "education_specialist"),
        "family": ("relationship_sponsorship", "Relationship sponsorship", "Verify relationship and sponsorship evidence.", "mobility_consultant"),
        "settlement": ("settlement_prerequisites", "Settlement prerequisites", "Verify route-specific settlement prerequisites.", "mobility_consultant"),
        "digital_nomad": ("remote_work_evidence", "Remote-work evidence", "Verify remote employment, income, and contract evidence.", "mobility_consultant"),
    }.get(domain, ("purpose_and_financial_evidence", "Purpose and financial evidence", "Verify purpose, funds, and route-specific evidence.", "mobility_consultant"))


def _stage_blueprint(domain: str) -> list[tuple[str, str, str, str, bool]]:
    route_key, route_title, route_description, route_owner = _route_stage(domain)
    return [
        ("profile_readiness", "Profile readiness", "Confirm the immutable profile version is complete enough to plan from.", "mobility_operator", False),
        ("evidence_collection", "Evidence collection", "Collect and verify pathway and profile evidence gaps.", "document_specialist", False),
        ("eligibility_review", "Human eligibility review", "A qualified operator reviews the evidence-backed pathway recommendation.", "mobility_consultant", True),
        (route_key, route_title, route_description, route_owner, True),
        ("application_preparation", "Application preparation", "Prepare the application against the reviewed route and evidence.", "application_specialist", False),
        ("application_review", "Human application review", "Review the complete application before any submission action.", "application_specialist", True),
        ("submission_to_authority", "Submission to authority", "Record the separately approved submission to the competent authority.", "authorized_operator", True),
        ("authority_processing", "Authority processing", "Track the authority-owned processing window without predicting an outcome.", "case_manager", False),
        ("authority_decision", "Authority decision", "Record the verified external authority decision through the decision control.", "authorized_operator", True),
        ("relocation", "Relocation", "Coordinate travel, arrival, registration, and immediate compliance tasks.", "relocation_specialist", False),
        ("settlement_integration", "Settlement and integration", "Track post-arrival onboarding, renewals, and integration actions.", "case_manager", False),
    ]


def generate_timeline(
    session: Session,
    assessment_id: UUID,
    *,
    actor: str,
    target_date: datetime | None = None,
) -> MobilityTimelineRead:
    existing = session.exec(
        select(MobilityTimeline).where(MobilityTimeline.comparison_assessment_id == assessment_id)
    ).first()
    if existing:
        return timeline_read(session, existing)
    assessment = session.get(PathwayComparisonAssessment, assessment_id)
    if assessment is None:
        raise ValueError("Pathway comparison not found")
    if assessment.status not in {"ready_for_review", "needs_profile_review"}:
        raise ValueError("Timeline requires a comparison with a primary evidence-backed pathway")
    if not assessment.primary_pathway_id or not assessment.primary_pathway_version_id:
        raise ValueError("Comparison has no primary pathway version")
    lead = session.get(Lead, assessment.lead_id)
    pathway = session.get(MobilityPathway, assessment.primary_pathway_id)
    version = session.get(MobilityPathwayVersion, assessment.primary_pathway_version_id)
    profile = current_mobility_profile(session, assessment.lead_id)
    if lead is None or pathway is None or version is None:
        raise ValueError("Comparison provenance is incomplete")
    if profile is None or profile.consent_status != "granted":
        raise ValueError("Current profile consent must be granted before timeline generation")
    if profile.id != assessment.profile_id or profile.profile_version != assessment.profile_version:
        raise ValueError("Comparison is stale because the current profile version changed")

    created_at = now_utc()
    processing = _load(version.processing_time_json, {})
    processing_weeks = max(1, int(processing.get("maximum_weeks") or 12))
    offsets = [7, 14, 7, 21, 14, 7, 1, processing_weeks * 7, 1, 30, 90]
    due_at = created_at
    missing_evidence = _load(assessment.missing_evidence_json, [])
    required_documents = _load(version.required_documents_json, [])
    timeline = MobilityTimeline(
        lead_id=assessment.lead_id,
        profile_id=assessment.profile_id,
        profile_version=assessment.profile_version,
        comparison_assessment_id=assessment.id,
        primary_pathway_id=assessment.primary_pathway_id,
        primary_pathway_version_id=assessment.primary_pathway_version_id,
        title=f"{pathway.name} mobility timeline",
        target_date=target_date,
        schedule_json=_dump({
            "basis": "deterministic_dependency_schedule",
            "processing_window_weeks": processing_weeks,
            "target_date": target_date.isoformat() if target_date else None,
            "warning": "Dates are planning estimates; authority processing and decisions remain external.",
        }),
        generated_by=actor,
        created_at=created_at,
        updated_at=created_at,
    )
    session.add(timeline)
    session.flush()
    previous_key: str | None = None
    for index, (key, title, description, owner, human) in enumerate(_stage_blueprint(pathway.domain), start=1):
        due_at += timedelta(days=offsets[index - 1])
        evidence: list[str] = []
        if key == "evidence_collection":
            evidence = list(dict.fromkeys([*required_documents, *missing_evidence]))
        session.add(MobilityTimelineMilestone(
            timeline_id=timeline.id,
            stage_order=index,
            stage_key=key,
            title=title,
            description=description,
            dependencies_json=_dump([previous_key] if previous_key else []),
            required_evidence_json=_dump(evidence),
            owner_role=owner,
            due_at=due_at,
            requires_human_approval=human,
            created_at=created_at,
            updated_at=created_at,
        ))
        previous_key = key
    timeline.current_stage_key = "profile_readiness"
    record_audit(
        session,
        action="mobility_timeline_generated",
        entity_type="mobility_timeline",
        entity_id=timeline.id,
        after_state={
            "lead_id": str(timeline.lead_id),
            "comparison_assessment_id": str(assessment.id),
            "profile_version": timeline.profile_version,
            "pathway_version_id": str(timeline.primary_pathway_version_id),
            "milestone_count": 11,
        },
        reason="Generated dependency-controlled timeline from immutable pathway comparison",
        actor=actor,
        source="mobility_timeline_v8_3",
    )
    session.commit()
    session.refresh(timeline)
    return timeline_read(session, timeline)


def _ensure_current_consent(session: Session, timeline: MobilityTimeline, actor: str) -> None:
    profile = current_mobility_profile(session, timeline.lead_id)
    if profile and profile.consent_status == "granted":
        return
    before = timeline.status
    timeline.status = "restricted"
    timeline.updated_at = now_utc()
    record_audit(
        session,
        action="mobility_timeline_restricted",
        entity_type="mobility_timeline",
        entity_id=timeline.id,
        before_state={"status": before},
        after_state={"status": "restricted"},
        reason="Current profile consent is not granted",
        actor=actor,
        source="mobility_timeline_v8_3",
    )
    session.commit()
    raise ValueError("Current profile consent must be granted for timeline transitions")


def activate_timeline(session: Session, timeline_id: UUID, *, actor: str) -> MobilityTimelineRead:
    timeline = session.get(MobilityTimeline, timeline_id)
    if timeline is None:
        raise ValueError("Mobility timeline not found")
    _ensure_current_consent(session, timeline, actor)
    if timeline.status == "active":
        return timeline_read(session, timeline)
    if timeline.status != "draft":
        raise ValueError("Only a draft timeline can be activated")
    rows = _milestones(session, timeline.id)
    if not rows:
        raise ValueError("Timeline contains no milestones")
    now = now_utc()
    timeline.status = "active"
    timeline.activated_by = actor
    timeline.activated_at = now
    timeline.current_stage_key = rows[0].stage_key
    timeline.updated_at = now
    rows[0].status = "ready"
    rows[0].updated_at = now
    record_audit(
        session,
        action="mobility_timeline_activated",
        entity_type="mobility_timeline",
        entity_id=timeline.id,
        after_state={"status": "active", "current_stage_key": rows[0].stage_key},
        reason="Human operator activated timeline",
        actor=actor,
        source="mobility_timeline_v8_3",
    )
    session.commit()
    session.refresh(timeline)
    return timeline_read(session, timeline)


def transition_milestone(
    session: Session,
    timeline_id: UUID,
    milestone_id: UUID,
    *,
    action: str,
    note: str | None,
    actor: str,
) -> MobilityTimelineRead:
    timeline = session.get(MobilityTimeline, timeline_id)
    milestone = session.get(MobilityTimelineMilestone, milestone_id)
    if timeline is None or milestone is None or milestone.timeline_id != timeline_id:
        raise ValueError("Mobility timeline or milestone not found")
    _ensure_current_consent(session, timeline, actor)
    if timeline.status != "active":
        raise ValueError("Timeline must be active before milestone transitions")
    rows = _milestones(session, timeline.id)
    by_key = {row.stage_key: row for row in rows}
    dependencies = _load(milestone.dependencies_json, [])
    dependencies_complete = all(by_key[key].status == "completed" for key in dependencies)
    now = now_utc()
    before = {"status": milestone.status, "blockers": _load(milestone.blockers_json, [])}
    clean_note = note.strip() if note else None

    if action == "start":
        if milestone.status != "ready" or not dependencies_complete:
            raise ValueError("Milestone is not ready or its dependencies are incomplete")
        milestone.status = "in_progress"
        milestone.started_at = now
    elif action == "complete":
        if milestone.status not in {"ready", "in_progress"} or not dependencies_complete:
            raise ValueError("Milestone cannot be completed before its dependencies")
        if milestone.requires_human_approval and not clean_note:
            raise ValueError("A human approval note is required to complete this milestone")
        milestone.status = "completed"
        milestone.started_at = milestone.started_at or now
        milestone.completed_at = now
        milestone.approved_by = actor if milestone.requires_human_approval else milestone.approved_by
    elif action == "block":
        if milestone.status not in {"ready", "in_progress"}:
            raise ValueError("Only a ready or in-progress milestone can be blocked")
        if not clean_note:
            raise ValueError("A blocker reason is required")
        milestone.status = "blocked"
        milestone.blockers_json = _dump([clean_note])
    elif action == "unblock":
        if milestone.status != "blocked":
            raise ValueError("Only a blocked milestone can be unblocked")
        milestone.status = "ready" if dependencies_complete else "pending"
        milestone.blockers_json = _dump([])
    else:
        raise ValueError("Unsupported timeline transition")

    if clean_note:
        milestone.notes = clean_note
    milestone.updated_at = now
    if action == "complete":
        completed_keys = {row.stage_key for row in rows if row.status == "completed"}
        completed_keys.add(milestone.stage_key)
        for row in rows:
            if row.status != "pending":
                continue
            deps = _load(row.dependencies_json, [])
            if all(key in completed_keys for key in deps):
                row.status = "ready"
                row.updated_at = now
        remaining = [row for row in rows if row.status != "completed"]
        if not remaining:
            timeline.status = "completed"
            timeline.completed_at = now
            timeline.current_stage_key = None
        else:
            timeline.current_stage_key = remaining[0].stage_key
    timeline.updated_at = now
    record_audit(
        session,
        action="mobility_timeline_milestone_transitioned",
        entity_type="mobility_timeline_milestone",
        entity_id=milestone.id,
        before_state=before,
        after_state={"status": milestone.status, "approved_by": milestone.approved_by},
        reason=clean_note or action,
        actor=actor,
        source="mobility_timeline_v8_3",
    )
    session.commit()
    session.refresh(timeline)
    return timeline_read(session, timeline)
