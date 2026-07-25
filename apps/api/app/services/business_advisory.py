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
    BusinessAdvisorySituationRequest,
    BusinessAdvisorySolutionResponse,
    BusinessStrategyOption,
    SolutionRecommendation,
)
from app.services.audit_log import record_audit, to_audit_dict
from app.services.llm_client import LLMProviderError, LLMProviderFactory, is_llm_enabled


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

    next_actions = list(_SITUATION_ACTIONS.get(payload.primary_intent, _SITUATION_ACTIONS["launch_startup"])[:2])
    next_actions.append(
        "Validate the commercial objective, controlling persons, family scope, timing, and target-country priorities with a human adviser."
    )
    if not pathways:
        next_actions.append("Research and independently publish official-source business pathways before making a country-specific route recommendation.")
    if risk_flags:
        next_actions.append("Resolve disclosed legal, tax, sanctions, ownership, or source-of-funds issues with the appropriate licensed specialist.")

    options: list[dict[str, Any]] = []
    intent_actions = _SITUATION_ACTIONS.get(payload.primary_intent, _SITUATION_ACTIONS["launch_startup"])
    for index, key in enumerate(INTENT_STRATEGIES[payload.primary_intent]):
        fit = _strategy_fit_score(key, payload, pathways, investment_programs, commercial_fit_score)
        fit = round(max(0.0, min(100.0, fit - index * 6.0)), 1)
        if "prohibited_conduct_signal" in risk_flags:
            fit = min(fit, 20.0)
        relevant = [item for item in pathways if key.split("_")[0] in item["domain"].lower()]
        if not relevant:
            relevant = pathways[:3]
        relevant_programs = investment_programs[:3] if key in {
            "investor_residence", "active_business_investment", "asset_and_family_mobility", "family_office_mobility"
        } else []
        option_blockers = list(blockers)

        rationale = [
            f"{STRATEGY_TITLES[key]} fits the '{payload.primary_intent.replace('_', ' ')}' intent.",
            f"Situation-aware fit is {fit:.0f}/100 based on disclosed facts, target countries ({', '.join(payload.target_countries)}), and available routes.",
        ]
        if relevant:
            rationale.append(f"Grounded in {len(relevant)} published pathway(s) for this archetype.")
        elif pathways:
            rationale.append("No directly matching published pathway is available; using the closest published routes for reference.")
        else:
            rationale.append("No published, source-controlled pathway is available yet for the selected countries.")

        options.append({
            "strategy_key": key,
            "title": STRATEGY_TITLES[key],
            "fit_score": fit,
            "fit_band": _band(fit),
            "rationale": rationale,
            "blockers": option_blockers,
            "next_actions": intent_actions[:3],
            "published_pathways": relevant,
            "verified_programs": relevant_programs,
            "verification_state": "published_program_grounded" if relevant_programs else (
                "published_pathway_grounded" if relevant else "archetype_only_requires_route_verification"
            ),
        })

    # Re-sort so the strongest option is first, then preserve original order for ties.
    options.sort(key=lambda option: (-option["fit_score"], INTENT_STRATEGIES[payload.primary_intent].index(option["strategy_key"])))

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


SOLUTION_DISCLAIMER = (
    "This recommendation is decision-support guidance for business and wealth mobility planning. "
    "It is not a legal, tax, or immigration opinion, and it does not guarantee authority outcomes. "
    "Execution requires licensed advisers and independently verified official sources; "
    "risky or complex situations must be reviewed by the appropriate specialist before any action."
)


SUCCESS_BANDS = [
    (80, "highly_favourable"),
    (60, "favourable"),
    (40, "conditional"),
    (20, "challenging"),
    (0, "not_viable"),
]


def _solution_band(score: float) -> str:
    for threshold, band in SUCCESS_BANDS:
        if score >= threshold:
            return band
    return "not_viable"


def _situation_risk_flags(payload: BusinessAdvisorySituationRequest) -> list[str]:
    narrative = " ".join([payload.situation, *payload.risk_disclosures]).lower()
    flags: list[str] = []
    if any(signal in narrative for signal in PROHIBITED_SIGNALS):
        flags.append("prohibited_conduct_signal")
    if any(signal in narrative for signal in SPECIALIST_SIGNALS):
        flags.append("specialist_risk_disclosure")
    if payload.primary_intent in {
        "passive_investment", "family_office_relocation", "tax_residency_planning", "asset_and_family_mobility",
    } and not payload.lawful_source_of_funds_confirmed:
        flags.append("source_of_funds_unconfirmed")
    return flags


