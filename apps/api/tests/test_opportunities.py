from __future__ import annotations

from sqlmodel import Session

from app.models.domain import Lead, LeadIntent, LeadStatus, Opportunity


def _create_lead(session: Session, **kwargs) -> Lead:
    lead = Lead(
        full_name=kwargs.get("full_name", "Test Lead"),
        email=kwargs.get("email"),
        target_country=kwargs.get("target_country", "Germany"),
        intent=kwargs.get("intent", LeadIntent.overseas_job),
        status=LeadStatus.new,
        notes=kwargs.get("notes"),
    )
    session.add(lead)
    session.commit()
    session.refresh(lead)
    return lead


def test_seed_opportunities(client, db_session: Session) -> None:
    response = client.post("/api/v1/opportunities/seed")
    assert response.status_code == 200
    data = response.json()
    assert data["seeded"] > 0

    # Idempotent.
    response2 = client.post("/api/v1/opportunities/seed")
    assert response2.json()["seeded"] == 0


def test_list_opportunities(client, db_session: Session) -> None:
    opp = Opportunity(
        title="Test Opportunity",
        country="germany",
        domain="work",
        source="manual",
    )
    db_session.add(opp)
    db_session.commit()

    response = client.get("/api/v1/opportunities")
    assert response.status_code == 200
    data = response.json()
    assert any(o["title"] == "Test Opportunity" for o in data)


def test_match_opportunities(client, db_session: Session) -> None:
    # Seed default opportunities.
    client.post("/api/v1/opportunities/seed")
    lead = _create_lead(
        db_session,
        full_name="Nurse Lead",
        target_country="Germany",
        intent=LeadIntent.overseas_job,
        notes="registered nurse with 3 years experience",
    )

    response = client.post(f"/api/v1/opportunities/match/{lead.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["lead_id"] == str(lead.id)
    assert len(data["matches"]) > 0
    assert data["top_opportunity_id"] is not None
    scores = [m["match_score"] for m in data["matches"]]
    assert scores == sorted(scores, reverse=True)
