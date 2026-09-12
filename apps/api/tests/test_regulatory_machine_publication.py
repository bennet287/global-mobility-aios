from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
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
from app.models.regulatory_publication import (
    RegulatoryPublicationSet,
    RegulatoryReviewDisposition,
)
from app.services.audit_log import record_audit
from app.services.regulatory_authority_bridge import BRIDGE_ACTION, BRIDGE_VERSION
from app.services.regulatory_machine_publication import (
    PUBLICATION_ACTION,
    RegulatoryMachinePublicationError,
    publish_board_delegated_machine_rule_set,
)
from app.services.regulatory_promotion_authorization import AUTHORIZATION_ACTION, AUTHORIZATION_VERSION


def _live_bridge(*, valid: bool = True):
    return SimpleNamespace(
        evidence_ready=valid,
        board_delegation_valid=valid,
        bridge_state=(
            "delegation_ready_execution_adapter_missing" if valid else "board_delegation_required"
        ),
        autonomy_profile_id="board-profile-ria74",
        autonomy_profile_sequence=3,
    )


def _seed(db_session, *, rule_count: int = 2):
    jurisdiction = Jurisdiction(code="AT-RIA74", name="Austria RI.A7.4")
    db_session.add(jurisdiction)
    db_session.flush()
    source = OfficialSource(
        jurisdiction_id=jurisdiction.id,
        country="Austria",
        domain="work",
        name="Austrian immigration authority RI.A7.4",
        url="https://example.gv.at/ria74/programs",
    )
    db_session.add(source)
    db_session.flush()
    snapshot = SourceSnapshot(
        official_source_id=source.id,
        url=source.url,
        content_hash="7" * 64,
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
        title="RI.A7.4 deterministic programme",
        summary="Atomic publication contract candidate.",
        materiality="medium",
        status="pending_review",
        detected_at=now_utc(),
    )
    db_session.add(change)
    db_session.flush()

    intended = [
        {
            "candidate_key": f"{jurisdiction.id}:{source.id}:talent",
            "program_id": "talent",
            "rule_key": f"talent_rule_{index + 1}",
            "field": f"candidate.field_{index + 1}",
            "operator": "present",
            "value_type": "string",
            "value": None,
            "currency": None,
            "unit": None,
            "effective_from": "2026-10-01T00:00:00+00:00",
            "effective_to": None,
            "source_text": f"Official deterministic rule {index + 1}.",
            "intended_operation": "create_verified_rule_candidate",
            "execution_allowed": False,
        }
        for index in range(rule_count)
    ]

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
            "autonomy_profile_id": "board-profile-ria74",
            "autonomy_profile_sequence": 3,
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
    review = HumanReview(
        regulatory_change_id=change.id,
        review_type="regulatory_change",
        status=ReviewStatus.pending,
        priority="medium",
        reason="Validate detected regulatory change.",
    )
    db_session.add(review)
    db_session.commit()
    return change, authorization, bridge, review


def _enable(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.regulatory_machine_publication.MACHINE_PUBLICATION_EXECUTION_ENABLED",
        True,
    )
    monkeypatch.setattr(
        "app.services.regulatory_publication_execution_adapter.assess_regulatory_authority_bridge",
        lambda *args, **kwargs: _live_bridge(),
    )


def test_ri_a74_production_kill_switch_keeps_all_canonical_writes_off(db_session) -> None:
    change, _, _, review = _seed(db_session)

    with pytest.raises(RegulatoryMachinePublicationError, match="execution is disabled"):
        publish_board_delegated_machine_rule_set(db_session, change.id)

    assert db_session.exec(select(RegulatoryPublicationSet)).all() == []
    assert db_session.exec(select(RegulatoryReviewDisposition)).all() == []
    assert db_session.exec(select(VerifiedRule)).all() == []
    db_session.refresh(review)
    db_session.refresh(change)
    assert review.status == ReviewStatus.pending
    assert change.status == "pending_review"
    assert change.published_at is None


