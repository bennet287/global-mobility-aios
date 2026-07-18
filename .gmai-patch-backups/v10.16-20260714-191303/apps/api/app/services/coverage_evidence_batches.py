from __future__ import annotations

import hashlib
import json
from typing import Any

from sqlmodel import Session, select

from app.models.domain import (
    Jurisdiction,
    JurisdictionCoverageEvidenceBatch,
    JurisdictionCoverageEvidenceBatchItem,
    JurisdictionImmigrationAssessment,
    JurisdictionRegistryEntry,
    JurisdictionRegistryRelease,
    JurisdictionSourceCertification,
)
from app.services.audit_log import record_audit
from app.services.jurisdiction_registry import (
    immigration_assessment_payload,
    propose_immigration_assessment,
    propose_source_certification,
    source_certification_payload,
)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _active_release(session: Session) -> JurisdictionRegistryRelease:
    release = session.exec(
        select(JurisdictionRegistryRelease).where(JurisdictionRegistryRelease.status == "active")
    ).first()
    if release is None:
        raise ValueError("No active jurisdiction registry release")
    return release


def _entry_for_code(
    session: Session,
    *,
    release_id: Any,
    alpha2_code: str,
) -> tuple[JurisdictionRegistryEntry, Jurisdiction]:
    code = alpha2_code.strip().upper()
    entry = session.exec(
        select(JurisdictionRegistryEntry).where(
            JurisdictionRegistryEntry.registry_release_id == release_id,
            JurisdictionRegistryEntry.alpha2_code == code,
        )
    ).first()
    if entry is None:
        raise ValueError(f"Jurisdiction {code} is not part of the active registry release")
    jurisdiction = session.get(Jurisdiction, entry.jurisdiction_id)
    if jurisdiction is None or not jurisdiction.active:
        raise ValueError(f"Jurisdiction {code} is not active")
    return entry, jurisdiction


def _normalise_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalised: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(items, start=1):
        code = str(item.get("alpha2_code") or "").strip().upper()
        if len(code) != 2:
            raise ValueError(f"Batch row {index} has an invalid alpha-2 code")
        if code in seen:
            raise ValueError(f"Batch contains duplicate jurisdiction {code}")
        seen.add(code)
        assessment = item.get("immigration_assessment")
        certification = item.get("source_certification")
        if assessment is None and certification is None:
            raise ValueError(f"Batch row {index} has no evidence operation")
        normalised.append(
            {
                "alpha2_code": code,
                "immigration_assessment": assessment,
                "source_certification": certification,
            }
        )
    return normalised


def _linked_statuses(
    session: Session,
    items: list[JurisdictionCoverageEvidenceBatchItem],
) -> list[str]:
    statuses: list[str] = []
    for item in items:
        if item.immigration_assessment_id:
            assessment = session.get(JurisdictionImmigrationAssessment, item.immigration_assessment_id)
            statuses.append(assessment.status if assessment else "missing")
        if item.source_certification_id:
            certification = session.get(JurisdictionSourceCertification, item.source_certification_id)
            statuses.append(certification.status if certification else "missing")
    return statuses


def _derived_status(statuses: list[str]) -> str:
    if not statuses:
        return "empty"
    if any(status == "pending_review" for status in statuses):
        return "pending_review"
    if all(status == "approved" for status in statuses):
        return "approved"
    if all(status == "rejected" for status in statuses):
        return "rejected"
    if any(status in {"missing", "superseded"} for status in statuses):
        return "historical_or_incomplete"
    return "reviewed_with_mixed_outcomes"


