from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import Request
from sqlmodel import Session, select

from app.models.domain import CorporateAccount, PartnerApiCredential, now_utc
from app.services.audit_log import record_audit


API_SOURCE = "partner_api_v1"
ALLOWED_SCOPES = {"account:read", "cases:read", "compliance:read"}


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _hash_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def credential_scopes(credential: PartnerApiCredential) -> list[str]:
    return [scope for scope in credential.scopes.split(",") if scope]


def _safe_credential(credential: PartnerApiCredential) -> dict[str, object]:
    return {
        "id": str(credential.id),
        "corporate_account_id": str(credential.corporate_account_id),
        "key_prefix": credential.key_prefix,
        "label": credential.label,
        "scopes": credential_scopes(credential),
        "status": credential.status,
        "expires_at": credential.expires_at.isoformat(),
        "created_by": credential.created_by,
        "access_count": credential.access_count,
        "last_used_at": credential.last_used_at.isoformat() if credential.last_used_at else None,
        "revoked_by": credential.revoked_by,
        "revoked_at": credential.revoked_at.isoformat() if credential.revoked_at else None,
        "revocation_reason": credential.revocation_reason,
        "created_at": credential.created_at.isoformat(),
        "updated_at": credential.updated_at.isoformat(),
    }


def partner_credential_read(credential: PartnerApiCredential) -> dict[str, object]:
    payload = _safe_credential(credential)
    payload["expired"] = _as_utc(credential.expires_at) <= now_utc()
    return payload


def issue_partner_api_credential(
    session: Session,
    corporate_account_id: UUID,
    *,
    actor: str,
    label: str,
    scopes: list[str],
    expires_in_days: int = 90,
) -> tuple[PartnerApiCredential, str]:
    account = session.get(CorporateAccount, corporate_account_id)
    if account is None:
        raise ValueError("Corporate account not found")
    if account.account_status != "active":
        raise ValueError("Partner API credentials require an active corporate account")
    clean_label = label.strip()
    if len(clean_label) < 2 or len(clean_label) > 120:
        raise ValueError("Credential label must contain 2 to 120 characters")
    clean_scopes = sorted({scope.strip().lower() for scope in scopes})
    if not clean_scopes or not set(clean_scopes) <= ALLOWED_SCOPES:
        raise ValueError("Partner API credential contains an unsupported scope")
    if expires_in_days < 1 or expires_in_days > 365:
        raise ValueError("Partner API credential expiry must be between 1 and 365 days")

    issued_at = now_utc()
    api_key = f"gmai_partner_live_{secrets.token_urlsafe(36)}"
    credential = PartnerApiCredential(
        key_hash=_hash_key(api_key),
        key_prefix=api_key[:24],
        corporate_account_id=account.id,
        label=clean_label,
        scopes=",".join(clean_scopes),
        status="active",
        expires_at=issued_at + timedelta(days=expires_in_days),
        created_by=actor,
        created_at=issued_at,
        updated_at=issued_at,
    )
    session.add(credential)
    session.flush()
    record_audit(
        session,
        action="partner_api_credential_created",
        entity_type="partner_api_credential",
        entity_id=credential.id,
        after_state=_safe_credential(credential),
        reason="Account-scoped partner API credential issued.",
        actor=actor,
        source=API_SOURCE,
    )
    session.commit()
    session.refresh(credential)
    return credential, api_key


def expire_partner_api_credentials(
    session: Session,
    *,
    actor: str = "partner-api-expiry-monitor",
) -> int:
    now = now_utc()
    expired = 0
    for credential in session.exec(
        select(PartnerApiCredential).where(PartnerApiCredential.status == "active")
    ).all():
        if _as_utc(credential.expires_at) > now:
            continue
        credential.status = "expired"
        credential.updated_at = now
        session.add(credential)
        record_audit(
            session,
            action="partner_api_credential_expired",
            entity_type="partner_api_credential",
            entity_id=credential.id,
            after_state=_safe_credential(credential),
            reason="Partner API credential reached its expiry time.",
            actor=actor,
            source=API_SOURCE,
        )
        expired += 1
    if expired:
        session.commit()
    return expired


def resolve_partner_api_credential(
    session: Session,
    api_key: str,
    *,
    required_scope: str,
    request: Request,
) -> PartnerApiCredential:
    clean_key = api_key.strip()
    if (
        not clean_key.startswith("gmai_partner_live_")
        or len(clean_key) > 256
        or required_scope not in ALLOWED_SCOPES
    ):
        raise PermissionError("Partner API credential is invalid or unavailable")
    key_hash = _hash_key(clean_key)
    credential = session.exec(
        select(PartnerApiCredential).where(PartnerApiCredential.key_hash == key_hash)
    ).first()
    if credential is None or not hmac.compare_digest(credential.key_hash, key_hash):
        raise PermissionError("Partner API credential is invalid or unavailable")
    if credential.status != "active":
        raise PermissionError("Partner API credential is invalid or unavailable")
    if _as_utc(credential.expires_at) <= now_utc():
        credential.status = "expired"
        credential.updated_at = now_utc()
        session.add(credential)
        record_audit(
            session,
            action="partner_api_credential_expired",
            entity_type="partner_api_credential",
            entity_id=credential.id,
            after_state=_safe_credential(credential),
            reason="Expired partner API credential was presented.",
            actor="partner-api",
            source=API_SOURCE,
        )
        session.commit()
        raise PermissionError("Partner API credential is invalid or unavailable")
    if required_scope not in credential_scopes(credential):
        raise LookupError(f"Partner API credential lacks required scope: {required_scope}")
    account = session.get(CorporateAccount, credential.corporate_account_id)
    if account is None or account.account_status != "active":
        raise PermissionError("Partner API credential is invalid or unavailable")

    now = now_utc()
    credential.access_count += 1
    credential.last_used_at = now
    credential.updated_at = now
    session.add(credential)
    record_audit(
        session,
        action="partner_api_accessed",
        entity_type="partner_api_credential",
        entity_id=credential.id,
        after_state={
            "credential_id": str(credential.id),
            "corporate_account_id": str(credential.corporate_account_id),
            "scope": required_scope,
            "method": request.method,
            "path": request.url.path,
            "access_count": credential.access_count,
        },
        reason="Versioned account-scoped partner API accessed.",
        actor=f"partner-api:{credential.id}",
        source=API_SOURCE,
    )
    session.commit()
    session.refresh(credential)
    return credential


def revoke_partner_api_credential(
    session: Session,
    credential_id: UUID,
    *,
    actor: str,
    reason: str,
) -> PartnerApiCredential:
    credential = session.get(PartnerApiCredential, credential_id)
    if credential is None:
        raise ValueError("Partner API credential not found")
    if credential.status != "active":
        raise ValueError(f"Partner API credential is already {credential.status}")
    clean_reason = reason.strip()
    if len(clean_reason) < 3:
        raise ValueError("A revocation reason is required")
    before = _safe_credential(credential)
    now = now_utc()
    credential.status = "revoked"
    credential.revoked_by = actor
    credential.revoked_at = now
    credential.revocation_reason = clean_reason
    credential.updated_at = now
    session.add(credential)
    record_audit(
        session,
        action="partner_api_credential_revoked",
        entity_type="partner_api_credential",
        entity_id=credential.id,
        before_state=before,
        after_state=_safe_credential(credential),
        reason=clean_reason,
        actor=actor,
        source=API_SOURCE,
    )
    session.commit()
    session.refresh(credential)
    return credential
