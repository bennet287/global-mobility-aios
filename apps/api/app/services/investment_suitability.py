from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlmodel import Session, select

from app.models.domain import (
    BusinessMobilityAdvisoryAssessment,
    DocumentRecord,
    InvestmentMobilityProgram,
    InvestmentMobilityProgramVersion,
    InvestmentMobilitySuitabilityAssessment,
    InvestmentMobilitySuitabilityReview,
    Lead,
)
from app.schemas_investment_suitability import (
    InvestmentProgramSuitabilityResult,
    InvestmentSuitabilityCreate,
    InvestmentSuitabilityRead,
    InvestmentSuitabilityReviewCreate,
)
from app.services.audit_log import record_audit, to_audit_dict


SCORE_SEMANTICS = (
    "Mobility-route readiness from disclosed capital, controlled evidence, family scope, risk constraints, "
    "and independently published program versions; not investment advice, eligibility, approval probability, "
    "return forecast, tax opinion, or capital-safety guarantee."
)

PROHIBITED_SIGNALS = {
    "hide ownership", "conceal funds", "nominee owner", "fake document", "forge", "backdate",
    "evade tax", "avoid sanctions", "bypass sanctions", "sham company", "misrepresent",
}


def _dump(value: Any) -> str:
    return json.dumps(value, default=str, sort_keys=True, separators=(",", ":"))


def _load(value: str | None, default: Any) -> Any:
    try:
        return json.loads(value) if value else default
    except (TypeError, ValueError):
        return default


def _band(score: float) -> str:
    if score >= 75: return "strong_readiness"
    if score >= 55: return "workable_with_actions"
    if score >= 35: return "material_gaps"
    return "not_ready"


def suitability_read(row: InvestmentMobilitySuitabilityAssessment) -> InvestmentSuitabilityRead:
    return InvestmentSuitabilityRead(
        **row.model_dump(),
        candidate_program_version_ids=_load(row.candidate_program_version_ids_json, []),
        ranked_programs=[InvestmentProgramSuitabilityResult.model_validate(item) for item in _load(row.ranked_programs_json, [])],
        blockers=_load(row.blockers_json, []),
        next_actions=_load(row.next_actions_json, []),
        evidence_basis=_load(row.evidence_basis_json, []),
        score_semantics=SCORE_SEMANTICS,
    )


def _candidate_programs(session: Session, payload: InvestmentSuitabilityCreate):
    countries = {item.strip().lower() for item in payload.target_countries}
    selected_ids = set(payload.program_ids)
    programs = session.exec(select(InvestmentMobilityProgram).where(
        InvestmentMobilityProgram.catalogue_status == "active"
    )).all()
    candidates = []
    for program in programs:
        if selected_ids and program.id not in selected_ids:
            continue
        if not selected_ids and countries and program.country.strip().lower() not in countries:
            continue
        version = session.exec(select(InvestmentMobilityProgramVersion).where(
            InvestmentMobilityProgramVersion.program_id == program.id,
            InvestmentMobilityProgramVersion.lifecycle_status == "published",
        ).order_by(InvestmentMobilityProgramVersion.version_number.desc())).first()
        if version:
            candidates.append((program, version))
    return candidates


