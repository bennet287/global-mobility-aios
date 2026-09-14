from __future__ import annotations

import hashlib
import json

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
from app.models.regulatory_publication import RegulatoryPublicationSet, RegulatoryReviewDisposition
from app.services.regulatory_graph_publication_provenance import assess_graph_publication_provenance
from app.services.regulatory_machine_publication import PUBLICATION_ACTION, PUBLICATION_CONTRACT_VERSION
from app.services.regulatory_promotion_authorization import AUTHORIZATION_ACTION, AUTHORIZATION_VERSION


def _stable_json(value) -> str:
    return json.dumps(value, default=str, sort_keys=True, separators=(",", ":"))


def _sha256(value) -> str:
    return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()


def _seed(db_session, *, machine: bool):
    jurisdiction = Jurisdiction(code="AT-RIA75", name="Austria RI.A7.5")
    db_session.add(jurisdiction)
    db_session.flush()
    source = OfficialSource(
        jurisdiction_id=jurisdiction.id,
        country="Austria",
        domain="work",
        name="RI.A7.5 authority",
        url="https://example.gv.at/ria75",
    )
    db_session.add(source)
    db_session.flush()
    snapshot = SourceSnapshot(
        official_source_id=source.id,
        url=source.url,
        content_hash="8" * 64,
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
        title="RI.A7.5 programme",
        summary="Dual provenance fixture.",
        materiality="medium",
        status="published",
        detected_at=now_utc(),
        published_at=now_utc(),
        reviewed_by=None if machine else "human-reviewer",
        reviewed_at=None if machine else now_utc(),
    )
    db_session.add(change)
    db_session.flush()
    rule = VerifiedRule(
        country="austria",
        domain="work",
        rule_key="ria75_rule",
        statement="Official RI.A7.5 deterministic rule.",
        official_source_id=source.id,
        jurisdiction_id=jurisdiction.id,
        regulatory_change_id=change.id,
        source_snapshot_id=snapshot.id,
        confidence=1.0,
        active=True,
        approved_by="agent:ria75-agent" if machine else "human-publisher",
        published_at=now_utc(),
    )
    db_session.add(rule)
    db_session.flush()
    return change, snapshot, rule


def _machine_lineage(db_session, change, snapshot, rule, *, review_count: int = 1):
    intended = [{
        "candidate_key": "at:work:ria75",
        "program_id": "ria75",
        "rule_key": rule.rule_key,
        "field": "salary",
        "operator": "gte",
        "value_type": "integer",
        "value": 50000,
        "currency": "EUR",
        "unit": None,
        "effective_from": None,
        "effective_to": None,
        "source_text": rule.statement,
        "intended_operation": "create_verified_rule_candidate",
        "execution_allowed": False,
    }]
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
        source="pytest",
    )
    bridge = AuditLog(
        action="regulatory_machine_authority_bridge_assessed",
        entity_type="regulatory_change",
        entity_id=str(change.id),
        after_state_json="{}",
        actor="pytest",
        source="pytest",
    )
    db_session.add(authorization)
    db_session.add(bridge)
    db_session.flush()
    manifest = [{
        "ordinal": 1,
        "verified_rule_id": str(rule.id),
        "rule_key": rule.rule_key,
        "mutation_sha256": _sha256(intended[0]),
    }]
    mutation_fingerprint = _sha256(intended)
    publication_set = RegulatoryPublicationSet(
        regulatory_change_id=change.id,
        source_snapshot_id=snapshot.id,
        source_snapshot_hash=snapshot.content_hash,
        publication_mode="board_delegated_machine",
        actor_type="agent",
        actor_key="ria75-agent",
        authorization_audit_id=authorization.id,
        authority_bridge_audit_id=bridge.id,
        autonomy_profile_id="board-profile-ria75",
        autonomy_profile_sequence=4,
        intended_rule_count=1,
        intended_mutations_sha256=mutation_fingerprint,
        published_rules_json=_stable_json(manifest),
        status="published",
        published_at=rule.published_at,
    )
    db_session.add(publication_set)
    db_session.flush()

    reviews = []
    for index in range(review_count):
        review = HumanReview(
            regulatory_change_id=change.id,
            review_type="regulatory_change",
            status=ReviewStatus.resolved,
            reason=f"RI.A7.5 governed review requirement {index + 1}",
            reviewer_notes="Human review waived under Board delegation; no human review performed.",
        )
        db_session.add(review)
        db_session.flush()
        reviews.append(review)
        db_session.add(
            RegulatoryReviewDisposition(
                human_review_id=review.id,
                regulatory_change_id=change.id,
                publication_set_id=publication_set.id,
                disposition="waived_board_delegation",
                actor_type="agent",
                actor_key="ria75-agent",
                authority_bridge_audit_id=bridge.id,
                disposition_reason="Board-delegated deterministic publication; human review waived.",
            )
        )

    publication_audit = AuditLog(
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
        actor="agent:ria75-agent",
        source=PUBLICATION_CONTRACT_VERSION,
    )
    db_session.add(publication_audit)
    db_session.commit()
    return authorization, bridge, publication_set, reviews


