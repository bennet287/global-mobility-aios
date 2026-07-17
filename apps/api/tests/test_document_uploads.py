from __future__ import annotations

import hashlib
from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models.domain import AuditLog, DocumentRecord

from .conftest import create_lead


def test_document_upload_stores_file_and_metadata(
    client: TestClient,
    db_session: Session,
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "document_storage_backend", "local")
    monkeypatch.setattr(settings, "document_local_storage_dir", str(tmp_path))
    lead = create_lead(db_session)
    content = b"passport-bytes"

    response = client.post(
        "/api/v1/documents/upload",
        data={
            "lead_id": str(lead.id),
            "document_type": "passport",
            "status": "received",
        },
        files={"file": ("passport.pdf", content, "application/pdf")},
    )

    assert response.status_code == 200
    payload = response.json()
    document = payload["document"]
    assert payload["status"] == "uploaded"
    assert document["lead_id"] == str(lead.id)
    assert document["document_type"] == "passport"
    assert document["filename"] == "passport.pdf"
    assert document["storage_provider"] == "local"
    assert document["mime_type"] == "application/pdf"
    assert document["file_size_bytes"] == len(content)
    assert document["file_hash"] == hashlib.sha256(content).hexdigest()
    assert document["storage_key_exposed"] is False
    assert "storage_key" not in document

    stored = db_session.get(DocumentRecord, UUID(document["id"]))
    assert stored is not None
    assert stored.file_hash == document["file_hash"]
    assert stored.storage_key is not None
    assert (tmp_path / stored.storage_key).read_bytes() == content
    assert stored.uploaded_at is not None

    audit = db_session.exec(select(AuditLog).where(AuditLog.action == "document_uploaded")).first()
    assert audit is not None
    assert audit.entity_id == document["id"]


def test_document_file_metadata_endpoint(client: TestClient, tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "document_storage_backend", "local")
    monkeypatch.setattr(settings, "document_local_storage_dir", str(tmp_path))
    response = client.post(
        "/api/v1/documents/upload",
        data={"document_type": "cv", "status": "needs_review"},
        files={"file": ("cv.txt", b"cv", "text/plain")},
    )
    assert response.status_code == 200
    document_id = response.json()["document"]["id"]

    metadata = client.get(f"/api/v1/documents/{document_id}/file")

    assert metadata.status_code == 200
    payload = metadata.json()
    assert payload["download_supported"] is True
    assert payload["signed_access_required"] is True
    assert payload["direct_object_url"] is None
    assert payload["storage_key_exposed"] is False
    assert payload["document"]["id"] == document_id