def coverage_batch_payload(
    session: Session,
    batch: JurisdictionCoverageEvidenceBatch,
    *,
    include_items: bool = True,
) -> dict[str, Any]:
    items = session.exec(
        select(JurisdictionCoverageEvidenceBatchItem)
        .where(JurisdictionCoverageEvidenceBatchItem.batch_id == batch.id)
        .order_by(JurisdictionCoverageEvidenceBatchItem.row_number)
    ).all()
    statuses = _linked_statuses(session, items)
    payload: dict[str, Any] = {
        "id": batch.id,
        "registry_release_id": batch.registry_release_id,
        "batch_key": batch.batch_key,
        "name": batch.name,
        "notes": batch.notes,
        "item_count": batch.item_count,
        "immigration_assessment_count": batch.immigration_assessment_count,
        "source_certification_count": batch.source_certification_count,
        "status": _derived_status(statuses),
        "stored_status": batch.status,
        "submitted_by": batch.submitted_by,
        "created_at": batch.created_at,
        "review_counts": {
            "pending_review": statuses.count("pending_review"),
            "approved": statuses.count("approved"),
            "rejected": statuses.count("rejected"),
            "superseded": statuses.count("superseded"),
            "missing": statuses.count("missing"),
        },
    }
    if include_items:
        result_items: list[dict[str, Any]] = []
        for item in items:
            assessment = session.get(JurisdictionImmigrationAssessment, item.immigration_assessment_id) if item.immigration_assessment_id else None
            certification = session.get(JurisdictionSourceCertification, item.source_certification_id) if item.source_certification_id else None
            result_items.append(
                {
                    "id": item.id,
                    "row_number": item.row_number,
                    "jurisdiction_id": item.jurisdiction_id,
                    "registry_entry_id": item.registry_entry_id,
                    "alpha2_code": item.alpha2_code,
                    "payload_sha256": item.payload_sha256,
                    "immigration_assessment": immigration_assessment_payload(assessment) if assessment else None,
                    "source_certification": source_certification_payload(certification) if certification else None,
                    "created_at": item.created_at,
                }
            )
        payload["items"] = result_items
    return payload


def create_coverage_evidence_batch(
    session: Session,
    *,
    name: str,
    notes: str,
    items: list[dict[str, Any]],
    actor: str,
) -> tuple[JurisdictionCoverageEvidenceBatch, bool]:
    release = _active_release(session)
    normalised = _normalise_items(items)
    canonical_payload = {
        "registry_release_id": str(release.id),
        "items": normalised,
    }
    batch_key = _sha256(canonical_payload)
    existing = session.exec(
        select(JurisdictionCoverageEvidenceBatch).where(
            JurisdictionCoverageEvidenceBatch.batch_key == batch_key
        )
    ).first()
    if existing:
        return existing, False

    prepared: list[tuple[int, JurisdictionRegistryEntry, Jurisdiction, dict[str, Any]]] = []
    for row_number, item in enumerate(normalised, start=1):
        entry, jurisdiction = _entry_for_code(
            session,
            release_id=release.id,
            alpha2_code=item["alpha2_code"],
        )
        prepared.append((row_number, entry, jurisdiction, item))

    batch = JurisdictionCoverageEvidenceBatch(
        registry_release_id=release.id,
        batch_key=batch_key,
        name=name.strip(),
        notes=notes.strip(),
        item_count=len(prepared),
        immigration_assessment_count=sum(1 for _, _, _, item in prepared if item["immigration_assessment"]),
        source_certification_count=sum(1 for _, _, _, item in prepared if item["source_certification"]),
        status="submitted_for_review",
        submitted_by=actor,
    )
    session.add(batch)
    session.flush()

    try:
        for row_number, entry, jurisdiction, item in prepared:
            assessment = None
            certification = None
            if item["immigration_assessment"]:
                assessment = propose_immigration_assessment(
                    session,
                    jurisdiction_id=jurisdiction.id,
                    actor=actor,
                    commit=False,
                    **item["immigration_assessment"],
                )
            if item["source_certification"]:
                certification = propose_source_certification(
                    session,
                    jurisdiction_id=jurisdiction.id,
                    actor=actor,
                    commit=False,
                    **item["source_certification"],
                )
            item_payload = {
                "alpha2_code": item["alpha2_code"],
                "immigration_assessment": item["immigration_assessment"],
                "source_certification": item["source_certification"],
            }
            session.add(
                JurisdictionCoverageEvidenceBatchItem(
                    batch_id=batch.id,
                    row_number=row_number,
                    jurisdiction_id=jurisdiction.id,
                    registry_entry_id=entry.id,
                    alpha2_code=item["alpha2_code"],
                    immigration_assessment_id=assessment.id if assessment else None,
                    source_certification_id=certification.id if certification else None,
                    payload_sha256=_sha256(item_payload),
                    payload_json=_canonical_json(item_payload),
                )
            )
        record_audit(
            session,
            action="jurisdiction_coverage_evidence_batch_submitted",
            entity_type="jurisdiction_coverage_evidence_batch",
            entity_id=batch.id,
            after_state={
                "registry_release_id": release.id,
                "batch_key": batch.batch_key,
                "item_count": batch.item_count,
                "immigration_assessment_count": batch.immigration_assessment_count,
                "source_certification_count": batch.source_certification_count,
            },
            reason=batch.notes,
            actor=actor,
            source="global_intelligence",
        )
        session.commit()
        session.refresh(batch)
    except Exception:
        session.rollback()
        raise
    return batch, True