def test_ri_a74_persists_multi_rule_set_and_truthful_review_waiver_atomically(
    db_session,
    monkeypatch,
) -> None:
    change, authorization, bridge, review = _seed(db_session, rule_count=2)
    _enable(monkeypatch)

    publication_set, rules = publish_board_delegated_machine_rule_set(
        db_session,
        change.id,
        actor_key="regulatory-publisher-ria74",
    )

    assert publication_set.regulatory_change_id == change.id
    assert publication_set.authorization_audit_id == authorization.id
    assert publication_set.authority_bridge_audit_id == bridge.id
    assert publication_set.autonomy_profile_id == "board-profile-ria74"
    assert publication_set.autonomy_profile_sequence == 3
    assert publication_set.intended_rule_count == 2
    assert len(publication_set.intended_mutations_sha256) == 64
    assert publication_set.actor_type == "agent"
    assert publication_set.actor_key == "regulatory-publisher-ria74"
    assert len(rules) == 2
    assert {rule.rule_key for rule in rules} == {"talent_rule_1", "talent_rule_2"}
    assert all(rule.approved_by == "agent:regulatory-publisher-ria74" for rule in rules)
    assert all(rule.regulatory_change_id == change.id for rule in rules)

    db_session.refresh(review)
    db_session.refresh(change)
    disposition = db_session.exec(
        select(RegulatoryReviewDisposition).where(
            RegulatoryReviewDisposition.human_review_id == review.id
        )
    ).one()
    assert review.status == ReviewStatus.resolved
    assert "no human review was performed" in (review.reviewer_notes or "")
    assert disposition.disposition == "waived_board_delegation"
    assert disposition.actor_type == "agent"
    assert disposition.actor_key == "regulatory-publisher-ria74"
    assert disposition.publication_set_id == publication_set.id
    assert change.status == "published"
    assert change.reviewed_by is None
    assert change.reviewed_at is None
    assert change.published_at is not None

    manifest = json.loads(publication_set.published_rules_json)
    assert {item["verified_rule_id"] for item in manifest} == {str(rule.id) for rule in rules}
    assert len(db_session.exec(select(AuditLog).where(AuditLog.action == PUBLICATION_ACTION)).all()) == 1


def test_ri_a74_replay_is_idempotent_after_atomic_commit(db_session, monkeypatch) -> None:
    change, _, _, _ = _seed(db_session, rule_count=2)
    _enable(monkeypatch)

    first_set, first_rules = publish_board_delegated_machine_rule_set(db_session, change.id)
    second_set, second_rules = publish_board_delegated_machine_rule_set(db_session, change.id)

    assert second_set.id == first_set.id
    assert {rule.id for rule in second_rules} == {rule.id for rule in first_rules}
    assert len(db_session.exec(select(RegulatoryPublicationSet)).all()) == 1
    assert len(db_session.exec(select(RegulatoryReviewDisposition)).all()) == 1
    assert len(db_session.exec(select(VerifiedRule)).all()) == 2
    assert len(db_session.exec(select(AuditLog).where(AuditLog.action == PUBLICATION_ACTION)).all()) == 1


def test_ri_a74_duplicate_rule_failure_rolls_back_entire_set(db_session, monkeypatch) -> None:
    change, authorization, _, review = _seed(db_session, rule_count=2)
    _enable(monkeypatch)
    payload = json.loads(authorization.after_state_json)
    payload["intended_rule_mutations"][1]["rule_key"] = payload["intended_rule_mutations"][0]["rule_key"]
    authorization.after_state_json = json.dumps(payload, sort_keys=True, default=str)
    db_session.add(authorization)
    db_session.commit()

    with pytest.raises(RegulatoryMachinePublicationError, match="duplicate or empty rule keys"):
        publish_board_delegated_machine_rule_set(db_session, change.id)

    assert db_session.exec(select(RegulatoryPublicationSet)).all() == []
    assert db_session.exec(select(RegulatoryReviewDisposition)).all() == []
    assert db_session.exec(select(VerifiedRule)).all() == []
    db_session.refresh(review)
    db_session.refresh(change)
    assert review.status == ReviewStatus.pending
    assert change.status == "pending_review"
    assert change.published_at is None


def test_ri_a74_live_board_drift_blocks_even_when_test_execution_switch_is_on(
    db_session,
    monkeypatch,
) -> None:
    change, _, _, _ = _seed(db_session, rule_count=1)
    monkeypatch.setattr(
        "app.services.regulatory_machine_publication.MACHINE_PUBLICATION_EXECUTION_ENABLED",
        True,
    )
    monkeypatch.setattr(
        "app.services.regulatory_publication_execution_adapter.assess_regulatory_authority_bridge",
        lambda *args, **kwargs: _live_bridge(valid=False),
    )

    with pytest.raises(RegulatoryMachinePublicationError, match="preflight is not authorized"):
        publish_board_delegated_machine_rule_set(db_session, change.id)

    assert db_session.exec(select(RegulatoryPublicationSet)).all() == []
    assert db_session.exec(select(RegulatoryReviewDisposition)).all() == []
    assert db_session.exec(select(VerifiedRule)).all() == []
