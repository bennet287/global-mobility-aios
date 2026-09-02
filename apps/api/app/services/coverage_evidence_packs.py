from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from pydantic import ValidationError
from sqlmodel import Session

from app.schemas import JurisdictionCoverageEvidenceBatchCreate
from app.services.coverage_evidence_batches import create_coverage_evidence_batch


DEFAULT_COVERAGE_EVIDENCE_PACK = (
    "knowledge/global_coverage/tranches/v10_17_official_evidence_starter.json"
)
_ALLOWED_REVIEW_STATUS = "pending_independent_review"
_VERSION_PATTERN = re.compile(r"^v\d+\.\d+(?:\.\d+)?$")


@dataclass(frozen=True)
class LoadedCoverageEvidencePack:
    path: Path
    pack_version: str
    title: str
    verified_at: date
    review_status: str
    jurisdiction_count: int
    batch: JurisdictionCoverageEvidenceBatchCreate
    references: tuple[dict[str, Any], ...]
    payload_sha256: str
    raw: dict[str, Any]

    def summary(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "pack_version": self.pack_version,
            "title": self.title,
            "verified_at": self.verified_at.isoformat(),
            "review_status": self.review_status,
            "jurisdiction_count": self.jurisdiction_count,
            "alpha2_codes": [item.alpha2_code.upper() for item in self.batch.items],
            "payload_sha256": self.payload_sha256,
            "creates_coverage_claim": False,
            "auto_approves_evidence": False,
            "requires_separate_reviewer": True,
        }


def _project_root() -> Path:
    return Path(__file__).resolve().parents[4]


def resolve_coverage_evidence_pack(path: str | Path | None = None) -> Path:
    candidate = Path(path or DEFAULT_COVERAGE_EVIDENCE_PACK)
    if candidate.is_absolute():
        return candidate
    if candidate.exists():
        return candidate.resolve()
    return (_project_root() / candidate).resolve()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _https_hostname(value: str, *, label: str) -> str:
    parsed = urlparse(value.strip())
    if parsed.scheme.lower() != "https" or not parsed.hostname:
        raise ValueError(f"{label} must be an absolute HTTPS URL")
    if parsed.username or parsed.password:
        raise ValueError(f"{label} must not contain credentials")
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError(f"{label} contains an invalid port") from exc
    if port not in (None, 443):
        raise ValueError(f"{label} must use the standard HTTPS port")
    return parsed.hostname.lower().rstrip(".")


def _domain_covers(hostname: str, allowed_domains: list[str]) -> bool:
    normalized = {value.strip().lower().rstrip(".") for value in allowed_domains}
    return any(hostname == domain or hostname.endswith(f".{domain}") for domain in normalized)