def _situation_aware_score(
    payload: BusinessAdvisorySituationRequest,
    pathways: list[dict[str, Any]],
    programs: list[dict[str, Any]],
    risk_flags: list[str],
) -> float:
    """Compute a success meter that reflects facts, pathways, timeline, and disclosed risks."""
    base = _commercial_fit_from_situation(payload)
    pathway_boost = min(35.0, len(pathways) * 10.0 + len(programs) * 8.0)
    if pathways and all(item.get("source_snapshot_id") for item in pathways):
        pathway_boost += 10.0

    timeline_factor = 0.0
    if payload.timeline_months:
        # Tighter timelines reduce the score unless capital is already available.
        if payload.timeline_months <= 6:
            timeline_factor = -10.0
        elif payload.timeline_months <= 12:
            timeline_factor = -5.0
        else:
            timeline_factor = 5.0
    if payload.capital_available_minor:
        timeline_factor += 5.0

    risk_penalty = 12.0 * len(risk_flags)
    if "prohibited_conduct_signal" in risk_flags:
        risk_penalty += 15.0

    score = base * 0.55 + pathway_boost * 0.35 + timeline_factor * 0.10 - risk_penalty
    score = max(0.0, min(100.0, score))
    if not pathways:
        score = min(score, 45.0)
    if "prohibited_conduct_signal" in risk_flags:
        score = min(score, 20.0)
    return round(score, 1)


_SITUATION_ACTIONS = {
    "launch_startup": [
        "Incorporate the target-country vehicle and prepare a founder-investor narrative.",
        "Draft a 12-24 month operating plan that shows local substance (office, hires, revenue).",
        "Collect proof of capital, founder track record, and lawful source-of-funds documents.",
    ],
    "expand_existing_business": [
        "Prepare audited/reviewed financials and an org chart showing the expansion rationale.",
        "Identify the transfer mechanism (intra-company assignment, local hire, branch).",
        "Map the target-country corporate, VAT, payroll, and immigration registration sequence.",
    ],
    "founder_relocation": [
        "Confirm personal and corporate residency requirements for the founder and family.",
        "Structure the move so the company continues to trade or raises in the new jurisdiction.",
        "Obtain tax, immigration, and school/housing clearances before the relocation date.",
    ],
    "passive_investment": [
        "Match available capital to the minimum commitment of a published residence/citizenship program.",
        "Obtain a source-of-funds audit and a clean criminal-record certificate.",
        "Appoint a licensed local adviser and escrow agent before any capital transfer.",
    ],
    "family_office_relocation": [
        "Catalogue the family balance sheet, asset locations, and existing tax residencies.",
        "Select a jurisdiction that fits the family's investment, governance, and schooling needs.",
        "Build a family-constitution draft and engage a multi-jurisdiction tax/estate team.",
    ],
    "tax_residency_planning": [
        "Document current tax residency triggers and any treaty tie-breaker positions.",
        "Model the 183-day, permanent home, centre of vital interests, and habitual abode tests.",
        "Implement a substance plan (home, office, board meetings, banking) before year-end.",
    ],
    "asset_and_family_mobility": [
        "Map assets by jurisdiction, ownership structure, and portability.",
        "Prepare custody, schooling, healthcare, and residence permits for family members.",
        "Align the asset-protection and succession plan with the new residency structure.",
    ],
}


