from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

import yaml

from app.models.domain import VerificationStatus
from app.schemas import TruthRequest, TruthResponse

OFFICIAL_DOMAIN_HINTS = {
    ".gov",
    ".gv.at",
    ".gob.",
    ".gc.ca",
    ".gov.uk",
    ".homeaffairs.gov.au",
    ".diplo.de",
    ".europa.eu",
    ".admin.ch",
    ".go.jp",
    ".gov.in",
    "migration.gv.at",
    "auswaertiges-amt.de",
    "make-it-in-germany.com",
    "oead.at",
    "canada.ca",
    "immi.homeaffairs.gov.au",
}

HIGH_RISK_PHRASES = [
    "guaranteed visa",
    "100% visa",
    "visa guaranteed",
    "without financial proof",
    "no documents required",
    "bypass embassy",
    "fake experience",
    "fake bank statement",
    "pay and get visa",
    "work visa without employer",
]

MISLEADING_PHRASES = [
    "easy approval",
    "no rejection",
    "secret route",
    "agent can arrange",
    "embassy contact",
]

SENSITIVE_DOMAINS = {"visa", "job", "scholarship"}

@dataclass
class TruthEngine:
    strict_mode: bool = True
    source_registry_path: str = "knowledge/official_sources/sources.yaml"

    def verify(self, request: TruthRequest) -> TruthResponse:
        claim_lower = request.claim.lower()
        red_flags = self._red_flags(claim_lower)
        registry_sources = self._registry_sources(request.country, request.domain)
        official_sources = self._merge_sources(
            self._official_sources(request.source_urls),
            registry_sources,
        )

        if any(flag in HIGH_RISK_PHRASES for flag in red_flags):
            return TruthResponse(
                verdict=VerificationStatus.rejected,
                confidence=0.95,
                requires_human_review=True,
                explanation="The claim contains high-risk wording commonly associated with misinformation or improper immigration advice.",
                official_sources=official_sources,
                red_flags=red_flags,
                recommended_next_step="Reject this claim and replace it with a source-grounded explanation from official channels.",
            )

        if red_flags:
            confidence = 0.45 if official_sources else 0.30
            return TruthResponse(
                verdict=VerificationStatus.needs_review,
                confidence=confidence,
                requires_human_review=True,
                explanation="The claim contains potentially misleading wording. A human reviewer should validate it before client-facing use.",
                official_sources=official_sources,
                red_flags=red_flags,
                recommended_next_step="Escalate to a human reviewer and verify the exact rule against official government or institution sources.",
            )

        if official_sources:
            confidence = 0.86 if len(official_sources) >= 2 else 0.78
            requires_review = request.domain in SENSITIVE_DOMAINS
            return TruthResponse(
                verdict=VerificationStatus.verified,
                confidence=confidence,
                requires_human_review=requires_review,
                explanation="Official sources are available for this country/domain. Sensitive recommendations still require review before final client delivery.",
                official_sources=official_sources,
                red_flags=red_flags,
                recommended_next_step="Generate a conditional recommendation with source URL, retrieval date, country, visa/job/study category, and assumptions.",
            )

        fallback_confidence = 0.35 if self.strict_mode else 0.55
        return TruthResponse(
            verdict=VerificationStatus.needs_review,
            confidence=fallback_confidence,
            requires_human_review=True,
            explanation="No official source evidence was found. The system cannot treat this claim as verified.",
            official_sources=official_sources,
            red_flags=red_flags,
            recommended_next_step="Retrieve official sources before generating advice or recommendations.",
        )

    def _red_flags(self, claim_lower: str) -> list[str]:
        flags = [phrase for phrase in HIGH_RISK_PHRASES if phrase in claim_lower]
        flags += [phrase for phrase in MISLEADING_PHRASES if phrase in claim_lower]
        return flags

    def _official_sources(self, urls: Iterable[str]) -> list[str]:
        official: list[str] = []
        for url in urls:
            host = urlparse(url).netloc.lower()
            if any(hint in host for hint in OFFICIAL_DOMAIN_HINTS):
                official.append(url)
        return official

    def _registry_sources(self, country: str | None, domain: str) -> list[str]:
        if not country:
            return []

        registry_file = Path(self.source_registry_path)

        if not registry_file.exists():
            alt_candidates = [
                Path("/knowledge/official_sources/sources.yaml"),
                Path(__file__).resolve().parents[5] / self.source_registry_path,
            ]
            registry_file = next((candidate for candidate in alt_candidates if candidate.exists()), registry_file)

        if not registry_file.exists():
            return []

        data = yaml.safe_load(registry_file.read_text(encoding="utf-8")) or {}
        country_key = country.lower().strip().replace(" ", "_")
        domain_key = "visa" if domain in {"visa", "job", "study", "scholarship"} else domain
        entries = data.get(country_key, {}).get(domain_key, [])
        return [entry["url"] for entry in entries if isinstance(entry, dict) and entry.get("url")]

    def _merge_sources(self, *groups: list[str]) -> list[str]:
        seen: set[str] = set()
        merged: list[str] = []
        for group in groups:
            for url in group:
                if url not in seen:
                    seen.add(url)
                    merged.append(url)
        return merged
