from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch
from uuid import UUID

from sqlmodel import Session, select

from app.core.config import settings
from app.models.domain import AuditLog, DocumentExtractionJob, DocumentRecord, DocumentSchemaDefinition
from app.tasks.document_extraction_tasks import run_document_extraction_task

from .conftest import create_lead


def _upload_text_document(client, lead_id: UUID, content: bytes, document_type: str = "passport") -> dict:
    response = client.post(
        "/api/v1/documents/upload",
        data={"lead_id": str(lead_id), "document_type": document_type, "status": "received"},
        files={"file": (f"{document_type}.txt", content, "text/plain")},
    )
    assert response.status_code == 200, response.text
    return response.json()["document"]


def test_server_extraction_uses_versioned_schema_and_requires_review(
    client,
    db_session: Session,
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "document_storage_backend", "local")
    monkeypatch.setattr(settings, "document_local_storage_dir", str(tmp_path))
    lead = create_lead(db_session, name="Document Intelligence Lead")
    seeded = client.post("/api/v1/document-intelligence/schemas/seed")
    assert seeded.status_code == 200, seeded.text
    assert len(seeded.json()) == 6
    assert seeded.json()[0]["version_number"] == 1
    document = _upload_text_document(
        client,
        lead.id,
        b"Name: Ada Lovelace\nNationality: British\nPassport No: X1234567\nExpiry Date: 14-07-2031",
    )

    with patch("app.routers.document_intelligence.run_document_extraction_task.delay") as delay:
        delay.return_value.id = "document-task-123"
        queued = client.post(
            f"/api/v1/document-intelligence/documents/{document['id']}/extract",
            json={"language": "eng"},
        )
    assert queued.status_code == 202, queued.text
    queued_job = queued.json()
    assert queued_job["status"] == "queued"
    assert queued_job["task_id"] == "document-task-123"
    assert queued_job["schema_key"] == "passport_identity_v1"
    assert queued_job["schema_version"] == 1
    assert len(db_session.exec(select(DocumentSchemaDefinition)).all()) == 6

    result = run_document_extraction_task.run(queued_job["id"])
    assert result["status"] == "needs_review"
    detail = client.get(f"/api/v1/document-intelligence/extractions/{queued_job['id']}")
    assert detail.status_code == 200
    extracted = detail.json()
    assert extracted["structured_data"]["full_name"] == "Ada Lovelace"
    assert extracted["structured_data"]["document_number"] == "X1234567"
    assert extracted["structured_data"]["expiry_date"] == "14-07-2031"
    assert extracted["field_confidence"]["document_number"] == 0.8

    approved = client.post(
        f"/api/v1/document-intelligence/extractions/{queued_job['id']}/review",
        json={"decision": "approved", "notes": "Fields compared with the uploaded document."},
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "approved"
    assert approved.json()["reviewed_by"] == "pytest-admin"

    stored_document = db_session.get(DocumentRecord, UUID(document["id"]))
    db_session.refresh(stored_document)
    metadata = json.loads(stored_document.extracted_metadata_json or "{}")
    assert stored_document.status == "received"
    assert metadata["document_intelligence"]["approved_extraction_job_id"] == queued_job["id"]
    assert "does not verify" in metadata["document_intelligence"]["verification_boundary"]

    actions = {
        row.action for row in db_session.exec(
            select(AuditLog).where(AuditLog.entity_type.in_([
                "document_schema_definition", "document_extraction_job",
            ]))
        ).all()
    }
    assert {
        "document_schemas_seeded",
        "document_extraction_queued",
        "document_extraction_completed",
        "document_extraction_approved",
    } <= actions


def test_extraction_fails_closed_when_stored_file_hash_changes(
    client,
    db_session: Session,
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "document_storage_backend", "local")
    monkeypatch.setattr(settings, "document_local_storage_dir", str(tmp_path))
    lead = create_lead(db_session, name="Hash Guard Lead")
    document = _upload_text_document(client, lead.id, b"Name: Grace Hopper\nPassport No: A1234567")
    with patch("app.routers.document_intelligence.run_document_extraction_task.delay") as delay:
        delay.return_value.id = "hash-task"
        queued = client.post(
            f"/api/v1/document-intelligence/documents/{document['id']}/extract",
            json={"language": "eng"},
        )
    assert queued.status_code == 202
    (tmp_path / document["storage_key"]).write_bytes(b"tampered")

    result = run_document_extraction_task.run(queued.json()["id"])
    assert result["status"] == "failed"
    job = db_session.get(DocumentExtractionJob, UUID(queued.json()["id"]))
    db_session.refresh(job)
    assert job.error_code == "extraction_failed"
    assert "hash does not match" in (job.error_message or "")


def test_extraction_rejects_unsupported_document_type(
    client,
    db_session: Session,
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "document_storage_backend", "local")
    monkeypatch.setattr(settings, "document_local_storage_dir", str(tmp_path))
    lead = create_lead(db_session, name="Unsupported Document Lead")
    document = _upload_text_document(client, lead.id, b"miscellaneous", document_type="other")
    response = client.post(
        f"/api/v1/document-intelligence/documents/{document['id']}/extract",
        json={"language": "eng"},
    )
    assert response.status_code == 400
    assert "no published extraction schema" in response.json()["detail"].lower()
