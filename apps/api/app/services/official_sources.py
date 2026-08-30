from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlparse

import yaml
from sqlmodel import Session, select

from app.models.domain import (
    CountryPolicy,
    OfficialSource,
    SourceCheckRun,
    SourceSnapshot,
    TruthClaim,
)
from app.schemas import TruthRequest, TruthResponse


DEFAULT_REGISTRY_PATH = "knowledge/official_sources/sources.yaml"
BOOTSTRAP_COUNTRIES = {"germany", "austria", "canada", "uk", "united_kingdom", "australia"}


def normalize_country(value: Optional[str]) -> str:
    country = str(value or "").strip().lower().replace("-", " ").replace("_", " ")
    aliases = {
        "de": "germany",
        "deutschland": "germany",
        "at": "austria",
        "ca": "canada",
        "gb": "united kingdom",
        "great britain": "united kingdom",
        "uk": "united kingdom",
        "united kingdom": "united kingdom",
        "australia": "australia",
    }
    return aliases.get(country, country)


def registry_country_key(value: Optional[str]) -> str:
    country = normalize_country(value)
    if country == "united kingdom":
        return "united_kingdom"
    return country.replace(" ", "_")


def normalize_domain(value: Optional[str]) -> str:
    domain = str(value or "general").strip().lower()
    if domain in {"study", "scholarship", "job"}:
        return "visa"
    return domain or "general"


def registry_path(path: str = DEFAULT_REGISTRY_PATH) -> Path:
    candidate = Path(path)
    if candidate.exists():
        return candidate
    # The registry lives at the project root; official_sources.py is under
    # apps/api/app/services/, so the project root is 4 parents up.
    root_candidate = Path(__file__).resolve().parents[4] / path
    if root_candidate.exists():
        return root_candidate
    return candidate


def load_registry(path: str = DEFAULT_REGISTRY_PATH) -> Dict[str, Any]:
    source_path = registry_path(path)
    if not source_path.exists():
        return {}
    return yaml.safe_load(source_path.read_text(encoding="utf-8")) or {}


def _source_name(entry: Dict[str, Any], url: str) -> str:
    parsed = urlparse(url)
    return str(entry.get("name") or entry.get("title") or parsed.netloc or url)


def _source_type(entry: Dict[str, Any]) -> str:
    return str(entry.get("source_type") or entry.get("type") or "official")


def _existing_source(session: Session, url: str) -> Optional[OfficialSource]:
    return session.exec(select(OfficialSource).where(OfficialSource.url == url)).first()


def upsert_official_source(
    session: Session,
    *,
    country: str,
    domain: str,
    name: str,
    url: str,
    source_type: str = "official",
    authority: Optional[str] = None,
    commit: bool = False,
) -> OfficialSource:
    existing = _existing_source(session, url)
    if existing:
        existing.country = normalize_country(country)
        existing.domain = normalize_domain(domain)
        existing.name = name
        existing.source_type = source_type
        existing.authority = authority
        existing.active = True
        session.add(existing)
        source = existing
    else:
        source = OfficialSource(
            country=normalize_country(country),
            domain=normalize_domain(domain),
            name=name,
            url=url,
            source_type=source_type,
            authority=authority,
            active=True,
        )
        session.add(source)
    if commit:
        session.commit()
        session.refresh(source)
    return source


def seed_official_sources(session: Session, *, registry: Optional[Dict[str, Any]] = None, commit: bool = True) -> Dict[str, Any]:
    data = registry if registry is not None else load_registry()
    seeded = 0
    skipped = 0
    countries: set[str] = set()

    for country_key, domains in data.items():
        if country_key not in BOOTSTRAP_COUNTRIES:
            skipped += 1
            continue
        if not isinstance(domains, dict):
            skipped += 1
            continue
        country = normalize_country(country_key)
        countries.add(country)
        for domain_key, entries in domains.items():
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if not isinstance(entry, dict) or not entry.get("url"):
                    skipped += 1
                    continue
                url = str(entry["url"]).strip()
                source = upsert_official_source(
                    session,
                    country=country,
                    domain=str(domain_key),
                    name=_source_name(entry, url),
                    url=url,
                    source_type=_source_type(entry),
                    authority=entry.get("authority"),
                    commit=False,
                )
                seeded += 1
                ensure_country_policy(session, country=source.country, domain=source.domain)

    if commit:
        session.commit()

    return {
        "status": "seeded",
        "sources_seen": seeded,
        "skipped": skipped,
        "countries": sorted(countries),
    }


def ensure_country_policy(session: Session, *, country: str, domain: str) -> CountryPolicy:
    country = normalize_country(country)
    domain = normalize_domain(domain)
    policy = session.exec(
        select(CountryPolicy)
        .where(CountryPolicy.country == country)
        .where(CountryPolicy.domain == domain)
    ).first()
    if policy:
        return policy
    policy = CountryPolicy(
        country=country,
        domain=domain,
        policy_json=json.dumps({
            "verification_required": True,
            "human_review_required": domain in {"visa", "job", "scholarship"},
            "source_priority": ["government", "official", "official_portal", "official_agency"],
        }),
        status="active",
    )
    session.add(policy)
    return policy


def list_sources(session: Session, *, country: Optional[str] = None, domain: Optional[str] = None) -> List[OfficialSource]:
    statement = select(OfficialSource).where(OfficialSource.active == True)  # noqa: E712
    if country:
        statement = statement.where(OfficialSource.country == normalize_country(country))
    if domain:
        statement = statement.where(OfficialSource.domain == normalize_domain(domain))
    return list(session.exec(statement.order_by(OfficialSource.country, OfficialSource.domain, OfficialSource.name)).all())


def sources_for_claim(session: Session, *, country: Optional[str], domain: str, fallback_urls: Iterable[str] = ()) -> List[OfficialSource]:
    sources = list_sources(session, country=country, domain=domain)
    if not sources and country:
        sources = list_sources(session, country=country, domain="visa")
    known_urls = {source.url for source in sources}
    for url in fallback_urls:
        if url not in known_urls:
            sources.append(upsert_official_source(
                session,
                country=country or "unknown",
                domain=domain,
                name=urlparse(url).netloc or url,
                url=url,
                source_type="official",
                commit=False,
            ))
            known_urls.add(url)
    return sources


def record_source_check_run(
    session: Session,
    *,
    truth_claim: TruthClaim,
    request: TruthRequest,
    result: TruthResponse,
    commit: bool = True,
) -> SourceCheckRun:
    sources = sources_for_claim(
        session,
        country=request.country,
        domain=request.domain,
        fallback_urls=result.official_sources,
    )
    matched = [
        {
            "id": str(source.id),
            "name": source.name,
            "url": source.url,
            "country": source.country,
            "domain": source.domain,
            "source_type": source.source_type,
        }
        for source in sources
    ]
    check_run = SourceCheckRun(
        truth_claim_id=truth_claim.id,
        country=normalize_country(request.country),
        domain=normalize_domain(request.domain),
        claim=request.claim,
        verdict=str(getattr(result.verdict, "value", result.verdict)).lower(),
        confidence=result.confidence,
        evidence_count=len(matched),
        matched_sources_json=json.dumps(matched),
        corrected_statement=result.recommended_next_step,
    )
    session.add(check_run)

    for source in sources:
        session.add(SourceSnapshot(
            official_source_id=source.id,
            url=source.url,
            status="referenced",
            metadata_json=json.dumps({
                "source_check_run_id": str(check_run.id),
                "truth_claim_id": str(truth_claim.id),
            }),
        ))

    if commit:
        session.commit()
        session.refresh(check_run)
    return check_run
