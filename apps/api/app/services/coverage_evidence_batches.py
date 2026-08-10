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
    OfficialSource,
    RegulatoryAuthority,
    SourceMonitor,
)
from app.schemas import RegulatorySourceOnboardingRequest
from app.services.audit_log import record_audit
from app.services.jurisdiction_registry import (
    immigration_assessment_payload,
    propose_immigration_assessment,
    propose_source_certification,
    source_certification_payload,
)
from app.services.regulatory_intelligence import onboard_regulatory_source


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
        onboarding = item.get("source_onboarding")
        if assessment is None and certification is None and onboarding is None:
            raise ValueError(f"Batch row {index} has no evidence operation")
        if certification is not None and onboarding is not None:
            raise ValueError(
                f"Batch row {index} must not combine source_certification with source_onboarding"
            )
        normalised.append(
            {
                "alpha2_code": code,
                "immigration_assessment": assessment,
                "source_certification": certification,
                "source_onboarding": onboarding,
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


def reconcile_coverage_batch_existing_source_linkage(
    session: Session,
    batch_id: Any,
    *,
    actor: str,
    commit: bool = True,
) -> dict[str, Any]:
    """Backfill derived linkage for certification-only coverage batch items.

    This operation never changes the certification, source, monitor,
    retrieval history, immutable snapshots, or original batch payload.
    Existing non-null linkage must already agree with the approved
    certification or the operation fails closed.
    """

    batch = session.get(
        JurisdictionCoverageEvidenceBatch,
        batch_id,
    )
    if batch is None:
        raise ValueError("Coverage evidence batch not found")

    items = session.exec(
        select(JurisdictionCoverageEvidenceBatchItem)
        .where(
            JurisdictionCoverageEvidenceBatchItem.batch_id
            == batch.id
        )
        .order_by(
            JurisdictionCoverageEvidenceBatchItem.row_number
        )
    ).all()

    changes: list[dict[str, Any]] = []

    for item in items:
        if item.source_certification_id is None:
            continue

        certification = session.get(
            JurisdictionSourceCertification,
            item.source_certification_id,
        )
        if certification is None:
            raise ValueError(
                f"Coverage batch item {item.id} references "
                "a missing source certification"
            )

        if certification.status != "approved":
            raise ValueError(
                f"Source certification for {item.alpha2_code} "
                "is not independently approved"
            )

        if certification.jurisdiction_id != item.jurisdiction_id:
            raise ValueError(
                f"Source certification for {item.alpha2_code} "
                "belongs to a different jurisdiction"
            )

        expected_authority_id = (
            certification.regulatory_authority_id
        )
        expected_source_id = certification.official_source_id

        if (
            item.regulatory_authority_id is not None
            and item.regulatory_authority_id
            != expected_authority_id
        ):
            raise ValueError(
                f"Stored authority linkage for {item.alpha2_code} "
                "conflicts with the approved certification"
            )

        if (
            item.official_source_id is not None
            and item.official_source_id != expected_source_id
        ):
            raise ValueError(
                f"Stored source linkage for {item.alpha2_code} "
                "conflicts with the approved certification"
            )

        authority = session.get(
            RegulatoryAuthority,
            expected_authority_id,
        )
        if (
            authority is None
            or not authority.active
            or authority.jurisdiction_id
            != item.jurisdiction_id
        ):
            raise ValueError(
                f"Certified authority for {item.alpha2_code} "
                "is not active in the batch jurisdiction"
            )

        source = session.get(
            OfficialSource,
            expected_source_id,
        )
        if (
            source is None
            or not source.active
            or source.jurisdiction_id
            != item.jurisdiction_id
        ):
            raise ValueError(
                f"Certified source for {item.alpha2_code} "
                "is not active in the batch jurisdiction"
            )

        if (
            source.regulatory_authority_id
            != authority.id
        ):
            raise ValueError(
                f"Certified source for {item.alpha2_code} "
                "is not attached to the certified authority"
            )

        monitor = session.exec(
            select(SourceMonitor).where(
                SourceMonitor.official_source_id
                == source.id
            )
        ).first()

        if monitor is None:
            raise ValueError(
                f"Certified source for {item.alpha2_code} "
                "does not have an existing source monitor"
            )

        if (
            item.source_monitor_id is not None
            and item.source_monitor_id != monitor.id
        ):
            raise ValueError(
                f"Stored monitor linkage for {item.alpha2_code} "
                "conflicts with the certified source"
            )

        before = {
            "batch_item_id": item.id,
            "regulatory_authority_id":
                item.regulatory_authority_id,
            "official_source_id":
                item.official_source_id,
            "source_monitor_id":
                item.source_monitor_id,
        }

        after = {
            "batch_item_id": item.id,
            "regulatory_authority_id":
                authority.id,
            "official_source_id":
                source.id,
            "source_monitor_id":
                monitor.id,
        }

        if before == after:
            continue

        item.regulatory_authority_id = authority.id
        item.official_source_id = source.id
        item.source_monitor_id = monitor.id

        session.add(item)

        changes.append({
            "before": before,
            "after": after,
        })

    if changes:
        session.flush()

        record_audit(
            session,
            action=(
                "jurisdiction_coverage_existing_source_"
                "linkage_reconciled"
            ),
            entity_type=(
                "jurisdiction_coverage_evidence_batch"
            ),
            entity_id=batch.id,
            before_state={
                "items": [
                    change["before"]
                    for change in changes
                ]
            },
            after_state={
                "items": [
                    change["after"]
                    for change in changes
                ]
            },
            reason=(
                "Backfill derived authority, official-source, "
                "and monitor linkage for certification-only "
                "coverage batch items. Certification, source, "
                "retrieval, snapshot, and payload provenance "
                "remain unchanged."
            ),
            actor=actor,
            source="global_intelligence_v13_10_2_3",
        )

        if commit:
            session.commit()

    return {
        "batch_id": batch.id,
        "changed": len(changes),
        "items": [
            change["after"]
            for change in changes
        ],
        "safety": {
            "changes_certification": False,
            "changes_source": False,
            "changes_snapshot": False,
            "changes_payload": False,
            "creates_coverage_claim": False,
            "publishes_verified_rule": False,
        },
    }


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
        "source_onboarding_count": batch.source_onboarding_count,
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
            authority = session.get(RegulatoryAuthority, item.regulatory_authority_id) if item.regulatory_authority_id else None
            source = session.get(OfficialSource, item.official_source_id) if item.official_source_id else None
            monitor = session.get(SourceMonitor, item.source_monitor_id) if item.source_monitor_id else None
            source_onboarding = None
            if authority or source or monitor:
                source_onboarding = {
                    "regulatory_authority_id": authority.id if authority else None,
                    "authority_name": authority.name if authority else None,
                    "official_source_id": source.id if source else None,
                    "source_name": source.name if source else None,
                    "source_url": source.url if source else None,
                    "source_monitor_id": monitor.id if monitor else None,
                    "monitor_status": monitor.status if monitor else None,
                    "next_check_at": monitor.next_check_at if monitor else None,
                }
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
                    "source_onboarding": source_onboarding,
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
        source_certification_count=sum(
            1 for _, _, _, item in prepared
            if item["source_certification"] or item["source_onboarding"]
        ),
        source_onboarding_count=sum(1 for _, _, _, item in prepared if item["source_onboarding"]),
        status="submitted_for_review",
        submitted_by=actor,
    )
    session.add(batch)
    session.flush()

    try:
        for row_number, entry, jurisdiction, item in prepared:
            assessment = None
            certification = None
            authority = None
            source = None
            monitor = None
            if item["source_onboarding"]:
                onboarding = dict(item["source_onboarding"])
                certification_scope = onboarding.pop("certification_scope", "primary_immigration")
                certification_domains = onboarding.pop("certification_domains")
                evidence_notes = onboarding.pop("evidence_notes")
                onboarding_request = RegulatorySourceOnboardingRequest(
                    jurisdiction_code=entry.alpha2_code,
                    jurisdiction_name=entry.canonical_name,
                    jurisdiction_type=entry.jurisdiction_type,
                    parent_code=entry.parent_code,
                    region=entry.region,
                    **onboarding,
                )
                onboarded_jurisdiction, authority, source, monitor = onboard_regulatory_source(
                    session,
                    onboarding_request,
                    actor=actor,
                    commit=False,
                )
                if onboarded_jurisdiction.id != jurisdiction.id:
                    raise ValueError(
                        f"Source onboarding for {entry.alpha2_code} resolved to a different jurisdiction"
                    )
            if item["immigration_assessment"]:
                assessment_input = dict(item["immigration_assessment"])
                if source is not None:
                    supplied_source_id = assessment_input.get("official_source_id")
                    if supplied_source_id not in (None, source.id):
                        raise ValueError(
                            f"Immigration assessment source for {entry.alpha2_code} does not match the onboarded source"
                        )
                    assessment_input["official_source_id"] = source.id
                assessment = propose_immigration_assessment(
                    session,
                    jurisdiction_id=jurisdiction.id,
                    actor=actor,
                    commit=False,
                    **assessment_input,
                )
            if source is not None and authority is not None:
                certification = propose_source_certification(
                    session,
                    jurisdiction_id=jurisdiction.id,
                    regulatory_authority_id=authority.id,
                    official_source_id=source.id,
                    coverage_domains=certification_domains,
                    evidence_notes=evidence_notes,
                    certification_scope=certification_scope,
                    actor=actor,
                    commit=False,
                )
            elif item["source_certification"]:
                certification = propose_source_certification(
                    session,
                    jurisdiction_id=jurisdiction.id,
                    actor=actor,
                    commit=False,
                    **item["source_certification"],
                )

                # Certification-only batches reference an already-onboarded
                # official source. Resolve its existing governed linkage so
                # the batch item does not persist null denormalized IDs.
                authority = session.get(
                    RegulatoryAuthority,
                    certification.regulatory_authority_id,
                )
                source = session.get(
                    OfficialSource,
                    certification.official_source_id,
                )

                if (
                    authority is None
                    or not authority.active
                    or authority.jurisdiction_id != jurisdiction.id
                ):
                    raise ValueError(
                        f"Certified authority for {entry.alpha2_code} is not active "
                        "in the batch jurisdiction"
                    )

                if (
                    source is None
                    or not source.active
                    or source.jurisdiction_id != jurisdiction.id
                ):
                    raise ValueError(
                        f"Certified source for {entry.alpha2_code} is not active "
                        "in the batch jurisdiction"
                    )

                if source.regulatory_authority_id != authority.id:
                    raise ValueError(
                        f"Certified source for {entry.alpha2_code} is not attached "
                        "to the certified regulatory authority"
                    )

                monitor = session.exec(
                    select(SourceMonitor).where(
                        SourceMonitor.official_source_id == source.id
                    )
                ).first()
            if (
                assessment is None
                and certification is not None
                and certification.certification_scope.startswith("supplemental_")
            ):
                assessment = session.exec(
                    select(JurisdictionImmigrationAssessment)
                    .where(JurisdictionImmigrationAssessment.jurisdiction_id == jurisdiction.id)
                    .where(JurisdictionImmigrationAssessment.status == "approved")
                    .order_by(JurisdictionImmigrationAssessment.assessment_version.desc())
                ).first()
                if assessment is None:
                    raise ValueError(
                        f"Supplemental source onboarding for {entry.alpha2_code} requires an approved immigration assessment"
                    )
            item_payload = {
                "alpha2_code": item["alpha2_code"],
                "immigration_assessment": item["immigration_assessment"],
                "source_certification": item["source_certification"],
                "source_onboarding": item["source_onboarding"],
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
                    regulatory_authority_id=authority.id if authority else None,
                    official_source_id=source.id if source else None,
                    source_monitor_id=monitor.id if monitor else None,
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
                "source_onboarding_count": batch.source_onboarding_count,
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
