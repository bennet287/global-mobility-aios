from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlmodel import Session, select

from app.models.domain import (
    BusinessMobilityAdvisoryAssessment,
    BusinessMobilityAdvisoryReview,
    CorporateMobilityCase,
    DocumentRecord,
    InvestmentMobilityProgram,
    InvestmentMobilityProgramVersion,
    Lead,
    MobilityPathway,
    MobilityPathwayVersion,
)
from app.schemas_business_advisory import (
    BusinessAdvisoryCreate,
    BusinessAdvisoryRead,
    BusinessAdvisoryReviewCreate,
    BusinessStrategyOption,
)
from app.services.audit_log import record_audit, to_audit_dict


SCORE_SEMANTICS = (
    "Decision-support feasibility from disclosed facts, controlled evidence, and published pathway coverage; "
    "it is not a probability, guarantee, legal opinion, tax opinion, or authority prediction."
)

INTENT_STRATEGIES = {
    "launch_startup": ["founder_startup", "entrepreneur_operating_business", "company_expansion"],
    "expand_existing_business": ["company_expansion", "intra_company_transfer", "entrepreneur_operating_business"],
    "founder_relocation": ["founder_startup", "entrepreneur_operating_business", "intra_company_transfer"],
    "passive_investment": ["investor_residence", "active_business_investment", "asset_and_family_mobility"],
    "family_office_relocation": ["family_office_mobility", "investor_residence", "tax_residency_specialist"],
    "tax_residency_planning": ["tax_residency_specialist", "family_office_mobility", "operating_business_substance"],
    "asset_and_family_mobility": ["asset_and_family_mobility", "family_office_mobility", "investor_residence"],
}

STRATEGY_TITLES = {
    "founder_startup": "Founder or startup pathway",
    "entrepreneur_operating_business": "Entrepreneur-led operating business",
    "company_expansion": "Existing-company international expansion",
    "intra_company_transfer": "Intra-company founder or executive transfer",
    "investor_residence": "Passive-investor residence pathway",
    "active_business_investment": "Active business investment and management",
    "asset_and_family_mobility": "Coordinated asset and family mobility",
    "family_office_mobility": "Family-office relocation structure",
    "tax_residency_specialist": "Tax-residency-led mobility planning",
    "operating_business_substance": "Operating-company substance strategy",
}

PROHIBITED_SIGNALS = {
    "hide ownership", "conceal ownership", "nominee owner", "fake document", "forge",
    "backdate", "evade tax", "avoid sanctions", "bypass sanctions", "unexplained cash",
    "sham company", "hide funds", "misrepresent",
}

SPECIALIST_SIGNALS = {
    "criminal record", "visa refusal", "prior refusal", "sanction", "pep", "politically exposed",
    "tax debt", "source of funds", "bankruptcy", "litigation",
}

BUSINESS_DOMAINS = {"business", "entrepreneur", "startup", "investment", "wealth", "tax", "corporate"}


def _dump(value: Any) -> str:
    return json.dumps(value, default=str, sort_keys=True)


def _load(value: str, default: Any) -> Any:
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def _band(score: float) -> str:
    if score >= 75:
        return "strong"
    if score >= 55:
        return "workable"
    if score >= 35:
        return "constrained"
    return "evidence_limited"


def advisory_read(row: BusinessMobilityAdvisoryAssessment) -> BusinessAdvisoryRead:
    return BusinessAdvisoryRead(
        **row.model_dump(),
        strategy_options=[BusinessStrategyOption.model_validate(item) for item in _load(row.strategy_options_json, [])],
        blockers=_load(row.blockers_json, []),
        next_actions=_load(row.next_actions_json, []),
        evidence_basis=_load(row.evidence_basis_json, []),
        risk_flags=_load(row.risk_flags_json, []),
        score_semantics=SCORE_SEMANTICS,
    )


