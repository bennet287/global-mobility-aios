from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    CountryPolicy,
    DocumentRecord,
    EligibilityAssessment,
    Lead,
    LeadIntent,
    Profile,
    VerifiedRule,
)


def _normalize(text: str | None) -> str | None:
    if not text:
        return None
    return text.strip().lower()


def _intent_domain(intent: LeadIntent | str | None) -> str:
    value = getattr(intent, "value", intent) if intent is not None else "unknown"
    value = (value or "unknown").lower()
    if value in {"study_abroad", "study", "student"}:
        return "study"
    if value in {"overseas_job", "work", "job", "employment"}:
        return "work"
    if value in {"visa", "permanent", "residency", "immigration"}:
        return "visa"
    return "general"


def _json_loads(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        data = json.loads(value)
        return data if isinstance(data, dict) else {"value": data}
    except Exception:
        return {"raw": value}


def _has_any(haystack: str | None, needles: set[str]) -> bool:
    if not haystack:
        return False
    lower = haystack.lower()
    return any(n in lower for n in needles)


def _document_types(documents: list[DocumentRecord]) -> set[str]:
    return {d.document_type.lower() for d in documents}


def _pathways(country: str | None, domain: str) -> list[str]:
    if not country:
        return ["Consultant will identify relevant pathways once target country is known."]

    key = f"{country.lower()}:{domain}"
    pathways: dict[str, list[str]] = {
        "germany:work": [
            "EU Blue Card (skilled employment with recognised qualification)",
            "Skilled Immigration Act (Fachkräfteeinwanderungsgesetz) pathway",
            "Job Seeker Visa (qualified professionals seeking employment)",
        ],
        "germany:study": [
            "German Student Visa (admission to a recognised institution)",
            "Student Applicant Visa (applying from within Germany)",
        ],
        "canada:work": [
            "Express Entry (FSW/CEC/FST skilled worker streams)",
            "Provincial Nominee Program (PNP)",
            "Employer-Specific or Open Work Permit",
        ],
        "canada:study": [
            "Study Permit (with DLI acceptance letter)",
            "Post-Graduation Work Permit (after eligible study)",
        ],
        "australia:work": [
            "Skilled Independent Visa (subclass 189)",
            "Skilled Nominated Visa (subclass 190)",
            "Employer Nomination Scheme (subclass 186)",
        ],
        "australia:study": [
            "Student Visa (subclass 500) with COE",
        ],
        "uk:work": [
            "Skilled Worker Visa (with eligible employer sponsor)",
            "Health and Care Worker Visa",
            "Global Talent Visa",
        ],
        "uk:study": [
            "Student Visa (formerly Tier 4)",
            "Graduate Visa (post-study work)",
        ],
        "usa:work": [
            "H-1B Specialty Occupation Visa",
            "Employment-Based Green Card (EB-2/EB-3)",
            "O-1 Extraordinary Ability Visa",
        ],
        "usa:study": [
            "F-1 Student Visa",
            "Optional Practical Training (post-completion)",
        ],
    }
    return pathways.get(key, [f"{domain.title()}-related {country.title()} pathways will be matched by a consultant."])


def _required_documents(domain: str) -> list[str]:
    base = ["Valid passport"]
    if domain == "work":
        base.extend([
            "CV / resume",
            "Degree or professional certificate",
            "Language test results or proof of language ability",
            "Proof of financial means (bank statements or salary proof)",
            "Employment contract or job offer (if available)",
        ])
    elif domain == "study":
        base.extend([
            "Academic transcripts and certificates",
            "Language test results",
            "Admission letter or Confirmation of Enrolment (COE)",
            "Proof of financial means for tuition and living costs",
            "Statement of purpose or motivation letter",
        ])
    elif domain == "visa":
        base.extend([
            "Financial proof",
            "Purpose of travel statement",
            "Accommodation or invitation letter",
            "Travel itinerary or return ticket evidence",
        ])
    else:
        base.extend([
            "CV / resume",
            "Relevant certificates",
            "Proof of financial means",
        ])
    return base


def _country_policy_notes(policy: CountryPolicy | None) -> list[str]:
    if policy is None:
        return ["No country policy on file; assessment uses generic rules."]
    data = _json_loads(policy.policy_json)
    notes: list[str] = []
    if data.get("verification_required"):
        notes.append("Country policy requires source verification before any claim is client-facing.")
    if data.get("human_review_required"):
        notes.append("Country policy mandates human review for this domain.")
    return notes or ["Country policy loaded; no additional generic notes."]


def _verified_rule_statements(rules: list[VerifiedRule]) -> list[str]:
    return [r.statement for r in rules if r.statement]


def evaluate_lead_eligibility(
    session: Session,
    lead_id: UUID,
    profile_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a deterministic eligibility assessment for a lead.

    The engine is intentionally rule-based so it works without an LLM on Windows.
    """
    lead = session.get(Lead, lead_id)
    if lead is None:
        raise ValueError(f"Lead {lead_id} not found")

    # Load latest profile if it exists and merge optional override data.
    profile_row = session.exec(
        select(Profile).where(Profile.lead_id == lead_id).order_by(Profile.updated_at.desc())
    ).first()
    profile: dict[str, Any] = _json_loads(profile_row.language_scores_json) if profile_row else {}
    if profile_row:
        profile.update({
            "highest_qualification": profile_row.highest_qualification,
            "field_of_study": profile_row.field_of_study,
            "desired_role": profile_row.desired_role,
            "years_experience": profile_row.years_experience,
            "budget_eur": profile_row.budget_eur,
            "current_country": profile_row.current_country,
            "target_country": profile_row.target_country,
            "skills": _json_loads(profile_row.skills_json).get("skills", []),
        })
    if profile_data:
        profile.update(profile_data)

    documents = session.exec(select(DocumentRecord).where(DocumentRecord.lead_id == lead_id)).all()
    doc_types = _document_types(list(documents))

    country = _normalize(lead.target_country or profile.get("target_country"))
    domain = _intent_domain(lead.intent)
    notes_lower = (lead.notes or "").lower()

    # Fetch country-specific data.
    policy = session.exec(
        select(CountryPolicy).where(
            CountryPolicy.country == (country or ""),
            CountryPolicy.domain == domain,
            CountryPolicy.status == "active",
        )
    ).first()
    rules = list(session.exec(
        select(VerifiedRule).where(
            VerifiedRule.country == (country or ""),
            VerifiedRule.domain == domain,
            VerifiedRule.active == True,
        )
    ).all())

    # Factors.
    years_experience = lead.notes and _extract_years_experience(lead.notes)
    if years_experience is None:
        years_experience = profile.get("years_experience")
    years_experience = float(years_experience) if years_experience is not None else 0.0

    has_qualification = bool(
        profile.get("highest_qualification")
        or "degree" in doc_types
        or "language_certificate" in doc_types
        or _has_any(lead.notes, {"degree", "bachelor", "master", "phd", "diploma", "certificate"})
    )
    has_language_scores = bool(
        profile.get("language_scores_json")
        or profile.get("language_score")
        or "language_certificate" in doc_types
        or _has_any(lead.notes, {"ielts", "toefl", "goethe", "telc", "testdaf", "pte", "language"})
    )
    budget_eur = profile.get("budget_eur")
    has_financial_proof = bool(
        budget_eur and budget_eur > 0
        or _has_any(lead.notes, {"budget", "savings", "bank", "financial", "fund"})
    )
    has_job_offer = bool(
        _has_any(lead.notes, {"job offer", "contract", "employer", "sponsor", "offer letter"})
    )
    has_passport = "passport" in doc_types

    # Scoring (max 1.0).
    score = 0.0
    confidence = 0.5

    target_country_present = bool(country)
    intent_known = getattr(lead.intent, "value", str(lead.intent)) != "unknown"

    if target_country_present and intent_known:
        score += 0.2
        confidence += 0.1

    if years_experience >= 5:
        score += 0.25
    elif years_experience >= 2:
        score += 0.15
    elif years_experience > 0:
        score += 0.05

    if has_qualification:
        score += 0.15
    if has_language_scores:
        score += 0.15
    if has_financial_proof:
        score += 0.15
    if has_job_offer:
        score += 0.1
    if has_passport:
        score += 0.05

    score = round(min(score, 1.0), 2)
    confidence = round(min(confidence, 1.0), 2)

    # Risks and status.
    risks: list[str] = []
    if not target_country_present:
        risks.append("Target country is missing; pathways cannot be narrowed.")
    if not intent_known:
        risks.append("Client goal/intent is unknown; required documents list is generic.")
    if years_experience < 1:
        risks.append("Limited documented work experience for employment-based pathways.")
    if not has_qualification:
        risks.append("No qualification or certificate information provided.")
    if not has_language_scores:
        risks.append("Language ability not documented; many pathways require proof.")
    if not has_financial_proof:
        risks.append("Financial proof missing; visa and study applications typically require it.")

    policy_notes = _country_policy_notes(policy)
    rule_statements = _verified_rule_statements(rules)
    if rule_statements:
        risks.extend([f"Verified rule: {s}" for s in rule_statements])

    if not target_country_present or not intent_known:
        status = "insufficient_profile"
    elif score >= 0.75:
        status = "eligible"
    elif score >= 0.55:
        status = "likely_eligible"
    elif score >= 0.35:
        status = "needs_documents"
    else:
        status = "ineligible"

    pathways = _pathways(country, domain)
    required_documents = _required_documents(domain)

    factors = {
        "target_country_present": target_country_present,
        "intent_known": intent_known,
        "years_experience": years_experience,
        "has_qualification": has_qualification,
        "has_language_scores": has_language_scores,
        "has_financial_proof": has_financial_proof,
        "has_job_offer": has_job_offer,
        "has_passport": has_passport,
        "document_types": sorted(doc_types),
        "policy_notes": policy_notes,
        "verified_rules_count": len(rules),
    }

    summary = (
        f"{status.replace('_', ' ').title()} assessment for {lead.full_name or 'lead'} "
        f"interested in {domain}-related options{f' in {country.title()}' if country else ''}. "
        f"Overall score {score} based on profile factors and uploaded documents."
    )

    return {
        "target_country": country,
        "domain": domain,
        "overall_score": score,
        "confidence": confidence,
        "status": status,
        "summary": summary,
        "risks": risks,
        "required_documents": required_documents,
        "pathways": pathways,
        "factors": factors,
        "policy_notes": policy_notes,
    }


def _extract_years_experience(text: str) -> float | None:
    import re
    match = re.search(r"(\d+)\+?\s*years?\s+(?:of\s+)?experience", text, re.IGNORECASE)
    if match:
        return float(match.group(1))
    return None


def persist_eligibility_assessment(
    session: Session,
    lead_id: UUID,
    agent_run_id: UUID | None,
    result: dict[str, Any],
) -> EligibilityAssessment:
    assessment = EligibilityAssessment(
        lead_id=lead_id,
        agent_run_id=agent_run_id,
        target_country=result.get("target_country"),
        domain=result.get("domain", "general"),
        overall_score=result.get("overall_score", 0.0),
        confidence=result.get("confidence", 0.0),
        status=result.get("status", "insufficient_profile"),
        summary=result.get("summary"),
        assessment_json=json.dumps({"factors": result.get("factors", {}), "policy_notes": result.get("policy_notes", [])}, default=str, sort_keys=True),
        risks_json=json.dumps(result.get("risks", []), default=str, sort_keys=True),
        required_documents_json=json.dumps(result.get("required_documents", []), default=str, sort_keys=True),
        pathways_json=json.dumps(result.get("pathways", []), default=str, sort_keys=True),
    )
    session.add(assessment)
    session.commit()
    session.refresh(assessment)
    return assessment
