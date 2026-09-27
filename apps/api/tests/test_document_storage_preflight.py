from __future__ import annotations

from app.core.config import settings
from app.services.document_storage_preflight import probe_object, run_preflight


class MissingObject(Exception):
    code = "NoSuchKey"


class Response:
    def __init__(self, content: bytes, *, encrypted: bool = True) -> None:
        self.content = content
        self.headers = {"x-amz-server-side-encryption": "AES256"} if encrypted else {}
        self.closed = False

    def read(self) -> bytes:
        return self.content

    def close(self) -> None:
        self.closed = True

    def release_conn(self) -> None:
        pass


class Store:
    def __init__(self, *, encrypted: bool = True, fail_put: bool = False) -> None:
        self.content = None
        self.encrypted = encrypted
        self.fail_put = fail_put
        self.removals = []
        self.response = None

    def put_object(self, bucket, key, data, *, length, content_type, sse):
        self.content = data.read()
        assert len(self.content) == length
        assert sse is not None
        if self.fail_put:
            raise RuntimeError("unknown outcome after write")

    def get_object(self, bucket, key):
        self.response = Response(self.content, encrypted=self.encrypted)
        return self.response

    def remove_object(self, bucket, key):
        self.removals.append(key)
        self.content = None

    def stat_object(self, bucket, key):
        if self.content is None:
            raise MissingObject()
        return object()


def test_storage_probe_proves_encrypted_round_trip_and_cleanup():
    store = Store()
    result = probe_object(store, "documents", "documents/production-preflight/one.bin", b"synthetic", object())
    assert result == {"write": True, "read": True, "sse_s3": True, "cleanup": True, "passed": True}
    assert store.response.closed is True
    assert len(store.removals) == 1


def test_storage_probe_rejects_missing_encryption_metadata():
    store = Store(encrypted=False)
    result = probe_object(store, "documents", "documents/production-preflight/two.bin", b"synthetic", object())
    assert result["passed"] is False
    assert result["failure_stage"] == "encryption_metadata"
    assert result["cleanup"] is True


def test_storage_probe_cleans_up_unknown_put_outcome():
    store = Store(fail_put=True)
    result = probe_object(store, "documents", "documents/production-preflight/three.bin", b"synthetic", object())
    assert result["passed"] is False
    assert result["failure_stage"] == "write"
    assert result["cleanup"] is True
    assert len(store.removals) == 1


def test_storage_preflight_requires_strict_production_posture(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "document_storage_production_strict", False)
    assert run_preflight() == {
        "passed": False,
        "probe": "not_run",
        "failure_stage": "strict_storage_posture_required",
    }