def test_ri_a75_preserves_existing_human_publication_provenance(db_session) -> None:
    change, snapshot, rule = _seed(db_session, machine=False)

    result = assess_graph_publication_provenance(db_session, rule, change, snapshot)

    assert result.complete is True
    assert result.human_published is True
    assert result.board_delegated_machine is False
    assert result.provenance_type == "human_regulatory_change"
    assert result.reasons == ()


def test_ri_a75_rejects_agent_rule_without_atomic_publication_set(db_session) -> None:
    change, snapshot, rule = _seed(db_session, machine=True)

    result = assess_graph_publication_provenance(db_session, rule, change, snapshot)

    assert result.complete is False
    assert result.board_delegated_machine is False
    assert result.reasons == ("machine_publication_set_missing",)


def test_ri_a75_accepts_complete_board_delegated_machine_publication_lineage(db_session) -> None:
    change, snapshot, rule = _seed(db_session, machine=True)
    _, _, publication_set, _ = _machine_lineage(db_session, change, snapshot, rule)

    result = assess_graph_publication_provenance(db_session, rule, change, snapshot)

    assert result.complete is True
    assert result.human_published is False
    assert result.board_delegated_machine is True
    assert result.provenance_type == "board_delegated_machine"
    assert result.publication_set_id == str(publication_set.id)
    assert result.reasons == ()


def test_ri_a75_machine_provenance_rejects_missing_review_disposition(db_session) -> None:
    change, snapshot, rule = _seed(db_session, machine=True)
    _, _, _, reviews = _machine_lineage(db_session, change, snapshot, rule)
    disposition = db_session.query(RegulatoryReviewDisposition).filter(
        RegulatoryReviewDisposition.human_review_id == reviews[0].id
    ).one()
    db_session.delete(disposition)
    db_session.commit()

    result = assess_graph_publication_provenance(db_session, rule, change, snapshot)

    assert result.complete is False
    assert "machine_review_disposition_coverage_incomplete" in result.reasons


def test_ri_a75_machine_provenance_rejects_partial_review_disposition_coverage(db_session) -> None:
    change, snapshot, rule = _seed(db_session, machine=True)
    _, _, _, reviews = _machine_lineage(db_session, change, snapshot, rule, review_count=2)
    disposition = db_session.query(RegulatoryReviewDisposition).filter(
        RegulatoryReviewDisposition.human_review_id == reviews[1].id
    ).one()
    db_session.delete(disposition)
    db_session.commit()

    result = assess_graph_publication_provenance(db_session, rule, change, snapshot)

    assert result.complete is False
    assert "machine_review_disposition_coverage_incomplete" in result.reasons


def test_ri_a75_machine_provenance_rejects_wrong_disposition_bridge(db_session) -> None:
    change, snapshot, rule = _seed(db_session, machine=True)
    authorization, _, publication_set, reviews = _machine_lineage(db_session, change, snapshot, rule)
    disposition = db_session.query(RegulatoryReviewDisposition).filter(
        RegulatoryReviewDisposition.human_review_id == reviews[0].id
    ).one()
    disposition.authority_bridge_audit_id = authorization.id
    db_session.add(disposition)
    db_session.commit()

    result = assess_graph_publication_provenance(db_session, rule, change, snapshot)

    assert result.complete is False
    assert "machine_review_disposition_invalid" in result.reasons
    assert result.publication_set_id == str(publication_set.id)


def test_ri_a75_machine_provenance_rejects_authorization_mutation_fingerprint_mismatch(db_session) -> None:
    change, snapshot, rule = _seed(db_session, machine=True)
    authorization, _, _, _ = _machine_lineage(db_session, change, snapshot, rule)
    payload = json.loads(authorization.after_state_json)
    payload["intended_rule_mutations"][0]["value"] = 99999
    authorization.after_state_json = _stable_json(payload)
    db_session.add(authorization)
    db_session.commit()

    result = assess_graph_publication_provenance(db_session, rule, change, snapshot)

    assert result.complete is False
    assert "machine_mutation_fingerprint_mismatch" in result.reasons


def test_ri_a75_machine_provenance_fails_closed_on_snapshot_drift(db_session) -> None:
    change, snapshot, rule = _seed(db_session, machine=True)
    _, _, publication_set, _ = _machine_lineage(db_session, change, snapshot, rule)
    publication_set.source_snapshot_hash = "0" * 64
    db_session.add(publication_set)
    db_session.commit()

    result = assess_graph_publication_provenance(db_session, rule, change, snapshot)

    assert result.complete is False
    assert result.board_delegated_machine is False
    assert "machine_publication_snapshot_hash_mismatch" in result.reasons
