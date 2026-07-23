from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.domain import (
    AuditLog,
    MobilityPathway,
    MobilityPathwayVersion,
    OfficialSource,
    SourceSnapshot,
)


def _grounding(session: Session, *, country: str = "portugal"):
    source = OfficialSource(
        country=country,
        domain="investment",
        name=f"{country.title()} investment authority",
        url=f"https://investment.gov.{country[:2]}/program",
        active=True,
    )
    session.add(source)
    session.commit()
    session.refresh(source)
    snapshot = SourceSnapshot(
        official_source_id=source.id,
        url=source.url,
        content_hash=f"{country}-investment-snapshot",
        content_text="Official investment route, threshold, due diligence, family and presence requirements.",
        status="captured",
        retrieval_method="http",
    )
    pathway = MobilityPathway(
        pathway_key=f"{country}-investor-route",
        name=f"{country.title()} Investor Route",
        country=country,
        domain="investment",
        catalogue_status="active",
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
        lifecycle_status="published",
        official_source_id=source.id,
        source_snapshot_id=snapshot.id,
        created_by="pathway-proposer",
        approved_by="pathway-reviewer",
    )
    session.add(version)
    session.commit()
    session.refresh(version)
    return pathway, version, source, snapshot


def _payload(pathway, version, source, snapshot):
    return {
        "program_key": "pt-governed-investor-route",
        "name": "Portugal Governed Investor Route",
        "country": "Portugal",
        "program_type": "residence_by_investment",
        "pathway_id": str(pathway.id),
        "description": "A source-grounded operator catalogue record.",
        "pathway_version_id": str(version.id),
        "official_source_id": str(source.id),
        "source_snapshot_id": str(snapshot.id),
        "minimum_commitment_minor": 50000000,
        "currency": "eur",
        "investment_options": [{"type": "regulated_fund", "minimum_minor": 50000000}],
        "holding_period_text": "Maintain the qualifying position for the official required period.",
        "physical_presence_text": "Presence requirements must be re-verified before action.",
        "family_scope": ["spouse", "dependent_children"],
        "due_diligence": ["lawful source of funds", "criminal record review", "sanctions screening"],
        "fees": {"government_fees": "Verify against the current official schedule"},
        "benefits": ["Residence route subject to authority approval"],
        "risks": ["Capital at risk", "Rules and qualifying assets can change"],
    }


def test_program_requires_independent_publication_and_records_audit(client: TestClient, db_session: Session):
    pathway, version, source, snapshot = _grounding(db_session)
    created = client.post("/api/v1/investment-mobility/programs", json=_payload(pathway, version, source, snapshot))
    assert created.status_code == 201, created.text
    draft = created.json()
    assert draft["catalogue_status"] == "draft"
    assert draft["current_version"]["currency"] == "EUR"
    publish = client.post(
        f"/api/v1/investment-mobility/versions/{draft['current_version']['id']}/publish",
        json={"review_notes": "Reviewed against the pinned official source snapshot."},
    )
    assert publish.status_code == 400
    assert "independent reviewer" in publish.json()["detail"]

    client.headers["X-GMAI-User"] = "pytest-investment-reviewer"
    published = client.post(
        f"/api/v1/investment-mobility/versions/{draft['current_version']['id']}/publish",
        json={"review_notes": "Reviewed against the pinned official source snapshot."},
    )
    assert published.status_code == 200, published.text
    body = published.json()
    assert body["catalogue_status"] == "active"
    assert body["current_version"]["lifecycle_status"] == "published"
    assert body["current_version"]["approved_by"] == "pytest-investment-reviewer"
    actions = {row.action for row in db_session.exec(select(AuditLog)).all()}
    assert {"investment_mobility_program_created", "investment_mobility_program_version_published"} <= actions