def load_coverage_evidence_pack(
    path: str | Path | None = None,
) -> LoadedCoverageEvidencePack:
    resolved = resolve_coverage_evidence_pack(path)
    if not resolved.is_file():
        raise ValueError(f"Coverage evidence pack not found: {resolved}")
    try:
        raw = json.loads(resolved.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Coverage evidence pack is not valid JSON: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError("Coverage evidence pack root must be an object")

    pack_version = str(raw.get("pack_version") or "").strip()
    if not _VERSION_PATTERN.fullmatch(pack_version):
        raise ValueError("Coverage evidence pack_version must use a vN.N or vN.N.N format")
    title = str(raw.get("title") or "").strip()
    if len(title) < 3:
        raise ValueError("Coverage evidence pack title is required")
    try:
        verified_at = date.fromisoformat(str(raw.get("verified_at") or ""))
    except ValueError as exc:
        raise ValueError("Coverage evidence verified_at must use YYYY-MM-DD") from exc
    review_status = str(raw.get("review_status") or "").strip()
    if review_status != _ALLOWED_REVIEW_STATUS:
        raise ValueError(
            f"Coverage evidence review_status must remain {_ALLOWED_REVIEW_STATUS}"
        )
    if raw.get("coverage_claim_ready") is not False:
        raise ValueError("Coverage evidence packs must not claim global coverage readiness")

    safety = raw.get("safety")
    if not isinstance(safety, dict):
        raise ValueError("Coverage evidence pack safety object is required")
    if safety.get("creates_coverage_claim") is not False:
        raise ValueError("Coverage evidence pack must declare creates_coverage_claim=false")
    if safety.get("auto_approves_evidence") is not False:
        raise ValueError("Coverage evidence pack must declare auto_approves_evidence=false")
    if safety.get("requires_separate_reviewer") is not True:
        raise ValueError("Coverage evidence pack must require a separate reviewer")

    try:
        batch = JurisdictionCoverageEvidenceBatchCreate.model_validate(raw.get("batch"))
    except ValidationError as exc:
        raise ValueError(f"Coverage evidence batch payload is invalid: {exc}") from exc

    codes = [item.alpha2_code.strip().upper() for item in batch.items]
    if len(codes) != len(set(codes)):
        raise ValueError("Coverage evidence pack contains duplicate jurisdiction codes")
    declared_count = raw.get("jurisdiction_count")
    if not isinstance(declared_count, int) or declared_count != len(codes):
        raise ValueError("Coverage evidence jurisdiction_count does not match batch items")

    references_raw = raw.get("references")
    if not isinstance(references_raw, list):
        raise ValueError("Coverage evidence pack references must be a list")
    references: list[dict[str, Any]] = []
    reference_codes: list[str] = []
    for index, reference in enumerate(references_raw, start=1):
        if not isinstance(reference, dict):
            raise ValueError(f"Coverage reference {index} must be an object")
        code = str(reference.get("alpha2_code") or "").strip().upper()
        if len(code) != 2:
            raise ValueError(f"Coverage reference {index} has an invalid alpha-2 code")
        _https_hostname(
            str(reference.get("authority_evidence_url") or ""),
            label=f"Coverage reference {code} authority_evidence_url",
        )
        _https_hostname(
            str(reference.get("source_url") or ""),
            label=f"Coverage reference {code} source_url",
        )
        if len(str(reference.get("evidence_summary") or "").strip()) < 10:
            raise ValueError(f"Coverage reference {code} evidence_summary is required")
        reference_codes.append(code)
        references.append(reference)
    if reference_codes != codes:
        raise ValueError("Coverage references must match batch jurisdiction order exactly")

    reference_by_code = {str(row["alpha2_code"]).upper(): row for row in references}
    for item in batch.items:
        code = item.alpha2_code.strip().upper()
        if item.immigration_assessment is not None:
            _https_hostname(
                item.immigration_assessment.evidence_url,
                label=f"{code} immigration assessment evidence_url",
            )
        onboarding = item.source_onboarding
        if onboarding is None:
            raise ValueError(
                f"Starter evidence pack item {code} must include source_onboarding"
            )
        source_hostname = _https_hostname(
            onboarding.source_url,
            label=f"{code} source_onboarding source_url",
        )
        if onboarding.authority_website_url:
            _https_hostname(
                onboarding.authority_website_url,
                label=f"{code} source_onboarding authority_website_url",
            )
        if not _domain_covers(source_hostname, onboarding.allowed_domains):
            raise ValueError(
                f"{code} source hostname is not covered by source_onboarding allowed_domains"
            )
        reference_source = str(reference_by_code[code].get("source_url") or "").rstrip("/")
        if reference_source != onboarding.source_url.rstrip("/"):
            raise ValueError(f"{code} reference source_url does not match source_onboarding")

    return LoadedCoverageEvidencePack(
        path=resolved,
        pack_version=pack_version,
        title=title,
        verified_at=verified_at,
        review_status=review_status,
        jurisdiction_count=declared_count,
        batch=batch,
        references=tuple(references),
        payload_sha256=_sha256(raw),
        raw=raw,
    )


def submit_coverage_evidence_pack(
    session: Session,
    *,
    pack: LoadedCoverageEvidencePack,
    actor: str,
):
    actor_name = actor.strip()
    if len(actor_name) < 2:
        raise ValueError("Coverage evidence pack submission requires an authenticated actor")
    return create_coverage_evidence_batch(
        session,
        name=pack.batch.name,
        notes=pack.batch.notes,
        items=[item.model_dump() for item in pack.batch.items],
        actor=actor_name,
    )
