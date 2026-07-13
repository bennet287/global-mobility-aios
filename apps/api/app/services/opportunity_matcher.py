from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import Lead, Opportunity, Profile


def _json_loads(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        data = json.loads(value)
        return data if isinstance(data, dict) else {"value": data}
    except Exception:
        return {"raw": value}


def _load_tags(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        data = json.loads(value)
        return [str(t).lower() for t in data if t] if isinstance(data, list) else []
    except Exception:
        return []


def _normalize(text: str | None) -> str:
    return (text or "").lower().strip()


def _overlap_score(needles: set[str], haystack: set[str]) -> float:
    if not needles or not haystack:
        return 0.0
    intersection = needles & haystack
    return len(intersection) / max(len(needles), 1)


def _extract_years_experience(text: str | None) -> float | None:
    import re
    if not text:
        return None
    match = re.search(r"(\d+)\+?\s*years?\s+(?:of\s+)?experience", text, re.IGNORECASE)
    if match:
        return float(match.group(1))
    return None


def match_opportunities_for_lead(
    session: Session,
    lead_id: UUID,
    limit: int = 10,
) -> dict[str, Any]:
    lead = session.get(Lead, lead_id)
    if lead is None:
        raise ValueError(f"Lead {lead_id} not found")

    profile = session.exec(
        select(Profile).where(Profile.lead_id == lead_id).order_by(Profile.updated_at.desc())
    ).first()

    opportunities = list(session.exec(
        select(Opportunity).where(Opportunity.active == True)
    ).all())

    lead_country = _normalize(lead.target_country)
    lead_intent = _normalize(getattr(lead.intent, "value", lead.intent))
    lead_notes = _normalize(lead.notes)
    profession = _normalize(profile.desired_role if profile else None)
    field = _normalize(profile.field_of_study if profile else None)
    years_exp = profile.years_experience if profile and profile.years_experience else _extract_years_experience(lead.notes)
    budget = profile.budget_eur if profile and profile.budget_eur else None

    # Expand profession/field from notes if not in profile.
    if not profession:
        profession = lead_notes
    if not field:
        field = lead_notes

    matches: list[dict[str, Any]] = []
    for opp in opportunities:
        score = 0.0
        reasons: list[str] = []
        risks: list[str] = []

        # Country match (strong signal).
        opp_country = _normalize(opp.country)
        if lead_country and opp_country == lead_country:
            score += 0.35
            reasons.append(f"Target country matches {opp.country.title()}")
        elif lead_country:
            risks.append(f"Opportunity is in {opp.country.title()}, not {lead.target_country.title()}")
        else:
            risks.append("Lead target country unknown")

        # Domain / intent alignment.
        opp_domain = _normalize(opp.domain)
        if lead_intent and (lead_intent in opp_domain or opp_domain in lead_intent):
            score += 0.15
            reasons.append(f"Domain aligns with {opp.domain} intent")
        elif lead_intent == "unknown":
            risks.append("Lead intent unknown")

        # Profession tags.
        opp_prof_tags = set(_load_tags(opp.profession_tags_json))
        if opp_prof_tags:
            prof_score = _overlap_score(opp_prof_tags, set(profession.split()))
            if prof_score > 0:
                score += 0.2 * prof_score
                reasons.append(f"Profession match: {', '.join(opp_prof_tags & set(profession.split()))}")
            else:
                risks.append("Profession does not match opportunity requirements")

        # Field tags.
        opp_field_tags = set(_load_tags(opp.field_tags_json))
        if opp_field_tags:
            field_score = _overlap_score(opp_field_tags, set(field.split()))
            if field_score > 0:
                score += 0.15 * field_score
                reasons.append(f"Field match: {', '.join(opp_field_tags & set(field.split()))}")

        # Experience requirement.
        if opp.required_years_experience is not None:
            if years_exp is not None and years_exp >= opp.required_years_experience:
                score += 0.1
                reasons.append(f"Meets experience requirement ({years_exp} years)")
            else:
                risks.append(f"Requires {opp.required_years_experience} years experience")

        # Budget / salary.
        if opp.budget_eur is not None and budget is not None and budget >= opp.budget_eur:
            score += 0.05
            reasons.append("Budget meets opportunity requirement")
        if opp.salary_eur is not None:
            reasons.append(f"Opportunity offers up to €{opp.salary_eur:,.0f}")

        score = round(min(score, 1.0), 2)
        matches.append({
            "opportunity": opp,
            "match_score": score,
            "confidence": round(0.5 + score * 0.5, 2),
            "reasons": reasons,
            "risks": risks,
        })

    matches.sort(key=lambda m: m["match_score"], reverse=True)
    top = matches[0] if matches else None

    return {
        "lead_id": lead_id,
        "matches": matches[:limit],
        "top_opportunity_id": top["opportunity"].id if top else None,
        "summary": (
            f"Found {len(matches)} active opportunities; "
            f"best match score {top['match_score'] if top else 0}."
        ),
    }


def seed_default_opportunities(session: Session) -> int:
    """Insert a small set of demo opportunities if none exist."""
    existing = session.exec(select(Opportunity)).first()
    if existing:
        return 0

    defaults = [
        Opportunity(
            title="Registered Nurse - University Hospital Frankfurt",
            organization="University Hospital Frankfurt",
            country="germany",
            domain="work",
            profession_tags_json=json.dumps(["nurse", "registered nurse", "healthcare"]),
            field_tags_json=json.dumps(["healthcare", "nursing"]),
            required_years_experience=2.0,
            language_requirement="B2 German",
            salary_eur=55000.0,
            description="Full-time nursing role for internationally qualified nurses with German B2.",
            source="demo",
        ),
        Opportunity(
            title="Software Engineer - Berlin Tech Visa Program",
            organization="Berlin Tech Talent",
            country="germany",
            domain="work",
            profession_tags_json=json.dumps(["software engineer", "developer", "it"]),
            field_tags_json=json.dumps(["technology", "software"]),
            required_years_experience=3.0,
            language_requirement="English B2",
            salary_eur=70000.0,
            description="EU Blue Card eligible software engineering roles in Berlin.",
            source="demo",
        ),
        Opportunity(
            title="MSc Computer Science - TU Munich",
            organization="Technical University of Munich",
            country="germany",
            domain="study",
            profession_tags_json=json.dumps([]),
            field_tags_json=json.dumps(["computer science", "technology", "engineering"]),
            required_years_experience=0.0,
            language_requirement="English C1 or German C1",
            budget_eur=12000.0,
            description="English-taught master's program with strong industry placement.",
            source="demo",
        ),
        Opportunity(
            title="Express Entry - Federal Skilled Worker",
            organization="Government of Canada",
            country="canada",
            domain="visa",
            profession_tags_json=json.dumps(["skilled worker", "professional"]),
            field_tags_json=json.dumps([]),
            required_years_experience=1.0,
            language_requirement="CLB 7",
            description="Permanent residency pathway for skilled workers with one year of skilled experience.",
            source="demo",
        ),
        Opportunity(
            title="Health and Care Worker Visa",
            organization="NHS England",
            country="uk",
            domain="work",
            profession_tags_json=json.dumps(["nurse", "care worker", "healthcare"]),
            field_tags_json=json.dumps(["healthcare", "nursing"]),
            required_years_experience=1.0,
            language_requirement="IELTS 5.5",
            salary_eur=32000.0,
            description="Sponsored visa route for qualified health and care professionals.",
            source="demo",
        ),
    ]
    for opp in defaults:
        session.add(opp)
    session.commit()
    return len(defaults)
