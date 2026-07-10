from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Optional

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
        digest = sha256_hex(content)
        storage_key = build_storage_key(
            lead_id=lead_id,
            document_type=document_type,
            filename=filename,
            digest=digest,
        )
        target = self.root_dir / storage_key
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return StoredDocument(
            storage_provider=self.provider,
            storage_key=storage_key,
            file_hash=digest,
            file_size_bytes=len(content),
            mime_type=mime_type,
        )


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
        from minio import Minio

        digest = sha256_hex(content)
        storage_key = build_storage_key(
            lead_id=lead_id,
            document_type=document_type,
            filename=filename,
            digest=digest,
        )
        client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        bucket = settings.minio_bucket_documents
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
        client.put_object(
            bucket,
            storage_key,
            BytesIO(content),
            length=len(content),
            content_type=mime_type or "application/octet-stream",
        )
        return StoredDocument(
            storage_provider=self.provider,
            storage_key=storage_key,
            file_hash=digest,
            file_size_bytes=len(content),
            mime_type=mime_type,
        )


def document_storage_client():
    backend = settings.document_storage_backend.strip().lower()
    if backend == "minio":
        return MinioDocumentStorage()
    return LocalDocumentStorage()
