from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models.domain import AuditLog, DocumentAccessGrant, DocumentRecord
from app.services.document_access import now_utc
from app.services.document_storage import _policy_allows_public_read

from .conftest import create_lead


def _configure_local(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(settings, "app_env", "local")
    monkeypatch.setattr(settings, "document_storage_backend", "local")
    monkeypatch.setattr(settings, "document_local_storage_dir", str(tmp_path))
    monkeypatch.setattr(settings, "document_access_token_secret", "pytest-document-access-secret")
    monkeypatch.setattr(settings, "document_storage_production_strict", False)
    monkeypatch.setattr(settings, "document_access_default_ttl_seconds", 300)
    monkeypatch.setattr(settings, "document_access_max_ttl_seconds", 900)
    monkeypatch.setattr(settings, "document_access_default_max_uses", 1)
    monkeypatch.setattr(settings, "document_access_max_uses", 5)


def _upload(client: TestClient, lead_id: str, content: bytes = b"secure-passport") -> dict:
    response = client.post(
        "/api/v1/documents/upload",
        data={"lead_id": lead_id, "document_type": "passport", "status": "verified"},
        files={"file": ("passport.pdf", content, "application/pdf")},
    )
    assert response.status_code == 200
    return response.json()["document"]


def test_signed_document_access_is_short_lived_single_use_and_audited(
    client: TestClient,
    db_session: Session,
    tmp_path: Path,
    monkeypatch,
) -> None:
    _configure_local(monkeypatch, tmp_path)
    lead = create_lead(db_session)
    document = _upload(client, str(lead.id))
    stored_before = db_session.get(DocumentRecord, UUID(document["id"]))
    assert stored_before is not None
    status_before = stored_before.status

    issued = client.post(
        f"/api/v1/document-access/documents/{document['id']}/grants",
        json={
            "lead_id": str(lead.id),
            "purpose": "document_verification",
            "ttl_seconds": 120,
            "max_uses": 1,
        },
    )
    assert issued.status_code == 201
    payload = issued.json()
    assert payload["direct_object_url"] is None
    assert payload["storage_credentials_exposed"] is False
    assert payload["storage_key_exposed"] is False
    assert payload["grant"]["storage_key_exposed"] is False
    assert "storage_key" not in payload["grant"]
    token = payload["token"]
    grant_id = payload["grant"]["id"]

    listed = client.get(f"/api/v1/document-access/grants?lead_id={lead.id}")
    assert listed.status_code == 200
    assert listed.json()[0]["token_returned"] is False
    assert "token" not in listed.json()[0]

    content = client.post("/api/v1/document-access/content", json={"token": token})
    assert content.status_code == 200
    assert content.content == b"secure-passport"
    assert content.headers["cache-control"].startswith("no-store")
    assert content.headers["x-content-type-options"] == "nosniff"
    assert content.headers["x-gmai-document-grant"] == grant_id

    consumed = db_session.get(DocumentAccessGrant, UUID(grant_id))
    assert consumed is not None
    assert consumed.status == "consumed"
    assert consumed.use_count == 1
    stored_after = db_session.get(DocumentRecord, UUID(document["id"]))
    assert stored_after is not None
    assert stored_after.status == status_before

    second = client.post("/api/v1/document-access/content", json={"token": token})
    assert second.status_code == 403
    actions = db_session.exec(select(AuditLog.action).where(AuditLog.entity_id == grant_id)).all()
    assert "document_access_grant_created" in actions
    assert "document_accessed" in actions
    assert "document_access_denied" in actions


def test_document_access_enforces_actor_role_scope_and_revocation(
    raw_client: TestClient,
    db_session: Session,
    tmp_path: Path,
    monkeypatch,
) -> None:
    _configure_local(monkeypatch, tmp_path)
    raw_client.headers.update({"X-GMAI-Role": "admin", "X-GMAI-User": "grant-admin"})
    lead = create_lead(db_session)
    document = _upload(raw_client, str(lead.id))

    issued = raw_client.post(
        f"/api/v1/document-access/documents/{document['id']}/grants",
        json={
            "lead_id": str(lead.id),
            "purpose": "operator_review",
            "recipient_username": "readonly-recipient",
            "recipient_role": "read_only",
            "max_uses": 2,
        },
    )
    assert issued.status_code == 201
    token = issued.json()["token"]
    grant_id = issued.json()["grant"]["id"]

    wrong_actor = raw_client.post("/api/v1/document-access/content", json={"token": token})
    assert wrong_actor.status_code == 403

    raw_client.headers.update({"X-GMAI-Role": "read_only", "X-GMAI-User": "readonly-recipient"})
    allowed = raw_client.post("/api/v1/document-access/content", json={"token": token})
    assert allowed.status_code == 200

    raw_client.headers.update({"X-GMAI-Role": "admin", "X-GMAI-User": "grant-admin"})
    revoked = raw_client.post(
        f"/api/v1/document-access/grants/{grant_id}/revoke",
        json={"reason": "Review completed; further access is no longer required."},
    )
    assert revoked.status_code == 200
    assert revoked.json()["status"] == "revoked"

    raw_client.headers.update({"X-GMAI-Role": "read_only", "X-GMAI-User": "readonly-recipient"})
    denied = raw_client.post("/api/v1/document-access/content", json={"token": token})
    assert denied.status_code == 403


def test_document_access_fails_closed_for_expired_or_altered_objects(
    client: TestClient,
    db_session: Session,
    tmp_path: Path,
    monkeypatch,
) -> None:
    _configure_local(monkeypatch, tmp_path)
    lead = create_lead(db_session)
    document = _upload(client, str(lead.id), b"original")
    stored_document = db_session.get(DocumentRecord, UUID(document["id"]))
    assert stored_document is not None and stored_document.storage_key

    issued = client.post(
        f"/api/v1/document-access/documents/{document['id']}/grants",
        json={"lead_id": str(lead.id), "purpose": "consistency_review", "max_uses": 2},
    )
    assert issued.status_code == 201
    token = issued.json()["token"]
    grant_id = UUID(issued.json()["grant"]["id"])

    (tmp_path / stored_document.storage_key).write_bytes(b"tampered")
    altered = client.post("/api/v1/document-access/content", json={"token": token})
    assert altered.status_code == 403
    assert "stored_object_missing_or_altered" in altered.json()["detail"]

    (tmp_path / stored_document.storage_key).write_bytes(b"original")
    grant = db_session.get(DocumentAccessGrant, grant_id)
    assert grant is not None
    grant.expires_at = now_utc() - timedelta(seconds=1)
    db_session.add(grant)
    db_session.commit()

    expired = client.post("/api/v1/document-access/content", json={"token": token})
    assert expired.status_code == 403
    assert "grant_expired" in expired.json()["detail"]
    db_session.refresh(grant)
    assert grant.status == "expired"


def test_production_storage_posture_fails_closed_and_public_policy_is_detected(
    client: TestClient,
    db_session: Session,
    tmp_path: Path,
    monkeypatch,
) -> None:
    _configure_local(monkeypatch, tmp_path)
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "document_storage_production_strict", True)
    monkeypatch.setattr(settings, "document_storage_backend", "local")
    monkeypatch.setattr(settings, "document_storage_allow_local_in_production", False)
    monkeypatch.setattr(settings, "document_storage_retention_days", 0)
    monkeypatch.setattr(settings, "document_storage_backup_strategy", "")
    monkeypatch.setattr(settings, "document_storage_recovery_tested_at", "")

    posture = client.get("/api/v1/document-access/storage-posture")
    assert posture.status_code == 200
    assert posture.json()["ready"] is False
    assert "production_requires_minio" in posture.json()["failures"]

    lead = create_lead(db_session)
    doc = DocumentRecord(
        lead_id=lead.id,
        document_type="passport",
        filename="passport.pdf",
        storage_provider="local",
        storage_key="documents/test/passport.pdf",
        file_hash="0" * 64,
        file_size_bytes=1,
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)
    issued = client.post(
        f"/api/v1/document-access/documents/{doc.id}/grants",
        json={"lead_id": str(lead.id), "purpose": "operator_review"},
    )
    assert issued.status_code == 503

    public_policy = '{"Statement":[{"Effect":"Allow","Principal":"*","Action":"s3:GetObject","Resource":"arn:aws:s3:::gmai-documents/*"}]}'
    private_policy = '{"Statement":[{"Effect":"Deny","Principal":"*","Action":"s3:GetObject","Resource":"arn:aws:s3:::gmai-documents/*"}]}'
    assert _policy_allows_public_read(public_policy, "gmai-documents") is True
    assert _policy_allows_public_read(private_policy, "gmai-documents") is False
