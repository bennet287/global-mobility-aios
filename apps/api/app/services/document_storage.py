from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path, PurePosixPath
from typing import Any, Optional

from app.core.config import settings


@dataclass(frozen=True)
class StoredDocument:
    storage_provider: str
    storage_key: str
    file_hash: str
    file_size_bytes: int
    mime_type: Optional[str]


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def sha256_hex(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def safe_path_part(value: object) -> str:
    text = str(value or "unknown").strip().lower()
    text = re.sub(r"[^a-z0-9._-]+", "-", text)
    return text.strip("-") or "unknown"


def validate_storage_key(storage_key: str) -> str:
    key = str(storage_key or "").strip().replace("\\", "/")
    path = PurePosixPath(key)
    if not key or key.startswith("/") or ".." in path.parts:
        raise ValueError("Invalid document storage key")
    if not key.startswith("documents/"):
        raise ValueError("Document storage key is outside the controlled documents prefix")
    return key


def build_storage_key(*, lead_id: object, document_type: str, filename: str, digest: str) -> str:
    stem = safe_path_part(Path(filename).stem)
    suffix = safe_path_part(Path(filename).suffix.lstrip("."))
    extension = f".{suffix}" if suffix else ""
    return "/".join([
        "documents",
        safe_path_part(lead_id),
        safe_path_part(document_type),
        f"{stem}-{digest[:12]}{extension}",
    ])


def _is_production() -> bool:
    return settings.app_env.strip().lower() in {"production", "prod"}


def document_storage_posture() -> dict[str, Any]:
    backend = settings.document_storage_backend.strip().lower()
    secret = settings.document_access_token_secret.strip()
    default_credentials = (
        settings.minio_access_key.strip() in {"", "minioadmin"}
        or settings.minio_secret_key.strip() in {"", "minioadmin"}
    )
    controls = {
        "environment": settings.app_env,
        "backend": backend,
        "strict_mode": settings.document_storage_production_strict,
        "signed_access_secret_configured": bool(secret),
        "signed_access_ttl_seconds": settings.document_access_default_ttl_seconds,
        "signed_access_max_ttl_seconds": settings.document_access_max_ttl_seconds,
        "minio_tls_enabled": bool(settings.minio_secure),
        "minio_default_credentials": default_credentials,
        "bucket_auto_create": bool(settings.minio_auto_create_bucket),
        "server_side_encryption_enabled": bool(settings.minio_server_side_encryption),
        "retention_days": settings.document_storage_retention_days,
        "backup_strategy_configured": bool(settings.document_storage_backup_strategy.strip()),
        "recovery_test_recorded": bool(settings.document_storage_recovery_tested_at.strip()),
        "local_storage_allowed_in_production": bool(settings.document_storage_allow_local_in_production),
    }
    failures: list[str] = []
    if _is_production() and settings.document_storage_production_strict:
        if backend != "minio" and not settings.document_storage_allow_local_in_production:
            failures.append("production_strict_requires_minio")
        if backend == "minio" and not settings.minio_secure:
            failures.append("minio_tls_required")
        if backend == "minio" and default_credentials:
            failures.append("non_default_minio_credentials_required")
        if backend == "minio" and settings.minio_auto_create_bucket:
            failures.append("production_bucket_must_be_preprovisioned")
        if not secret:
            failures.append("separate_document_access_secret_required")
        if settings.document_access_max_ttl_seconds > 900:
            failures.append("document_access_max_ttl_must_not_exceed_900_seconds")
        if settings.document_storage_retention_days <= 0:
            failures.append("retention_policy_required")
        if not settings.document_storage_backup_strategy.strip():
            failures.append("backup_strategy_required")
        if not settings.document_storage_recovery_tested_at.strip():
            failures.append("recovery_test_record_required")
    controls["failures"] = failures
    controls["ready"] = not failures
    return controls


def validate_document_storage_configuration() -> dict[str, Any]:
    posture = document_storage_posture()
    if posture["failures"]:
        raise RuntimeError(
            "Document storage configuration failed closed: " + ", ".join(posture["failures"])
        )
    return posture


def _minio_client():
    from minio import Minio

    return Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )


def _policy_allows_public_read(policy: str, bucket: str) -> bool:
    try:
        parsed = json.loads(policy)
    except Exception:
        return True
    statements = parsed.get("Statement", [])
    if isinstance(statements, dict):
        statements = [statements]
    for statement in statements:
        if not isinstance(statement, dict) or str(statement.get("Effect")) != "Allow":
            continue
        principal = statement.get("Principal")
        public_principal = principal == "*" or (
            isinstance(principal, dict) and any(value == "*" for value in principal.values())
        )
        if not public_principal:
            continue
        actions = statement.get("Action", [])
        if isinstance(actions, str):
            actions = [actions]
        read_action = any(action in {"*", "s3:*", "s3:GetObject"} for action in actions)
        resources = statement.get("Resource", [])
        if isinstance(resources, str):
            resources = [resources]
        bucket_resource = any(bucket in str(resource) for resource in resources) or not resources
        if read_action and bucket_resource:
            return True
    return False


