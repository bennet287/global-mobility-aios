from __future__ import annotations

import hashlib

import pytest

from app.core.config import settings
from app.services import document_storage_recovery as recovery


class Store:
    def __init__(self, values: dict[str, bytes]) -> None:
        self.values = values

    def get_document(self, key: str) -> bytes:
        return self.values[key]


def entry(key: str, content: bytes) -> dict:
    return {
        "storage_key": key,
        "sha256": hashlib.sha256(content).hexdigest(),
        "size_bytes": len(content),
    }


def test_recovery_verifier_checks_hash_and_size_through_canonical_adapter(monkeypatch):
    content = b"recovered-document"
    manifest = {
        "schema": recovery.SCHEMA,
        "manifest_id": "drill-2026-10-01",
        "storage_provider": "minio",
        "objects": [entry("documents/recovery-proof/one.bin", content)],
    }
    monkeypatch.setattr(recovery, "document_storage_client", lambda: Store({
        "documents/recovery-proof/one.bin": content,
    }))
    result = recovery.verify_recovered_objects(manifest)
    assert result["passed"] is True
    assert result["object_count"] == 1
    assert result["backup_created_by_this_verifier"] is False
    assert result["restore_performed_by_this_verifier"] is False
    assert result["production_recovery_claimed"] is False


def test_recovery_verifier_fails_content_mismatch(monkeypatch):
    expected = b"expected"
    manifest = {
        "schema": recovery.SCHEMA,
        "storage_provider": "minio",
        "objects": [entry("documents/recovery-proof/two.bin", expected)],
    }
    monkeypatch.setattr(recovery, "document_storage_client", lambda: Store({
        "documents/recovery-proof/two.bin": b"wrong",
    }))
    assert recovery.verify_recovered_objects(manifest)["passed"] is False


def test_manifest_rejects_wrong_backend_duplicate_keys_and_invalid_hash(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "document_storage_backend", "oci")
    base = {
        "schema": recovery.SCHEMA,
        "storage_provider": "minio",
        "objects": [entry("documents/recovery-proof/one.bin", b"x")],
    }
    path = tmp_path / "manifest.json"
    import json
    path.write_text(json.dumps(base), encoding="utf-8")
    with pytest.raises(ValueError, match="does not match configured backend"):
        recovery.load_manifest(path)

    monkeypatch.setattr(settings, "document_storage_backend", "minio")
    base["objects"] = [entry("documents/recovery-proof/one.bin", b"x")] * 2
    path.write_text(json.dumps(base), encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        recovery.load_manifest(path)

    base["objects"] = [{
        "storage_key": "documents/recovery-proof/one.bin",
        "sha256": "not-a-digest",
        "size_bytes": 1,
    }]
    path.write_text(json.dumps(base), encoding="utf-8")
    with pytest.raises(ValueError, match="sha256"):
        recovery.load_manifest(path)
