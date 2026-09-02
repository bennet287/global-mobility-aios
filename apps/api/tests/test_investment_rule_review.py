from __future__ import annotations

from uuid import UUID

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.domain import (
    InvestmentMobilityRuleDecision,
    MobilityPathway,
    MobilityPathwayVersion,
    OfficialSource,
    SourceSnapshot,
    VerifiedRule,
)


def _draft(session: Session):
    source = OfficialSource(
        country="austria",
        domain="investment",
        name="Austria Self-employed Key Workers",
        url="https://www.migration.gv.at/en/self-employed-key-workers/",
        source_type="government",
        active=True,
    )
    session.add(source)
    session.commit()
    session.refresh(source)
    snapshot = SourceSnapshot(
        official_source_id=source.id,
        url=source.url,
        content_hash="a" * 64,
        content_text="Controlled official-source baseline.",
        http_status=200,
        retrieval_method="http",
        status="baseline",
    )
    pathway = MobilityPathway(
        pathway_key="at-self-employed-key-worker",
        name="Austria Self-employed Key Worker",
        country="austria",
        domain="investment",
        catalogue_status="draft",
        created_by="pathway-proposer",
    )
    session.add(snapshot)
    session.add(pathway)
    session.commit()
    session.refresh(snapshot)
    session.refresh(pathway)
    version = MobilityPathwayVersion(
        pathway_id=pathway.id,
        version_number=1,
        lifecycle_status="draft",
        official_source_id=source.id,
        source_snapshot_id=snapshot.id,
        eligibility_criteria_json='{"capital_indicator_minor":10000000}',
        required_documents_json='["business plan"]',
        risks_json='["not automatic eligibility"]',
        created_by="pathway-proposer",
    )
    session.add(version)
    session.commit()
    session.refresh(version)
    return pathway, version, source, snapshot


def _payload(version: MobilityPathwayVersion):
    return {
        "pathway_version_id": str(version.id),
        "rules": [
            {
                "rule_key": "at-self-employed-core-test",
                "statement": "The activity must create macroeconomic benefit beyond its operational benefit.",
                "evidence_scope": "route_core_test",
            },
            {
                "rule_key": "at-self-employed-capital-indicator",
                "statement": "A sustained EUR 100,000 capital transfer is one stated indicator and is not automatic eligibility.",
                "evidence_scope": "indicative_criteria",
            },
        ],
    }


def test_rule_approval_requires_independent_reviewer_and_creates_new_pathway_version(
    client: TestClient, db_session: Session,
):
    pathway, version, _, snapshot = _draft(db_session)
    created = client.post(
        "/api/v1/investment-mobility/rule-proposals",
        json=_payload(version),
    )
    assert created.status_code == 201, created.text
    proposal = created.json()
    assert proposal["status"] == "pending_review"
    assert proposal["source_content_hash"] == snapshot.content_hash

    same_actor = client.post(
        f"/api/v1/investment-mobility/rule-proposals/{proposal['id']}/review",
        json={"decision": "approved", "reason": "Reviewed against the exact official snapshot."},
    )
    assert same_actor.status_code == 400
    assert "independent reviewer" in same_actor.json()["detail"]

    client.headers["X-GMAI-User"] = "independent-investment-rule-reviewer"
    approved = client.post(
        f"/api/v1/investment-mobility/rule-proposals/{proposal['id']}/review",
        json={"decision": "approved", "reason": "Reviewed against the exact official snapshot."},
    )
    assert approved.status_code == 200, approved.text
    body = approved.json()
    assert body["status"] == "approved"
    assert len(body["created_verified_rule_ids"]) == 2
    assert body["replacement_pathway_version_id"]

    db_session.expire_all()
    original = db_session.get(MobilityPathwayVersion, version.id)
    replacement = db_session.get(
        MobilityPathwayVersion, UUID(body["replacement_pathway_version_id"])
    )
    assert original.lifecycle_status == "superseded"
    assert replacement.version_number == 2
    assert replacement.lifecycle_status == "draft"
    assert all(
        rule.source_snapshot_id == snapshot.id
        for rule in db_session.exec(select(VerifiedRule)).all()
    )
    decisions = db_session.exec(select(InvestmentMobilityRuleDecision)).all()
    assert len(decisions) == 1
    assert decisions[0].decision == "approved"
    assert pathway.catalogue_status == "draft"


def test_rejected_rule_proposal_creates_no_verified_rule(
    client: TestClient, db_session: Session,
):
    _, version, _, _ = _draft(db_session)
    proposal = client.post(
        "/api/v1/investment-mobility/rule-proposals", json=_payload(version)
    ).json()
    client.headers["X-GMAI-User"] = "independent-rejector"
    rejected = client.post(
        f"/api/v1/investment-mobility/rule-proposals/{proposal['id']}/review",
        json={"decision": "rejected", "reason": "The extracted statements need source-scope correction."},
    )
    assert rejected.status_code == 200, rejected.text
    assert rejected.json()["status"] == "rejected"
    assert rejected.json()["created_verified_rule_ids"] == []
    assert db_session.exec(select(VerifiedRule)).all() == []


def test_read_only_role_cannot_review_rule_proposal(
    client: TestClient, raw_client: TestClient, db_session: Session,
):
    _, version, _, _ = _draft(db_session)
    proposal = client.post(
        "/api/v1/investment-mobility/rule-proposals", json=_payload(version)
    ).json()
    raw_client.headers.update({
        "X-GMAI-Role": "read_only",
        "X-GMAI-User": "readonly-rule-reviewer",
    })
    response = raw_client.post(
        f"/api/v1/investment-mobility/rule-proposals/{proposal['id']}/review",
        json={"decision": "approved", "reason": "This mutation must be forbidden for read-only users."},
    )
    assert response.status_code == 403
