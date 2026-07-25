from sqlmodel import select

from app.models.domain import (
    AuditLog,
    MobilityPathway,
    MobilityPathwayVersion,
)
from tests.conftest import create_document, create_lead


BASE_PAYLOAD = {
    "primary_intent": "launch_startup",
    "situation": "I want to relocate as a founder, launch a software company, and move my family within twelve months.",
    "target_countries": ["Portugal"],
    "capital_available_minor": 15000000,
    "currency": "EUR",
    "founder_experience_years": 8,
    "timeline_months": 12,
    "family_relocation": True,
    "lawful_source_of_funds_confirmed": True,
}


def _published_business_pathway(db_session):
    pathway = MobilityPathway(
        pathway_key="pt-reviewed-founder-route",
        name="Portugal reviewed founder route",
        country="portugal",
        domain="entrepreneur",
        catalogue_status="published",
        created_by="pytest-admin",
    )
    db_session.add(pathway)
    db_session.flush()
    version = MobilityPathwayVersion(
        pathway_id=pathway.id,
        version_number=1,
        lifecycle_status="published",
        verified_rule_ids_json="[]",
        human_review_required=True,
        approved_by="independent-publisher",
        created_by="pytest-admin",
    )
    db_session.add(version)
    db_session.commit()
    return pathway, version


def test_advisory_produces_ranked_options_without_claiming_probability(client):
    response = client.post("/api/v1/business-mobility-advisory/assessments", json=BASE_PAYLOAD)
    assert response.status_code == 201, response.text
    body = response.json()
    assert len(body["strategy_options"]) == 3
    assert body["strategy_options"][0]["fit_score"] >= body["strategy_options"][1]["fit_score"]
    assert body["feasibility_score"] <= 49
    assert body["pathway_grounding_score"] == 0
    assert "not a probability" in body["score_semantics"]
    assert body["human_review_required"] is True
    assert body["status"] == "pending_review"


def test_advisory_grounds_options_in_published_business_pathways(client, db_session):
    pathway, version = _published_business_pathway(db_session)
    response = client.post("/api/v1/business-mobility-advisory/assessments", json=BASE_PAYLOAD)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["pathway_grounding_score"] > 0
    references = [item for option in body["strategy_options"] for item in option["published_pathways"]]
    assert any(item["pathway_id"] == str(pathway.id) for item in references)
    assert any(item["pathway_version_id"] == str(version.id) for item in references)
    assert body["strategy_options"][0]["verification_state"] == "published_pathway_grounded"


def test_advisory_controlled_documents_must_belong_to_selected_lead(client, db_session):
    lead = create_lead(db_session, name="Business Client", target_country="Portugal")
    other = create_lead(db_session, name="Other Owner", target_country="Portugal")
    wrong_document = create_document(db_session, other, document_type="bank_statement")
    response = client.post(
        "/api/v1/business-mobility-advisory/assessments",
        json={**BASE_PAYLOAD, "lead_id": str(lead.id), "document_record_ids": [str(wrong_document.id)]},
    )
    assert response.status_code == 400
    assert "selected lead" in response.json()["detail"]