def create_suitability_assessment(
    session: Session, payload: InvestmentSuitabilityCreate, *, actor: str,
) -> InvestmentMobilitySuitabilityAssessment:
    lead = session.get(Lead, payload.lead_id)
    if lead is None:
        raise ValueError("Lead not found")
    advisory = session.get(BusinessMobilityAdvisoryAssessment, payload.business_advisory_assessment_id) if payload.business_advisory_assessment_id else None
    if payload.business_advisory_assessment_id and advisory is None:
        raise ValueError("Business mobility advisory not found")
    if advisory and advisory.lead_id != lead.id:
        raise ValueError("Business mobility advisory must belong to the selected lead")

    documents: list[DocumentRecord] = []
    for document_id in payload.document_record_ids:
        document = session.get(DocumentRecord, document_id)
        if document is None:
            raise ValueError("Suitability evidence document not found")
        if document.lead_id != lead.id:
            raise ValueError("Suitability evidence documents must belong to the selected lead")
        documents.append(document)

    candidates = _candidate_programs(session, payload)
    if not candidates:
        raise ValueError("No independently published investment programs match the selection")
    narrative = " ".join(payload.disclosed_constraints).lower()
    prohibited = any(signal in narrative for signal in PROHIBITED_SIGNALS)
    verified_documents = sum(1 for document in documents if document.status == "verified")
    evidence_score = min(100.0, len(documents) * 12.0 + verified_documents * 13.0 + (25.0 if payload.lawful_source_of_funds_confirmed else 0.0))

    results: list[dict[str, Any]] = []
    global_blockers: list[str] = []
    for program, version in candidates:
        findings: list[str] = []
        blockers: list[str] = []
        actions: list[str] = []
        if version.currency == payload.currency:
            ratio = payload.available_capital_minor / max(1, version.minimum_commitment_minor)
            capital_score = min(100.0, ratio * 100.0)
            if ratio >= 1:
                findings.append("Declared available capital covers the recorded minimum commitment.")
            else:
                shortfall = version.minimum_commitment_minor - payload.available_capital_minor
                blockers.append(f"Declared capital is below the recorded minimum by {shortfall} {version.currency} minor units.")
        else:
            capital_score = 15.0
            blockers.append("Capital and program currencies differ; no unverified exchange-rate conversion was applied.")
            actions.append("Obtain a dated, reviewable currency conversion and liquidity confirmation.")

        family_scope = _load(version.family_scope_json, [])
        family_score = 100.0 if payload.family_members == 1 else (85.0 if family_scope else 30.0)
        if payload.family_members > 1 and not family_scope:
            blockers.append("The published program version does not record dependant coverage.")
        risks = _load(version.risks_json, [])
        risk_score = {"conservative": 62.0, "balanced": 78.0, "growth": 86.0}[payload.risk_tolerance]
        if payload.capital_preservation_required:
            risk_score = min(risk_score, 35.0)
            blockers.append("Capital preservation is required, while the program records capital-at-risk considerations.")
        if not payload.lawful_source_of_funds_confirmed:
            blockers.append("Lawful source of funds is not yet confirmed with controlled evidence.")
            actions.append("Complete source-of-funds and source-of-wealth verification before route selection.")
        if not documents:
            blockers.append("No controlled client evidence is linked to this comparison.")
            actions.append("Link identity, wealth, liquidity, ownership, and source-of-funds evidence.")
        if prohibited:
            blockers.append("A concealment, deception, evasion, or circumvention signal prevents this route from being operationalized.")

        score = capital_score * .4 + evidence_score * .25 + family_score * .15 + risk_score * .2
        if prohibited: score = min(score, 20.0)
        score = round(max(0.0, min(100.0, score)), 1)
        actions.extend([
            "Have a licensed adviser re-verify current program conditions and client-specific admissibility.",
            "Complete regulated investment suitability, tax, banking, sanctions, and legal reviews before committing capital.",
        ])
        results.append(InvestmentProgramSuitabilityResult(
            program_id=program.id, program_version_id=version.id, name=program.name, country=program.country,
            program_type=program.program_type, minimum_commitment_minor=version.minimum_commitment_minor,
            currency=version.currency, readiness_score=score, readiness_band=_band(score),
            capital_coverage_score=round(capital_score, 1), evidence_score=round(evidence_score, 1),
            family_fit_score=round(family_score, 1), risk_alignment_score=round(risk_score, 1),
            findings=findings, blockers=blockers, next_actions=list(dict.fromkeys(actions)),
            official_source_id=version.official_source_id, source_snapshot_id=version.source_snapshot_id,
            pathway_version_id=version.pathway_version_id,
        ).model_dump(mode="json"))
        global_blockers.extend(blockers)

    results.sort(key=lambda item: item["readiness_score"], reverse=True)
    overall = round(results[0]["readiness_score"], 1)
    next_actions = list(dict.fromkeys(action for item in results[:3] for action in item["next_actions"]))
    evidence_basis = [{"document_id": str(doc.id), "document_type": doc.document_type, "status": doc.status} for doc in documents]
    evidence_basis += [{"program_version_id": item["program_version_id"], "source_snapshot_id": item["source_snapshot_id"]} for item in results]
    row = InvestmentMobilitySuitabilityAssessment(
        lead_id=lead.id, business_advisory_assessment_id=payload.business_advisory_assessment_id,
        input_json=_dump(payload.model_dump(mode="json")),
        candidate_program_version_ids_json=_dump([item["program_version_id"] for item in results]),
        ranked_programs_json=_dump(results), blockers_json=_dump(list(dict.fromkeys(global_blockers))),
        next_actions_json=_dump(next_actions), evidence_basis_json=_dump(evidence_basis),
        overall_readiness_score=overall, readiness_band=_band(overall), status="pending_review",
        human_review_required=True, generated_by=actor,
    )
    session.add(row); session.flush()
    record_audit(session, action="investment_mobility_suitability_created", entity_type="investment_mobility_suitability",
                 entity_id=row.id, after_state=row, actor=actor, source="investment_suitability_v11_6")
    session.commit(); session.refresh(row)
    return row


def review_suitability_assessment(
    session: Session, assessment: InvestmentMobilitySuitabilityAssessment,
    payload: InvestmentSuitabilityReviewCreate, *, actor: str,
) -> InvestmentMobilitySuitabilityReview:
    if assessment.status != "pending_review":
        raise ValueError("Investment mobility suitability assessment is not pending review")
    if assessment.generated_by == actor:
        raise ValueError("Investment mobility suitability assessment requires a different reviewer")
    before = to_audit_dict(assessment)
    now = datetime.now(timezone.utc)
    review = InvestmentMobilitySuitabilityReview(
        assessment_id=assessment.id, decision=payload.decision, reason=payload.reason.strip(), reviewer=actor,
    )
    assessment.status = payload.decision
    assessment.reviewed_by = actor
    assessment.reviewed_at = now
    assessment.review_notes = payload.reason.strip()
    assessment.updated_at = now
    session.add(review); session.add(assessment); session.flush()
    record_audit(session, action="investment_mobility_suitability_reviewed", entity_type="investment_mobility_suitability",
                 entity_id=assessment.id, before_state=before, after_state=assessment, reason=payload.reason.strip(),
                 actor=actor, source="investment_suitability_v11_6")
    session.commit(); session.refresh(review)
    return review
