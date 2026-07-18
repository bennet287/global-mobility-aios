from __future__ import annotations

from sqlmodel import Session, select

from app.models.domain import (
    InitialRuleAssertion,
    RegulatoryChange,
    RegulatoryKnowledgeEdge,
    SourceSnapshot,
    VerifiedRule,
)
from app.schemas import (
    InitialRuleAssertionCreateRequest,
    InitialRuleAssertionPublishRequest,
    InitialRuleAssertionReviewRequest,
)
from app.services.coverage_evidence_batches import coverage_batch_payload, create_coverage_evidence_batch
from app.services.initial_rule_assertions import (
    propose_initial_rule_assertion,
    publish_initial_rule_assertion,
    review_initial_rule_assertion,
)
from app.services.jurisdiction_registry import (
    import_un_m49_registry,
    review_immigration_assessment,
    review_source_certification,
)
from app.services.regulatory_knowledge_graph import knowledge_graph_payload


SAMPLE_M49 = """
<html><table id="downloadTableEN"><tbody>
<tr><td>001</td><td>World</td><td>150</td><td>Europe</td><td>155</td><td>Western Europe</td><td></td><td></td><td>Austria</td><td>040</td><td>AT</td><td>AUT</td></tr>
<tr><td>001</td><td>World</td><td>150</td><td>Europe</td><td>155</td><td>Western Europe</td><td></td><td></td><td>Germany</td><td>276</td><td>DE</td><td>DEU</td></tr>
</tbody></table></html>
"""


def _setup_batch(session: Session):
    import_un_m49_registry(
        session,
        actor="registry-importer",
        source_text=SAMPLE_M49,
        minimum_entries=2,
        require_global_scope=False,
    )
    batch, _ = create_coverage_evidence_batch(
        session,
        name="Initial rule assertion batch",
        notes="Approved coverage evidence and baseline snapshot for initial rule assertion testing.",
        items=[{
            "alpha2_code": "AT",
            "source_onboarding": {
                "authority_name": "Austrian immigration authority",
                "authority_type": "immigration_authority",
                "authority_website_url": "https://official.example/immigration",
                "authority_domains": ["visa"],
                "source_name": "Austria official immigration portal",
                "source_url": "https://official.example/immigration",
                "source_domain": "visa",
                "source_type": "government",
                "schedule_minutes": 1440,
                "fetch_method": "http",
                "allowed_domains": ["official.example"],
                "max_redirects": 3,
                "parser_profile": "generic",
                "parser_config": {},
                "certification_domains": ["visa"],
                "evidence_notes": "Official authority ownership and primary immigration scope require independent review.",
            },
            "immigration_assessment": {
                "rule_relationship": "independent",
                "parent_code": None,
                "evidence_url": "https://official.example/immigration/framework",
                "evidence_title": "Official immigration framework",
                "rationale": "Official evidence identifies the directly administering immigration authority.",
            },
        }],
        actor="coverage-proposer",
    )
    item = coverage_batch_payload(session, batch)["items"][0]
    return batch, item


def _approve_and_capture(session: Session, batch, item):
    review_immigration_assessment(
        session,
        assessment_id=item["immigration_assessment"]["id"],
        decision="approved",
        notes="Independent relationship review completed.",
        actor="coverage-reviewer",
    )
    review_source_certification(
        session,
        certification_id=item["source_certification"]["id"],
        decision="approved",
        notes="Independent source certification completed.",
        actor="coverage-reviewer",
    )
    source_id = item["source_onboarding"]["official_source_id"]
    snapshot = SourceSnapshot(
        official_source_id=source_id,
        url="https://official.example/immigration",
        content_hash="a" * 64,
        content_text="Official baseline immigration guidance states the authority administers residence permits.",
        http_status=200,
        retrieval_method="http",
        parser_version="generic-v1",
        status="baseline",
    )
    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)
    return snapshot


def _payload() -> InitialRuleAssertionCreateRequest:
    return InitialRuleAssertionCreateRequest(
        alpha2_code="AT",
        domain="visa",
        title="Austria residence permit authority baseline rule",
        rule_key="residence_permit_authority",
        statement="Austria administers residence and settlement permits through the responsible federal immigration authority.",
        rationale="The reviewed official baseline identifies the authority and the public residence-permit framework.",
        evidence_excerpt="The official baseline states that the responsible federal authority administers residence and settlement matters.",
        confidence=0.95,
    )


def test_initial_rule_assertion_requires_approved_baseline(db_session: Session) -> None:
    batch, item = _setup_batch(db_session)
    try:
        propose_initial_rule_assertion(
            db_session,
            batch_id=batch.id,
            payload=_payload(),
            actor="assertion-proposer",
        )
    except ValueError as exc:
        assert "independently approved" in str(exc)
    else:
        raise AssertionError("Pending coverage review should block initial assertion")

    _approve_and_capture(db_session, batch, item)
    assertion, created = propose_initial_rule_assertion(
        db_session,
        batch_id=batch.id,
        payload=_payload(),
        actor="assertion-proposer",
    )
    repeated, repeated_created = propose_initial_rule_assertion(
        db_session,
        batch_id=batch.id,
        payload=_payload(),
        actor="assertion-proposer",
    )
    assert created is True
    assert repeated_created is False
    assert repeated.id == assertion.id


