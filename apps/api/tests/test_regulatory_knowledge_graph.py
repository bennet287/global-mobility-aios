from __future__ import annotations

from uuid import UUID

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.domain import (
    AuditLog,
    RegulatoryKnowledgeEdge,
    RegulatoryKnowledgeNode,
    VerifiedRule,
)


def _publish_reviewed_rule(client: TestClient) -> dict:
    onboarded = client.post(
        "/api/v1/regulatory-intelligence/source-onboarding",
        json={
            "jurisdiction_code": "AT",
            "jurisdiction_name": "Austria",
            "jurisdiction_type": "country",
            "region": "Europe",
            "authority_name": "Federal immigration authority graph fixture",
            "authority_website_url": "https://www.bmi.gv.at/",
            "source_name": "Residence permit graph fixture",
            "source_url": "https://www.bmi.gv.at/example-residence-permit-rules",
            "source_domain": "visa",
            "source_type": "government",
            "allowed_domains": ["bmi.gv.at"],
        },
    )
    assert onboarded.status_code == 201
    source_id = onboarded.json()["official_source"]["id"]
    assert client.post(
        f"/api/v1/regulatory-intelligence/sources/{source_id}/snapshots",
        json={"content_text": "The skilled residence permit salary requirement is EUR 40,000."},
    ).status_code == 201
    changed = client.post(
        f"/api/v1/regulatory-intelligence/sources/{source_id}/snapshots",
        json={
            "content_text": "The skilled residence permit salary requirement is EUR 45,000.",
            "materiality": "critical",
        },
    )
    assert changed.status_code == 201
    change = changed.json()["change"]
    proposal = changed.json()["classification_proposal"]

    empty_graph = client.get("/api/v1/regulatory-intelligence/knowledge-graph")
    assert empty_graph.status_code == 200
    assert empty_graph.json()["counts"]["edges"] == 0

    accepted = client.post(
        f"/api/v1/regulatory-intelligence/classification-proposals/{proposal['id']}/review",
        json={
            "decision": "accepted",
            "reviewer": "graph-classification-reviewer",
            "notes": "The exact removed and added salary lines support the proposal.",
        },
    )
    assert accepted.status_code == 200
    reviewed = client.post(
        f"/api/v1/regulatory-intelligence/changes/{change['id']}/review",
        json={
            "decision": "approved",
            "reviewer": "graph-regulatory-reviewer",
            "notes": "Validated against the immutable official-source snapshot.",
        },
    )
    assert reviewed.status_code == 200
    published = client.post(
        f"/api/v1/regulatory-intelligence/changes/{change['id']}/publish",
        json={
            "rule_key": "skilled_residence_minimum_salary",
            "statement": "The skilled residence permit salary requirement is EUR 45,000.",
            "reviewer": "graph-rule-publisher",
            "confidence": 1.0,
        },
        headers={"X-GMAI-Role": "reviewer", "X-GMAI-User": "graph-rule-publisher"},
    )
    assert published.status_code == 200
    return published.json()["verified_rule"]


