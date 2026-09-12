from __future__ import annotations

from datetime import timedelta

from sqlmodel import select

from app.models.domain import (
    AuditLog,
    Jurisdiction,
    MobilityPathway,
    OfficialSource,
    RegulatoryChange,
    SourceSnapshot,
    VerifiedRule,
    now_utc,
)
from app.services.audit_log import record_audit
from app.services.regulatory_freshness_guard import (
    FRESHNESS_ACTION,
    assess_regulatory_freshness,
    scan_regulatory_freshness,
)
from app.services.regulatory_promotion_policy import PROMOTION_ACTION, PROMOTION_POLICY_VERSION


def _seed_shadow_promoted_candidate(db_session, *, source_active: bool = True):
    jurisdiction = Jurisdiction(code="AT-RIA8", name="Austria RI.A8")
    db_session.add(jurisdiction)
    db_session.flush()

    source = OfficialSource(
        jurisdiction_id=jurisdiction.id,
        country="Austria",
        domain="work",
        name="Austrian immigration authority RI.A8",
        url="https://example.gv.at/ria8/programs",
        active=source_active,
    )
    db_session.add(source)
    db_session.flush()

    captured_at = now_utc() - timedelta(hours=1)
    snapshot = SourceSnapshot(
        official_source_id=source.id,
        url=source.url,
        content_hash="d" * 64,
        status="changed",
        parser_version="structured-program-catalog-v1",
        captured_at=captured_at,
        metadata_json="{}",
    )
    db_session.add(snapshot)
    db_session.flush()

    change = RegulatoryChange(
        jurisdiction_id=jurisdiction.id,
        official_source_id=source.id,
        current_snapshot_id=snapshot.id,
        domain="work",
        change_type="new_program",
        title="New deterministic route",
        summary="Certified deterministic candidate.",
        materiality="medium",
        status="pending_review",
        detected_at=now_utc(),
    )
    db_session.add(change)
    db_session.flush()

    promotion = record_audit(
        db_session,
        action=PROMOTION_ACTION,
        entity_type="regulatory_change",
        entity_id=change.id,
        after_state={
            "regulatory_change_id": str(change.id),
            "promotion_policy_version": PROMOTION_POLICY_VERSION,
            "shadow_mode": True,
            "compiler_audit_id": "pytest-compiler",
            "discovery_audit_id": "pytest-discovery",
            "source_snapshot_id": str(snapshot.id),
            "source_snapshot_content_hash": snapshot.content_hash,
            "candidates": [
                {
                    "candidate_key": f"{jurisdiction.id}:{source.id}:talent",
                    "program_id": "talent",
                    "outcome": "shadow_eligible",
                    "shadow_promotion_eligible": True,
                    "reasons": [],
                    "typed_rule_keys": ["minimum_salary"],
                    "publication_allowed": False,
                    "pathway_write_allowed": False,
                    "verified_rule_write_allowed": False,
                    "canonical_write_allowed": False,
                }
            ],
            "publication_writes_allowed": False,
            "pathway_writes_allowed": False,
            "verified_rule_writes_allowed": False,
            "canonical_write_allowed": False,
            "reasons": [],
        },
        actor="pytest-promotion",
        source=PROMOTION_POLICY_VERSION,
    )
    db_session.commit()
    return source, snapshot, change, promotion


def _add_newer_snapshot(db_session, source, current, *, content_hash: str):
    newer = SourceSnapshot(
        official_source_id=source.id,
        previous_snapshot_id=current.id,
        url=source.url,
        content_hash=content_hash,
        status="changed",
        parser_version="structured-program-catalog-v1",
        captured_at=current.captured_at + timedelta(minutes=30),
        metadata_json="{}",
    )
    db_session.add(newer)
    db_session.commit()
    return newer