def list_coverage_evidence_batches(
    session: Session,
    *,
    limit: int = 50,
) -> list[JurisdictionCoverageEvidenceBatch]:
    return session.exec(
        select(JurisdictionCoverageEvidenceBatch)
        .order_by(JurisdictionCoverageEvidenceBatch.created_at.desc())
        .limit(limit)
    ).all()


def jurisdiction_coverage_worklist(
    session: Session,
    *,
    gap: str | None = None,
    region: str | None = None,
    limit: int = 249,
) -> dict[str, Any]:
    from app.services.jurisdiction_registry import jurisdiction_registry_coverage

    coverage = jurisdiction_registry_coverage(session)
    entries = [entry for entry in coverage.get("entries", []) if entry.get("coverage_required")]
    if gap and gap != "all":
        entries = [entry for entry in entries if gap in entry.get("missing", [])]
    if region and region != "all":
        entries = [entry for entry in entries if (entry.get("region") or "Unassigned") == region]
    priority_order = {
        "immigration_rule_assessment": 0,
        "reviewed_primary_authority": 1,
        "reviewed_primary_source": 2,
        "official_source": 3,
        "authority": 4,
        "fresh_monitor": 5,
        "verified_rule": 6,
    }
    entries.sort(
        key=lambda entry: (
            min((priority_order.get(item, 99) for item in entry.get("missing", [])), default=99),
            entry.get("region") or "",
            entry.get("name") or "",
        )
    )
    selected = entries[:limit]
    return {
        "generated_at": coverage.get("generated_at"),
        "release": coverage.get("release"),
        "filters": {"gap": gap or "all", "region": region or "all", "limit": limit},
        "total": len(entries),
        "items": [
            {
                "jurisdiction_id": entry["jurisdiction_id"],
                "registry_entry_id": entry["id"],
                "alpha2_code": entry["alpha2_code"],
                "name": entry["name"],
                "region": entry.get("region"),
                "jurisdiction_type": entry["jurisdiction_type"],
                "immigration_rule_status": entry["immigration_rule_status"],
                "missing": entry.get("missing", []),
                "has_authority": entry.get("has_authority", False),
                "has_official_source": entry.get("has_official_source", False),
                "pending_assessment": entry.get("pending_assessment"),
                "pending_source_certification": entry.get("pending_source_certification"),
            }
            for entry in selected
        ],
        "safety": {
            "creates_coverage_claim": False,
            "human_review_required": True,
            "message": "The worklist prioritizes evidence gaps. It does not certify coverage or infer immigration authority.",
        },
    }
