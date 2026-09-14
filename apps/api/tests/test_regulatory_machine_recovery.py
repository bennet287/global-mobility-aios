from __future__ import annotations

import hashlib
import json

import pytest
from sqlmodel import select

from app.models.domain import (
    AuditLog,
    HumanReview,
    Jurisdiction,
    OfficialSource,
    RegulatoryChange,
    RegulatoryKnowledgeEdge,
    ReviewStatus,
    SourceSnapshot,
    VerifiedRule,
    now_utc,
)
from app.models.regulatory_publication import RegulatoryPublicationSet, RegulatoryReviewDisposition
from app.services.regulatory_knowledge_graph import project_verified_rule
from app.services.regulatory_machine_publication import PUBLICATION_ACTION, PUBLICATION_CONTRACT_VERSION
from app.services.regulatory_machine_recovery import (
    RECOVERY_ACTION,
    RegulatoryMachineRecoveryError,
    quarantine_board_delegated_machine_publication_set,
)
from app.services.regulatory_promotion_authorization import AUTHORIZATION_ACTION, AUTHORIZATION_VERSION


def _stable_json(value) -> str:
    return json.dumps(value, default=str, sort_keys=True, separators=(",", ":"))


def _sha256(value) -> str:
    return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()


def _seed_machine_publication(db_session, *, rule_count: int = 2):
    jurisdiction = Jurisdiction(code="AT-RIA8R", name="Austria RI.A8 Recovery")
    db_session.add(jurisdiction)
    db_session.flush()
    source = OfficialSource(
        jurisdiction_id=jurisdiction.id,
        country="Austria",
        domain="work",
        name="RI.A8 recovery authority",
        url="https://example.gv.at/ria8/recovery",
    )
    db_session.add(source)
    db_session.flush()
    snapshot = SourceSnapshot(
        official_source_id=source.id,
        url=source.url,
        content_hash="6" * 64,
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
        title="RI.A8 recovery programme",
        summary="Board-delegated machine publication recovery fixture.",
        materiality="medium",
        status="published",
        detected_at=now_utc(),
        published_at=now_utc(),
        reviewed_by=None,
        reviewed_at=None,
    )
    db_session.add(change)
    db_session.flush()

    intended = [
        {
            "candidate_key": f"recovery:{index + 1}",
            "program_id": "ria8-recovery",
            "rule_key": f"ria8_recovery_rule_{index + 1}",
            "field": f"candidate.field_{index + 1}",
            "operator": "present",
            "value_type": "string",
            "value": None,
            "currency": None,
            "unit": None,
            "effective_from": None,
            "effective_to": None,
            "source_text": f"RI.A8 deterministic recovery rule {index + 1}.",
            "intended_operation": "create_verified_rule_candidate",
            "execution_allowed": False,
        }
        for index in range(rule_count)
    ]
    authorization = AuditLog(
        action=AUTHORIZATION_ACTION,
        entity_type="regulatory_change",
        entity_id=str(change.id),
        after_state_json=_stable_json({
            "authorization_version": AUTHORIZATION_VERSION,
            "regulatory_change_id": str(change.id),
            "intended_rule_mutations": intended,
        }),
        actor="pytest",
        source=AUTHORIZATION_VERSION,
    )
    bridge = AuditLog(
        action="regulatory_machine_authority_bridge_assessed",
        entity_type="regulatory_change",
        entity_id=str(change.id),
        after_state_json="{}",
        actor="pytest",
        source="regulatory-authority-bridge-v1",
    )
    db_session.add(authorization)
    db_session.add(bridge)
    db_session.flush()

    rules = []
    for mutation in intended:
        rule = VerifiedRule(
            country="austria",
            domain="work",
            rule_key=mutation["rule_key"],
            statement=mutation["source_text"],
            official_source_id=source.id,
            jurisdiction_id=jurisdiction.id,
            regulatory_change_id=change.id,
            source_snapshot_id=snapshot.id,
            confidence=1.0,
            active=True,
            approved_by="agent:ria8-recovery-agent",
            published_at=now_utc(),
        )
        db_session.add(rule)
        db_session.flush()
        rules.append(rule)

    manifest = [
        {
            "ordinal": index,
            "verified_rule_id": str(rule.id),
            "rule_key": rule.rule_key,
            "mutation_sha256": _sha256(intended[index - 1]),
        }
        for index, rule in enumerate(rules, start=1)
    ]
    mutation_fingerprint = _sha256(intended)
    publication_set = RegulatoryPublicationSet(
        regulatory_change_id=change.id,
        source_snapshot_id=snapshot.id,
        source_snapshot_hash=snapshot.content_hash,
        publication_mode="board_delegated_machine",
        actor_type="agent",
        actor_key="ria8-recovery-agent",
        authorization_audit_id=authorization.id,
        authority_bridge_audit_id=bridge.id,
        autonomy_profile_id="board-profile-ria8-recovery",
        autonomy_profile_sequence=5,
        intended_rule_count=len(rules),
        intended_mutations_sha256=mutation_fingerprint,
        published_rules_json=_stable_json(manifest),
        status="published",
        published_at=now_utc(),
    )
    db_session.add(publication_set)
    db_session.flush()

    review = HumanReview(
        regulatory_change_id=change.id,
        review_type="regulatory_change",
        status=ReviewStatus.resolved,
        reason="RI.A8 recovery governed review requirement",
        reviewer_notes="Human review waived under Board delegation; no human review performed.",
    )
    db_session.add(review)
    db_session.flush()
    db_session.add(
        RegulatoryReviewDisposition(
            human_review_id=review.id,
            regulatory_change_id=change.id,
            publication_set_id=publication_set.id,
            disposition="waived_board_delegation",
            actor_type="agent",
            actor_key=publication_set.actor_key,
            authority_bridge_audit_id=bridge.id,
            disposition_reason="Board-delegated deterministic publication; human review waived.",
        )
    )
    db_session.add(
        AuditLog(
            action=PUBLICATION_ACTION,
            entity_type="regulatory_publication_set",
            entity_id=str(publication_set.id),
            after_state_json=_stable_json({
                "contract_version": PUBLICATION_CONTRACT_VERSION,
                "publication_set_id": str(publication_set.id),
                "authorization_audit_id": str(authorization.id),
                "authority_bridge_audit_id": str(bridge.id),
                "autonomy_profile_id": publication_set.autonomy_profile_id,
                "autonomy_profile_sequence": publication_set.autonomy_profile_sequence,
                "source_snapshot_id": str(snapshot.id),
                "source_snapshot_hash": snapshot.content_hash,
                "intended_mutations_sha256": mutation_fingerprint,
                "published_rules": manifest,
            }),
            actor="agent:ria8-recovery-agent",
            source=PUBLICATION_CONTRACT_VERSION,
        )
    )
    db_session.commit()

    for rule in rules:
        project_verified_rule(
            db_session,
            rule,
            actor="agent:ria8-recovery-agent",
            audit=True,
        )
    db_session.commit()
    return publication_set, rules


