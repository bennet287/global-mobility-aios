from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.domain import (
    AuditLog,
    CountryRankingAssessment,
    Jurisdiction,
    OfficialSource,
    SourceSnapshot,
    VerifiedRule,
    now_utc,
)
from tests.test_pathway_catalogue import _evidence, _lead_with_profile, _pathway_payload


def _country_evidence(session: Session, *, code: str, country: str):
    normalized = country.lower()
    jurisdiction = Jurisdiction(code=code, name=country, region="Test Region")
    session.add(jurisdiction)
    session.commit()
    session.refresh(jurisdiction)
    source = OfficialSource(
        jurisdiction_id=jurisdiction.id,
        country=normalized,
        domain="work",
        name=f"{country} Mobility Authority",
        url=f"https://example.gov.{code.lower()}/work",
        source_type="government",
        active=True,
    )
    session.add(source)
    session.commit()
    session.refresh(source)
    snapshot = SourceSnapshot(
        official_source_id=source.id,
        url=source.url,
        content_hash=f"{normalized}-ranking-snapshot",
        content_text=f"Official {country} work pathway requirements.",
        status="captured",
        retrieval_method="http",
    )
    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)
    rule = VerifiedRule(
        country=normalized,
        domain="work",
        rule_key=f"{normalized}-ranking-rule",
        statement=f"Applicants must meet the reviewed {country} work requirements.",
        official_source_id=source.id,
        jurisdiction_id=jurisdiction.id,
        source_snapshot_id=snapshot.id,
        confidence=0.96,
        active=True,
        approved_by="pytest-reviewer",
        published_at=now_utc(),
    )
    session.add(rule)
    session.commit()
    session.refresh(rule)
    return jurisdiction, source, snapshot, rule


def _publish(client: TestClient, payload: dict) -> dict:
    created = client.post("/api/v1/pathways", json=payload)
    assert created.status_code == 201, created.text
    published = client.post(
        f"/api/v1/pathways/versions/{created.json()['current_version']['id']}/publish",
        json={"review_notes": "Reviewed country-ranking evidence and long-term metadata."},
        headers={"X-GMAI-Role": "admin", "X-GMAI-User": "pytest-pathway-reviewer"},
    )
    assert published.status_code == 200, published.text
    return published.json()


def test_reviewed_country_ranking_preserves_coverage_boundary_and_long_term_uncertainty(
    client: TestClient,
    db_session: Session,
) -> None:
    de_jurisdiction, de_source, de_snapshot, de_rule = _evidence(db_session)
    de_rule.published_at = now_utc()
    db_session.add(de_rule)
    db_session.commit()
    germany = _pathway_payload(de_jurisdiction, de_source, de_snapshot, de_rule)
    germany["metadata"] = {
        "long_term_mobility": {
            "permanent_residence": {
                "status": "conditional",
                "summary": "Permanent residence requires a later reviewed residence-stage assessment.",
                "minimum_years": 5,
                "dependencies": ["continuous lawful residence", "language and integration evidence"],
            },
            "citizenship": {
                "status": "conditional",
                "summary": "Citizenship requires a separate future eligibility review.",
                "minimum_years": 8,
                "dependencies": ["residence history", "naturalisation requirements"],
            },
        }
    }
    _publish(client, germany)

    ca_jurisdiction, ca_source, ca_snapshot, ca_rule = _country_evidence(
        db_session,
        code="CA",
        country="Canada",
    )
    canada = _pathway_payload(ca_jurisdiction, ca_source, ca_snapshot, ca_rule)
    canada.update({
        "pathway_key": "ca-reviewed-worker",
        "name": "Canada Reviewed Worker Pathway",
        "country": "Canada",
        "official_source_id": str(ca_source.id),
        "source_snapshot_id": str(ca_snapshot.id),
        "verified_rule_ids": [str(ca_rule.id)],
        "eligibility_criteria": {
            **canada["eligibility_criteria"],
            "required_skills": ["software engineering"],
            "minimum_funds_eur": 18000,
        },
        "costs": {"currency": "EUR"},
        "processing_time": {},
        "metadata": {},
    })
    _publish(client, canada)

    lead, _, _ = _lead_with_profile(client, db_session)
    payload = {
        "explicit_user_acceptance": True,
        "user_attestation": "The client explicitly accepted a reviewed cross-country comparison using the current profile.",
        "notes": "Country ranking discussed as an internal planning assessment with no eligibility guarantee.",
        "limit_countries": 10,
    }
    response = client.post(f"/api/v1/pathways/country-rankings/{lead.id}", json=payload)
    assert response.status_code == 201, response.text
    ranking = response.json()
    assert ranking["status"] == "reviewed_catalogue_only"
    assert ranking["scope"]["global_coverage_claim_ready"] is False
    assert ranking["scope"]["complete_global_ranking_claim_allowed"] is False
    assert ranking["scope"]["ranking_scope"] == "reviewed_published_catalogue_only"
    assert ranking["scope"]["published_catalogue_countries"] == 2
    assert [item["country"] for item in ranking["countries"]] == ["germany", "canada"]
    assert ranking["countries"][0]["rank"] == 1
    assert ranking["countries"][0]["primary_pathway"]["pathway"]["name"] == "Germany Skilled Worker Pathway"
    dependencies = {item["stage"]: item for item in ranking["countries"][0]["long_term_dependencies"]}
    assert dependencies["permanent_residence"]["status"] == "recorded"
    assert dependencies["permanent_residence"]["minimum_years"] == 5.0
    assert dependencies["citizenship"]["status"] == "recorded"
    canada_dependencies = ranking["countries"][1]["long_term_dependencies"]
    assert all(item["status"] == "not_recorded" for item in canada_dependencies)
    assert ranking["countries"][1]["uncertainty"]["level"] in {"medium", "high"}
    assert "not a complete global ranking" in ranking["summary"].lower()
    assert ranking["human_review_required"] is True

    repeated = client.post(f"/api/v1/pathways/country-rankings/{lead.id}", json=payload)
    assert repeated.status_code == 201
    assert repeated.json()["assessment_id"] == ranking["assessment_id"]
    assert len(db_session.exec(select(CountryRankingAssessment)).all()) == 1

    latest = client.get(f"/api/v1/pathways/country-rankings/{lead.id}/latest")
    history = client.get(f"/api/v1/pathways/country-rankings/{lead.id}")
    assert latest.status_code == 200
    assert latest.json()["assessment_id"] == ranking["assessment_id"]
    assert history.status_code == 200
    assert len(history.json()) == 1
    actions = {
        row.action
        for row in db_session.exec(
            select(AuditLog).where(AuditLog.entity_type == "country_ranking_assessment")
        ).all()
    }
    assert "country_ranking_generated" in actions


def test_country_ranking_requires_explicit_acceptance(client: TestClient, db_session: Session) -> None:
    lead, _, _ = _lead_with_profile(client, db_session)
    response = client.post(
        f"/api/v1/pathways/country-rankings/{lead.id}",
        json={
            "explicit_user_acceptance": False,
            "user_attestation": "The client did not accept a country reassessment.",
            "notes": "Do not generate.",
        },
    )
    assert response.status_code == 400
    assert "explicit user acceptance" in response.json()["detail"].lower()
    assert db_session.exec(select(CountryRankingAssessment)).all() == []
