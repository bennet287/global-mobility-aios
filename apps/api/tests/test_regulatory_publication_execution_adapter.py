from __future__ import annotations

from types import SimpleNamespace

from sqlmodel import select

from app.models.domain import (
    AuditLog,
    HumanReview,
    Jurisdiction,
    OfficialSource,
    RegulatoryChange,
    ReviewStatus,
    SourceSnapshot,
    VerifiedRule,
    now_utc,
)
from app.services.audit_log import record_audit
from app.services.regulatory_authority_bridge import BRIDGE_ACTION, BRIDGE_VERSION
from app.services.regulatory_promotion_authorization import AUTHORIZATION_ACTION, AUTHORIZATION_VERSION
from app.services.regulatory_publication_execution_adapter import (
    EXECUTION_ADAPTER_ACTION,
    EXECUTION_ADAPTER_VERSION,
    assess_regulatory_publication_execution,
    scan_regulatory_publication_execution_preflight,
)


def _live_bridge(*, valid: bool = True):
    return SimpleNamespace(
        evidence_ready=valid,
        board_delegation_valid=valid,
        bridge_state=(
            "delegation_ready_execution_adapter_missing" if valid else "board_delegation_required"
        ),
        autonomy_profile_id="board-profile-ria73",
        autonomy_profile_sequence=1,
    )


def _seed_execution_lineage(db_session, *, rule_count: int = 2, pending_review: bool = True):
    jurisdiction = Jurisdiction(code="AT-RIA73", name="Austria RI.A7.3")
    db_session.add(jurisdiction)
    db_session.flush()
    source = OfficialSource(
        jurisdiction_id=jurisdiction.id,
        country="Austria",
        domain="work",
        name="Austrian immigration authority RI.A7.3",
        url="https://example.gv.at/ria73/programs",
    )
    db_session.add(source)
    db_session.flush()
    snapshot = SourceSnapshot(
        official_source_id=source.id,
        url=source.url,
        content_hash="f" * 64,
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
        title="RI.A7.3 deterministic programme",
        summary="Execution-adapter safety candidate.",
        materiality="medium",
        status="pending_review",
        detected_at=now_utc(),
    )
    db_session.add(change)
    db_session.flush()

    intended = []
    for index in range(rule_count):
        intended.append(
            {
                "candidate_key": f"{jurisdiction.id}:{source.id}:talent",
                "program_id": "talent",
                "rule_key": f"rule_{index + 1}",
                "field": f"candidate.field_{index + 1}",
                "operator": "present",
                "value_type": "string",
                "value": None,
                "currency": None,
                "unit": None,
                "effective_from": "2026-10-01",
                "effective_to": None,
                "source_text": f"Official deterministic rule {index + 1}.",
                "intended_operation": "create_verified_rule_candidate",
                "execution_allowed": False,
            }
        )

    authorization = record_audit(
        db_session,
        action=AUTHORIZATION_ACTION,
        entity_type="regulatory_change",
        entity_id=change.id,
        after_state={
            "regulatory_change_id": str(change.id),
            "authorization_version": AUTHORIZATION_VERSION,
            "authorization_state": "evidence_ready_authority_missing",
            "evidence_ready": True,
            "execution_authority": False,
            "source_snapshot_id": str(snapshot.id),
            "source_snapshot_content_hash": snapshot.content_hash,
            "intended_rule_mutations": intended,
            "verified_rule_writes_allowed": False,
            "pathway_writes_allowed": False,
            "publication_writes_allowed": False,
            "canonical_write_allowed": False,
        },
        actor="pytest-authorization",
        source=AUTHORIZATION_VERSION,
    )
    db_session.flush()
    bridge = record_audit(
        db_session,
        action=BRIDGE_ACTION,
        entity_type="regulatory_change",
        entity_id=change.id,
        after_state={
            "regulatory_change_id": str(change.id),
            "bridge_version": BRIDGE_VERSION,
            "authorization_audit_id": str(authorization.id),
            "autonomy_profile_id": "board-profile-ria73",
            "autonomy_profile_sequence": 1,
            "evidence_ready": True,
            "board_delegation_valid": True,
            "execution_bridge_enabled": False,
            "execution_authority": False,
            "bridge_state": "delegation_ready_execution_adapter_missing",
            "canonical_write_allowed": False,
            "reasons": [],
        },
        actor="pytest-bridge",
        source=BRIDGE_VERSION,
    )
    if pending_review:
        db_session.add(
            HumanReview(
                regulatory_change_id=change.id,
                review_type="regulatory_change",
                status=ReviewStatus.pending,
                priority="medium",
                reason="Validate detected regulatory change.",
            )
        )
    db_session.commit()
    return change, authorization, bridge


