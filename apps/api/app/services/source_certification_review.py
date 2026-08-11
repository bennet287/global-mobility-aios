from __future__ import annotations

import hashlib
import json
from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    Jurisdiction,
    JurisdictionSourceCertification,
    OfficialSource,
    RegulatoryAuthority,
    ShortageOccupationEntry,
    SourceSnapshot,
)
from app.schemas import SourceCertificationReviewPackRead
from app.services.shortage_occupations import shortage_occupation_projection_summary


REVIEW_PACK_VERSION = "source_certification_structured_evidence_v1"


def _load(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def source_certification_requires_structured_review_pack(
    session: Session,
    certification: JurisdictionSourceCertification,
) -> bool:
    """Return whether this certification has structured evidence that must be reviewed.

    This is deliberately data-driven rather than country- or certification-ID-specific.
    A source enters the stricter review path as soon as immutable structured occupation
    rows exist for that exact official source.
    """
    return session.exec(
        select(ShortageOccupationEntry.id)
        .where(
            ShortageOccupationEntry.jurisdiction_id == certification.jurisdiction_id,
            ShortageOccupationEntry.official_source_id == certification.official_source_id,
        )
        .limit(1)
    ).first() is not None


def _projection_keys(
    session: Session,
    certification: JurisdictionSourceCertification,
    *,
    source_snapshot_id: UUID | None,
) -> list[tuple[UUID, int, str]]:
    statement = select(ShortageOccupationEntry).where(
        ShortageOccupationEntry.jurisdiction_id == certification.jurisdiction_id,
        ShortageOccupationEntry.official_source_id == certification.official_source_id,
    )
    if source_snapshot_id is not None:
        statement = statement.where(
            ShortageOccupationEntry.source_snapshot_id == source_snapshot_id
        )
    rows = list(session.exec(statement).all())
    keys = sorted(
        {
            (row.source_snapshot_id, row.year, row.scope)
            for row in rows
        },
        key=lambda value: (str(value[0]), value[1], value[2]),
    )
    return keys


def source_certification_review_pack(
    session: Session,
    certification_id: UUID,
    *,
    source_snapshot_id: UUID | None = None,
) -> SourceCertificationReviewPackRead:
    certification = session.get(JurisdictionSourceCertification, certification_id)
    if certification is None:
        raise ValueError("Source certification not found")
    if not source_certification_requires_structured_review_pack(session, certification):
        raise ValueError(
            "This source certification has no structured shortage-occupation evidence review pack"
        )

    jurisdiction = session.get(Jurisdiction, certification.jurisdiction_id)
    authority = session.get(RegulatoryAuthority, certification.regulatory_authority_id)
    source = session.get(OfficialSource, certification.official_source_id)
    if jurisdiction is None or source is None or authority is None:
        raise ValueError("Certification provenance is incomplete")
    if source.jurisdiction_id != jurisdiction.id:
        raise ValueError("Certification official source jurisdiction does not match")
    if source.regulatory_authority_id != authority.id:
        raise ValueError("Certification official source authority does not match")

    keys = _projection_keys(
        session,
        certification,
        source_snapshot_id=source_snapshot_id,
    )
    if not keys:
        if source_snapshot_id is not None:
            raise ValueError(
                "No structured shortage-occupation projection exists for the pinned source snapshot"
            )
        raise ValueError("No structured shortage-occupation projection exists for this source")
    if len(keys) != 1:
        raise ValueError(
            "Multiple structured shortage-occupation projections exist for this source; "
            "pin source_snapshot_id before independent review"
        )

    snapshot_id, year, scope = keys[0]
    summary = shortage_occupation_projection_summary(
        session,
        source_snapshot_id=snapshot_id,
        year=year,
        scope=scope,
    )
    snapshot = session.get(SourceSnapshot, snapshot_id)
    if snapshot is None or snapshot.official_source_id != source.id:
        raise ValueError("Structured review snapshot provenance is invalid")

    entries = list(
        session.exec(
            select(ShortageOccupationEntry)
            .where(
                ShortageOccupationEntry.source_snapshot_id == snapshot.id,
                ShortageOccupationEntry.year == year,
                ShortageOccupationEntry.scope == scope,
            )
            .order_by(ShortageOccupationEntry.source_ordinal)
        ).all()
    )

    entry_payloads: list[dict[str, Any]] = []
    for row in entries:
        entry_payloads.append(
            {
                "source_ordinal": row.source_ordinal,
                "occupation_group": row.occupation_group,
                "normalized_occupation_group": row.normalized_occupation_group,
                "occupation_aliases": _load(row.occupation_aliases_json, []),
                "province_codes": _load(row.province_codes_json, []),
                "province_names": _load(row.province_names_json, []),
                "entry_sha256": row.entry_sha256,
            }
        )

    try:
        coverage_domains = json.loads(certification.coverage_domains_json)
    except (TypeError, ValueError):
        coverage_domains = []

    canonical_evidence = {
        "pack_version": REVIEW_PACK_VERSION,
        "certification": {
            "id": str(certification.id),
            "jurisdiction_id": str(certification.jurisdiction_id),
            "regulatory_authority_id": str(certification.regulatory_authority_id),
            "official_source_id": str(certification.official_source_id),
            "certification_version": certification.certification_version,
            "certification_scope": certification.certification_scope,
            "coverage_domains": coverage_domains,
            "evidence_notes": certification.evidence_notes,
            "proposed_by": certification.proposed_by,
            "created_at": certification.created_at.isoformat(),
        },
        "jurisdiction": {
            "id": str(jurisdiction.id),
            "code": jurisdiction.code,
            "name": jurisdiction.name,
        },
        "authority": {
            "id": str(authority.id),
            "name": authority.name,
            "authority_type": authority.authority_type,
            "website_url": authority.website_url,
        },
        "official_source": {
            "id": str(source.id),
            "name": source.name,
            "url": source.url,
            "country": source.country,
            "domain": source.domain,
            "source_type": source.source_type,
            "active": source.active,
        },
        "source_snapshot": {
            "id": str(snapshot.id),
            "url": snapshot.url,
            "content_hash": snapshot.content_hash,
            "content_text_sha256": hashlib.sha256(
                (snapshot.content_text or "").encode("utf-8")
            ).hexdigest(),
            "http_status": snapshot.http_status,
            "retrieval_method": snapshot.retrieval_method,
            "parser_version": snapshot.parser_version,
            "status": snapshot.status,
            "captured_at": snapshot.captured_at.isoformat(),
        },
        "structured_projection": {
            "year": summary["year"],
            "scope": summary["scope"],
            "entry_count": summary["entry_count"],
            "entry_set_sha256": summary["entry_set_sha256"],
            "extraction_version": summary["extraction_version"],
            "source_snapshot_content_hash": summary["source_snapshot_content_hash"],
        },
        "structured_entries": entry_payloads,
    }
    evidence_pack_sha256 = _sha256(canonical_evidence)

    return SourceCertificationReviewPackRead(
        pack_version=REVIEW_PACK_VERSION,
        evidence_pack_sha256=evidence_pack_sha256,
        certification_id=certification.id,
        certification_status=certification.status,
        proposed_by=certification.proposed_by,
        jurisdiction=canonical_evidence["jurisdiction"],
        regulatory_authority=canonical_evidence["authority"],
        official_source=canonical_evidence["official_source"],
        source_snapshot=canonical_evidence["source_snapshot"],
        source_content_text=snapshot.content_text or "",
        structured_projection=canonical_evidence["structured_projection"],
        structured_entries=entry_payloads,
        review_checklist=[
            "Confirm the official source and immutable snapshot are the intended evidence for this certification.",
            "Compare every structured occupation group, listed alias, and regional province mapping against the source text.",
            "Confirm the declared year, scope, entry count, snapshot content hash, and entry-set hash are correct.",
            "Do not infer individual case eligibility, qualification equivalence, job-offer sufficiency, or authority outcome from list membership.",
            "Only submit the independent-human attestation if you personally reviewed this evidence and are not the proposer.",
        ],
    )