def test_advisory_flags_deception_and_returns_lawful_remediation(client):
    response = client.post(
        "/api/v1/business-mobility-advisory/assessments",
        json={
            **BASE_PAYLOAD,
            "situation": "I want to use a nominee owner to hide ownership and backdate company records before relocating.",
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert "prohibited_conduct_signal" in body["risk_flags"]
    assert body["feasibility_score"] <= 20
    assert body["escalation_required"] is True
    assert any("cannot be operationalized" in blocker for blocker in body["blockers"])
    assert any("licensed specialist" in action for action in body["next_actions"])


def test_advisory_review_requires_a_different_operator(client, db_session):
    created = client.post("/api/v1/business-mobility-advisory/assessments", json=BASE_PAYLOAD).json()
    self_review = client.post(
        f"/api/v1/business-mobility-advisory/assessments/{created['id']}/reviews",
        json={"decision": "approved", "reason": "Commercial strategy and limitations reviewed."},
    )
    assert self_review.status_code == 400
    reviewed = client.post(
        f"/api/v1/business-mobility-advisory/assessments/{created['id']}/reviews",
        json={"decision": "approved", "reason": "Commercial strategy and limitations independently reviewed."},
        headers={"X-GMAI-Role": "admin", "X-GMAI-User": "business-reviewer"},
    )
    assert reviewed.status_code == 201, reviewed.text
    refreshed = client.get(f"/api/v1/business-mobility-advisory/assessments/{created['id']}").json()
    assert refreshed["status"] == "approved"
    assert refreshed["reviewed_by"] == "business-reviewer"
    actions = db_session.exec(select(AuditLog.action).where(
        AuditLog.source == "business_mobility_advisory_v11_4"
    )).all()
    assert actions == ["business_mobility_advisory_created", "business_mobility_advisory_reviewed"]


def test_read_only_role_cannot_generate_advisory(raw_client):
    raw_client.headers.update({"X-GMAI-Role": "read_only", "X-GMAI-User": "readonly-user"})
    response = raw_client.post("/api/v1/business-mobility-advisory/assessments", json=BASE_PAYLOAD)
    assert response.status_code == 403


ADVISE_PAYLOAD = {
    "primary_intent": "launch_startup",
    "situation": "I want to relocate as a founder, launch a software company, and move my family within twelve months.",
    "target_countries": ["Portugal"],
    "capital_available_minor": 15000000,
    "currency": "EUR",
    "founder_experience_years": 8,
    "timeline_months": 12,
    "family_relocation": True,
    "lawful_source_of_funds_confirmed": True,
}


def test_advise_returns_solution_with_success_meter(client):
    response = client.post("/api/v1/business-mobility-advisory/advise", json=ADVISE_PAYLOAD)
    assert response.status_code == 200, response.text
    body = response.json()
    assert "summary" in body
    assert "recommended_solution" in body
    assert body["overall_success_meter"] >= 0 and body["overall_success_meter"] <= 100
    assert body["recommended_solution"]["success_meter"] >= 0
    assert "success_band" in body["recommended_solution"]
    assert "actions" in body["recommended_solution"]
    assert "disclaimer" in body
    assert "human_review_required" in body


def test_advise_grounds_solution_in_published_pathways(client, db_session):
    pathway, version = _published_business_pathway(db_session)
    response = client.post("/api/v1/business-mobility-advisory/advise", json=ADVISE_PAYLOAD)
    assert response.status_code == 200, response.text
    body = response.json()
    grounding = body["recommended_solution"]["grounding_pathways"]
    assert any(item["pathway_id"] == str(pathway.id) for item in grounding)
    assert body["overall_success_meter"] > 0


def test_advise_flags_prohibited_conduct_and_lowers_success_meter(client):
    response = client.post(
        "/api/v1/business-mobility-advisory/advise",
        json={
            **ADVISE_PAYLOAD,
            "situation": "I want to use a nominee owner to hide ownership and backdate company records before relocating.",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert "prohibited_conduct_signal" in body["risk_flags"]
    assert body["human_review_required"] is True
    assert body["overall_success_meter"] <= 20


def test_advise_provides_situation_specific_actions_and_factors(client):
    response = client.post("/api/v1/business-mobility-advisory/advise", json=ADVISE_PAYLOAD)
    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["recommended_solution"]["actions"]) >= 3
    assert len(body["critical_factors"]) >= 3
    # Actions should reference the specific intent (startup/founder), not be purely generic.
    action_text = " ".join(body["recommended_solution"]["actions"]).lower()
    assert any(keyword in action_text for keyword in ["founder", "startup", "operating plan", "substance"])


def test_advise_still_recommends_lawful_alternative_for_risky_situation(client):
    response = client.post(
        "/api/v1/business-mobility-advisory/advise",
        json={
            **ADVISE_PAYLOAD,
            "situation": "I have a prior visa refusal and want to launch a software company in Portugal with my family.",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert "specialist_risk_disclosure" in body["risk_flags"]
    # A recommendation must still be returned, not just a refusal.
    assert body["recommended_solution"]["success_meter"] > 0
    assert len(body["alternative_options"]) >= 1
    assert body["human_review_required"] is True


def test_advise_success_meter_responds_to_capital_and_timeline(client):
    strong_payload = {
        **ADVISE_PAYLOAD,
        "capital_available_minor": 5_000_000_00,
        "net_worth_minor": 10_000_000_00,
        "lawful_source_of_funds_confirmed": True,
        "timeline_months": 18,
    }
    response = client.post("/api/v1/business-mobility-advisory/advise", json=strong_payload)
    assert response.status_code == 200, response.text
    strong = response.json()

    weak_payload = {
        **ADVISE_PAYLOAD,
        "capital_available_minor": None,
        "net_worth_minor": None,
        "founder_experience_years": 0,
        "timeline_months": 3,
    }
    response = client.post("/api/v1/business-mobility-advisory/advise", json=weak_payload)
    assert response.status_code == 200, response.text
    weak = response.json()

    assert strong["overall_success_meter"] > weak["overall_success_meter"]
