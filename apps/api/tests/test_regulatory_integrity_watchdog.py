from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select

from app.models.domain import AuditLog, Jurisdiction, OfficialSource, RegulatoryChange, SourceSnapshot
from app.services.audit_log import record_audit
from app.services.regulatory_integrity_watchdog import (
    WATCHDOG_ACTION,
    evaluate_temporal_integrity,
    scan_regulatory_integrity,
)
from app.services.regulatory_machine_verification import VERIFICATION_ACTION, VERIFICATION_VERSION


def _verification_payload(change_id: str, *, added: list[str] | None = None, retired: list[str] | None = None) -> dict:
    return {
        "regulatory_change_id": change_id,
        "verification_version": VERIFICATION_VERSION,
        "verification_method": "snapshot-catalog-differential-v1",
        "verdict": "verified",
        "independently_verified": True,
        "canonical_write_allowed": False,
        "reasons": [],
        "evidence": {
            "catalog_differential": {
                "valid": True,
                "added_program_ids": added or [],
                "removed_program_ids": retired or [],
                "deactivated_program_ids": [],
                "reasons": [],
            }
        },
    }


def test_temporal_integrity_rejects_reversed_snapshot_chronology() -> None:
    now = datetime.now(timezone.utc)
    valid, reasons = evaluate_temporal_integrity(
        previous_captured_at=now,
        current_captured_at=now - timedelta(minutes=1),
        detected_at=now + timedelta(minutes=1),
    )

    assert valid is False
    assert "snapshot_capture_time_reversed" in reasons


def test_temporal_integrity_rejects_detection_before_current_capture() -> None:
    now = datetime.now(timezone.utc)
    valid, reasons = evaluate_temporal_integrity(
        previous_captured_at=now - timedelta(minutes=2),
        current_captured_at=now,
        detected_at=now - timedelta(minutes=1),
    )

    assert valid is False
    assert "change_detected_before_current_snapshot_capture" in reasons


def test_watchdog_detects_opposing_verified_program_states_and_is_idempotent(
    db_session: Session,
) -> None:
    jurisdiction = Jurisdiction(code="AT-RIA3", name="RI.A3 Test Jurisdiction")
    db_session.add(jurisdiction)
    db_session.commit()
    db_session.refresh(jurisdiction)

    source = OfficialSource(
        jurisdiction_id=jurisdiction.id,
        country="RI.A3 Test Jurisdiction",
        domain="visa",
        name="RI.A3 Official Program Catalog",
        url="https://example.invalid/ria3-programs.json",
    )
    db_session.add(source)
    db_session.commit()
    db_session.refresh(source)

    previous = SourceSnapshot(
        official_source_id=source.id,
        url=source.url,
        content_hash="sha256:ria3-previous",
        status="changed",
    )
    db_session.add(previous)
    db_session.commit()
    db_session.refresh(previous)

    current = SourceSnapshot(
        official_source_id=source.id,
        previous_snapshot_id=previous.id,
        url=source.url,
        content_hash="sha256:ria3-current",
        status="changed",
    )
    db_session.add(current)
    db_session.commit()
    db_session.refresh(current)

    added = RegulatoryChange(
        jurisdiction_id=jurisdiction.id,
        official_source_id=source.id,
        previous_snapshot_id=previous.id,
        current_snapshot_id=current.id,
        domain="visa",
        change_type="new_program",
        title="Talent route added",
        summary="Independent verification says talent is present.",
        materiality="medium",
        status="pending_review",
        detected_at=current.captured_at + timedelta(seconds=1),
    )
    retired = RegulatoryChange(
        jurisdiction_id=jurisdiction.id,
        official_source_id=source.id,
        previous_snapshot_id=previous.id,
        current_snapshot_id=current.id,
        domain="visa",
        change_type="program_removed",
        title="Talent route retired",
        summary="Independent verification says talent is retired.",
        materiality="medium",
        status="pending_review",
        detected_at=current.captured_at + timedelta(seconds=2),
    )
    db_session.add(added)
    db_session.add(retired)
    db_session.commit()
    db_session.refresh(added)
    db_session.refresh(retired)

    for change, payload in (
        (added, _verification_payload(str(added.id), added=["talent"])),
        (retired, _verification_payload(str(retired.id), retired=["talent"])),
    ):
        record_audit(
            db_session,
            action=VERIFICATION_ACTION,
            entity_type="regulatory_change",
            entity_id=change.id,
            after_state=payload,
            actor="pytest-verification-agent",
            source=VERIFICATION_VERSION,
        )
    db_session.commit()

    first = scan_regulatory_integrity(db_session)
    second = scan_regulatory_integrity(db_session)

    watchdog_audits = db_session.exec(
        select(AuditLog).where(AuditLog.action == WATCHDOG_ACTION)
    ).all()
    persisted_added = db_session.get(RegulatoryChange, added.id)
    persisted_retired = db_session.get(RegulatoryChange, retired.id)

    assert first["independently_verified_inputs"] == 2
    assert first["integrity_clear"] == 0
    assert first["integrity_exceptions"] == 2
    assert first["audit_writes"] == 2
    assert first["canonical_writes"] == 0
    assert second["audit_writes"] == 0
    assert second["canonical_writes"] == 0
    assert len(watchdog_audits) == 2
    assert all(
        "contradictory_independently_verified_program_state" in assessment["reasons"]
        for assessment in first["assessments"]
    )
    assert persisted_added is not None and persisted_added.status == "pending_review"
    assert persisted_retired is not None and persisted_retired.status == "pending_review"
    assert persisted_added.published_at is None
    assert persisted_retired.published_at is None
