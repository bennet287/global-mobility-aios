from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.domain import (
    AuditLog,
    DocumentRecord,
    FamilyOfficeMobilityAssessment,
    FamilyOfficeMobilityReview,
    Lead,
    MobilityPathway,
    MobilityPathwayVersion,
)


def _lead(session: Session, name: str = "HNWI Principal") -> Lead:
    lead = Lead(
        full_name=name,
        email=f"{name.lower().replace(' ', '.')}@example.com",
        source="family-office-test",
        target_country="Austria",
    )
    session.add(lead)
    session.commit()
    session.refresh(lead)
    return lead


def _document(
    session: Session,
    lead: Lead,
    document_type: str = "source_of_wealth",
    status: str = "verified",
) -> DocumentRecord:
    document = DocumentRecord(
        lead_id=lead.id,
        document_type=document_type,
        filename=f"{document_type}.pdf",
        status=status,
    )
    session.add(document)
    session.commit()
    session.refresh(document)
    return document


def _published_pathway(session: Session) -> MobilityPathway:
    pathway = MobilityPathway(
        pathway_key="at-family-office-test",
        name="Austria Family Office Route",
        country="Austria",
        domain="wealth",
        catalogue_status="active",
        created_by="independent-pathway-publisher",
    )
    session.add(pathway)
    session.commit()
    session.refresh(pathway)
    version = MobilityPathwayVersion(
        pathway_id=pathway.id,
        version_number=1,
        lifecycle_status="published",
        approved_by="independent-pathway-publisher",
        created_by="pathway-proposer",
    )
    session.add(version)
    session.commit()
    return pathway


def _payload(lead: Lead, documents: list[DocumentRecord] | None = None):
    return {
        "lead_id": str(lead.id),
        "family_office_name": "Atlas Family Office",
        "primary_objectives": [
            "Relocate family principals",
            "Coordinate holding-company governance",
        ],
        "target_jurisdictions": ["Austria"],
        "current_tax_residencies": ["United Kingdom"],
        "citizenships": ["United Kingdom"],
        "family_members": 4,
        "structures": [{
            "name": "Atlas Holdings",
            "structure_type": "holding_company",
            "jurisdiction": "United Kingdom",
            "beneficial_ownership_disclosed": True,
        }],
        "asset_classes": ["operating businesses", "listed securities", "real estate"],
        "estimated_net_worth_minor": 2_500_000_000,
        "liquid_assets_minor": 800_000_000,
        "currency": "EUR",
        "source_of_wealth_status": "independently_verified",
        "source_of_funds_status": "documented",
        "beneficial_ownership_documented": True,
        "screening_status": "cleared",
        "pep_or_sanctions_exposure_disclosed": False,
        "tax_adviser_engaged": True,
        "legal_adviser_engaged": True,
        "succession_plan_documented": True,
        "banking_relationships_confirmed": True,
        "disclosed_constraints": ["Family school calendar must be preserved"],
        "document_record_ids": [str(document.id) for document in documents or []],
    }


def test_family_office_assessment_builds_controlled_workstreams(
    client: TestClient,
    db_session: Session,
):
    lead = _lead(db_session)
    wealth = _document(db_session, lead)
    passport = _document(db_session, lead, "passport")
    _published_pathway(db_session)

    response = client.post(
        "/api/v1/family-office-mobility/assessments",
        json=_payload(lead, [wealth, passport]),
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "pending_review"
    assert body["human_review_required"] is True
    assert len(body["workstreams"]) == 5
    assert body["mobility_grounding_score"] == 60.0
    assert body["grounded_pathway_versions"][0]["name"] == "Austria Family Office Route"
    assert "not an eligibility or approval probability" in body["score_semantics"]
    assert body["readiness_score"] < 100
    assert db_session.exec(select(FamilyOfficeMobilityAssessment)).one()
    actions = {
        row.action for row in db_session.exec(select(AuditLog)).all()
    }
    assert "family_office_mobility_assessment_created" in actions


def test_family_office_assessment_rejects_cross_client_evidence(
    client: TestClient,
    db_session: Session,
):
    principal = _lead(db_session, "Principal One")
    other = _lead(db_session, "Principal Two")
    other_document = _document(db_session, other)
    response = client.post(
        "/api/v1/family-office-mobility/assessments",
        json=_payload(principal, [other_document]),
    )
    assert response.status_code == 400
    assert "selected lead" in response.json()["detail"]
    assert db_session.exec(select(FamilyOfficeMobilityAssessment)).all() == []


def test_family_office_assessment_caps_unverified_or_prohibited_execution(
    client: TestClient,
    db_session: Session,
):
    lead = _lead(db_session)
    payload = _payload(lead)
    payload["screening_status"] = "pending"
    payload["beneficial_ownership_documented"] = False
    payload["disclosed_constraints"] = ["Use a nominee owner to hide ownership"]
    response = client.post(
        "/api/v1/family-office-mobility/assessments",
        json=payload,
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["readiness_score"] <= 20
    assert "concealment_evasion_or_misrepresentation_signal" in body["escalation_flags"]
    assert any("prevents operationalization" in blocker for blocker in body["blockers"])


def test_family_office_review_requires_independent_reviewer(
    client: TestClient,
    db_session: Session,
):
    lead = _lead(db_session)
    assessment = client.post(
        "/api/v1/family-office-mobility/assessments",
        json=_payload(lead),
    ).json()
    same_actor = client.post(
        f"/api/v1/family-office-mobility/assessments/{assessment['id']}/reviews",
        json={"decision": "approved", "reason": "Reviewed every controlled workstream."},
    )
    assert same_actor.status_code == 400
    assert "different reviewer" in same_actor.json()["detail"]

    client.headers["X-GMAI-User"] = "independent-family-office-reviewer"
    approved = client.post(
        f"/api/v1/family-office-mobility/assessments/{assessment['id']}/reviews",
        json={"decision": "approved", "reason": "Reviewed every controlled workstream."},
    )
    assert approved.status_code == 201, approved.text
    refreshed = client.get(
        f"/api/v1/family-office-mobility/assessments/{assessment['id']}"
    ).json()
    assert refreshed["status"] == "approved"
    assert refreshed["reviewed_by"] == "independent-family-office-reviewer"
    assert len(db_session.exec(select(FamilyOfficeMobilityReview)).all()) == 1


def test_read_only_role_cannot_create_family_office_assessment(
    raw_client: TestClient,
    db_session: Session,
):
    lead = _lead(db_session)
    raw_client.headers.update({
        "X-GMAI-Role": "read_only",
        "X-GMAI-User": "family-office-observer",
    })
    response = raw_client.post(
        "/api/v1/family-office-mobility/assessments",
        json=_payload(lead),
    )
    assert response.status_code == 403
