from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    DocumentRecord,
    Jurisdiction,
    Lead,
    MobilityPathway,
    MobilityPathwayVersion,
    OfficialSource,
    PathwayComparisonAssessment,
    Profile,
    SourceSnapshot,
    VerifiedRule,
    now_utc,
)
from app.schemas import (
    PathwayComparisonItem,
    PathwayComparisonRead,
    PathwayCostExplanation,
    PathwayCreate,
    PathwayRead,
    PathwayRiskExplanation,
    PathwayVersionInput,
    PathwayVersionRead,
)
from app.services.audit_log import record_audit
from app.services.mobility_profiles import current_mobility_profile, profile_facts


def _dump(value: Any) -> str:
    return json.dumps(value, default=str, sort_keys=True)


def _load(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def _normal(value: str | None) -> str:
    return (value or "").strip().lower()


def pathway_version_read(version: MobilityPathwayVersion) -> PathwayVersionRead:
    return PathwayVersionRead(
        id=version.id,
        pathway_id=version.pathway_id,
        version_number=version.version_number,
        lifecycle_status=version.lifecycle_status,
        supersedes_version_id=version.supersedes_version_id,
        official_source_id=version.official_source_id,
        source_snapshot_id=version.source_snapshot_id,
        verified_rule_ids=[UUID(str(value)) for value in _load(version.verified_rule_ids_json, [])],
        eligibility_criteria=_load(version.eligibility_criteria_json, {}),
        required_documents=_load(version.required_documents_json, []),
        costs=_load(version.costs_json, {}),
        processing_time=_load(version.processing_time_json, {}),
        benefits=_load(version.benefits_json, []),
        risks=_load(version.risks_json, []),
        metadata=_load(version.metadata_json, {}),
        effective_from=version.effective_from,
        effective_to=version.effective_to,
        human_review_required=version.human_review_required,
        approved_by=version.approved_by,
        review_notes=version.review_notes,
        published_at=version.published_at,
        created_by=version.created_by,
        created_at=version.created_at,
        updated_at=version.updated_at,
    )


def current_pathway_version(
    session: Session,
    pathway_id: UUID,
    *,
    published_only: bool = False,
) -> MobilityPathwayVersion | None:
    statement = select(MobilityPathwayVersion).where(MobilityPathwayVersion.pathway_id == pathway_id)
    if published_only:
        statement = statement.where(MobilityPathwayVersion.lifecycle_status == "published")
    return session.exec(statement.order_by(MobilityPathwayVersion.version_number.desc())).first()


def pathway_read(
    session: Session,
    pathway: MobilityPathway,
    *,
    published_only: bool = False,
) -> PathwayRead:
    version = current_pathway_version(session, pathway.id, published_only=published_only)
    return PathwayRead(
        id=pathway.id,
        pathway_key=pathway.pathway_key,
        name=pathway.name,
        country=pathway.country,
        domain=pathway.domain,
        jurisdiction_id=pathway.jurisdiction_id,
        description=pathway.description,
        catalogue_status=pathway.catalogue_status,
        created_by=pathway.created_by,
        created_at=pathway.created_at,
        updated_at=pathway.updated_at,
        current_version=pathway_version_read(version) if version else None,
    )


def pathway_read_with_version(pathway: MobilityPathway, version: MobilityPathwayVersion) -> PathwayRead:
    return PathwayRead(
        id=pathway.id,
        pathway_key=pathway.pathway_key,
        name=pathway.name,
        country=pathway.country,
        domain=pathway.domain,
        jurisdiction_id=pathway.jurisdiction_id,
        description=pathway.description,
        catalogue_status=pathway.catalogue_status,
        created_by=pathway.created_by,
        created_at=pathway.created_at,
        updated_at=pathway.updated_at,
        current_version=pathway_version_read(version),
    )


def _validate_draft_evidence(
    session: Session,
    pathway: MobilityPathway,
    payload: PathwayVersionInput,
) -> None:
    if pathway.jurisdiction_id and session.get(Jurisdiction, pathway.jurisdiction_id) is None:
        raise ValueError("Jurisdiction not found")
    source = session.get(OfficialSource, payload.official_source_id) if payload.official_source_id else None
    if payload.official_source_id and source is None:
        raise ValueError("Official source not found")
    if source and _normal(source.country) != _normal(pathway.country):
        raise ValueError("Official source country does not match the pathway")
    snapshot = session.get(SourceSnapshot, payload.source_snapshot_id) if payload.source_snapshot_id else None
    if payload.source_snapshot_id and snapshot is None:
        raise ValueError("Source snapshot not found")
    if snapshot and payload.official_source_id and snapshot.official_source_id != payload.official_source_id:
        raise ValueError("Source snapshot does not belong to the selected official source")
    for rule_id in payload.verified_rule_ids:
        if session.get(VerifiedRule, rule_id) is None:
            raise ValueError(f"Verified rule {rule_id} not found")


def _create_version_row(
    session: Session,
    pathway: MobilityPathway,
    payload: PathwayVersionInput,
    *,
    actor: str,
) -> MobilityPathwayVersion:
    _validate_draft_evidence(session, pathway, payload)
    existing = list(session.exec(
        select(MobilityPathwayVersion)
        .where(MobilityPathwayVersion.pathway_id == pathway.id)
        .order_by(MobilityPathwayVersion.version_number.desc())
    ).all())
    previous = existing[0] if existing else None
    now = now_utc()
    dumped = payload.model_dump(mode="json")
    version = MobilityPathwayVersion(
        pathway_id=pathway.id,
        version_number=max((item.version_number for item in existing), default=0) + 1,
        lifecycle_status="draft",
        supersedes_version_id=previous.id if previous else None,
        official_source_id=payload.official_source_id,
        source_snapshot_id=payload.source_snapshot_id,
        verified_rule_ids_json=_dump(dumped["verified_rule_ids"]),
        eligibility_criteria_json=_dump(payload.eligibility_criteria),
        required_documents_json=_dump(payload.required_documents),
        costs_json=_dump(payload.costs),
        processing_time_json=_dump(payload.processing_time),
        benefits_json=_dump(payload.benefits),
        risks_json=_dump(payload.risks),
        metadata_json=_dump(payload.metadata),
        effective_from=payload.effective_from,
        effective_to=payload.effective_to,
        human_review_required=True,
        created_by=actor,
        created_at=now,
        updated_at=now,
    )
    session.add(version)
    session.flush()
    return version


def create_pathway(
    session: Session,
    payload: PathwayCreate,
    *,
    actor: str,
) -> tuple[MobilityPathway, MobilityPathwayVersion]:
    key = _normal(payload.pathway_key).replace(" ", "-")
    if session.exec(select(MobilityPathway).where(MobilityPathway.pathway_key == key)).first():
        raise ValueError("Pathway key already exists")
    if payload.jurisdiction_id and session.get(Jurisdiction, payload.jurisdiction_id) is None:
        raise ValueError("Jurisdiction not found")
    now = now_utc()
    pathway = MobilityPathway(
        pathway_key=key,
        name=payload.name.strip(),
        country=_normal(payload.country),
        domain=_normal(payload.domain),
        jurisdiction_id=payload.jurisdiction_id,
        description=payload.description,
        catalogue_status="draft",
        created_by=actor,
        created_at=now,
        updated_at=now,
    )
    session.add(pathway)
    session.flush()
    version = _create_version_row(session, pathway, payload, actor=actor)
    record_audit(
        session,
        action="mobility_pathway_created",
        entity_type="mobility_pathway",
        entity_id=pathway.id,
        after_state={
            "pathway": pathway.model_dump(mode="json"),
            "version": version.model_dump(mode="json"),
        },
        reason="Created governed pathway with draft version 1",
        actor=actor,
        source="pathway_catalogue_v8_1",
    )
    session.commit()
    session.refresh(pathway)
    session.refresh(version)
    return pathway, version


def create_pathway_version(
    session: Session,
    pathway_id: UUID,
    payload: PathwayVersionInput,
    *,
    actor: str,
) -> MobilityPathwayVersion:
    pathway = session.get(MobilityPathway, pathway_id)
    if pathway is None:
        raise ValueError("Pathway not found")
    if pathway.catalogue_status == "retired":
        raise ValueError("Retired pathways cannot receive new versions")
    version = _create_version_row(session, pathway, payload, actor=actor)
    pathway.updated_at = now_utc()
    session.add(pathway)
    record_audit(
        session,
        action="mobility_pathway_version_created",
        entity_type="mobility_pathway_version",
        entity_id=version.id,
        after_state=version,
        reason=f"Created immutable draft version {version.version_number}",
        actor=actor,
        source="pathway_catalogue_v8_1",
    )
    session.commit()
    session.refresh(version)
    return version


def _relevant_rule_domains(pathway_domain: str) -> set[str]:
    return {
        "study": {"study", "visa"},
        "work": {"work", "visa"},
        "visa": {"visa"},
        "scholarship": {"scholarship", "study"},
        "settlement": {"settlement", "visa"},
        "family": {"family", "visa"},
        "digital_nomad": {"digital_nomad", "work", "visa"},
    }.get(pathway_domain, {pathway_domain})


def publish_pathway_version(
    session: Session,
    version_id: UUID,
    *,
    actor: str,
    review_notes: str,
) -> tuple[MobilityPathway, MobilityPathwayVersion]:
    version = session.get(MobilityPathwayVersion, version_id)
    if version is None:
        raise ValueError("Pathway version not found")
    if version.lifecycle_status != "draft":
        raise ValueError("Only draft pathway versions can be published")
    pathway = session.get(MobilityPathway, version.pathway_id)
    if pathway is None or pathway.catalogue_status == "retired":
        raise ValueError("Pathway is not publishable")
    source = session.get(OfficialSource, version.official_source_id) if version.official_source_id else None
    if source is None or not source.active:
        raise ValueError("An active official source is required before publication")
    if _normal(source.country) != pathway.country:
        raise ValueError("Official source country no longer matches the pathway")
    snapshot = session.get(SourceSnapshot, version.source_snapshot_id) if version.source_snapshot_id else None
    if snapshot is None or snapshot.official_source_id != source.id:
        raise ValueError("A snapshot from the selected official source is required before publication")
    rule_ids = [UUID(str(value)) for value in _load(version.verified_rule_ids_json, [])]
    if not rule_ids:
        raise ValueError("At least one active verified rule is required before publication")
    allowed_domains = _relevant_rule_domains(pathway.domain)
    for rule_id in rule_ids:
        rule = session.get(VerifiedRule, rule_id)
        if rule is None or not rule.active:
            raise ValueError(f"Verified rule {rule_id} is missing or inactive")
        if _normal(rule.country) != pathway.country or _normal(rule.domain) not in allowed_domains:
            raise ValueError(f"Verified rule {rule_id} does not match the pathway jurisdiction or domain")

    now = now_utc()
    published = list(session.exec(
        select(MobilityPathwayVersion).where(
            MobilityPathwayVersion.pathway_id == pathway.id,
            MobilityPathwayVersion.lifecycle_status == "published",
        )
    ).all())
    for previous in published:
        previous.lifecycle_status = "superseded"
        previous.updated_at = now
        session.add(previous)
    version.lifecycle_status = "published"
    version.approved_by = actor
    version.review_notes = review_notes
    version.published_at = now
    version.updated_at = now
    pathway.catalogue_status = "active"
    pathway.updated_at = now
    session.add(version)
    session.add(pathway)
    record_audit(
        session,
        action="mobility_pathway_version_published",
        entity_type="mobility_pathway_version",
        entity_id=version.id,
        before_state={"lifecycle_status": "draft"},
        after_state=version,
        reason=review_notes,
        actor=actor,
        source="pathway_catalogue_v8_1",
    )
    session.commit()
    session.refresh(pathway)
    session.refresh(version)
    return pathway, version


def retire_pathway(
    session: Session,
    pathway_id: UUID,
    *,
    actor: str,
    reason: str,
) -> MobilityPathway:
    pathway = session.get(MobilityPathway, pathway_id)
    if pathway is None:
        raise ValueError("Pathway not found")
    before = {"catalogue_status": pathway.catalogue_status}
    now = now_utc()
    pathway.catalogue_status = "retired"
    pathway.updated_at = now
    versions = session.exec(
        select(MobilityPathwayVersion).where(
            MobilityPathwayVersion.pathway_id == pathway_id,
            MobilityPathwayVersion.lifecycle_status.in_(["draft", "published"]),
        )
    ).all()
    for version in versions:
        version.lifecycle_status = "retired"
        version.updated_at = now
        session.add(version)
    session.add(pathway)
    record_audit(
        session,
        action="mobility_pathway_retired",
        entity_type="mobility_pathway",
        entity_id=pathway.id,
        before_state=before,
        after_state={"catalogue_status": "retired"},
        reason=reason,
        actor=actor,
        source="pathway_catalogue_v8_1",
    )
    session.commit()
    session.refresh(pathway)
    return pathway


def _intent_domain(lead: Lead, facts: dict[str, Any]) -> str:
    goals = facts.get("goals", [])
    if goals:
        return _normal(goals[0].get("domain"))
    value = _normal(getattr(lead.intent, "value", lead.intent))
    return {"study_abroad": "study", "overseas_job": "work"}.get(value, value)


def match_pathways_for_lead(
    session: Session,
    lead_id: UUID,
    *,
    limit: int = 10,
    profile_override: Profile | None = None,
    pathway_version_ids: list[UUID] | None = None,
    country_scope: str = "target",
) -> dict[str, Any]:
    lead = session.get(Lead, lead_id)
    if lead is None:
        raise ValueError("Lead not found")
    profile = profile_override or current_mobility_profile(session, lead_id)
    facts = profile_facts(profile)
    consent = profile.consent_status if profile else "not_recorded"
    if consent == "withdrawn":
        return {
            "lead_id": lead_id,
            "profile_id": profile.id,
            "profile_version": profile.profile_version,
            "consent_status": consent,
            "matches": [],
            "summary": "Pathway matching is restricted because profile consent was withdrawn.",
        }

    country = _normal(facts.get("target_country") or lead.target_country)
    if country_scope not in {"target", "global"}:
        raise ValueError("Country scope must be target or global")
    domain = _intent_domain(lead, facts)
    documents = list(session.exec(select(DocumentRecord).where(DocumentRecord.lead_id == lead_id)).all())
    document_types = {_normal(document.document_type) for document in documents}
    candidate_pairs: list[tuple[MobilityPathway, MobilityPathwayVersion]] = []
    if pathway_version_ids is not None:
        seen: set[UUID] = set()
        for version_id in pathway_version_ids:
            if version_id in seen:
                continue
            seen.add(version_id)
            version = session.get(MobilityPathwayVersion, version_id)
            pathway = session.get(MobilityPathway, version.pathway_id) if version else None
            if version is None or pathway is None:
                raise ValueError("Accepted pathway version provenance is incomplete")
            if version.lifecycle_status not in {"published", "superseded", "retired"}:
                raise ValueError("Accepted pathway versions must have completed human-reviewed publication")
            candidate_pairs.append((pathway, version))
    elif country_scope == "global":
        candidates = list(session.exec(
            select(MobilityPathway).where(MobilityPathway.catalogue_status == "active")
        ).all())
        for pathway in candidates:
            version = current_pathway_version(session, pathway.id, published_only=True)
            if version is not None:
                candidate_pairs.append((pathway, version))
    elif country:
        candidates = list(session.exec(
            select(MobilityPathway).where(
                MobilityPathway.catalogue_status == "active",
                MobilityPathway.country == country,
            )
        ).all())
        for pathway in candidates:
            version = current_pathway_version(session, pathway.id, published_only=True)
            if version is not None:
                candidate_pairs.append((pathway, version))
    now = now_utc()
    matches: list[dict[str, Any]] = []
    for pathway, version in candidate_pairs:
        if country_scope == "target" and country and pathway.country != country:
            continue
        if version.effective_from and version.effective_from > now:
            continue
        if version.effective_to and version.effective_to < now:
            continue
        criteria = _load(version.eligibility_criteria_json, {})
        reasons = [
            f"Target country matches {pathway.country.title()}"
            if country_scope == "target"
            else f"Human-published pathway is available in {pathway.country.title()}"
        ]
        missing: list[str] = []
        score = 0.35
        if domain == pathway.domain or pathway.domain == "visa":
            score += 0.25
            reasons.append(f"Pathway domain aligns with {domain or 'general'} goal")

        years = float(facts.get("years_experience") or 0)
        minimum_years = float(criteria.get("minimum_years_experience") or 0)
        if minimum_years:
            if years >= minimum_years:
                score += 0.1
                reasons.append(f"Meets {minimum_years:g}-year experience threshold")
            else:
                missing.append(f"Requires at least {minimum_years:g} years of experience")

        required_skills = {_normal(value) for value in criteria.get("required_skills", []) if value}
        profile_skills = {_normal(value) for value in facts.get("skills", []) if value}
        if required_skills:
            overlap = required_skills & profile_skills
            score += 0.1 * (len(overlap) / len(required_skills))
            if overlap:
                reasons.append(f"Matched skills: {', '.join(sorted(overlap))}")
            for skill in sorted(required_skills - profile_skills):
                missing.append(f"Skill evidence missing: {skill}")

        qualification = _normal(facts.get("highest_qualification"))
        qualification_keywords = {_normal(value) for value in criteria.get("qualification_keywords", []) if value}
        if qualification_keywords:
            if any(keyword in qualification for keyword in qualification_keywords):
                score += 0.1
                reasons.append("Qualification aligns with pathway criteria")
            else:
                missing.append("Required qualification evidence is missing or does not match")

        required_languages = {_normal(value) for value in criteria.get("required_languages", []) if value}
        profile_languages = {
            _normal(item.get("language"))
            for item in facts.get("languages", [])
            if isinstance(item, dict) and item.get("language")
        }
        if required_languages:
            matched_languages = required_languages & profile_languages
            if matched_languages:
                score += 0.05 * (len(matched_languages) / len(required_languages))
                reasons.append(f"Matched languages: {', '.join(sorted(matched_languages))}")
            for language in sorted(required_languages - profile_languages):
                missing.append(f"Language evidence missing: {language}")

        available_funds = float(facts.get("budget_eur") or 0)
        minimum_funds = float(criteria.get("minimum_funds_eur") or 0)
        if minimum_funds:
            if available_funds >= minimum_funds:
                score += 0.05
                reasons.append("Recorded funds meet the pathway threshold")
            else:
                missing.append(f"Financial evidence below EUR {minimum_funds:,.0f}")

        required_evidence = {_normal(value) for value in criteria.get("required_evidence", []) if value}
        for evidence in sorted(required_evidence - document_types):
            missing.append(f"Document missing: {evidence}")
        if required_evidence and required_evidence <= document_types:
            score += 0.05
            reasons.append("Required profile evidence is uploaded")

        score = round(min(score, 1.0), 2)
        matches.append({
            "pathway": pathway_read_with_version(pathway, version),
            "match_score": score,
            "confidence": round(min(0.55 + score * 0.4, 0.95), 2),
            "reasons": reasons,
            "missing_evidence": missing,
            "verified_rule_ids": [UUID(str(value)) for value in _load(version.verified_rule_ids_json, [])],
        })
    matches.sort(key=lambda item: item["match_score"], reverse=True)
    maximum = 1000 if country_scope == "global" else 50
    selected = matches[: max(1, min(limit, maximum))]
    return {
        "lead_id": lead_id,
        "profile_id": profile.id if profile else None,
        "profile_version": profile.profile_version if profile else None,
        "consent_status": consent,
        "matches": selected,
        "summary": (
            f"Matched {len(selected)} published, evidence-backed pathways across the reviewed catalogue."
            if country_scope == "global"
            else f"Matched {len(selected)} published, evidence-backed pathways for {country.title() if country else 'the selected profile'}."
        ),
    }


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _cost_explanation(version: PathwayVersionRead) -> PathwayCostExplanation:
    costs = version.costs
    currency = str(costs.get("currency") or "EUR").upper()
    components: dict[str, float] = {}
    one_time = 0.0
    monthly = 0.0
    annual = 0.0
    minimum_funds = _number(costs.get("minimum_funds_eur"))
    criteria_funds = _number(version.eligibility_criteria.get("minimum_funds_eur"))
    if minimum_funds is None:
        minimum_funds = criteria_funds
    for key, raw in costs.items():
        value = _number(raw)
        if value is None or key in {"minimum_funds_eur", "currency"}:
            continue
        components[key] = value
        normalized = key.lower()
        if "monthly" in normalized:
            monthly += value
        elif "annual" in normalized or "yearly" in normalized:
            annual += value
        else:
            one_time += value
    notes: list[str] = []
    if not components:
        notes.append("No payable fee components are recorded in the published pathway version.")
    if minimum_funds is not None:
        notes.append("Minimum funds are an eligibility threshold, not a payable fee.")
    notes.append("Amounts are catalogue estimates and require operator verification before client use.")
    return PathwayCostExplanation(
        currency=currency,
        one_time_total=round(one_time, 2) if any("monthly" not in key.lower() and "annual" not in key.lower() and "yearly" not in key.lower() for key in components) else None,
        monthly_total=round(monthly, 2) if monthly else None,
        annual_total=round(annual, 2) if annual else None,
        minimum_funds=minimum_funds,
        components=components,
        notes=notes,
    )


def _utc(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _risk_explanation(
    session: Session,
    version: PathwayVersionRead,
    missing_evidence: list[str],
) -> PathwayRiskExplanation:
    declared = list(version.risks)
    evidence = list(missing_evidence)
    regulatory: list[str] = []
    for rule_id in version.verified_rule_ids:
        rule = session.get(VerifiedRule, rule_id)
        if rule is None or not rule.active:
            regulatory.append(f"Verified rule {rule_id} is no longer active; re-review is required.")
        elif rule.confidence < 0.9:
            regulatory.append(f"Verified rule {rule.rule_key} has confidence below 0.90.")
    snapshot = session.get(SourceSnapshot, version.source_snapshot_id) if version.source_snapshot_id else None
    if snapshot is None:
        regulatory.append("The published pathway has no retrievable source snapshot.")
    else:
        age_days = max(0, (now_utc() - _utc(snapshot.captured_at)).days)
        if age_days > 180:
            regulatory.append(f"Official-source snapshot is {age_days} days old and should be refreshed.")
    source = session.get(OfficialSource, version.official_source_id) if version.official_source_id else None
    if source is None or not source.active:
        regulatory.append("The linked official source is inactive or unavailable.")
    score = min(1.0, len(declared) * 0.12 + len(evidence) * 0.1 + len(regulatory) * 0.25)
    level = "high" if score >= 0.65 else "medium" if score >= 0.3 else "low"
    return PathwayRiskExplanation(
        level=level,
        score=round(score, 2),
        declared_risks=declared,
        evidence_risks=evidence,
        regulatory_risks=regulatory,
    )


def _comparison_item(session: Session, match: dict[str, Any]) -> PathwayComparisonItem:
    pathway: PathwayRead = match["pathway"]
    version = pathway.current_version
    if version is None:
        raise ValueError("Published pathway version is missing")
    cost = _cost_explanation(version)
    missing = list(dict.fromkeys(match.get("missing_evidence", [])))
    risk = _risk_explanation(session, version, missing)
    tradeoffs: list[str] = []
    if cost.one_time_total is None:
        tradeoffs.append("Upfront payable costs are not yet complete in the catalogue.")
    else:
        tradeoffs.append(f"Recorded upfront fees total {cost.currency} {cost.one_time_total:,.2f}.")
    timing = version.processing_time
    if timing.get("minimum_weeks") is not None or timing.get("maximum_weeks") is not None:
        tradeoffs.append(
            f"Recorded processing range is {timing.get('minimum_weeks', '?')}–{timing.get('maximum_weeks', '?')} weeks."
        )
    else:
        tradeoffs.append("No reviewed processing-time range is recorded.")
    tradeoffs.append(f"{len(missing)} profile or document evidence gap(s) remain.")
    explanation = (
        f"{pathway.name} scored {round(match['match_score'] * 100)}% against the current profile. "
        f"Its current risk level is {risk.level}, with {len(missing)} missing evidence item(s)."
    )
    return PathwayComparisonItem(
        pathway=pathway,
        match_score=match["match_score"],
        confidence=match["confidence"],
        reasons=match.get("reasons", []),
        cost=cost,
        risk=risk,
        missing_evidence=missing,
        benefits=version.benefits,
        tradeoffs=tradeoffs,
        explanation=explanation,
        verified_rule_ids=match.get("verified_rule_ids", []),
    )


def generate_pathway_comparison(
    session: Session,
    lead_id: UUID,
    *,
    actor: str,
    limit: int = 5,
    profile_override: Profile | None = None,
    pathway_version_ids: list[UUID] | None = None,
    reassessment_acceptance_id: UUID | None = None,
) -> PathwayComparisonRead:
    lead = session.get(Lead, lead_id)
    if lead is None:
        raise ValueError("Lead not found")
    profile = profile_override or current_mobility_profile(session, lead_id)
    consent = profile.consent_status if profile else "not_recorded"
    generated_at = now_utc()
    if consent == "withdrawn":
        record_audit(
            session,
            action="pathway_comparison_restricted",
            entity_type="lead",
            entity_id=lead_id,
            reason="Current profile consent is withdrawn",
            actor=actor,
            source="pathway_comparison_v8_2",
        )
        session.commit()
        return PathwayComparisonRead(
            lead_id=lead_id,
            profile_id=profile.id,
            profile_version=profile.profile_version,
            status="restricted",
            consent_status=consent,
            summary="Pathway comparison is restricted because profile consent was withdrawn.",
            generated_by=actor,
            generated_at=generated_at,
        )

    match_result = match_pathways_for_lead(
        session,
        lead_id,
        limit=limit,
        profile_override=profile,
        pathway_version_ids=pathway_version_ids,
    )
    items = [_comparison_item(session, match) for match in match_result.get("matches", [])]
    primary = items[0] if items else None
    alternatives = items[1:]
    missing = list(dict.fromkeys(
        evidence
        for item in items
        for evidence in item.missing_evidence
    ))
    if not profile:
        missing.insert(0, "Universal mobility profile has not been created.")
    elif profile.completeness_score < 70:
        missing.insert(0, f"Universal mobility profile is only {profile.completeness_score:.0f}% complete.")
    if primary:
        status = "ready_for_review" if profile and profile.completeness_score >= 70 else "needs_profile_review"
        summary = (
            f"{primary.pathway.name} is the leading evidence-backed option at "
            f"{round(primary.match_score * 100)}%, with {len(alternatives)} alternative(s). "
            "A human operator must verify costs, risks, and regulatory freshness before client use."
        )
    else:
        status = "insufficient_pathways"
        summary = "No published evidence-backed pathways match the current target country and profile."

    comparison_payload = {
        "consent_status": consent,
        "primary": primary.model_dump(mode="json") if primary else None,
        "alternatives": [item.model_dump(mode="json") for item in alternatives],
        "reassessment_acceptance_id": str(reassessment_acceptance_id) if reassessment_acceptance_id else None,
    }
    assessment = PathwayComparisonAssessment(
        lead_id=lead_id,
        profile_id=profile.id if profile else None,
        profile_version=profile.profile_version if profile else None,
        primary_pathway_id=primary.pathway.id if primary else None,
        primary_pathway_version_id=primary.pathway.current_version.id if primary and primary.pathway.current_version else None,
        status=status,
        comparison_json=_dump(comparison_payload),
        cost_summary_json=_dump(primary.cost.model_dump(mode="json") if primary else {}),
        risk_summary_json=_dump(primary.risk.model_dump(mode="json") if primary else {}),
        alternative_pathways_json=_dump([str(item.pathway.id) for item in alternatives]),
        missing_evidence_json=_dump(missing),
        summary=summary,
        human_review_required=True,
        generated_by=actor,
        created_at=generated_at,
    )
    session.add(assessment)
    session.flush()
    record_audit(
        session,
        action="pathway_comparison_generated",
        entity_type="pathway_comparison_assessment",
        entity_id=assessment.id,
        after_state={
            "lead_id": str(lead_id),
            "profile_id": str(profile.id) if profile else None,
            "profile_version": profile.profile_version if profile else None,
            "status": status,
            "primary_pathway_id": str(primary.pathway.id) if primary else None,
            "alternative_count": len(alternatives),
            "missing_evidence_count": len(missing),
            "reassessment_acceptance_id": str(reassessment_acceptance_id) if reassessment_acceptance_id else None,
        },
        reason=(
            "Generated explicitly accepted reassessment from pinned profile and regulatory versions"
            if reassessment_acceptance_id
            else "Generated deterministic pathway cost, risk, alternatives, and evidence comparison"
        ),
        actor=actor,
        source="reassessment_acceptance_v10_12" if reassessment_acceptance_id else "pathway_comparison_v8_2",
    )
    session.commit()
    session.refresh(assessment)
    return PathwayComparisonRead(
        assessment_id=assessment.id,
        lead_id=lead_id,
        profile_id=assessment.profile_id,
        profile_version=assessment.profile_version,
        status=status,
        consent_status=consent,
        primary=primary,
        alternatives=alternatives,
        missing_evidence=missing,
        summary=summary,
        human_review_required=True,
        generated_by=actor,
        generated_at=assessment.created_at,
    )


def pathway_comparison_read(assessment: PathwayComparisonAssessment) -> PathwayComparisonRead:
    comparison = _load(assessment.comparison_json, {})
    return PathwayComparisonRead(
        assessment_id=assessment.id,
        lead_id=assessment.lead_id,
        profile_id=assessment.profile_id,
        profile_version=assessment.profile_version,
        status=assessment.status,
        consent_status=comparison.get("consent_status", "not_recorded"),
        primary=comparison.get("primary"),
        alternatives=comparison.get("alternatives", []),
        missing_evidence=_load(assessment.missing_evidence_json, []),
        summary=assessment.summary or "",
        human_review_required=assessment.human_review_required,
        generated_by=assessment.generated_by,
        generated_at=assessment.created_at,
    )
