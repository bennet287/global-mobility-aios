from __future__ import annotations

from uuid import UUID

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.domain import (
    AuditLog,
    HumanReview,
    OfficialSource,
    RegulatoryAuthority,
    RegulatoryChange,
    SourceMonitor,
    SourceSnapshot,
    VerifiedRule,
    Jurisdiction,
    now_utc,
)


def test_regulatory_source_onboarding_is_validated_audited_and_idempotent(
    client: TestClient,
    db_session: Session,
) -> None:
    payload = {
        "jurisdiction_code": "NZ",
        "jurisdiction_name": "New Zealand",
        "jurisdiction_type": "country",
        "region": "Oceania",
        "authority_name": "Immigration New Zealand",
        "authority_type": "immigration_authority",
        "authority_website_url": "https://www.immigration.govt.nz/",
        "authority_domains": ["visa", "work"],
        "source_name": "New Zealand work visa guidance",
        "source_url": "https://www.immigration.govt.nz/new-zealand-visas/visas/visa/accredited-employer-work-visa",
        "source_domain": "visa",
        "source_type": "government",
        "schedule_minutes": 720,
        "fetch_method": "http",
        "allowed_domains": ["immigration.govt.nz"],
        "max_redirects": 2,
        "parser_profile": "gazette_html_v1",
        "parser_config": {"notice_kind": "immigration"},
    }

    response = client.post("/api/v1/regulatory-intelligence/source-onboarding", json=payload)
    assert response.status_code == 201
    created = response.json()
    assert created["jurisdiction"]["code"] == "NZ"
    assert created["authority"]["name"] == "Immigration New Zealand"
    assert created["official_source"]["regulatory_authority_id"] == created["authority"]["id"]
    assert created["monitor"]["allowed_domains"] == ["immigration.govt.nz"]
    assert created["monitor"]["schedule_minutes"] == 720
    assert created["monitor"]["parser_profile"] == "gazette_html_v1"
    assert created["monitor"]["parser_config"] == {"notice_kind": "immigration"}

    payload["schedule_minutes"] = 360
    repeated = client.post("/api/v1/regulatory-intelligence/source-onboarding", json=payload)
    assert repeated.status_code == 201
    assert repeated.json()["jurisdiction"]["id"] == created["jurisdiction"]["id"]
    assert repeated.json()["authority"]["id"] == created["authority"]["id"]
    assert repeated.json()["official_source"]["id"] == created["official_source"]["id"]
    assert repeated.json()["monitor"]["id"] == created["monitor"]["id"]
    assert repeated.json()["monitor"]["schedule_minutes"] == 360

    assert len(db_session.exec(select(Jurisdiction)).all()) == 1
    assert len(db_session.exec(select(RegulatoryAuthority)).all()) == 1
    assert len(db_session.exec(select(OfficialSource)).all()) == 1
    assert len(db_session.exec(select(SourceMonitor)).all()) == 1
    audit = db_session.exec(
        select(AuditLog).where(AuditLog.action == "regulatory_source_onboarded")
    ).first()
    assert audit is not None
    assert audit.actor == "pytest-admin"

    dashboard = client.get("/api/v1/regulatory-intelligence/dashboard")
    assert dashboard.status_code == 200
    coverage = dashboard.json()["coverage"]
    assert coverage["jurisdictions"][0]["monitoring_coverage_percent"] == 100.0
    assert coverage["jurisdictions"][0]["freshness_percent"] == 0.0
    assert coverage["authorities"][0]["official_sources"] == 1
    visa_coverage = next(row for row in coverage["domains"] if row["domain"] == "visa")
    assert visa_coverage["monitored_sources"] == 1

    invalid = dict(payload)
    invalid.update({
        "jurisdiction_code": "XX",
        "jurisdiction_name": "Invalid Test Jurisdiction",
        "source_url": "http://private.example.test/rules",
        "allowed_domains": ["private.example.test"],
    })
    invalid_response = client.post("/api/v1/regulatory-intelligence/source-onboarding", json=invalid)
    assert invalid_response.status_code == 400
    assert "must use HTTPS" in invalid_response.json()["detail"]
    assert db_session.exec(select(Jurisdiction).where(Jurisdiction.code == "XX")).first() is None


