"""Synthetic target-host object-store probe; never a substitute for restore proof."""

from __future__ import annotations

import json
import secrets
from io import BytesIO
from typing import Any

from app.core.config import settings
from app.services.document_storage import (
    _minio_client,
    document_storage_posture,
    validate_minio_bucket_private,
)


def probe_object(client: Any, bucket: str, key: str, content: bytes, sse: Any) -> dict[str, Any]:
    """Write one unique synthetic object and prove read, SSE response and cleanup."""
    result: dict[str, Any] = {"write": False, "read": False, "sse_s3": False, "cleanup": False}
    stage = "write"
    try:
        client.put_object(bucket, key, BytesIO(content), length=len(content),
                          content_type="application/octet-stream", sse=sse)
        result["write"] = True
        stage = "read"
        response = client.get_object(bucket, key)
        try:
            result["read"] = response.read() == content
            headers = {str(k).lower(): str(v) for k, v in response.headers.items()}
            result["sse_s3"] = headers.get("x-amz-server-side-encryption") == "AES256"
            if not result["read"]:
                result["failure_stage"] = "content_mismatch"
            elif not result["sse_s3"]:
                result["failure_stage"] = "encryption_metadata"
        finally:
            response.close()
            response.release_conn()
    except Exception:
        result["failure_stage"] = stage
    finally:
        # A failed PUT can have an unknown outcome. Attempt cleanup even then.
        try:
            client.remove_object(bucket, key)
            try:
                client.stat_object(bucket, key)
            except Exception as exc:
                if getattr(exc, "code", None) in {"NoSuchKey", "NotFound", "NoSuchObject"}:
                    result["cleanup"] = True
                else:
                    result["failure_stage"] = "cleanup_verification"
            else:
                result["failure_stage"] = "cleanup_verification"
        except Exception:
            result["failure_stage"] = "cleanup"
    result["passed"] = all(result[name] for name in ("write", "read", "sse_s3", "cleanup"))
    return result


def run_preflight() -> dict[str, Any]:
    result: dict[str, Any] = {"passed": False, "probe": "not_run"}
    if not settings.is_production():
        result["failure_stage"] = "production_environment_required"
        return result
    if not settings.document_storage_production_strict:
        result["failure_stage"] = "strict_storage_posture_required"
        return result

    posture = document_storage_posture()
    # A storage probe can precede the independent backup and recovery drill.
    pending_recovery = {"backup_strategy_required", "recovery_test_record_required"}
    failures = set(posture["failures"])
    if failures - pending_recovery:
        result["failure_stage"] = "storage_configuration"
        result["configuration_failures"] = sorted(failures - pending_recovery)
        return result
    result["declared_recovery_fields_missing"] = bool(failures & pending_recovery)
    result["recovery_proven_by_this_probe"] = False

    bucket = settings.minio_bucket_documents
    try:
        client = _minio_client()
        if not client.bucket_exists(bucket):
            result["failure_stage"] = "bucket_missing"
            return result
        validate_minio_bucket_private(client)
    except Exception:
        result["failure_stage"] = "bucket_or_policy_check"
        return result

    from minio.sse import SseS3

    key = f"documents/production-preflight/{secrets.token_hex(16)}.bin"
    result["probe"] = "attempted"
    result["probe_key"] = key  # Synthetic key only; useful if cleanup fails.
    probe = probe_object(client, bucket, key, secrets.token_bytes(32), SseS3())
    result.update(probe)
    # This pass is only the live storage operation; recovery and external
    # unauthenticated-read proof remain separately required for production.
    return result


if __name__ == "__main__":
    outcome = run_preflight()
    print(json.dumps(outcome, sort_keys=True))
    raise SystemExit(0 if outcome["passed"] else 1)