_SITUATION_CRITICAL_FACTORS = {
    "launch_startup": [
        "Founder experience and capital availability in the target jurisdiction.",
        "Published startup, entrepreneur, or innovation pathway for the country.",
        "Local substance plan that satisfies authority review.",
    ],
    "expand_existing_business": [
        "Trading history, revenue, and staffing that justify the expansion.",
        "Corporate and transfer mechanism matched to a published pathway.",
        "Local payroll, tax, and immigration registration readiness.",
    ],
    "founder_relocation": [
        "Personal and corporate residency alignment.",
        "Continuity of the company's operations and funding post-move.",
        "Family relocation logistics and timelines.",
    ],
    "passive_investment": [
        "Capital amount versus published program minimums.",
        "Clean source-of-funds evidence and criminal-record status.",
        "Licensed local adviser and escrow arrangement.",
    ],
    "family_office_relocation": [
        "Complexity of the family balance sheet and asset locations.",
        "Jurisdiction fit for investment, governance, schooling, and lifestyle.",
        "Multi-jurisdiction tax and estate planning readiness.",
    ],
    "tax_residency_planning": [
        "Current tax-residency triggers and treaty positions.",
        "Substance evidence across the 183-day, home, interests, and abode tests.",
        "Timing relative to the tax year and reporting deadlines.",
    ],
    "asset_and_family_mobility": [
        "Asset portability and ownership-structure complexity.",
        "Family-member residence, custody, and schooling requirements.",
        "Alignment of asset protection with the new residency plan.",
    ],
}


def _strategy_fit_score(
    strategy_key: str,
    payload: BusinessAdvisorySituationRequest,
    pathways: list[dict[str, Any]],
    programs: list[dict[str, Any]],
    base_score: float,
) -> float:
    """Adjust the base score for how well a given strategy matches the situation."""
    score = base_score
    relevant = [p for p in pathways if strategy_key.split("_")[0] in p["domain"].lower()]
    if relevant:
        score += 8.0
    if strategy_key in {
        "investor_residence", "active_business_investment", "asset_and_family_mobility", "family_office_mobility"
    } and programs:
        score += 8.0
    if payload.primary_intent == "launch_startup" and strategy_key in {"founder_startup", "entrepreneur_operating_business"}:
        score += 10.0
    if payload.primary_intent == "expand_existing_business" and strategy_key in {"company_expansion", "intra_company_transfer"}:
        score += 10.0
    if payload.primary_intent == "passive_investment" and strategy_key in {"investor_residence", "active_business_investment"}:
        score += 10.0
    if payload.primary_intent == "family_office_relocation" and strategy_key in {"family_office_mobility", "investor_residence"}:
        score += 10.0
    if payload.primary_intent == "tax_residency_planning" and strategy_key in {"tax_residency_specialist", "operating_business_substance"}:
        score += 10.0
    if payload.primary_intent == "asset_and_family_mobility" and strategy_key in {"asset_and_family_mobility", "family_office_mobility"}:
        score += 10.0
    if payload.primary_intent == "founder_relocation" and strategy_key in {"founder_startup", "intra_company_transfer"}:
        score += 10.0
    return round(max(0.0, min(100.0, score)), 1)