def test_regulatory_change_is_review_gated_before_rule_publication(
    client: TestClient,
    db_session: Session,
) -> None:
    assert client.post("/api/v1/official-sources/seed").status_code == 200
    source = db_session.exec(
        select(OfficialSource).where(OfficialSource.country == "germany")
    ).first()
    assert source is not None

    jurisdiction_response = client.post(
        "/api/v1/regulatory-intelligence/jurisdictions",
        json={
            "code": "DE",
            "name": "Germany",
            "jurisdiction_type": "country",
            "region": "Europe",
        },
    )
    assert jurisdiction_response.status_code == 201
    jurisdiction_id = jurisdiction_response.json()["jurisdiction"]["id"]

    authority_response = client.post(
        "/api/v1/regulatory-intelligence/authorities",
        json={
            "jurisdiction_id": jurisdiction_id,
            "name": "Federal Foreign Office",
            "authority_type": "immigration_authority",
            "website_url": "https://www.auswaertiges-amt.de/",
            "domains": ["visa", "immigration"],
            "official_source_ids": [str(source.id)],
        },
    )
    assert authority_response.status_code == 201
    db_session.refresh(source)
    assert str(source.jurisdiction_id) == jurisdiction_id
    assert source.regulatory_authority_id is not None

    monitor_response = client.post(
        "/api/v1/regulatory-intelligence/source-monitors",
        json={"official_source_id": str(source.id), "schedule_minutes": 60, "fetch_method": "http"},
    )
    assert monitor_response.status_code == 201

    baseline = client.post(
        f"/api/v1/regulatory-intelligence/sources/{source.id}/snapshots",
        json={
            "content_text": "Skilled worker visa minimum salary requirement is EUR 40,000.",
            "retrieval_method": "http",
            "parser_version": "test-v1",
        },
    )
    assert baseline.status_code == 201
    assert baseline.json()["snapshot"]["status"] == "baseline"
    assert baseline.json()["change"] is None

    unchanged = client.post(
        f"/api/v1/regulatory-intelligence/sources/{source.id}/snapshots",
        json={
            "content_text": "Skilled worker visa minimum salary requirement is EUR 40,000.",
            "retrieval_method": "http",
        },
    )
    assert unchanged.status_code == 201
    assert unchanged.json()["unchanged"] is True
    assert unchanged.json()["change"] is None

    changed = client.post(
        f"/api/v1/regulatory-intelligence/sources/{source.id}/snapshots",
        json={
            "content_text": "Skilled worker visa minimum salary requirement is EUR 45,000.",
            "retrieval_method": "http",
            "change_type": "salary_threshold_change",
            "title": "Skilled worker salary threshold changed",
            "summary": "The official salary threshold changed from EUR 40,000 to EUR 45,000.",
            "materiality": "critical",
        },
    )
    assert changed.status_code == 201
    change_payload = changed.json()["change"]
    assert change_payload["status"] == "pending_review"
    assert change_payload["change_type"] == "salary_threshold_change"
    change_id = change_payload["id"]

    early_publish = client.post(
        f"/api/v1/regulatory-intelligence/changes/{change_id}/publish",
        json={
            "rule_key": "skilled_worker_minimum_salary",
            "statement": "The minimum salary is EUR 45,000.",
            "reviewer": "pytest-reviewer",
        },
    )
    assert early_publish.status_code == 400

    review_response = client.post(
        f"/api/v1/regulatory-intelligence/changes/{change_id}/review",
        json={
            "decision": "approved",
            "reviewer": "pytest-reviewer",
            "notes": "Confirmed against the captured official source.",
        },
    )
    assert review_response.status_code == 200
    assert review_response.json()["change"]["status"] == "approved"

    publish_response = client.post(
        f"/api/v1/regulatory-intelligence/changes/{change_id}/publish",
        json={
            "rule_key": "skilled_worker_minimum_salary",
            "statement": "The skilled worker minimum salary requirement is EUR 45,000.",
            "reviewer": "pytest-reviewer",
            "confidence": 1.0,
        },
    )
    assert publish_response.status_code == 200
    rule_payload = publish_response.json()["verified_rule"]
    assert rule_payload["regulatory_change_id"] == change_id
    assert rule_payload["approved_by"] == "pytest-reviewer"

    assert len(db_session.exec(select(SourceSnapshot)).all()) >= 3
    assert db_session.exec(select(SourceMonitor)).one().last_checked_at is not None
    assert db_session.exec(select(RegulatoryChange)).one().status == "published"
    assert db_session.exec(select(VerifiedRule)).one().active is True
    review = db_session.exec(
        select(HumanReview).where(HumanReview.regulatory_change_id == UUID(change_id))
    ).one()
    assert str(getattr(review.status, "value", review.status)) == "resolved"
    audit_actions = {row.action for row in db_session.exec(select(AuditLog)).all()}
    assert {
        "regulatory_change_detected",
        "regulatory_change_reviewed",
        "verified_rule_published",
    }.issubset(audit_actions)

    dashboard = client.get("/api/v1/regulatory-intelligence/dashboard")
    assert dashboard.status_code == 200
    assert dashboard.json()["counts"]["monitors"] == 1
    assert dashboard.json()["counts"]["changes_published"] == 1
    snapshots = client.get("/api/v1/regulatory-intelligence/snapshots")
    assert snapshots.status_code == 200
    assert snapshots.json()["total_returned"] >= 3
    rules = client.get("/api/v1/regulatory-intelligence/verified-rules", params={"active": True})
    assert rules.status_code == 200
    assert rules.json()["total_returned"] == 1


