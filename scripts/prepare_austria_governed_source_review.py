#!/usr/bin/env python3
"""Prepare Austria 2026 governed source evidence for independent human review.

This operator composes existing production governance services. It may onboard
official sources, retrieve immutable snapshots, materialize deterministic 2026
shortage-occupation projections, submit the primary coverage evidence for
independent review, and create the canonical Austria pathway as a draft.

It deliberately does not approve reviews, publish verified rules or pathways,
create Live Organization objectives, invoke an LLM/provider, or authorize an
external action.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
API_PATH = ROOT / "apps" / "api"
if str(API_PATH) not in sys.path:
    sys.path.insert(0, str(API_PATH))

from sqlmodel import Session, select  # noqa: E402

from app.core.db import engine, register_models  # noqa: E402
from app.models.domain import (  # noqa: E402
    Jurisdiction,
    JurisdictionCoverageEvidenceBatchItem,
    JurisdictionImmigrationAssessment,
    JurisdictionRegistryEntry,
    JurisdictionRegistryRelease,
    JurisdictionSourceCertification,
    MobilityPathway,
    OfficialSource,
    SourceMonitor,
    SourceSnapshot,
)
from app.schemas import (  # noqa: E402
    PathwayCreate,
    PathwayVersionEvidenceInput,
    RegulatorySourceOnboardingRequest,
    ShortageOccupationMaterializeRequest,
)
from app.services.coverage_evidence_batches import (  # noqa: E402
    coverage_batch_payload,
    create_coverage_evidence_batch,
)
from app.services.pathway_catalogue import (  # noqa: E402
    STRUCTURED_OCCUPATION_PROJECTION_TYPE,
    create_pathway,
    latest_pathway_version,
    pathway_publication_readiness,
)
from app.services.pathway_evidence import pathway_version_evidence_rows  # noqa: E402
from app.services.regulatory_intelligence import onboard_regulatory_source  # noqa: E402
from app.services.shortage_occupations import (  # noqa: E402
    EXTRACTION_VERSION,
    materialize_shortage_occupation_snapshot,
    shortage_occupation_projection_summary,
)
from app.services.source_retrieval import execute_source_monitor  # noqa: E402


CONTRACT_VERSION = "austria-governed-source-review-preparation-cli.v1"
PATHWAY_KEY = "at-rwr-skilled-worker-shortage-occupation"
YEAR = 2026
EXPECTED_NATIONAL_GROUPS = 64
EXPECTED_REGIONAL_GROUPS = 66
ACTOR_DEFAULT = "austria-governed-source-review-preparer"

AUTHORITY_NAME = (
    "Federal Ministry of Labour, Social Affairs, Health, Care and Consumer Protection"
)
AUTHORITY_TYPE = "federal_ministry"
AUTHORITY_WEBSITE_URL = "https://www.sozialministerium.gv.at/"

NATIONAL_URL = (
    "https://www.migration.gv.at/en/types-of-immigration/permanent-immigration/"
    "austria-wide-shortage-occupations/"
)
REGIONAL_URL = (
    "https://www.migration.gv.at/en/types-of-immigration/permanent-immigration/"
    "regional-shortage-occupations/"
)
SOURCE_SPECS = {
    "national": {
        "name": "Migration.gv.at - Austria-wide shortage occupations",
        "url": NATIONAL_URL,
    },
    "regional": {
        "name": "Migration.gv.at - Regional shortage occupations",
        "url": REGIONAL_URL,
    },
}


class PreparationBlocked(RuntimeError):
    """Fail-closed operator preparation blocker."""


def _registry_context(
    session: Session,
) -> tuple[JurisdictionRegistryRelease, JurisdictionRegistryEntry, Jurisdiction]:
    release = session.exec(
        select(JurisdictionRegistryRelease).where(
            JurisdictionRegistryRelease.status == "active"
        )
    ).first()
    if release is None:
        raise PreparationBlocked("active_jurisdiction_registry_release_missing")
    entry = session.exec(
        select(JurisdictionRegistryEntry).where(
            JurisdictionRegistryEntry.registry_release_id == release.id,
            JurisdictionRegistryEntry.alpha2_code == "AT",
        )
    ).first()
    if entry is None:
        raise PreparationBlocked("austria_registry_entry_missing")
    jurisdiction = session.get(Jurisdiction, entry.jurisdiction_id)
    if jurisdiction is None or not jurisdiction.active:
        raise PreparationBlocked("austria_jurisdiction_missing_or_inactive")
    return release, entry, jurisdiction


def _source_by_url(session: Session, url: str) -> OfficialSource | None:
    return session.exec(
        select(OfficialSource).where(OfficialSource.url == url)
    ).first()


def _monitor_for_source(session: Session, source_id: UUID) -> SourceMonitor | None:
    return session.exec(
        select(SourceMonitor).where(SourceMonitor.official_source_id == source_id)
    ).first()


def _latest_snapshot(session: Session, source_id: UUID) -> SourceSnapshot | None:
    return session.exec(
        select(SourceSnapshot)
        .where(SourceSnapshot.official_source_id == source_id)
        .order_by(SourceSnapshot.captured_at.desc())
    ).first()


def _structured_link(
    summary: dict[str, Any],
    *,
    evidence_role: str,
) -> PathwayVersionEvidenceInput:
    return PathwayVersionEvidenceInput(
        evidence_role=evidence_role,
        official_source_id=summary["official_source_id"],
        source_snapshot_id=summary["source_snapshot_id"],
        required_for_publication=True,
        metadata={
            "projection_type": STRUCTURED_OCCUPATION_PROJECTION_TYPE,
            "year": summary["year"],
            "scope": summary["scope"],
            "entry_count": summary["entry_count"],
            "entry_set_sha256": summary["entry_set_sha256"],
            "extraction_version": summary["extraction_version"],
            "source_snapshot_content_hash": summary[
                "source_snapshot_content_hash"
            ],
        },
    )


def _onboarding_payload(
    *,
    entry: JurisdictionRegistryEntry,
    spec: dict[str, str],
) -> RegulatorySourceOnboardingRequest:
    return RegulatorySourceOnboardingRequest(
        jurisdiction_code=entry.alpha2_code,
        jurisdiction_name=entry.canonical_name,
        jurisdiction_type=entry.jurisdiction_type,
        parent_code=entry.parent_code,
        region=entry.region,
        authority_name=AUTHORITY_NAME,
        authority_type=AUTHORITY_TYPE,
        authority_website_url=AUTHORITY_WEBSITE_URL,
        authority_domains=["visa"],
        source_name=spec["name"],
        source_url=spec["url"],
        source_domain="visa",
        source_type="government",
        schedule_minutes=1440,
        fetch_method="http",
        allowed_domains=["migration.gv.at"],
        max_redirects=3,
        parser_profile="generic",
        parser_config={},
    )


def _ensure_sources(
    session: Session,
    *,
    entry: JurisdictionRegistryEntry,
    actor: str,
) -> dict[str, tuple[OfficialSource, SourceMonitor]]:
    resolved: dict[str, tuple[OfficialSource, SourceMonitor]] = {}
    authority_id: UUID | None = None
    for scope in ("national", "regional"):
        _, authority, source, monitor = onboard_regulatory_source(
            session,
            _onboarding_payload(entry=entry, spec=SOURCE_SPECS[scope]),
            actor=actor,
        )
        if authority_id is not None and authority.id != authority_id:
            raise PreparationBlocked("austria_source_authority_mismatch")
        authority_id = authority.id
        resolved[scope] = (source, monitor)
    return resolved


def _retrieve_snapshots(
    session: Session,
    *,
    sources: dict[str, tuple[OfficialSource, SourceMonitor]],
    retrieval_executor: Callable[..., Any],
) -> dict[str, SourceSnapshot]:
    snapshots: dict[str, SourceSnapshot] = {}
    for scope in ("national", "regional"):
        source, monitor = sources[scope]
        run = retrieval_executor(session, monitor.id)
        if getattr(run, "status", None) not in {
            "baseline",
            "unchanged",
            "changed",
            "not_modified",
        }:
            raise PreparationBlocked(
                f"{scope}_source_retrieval_not_successful:"
                f"{getattr(run, 'status', None)}"
            )
        snapshot = _latest_snapshot(session, source.id)
        if snapshot is None or not snapshot.content_hash or not snapshot.content_text:
            raise PreparationBlocked(f"{scope}_immutable_snapshot_missing")
        snapshots[scope] = snapshot
    return snapshots


def _materialize(
    session: Session,
    *,
    snapshots: dict[str, SourceSnapshot],
    actor: str,
    expected_national_group_count: int,
    expected_regional_group_count: int,
) -> dict[str, dict[str, Any]]:
    counts = {
        "national": expected_national_group_count,
        "regional": expected_regional_group_count,
    }
    summaries: dict[str, dict[str, Any]] = {}
    for scope in ("national", "regional"):
        snapshot = snapshots[scope]
        materialize_shortage_occupation_snapshot(
            session,
            ShortageOccupationMaterializeRequest(
                source_snapshot_id=snapshot.id,
                year=YEAR,
                scope=scope,
                expected_group_count=counts[scope],
                parser_profile=EXTRACTION_VERSION,
            ),
            actor=actor,
        )
        summaries[scope] = shortage_occupation_projection_summary(
            session,
            source_snapshot_id=snapshot.id,
            year=YEAR,
            scope=scope,
        )
    return summaries


def _ensure_primary_review_batch(
    session: Session,
    *,
    national_source: OfficialSource,
    national_monitor: SourceMonitor,
    national_snapshot: SourceSnapshot,
    actor: str,
) -> tuple[Any, bool]:
    if national_source.regulatory_authority_id is None:
        raise PreparationBlocked("national_source_authority_missing")
    item = {
        "alpha2_code": "AT",
        "immigration_assessment": {
            "rule_relationship": "independent",
            "parent_code": None,
            "evidence_url": national_source.url,
            "evidence_title": (
                "Migration.gv.at - Austria-wide shortage occupations 2026"
            ),
            "rationale": (
                "Austria is assessed as an independent immigration jurisdiction. "
                "The immutable migration.gv.at baseline is pinned for independent "
                "human review before any coverage claim or rule publication."
            ),
            "official_source_id": national_source.id,
            "source_snapshot_id": national_snapshot.id,
        },
        "source_certification": {
            "regulatory_authority_id": national_source.regulatory_authority_id,
            "official_source_id": national_source.id,
            "coverage_domains": ["visa"],
            "evidence_notes": (
                "Primary Austrian migration source proposal for the governed 2026 "
                "shortage-occupation pathway. Independent human certification is "
                "required."
            ),
            "certification_scope": "primary_immigration",
        },
    }
    batch, created = create_coverage_evidence_batch(
        session,
        name="Austria 2026 shortage-occupation primary source review",
        notes=(
            "Prepare the primary migration.gv.at authority/source relationship and "
            "immigration-rule relationship for independent human review. No "
            "approval or coverage claim is created by this batch."
        ),
        items=[item],
        actor=actor,
    )
    payload = coverage_batch_payload(session, batch, include_items=True)
    items = payload.get("items") or []
    if len(items) != 1:
        raise PreparationBlocked("austria_primary_review_batch_item_invalid")
    batch_item = session.get(JurisdictionCoverageEvidenceBatchItem, items[0]["id"])
    if batch_item is None:
        raise PreparationBlocked("austria_primary_review_batch_item_missing")
    if batch_item.official_source_id != national_source.id:
        raise PreparationBlocked("austria_primary_review_batch_source_mismatch")
    if batch_item.source_monitor_id != national_monitor.id:
        raise PreparationBlocked("austria_primary_review_batch_monitor_mismatch")
    return batch, created


def _expected_evidence_identity(
    summaries: dict[str, dict[str, Any]],
) -> dict[str, tuple[UUID, UUID]]:
    return {
        "core_route": (
            summaries["national"]["official_source_id"],
            summaries["national"]["source_snapshot_id"],
        ),
        "national_occupation_list": (
            summaries["national"]["official_source_id"],
            summaries["national"]["source_snapshot_id"],
        ),
        "regional_occupation_list": (
            summaries["regional"]["official_source_id"],
            summaries["regional"]["source_snapshot_id"],
        ),
    }


def _validate_existing_pathway(
    session: Session,
    pathway: MobilityPathway,
    summaries: dict[str, dict[str, Any]],
):
    version = latest_pathway_version(session, pathway.id)
    if version is None:
        raise PreparationBlocked("canonical_pathway_has_no_version")
    expected = _expected_evidence_identity(summaries)
    actual = {
        row.evidence_role: (row.official_source_id, row.source_snapshot_id)
        for row in pathway_version_evidence_rows(session, version)
    }
    for role, identity in expected.items():
        if actual.get(role) != identity:
            raise PreparationBlocked(
                f"canonical_pathway_existing_evidence_mismatch:{role}"
            )
    return version


def _ensure_pathway(
    session: Session,
    *,
    jurisdiction: Jurisdiction,
    summaries: dict[str, dict[str, Any]],
    actor: str,
):
    existing = session.exec(
        select(MobilityPathway).where(MobilityPathway.pathway_key == PATHWAY_KEY)
    ).first()
    if existing is not None:
        if existing.jurisdiction_id not in (None, jurisdiction.id):
            raise PreparationBlocked("canonical_pathway_jurisdiction_mismatch")
        return existing, _validate_existing_pathway(session, existing, summaries), False

    national = summaries["national"]
    regional = summaries["regional"]
    pathway, version = create_pathway(
        session,
        PathwayCreate(
            pathway_key=PATHWAY_KEY,
            name=(
                "Austria Red-White-Red Card - Skilled Workers in Shortage "
                "Occupations"
            ),
            country="austria",
            domain="visa",
            jurisdiction_id=jurisdiction.id,
            description=(
                "Governed Austrian Red-White-Red Card pathway for skilled workers "
                "in the official 2026 national or regional shortage-occupation "
                "lists."
            ),
            official_source_id=national["official_source_id"],
            source_snapshot_id=national["source_snapshot_id"],
            evidence_links=[
                _structured_link(
                    national,
                    evidence_role="national_occupation_list",
                ),
                _structured_link(
                    regional,
                    evidence_role="regional_occupation_list",
                ),
            ],
            verified_rule_ids=[],
            eligibility_criteria={},
            required_documents=[],
            costs={},
            processing_time={},
            benefits=[],
            risks=[],
            metadata={
                "preparation_contract": CONTRACT_VERSION,
                "year": YEAR,
                "independent_human_review_required": True,
                "source_scope": "migration.gv.at shortage occupations",
            },
        ),
        actor=actor,
    )
    return pathway, version, True


def _review_records(
    session: Session,
    *,
    jurisdiction_id: UUID | None,
    national_source_id: UUID | None,
) -> dict[str, Any]:
    assessment = None
    if jurisdiction_id is not None:
        assessment = session.exec(
            select(JurisdictionImmigrationAssessment)
            .where(
                JurisdictionImmigrationAssessment.jurisdiction_id
                == jurisdiction_id
            )
            .order_by(
                JurisdictionImmigrationAssessment.assessment_version.desc()
            )
        ).first()
    certification = None
    if national_source_id is not None:
        certification = session.exec(
            select(JurisdictionSourceCertification)
            .where(
                JurisdictionSourceCertification.official_source_id
                == national_source_id
            )
            .order_by(
                JurisdictionSourceCertification.certification_version.desc()
            )
        ).first()
    return {
        "immigration_assessment_id": str(assessment.id) if assessment else None,
        "immigration_assessment_status": assessment.status if assessment else None,
        "primary_source_certification_id": (
            str(certification.id) if certification else None
        ),
        "primary_source_certification_status": (
            certification.status if certification else None
        ),
    }


def assess_review_preparation(session: Session) -> dict[str, Any]:
    blockers: list[str] = []
    release = entry = jurisdiction = None
    try:
        release, entry, jurisdiction = _registry_context(session)
    except PreparationBlocked as exc:
        blockers.append(str(exc))

    source_payload: dict[str, Any] = {}
    summaries: dict[str, dict[str, Any]] = {}
    expected_counts = {
        "national": EXPECTED_NATIONAL_GROUPS,
        "regional": EXPECTED_REGIONAL_GROUPS,
    }
    for scope in ("national", "regional"):
        spec = SOURCE_SPECS[scope]
        source = _source_by_url(session, spec["url"])
        monitor = _monitor_for_source(session, source.id) if source else None
        snapshot = _latest_snapshot(session, source.id) if source else None
        summary = None
        if snapshot is not None:
            try:
                summary = shortage_occupation_projection_summary(
                    session,
                    source_snapshot_id=snapshot.id,
                    year=YEAR,
                    scope=scope,
                )
            except ValueError:
                summary = None
        if source is None:
            blockers.append(f"{scope}_official_source_missing")
        if monitor is None:
            blockers.append(f"{scope}_source_monitor_missing")
        elif (monitor.status or "").strip().casefold() != "active":
            blockers.append(f"{scope}_source_monitor_inactive")
        if snapshot is None:
            blockers.append(f"{scope}_immutable_snapshot_missing")
        if summary is None:
            blockers.append(f"{scope}_structured_projection_missing")
        else:
            summaries[scope] = summary
            if summary["entry_count"] != expected_counts[scope]:
                blockers.append(
                    f"{scope}_structured_projection_count_unexpected:"
                    f"{summary['entry_count']}"
                )
        source_payload[scope] = {
            "official_source_id": str(source.id) if source else None,
            "source_monitor_id": str(monitor.id) if monitor else None,
            "monitor_status": monitor.status if monitor else None,
            "source_snapshot_id": str(snapshot.id) if snapshot else None,
            "entry_count": summary["entry_count"] if summary else 0,
            "entry_set_sha256": summary["entry_set_sha256"] if summary else None,
        }

    pathway = session.exec(
        select(MobilityPathway).where(MobilityPathway.pathway_key == PATHWAY_KEY)
    ).first()
    version = latest_pathway_version(session, pathway.id) if pathway else None
    readiness = None
    if pathway is None:
        blockers.append("canonical_pathway_missing")
    elif version is None:
        blockers.append("canonical_pathway_has_no_version")
    else:
        readiness = pathway_publication_readiness(session, version.id)

    national_source = _source_by_url(session, NATIONAL_URL)
    reviews = _review_records(
        session,
        jurisdiction_id=jurisdiction.id if jurisdiction else None,
        national_source_id=national_source.id if national_source else None,
    )
    if reviews["immigration_assessment_id"] is None:
        blockers.append("austria_immigration_assessment_review_record_missing")
    if reviews["primary_source_certification_id"] is None:
        blockers.append("austria_primary_source_certification_review_record_missing")

    prepared = not blockers
    return {
        "contract_version": CONTRACT_VERSION,
        "mode": "check",
        "year": YEAR,
        "route_key": PATHWAY_KEY,
        "registry_release_id": str(release.id) if release else None,
        "registry_release_version": release.version if release else None,
        "austria_registry_entry_id": str(entry.id) if entry else None,
        "austria_jurisdiction_id": str(jurisdiction.id) if jurisdiction else None,
        "sources": source_payload,
        "pathway_id": str(pathway.id) if pathway else None,
        "pathway_status": pathway.catalogue_status if pathway else None,
        "pathway_version_id": str(version.id) if version else None,
        "pathway_version_number": version.version_number if version else None,
        "pathway_version_status": version.lifecycle_status if version else None,
        "pathway_publication_ready": readiness.ready if readiness else False,
        "pathway_publication_blockers": readiness.blockers if readiness else [],
        **reviews,
        "prepared_for_independent_human_review": prepared,
        "professional_review_required": True,
        "provider_invoked": False,
        "external_action_authorized": False,
        "pathway_published_by_this_operation": False,
        "verified_rule_published_by_this_operation": False,
        "secrets_exposed": False,
        "blockers": blockers,
    }


def prepare_review_state(
    session: Session,
    *,
    actor: str = ACTOR_DEFAULT,
    expected_national_group_count: int = EXPECTED_NATIONAL_GROUPS,
    expected_regional_group_count: int = EXPECTED_REGIONAL_GROUPS,
    retrieval_executor: Callable[..., Any] = execute_source_monitor,
) -> dict[str, Any]:
    _, entry, jurisdiction = _registry_context(session)
    sources = _ensure_sources(session, entry=entry, actor=actor)
    snapshots = _retrieve_snapshots(
        session,
        sources=sources,
        retrieval_executor=retrieval_executor,
    )
    summaries = _materialize(
        session,
        snapshots=snapshots,
        actor=actor,
        expected_national_group_count=expected_national_group_count,
        expected_regional_group_count=expected_regional_group_count,
    )
    batch, batch_created = _ensure_primary_review_batch(
        session,
        national_source=sources["national"][0],
        national_monitor=sources["national"][1],
        national_snapshot=snapshots["national"],
        actor=actor,
    )
    pathway, version, pathway_created = _ensure_pathway(
        session,
        jurisdiction=jurisdiction,
        summaries=summaries,
        actor=actor,
    )
    readiness = pathway_publication_readiness(session, version.id)
    reviews = _review_records(
        session,
        jurisdiction_id=jurisdiction.id,
        national_source_id=sources["national"][0].id,
    )
    return {
        "contract_version": CONTRACT_VERSION,
        "mode": "prepare-review",
        "year": YEAR,
        "route_key": PATHWAY_KEY,
        "expected_group_counts": {
            "national": expected_national_group_count,
            "regional": expected_regional_group_count,
        },
        "sources": {
            scope: {
                "official_source_id": str(sources[scope][0].id),
                "source_monitor_id": str(sources[scope][1].id),
                "source_snapshot_id": str(snapshots[scope].id),
                "entry_count": summaries[scope]["entry_count"],
                "entry_set_sha256": summaries[scope]["entry_set_sha256"],
                "source_snapshot_content_hash": summaries[scope][
                    "source_snapshot_content_hash"
                ],
            }
            for scope in ("national", "regional")
        },
        "coverage_batch_id": str(batch.id),
        "coverage_batch_created": batch_created,
        "pathway_id": str(pathway.id),
        "pathway_created": pathway_created,
        "pathway_status": pathway.catalogue_status,
        "pathway_version_id": str(version.id),
        "pathway_version_number": version.version_number,
        "pathway_version_status": version.lifecycle_status,
        "pathway_publication_ready": readiness.ready,
        "pathway_publication_blockers": readiness.blockers,
        "evidence_certification_statuses": (
            readiness.evidence_certification_statuses
        ),
        **reviews,
        "prepared_for_independent_human_review": True,
        "professional_review_required": True,
        "regional_source_certification_deferred_until_primary_approved": True,
        "provider_invoked": False,
        "external_action_authorized": False,
        "pathway_published_by_this_operation": False,
        "verified_rule_published_by_this_operation": False,
        "secrets_exposed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare the governed Austria 2026 shortage-occupation source lineage "
            "for independent human review without approving or publishing it."
        )
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--prepare-review", action="store_true")
    parser.add_argument("--actor", default=ACTOR_DEFAULT)
    parser.add_argument(
        "--expected-national-group-count",
        type=int,
        default=EXPECTED_NATIONAL_GROUPS,
    )
    parser.add_argument(
        "--expected-regional-group-count",
        type=int,
        default=EXPECTED_REGIONAL_GROUPS,
    )
    args = parser.parse_args()

    register_models()
    try:
        with Session(engine) as session:
            if args.check:
                result = assess_review_preparation(session)
                print(json.dumps(result, indent=2, sort_keys=True))
                return (
                    0
                    if result["prepared_for_independent_human_review"]
                    else 2
                )
            result = prepare_review_state(
                session,
                actor=args.actor,
                expected_national_group_count=args.expected_national_group_count,
                expected_regional_group_count=args.expected_regional_group_count,
            )
    except (PreparationBlocked, ValueError, RuntimeError) as exc:
        print(
            json.dumps(
                {
                    "contract_version": CONTRACT_VERSION,
                    "mode": (
                        "prepare-review" if args.prepare_review else "check"
                    ),
                    "prepared_for_independent_human_review": False,
                    "professional_review_required": True,
                    "provider_invoked": False,
                    "external_action_authorized": False,
                    "pathway_published_by_this_operation": False,
                    "verified_rule_published_by_this_operation": False,
                    "secrets_exposed": False,
                    "blockers": [str(exc)],
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 2

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