def test_human_published_rule_projects_complete_provenance_graph(
    client: TestClient,
    db_session: Session,
) -> None:
    rule = _publish_reviewed_rule(client)

    response = client.get(
        "/api/v1/regulatory-intelligence/knowledge-graph",
        params={"verified_rule_id": rule["id"]},
    )
    assert response.status_code == 200
    graph = response.json()
    assert graph["projection_version"] == "regulatory-graph-v1"
    assert graph["human_published_only"] is True
    assert graph["provenance_complete"] is True
    assert graph["counts"] == {"nodes": 7, "edges": 8, "verified_rules": 1}
    assert {node["node_type"] for node in graph["nodes"]} == {
        "jurisdiction",
        "regulatory_domain",
        "regulatory_authority",
        "official_source",
        "source_snapshot",
        "regulatory_change",
        "verified_rule",
    }
    assert {edge["relation_type"] for edge in graph["edges"]} == {
        "HAS_PUBLISHED_RULE",
        "IN_REGULATORY_DOMAIN",
        "DERIVED_FROM_CHANGE",
        "EVIDENCED_BY_SNAPSHOT",
        "CAPTURED_FROM_SOURCE",
        "OFFICIAL_SOURCE_FOR",
        "GOVERNED_BY_AUTHORITY",
        "AUTHORITY_FOR",
    }
    assert all(edge["verified_rule_id"] == rule["id"] for edge in graph["edges"])
    assert all(edge["source_snapshot_id"] == rule["source_snapshot_id"] for edge in graph["edges"])
    assert all(edge["regulatory_change_id"] == rule["regulatory_change_id"] for edge in graph["edges"])
    assert len(db_session.exec(select(RegulatoryKnowledgeNode)).all()) == 7
    assert len(db_session.exec(select(RegulatoryKnowledgeEdge)).all()) == 8
    audit_actions = {row.action for row in db_session.exec(select(AuditLog)).all()}
    assert "regulatory_knowledge_graph_projected" in audit_actions


def test_graph_sync_is_idempotent_and_ignores_unpublished_rules(
    client: TestClient,
    db_session: Session,
) -> None:
    published = _publish_reviewed_rule(client)
    published_rule = db_session.get(VerifiedRule, UUID(published["id"]))
    assert published_rule is not None
    unpublished = VerifiedRule(
        country="austria",
        domain="visa",
        rule_key="unreviewed_draft_rule",
        statement="This draft must never enter the graph.",
        official_source_id=published_rule.official_source_id,
        jurisdiction_id=published_rule.jurisdiction_id,
        regulatory_change_id=published_rule.regulatory_change_id,
        source_snapshot_id=published_rule.source_snapshot_id,
        confidence=0.2,
        active=True,
    )
    db_session.add(unpublished)
    db_session.commit()

    first = client.post(
        "/api/v1/regulatory-intelligence/knowledge-graph/sync",
        json={"actor": "graph-sync-reviewer"},
    )
    second = client.post(
        "/api/v1/regulatory-intelligence/knowledge-graph/sync",
        json={"actor": "graph-sync-reviewer"},
    )
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["sync"]["published_rules_considered"] == 1
    assert first.json()["sync"]["projected_rules"] == 1
    assert first.json()["sync"]["skipped"] == []
    assert len(db_session.exec(select(RegulatoryKnowledgeNode)).all()) == 7
    assert len(db_session.exec(select(RegulatoryKnowledgeEdge)).all()) == 8
    assert db_session.exec(
        select(RegulatoryKnowledgeEdge).where(RegulatoryKnowledgeEdge.verified_rule_id == unpublished.id)
    ).first() is None


def test_rule_retirement_preserves_history_and_deactivates_projection(
    client: TestClient,
    db_session: Session,
) -> None:
    rule = _publish_reviewed_rule(client)
    retired = client.post(
        f"/api/v1/regulatory-intelligence/verified-rules/{rule['id']}/retire",
        json={
            "reviewer": "graph-retirement-reviewer",
            "reason": "The authority replaced this published rule.",
        },
    )
    assert retired.status_code == 200

    active_graph = client.get(
        "/api/v1/regulatory-intelligence/knowledge-graph",
        params={"verified_rule_id": rule["id"], "active": True},
    ).json()
    historical_graph = client.get(
        "/api/v1/regulatory-intelligence/knowledge-graph",
        params={"verified_rule_id": rule["id"], "active": False},
    ).json()
    assert active_graph["counts"]["edges"] == 0
    assert historical_graph["counts"]["edges"] == 8
    assert all(edge["active"] is False and edge["retired_at"] for edge in historical_graph["edges"])
    assert all(node.active is False for node in db_session.exec(select(RegulatoryKnowledgeNode)).all())
    audit_actions = {row.action for row in db_session.exec(select(AuditLog)).all()}
    assert "regulatory_knowledge_graph_deactivated" in audit_actions