def test_verified_rule_can_be_superseded_and_retired(client: TestClient, db_session: Session) -> None:
    jurisdiction = Jurisdiction(code="CA", name="Canada")
    db_session.add(jurisdiction)
    db_session.flush()
    source = OfficialSource(
        jurisdiction_id=jurisdiction.id,
        country="canada",
        domain="visa",
        name="IRCC",
        url="https://www.canada.ca/immigration",
    )
    db_session.add(source)
    db_session.flush()
    first_snapshot = SourceSnapshot(
        official_source_id=source.id,
        url=source.url,
        content_hash="first",
        content_text="Threshold one",
        status="changed",
    )
    second_snapshot = SourceSnapshot(
        official_source_id=source.id,
        url=source.url,
        content_hash="second",
        content_text="Threshold two",
        status="changed",
    )
    db_session.add(first_snapshot)
    db_session.add(second_snapshot)
    db_session.flush()
    first_change = RegulatoryChange(
        jurisdiction_id=jurisdiction.id,
        official_source_id=source.id,
        current_snapshot_id=first_snapshot.id,
        domain="visa",
        change_type="salary_threshold_change",
        title="First threshold",
        summary="First approved threshold",
        status="approved",
        reviewed_by="reviewer",
        reviewed_at=now_utc(),
    )
    second_change = RegulatoryChange(
        jurisdiction_id=jurisdiction.id,
        official_source_id=source.id,
        previous_snapshot_id=first_snapshot.id,
        current_snapshot_id=second_snapshot.id,
        domain="visa",
        change_type="salary_threshold_change",
        title="Replacement threshold",
        summary="Replacement approved threshold",
        status="approved",
        reviewed_by="reviewer",
        reviewed_at=now_utc(),
    )
    db_session.add(first_change)
    db_session.add(second_change)
    db_session.commit()

    first_response = client.post(
        f"/api/v1/regulatory-intelligence/changes/{first_change.id}/publish",
        json={
            "rule_key": "minimum_salary",
            "statement": "The minimum salary is CAD 50,000.",
            "reviewer": "reviewer",
        },
    )
    assert first_response.status_code == 200
    first_rule_id = first_response.json()["verified_rule"]["id"]

    second_response = client.post(
        f"/api/v1/regulatory-intelligence/changes/{second_change.id}/publish",
        json={
            "rule_key": "minimum_salary",
            "statement": "The minimum salary is CAD 55,000.",
            "reviewer": "reviewer",
            "supersedes_rule_id": first_rule_id,
        },
    )
    assert second_response.status_code == 200
    second_rule_id = second_response.json()["verified_rule"]["id"]
    assert second_response.json()["verified_rule"]["supersedes_rule_id"] == first_rule_id

    first_rule = db_session.get(VerifiedRule, UUID(first_rule_id))
    assert first_rule is not None
    assert first_rule.active is False
    assert first_rule.retired_by == "reviewer"
    assert first_rule.effective_to is not None

    retire_response = client.post(
        f"/api/v1/regulatory-intelligence/verified-rules/{second_rule_id}/retire",
        json={"reviewer": "senior-reviewer", "reason": "Program closed by the authority."},
    )
    assert retire_response.status_code == 200
    assert retire_response.json()["verified_rule"]["active"] is False
    assert retire_response.json()["verified_rule"]["retirement_reason"] == "Program closed by the authority."

    actions = {row.action for row in db_session.exec(select(AuditLog)).all()}
    assert "verified_rule_superseded" in actions
    assert "verified_rule_retired" in actions


def test_reviewer_can_review_but_operator_cannot(raw_client: TestClient) -> None:
    raw_client.headers.update({"X-GMAI-Role": "operator", "X-GMAI-User": "operator"})
    response = raw_client.post(
        "/api/v1/regulatory-intelligence/jurisdictions",
        json={"code": "AT", "name": "Austria"},
    )
    assert response.status_code == 403

    raw_client.headers.update({"X-GMAI-Role": "reviewer", "X-GMAI-User": "reviewer"})
    response = raw_client.post(
        "/api/v1/regulatory-intelligence/jurisdictions",
        json={"code": "AT", "name": "Austria"},
    )
    assert response.status_code == 201
