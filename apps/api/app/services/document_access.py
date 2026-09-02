from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

from sqlmodel import Session, select

from app.core.auth import ROLES
from app.core.config import settings
from app.models.domain import DocumentAccessGrant, DocumentRecord
from app.services.audit_log import record_audit
from app.services.document_storage import (
    document_storage_client,
    document_storage_posture,
    sha256_hex,
    validate_document_storage_configuration,
)


DOCUMENT_ACCESS_PURPOSES = frozenset({
    "operator_review",
    "document_verification",
    "consistency_review",
    "application_preparation",
    "client_request_fulfilment",
    "legal_compliance_export",
})


@dataclass(frozen=True)
class AccessedDocument:
    content: bytes
    filename: str
    mime_type: str
    grant: DocumentAccessGrant


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _token_secret() -> bytes:
    configured = settings.document_access_token_secret.strip()
    secret = configured or settings.jwt_secret.strip()
    if not secret:
        raise RuntimeError("Document access token secret is not configured")
    if settings.document_storage_production_strict and not configured:
        raise RuntimeError("Production strict mode requires a separate document access token secret")
    return secret.encode("utf-8")


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * ((4 - len(value) % 4) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))


def _sign(payload: str) -> str:
    return hmac.new(_token_secret(), payload.encode("ascii"), hashlib.sha256).hexdigest()


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _hash_storage_key(storage_key: str) -> str:
    return hashlib.sha256(storage_key.encode("utf-8")).hexdigest()


def _safe_grant_state(grant: DocumentAccessGrant) -> dict[str, Any]:
    return {
        "id": str(grant.id),
        "document_id": str(grant.document_id),
        "lead_id": str(grant.lead_id),
        "issued_to": grant.issued_to,
        "issued_role": grant.issued_role,
        "purpose": grant.purpose,
        "status": grant.status,
        "expires_at": grant.expires_at.isoformat(),
        "max_uses": grant.max_uses,
        "use_count": grant.use_count,
        "storage_provider": grant.storage_provider,
        "filename": grant.filename,
        "created_by": grant.created_by,
        "last_accessed_by": grant.last_accessed_by,
        "last_accessed_at": grant.last_accessed_at.isoformat() if grant.last_accessed_at else None,
        "revoked_by": grant.revoked_by,
        "revoked_at": grant.revoked_at.isoformat() if grant.revoked_at else None,
        "revocation_reason": grant.revocation_reason,
        "created_at": grant.created_at.isoformat(),
        "updated_at": grant.updated_at.isoformat(),
    }


def grant_read(grant: DocumentAccessGrant) -> dict[str, Any]:
    payload = _safe_grant_state(grant)
    payload.update({
        "remaining_uses": max(0, grant.max_uses - grant.use_count),
        "expired": _as_utc(grant.expires_at) <= now_utc(),
        "token_returned": False,
        "storage_key_exposed": False,
    })
    return payload


def storage_posture_read() -> dict[str, Any]:
    posture = document_storage_posture()
    posture.update({
        "signed_access_enabled": True,
        "direct_object_urls_enabled": False,
        "storage_credentials_exposed": False,
        "unrestricted_object_keys_exposed": False,
        "allowed_purposes": sorted(DOCUMENT_ACCESS_PURPOSES),
    })
    return posture


def _verify_document_content(document: DocumentRecord) -> bytes:
    if not document.storage_key or document.storage_provider not in {"local", "minio"}:
        raise ValueError("Document is not stored in a supported server-readable backend")
    if not document.file_hash or document.file_size_bytes is None:
        raise ValueError("Document integrity metadata is incomplete")
    storage = document_storage_client(document.storage_provider)
    content = storage.get_document(document.storage_key)
    if len(content) != document.file_size_bytes:
        raise ValueError("Stored document size does not match immutable upload metadata")
    if sha256_hex(content) != document.file_hash:
        raise ValueError("Stored document hash does not match immutable upload metadata")
    return content