def _build_solution_prompt(
    payload: BusinessAdvisorySituationRequest,
    pathways: list[dict[str, Any]],
    programs: list[dict[str, Any]],
    risk_flags: list[str],
) -> str:
    financials = []
    if payload.capital_available_minor is not None:
        financials.append(f"capital available: {payload.capital_available_minor} {payload.currency}")
    if payload.net_worth_minor is not None:
        financials.append(f"net worth: {payload.net_worth_minor} {payload.currency}")
    if payload.annual_revenue_minor is not None:
        financials.append(f"annual revenue: {payload.annual_revenue_minor} {payload.currency}")

    grounding = {
        "pathways": pathways,
        "programs": programs,
        "risk_flags": risk_flags,
    }

    risk_guidance = ""
    if risk_flags:
        risk_guidance = (
            "\nDisclosed risk flags: " + ", ".join(risk_flags) + ". "
            "Do not ignore these flags. Recommend the strongest LAWFUL alternative, "
            "explain exactly how to remediate or compartmentalize the issue, and "
            "name the specialist (legal, tax, sanctions, immigration, or financial-crime) "
            "who must review before execution. You may describe aggressive-but-lawful planning; "
            "you must not provide instructions for forgery, fraud, tax evasion, sanctions evasion, "
            "or nominee concealment.\n"
        )

    return (
        "You are a senior, commercially oriented business and wealth mobility strategist. "
        "Your client is a business owner, founder, investor, HNWI, or family-office principal. "
        "Analyze the situation and recommend the strongest, most practical lawful mobility solution. "
        "Be specific: tie the recommendation to the disclosed facts, target countries, capital, "
        "timeline, family scope, and published pathways/programs. Do not be generic.\n\n"
        "Primary intent: " + payload.primary_intent.replace("_", " ") + "\n"
        "Target countries: " + ", ".join(payload.target_countries) + "\n"
        "Situation: " + payload.situation + "\n"
        + ("Financials: " + "; ".join(financials) + "\n" if financials else "")
        + ("Timeline: " + str(payload.timeline_months) + " months\n" if payload.timeline_months else "")
        + ("Family relocation: yes\n" if payload.family_relocation else "")
        + risk_guidance
        + "\nPublished grounding data (do not invent programs not listed):\n"
        + json.dumps(grounding, default=str, indent=2)
        + "\n\nReturn ONLY a JSON object matching this schema (no markdown):\n"
        "{\n"
        '  "summary": "2-3 sentence strategic summary that sounds like advice from a senior strategist",\n'
        '  "recommended_solution": {\n'
        '    "strategy_key": "one of: founder_startup, entrepreneur_operating_business, company_expansion, intra_company_transfer, investor_residence, active_business_investment, asset_and_family_mobility, family_office_mobility, tax_residency_specialist, operating_business_substance",\n'
        '    "title": "short, commercially crisp title",\n'
        '    "success_meter": 0-100 integer,\n'
        '    "rationale": "why this exact route fits the client\'s situation and intention",\n'
        '    "actions": ["concrete next step 1", "step 2", "step 3"],\n'
        '    "estimated_timeline_months": integer or null,\n'
        '    "estimated_commitment": {"amount_minor": integer, "currency": "3-letter code"} or null,\n'
        '    "risk_notes": ["specific risk 1", "specific risk 2"]\n'
        '  },\n'
        '  "alternative_options": [\n'
        '    { same shape as recommended_solution, at least 1 and at most 2 alternatives, each weaker or higher-risk than the primary }\n'
        '  ],\n'
        '  "critical_factors": ["factor that will make or break the primary recommendation", "factor 2", "factor 3"],\n'
        '  "overall_success_meter": 0-100 integer\n'
        "}"
    )


def _fallback_solution(
    payload: BusinessAdvisorySituationRequest,
    pathways: list[dict[str, Any]],
    programs: list[dict[str, Any]],
    risk_flags: list[str],
) -> BusinessAdvisorySolutionResponse:
    overall = _situation_aware_score(payload, pathways, programs, risk_flags)
    strategy_keys = INTENT_STRATEGIES[payload.primary_intent]
    base_score = _commercial_fit_from_situation(payload)

    options: list[SolutionRecommendation] = []
    for index, key in enumerate(strategy_keys[:3]):
        score = _strategy_fit_score(key, payload, pathways, programs, base_score)
        # Rank alternatives lower than the primary by a modest margin.
        score = round(max(0.0, min(100.0, score - index * 6.0)), 1)
        if "prohibited_conduct_signal" in risk_flags:
            score = min(score, 20.0)
        relevant = [item for item in pathways if key.split("_")[0] in item["domain"].lower()]
        if not relevant:
            relevant = pathways[:3]
        relevant_programs = programs[:2] if key in {
            "investor_residence", "active_business_investment", "asset_and_family_mobility", "family_office_mobility",
        } else []

        if risk_flags:
            risk_notes = [
                "Disclosed risk flags require licensed specialist review before execution.",
                "Remediation may include source-of-funds documentation, sanctions/PEP clearance, or lawful restructuring.",
            ]
        else:
            risk_notes = ["Requires licensed review and independently verified official sources before execution."]

        options.append(SolutionRecommendation(
            strategy_key=key,
            title=STRATEGY_TITLES[key],
            success_meter=score,
            success_band=_solution_band(score),
            rationale=(
                f"{STRATEGY_TITLES[key]} is matched to the '{payload.primary_intent.replace('_', ' ')}' intent. "
                f"Given the disclosed facts and target countries ({', '.join(payload.target_countries)}), "
                f"the situation-aware success meter is {score:.0f}/100."
            ),
            actions=_SITUATION_ACTIONS.get(payload.primary_intent, _SITUATION_ACTIONS["launch_startup"])[:3],
            estimated_timeline_months=payload.timeline_months,
            estimated_commitment={"amount_minor": payload.capital_available_minor or 0, "currency": payload.currency or "EUR"} if payload.capital_available_minor else None,
            grounding_pathways=relevant,
            grounding_programs=relevant_programs,
            risk_notes=risk_notes,
        ))

    # Re-sort so the highest-scoring option is recommended, not just the first archetype.
    options.sort(key=lambda option: option.success_meter, reverse=True)

    return BusinessAdvisorySolutionResponse(
        summary=(
            f"For the '{payload.primary_intent.replace('_', ' ')}' goal in {', '.join(payload.target_countries)}, "
            f"the strongest route is {options[0].title} with a situation-aware success meter of {options[0].success_meter:.0f}/100 "
            f"(overall {overall:.0f}/100)."
        ),
        recommended_solution=options[0],
        alternative_options=options[1:],
        critical_factors=_SITUATION_CRITICAL_FACTORS.get(
            payload.primary_intent,
            [
                "Availability of a published, source-controlled pathway for the target country.",
                "Verified capital, ownership, and source-of-funds evidence.",
                "Engagement of licensed legal, tax, and immigration advisers in the target jurisdiction.",
            ],
        ),
        overall_success_meter=overall,
        risk_flags=risk_flags,
        disclaimer=SOLUTION_DISCLAIMER,
        human_review_required=bool(risk_flags or not pathways or overall < 60),
    )