def _published_pathways(session: Session, countries: list[str]) -> list[dict[str, Any]]:
    normalized = {country.strip().lower() for country in countries}
    pathways = list(session.exec(select(MobilityPathway).where(
        MobilityPathway.catalogue_status.in_(["active", "published"])
    )).all())
    results: list[dict[str, Any]] = []
    for pathway in pathways:
        if pathway.country.strip().lower() not in normalized or pathway.domain.strip().lower() not in BUSINESS_DOMAINS:
            continue
        version = session.exec(select(MobilityPathwayVersion).where(
            MobilityPathwayVersion.pathway_id == pathway.id,
            MobilityPathwayVersion.lifecycle_status == "published",
        ).order_by(MobilityPathwayVersion.version_number.desc())).first()
        if version is None:
            continue
        results.append({
            "pathway_id": str(pathway.id),
            "pathway_version_id": str(version.id),
            "name": pathway.name,
            "country": pathway.country,
            "domain": pathway.domain,
            "official_source_id": str(version.official_source_id) if version.official_source_id else None,
            "source_snapshot_id": str(version.source_snapshot_id) if version.source_snapshot_id else None,
            "verified_rule_ids": _load(version.verified_rule_ids_json or "[]", []),
        })
    return results


def _published_investment_programs(session: Session, countries: list[str]) -> list[dict[str, Any]]:
    normalized = {country.strip().lower() for country in countries}
    programs = session.exec(select(InvestmentMobilityProgram).where(
        InvestmentMobilityProgram.catalogue_status == "active"
    )).all()
    results: list[dict[str, Any]] = []
    for program in programs:
        if program.country.strip().lower() not in normalized:
            continue
        version = session.exec(select(InvestmentMobilityProgramVersion).where(
            InvestmentMobilityProgramVersion.program_id == program.id,
            InvestmentMobilityProgramVersion.lifecycle_status == "published",
        ).order_by(InvestmentMobilityProgramVersion.version_number.desc())).first()
        if version is None:
            continue
        results.append({
            "program_id": str(program.id),
            "program_version_id": str(version.id),
            "name": program.name,
            "country": program.country,
            "program_type": program.program_type,
            "minimum_commitment_minor": version.minimum_commitment_minor,
            "currency": version.currency,
            "pathway_version_id": str(version.pathway_version_id),
            "official_source_id": str(version.official_source_id),
            "source_snapshot_id": str(version.source_snapshot_id),
        })
    return results


def _commercial_fit(payload: BusinessAdvisoryCreate) -> float:
    score = 25.0
    if payload.primary_intent in {"launch_startup", "founder_relocation"}:
        score += min(20.0, (payload.founder_experience_years or 0) * 2)
        score += 20 if payload.capital_available_minor is not None else 0
        score += 10 if payload.business_age_years is not None else 0
    elif payload.primary_intent == "expand_existing_business":
        score += 15 if (payload.business_age_years or 0) >= 2 else 0
        score += 20 if payload.annual_revenue_minor is not None else 0
        score += 15 if (payload.employees or 0) > 0 else 0
        score += 10 if payload.capital_available_minor is not None else 0
    elif payload.primary_intent in {"passive_investment", "family_office_relocation", "asset_and_family_mobility"}:
        score += 25 if payload.capital_available_minor is not None else 0
        score += 25 if payload.net_worth_minor is not None else 0
        score += 20 if payload.lawful_source_of_funds_confirmed else 0
    else:
        score += 20 if payload.net_worth_minor is not None else 0
        score += 20 if payload.lawful_source_of_funds_confirmed else 0
        score += 15 if payload.family_relocation else 0
    return min(100.0, score)


