from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.domain import (
    AuditLog,
    DocumentRecord,
    Lead,
    OfficialSource,
    SourceSnapshot,
    TaxResidencyAssessment,
    TaxResidencyAssessmentReview,
    TaxTreatyEvidence,
    TaxTreatyEvidenceDecision,
)


def _lead(session: Session, name: str = "Cross Border Principal") -> Lead:
    row = Lead(
        full_name=name,
        email=f"{name.lower().replace(' ', '.')}@example.com",
        source="tax-residency-test",
        target_country="Germany",
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def _document(session: Session, lead: Lead) -> DocumentRecord:
    row = DocumentRecord(
        lead_id=lead.id,
        document_type="travel_and_residence_ledger",
        filename="residence-ledger.pdf",
        status="verified",
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def _source_snapshot(
    session: Session,
    *,
    country: str = "Austria",
) -> tuple[OfficialSource, SourceSnapshot]:
    source = OfficialSource(
        country=country,
        domain="tax",
        name=f"{country} tax authority",
        url=f"https://tax.example/{country.lower()}-germany-treaty",
        active=True,
    )
    session.add(source)
    session.commit()
    session.refresh(source)
    snapshot = SourceSnapshot(
        official_source_id=source.id,
        url=source.url,
        content_hash=f"{country.lower()}-germany-treaty-v1",
        content_text="Official treaty text and protocol captured for controlled review.",
        status="captured",
        retrieval_method="http",
    )
    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)
    return source, snapshot


def _evidence_payload(source: OfficialSource, snapshot: SourceSnapshot) -> dict:
    return {
        "evidence_key": "at-de-residency-tie-breaker-2026",
        "jurisdiction_a": "Austria",
        "jurisdiction_b": "Germany",
        "topic": "residency_tie_breaker",
        "title": "Austria Germany residence coordination provision",
        "statement": (
            "The official text records the ordered treaty factors a licensed "
            "specialist must analyse after separate domestic residence conclusions."
        ),
        "official_source_id": str(source.id),
        "source_snapshot_id": str(snapshot.id),
        "effective_from": "2020-01-01T00:00:00Z",
    }


def _assessment_payload(
    lead: Lead,
    document: DocumentRecord,
    evidence_id: str,
) -> dict:
    return {
        "lead_id": str(lead.id),
        "tax_year": 2026,
        "current_residencies": ["Austria"],
        "target_residencies": ["Germany"],
        "citizenships": ["Austria"],
        "presence_periods": [
            {
                "jurisdiction": "Austria",
                "days": 170,
                "period_start": "2026-01-01",
                "period_end": "2026-06-19",
            },
            {
                "jurisdiction": "Germany",
                "days": 196,
                "period_start": "2026-06-20",
                "period_end": "2026-12-31",
            },
        ],
        "available_homes": [
            {
                "jurisdiction": "Austria",
                "home_type": "owned",
                "continuously_available": True,
            },
            {
                "jurisdiction": "Germany",
                "home_type": "leased",
                "continuously_available": True,
            },
        ],
        "spouse_or_dependant_jurisdictions": ["Germany"],
        "employment_jurisdictions": ["Germany"],
        "director_or_control_jurisdictions": ["Austria", "Germany"],
        "business_structure_jurisdictions": ["Austria"],
        "income_categories": ["employment", "dividends"],
        "planned_departure_date": "2026-06-19",
        "planned_arrival_date": "2026-06-20",
        "objectives": ["Coordinate a documented relocation and filing sequence"],
        "tax_adviser_engaged": True,
        "home_jurisdiction_adviser_engaged": True,
        "destination_adviser_engaged": True,
        "document_record_ids": [str(document.id)],
        "treaty_evidence_ids": [evidence_id],
    }


def _publish_evidence(
    client: TestClient,
    source: OfficialSource,
    snapshot: SourceSnapshot,
) -> dict:
    proposed = client.post(
        "/api/v1/tax-residency/treaty-evidence",
        json=_evidence_payload(source, snapshot),
    )
    assert proposed.status_code == 201, proposed.text
    client.headers["X-GMAI-User"] = "independent-treaty-reviewer"
    published = client.post(
        f"/api/v1/tax-residency/treaty-evidence/{proposed.json()['id']}/decisions",
        json={
            "decision": "approved",
            "reason": "Matched the statement to the exact official snapshot and effective dates.",
        },
    )
    assert published.status_code == 200, published.text
    return published.json()


def test_treaty_evidence_requires_independent_publication(
    client: TestClient,
    db_session: Session,
):
    source, snapshot = _source_snapshot(db_session)
    proposed = client.post(
        "/api/v1/tax-residency/treaty-evidence",
        json=_evidence_payload(source, snapshot),
    )
    assert proposed.status_code == 201, proposed.text
    assert proposed.json()["status"] == "pending_review"
    same_actor = client.post(
        f"/api/v1/tax-residency/treaty-evidence/{proposed.json()['id']}/decisions",
        json={
            "decision": "approved",
            "reason": "I checked the official-source snapshot and effective date.",
        },
    )
    assert same_actor.status_code == 400
    assert "different reviewer" in same_actor.json()["detail"]

    client.headers["X-GMAI-User"] = "independent-treaty-reviewer"
    approved = client.post(
        f"/api/v1/tax-residency/treaty-evidence/{proposed.json()['id']}/decisions",
        json={
            "decision": "approved",
            "reason": "Matched the statement to the official snapshot and effective date.",
        },
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "published"
    assert len(db_session.exec(select(TaxTreatyEvidenceDecision)).all()) == 1
    actions = {row.action for row in db_session.exec(select(AuditLog)).all()}
    assert "tax_treaty_evidence_created" in actions
    assert "tax_treaty_evidence_reviewed" in actions


def test_assessment_builds_issue_matrix_from_published_evidence(
    client: TestClient,
    db_session: Session,
):
    lead = _lead(db_session)
    document = _document(db_session, lead)
    source, snapshot = _source_snapshot(db_session)
    evidence = _publish_evidence(client, source, snapshot)

    response = client.post(
        "/api/v1/tax-residency/assessments",
        json=_assessment_payload(lead, document, evidence["id"]),
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "specialist_review_required"
    assert body["human_review_required"] is True
    assert body["treaty_grounding_score"] == 100.0
    assert body["specialist_coordination_score"] == 100.0
    assert len(body["workstreams"]) == 5
    assert any(
        issue["issue_key"] == "dual_residence_and_tie_breaker"
        for issue in body["issue_matrix"]
    )
    assert "not a tax-residency determination" in body["score_semantics"]
    assert db_session.exec(select(TaxResidencyAssessment)).one()


def test_assessment_rejects_unpublished_or_out_of_period_evidence(
    client: TestClient,
    db_session: Session,
):
    lead = _lead(db_session)
    document = _document(db_session, lead)
    source, snapshot = _source_snapshot(db_session)
    proposed = client.post(
        "/api/v1/tax-residency/treaty-evidence",
        json=_evidence_payload(source, snapshot),
    ).json()
    unpublished = client.post(
        "/api/v1/tax-residency/assessments",
        json=_assessment_payload(lead, document, proposed["id"]),
    )
    assert unpublished.status_code == 400
    assert "published" in unpublished.json()["detail"]

    client.headers["X-GMAI-User"] = "independent-treaty-reviewer"
    client.post(
        f"/api/v1/tax-residency/treaty-evidence/{proposed['id']}/decisions",
        json={
            "decision": "approved",
            "reason": "Matched to the official source and effective period.",
        },
    )
    row = db_session.get(TaxTreatyEvidence, UUID(proposed["id"]))
    assert row is not None
    row.effective_from = datetime(2027, 1, 1, tzinfo=timezone.utc)
    db_session.add(row)
    db_session.commit()
    expired = client.post(
        "/api/v1/tax-residency/assessments",
        json=_assessment_payload(lead, document, proposed["id"]),
    )
    assert expired.status_code == 400
    assert "not effective" in expired.json()["detail"]


def test_assessment_rejects_cross_client_document(
    client: TestClient,
    db_session: Session,
):
    lead = _lead(db_session, "Principal One")
    other = _lead(db_session, "Principal Two")
    other_document = _document(db_session, other)
    source, snapshot = _source_snapshot(db_session)
    evidence = _publish_evidence(client, source, snapshot)
    response = client.post(
        "/api/v1/tax-residency/assessments",
        json=_assessment_payload(lead, other_document, evidence["id"]),
    )
    assert response.status_code == 400
    assert "selected lead" in response.json()["detail"]


def test_prohibited_tax_evasion_signal_caps_readiness(
    client: TestClient,
    db_session: Session,
):
    lead = _lead(db_session)
    document = _document(db_session, lead)
    source, snapshot = _source_snapshot(db_session)
    evidence = _publish_evidence(client, source, snapshot)
    payload = _assessment_payload(lead, document, evidence["id"])
    payload["disclosed_constraints"] = ["Hide days and backdate lease records"]
    response = client.post("/api/v1/tax-residency/assessments", json=payload)
    assert response.status_code == 201, response.text
    assert response.json()["readiness_score"] <= 10
    assert (
        "tax_evasion_concealment_or_misrepresentation_signal"
        in response.json()["escalation_flags"]
    )


def test_assessment_review_requires_independent_specialist(
    client: TestClient,
    db_session: Session,
):
    lead = _lead(db_session)
    document = _document(db_session, lead)
    source, snapshot = _source_snapshot(db_session)
    evidence = _publish_evidence(client, source, snapshot)
    assessment = client.post(
        "/api/v1/tax-residency/assessments",
        json=_assessment_payload(lead, document, evidence["id"]),
    ).json()
    same_actor = client.post(
        f"/api/v1/tax-residency/assessments/{assessment['id']}/reviews",
        json={
            "decision": "specialist_reviewed",
            "reason": "Reviewed the domestic analyses and treaty evidence.",
        },
    )
    assert same_actor.status_code == 400

    client.headers["X-GMAI-User"] = "licensed-tax-specialist"
    reviewed = client.post(
        f"/api/v1/tax-residency/assessments/{assessment['id']}/reviews",
        json={
            "decision": "specialist_reviewed",
            "reason": "Reviewed the domestic analyses and treaty evidence.",
        },
    )
    assert reviewed.status_code == 201, reviewed.text
    refreshed = client.get(
        f"/api/v1/tax-residency/assessments/{assessment['id']}"
    ).json()
    assert refreshed["status"] == "specialist_reviewed"
    assert len(db_session.exec(select(TaxResidencyAssessmentReview)).all()) == 1


def test_read_only_role_cannot_mutate_tax_residency(
    raw_client: TestClient,
    db_session: Session,
):
    source, snapshot = _source_snapshot(db_session)
    raw_client.headers.update({
        "X-GMAI-Role": "read_only",
        "X-GMAI-User": "tax-observer",
    })
    response = raw_client.post(
        "/api/v1/tax-residency/treaty-evidence",
        json=_evidence_payload(source, snapshot),
    )
    assert response.status_code == 403
