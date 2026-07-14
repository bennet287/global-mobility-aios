from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import DocumentRecord, Lead, Profile, now_utc
from app.schemas import UniversalMobilityProfileRead, UniversalMobilityProfileUpsert
from app.services.audit_log import record_audit


def _load(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        loaded = json.loads(value)
        return loaded
    except (TypeError, ValueError):
        return default


def _dump(value: Any) -> str:
    return json.dumps(value, default=str, sort_keys=True)


def current_mobility_profile(session: Session, lead_id: UUID) -> Profile | None:
    """Return the newest immutable profile version, including restricted versions."""
    return session.exec(
        select(Profile)
        .where(Profile.lead_id == lead_id)
        .order_by(Profile.profile_version.desc(), Profile.updated_at.desc())
    ).first()


def profile_facts(profile: Profile | None) -> dict[str, Any]:
    """Expose one normalized fact shape to downstream decision services."""
    if profile is None:
        return {}

    education = _load(profile.education_json, [])
    employment = _load(profile.employment_json, [])
    family = _load(profile.family_json, {})
    finances = _load(profile.finances_json, {})
    goals = _load(profile.goals_json, [])
    constraints = _load(profile.constraints_json, {})
    consent = _load(profile.consent_json, {})
    evidence = _load(profile.evidence_json, [])
    skills_value = _load(profile.skills_json, [])
    if isinstance(skills_value, dict):
        skills = skills_value.get("skills", [])
    else:
        skills = skills_value if isinstance(skills_value, list) else []
    languages_value = _load(profile.language_scores_json, [])
    if isinstance(languages_value, dict):
        languages = languages_value.get("languages", [])
        if not languages and languages_value:
            languages = [languages_value]
    else:
        languages = languages_value if isinstance(languages_value, list) else []

    primary_education = education[0] if education else {}
    primary_goal = goals[0] if goals else {}
    current_employment = next(
        (item for item in employment if isinstance(item, dict) and item.get("current")),
        employment[0] if employment else {},
    )
    return {
        "profile_id": profile.id,
        "profile_version": profile.profile_version,
        "lifecycle_status": profile.lifecycle_status,
        "completeness_score": profile.completeness_score,
        "readiness_stage": profile.readiness_stage,
        "consent_status": profile.consent_status,
        "current_country": profile.current_country,
        "target_country": primary_goal.get("target_country") or profile.target_country,
        "desired_role": primary_goal.get("desired_role_or_program") or current_employment.get("role") or profile.desired_role,
        "highest_qualification": primary_education.get("qualification") or profile.highest_qualification,
        "field_of_study": primary_education.get("field_of_study") or profile.field_of_study,
        "years_experience": profile.years_experience,
        "budget_eur": finances.get("budget_eur", finances.get("available_budget_eur", profile.budget_eur)),
        "education": education,
        "employment": employment,
        "skills": skills,
        "languages": languages,
        "family": family,
        "finances": finances,
        "goals": goals,
        "constraints": constraints,
        "consent": consent,
        "evidence_document_ids": evidence,
    }


def _completeness(payload: UniversalMobilityProfileUpsert) -> tuple[float, str, list[str]]:
    checks = {
        "current_country": (10, bool(payload.current_country)),
        "education": (10, bool(payload.education)),
        "employment": (10, bool(payload.employment) or payload.years_experience is not None),
        "skills": (10, bool(payload.skills)),
        "languages": (10, bool(payload.languages)),
        "family": (5, payload.family_details_confirmed),
        "finances": (10, bool(payload.finances)),
        "goals": (15, bool(payload.goals)),
        "constraints": (5, payload.constraints_confirmed),
        "consent": (10, payload.consent_status == "granted"),
        "evidence": (5, bool(payload.evidence_document_ids)),
    }
    score = float(sum(weight for weight, present in checks.values() if present))
    missing = [name for name, (_, present) in checks.items() if not present]
    if payload.consent_status == "withdrawn":
        readiness = "restricted"
    elif score >= 85 and payload.evidence_document_ids and payload.consent_status == "granted":
        readiness = "evidence_ready"
    elif score >= 70:
        readiness = "pathway_ready"
    elif score >= 40:
        readiness = "developing"
    else:
        readiness = "foundation"
    return score, readiness, missing


def mobility_profile_read(profile: Profile) -> UniversalMobilityProfileRead:
    facts = profile_facts(profile)
    return UniversalMobilityProfileRead(
        id=profile.id,
        lead_id=profile.lead_id,
        profile_version=profile.profile_version,
        lifecycle_status=profile.lifecycle_status,
        supersedes_profile_id=profile.supersedes_profile_id,
        current_country=profile.current_country,
        education=facts.get("education", []),
        employment=facts.get("employment", []),
        years_experience=profile.years_experience,
        skills=facts.get("skills", []),
        languages=facts.get("languages", []),
        family=facts.get("family", {}),
        finances=facts.get("finances", {}),
        goals=facts.get("goals", []),
        constraints=facts.get("constraints", {}),
        consent=facts.get("consent", {}),
        evidence_document_ids=[UUID(str(value)) for value in facts.get("evidence_document_ids", [])],
        completeness_score=profile.completeness_score,
        readiness_stage=profile.readiness_stage,
        consent_status=profile.consent_status,
        missing_sections=_load(profile.missing_fields_json, []),
        activated_at=profile.activated_at,
        updated_by=profile.updated_by,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


def create_mobility_profile_version(
    session: Session,
    lead_id: UUID,
    payload: UniversalMobilityProfileUpsert,
    *,
    actor: str = "system",
) -> Profile:
    lead = session.get(Lead, lead_id)
    if lead is None:
        raise ValueError("Lead not found")

    for document_id in payload.evidence_document_ids:
        document = session.get(DocumentRecord, document_id)
        if document is None:
            raise ValueError(f"Evidence document {document_id} not found")
        if document.lead_id != lead_id:
            raise ValueError(f"Evidence document {document_id} belongs to another lead")

    existing = list(session.exec(
        select(Profile)
        .where(Profile.lead_id == lead_id)
        .order_by(Profile.profile_version.desc(), Profile.updated_at.desc())
    ).all())
    previous = existing[0] if existing else None
    next_version = max((row.profile_version for row in existing), default=0) + 1
    now = now_utc()
    score, readiness, missing = _completeness(payload)
    dumped = payload.model_dump(mode="json")
    education = dumped["education"]
    employment = dumped["employment"]
    goals = dumped["goals"]
    finances = dumped["finances"]
    languages = dumped["languages"]
    primary_education = education[0] if education else {}
    primary_goal = goals[0] if goals else {}
    current_employment = next((item for item in employment if item.get("current")), employment[0] if employment else {})

    for row in existing:
        if row.lifecycle_status in {"active", "restricted"}:
            row.lifecycle_status = "superseded"
            row.updated_at = now
            session.add(row)

    profile = Profile(
        lead_id=lead_id,
        profile_type="universal_mobility",
        profile_version=next_version,
        lifecycle_status="restricted" if payload.consent_status == "withdrawn" else "active",
        supersedes_profile_id=previous.id if previous else None,
        highest_qualification=primary_education.get("qualification"),
        field_of_study=primary_education.get("field_of_study"),
        current_country=payload.current_country,
        target_country=primary_goal.get("target_country"),
        desired_role=primary_goal.get("desired_role_or_program") or current_employment.get("role"),
        years_experience=payload.years_experience,
        budget_eur=finances.get("budget_eur", finances.get("available_budget_eur")),
        language_scores_json=_dump(languages),
        skills_json=_dump(payload.skills),
        missing_fields_json=_dump(missing),
        education_json=_dump(education),
        employment_json=_dump(employment),
        family_json=_dump({
            "status": payload.family_status,
            "members": dumped["family"],
            "details_confirmed": payload.family_details_confirmed,
        }),
        finances_json=_dump(finances),
        goals_json=_dump(goals),
        constraints_json=_dump({"items": dumped["constraints"], "confirmed": payload.constraints_confirmed}),
        consent_json=_dump({
            "status": payload.consent_status,
            "purposes": payload.consent_purposes,
            "expires_at": dumped["consent_expires_at"],
            "recorded_at": now,
        }),
        evidence_json=_dump(dumped["evidence_document_ids"]),
        completeness_score=score,
        readiness_stage=readiness,
        consent_status=payload.consent_status,
        activated_at=now,
        updated_by=actor,
        created_at=now,
        updated_at=now,
    )
    session.add(profile)
    session.flush()
    record_audit(
        session,
        action="mobility_profile_version_created",
        entity_type="profile",
        entity_id=profile.id,
        before_state=mobility_profile_read(previous).model_dump(mode="json") if previous else None,
        after_state=mobility_profile_read(profile).model_dump(mode="json"),
        reason=f"Created immutable universal mobility profile version {next_version}",
        actor=actor,
        source="profiles_api",
    )
    session.commit()
    session.refresh(profile)
    return profile