def _commercial_fit_from_situation(payload: BusinessAdvisorySituationRequest) -> float:
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


def advise_on_business_mobility_situation(
    session: Session,
    payload: BusinessAdvisorySituationRequest,
    *,
    actor: str,
) -> BusinessAdvisorySolutionResponse:
    pathways = _published_pathways(session, payload.target_countries)
    programs = _published_investment_programs(session, payload.target_countries)
    risk_flags = _situation_risk_flags(payload)

    if not is_llm_enabled():
        return _fallback_solution(payload, pathways, programs, risk_flags)

    try:
        provider = LLMProviderFactory.get_provider()
        prompt = _build_solution_prompt(payload, pathways, programs, risk_flags)
        response = provider.complete(
            system_prompt=prompt,
            messages=[{"role": "user", "content": "Provide the structured recommendation."}],
            response_format={"type": "json_object"},
        )
        data = json.loads(response.content)
        recommended = SolutionRecommendation(
            strategy_key=data["recommended_solution"]["strategy_key"],
            title=data["recommended_solution"]["title"],
            success_meter=max(0.0, min(100.0, float(data["recommended_solution"]["success_meter"]))),
            success_band=_solution_band(float(data["recommended_solution"]["success_meter"])),
            rationale=data["recommended_solution"]["rationale"],
            actions=data["recommended_solution"]["actions"],
            estimated_timeline_months=data["recommended_solution"].get("estimated_timeline_months"),
            estimated_commitment=data["recommended_solution"].get("estimated_commitment"),
            grounding_pathways=pathways[:3],
            grounding_programs=programs[:2],
            risk_notes=data["recommended_solution"].get("risk_notes", []),
        )
        alternatives = [
            SolutionRecommendation(
                strategy_key=item["strategy_key"],
                title=item["title"],
                success_meter=max(0.0, min(100.0, float(item["success_meter"]))),
                success_band=_solution_band(float(item["success_meter"])),
                rationale=item["rationale"],
                actions=item["actions"],
                estimated_timeline_months=item.get("estimated_timeline_months"),
                estimated_commitment=item.get("estimated_commitment"),
                grounding_pathways=pathways[:3],
                grounding_programs=programs[:2],
                risk_notes=item.get("risk_notes", []),
            )
            for item in data.get("alternative_options", [])[:2]
        ]
        overall = max(0.0, min(100.0, float(data.get("overall_success_meter", recommended.success_meter))))
        if not pathways:
            overall = min(overall, 45.0)
        if "prohibited_conduct_signal" in risk_flags:
            overall = min(overall, 20.0)
        return BusinessAdvisorySolutionResponse(
            summary=data.get("summary", recommended.rationale),
            recommended_solution=recommended,
            alternative_options=alternatives,
            critical_factors=data.get("critical_factors", []),
            overall_success_meter=overall,
            risk_flags=risk_flags,
            disclaimer=SOLUTION_DISCLAIMER,
            human_review_required=bool(risk_flags or not pathways or overall < 60),
        )
    except (LLMProviderError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        return _fallback_solution(payload, pathways, programs, risk_flags)
