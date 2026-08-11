from __future__ import annotations

import hashlib
import json
from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    AuditLog,
    Jurisdiction,
    JurisdictionSourceCertification,
    OfficialSource,
    RegulatoryAuthority,
    ShortageOccupationEntry,
    SourceSnapshot,
)
from app.schemas import (
    SourceCertificationReviewHistoryEntry,
    SourceCertificationReviewPackRead,
    SourceCertificationReviewProjectionOption,
    SourceCertificationReviewQueueItem,
    SourceCertificationReviewQueueRead,
    SourceCertificationReviewWorkspaceRead,
)
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


def _certification_payload(certification: JurisdictionSourceCertification) -> dict[str, Any]:
    return {
        "id": certification.id,
        "jurisdiction_id": certification.jurisdiction_id,
        "registry_entry_id": certification.registry_entry_id,
        "regulatory_authority_id": certification.regulatory_authority_id,
        "official_source_id": certification.official_source_id,
        "certification_version": certification.certification_version,
        "certification_scope": certification.certification_scope,
        "coverage_domains": _load(certification.coverage_domains_json, []),
        "evidence_notes": certification.evidence_notes,
        "status": certification.status,
        "proposed_by": certification.proposed_by,
        "reviewed_by": certification.reviewed_by,
        "reviewed_at": certification.reviewed_at,
        "review_notes": certification.review_notes,
        "supersedes_certification_id": certification.supersedes_certification_id,
        "created_at": certification.created_at,
        "updated_at": certification.updated_at,
    }


def _review_projections(
    session: Session,
    certification: JurisdictionSourceCertification,
) -> list[SourceCertificationReviewProjectionOption]:
    options: list[SourceCertificationReviewProjectionOption] = []
    for snapshot_id, year, scope in _projection_keys(
        session,
        certification,
        source_snapshot_id=None,
    ):
        summary = shortage_occupation_projection_summary(
            session,
            source_snapshot_id=snapshot_id,
            year=year,
            scope=scope,
        )
        options.append(
            SourceCertificationReviewProjectionOption(
                source_snapshot_id=snapshot_id,
                year=year,
                scope=scope,
                entry_count=summary["entry_count"],
                entry_set_sha256=summary["entry_set_sha256"],
                extraction_version=summary["extraction_version"],
                source_snapshot_content_hash=summary["source_snapshot_content_hash"],
            )
        )
    return options


def _review_identity_conflict(
    certification: JurisdictionSourceCertification,
    reviewer_identity: str,
) -> bool:
    return certification.proposed_by.strip().casefold() == reviewer_identity.strip().casefold()


def source_certification_review_history(
    session: Session,
    certification_id: UUID,
) -> list[SourceCertificationReviewHistoryEntry]:
    certification = session.get(JurisdictionSourceCertification, certification_id)
    if certification is None:
        raise ValueError("Source certification not found")

    rows = list(
        session.exec(
            select(AuditLog)
            .where(
                AuditLog.entity_type == "jurisdiction_source_certification",
                AuditLog.entity_id == str(certification.id),
                AuditLog.action == "jurisdiction_source_certification_reviewed",
            )
            .order_by(AuditLog.created_at.desc())
        ).all()
    )
    history: list[SourceCertificationReviewHistoryEntry] = []
    for row in rows:
        after_state = _load(row.after_state_json, {})
        review_evidence = after_state.get("review_evidence") or {}
        snapshot_value = review_evidence.get("source_snapshot_id") or None
        history.append(
            SourceCertificationReviewHistoryEntry(
                id=row.id,
                actor=row.actor,
                decision=review_evidence.get("decision"),
                notes=row.reason,
                evidence_pack_sha256=review_evidence.get("evidence_pack_sha256"),
                pack_version=review_evidence.get("pack_version"),
                source_snapshot_id=UUID(snapshot_value) if snapshot_value else None,
                independent_human_attestation=bool(
                    review_evidence.get("independent_human_attestation")
                ),
                structured_projection=review_evidence.get("structured_projection") or {},
                created_at=row.created_at,
            )
        )
    return history


def _review_context(
    session: Session,
    certification: JurisdictionSourceCertification,
    *,
    reviewer_identity: str,
    reviewer_role: str,
    source_snapshot_id: UUID | None,
) -> tuple[
    str,
    list[SourceCertificationReviewProjectionOption],
    SourceCertificationReviewPackRead | None,
    bool,
    bool,
]:
    projections = _review_projections(session, certification)
    review_pack: SourceCertificationReviewPackRead | None = None
    review_pack_state = "unavailable"

    if projections:
        if source_snapshot_id is None and len(projections) > 1:
            review_pack_state = "snapshot_pin_required"
        else:
            selected_snapshot_id = source_snapshot_id or projections[0].source_snapshot_id
            if selected_snapshot_id not in {item.source_snapshot_id for item in projections}:
                raise ValueError(
                    "Pinned source snapshot is not one of this certification's structured projections"
                )
            review_pack = source_certification_review_pack(
                session,
                certification.id,
                source_snapshot_id=selected_snapshot_id,
            )
            review_pack_state = "ready"

    identity_conflict = _review_identity_conflict(certification, reviewer_identity)
    can_submit = (
        certification.status == "pending_review"
        and review_pack_state == "ready"
        and not identity_conflict
        and reviewer_role in {"admin", "reviewer"}
    )
    return review_pack_state, projections, review_pack, identity_conflict, can_submit


