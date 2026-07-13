from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session

from tests.conftest import create_lead


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
    assert response.status_code == 200
    data = response.json()
    assert data["session_token"]
    assert data["lead_id"]
    assert data["status"] == "new"
    assert "Upload passport" in data["checklist"]
    assert "Anerkennung" in data["message"] or "received" in data["message"]


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
    assert create_response.status_code == 200
    token = create_response.json()["session_token"]

    response = client.get(f"/api/v1/public/intake/{token}")
    assert response.status_code == 200
    data = response.json()
    assert data["session_token"] == token
    assert data["status"] == "new"
    assert any("transcripts" in item.lower() for item in data["checklist"])