def create_advisory_assessment(
    session: Session, payload: BusinessAdvisoryCreate, *, actor: str
) -> BusinessMobilityAdvisoryAssessment:
    lead = session.get(Lead, payload.lead_id) if payload.lead_id else None
    if payload.lead_id and lead is None:
        raise ValueError("Lead not found")
    case = session.get(CorporateMobilityCase, payload.corporate_mobility_case_id) if payload.corporate_mobility_case_id else None
    if payload.corporate_mobility_case_id and case is None:
        raise ValueError("Corporate mobility case not found")
    if case and case.status == "closed":
        raise ValueError("Closed corporate mobility cases are immutable")
    if case and payload.lead_id and case.employee_lead_id and case.employee_lead_id != payload.lead_id:
        raise ValueError("Advisory lead must match the lead linked to the corporate mobility case")
    if payload.document_record_ids and lead is None:
        raise ValueError("A lead is required when controlled documents are supplied")

    documents: list[DocumentRecord] = []
    for document_id in payload.document_record_ids:
        document = session.get(DocumentRecord, document_id)
        if document is None:
            raise ValueError("Advisory document not found")
        if document.lead_id != payload.lead_id:
            raise ValueError("Advisory documents must belong to the selected lead")
        documents.append(document)

    pathways = _published_pathways(session, payload.target_countries)
    investment_programs = _published_investment_programs(session, payload.target_countries)
    narrative = " ".join([payload.situation, *payload.risk_disclosures]).lower()
    risk_flags: list[str] = []
    if any(signal in narrative for signal in PROHIBITED_SIGNALS):
        risk_flags.append("prohibited_conduct_signal")
    if any(signal in narrative for signal in SPECIALIST_SIGNALS):
        risk_flags.append("specialist_risk_disclosure")
    financial_intent = payload.primary_intent in {
        "passive_investment", "family_office_relocation", "tax_residency_planning", "asset_and_family_mobility",
    }
    if financial_intent and not payload.lawful_source_of_funds_confirmed:
        risk_flags.append("source_of_funds_unconfirmed")

    information_score = 45.0
    information_score += 10 if payload.timeline_months else 0
    information_score += 10 if payload.founder_experience_years is not None else 0
    information_score += 10 if payload.business_age_years is not None else 0
    information_score += 10 if payload.capital_available_minor is not None else 0
    information_score += 10 if payload.net_worth_minor is not None or payload.annual_revenue_minor is not None else 0
    information_score = min(100.0, information_score)
    evidence_score = min(100.0, len(documents) * 22.0 + sum(10.0 for item in documents if item.status == "verified"))
    if payload.lawful_source_of_funds_confirmed:
        evidence_score = min(100.0, evidence_score + 15.0)
    commercial_fit_score = _commercial_fit(payload)
    pathway_grounding_score = min(100.0, len(pathways) * 30.0 + len(investment_programs) * 25.0)
    if pathways and all(item["source_snapshot_id"] for item in pathways):
        pathway_grounding_score = min(100.0, pathway_grounding_score + 15.0)

    feasibility = (
        information_score * 0.25
        + evidence_score * 0.25
        + commercial_fit_score * 0.30
        + pathway_grounding_score * 0.20
    )
    feasibility -= 12.0 * len(risk_flags)
    if not pathways:
        feasibility = min(feasibility, 49.0)
    if "prohibited_conduct_signal" in risk_flags:
        feasibility = min(feasibility, 20.0)
    feasibility = round(max(0.0, min(100.0, feasibility)), 1)

    blockers: list[str] = []
    if not pathways:
        blockers.append("No published, source-controlled business or wealth pathway is available for the selected countries.")
    if not documents:
        blockers.append("No controlled client evidence is linked to the assessment.")
    if "source_of_funds_unconfirmed" in risk_flags:
        blockers.append("Lawful source of funds has not been confirmed for the financial mobility objective.")
    if "specialist_risk_disclosure" in risk_flags:
        blockers.append("The disclosed history requires licensed legal, tax, sanctions, or financial-crime review.")
    if "prohibited_conduct_signal" in risk_flags:
        blockers.append("The situation includes a concealment, deception, evasion, or circumvention signal that cannot be operationalized.")

    next_actions = [
        "Validate the commercial objective, controlling persons, family scope, timing, and target-country priorities with a human adviser.",
        "Collect identity, ownership, business-performance, capital, and lawful source-of-funds evidence in the controlled document workspace.",
    ]
    if not pathways:
        next_actions.append("Research and independently publish official-source business pathways before making a country-specific route recommendation.")
    if risk_flags:
        next_actions.append("Resolve disclosed legal, tax, sanctions, ownership, or source-of-funds issues with the appropriate licensed specialist.")

    options: list[dict[str, Any]] = []
    base_fit = commercial_fit_score
    for index, key in enumerate(INTENT_STRATEGIES[payload.primary_intent]):
        fit = round(max(0.0, min(100.0, base_fit - index * 9.0)), 1)
        relevant = [item for item in pathways if key.split("_")[0] in item["domain"].lower()]
        if not relevant:
            relevant = pathways[:3]
        relevant_programs = investment_programs[:3] if key in {
            "investor_residence", "active_business_investment", "asset_and_family_mobility", "family_office_mobility"
        } else []
        option_blockers = list(blockers)
        options.append({
            "strategy_key": key,
            "title": STRATEGY_TITLES[key],
            "fit_score": fit,
            "fit_band": _band(fit),
            "rationale": [
                f"Aligned to the declared intent: {payload.primary_intent.replace('_', ' ')}.",
                f"Commercial fact fit is {fit:.0f}/100 based on the supplied business and financial facts.",
            ],
            "blockers": option_blockers,
            "next_actions": next_actions[:3],
            "published_pathways": relevant,
            "verified_programs": relevant_programs,
            "verification_state": "published_program_grounded" if relevant_programs else (
                "published_pathway_grounded" if relevant else "archetype_only_requires_route_verification"
            ),
        })

    evidence_basis = [
        {"document_id": str(item.id), "document_type": item.document_type, "status": item.status}
        for item in documents
    ] + pathways + investment_programs
    dumped_input = payload.model_dump(mode="json")
    row = BusinessMobilityAdvisoryAssessment(
        lead_id=payload.lead_id,
        corporate_mobility_case_id=payload.corporate_mobility_case_id,
        primary_intent=payload.primary_intent,
        situation_text=payload.situation.strip(),
        input_json=_dump(dumped_input),
        feasibility_score=feasibility,
        feasibility_band=_band(feasibility),
        information_score=round(information_score, 1),
        evidence_score=round(evidence_score, 1),
        commercial_fit_score=round(commercial_fit_score, 1),
        pathway_grounding_score=round(pathway_grounding_score, 1),
        strategy_options_json=_dump(options),
        blockers_json=_dump(blockers),
        next_actions_json=_dump(next_actions),
        evidence_basis_json=_dump(evidence_basis),
        risk_flags_json=_dump(risk_flags),
        escalation_required=bool(risk_flags or not pathways or payload.primary_intent == "tax_residency_planning"),
        status="pending_review",
        human_review_required=True,
        generated_by=actor,
    )
    session.add(row)
    session.flush()
    record_audit(session, action="business_mobility_advisory_created", entity_type="business_mobility_advisory",
                 entity_id=row.id, after_state=row, actor=actor, source="business_mobility_advisory_v11_4")
    session.commit()
    session.refresh(row)
    return row