def test_ri_a8_current_shadow_candidate_is_fresh_and_non_authoritative(db_session) -> None:
    _, snapshot, change, promotion = _seed_shadow_promoted_candidate(db_session)

    assessment = assess_regulatory_freshness(db_session, change)

    assert assessment.promotion_audit_id == str(promotion.id)
    assert assessment.source_snapshot_id == str(snapshot.id)
    assert assessment.latest_snapshot_id == str(snapshot.id)
    assert assessment.freshness_status == "fresh"
    assert assessment.quarantine_required is False
    assert assessment.shadow_eligibility_revoked is False
    assert assessment.rollback_reference_snapshot_id == str(snapshot.id)
    assert assessment.rollback_reference_snapshot_content_hash == snapshot.content_hash
    assert assessment.canonical_write_allowed is False


def test_ri_a8_newer_equivalent_snapshot_keeps_candidate_fresh(db_session) -> None:
    source, snapshot, change, _ = _seed_shadow_promoted_candidate(db_session)
    newer = _add_newer_snapshot(db_session, source, snapshot, content_hash=snapshot.content_hash)

    assessment = assess_regulatory_freshness(db_session, change)

    assert assessment.latest_snapshot_id == str(newer.id)
    assert assessment.freshness_status == "fresh_equivalent"
    assert assessment.quarantine_required is False
    assert assessment.shadow_eligibility_revoked is False


def test_ri_a8_newer_changed_snapshot_quarantines_and_revokes_shadow_eligibility(db_session) -> None:
    source, snapshot, change, _ = _seed_shadow_promoted_candidate(db_session)
    newer = _add_newer_snapshot(db_session, source, snapshot, content_hash="e" * 64)

    assessment = assess_regulatory_freshness(db_session, change)

    assert assessment.latest_snapshot_id == str(newer.id)
    assert assessment.freshness_status == "quarantined"
    assert assessment.quarantine_required is True
    assert assessment.shadow_eligibility_revoked is True
    assert "newer_snapshot_content_drift" in assessment.reasons
    assert assessment.rollback_reference_snapshot_id == str(snapshot.id)
    assert assessment.canonical_write_allowed is False


def test_ri_a8_inactive_official_source_quarantines_candidate(db_session) -> None:
    _, _, change, _ = _seed_shadow_promoted_candidate(db_session, source_active=False)

    assessment = assess_regulatory_freshness(db_session, change)

    assert assessment.source_active is False
    assert assessment.quarantine_required is True
    assert assessment.shadow_eligibility_revoked is True
    assert "official_source_inactive" in assessment.reasons


def test_ri_a8_scan_is_idempotent_and_never_rolls_back_canonical_truth(db_session) -> None:
    source, snapshot, change, _ = _seed_shadow_promoted_candidate(db_session)
    _add_newer_snapshot(db_session, source, snapshot, content_hash="f" * 64)
    before_rules = len(db_session.exec(select(VerifiedRule)).all())
    before_pathways = len(db_session.exec(select(MobilityPathway)).all())

    first = scan_regulatory_freshness(db_session)
    second = scan_regulatory_freshness(db_session)

    audits = db_session.exec(
        select(AuditLog)
        .where(AuditLog.action == FRESHNESS_ACTION)
        .where(AuditLog.entity_type == "regulatory_change")
        .where(AuditLog.entity_id == str(change.id))
    ).all()

    assert first["quarantined"] == 1
    assert first["shadow_eligibility_revocations"] == 1
    assert first["rollback_writes"] == 0
    assert first["publication_writes"] == 0
    assert first["pathway_writes"] == 0
    assert first["verified_rule_writes"] == 0
    assert first["canonical_writes"] == 0
    assert first["audit_writes"] == 1
    assert second["audit_writes"] == 0
    assert len(audits) == 1
    assert len(db_session.exec(select(VerifiedRule)).all()) == before_rules == 0
    assert len(db_session.exec(select(MobilityPathway)).all()) == before_pathways == 0

    db_session.refresh(change)
    assert change.status == "pending_review"
    assert change.reviewed_at is None
    assert change.published_at is None