def validate_minio_bucket_private(client: Any) -> None:
    if not (_is_production() and settings.document_storage_production_strict):
        return
    try:
        policy = client.get_bucket_policy(settings.minio_bucket_documents)
    except Exception as exc:
        code = getattr(exc, "code", "")
        if code in {"NoSuchBucketPolicy", "NoSuchBucket"}:
            if code == "NoSuchBucket":
                raise RuntimeError("Configured document bucket does not exist") from exc
            return
        raise RuntimeError("Could not verify document bucket privacy") from exc
    if policy and _policy_allows_public_read(policy, settings.minio_bucket_documents):
        raise RuntimeError("Configured document bucket permits public object reads")


class LocalDocumentStorage:
    provider = "local"

    def __init__(self, root_dir: Optional[str] = None) -> None:
        self.root_dir = Path(root_dir or settings.document_local_storage_dir)

    def put_document(
        self,
        *,
        content: bytes,
        lead_id: object,
        document_type: str,
        filename: str,
        mime_type: Optional[str],
    ) -> StoredDocument:
        validate_document_storage_configuration()
        digest = sha256_hex(content)
        storage_key = validate_storage_key(build_storage_key(
            lead_id=lead_id,
            document_type=document_type,
            filename=filename,
            digest=digest,
        ))
        target = self.root_dir / storage_key
        root = self.root_dir.resolve()
        resolved_target = target.resolve()
        if root != resolved_target and root not in resolved_target.parents:
            raise ValueError("Document storage key escapes the configured storage root")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return StoredDocument(
            storage_provider=self.provider,
            storage_key=storage_key,
            file_hash=digest,
            file_size_bytes=len(content),
            mime_type=mime_type,
        )

    def get_document(self, storage_key: str) -> bytes:
        validate_document_storage_configuration()
        key = validate_storage_key(storage_key)
        root = self.root_dir.resolve()
        target = (root / key).resolve()
        if root != target and root not in target.parents:
            raise ValueError("Document storage key escapes the configured storage root")
        if not target.is_file():
            raise FileNotFoundError("Stored document file was not found")
        return target.read_bytes()


class MinioDocumentStorage:
    provider = "minio"

    def put_document(
        self,
        *,
        content: bytes,
        lead_id: object,
        document_type: str,
        filename: str,
        mime_type: Optional[str],
    ) -> StoredDocument:
        validate_document_storage_configuration()
        digest = sha256_hex(content)
        storage_key = validate_storage_key(build_storage_key(
            lead_id=lead_id,
            document_type=document_type,
            filename=filename,
            digest=digest,
        ))
        client = _minio_client()
        bucket = settings.minio_bucket_documents
        exists = client.bucket_exists(bucket)
        if not exists:
            if not settings.minio_auto_create_bucket:
                raise RuntimeError("Configured document bucket does not exist and auto-creation is disabled")
            client.make_bucket(bucket)
        validate_minio_bucket_private(client)
        kwargs: dict[str, Any] = {}
        if settings.minio_server_side_encryption:
            from minio.sse import SseS3

            kwargs["sse"] = SseS3()
        client.put_object(
            bucket,
            storage_key,
            BytesIO(content),
            length=len(content),
            content_type=mime_type or "application/octet-stream",
            **kwargs,
        )
        return StoredDocument(
            storage_provider=self.provider,
            storage_key=storage_key,
            file_hash=digest,
            file_size_bytes=len(content),
            mime_type=mime_type,
        )

    def get_document(self, storage_key: str) -> bytes:
        validate_document_storage_configuration()
        key = validate_storage_key(storage_key)
        client = _minio_client()
        if not client.bucket_exists(settings.minio_bucket_documents):
            raise FileNotFoundError("Configured document bucket was not found")
        validate_minio_bucket_private(client)
        response = client.get_object(settings.minio_bucket_documents, key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()


def public_document_metadata(document: Any) -> dict[str, Any]:
    return {
        "id": getattr(document, "id", None),
        "lead_id": getattr(document, "lead_id", None),
        "document_type": getattr(document, "document_type", None),
        "filename": getattr(document, "filename", None),
        "storage_provider": getattr(document, "storage_provider", None),
        "storage_reference_present": bool(getattr(document, "storage_key", None)),
        "file_hash": getattr(document, "file_hash", None),
        "mime_type": getattr(document, "mime_type", None),
        "file_size_bytes": getattr(document, "file_size_bytes", None),
        "status": getattr(document, "status", None),
        "uploaded_at": getattr(document, "uploaded_at", None),
        "verified_by": getattr(document, "verified_by", None),
        "verified_at": getattr(document, "verified_at", None),
        "expiry_date": getattr(document, "expiry_date", None),
        "created_at": getattr(document, "created_at", None),
        "updated_at": getattr(document, "updated_at", None),
        "signed_access_supported": bool(
            getattr(document, "storage_key", None)
            and getattr(document, "storage_provider", None) in {"local", "minio"}
            and getattr(document, "file_hash", None)
            and getattr(document, "file_size_bytes", None) is not None
        ),
        "storage_key_exposed": False,
    }


def document_storage_client(provider: Optional[str] = None):
    backend = (provider or settings.document_storage_backend).strip().lower()
    if backend == "minio":
        return MinioDocumentStorage()
    if backend == "local":
        return LocalDocumentStorage()
    raise ValueError("Unsupported document storage provider")