def review_advisory_assessment(
    session: Session,
    assessment: BusinessMobilityAdvisoryAssessment,
    payload: BusinessAdvisoryReviewCreate,
    *,
    actor: str,
) -> BusinessMobilityAdvisoryReview:
    if assessment.status != "pending_review":
        raise ValueError("Business mobility advisory is not pending review")
    if assessment.generated_by == actor:
        raise ValueError("Business mobility advisory requires a different reviewer")
    before = to_audit_dict(assessment)
    review = BusinessMobilityAdvisoryReview(
        assessment_id=assessment.id,
        decision=payload.decision,
        reason=payload.reason.strip(),
        reviewer=actor,
    )
    assessment.status = payload.decision
    assessment.reviewed_by = actor
    assessment.reviewed_at = datetime.now(timezone.utc)
    assessment.review_notes = payload.reason.strip()
    assessment.updated_at = datetime.now(timezone.utc)
    session.add(review)
    session.add(assessment)
    session.flush()
    record_audit(session, action="business_mobility_advisory_reviewed", entity_type="business_mobility_advisory",
                 entity_id=assessment.id, before_state=before, after_state=assessment,
                 reason=payload.reason.strip(), actor=actor, source="business_mobility_advisory_v11_4")
    session.commit()
    session.refresh(review)
    return review
