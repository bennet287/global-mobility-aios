from __future__ import annotations

from types import SimpleNamespace

from sqlmodel import select

from app.models.domain import AuditLog, Jurisdiction, OfficialSource, RegulatoryChange, SourceSnapshot, VerifiedRule, now_utc
from app.services.audit_log import record_audit
from app.services.regulatory_authority_bridge import (
    BRIDGE_ACTION,
    BRIDGE_VERSION,
    assess_regulatory_authority_bridge,
    scan_regulatory_authority_bridge,
)
from app.services.regulatory_promotion_authorization import AUTHORIZATION_ACTION, AUTHORIZATION_VERSION


def _seed_authorization(db_session, *, evidence_ready: bool = True):
    jurisdiction = Jurisdiction(code="AT-RIA72", name="Austria RI.A7.2")
    db_session.add(jurisdiction)
    db_session.flush()
    source = OfficialSource(
        jurisdiction_id=jurisdiction.id,
        country="Austria",
        domain="work",
        name="Austrian immigration authority RI.A7.2",
        url="https://example.gv.at/ria72/programs",
    )
    db_session.add(source)
    db_session.flush()
    snapshot = SourceSnapshot(
        official_source_id=source.id,
        url=source.url,
        content_hash="e" * 64,
        status="changed",
        parser_version="structured-program-catalog-v1",
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
        title="Board-governed deterministic route",
        summary="RI.A7.2 authority bridge candidate.",
        materiality="medium",
        status="pending_review",
        detected_at=now_utc(),
    )
    db_session.add(change)
    db_session.flush()
    authorization = record_audit(
        db_session,
        action=AUTHORIZATION_ACTION,
        entity_type="regulatory_change",
        entity_id=change.id,
        after_state={
            "regulatory_change_id": str(change.id),
            "authorization_version": AUTHORIZATION_VERSION,
            "authorization_state": "evidence_ready_authority_missing" if evidence_ready else "quarantined",
            "evidence_ready": evidence_ready,
            "execution_authority": False,
            "verified_rule_writes_allowed": False,
            "pathway_writes_allowed": False,
            "publication_writes_allowed": False,
            "canonical_write_allowed": False,
        },
        actor="pytest-authorization",
        source=AUTHORIZATION_VERSION,
    )
    db_session.commit()
    return change, authorization


def _profile(*, autonomy="A4", authority="deterministic_verified_rule_publication", risk="R4"):
    revision = SimpleNamespace(
        profile_sequence=1,
        autonomy_level=autonomy,
        board_ceiling="A4",
        authority_requirement=authority,
        risk_ceiling=risk,
        governance_source="human_board",
    )
    return SimpleNamespace(current_profile_id="board-profile-1", revisions=(revision,))


def test_ri_a72_missing_board_delegation_is_fail_closed(db_session) -> None:
    change, _ = _seed_authorization(db_session)

    assessment = assess_regulatory_authority_bridge(db_session, change)

    assert assessment.bridge_version == BRIDGE_VERSION
    assert assessment.evidence_ready is True
    assert assessment.board_delegation_valid is False
    assert assessment.execution_bridge_enabled is False
    assert assessment.execution_authority is False
    assert assessment.bridge_state == "board_delegation_required"
    assert "board_autonomy_profile_missing" in assessment.reasons
    assert assessment.canonical_write_allowed is False


def test_ri_a72_valid_board_delegation_still_cannot_execute(db_session, monkeypatch) -> None:
    change, authorization = _seed_authorization(db_session)
    monkeypatch.setattr(
        "app.services.regulatory_authority_bridge.capability_autonomy_profile_snapshot",
        lambda *args, **kwargs: _profile(),
    )

    assessment = assess_regulatory_authority_bridge(db_session, change)

    assert assessment.authorization_audit_id == str(authorization.id)
    assert assessment.board_delegation_valid is True
    assert assessment.bridge_state == "delegation_ready_execution_adapter_missing"
    assert assessment.autonomy_level == "A4"
    assert assessment.risk_ceiling == "R4"
    assert assessment.execution_bridge_enabled is False
    assert assessment.execution_authority is False
    assert assessment.canonical_write_allowed is False


def test_ri_a72_wrong_authority_or_low_autonomy_is_rejected(db_session, monkeypatch) -> None:
    change, _ = _seed_authorization(db_session)
    monkeypatch.setattr(
        "app.services.regulatory_authority_bridge.capability_autonomy_profile_snapshot",
        lambda *args, **kwargs: _profile(autonomy="A3", authority="human_review_required"),
    )

    assessment = assess_regulatory_authority_bridge(db_session, change)

    assert assessment.board_delegation_valid is False
    assert "autonomy_level_below_machine_publication_threshold" in assessment.reasons
    assert "authority_requirement_mismatch" in assessment.reasons
    assert assessment.execution_authority is False


def test_ri_a72_quarantined_authorization_cannot_be_rescued_by_board_profile(db_session, monkeypatch) -> None:
    change, _ = _seed_authorization(db_session, evidence_ready=False)
    monkeypatch.setattr(
        "app.services.regulatory_authority_bridge.capability_autonomy_profile_snapshot",
        lambda *args, **kwargs: _profile(),
    )

    assessment = assess_regulatory_authority_bridge(db_session, change)

    assert assessment.evidence_ready is False
    assert assessment.board_delegation_valid is True
    assert assessment.bridge_state == "quarantined"
    assert "authorization_evidence_not_ready" in assessment.reasons
    assert assessment.execution_authority is False


def test_ri_a72_batch_is_idempotent_and_never_writes_rules(db_session) -> None:
    change, _ = _seed_authorization(db_session)
    before_rules = len(db_session.exec(select(VerifiedRule)).all())

    first = scan_regulatory_authority_bridge(db_session)
    second = scan_regulatory_authority_bridge(db_session)

    audits = db_session.exec(
        select(AuditLog)
        .where(AuditLog.action == BRIDGE_ACTION)
        .where(AuditLog.entity_type == "regulatory_change")
        .where(AuditLog.entity_id == str(change.id))
    ).all()
    assert first["execution_bridge_enabled"] is False
    assert first["execution_authorized"] == 0
    assert first["verified_rule_writes"] == 0
    assert first["publication_writes"] == 0
    assert first["canonical_writes"] == 0
    assert first["audit_writes"] == 1
    assert second["audit_writes"] == 0
    assert len(audits) == 1
    assert len(db_session.exec(select(VerifiedRule)).all()) == before_rules == 0

    db_session.refresh(change)
    assert change.status == "pending_review"
    assert change.reviewed_by is None
    assert change.published_at is None
