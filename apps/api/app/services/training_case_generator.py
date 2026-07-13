from __future__ import annotations

import json
import random
from typing import Any

from sqlmodel import Session

from app.models.domain import TrainingCase

COUNTRIES = ["Germany", "Canada", "Australia", "UK", "USA"]
PROFESSIONS = ["Registered Nurse", "Software Engineer", "Civil Engineer", "Data Analyst", "Hospitality Worker"]
NATIONALITIES = ["India", "Philippines", "Nigeria", "Brazil", "Vietnam", "Egypt", "Pakistan"]


def _nurse_scenario(country: str, nationality: str) -> dict[str, Any]:
    years = random.randint(1, 8)
    has_license = random.choice([True, True, False])
    language = random.choice(["B1", "B2", "C1"])
    return {
        "profession": "Registered Nurse",
        "nationality": nationality,
        "target_country": country,
        "years_experience": years,
        "has_relevant_degree": True,
        "has_professional_license": has_license,
        "language_level": language,
        "goal": "work abroad",
    }


def _nurse_expected(scenario: dict[str, Any]) -> dict[str, Any]:
    country = scenario["target_country"]
    language = scenario["language_level"]
    license_ok = scenario["has_professional_license"]
    missing = []
    pathways = []
    if country == "Germany":
        pathways.append("Anerkennung (recognition) of nursing degree")
        if language in {"B1"}:
            missing.append("German B2 language certificate for registration")
        if not license_ok:
            missing.append("Home-country nursing license verification")
    elif country == "Canada":
        pathways.append("Provincial nursing regulatory body assessment")
        missing.append("NCLEX-RN or local jurisprudence exam")
    else:
        pathways.append(f"{country} nursing registration pathway")
        missing.append("Verify local registration requirements")
    return {
        "eligible_pathways": pathways,
        "missing_requirements": missing,
        "confidence": "medium" if missing else "high",
    }


def _tech_scenario(country: str, nationality: str) -> dict[str, Any]:
    years = random.randint(2, 10)
    has_degree = random.choice([True, True, False])
    language = random.choice(["B1", "B2", "C1", "fluent"])
    return {
        "profession": "Software Engineer",
        "nationality": nationality,
        "target_country": country,
        "years_experience": years,
        "has_relevant_degree": has_degree,
        "has_job_offer": random.choice([True, False]),
        "language_level": language,
        "goal": "work abroad",
    }


def _tech_expected(scenario: dict[str, Any]) -> dict[str, Any]:
    country = scenario["target_country"]
    missing = []
    pathways = []
    if country == "Germany":
        pathways.append("EU Blue Card or §18c Opportunity Card")
        if not scenario.get("has_job_offer"):
            missing.append("Signed employment contract or binding job offer")
        if scenario["language_level"] == "B1":
            missing.append("B1 German is minimum for Opportunity Card; B2+ improves chances")
    elif country in {"Canada", "Australia"}:
        pathways.append(f"Skilled worker points-based pathway ({country})")
        missing.append("Language test (IELTS/CELPIP/PTE)")
        missing.append("Educational Credential Assessment")
    else:
        pathways.append(f"{country} skilled worker route")
        missing.append("Confirm eligible occupation list and salary threshold")
    return {
        "eligible_pathways": pathways,
        "missing_requirements": missing,
        "confidence": "medium" if missing else "high",
    }


def _generic_scenario(profession: str, country: str, nationality: str) -> dict[str, Any]:
    return {
        "profession": profession,
        "nationality": nationality,
        "target_country": country,
        "years_experience": random.randint(1, 10),
        "has_relevant_degree": random.choice([True, False]),
        "language_level": random.choice(["A2", "B1", "B2", "C1"]),
        "goal": random.choice(["work abroad", "permanent residency", "short-term visa"]),
    }


def _generic_expected(scenario: dict[str, Any]) -> dict[str, Any]:
    return {
        "eligible_pathways": [f"Consult {scenario['target_country']} official immigration guidance for {scenario['profession']}"],
        "missing_requirements": ["Complete profile and document verification required"],
        "confidence": "low",
    }


def _build_case(profession: str, country: str) -> TrainingCase:
    nationality = random.choice(NATIONALITIES)
    if profession == "Registered Nurse":
        scenario = _nurse_scenario(country, nationality)
        expected = _nurse_expected(scenario)
    elif profession == "Software Engineer":
        scenario = _tech_scenario(country, nationality)
        expected = _tech_expected(scenario)
    else:
        scenario = _generic_scenario(profession, country, nationality)
        expected = _generic_expected(scenario)

    title = f"{nationality} {profession} → {country}"
    return TrainingCase(
        title=title,
        country=country,
        profession=profession,
        scenario_json=json.dumps(scenario, default=str, sort_keys=True),
        expected_outcome_json=json.dumps(expected, default=str, sort_keys=True),
        source="synthetic",
        times_run=0,
    )


def generate_training_cases(
    session: Session,
    count: int = 5,
    country: str | None = None,
    profession: str | None = None,
) -> list[TrainingCase]:
    """Generate synthetic training cases and persist them."""
    countries = [country] if country else COUNTRIES
    professions = [profession] if profession else PROFESSIONS
    cases: list[TrainingCase] = []
    for _ in range(count):
        case = _build_case(
            profession=random.choice(professions),
            country=random.choice(countries),
        )
        session.add(case)
        cases.append(case)
    session.commit()
    for case in cases:
        session.refresh(case)
    return cases
