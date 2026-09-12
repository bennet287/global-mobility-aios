from __future__ import annotations

import json

from sqlmodel import select

from app.models.domain import (
    AuditLog,
    Jurisdiction,
    MobilityPathway,
    MobilityPathwayVersion,
    OfficialSource,
    RegulatoryChange,
    SourceSnapshot,
    now_utc,
)
from app.services.audit_log import record_audit
from app.services.regulatory_integrity_watchdog import WATCHDOG_ACTION, WATCHDOG_VERSION
from app.services.regulatory_machine_verification import VERIFICATION_ACTION, VERIFICATION_VERSION
from app.services.regulatory_program_discovery import (
    DISCOVERY_ACTION,
    discover_new_program_candidates,
    discover_pathway_candidates,
)


def _program(program_id: str, name: str) -> dict:
    return {
        "program_id": program_id,
        "name": name,
        "status": "active",
        "active": True,
        "summary": "Official structured programme description.",
        "effective_date": "2026-10-01",
    }


def _seed_verified_new_program(db_session, *, watchdog_clear: bool = True):
    jurisdiction = Jurisdiction(code="AT", name="Austria")
    db_session.add(jurisdiction)
    db_session.flush()

    source = OfficialSource(
        jurisdiction_id=jurisdiction.id,
        country="Austria",
        domain="visa",
        name="Austrian immigration authority",
        url="https://example.gv.at/programs",
    )
    db_session.add(source)
    db_session.flush()

    snapshot = SourceSnapshot(
        official_source_id=source.id,
        url=source.url,
        content_hash="a" * 64,
        status="changed",
        parser_version="structured-program-catalog-v1",
        metadata_json=json.dumps(
            {
                "parser_profile": "structured_program_catalog_v1",
                "program_catalog": [_program("talent", "Global Talent Route")],
                "missing_means_retired": False,
            },
            sort_keys=True,
        ),
    )
    db_session.add(snapshot)
    db_session.flush()

    change = RegulatoryChange(
        jurisdiction_id=jurisdiction.id,
        official_source_id=source.id,
        current_snapshot_id=snapshot.id,
        domain="visa",
        change_type="new_program",
        title="New talent route",
        summary="The official source introduced a new talent route.",
        materiality="medium",
        status="pending_review",
        detected_at=now_utc(),
    )
    db_session.add(change)
    db_session.flush()

    verification = record_audit(
        db_session,
        action=VERIFICATION_ACTION,
        entity_type="regulatory_change",
        entity_id=change.id,
        after_state={
            "regulatory_change_id": str(change.id),
            "verification_version": VERIFICATION_VERSION,
            "verification_method": "snapshot-catalog-differential-v1",
            "verdict": "verified",
            "independently_verified": True,
            "canonical_write_allowed": False,
            "reasons": [],
            "evidence": {
                "current_snapshot_id": str(snapshot.id),
                "current_snapshot_content_hash": snapshot.content_hash,
                "catalog_differential": {
                    "valid": True,
                    "added_program_ids": ["talent"],
                    "removed_program_ids": [],
                    "deactivated_program_ids": [],
                    "reasons": [],
                },
            },
        },
        actor="pytest-verifier",
        source=VERIFICATION_VERSION,
    )
    db_session.flush()

    watchdog = record_audit(
        db_session,
        action=WATCHDOG_ACTION,
        entity_type="regulatory_change",
        entity_id=change.id,
        after_state={
            "regulatory_change_id": str(change.id),
            "watchdog_version": WATCHDOG_VERSION,
            "temporal_integrity": watchdog_clear,
            "contradiction_free": watchdog_clear,
            "eligible_for_future_promotion": watchdog_clear,
            "canonical_write_allowed": False,
            "reasons": [] if watchdog_clear else ["pytest_integrity_exception"],
            "conflicting_change_ids": [],
            "evidence": {"verification_audit_id": str(verification.id)},
        },
        actor="pytest-watchdog",
        source=WATCHDOG_VERSION,
    )
    db_session.commit()
    return jurisdiction, source, snapshot, change, verification, watchdog


