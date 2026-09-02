from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session

from tests.conftest import create_lead


def test_ocr_extract_creates_document(client: TestClient, db_session: Session) -> None:
    lead = create_lead(db_session, name="OCR Lead", target_country="Germany")
    payload = {
        "lead_id": str(lead.id),
        "document_type": "cv",
        "filename": "cv.png",
        "extracted_text": "Name: John Doe\nProfession: Software Engineer\n5 years of experience",
        "language": "eng",
        "confidence": 0.92,
    }
    response = client.post("/api/v1/documents/ocr-extract", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["document_type"] == "cv"
    assert "Software Engineer" in data["parsed_fields"]["profession"]
    assert data["parsed_fields"]["years_experience"] == 5.0
    assert data["document_id"]


def test_ocr_extract_updates_lead_notes(client: TestClient, db_session: Session) -> None:
    lead = create_lead(db_session, name="OCR Lead 2", target_country="Canada")
    payload = {
        "lead_id": str(lead.id),
        "document_type": "passport",
        "filename": "passport.png",
        "extracted_text": "Nationality: Indian\nPassport No: J1234567",
        "confidence": 0.95,
    }
    response = client.post("/api/v1/documents/ocr-extract", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["parsed_fields"]["nationality"]
    assert "J1234567" in data["parsed_fields"]["document_number"]