def test_ri_a74_review_and_multi_rule_contracts_are_ready_but_kill_switch_stays_closed(
    db_session,
    monkeypatch,
) -> None:
    change, authorization, bridge = _seed_execution_lineage(db_session, rule_count=2)
    monkeypatch.setattr(
        "app.services.regulatory_publication_execution_adapter.assess_regulatory_authority_bridge",
        lambda *args, **kwargs: _live_bridge(),
    )

    assessment = assess_regulatory_publication_execution(db_session, change)

    assert assessment.adapter_version == EXECUTION_ADAPTER_VERSION
    assert assessment.authorization_audit_id == str(authorization.id)
    assert assessment.bridge_audit_id == str(bridge.id)
    assert assessment.evidence_ready is True
    assert assessment.board_delegation_valid is True
    assert assessment.intended_rule_count == 2
    assert assessment.pending_human_review_count == 1
    assert assessment.review_disposition_contract_ready is True
    assert assessment.multi_rule_publication_contract_ready is True
    assert assessment.execution_state == "ready_but_disabled"
    assert assessment.reasons == ("machine_publication_disabled",)
    assert assessment.execution_authority is False
    assert assessment.canonical_write_allowed is False


def test_ri_a74_explicit_execution_override_authorizes_clean_contract_only(db_session, monkeypatch) -> None:
    change, _, _ = _seed_execution_lineage(db_session, rule_count=2)
    monkeypatch.setattr(
        "app.services.regulatory_publication_execution_adapter.assess_regulatory_authority_bridge",
        lambda *args, **kwargs: _live_bridge(),
    )

    assessment = assess_regulatory_publication_execution(
        db_session,
        change,
        machine_publication_enabled=True,
    )

    assert assessment.execution_state == "execution_authorized"
    assert assessment.reasons == ()
    assert assessment.execution_authority is True
    assert assessment.canonical_write_allowed is True


def test_ri_a73_live_delegation_drift_is_fail_closed(db_session, monkeypatch) -> None:
    change, _, _ = _seed_execution_lineage(db_session, rule_count=1, pending_review=False)
    monkeypatch.setattr(
        "app.services.regulatory_publication_execution_adapter.assess_regulatory_authority_bridge",
        lambda *args, **kwargs: _live_bridge(valid=False),
    )

    assessment = assess_regulatory_publication_execution(db_session, change)

    assert assessment.execution_state == "quarantined"
    assert "live_evidence_not_ready" in assessment.reasons
    assert "live_board_delegation_invalid" in assessment.reasons
    assert "live_bridge_state_not_delegation_ready" in assessment.reasons
    assert assessment.execution_authority is False


def test_ri_a74_batch_is_idempotent_and_never_writes_canonical_truth(db_session, monkeypatch) -> None:
    change, _, _ = _seed_execution_lineage(db_session, rule_count=2)
    monkeypatch.setattr(
        "app.services.regulatory_publication_execution_adapter.assess_regulatory_authority_bridge",
        lambda *args, **kwargs: _live_bridge(),
    )
    before_rules = len(db_session.exec(select(VerifiedRule)).all())

    first = scan_regulatory_publication_execution_preflight(db_session)
    second = scan_regulatory_publication_execution_preflight(db_session)

    audits = db_session.exec(
        select(AuditLog)
        .where(AuditLog.action == EXECUTION_ADAPTER_ACTION)
        .where(AuditLog.entity_type == "regulatory_change")
        .where(AuditLog.entity_id == str(change.id))
    ).all()
    assert first["machine_publication_enabled"] is False
    assert first["review_disposition_contract_ready"] is True
    assert first["multi_rule_publication_contract_ready"] is True
    assert first["execution_authorized"] == 0
    assert first["blocked_contract_gap"] == 0
    assert first["ready_but_disabled"] == 1
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
    assert change.reviewed_at is None
    assert change.published_at is None