def test_ri_a5_discovers_candidate_without_creating_pathway(db_session) -> None:
    _, _, snapshot, change, verification, watchdog = _seed_verified_new_program(db_session)
    before_pathways = len(db_session.exec(select(MobilityPathway)).all())

    packet = discover_pathway_candidates(db_session, change)

    assert len(packet.candidates) == 1
    candidate = packet.candidates[0]
    assert candidate.program_id == "talent"
    assert candidate.name == "Global Talent Route"
    assert candidate.candidate_only is True
    assert candidate.publication_allowed is False
    assert candidate.pathway_create_allowed is False
    assert candidate.canonical_write_allowed is False
    assert packet.source_snapshot_id == str(snapshot.id)
    assert packet.source_snapshot_content_hash == snapshot.content_hash
    assert packet.verification_audit_id == str(verification.id)
    assert packet.watchdog_audit_id == str(watchdog.id)
    assert packet.publication_allowed is False
    assert packet.pathway_create_allowed is False
    assert packet.canonical_write_allowed is False

    after_pathways = len(db_session.exec(select(MobilityPathway)).all())
    assert before_pathways == after_pathways == 0


def test_ri_a5_discovery_is_idempotent_and_audit_only(db_session) -> None:
    _, _, _, change, _, _ = _seed_verified_new_program(db_session)

    first = discover_new_program_candidates(db_session)
    second = discover_new_program_candidates(db_session)

    audits = db_session.exec(
        select(AuditLog)
        .where(AuditLog.action == DISCOVERY_ACTION)
        .where(AuditLog.entity_type == "regulatory_change")
        .where(AuditLog.entity_id == str(change.id))
    ).all()
    pathways = db_session.exec(select(MobilityPathway)).all()

    assert first["candidate_count"] == 1
    assert first["pathway_writes"] == 0
    assert first["publication_writes"] == 0
    assert first["canonical_writes"] == 0
    assert first["audit_writes"] == 1
    assert second["audit_writes"] == 0
    assert len(audits) == 1
    assert pathways == []

    db_session.refresh(change)
    assert change.status == "pending_review"
    assert change.reviewed_at is None
    assert change.published_at is None


def test_ri_a5_surfaces_existing_pathway_as_duplicate_signal(db_session) -> None:
    jurisdiction, source, _, change, _, _ = _seed_verified_new_program(db_session)
    pathway = MobilityPathway(
        pathway_key="at-global-talent",
        name="Global Talent Route",
        country="Austria",
        domain="work",
        jurisdiction_id=jurisdiction.id,
        catalogue_status="published",
    )
    db_session.add(pathway)
    db_session.flush()
    version = MobilityPathwayVersion(
        pathway_id=pathway.id,
        version_number=1,
        lifecycle_status="published",
        official_source_id=source.id,
        metadata_json=json.dumps({"source_program_id": "talent"}),
        approved_by="pytest-reviewer",
        published_at=now_utc(),
    )
    db_session.add(version)
    db_session.commit()

    packet = discover_pathway_candidates(db_session, change)

    assert len(packet.candidates) == 1
    assert packet.candidates[0].possible_existing_pathway_ids == (str(pathway.id),)
    assert packet.candidates[0].publication_allowed is False


def test_ri_a5_requires_integrity_clearance(db_session) -> None:
    _, _, _, change, _, _ = _seed_verified_new_program(db_session, watchdog_clear=False)

    packet = discover_pathway_candidates(db_session, change)
    result = discover_new_program_candidates(db_session)

    assert "regulatory_integrity_clearance_missing" in packet.reasons
    assert result["candidate_packets"] == 0
    assert result["audit_writes"] == 0
    assert db_session.exec(
        select(AuditLog).where(AuditLog.action == DISCOVERY_ACTION)
    ).all() == []