def source_certification_review_queue(
    session: Session,
    *,
    reviewer_identity: str,
    reviewer_role: str,
) -> SourceCertificationReviewQueueRead:
    rows = list(
        session.exec(
            select(JurisdictionSourceCertification)
            .where(JurisdictionSourceCertification.status == "pending_review")
            .order_by(JurisdictionSourceCertification.created_at.asc())
        ).all()
    )
    items: list[SourceCertificationReviewQueueItem] = []
    for certification in rows:
        if not source_certification_requires_structured_review_pack(session, certification):
            continue

        jurisdiction = session.get(Jurisdiction, certification.jurisdiction_id)
        authority = session.get(RegulatoryAuthority, certification.regulatory_authority_id)
        source = session.get(OfficialSource, certification.official_source_id)
        if jurisdiction is None or authority is None or source is None:
            continue

        state, projections, review_pack, conflict, can_submit = _review_context(
            session,
            certification,
            reviewer_identity=reviewer_identity,
            reviewer_role=reviewer_role,
            source_snapshot_id=None,
        )
        items.append(
            SourceCertificationReviewQueueItem(
                certification=_certification_payload(certification),
                jurisdiction={
                    "id": jurisdiction.id,
                    "code": jurisdiction.code,
                    "name": jurisdiction.name,
                },
                regulatory_authority={
                    "id": authority.id,
                    "name": authority.name,
                    "authority_type": authority.authority_type,
                },
                official_source={
                    "id": source.id,
                    "name": source.name,
                    "url": source.url,
                    "domain": source.domain,
                    "source_type": source.source_type,
                },
                review_pack_state=state,
                available_projections=projections,
                evidence_pack_sha256=(
                    review_pack.evidence_pack_sha256 if review_pack is not None else None
                ),
                selected_source_snapshot_id=(
                    UUID(str(review_pack.source_snapshot["id"]))
                    if review_pack is not None
                    else None
                ),
                reviewer_identity_conflict=conflict,
                can_submit_review=can_submit,
            )
        )

    return SourceCertificationReviewQueueRead(
        reviewer_identity=reviewer_identity,
        reviewer_role=reviewer_role,
        total=len(items),
        items=items,
        safety_message=(
            "Review-queue presence is not approval. A genuine separate human reviewer must "
            "personally compare the exact immutable source snapshot with every structured "
            "projection row before submitting an attested review decision."
        ),
    )


def source_certification_review_workspace(
    session: Session,
    certification_id: UUID,
    *,
    reviewer_identity: str,
    reviewer_role: str,
    source_snapshot_id: UUID | None = None,
) -> SourceCertificationReviewWorkspaceRead:
    certification = session.get(JurisdictionSourceCertification, certification_id)
    if certification is None:
        raise ValueError("Source certification not found")
    if not source_certification_requires_structured_review_pack(session, certification):
        raise ValueError(
            "This source certification has no structured shortage-occupation review workspace"
        )

    state, projections, review_pack, conflict, can_submit = _review_context(
        session,
        certification,
        reviewer_identity=reviewer_identity,
        reviewer_role=reviewer_role,
        source_snapshot_id=source_snapshot_id,
    )
    requirements = [
        "Reviewer identity must be genuinely independent from the proposer.",
        "The exact deterministic evidence-pack SHA-256 must be confirmed at submission time.",
        "The reviewer must personally compare the immutable source text with every structured row.",
        "Independent-human attestation is mandatory for either approval or rejection.",
        "A certification decision does not publish any pathway; pathway publication remains a separate controlled action.",
    ]
    if state == "snapshot_pin_required":
        requirements.insert(
            0,
            "Select and pin one exact structured source snapshot before review; multiple projections are available.",
        )
    if reviewer_role not in {"admin", "reviewer"}:
        requirements.insert(
            0,
            "The authenticated role is read-only for certification review submission; use an authorized reviewer or admin session.",
        )
    if conflict:
        requirements.insert(
            0,
            "The authenticated reviewer identity matches the proposer and cannot submit this review.",
        )

    return SourceCertificationReviewWorkspaceRead(
        certification=_certification_payload(certification),
        reviewer_identity=reviewer_identity,
        reviewer_role=reviewer_role,
        reviewer_identity_conflict=conflict,
        review_pack_state=state,
        can_submit_review=can_submit,
        submission_requirements=requirements,
        available_projections=projections,
        review_pack=review_pack,
        review_history=source_certification_review_history(session, certification.id),
    )