def test_initial_rule_assertion_review_and_publication_preserve_provenance(db_session: Session) -> None:
    batch, item = _setup_batch(db_session)
    snapshot = _approve_and_capture(db_session, batch, item)
    assertion, _ = propose_initial_rule_assertion(
        db_session,
        batch_id=batch.id,
        payload=_payload(),
        actor="assertion-proposer",
    )

    try:
        review_initial_rule_assertion(
            db_session,
            assertion.id,
            InitialRuleAssertionReviewRequest(decision="approved", notes="Self review is forbidden."),
            actor="assertion-proposer",
        )
    except ValueError as exc:
        assert "different authenticated reviewer" in str(exc)
    else:
        raise AssertionError("Proposer must not review their own assertion")

    reviewed = review_initial_rule_assertion(
        db_session,
        assertion.id,
        InitialRuleAssertionReviewRequest(
            decision="approved",
            notes="The statement is supported by the exact immutable baseline excerpt.",
        ),
        actor="assertion-reviewer",
    )
    assert reviewed.status == "approved"

    rule = publish_initial_rule_assertion(
        db_session,
        assertion.id,
        InitialRuleAssertionPublishRequest(
            attestation=True,
            publication_notes="Explicitly publish the independently reviewed baseline assertion.",
        ),
        actor="assertion-publisher",
    )
    assert rule.regulatory_change_id is None
    assert rule.initial_rule_assertion_id == assertion.id
    assert rule.source_snapshot_id == snapshot.id
    assert rule.active is True
    assert db_session.exec(select(RegulatoryChange)).all() == []

    persisted = db_session.get(InitialRuleAssertion, assertion.id)
    assert persisted is not None
    assert persisted.status == "published"
    assert persisted.published_rule_id == rule.id
    edges = db_session.exec(
        select(RegulatoryKnowledgeEdge).where(RegulatoryKnowledgeEdge.verified_rule_id == rule.id)
    ).all()
    assert edges
    assert all(edge.regulatory_change_id is None for edge in edges)
    assert all(edge.initial_rule_assertion_id == assertion.id for edge in edges)
    graph = knowledge_graph_payload(db_session, verified_rule_id=rule.id)
    assert graph["human_published_only"] is True
    assert graph["provenance_complete"] is True


def test_initial_rule_assertion_api_requires_separate_review_and_publish(client, db_session: Session) -> None:
    batch, item = _setup_batch(db_session)
    _approve_and_capture(db_session, batch, item)
    request_payload = _payload().model_dump(mode="json")

    proposed = client.post(
        f"/api/v1/global-intelligence/registry/coverage-batches/{batch.id}/initial-rule-assertions",
        json=request_payload,
        headers={"X-GMAI-Role": "admin", "X-GMAI-User": "assertion-proposer"},
    )
    assert proposed.status_code == 201, proposed.text
    assertion_id = proposed.json()["id"]
    assert proposed.json()["created"] is True
    assert proposed.json()["safety"]["source_change_claimed"] is False

    self_review = client.post(
        f"/api/v1/global-intelligence/registry/initial-rule-assertions/{assertion_id}/review",
        json={"decision": "approved", "notes": "This should be rejected."},
        headers={"X-GMAI-Role": "admin", "X-GMAI-User": "assertion-proposer"},
    )
    assert self_review.status_code == 400

    approved = client.post(
        f"/api/v1/global-intelligence/registry/initial-rule-assertions/{assertion_id}/review",
        json={"decision": "approved", "notes": "Exact snapshot evidence independently verified."},
        headers={"X-GMAI-Role": "reviewer", "X-GMAI-User": "assertion-reviewer"},
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "approved"

    published = client.post(
        f"/api/v1/global-intelligence/registry/initial-rule-assertions/{assertion_id}/publish",
        json={"attestation": True, "publication_notes": "Separate explicit publication after review."},
        headers={"X-GMAI-Role": "reviewer", "X-GMAI-User": "assertion-publisher"},
    )
    assert published.status_code == 200, published.text
    assert published.json()["initial_rule_assertion"]["status"] == "published"
    assert published.json()["verified_rule"]["initial_rule_assertion_id"] == assertion_id

    listed = client.get(
        f"/api/v1/global-intelligence/registry/coverage-batches/{batch.id}/initial-rule-assertions"
    )
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["assertions"][0]["status"] == "published"
    assert len(db_session.exec(select(VerifiedRule)).all()) == 1