def test_ri_a8_recovery_kill_switch_blocks_canonical_changes(db_session) -> None:
    publication_set, rules = _seed_machine_publication(db_session)

    with pytest.raises(RegulatoryMachineRecoveryError, match="recovery execution is disabled"):
        quarantine_board_delegated_machine_publication_set(
            db_session,
            publication_set.id,
            reason="Freshness drift detected",
        )

    db_session.refresh(publication_set)
    assert publication_set.status == "published"
    assert all(rule.active for rule in rules)
    assert all(rule.retired_at is None for rule in rules)


def test_ri_a8_recovery_atomically_quarantines_set_and_deactivates_graph(db_session) -> None:
    publication_set, rules = _seed_machine_publication(db_session)
    active_edges = db_session.exec(
        select(RegulatoryKnowledgeEdge).where(RegulatoryKnowledgeEdge.active == True)  # noqa: E712
    ).all()
    assert active_edges

    result = quarantine_board_delegated_machine_publication_set(
        db_session,
        publication_set.id,
        reason="Official-source freshness drift invalidated the publication set",
        actor="regulatory-emergency-recovery-agent",
        recovery_enabled=True,
    )

    db_session.refresh(publication_set)
    for rule in rules:
        db_session.refresh(rule)
    edges = db_session.exec(select(RegulatoryKnowledgeEdge)).all()
    assert result.recovery_state == "quarantined"
    assert result.canonical_write_performed is True
    assert publication_set.status == "quarantined"
    assert all(rule.active is False for rule in rules)
    assert all(rule.retired_at is not None for rule in rules)
    assert all(rule.retired_by == "regulatory-emergency-recovery-agent" for rule in rules)
    assert edges and all(edge.active is False for edge in edges)
    assert len(db_session.exec(select(AuditLog).where(AuditLog.action == RECOVERY_ACTION)).all()) == 1


def test_ri_a8_recovery_replay_is_idempotent(db_session) -> None:
    publication_set, _ = _seed_machine_publication(db_session, rule_count=1)
    first = quarantine_board_delegated_machine_publication_set(
        db_session,
        publication_set.id,
        reason="Deterministic emergency quarantine",
        recovery_enabled=True,
    )
    second = quarantine_board_delegated_machine_publication_set(
        db_session,
        publication_set.id,
        reason="Deterministic emergency quarantine",
        recovery_enabled=True,
    )

    assert first.recovery_state == "quarantined"
    assert second.recovery_state == "already_quarantined"
    assert second.canonical_write_performed is False
    assert len(db_session.exec(select(AuditLog).where(AuditLog.action == RECOVERY_ACTION)).all()) == 1


def test_ri_a8_recovery_failure_rolls_back_entire_publication_set(
    db_session,
    monkeypatch,
) -> None:
    publication_set, rules = _seed_machine_publication(db_session, rule_count=2)
    original = __import__(
        "app.services.regulatory_machine_recovery",
        fromlist=["deactivate_rule_projection"],
    ).deactivate_rule_projection
    calls = {"count": 0}

    def fail_on_second_projection(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 2:
            raise RuntimeError("synthetic graph recovery failure")
        return original(*args, **kwargs)

    monkeypatch.setattr(
        "app.services.regulatory_machine_recovery.deactivate_rule_projection",
        fail_on_second_projection,
    )

    with pytest.raises(RuntimeError, match="synthetic graph recovery failure"):
        quarantine_board_delegated_machine_publication_set(
            db_session,
            publication_set.id,
            reason="Atomic rollback proof",
            recovery_enabled=True,
        )

    db_session.refresh(publication_set)
    for rule in rules:
        db_session.refresh(rule)
    edges = db_session.exec(select(RegulatoryKnowledgeEdge)).all()
    assert publication_set.status == "published"
    assert all(rule.active is True for rule in rules)
    assert all(rule.retired_at is None for rule in rules)
    assert edges and all(edge.active is True for edge in edges)
    assert db_session.exec(select(AuditLog).where(AuditLog.action == RECOVERY_ACTION)).all() == []
