from __future__ import annotations

import json
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.domain import IntakeSession, Jurisdiction, Lead


def test_create_public_intake(client: TestClient) -> None:
    payload = {
        "full_name": "Aisha Patel",
        "email": "aisha@example.com",
        "phone": "+91 98765 43210",
        "goal": "I want to work in Germany as a registered nurse",
        "nationality": "India",
        "profession": "Registered Nurse",
        "years_experience": 3,
        "target_country": "Germany",
        "notes": "Has BSc Nursing and 1 year ICU experience.",
    }
    response = client.post("/api/v1/public/intake", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["session_token"]
    assert data["lead_id"]
    assert data["status"] == "new"
    assert "Upload passport" in data["checklist"]
    assert "Anerkennung" in data["message"] or "received" in data["message"]


def test_create_public_intake_austria_normalizes_to_jurisdiction_at(
    client: TestClient,
    db_session: Session,
) -> None:
    payload = {
        "full_name": "Aisha Patel",
        "email": "aisha@example.com",
        "goal": "Work abroad in Austria",
        "nationality": "India",
        "profession": "Software Engineer",
        "years_experience": 5,
        "target_country": "Austria",
        "current_country": "India",
        "job_offer_status": "pending",
        "qualification_recognition": "in_progress",
        "language_level": "B1",
    }
    response = client.post("/api/v1/public/intake", json=payload)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["session_token"]
    assert data["lead_id"]
    assert "Austria" in data["message"]
    checklist = data["checklist"]
    assert any("Austria eligibility" in item for item in checklist)
    assert any("occupation" in item.lower() for item in checklist)
    assert any("qualification recognition" in item.lower() for item in checklist)

    lead = db_session.get(Lead, UUID(data["lead_id"]))
    assert lead is not None
    assert lead.target_country == "Austria"
    assert lead.nationality == "India"
    assert lead.current_country == "India"
    assert lead.occupation_title == "Software Engineer"
    assert lead.years_experience == 5
    assert lead.job_offer_status == "pending"
    assert lead.qualification_recognition == "in_progress"
    assert lead.german_level == "B1"
    assert lead.notes is not None
    assert '"target_country": "Austria"' in lead.notes
    assert '"job_offer_status": "pending"' in lead.notes
    assert '"language_level": "B1"' in lead.notes

    jurisdiction = db_session.exec(
        select(Jurisdiction).where(Jurisdiction.code == "AT")
    ).first()
    assert jurisdiction is not None
    assert jurisdiction.name == "Austria"
    assert jurisdiction.active is True

    leads_response = client.get("/api/v1/leads")
    assert leads_response.status_code == 200
    assert [row["id"] for row in leads_response.json()] == [data["lead_id"]]


def test_get_public_intake(client: TestClient) -> None:
    payload = {
        "full_name": "Carlos Mendez",
        "email": "carlos@example.com",
        "goal": "Study abroad in Canada",
        "nationality": "Brazil",
        "profession": "Student",
        "target_country": "Canada",
    }
    create_response = client.post("/api/v1/public/intake", json=payload)
    assert create_response.status_code == 201
    token = create_response.json()["session_token"]

    response = client.get(f"/api/v1/public/intake/{token}")
    assert response.status_code == 200
    data = response.json()
    assert data["session_token"] == token
    assert data["status"] == "new"
    assert any("transcripts" in item.lower() for item in data["checklist"])


def _austria_payload() -> dict[str, object]:
    return {
        "full_name": "Round Four Austria Test",
        "goal": "Work abroad in Austria",
        "nationality": "India",
        "profession": "Software Engineer",
        "years_experience": 4,
        "target_country": " austria ",
        "current_country": "India",
        "job_offer_status": "none",
        "qualification_recognition": "unknown",
        "language_level": "A2",
        "notes": "Synthetic local-only persistence regression.",
        "submission_key": "public-intake-regression-0001",
    }


@pytest.mark.parametrize("email", [None, "", "   ", "valid@example.com"])
def test_optional_email_normalization_creates_one_atomic_case(
    client: TestClient,
    db_session: Session,
    email: str | None,
) -> None:
    payload = _austria_payload()
    payload["submission_key"] = f"public-intake-email-{email!r}"
    if email is not None:
        payload["email"] = email

    response = client.post("/api/v1/public/intake", json=payload)

    assert response.status_code == 201, response.text
    assert len(db_session.exec(select(Lead)).all()) == 1
    sessions = list(db_session.exec(select(IntakeSession)).all())
    assert len(sessions) == 1
    lead = db_session.get(Lead, sessions[0].lead_id)
    assert lead is not None
    assert lead.email == ("valid@example.com" if email == "valid@example.com" else None)


def test_malformed_email_is_rejected_without_false_persistence(
    client: TestClient,
    db_session: Session,
) -> None:
    payload = _austria_payload()
    payload["email"] = "not-an-email"

    response = client.post("/api/v1/public/intake", json=payload)

    assert response.status_code == 422
    assert list(db_session.exec(select(Lead)).all()) == []
    assert list(db_session.exec(select(IntakeSession)).all()) == []


def test_austria_intake_preserves_facts_and_returns_case_reference(
    client: TestClient,
    db_session: Session,
) -> None:
    response = client.post("/api/v1/public/intake", json=_austria_payload())

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["case_reference"].startswith("AT-")
    lead = db_session.get(Lead, UUID(data["lead_id"]))
    assert lead is not None
    assert lead.target_country == "Austria"
    assert lead.nationality == "India"
    assert lead.current_country == "India"
    assert lead.occupation_title == "Software Engineer"
    assert lead.years_experience == 4
    assert lead.job_offer_status == "none"
    assert lead.qualification_recognition == "unknown"
    assert lead.german_level == "A2"
    intake_session = db_session.exec(
        select(IntakeSession).where(IntakeSession.lead_id == lead.id)
    ).one()
    answers = json.loads(intake_session.answers_json or "{}")
    assert answers == {
        "current_country": "India",
        "goal": "Work abroad in Austria",
        "job_offer_status": "none",
        "language_level": "A2",
        "nationality": "India",
        "profession": "Software Engineer",
        "qualification_recognition": "unknown",
        "target_country": "Austria",
        "years_experience": 4.0,
    }


def test_duplicate_submission_key_returns_same_lead_without_duplicates(
    client: TestClient,
    db_session: Session,
) -> None:
    first = client.post("/api/v1/public/intake", json=_austria_payload())
    second = client.post("/api/v1/public/intake", json=_austria_payload())

    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    assert second.json()["lead_id"] == first.json()["lead_id"]
    assert first.json()["idempotent_replay"] is False
    assert second.json()["idempotent_replay"] is True
    assert len(db_session.exec(select(Lead)).all()) == 1
    assert len(db_session.exec(select(IntakeSession)).all()) == 1


def test_submission_key_cannot_be_reused_for_different_case_details(
    client: TestClient,
    db_session: Session,
) -> None:
    first = client.post("/api/v1/public/intake", json=_austria_payload())
    changed = _austria_payload()
    changed["profession"] = "Civil Engineer"
    second = client.post("/api/v1/public/intake", json=changed)

    assert first.status_code == 201
    assert second.status_code == 409
    assert len(db_session.exec(select(Lead)).all()) == 1
    assert len(db_session.exec(select(IntakeSession)).all()) == 1


def test_failed_atomic_persistence_returns_human_error_without_rows(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_commit = db_session.commit

    def fail_commit() -> None:
        raise RuntimeError("synthetic database failure")

    monkeypatch.setattr(db_session, "commit", fail_commit)
    response = client.post("/api/v1/public/intake", json=_austria_payload())
    monkeypatch.setattr(db_session, "commit", original_commit)

    assert response.status_code == 503
    assert response.json() == {"detail": "Your case could not be created. Please try again."}
    assert list(db_session.exec(select(Lead)).all()) == []
    assert list(db_session.exec(select(IntakeSession)).all()) == []
