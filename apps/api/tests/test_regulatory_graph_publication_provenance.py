from __future__ import annotations

import json

from app.models.domain import AuditLog, Jurisdiction, OfficialSource, RegulatoryChange, SourceSnapshot, VerifiedRule, now_utc
from app.models.regulatory_publication import RegulatoryPublicationSet
from app.services.regulatory_graph_publication_provenance import assess_graph_publication_provenance
from app.services.regulatory_machine_publication import PUBLICATION_ACTION, PUBLICATION_CONTRACT_VERSION


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
    authorization = AuditLog(
        action="regulatory_machine_promotion_authorization_assessed",
        entity_type="regulatory_change",
        entity_id=str(change.id),
        after_state_json="{}",
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
        "mutation_sha256": "9" * 64,
    }]
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
        intended_mutations_sha256="a" * 64,
        published_rules_json=json.dumps(manifest, sort_keys=True, separators=(",", ":")),
        status="published",
        published_at=rule.published_at,
    )
    db_session.add(publication_set)
    db_session.flush()
    publication_audit = AuditLog(
        action=PUBLICATION_ACTION,
        entity_type="regulatory_publication_set",
        entity_id=str(publication_set.id),
        after_state_json=json.dumps({
            "contract_version": PUBLICATION_CONTRACT_VERSION,
            "publication_set_id": str(publication_set.id),
            "authorization_audit_id": str(authorization.id),
            "authority_bridge_audit_id": str(bridge.id),
            "source_snapshot_id": str(snapshot.id),
            "source_snapshot_hash": snapshot.content_hash,
            "published_rules": manifest,
        }, sort_keys=True),
        actor="agent:ria75-agent",
        source=PUBLICATION_CONTRACT_VERSION,
    )
    db_session.add(publication_audit)
    db_session.commit()

    result = assess_graph_publication_provenance(db_session, rule, change, snapshot)

    assert result.complete is True
    assert result.human_published is False
    assert result.board_delegated_machine is True
    assert result.provenance_type == "board_delegated_machine"
    assert result.publication_set_id == str(publication_set.id)
    assert result.reasons == ()


def test_ri_a75_machine_provenance_fails_closed_on_snapshot_drift(db_session) -> None:
    change, snapshot, rule = _seed(db_session, machine=True)
    authorization = AuditLog(action="auth", entity_type="regulatory_change", entity_id=str(change.id), after_state_json="{}", actor="pytest", source="pytest")
    bridge = AuditLog(action="bridge", entity_type="regulatory_change", entity_id=str(change.id), after_state_json="{}", actor="pytest", source="pytest")
    db_session.add(authorization)
    db_session.add(bridge)
    db_session.flush()
    publication_set = RegulatoryPublicationSet(
        regulatory_change_id=change.id,
        source_snapshot_id=snapshot.id,
        source_snapshot_hash="0" * 64,
        actor_type="agent",
        actor_key="ria75-agent",
        authorization_audit_id=authorization.id,
        authority_bridge_audit_id=bridge.id,
        autonomy_profile_id="board-profile-ria75",
        autonomy_profile_sequence=4,
        intended_rule_count=1,
        intended_mutations_sha256="a" * 64,
        published_rules_json=json.dumps([{"verified_rule_id": str(rule.id)}]),
        status="published",
    )
    db_session.add(publication_set)
    db_session.commit()

    result = assess_graph_publication_provenance(db_session, rule, change, snapshot)

    assert result.complete is False
    assert result.board_delegated_machine is False
    assert "machine_publication_snapshot_hash_mismatch" in result.reasons
    assert "machine_publication_audit_missing" in result.reasons
