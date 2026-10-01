"""Verify restored document objects through the canonical storage adapter.

This verifier does not create backups, restore vendor storage, or mutate recovery
configuration. It verifies an operator-supplied manifest only after the restore
has been performed into the configured recovery target.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.services.document_storage import document_storage_client, validate_storage_key


SCHEMA = "aios-document-storage-recovery-manifest-v1"


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def load_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != SCHEMA:
        raise ValueError(f"Unsupported recovery manifest schema; expected {SCHEMA}")
    backend = str(payload.get("storage_provider") or "").strip().lower()
    configured = settings.document_storage_backend.strip().lower()
    if backend != configured:
        raise ValueError("Recovery manifest storage provider does not match configured backend")
    objects = payload.get("objects")
    if not isinstance(objects, list) or not objects:
        raise ValueError("Recovery manifest must contain at least one object")
    seen: set[str] = set()
    for item in objects:
        if not isinstance(item, dict):
            raise ValueError("Recovery manifest object entries must be mappings")
        key = validate_storage_key(str(item.get("storage_key") or ""))
        digest = str(item.get("sha256") or "").strip().lower()
        size = item.get("size_bytes")
        if key in seen:
            raise ValueError("Recovery manifest contains a duplicate storage key")
        seen.add(key)
        if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
            raise ValueError("Recovery manifest sha256 values must be lowercase hex digests")
        if type(size) is not int or size < 0:
            raise ValueError("Recovery manifest size_bytes must be a non-negative integer")
    return payload


def verify_recovered_objects(manifest: dict[str, Any]) -> dict[str, Any]:
    client = document_storage_client()
    checks: list[dict[str, Any]] = []
    for item in manifest["objects"]:
        key = validate_storage_key(str(item["storage_key"]))
        content = client.get_document(key)
        actual_hash = _sha256(content)
        actual_size = len(content)
        passed = actual_hash == item["sha256"] and actual_size == item["size_bytes"]
        checks.append({
            "storage_key": key,
            "expected_sha256": item["sha256"],
            "actual_sha256": actual_hash,
            "expected_size_bytes": item["size_bytes"],
            "actual_size_bytes": actual_size,
            "passed": passed,
        })
    return {
        "schema": "aios-document-storage-recovery-verification-v1",
        "storage_provider": manifest["storage_provider"],
        "manifest_id": str(manifest.get("manifest_id") or ""),
        "object_count": len(checks),
        "checks": checks,
        "passed": all(item["passed"] for item in checks),
        "backup_created_by_this_verifier": False,
        "restore_performed_by_this_verifier": False,
        "production_recovery_claimed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    manifest = load_manifest(args.manifest)
    result = verify_recovered_objects(manifest)
    output = json.dumps(result, sort_keys=True, indent=2)
    print(output)
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(output + "\n", encoding="utf-8")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