def issue_document_access_grant(
    session: Session,
    document_id: UUID,
    *,
    actor: str,
    actor_role: str,
    lead_id: UUID,
    purpose: str,
    ttl_seconds: Optional[int] = None,
    max_uses: Optional[int] = None,
    recipient_username: Optional[str] = None,
    recipient_role: Optional[str] = None,
) -> tuple[DocumentAccessGrant, str]:
    validate_document_storage_configuration()
    purpose = purpose.strip().lower()
    if purpose not in DOCUMENT_ACCESS_PURPOSES:
        raise ValueError("Unsupported document access purpose")
    if actor_role not in ROLES:
        raise ValueError("Unsupported actor role")

    target_username = (recipient_username or actor).strip()
    target_role = (recipient_role or actor_role).strip().lower()
    if not target_username or target_role not in ROLES:
        raise ValueError("A valid recipient username and role are required")
    if actor_role != "admin" and (target_username != actor or target_role != actor_role):
        raise ValueError("Only administrators can issue document access to another authenticated actor")

    ttl = ttl_seconds or settings.document_access_default_ttl_seconds
    if ttl < 30 or ttl > settings.document_access_max_ttl_seconds:
        raise ValueError(
            f"Document access TTL must be between 30 and {settings.document_access_max_ttl_seconds} seconds"
        )
    uses = max_uses or settings.document_access_default_max_uses
    if uses < 1 or uses > settings.document_access_max_uses:
        raise ValueError(f"Document access max_uses must be between 1 and {settings.document_access_max_uses}")

    document = session.get(DocumentRecord, document_id)
    if document is None:
        raise ValueError("Document not found")
    if document.lead_id is None or document.lead_id != lead_id:
        raise ValueError("Document lead scope does not match the requested access scope")
    _verify_document_content(document)

    issued_at = now_utc()
    expires_at = issued_at + timedelta(seconds=ttl)
    grant = DocumentAccessGrant(
        token_hash="pending",
        document_id=document.id,
        lead_id=lead_id,
        issued_to=target_username,
        issued_role=target_role,
        purpose=purpose,
        status="active",
        expires_at=expires_at,
        max_uses=uses,
        use_count=0,
        document_file_hash=document.file_hash or "",
        document_file_size_bytes=document.file_size_bytes or 0,
        storage_provider=document.storage_provider or "",
        storage_key_hash=_hash_storage_key(document.storage_key or ""),
        mime_type=document.mime_type,
        filename=document.filename,
        created_by=actor,
        created_at=issued_at,
        updated_at=issued_at,
    )
    session.add(grant)
    session.flush()
    token_payload = {
        "v": 1,
        "grant_id": str(grant.id),
        "document_id": str(document.id),
        "lead_id": str(lead_id),
        "issued_to": target_username,
        "issued_role": target_role,
        "purpose": purpose,
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
        "nonce": secrets.token_urlsafe(16),
    }
    encoded = _b64encode(json.dumps(token_payload, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    token = f"{encoded}.{_sign(encoded)}"
    grant.token_hash = _hash_token(token)
    session.add(grant)
    record_audit(
        session,
        action="document_access_grant_created",
        entity_type="document_access_grant",
        entity_id=grant.id,
        after_state=_safe_grant_state(grant),
        reason=f"Short-lived document access issued for {purpose}.",
        actor=actor,
        source="document_access_v9_5",
    )
    session.commit()
    session.refresh(grant)
    return grant, token


def _decode_token(token: str) -> dict[str, Any]:
    if not token or len(token) > 4096:
        raise ValueError("Invalid document access token")
    try:
        payload, signature = token.split(".", 1)
    except ValueError as exc:
        raise ValueError("Invalid document access token") from exc
    if not hmac.compare_digest(signature, _sign(payload)):
        raise ValueError("Invalid document access token signature")
    try:
        data = json.loads(_b64decode(payload).decode("utf-8"))
    except Exception as exc:
        raise ValueError("Invalid document access token payload") from exc
    required = {"grant_id", "document_id", "lead_id", "issued_to", "issued_role", "purpose", "exp"}
    if not required.issubset(data):
        raise ValueError("Incomplete document access token payload")
    return data


def _deny(
    session: Session,
    *,
    actor: str,
    reason_code: str,
    grant: Optional[DocumentAccessGrant] = None,
) -> None:
    record_audit(
        session,
        action="document_access_denied",
        entity_type="document_access_grant",
        entity_id=grant.id if grant else None,
        after_state={
            "reason_code": reason_code,
            "document_id": str(grant.document_id) if grant else None,
            "lead_id": str(grant.lead_id) if grant else None,
            "purpose": grant.purpose if grant else None,
        },
        reason=reason_code,
        actor=actor,
        source="document_access_v9_5",
        commit=True,
    )


def expire_document_access_grants(
    session: Session,
    *,
    actor: str = "document-access-expiry-monitor",
) -> dict[str, Any]:
    now = now_utc()
    rows = session.exec(
        select(DocumentAccessGrant).where(DocumentAccessGrant.status == "active")
    ).all()
    expired: list[str] = []
    for grant in rows:
        if _as_utc(grant.expires_at) > now:
            continue
        grant.status = "expired"
        grant.updated_at = now
        session.add(grant)
        record_audit(
            session,
            action="document_access_grant_expired",
            entity_type="document_access_grant",
            entity_id=grant.id,
            after_state=_safe_grant_state(grant),
            reason="Document access grant reached its immutable expiry time.",
            actor=actor,
            source="document_access_v9_5",
        )
        expired.append(str(grant.id))
    if expired:
        session.commit()
    return {"expired": len(expired), "grant_ids": expired, "external_messages_sent": 0}


def access_document_with_token(
    session: Session,
    token: str,
    *,
    actor: str,
    actor_role: str,
) -> AccessedDocument:
    try:
        payload = _decode_token(token)
        grant_id = UUID(str(payload["grant_id"]))
    except (ValueError, TypeError):
        _deny(session, actor=actor, reason_code="invalid_token")
        raise ValueError("Document access token is invalid")

    grant = session.get(DocumentAccessGrant, grant_id)
    if grant is None:
        _deny(session, actor=actor, reason_code="grant_not_found")
        raise ValueError("Document access grant not found")

    now = now_utc()
    checks = {
        "token_hash_mismatch": not hmac.compare_digest(grant.token_hash, _hash_token(token)),
        "token_scope_mismatch": any([
            str(grant.document_id) != str(payload.get("document_id")),
            str(grant.lead_id) != str(payload.get("lead_id")),
            grant.issued_to != str(payload.get("issued_to")),
            grant.issued_role != str(payload.get("issued_role")),
            grant.purpose != str(payload.get("purpose")),
        ]),
        "actor_mismatch": grant.issued_to != actor,
        "role_mismatch": grant.issued_role != actor_role,
        "grant_revoked": grant.status == "revoked",
        "grant_consumed": grant.status == "consumed" or grant.use_count >= grant.max_uses,
        "grant_not_active": grant.status not in {"active", "expired", "revoked", "consumed"},
        "grant_expired": _as_utc(grant.expires_at) <= now or int(payload.get("exp", 0)) <= int(now.timestamp()),
    }
    reason = next((key for key, failed in checks.items() if failed), None)
    if reason:
        if reason == "grant_expired" and grant.status == "active":
            grant.status = "expired"
            grant.updated_at = now
            session.add(grant)
            record_audit(
                session,
                action="document_access_grant_expired",
                entity_type="document_access_grant",
                entity_id=grant.id,
                after_state=_safe_grant_state(grant),
                reason="Document access attempt occurred after expiry.",
                actor=actor,
                source="document_access_v9_5",
            )
            session.commit()
        _deny(session, actor=actor, reason_code=reason, grant=grant)
        raise ValueError(f"Document access denied: {reason}")

    document = session.get(DocumentRecord, grant.document_id)
    if document is None:
        _deny(session, actor=actor, reason_code="document_not_found", grant=grant)
        raise ValueError("Document access denied: document_not_found")
    if document.lead_id != grant.lead_id:
        _deny(session, actor=actor, reason_code="lead_scope_changed", grant=grant)
        raise ValueError("Document access denied: lead_scope_changed")
    if not document.storage_key or not document.file_hash or document.file_size_bytes is None:
        _deny(session, actor=actor, reason_code="document_integrity_metadata_missing", grant=grant)
        raise ValueError("Document access denied: document_integrity_metadata_missing")
    metadata_changed = any([
        document.file_hash != grant.document_file_hash,
        document.file_size_bytes != grant.document_file_size_bytes,
        document.storage_provider != grant.storage_provider,
        _hash_storage_key(document.storage_key) != grant.storage_key_hash,
    ])
    if metadata_changed:
        _deny(session, actor=actor, reason_code="document_metadata_changed", grant=grant)
        raise ValueError("Document access denied: document_metadata_changed")

    try:
        content = _verify_document_content(document)
    except (ValueError, FileNotFoundError, RuntimeError):
        _deny(session, actor=actor, reason_code="stored_object_missing_or_altered", grant=grant)
        raise ValueError("Document access denied: stored_object_missing_or_altered")

    grant.use_count += 1
    grant.last_accessed_by = actor
    grant.last_accessed_at = now
    grant.updated_at = now
    if grant.use_count >= grant.max_uses:
        grant.status = "consumed"
    session.add(grant)
    record_audit(
        session,
        action="document_accessed",
        entity_type="document_access_grant",
        entity_id=grant.id,
        after_state=_safe_grant_state(grant),
        reason=f"Document content accessed for {grant.purpose}.",
        actor=actor,
        source="document_access_v9_5",
    )
    session.commit()
    session.refresh(grant)
    return AccessedDocument(
        content=content,
        filename=document.filename,
        mime_type=document.mime_type or "application/octet-stream",
        grant=grant,
    )


def revoke_document_access_grant(
    session: Session,
    grant_id: UUID,
    *,
    actor: str,
    actor_role: str,
    reason: str,
) -> DocumentAccessGrant:
    grant = session.get(DocumentAccessGrant, grant_id)
    if grant is None:
        raise ValueError("Document access grant not found")
    if actor_role != "admin" and grant.created_by != actor:
        raise ValueError("Only the grant creator or an administrator can revoke this access grant")
    if grant.status in {"revoked", "expired", "consumed"}:
        raise ValueError(f"Document access grant is already {grant.status}")
    note = reason.strip()
    if len(note) < 3:
        raise ValueError("A revocation reason is required")
    now = now_utc()
    before = _safe_grant_state(grant)
    grant.status = "revoked"
    grant.revoked_by = actor
    grant.revoked_at = now
    grant.revocation_reason = note
    grant.updated_at = now
    session.add(grant)
    record_audit(
        session,
        action="document_access_grant_revoked",
        entity_type="document_access_grant",
        entity_id=grant.id,
        before_state=before,
        after_state=_safe_grant_state(grant),
        reason=note,
        actor=actor,
        source="document_access_v9_5",
    )
    session.commit()
    session.refresh(grant)
    return grant