def test_program_rejects_mismatched_country_source(client: TestClient, db_session: Session):
    pathway, version, source, snapshot = _grounding(db_session)
    payload = _payload(pathway, version, source, snapshot)
    payload["country"] = "Austria"
    response = client.post("/api/v1/investment-mobility/programs", json=payload)
    assert response.status_code == 400
    assert "country" in response.json()["detail"].lower()


def test_program_rejects_guaranteed_outcome_claim(client: TestClient, db_session: Session):
    pathway, version, source, snapshot = _grounding(db_session)
    payload = _payload(pathway, version, source, snapshot)
    payload["benefits"] = ["Guaranteed citizenship for the whole family"]
    response = client.post("/api/v1/investment-mobility/programs", json=payload)
    assert response.status_code == 422
    assert "guaranteed" in response.text.lower()


def test_new_version_supersedes_published_version(client: TestClient, db_session: Session):
    pathway, pathway_version, source, snapshot = _grounding(db_session)
    created = client.post("/api/v1/investment-mobility/programs", json=_payload(pathway, pathway_version, source, snapshot)).json()
    client.headers["X-GMAI-User"] = "first-reviewer"
    first = client.post(
        f"/api/v1/investment-mobility/versions/{created['current_version']['id']}/publish",
        json={"review_notes": "First evidence review completed independently."},
    ).json()
    version_payload = _payload(pathway, pathway_version, source, snapshot)
    for key in ("program_key", "name", "country", "program_type", "pathway_id", "description"):
        version_payload.pop(key)
    version_payload["minimum_commitment_minor"] = 55000000
    client.headers["X-GMAI-User"] = "second-proposer"
    second = client.post(
        f"/api/v1/investment-mobility/programs/{first['id']}/versions", json=version_payload,
    )
    assert second.status_code == 201, second.text
    client.headers["X-GMAI-User"] = "second-reviewer"
    published = client.post(
        f"/api/v1/investment-mobility/versions/{second.json()['id']}/publish",
        json={"review_notes": "Changed threshold independently verified against the snapshot."},
    )
    assert published.status_code == 200, published.text
    versions = published.json()["versions"]
    assert versions[0]["version_number"] == 2
    assert versions[0]["lifecycle_status"] == "published"
    assert versions[1]["lifecycle_status"] == "superseded"


def test_read_only_role_cannot_create_program(raw_client: TestClient, db_session: Session):
    pathway, version, source, snapshot = _grounding(db_session)
    raw_client.headers.update({"X-GMAI-Role": "read_only", "X-GMAI-User": "readonly-investment"})
    response = raw_client.post("/api/v1/investment-mobility/programs", json=_payload(pathway, version, source, snapshot))
    assert response.status_code == 403


def test_published_program_grounds_business_wealth_advisory(client: TestClient, db_session: Session):
    pathway, pathway_version, source, snapshot = _grounding(db_session)
    draft = client.post(
        "/api/v1/investment-mobility/programs", json=_payload(pathway, pathway_version, source, snapshot),
    ).json()
    client.headers["X-GMAI-User"] = "program-reviewer"
    published = client.post(
        f"/api/v1/investment-mobility/versions/{draft['current_version']['id']}/publish",
        json={"review_notes": "Official program conditions independently reviewed."},
    )
    assert published.status_code == 200, published.text

    assessment = client.post("/api/v1/business-mobility-advisory/assessments", json={
        "primary_intent": "passive_investment",
        "situation": "The client seeks a transparent family residence strategy using documented investment capital.",
        "target_countries": ["Portugal"],
        "capital_available_minor": 75000000,
        "net_worth_minor": 250000000,
        "currency": "EUR",
        "timeline_months": 18,
        "family_relocation": True,
        "lawful_source_of_funds_confirmed": True,
        "risk_disclosures": [],
        "document_record_ids": [],
    })
    assert assessment.status_code == 201, assessment.text
    options = assessment.json()["strategy_options"]
    assert options[0]["verified_programs"][0]["program_id"] == published.json()["id"]
    assert options[0]["verification_state"] == "published_program_grounded"
