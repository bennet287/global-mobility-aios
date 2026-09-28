from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.core.config import settings
from app.services import document_storage as storage
from app.services.document_storage_preflight import probe_oci_object


class NotFound(Exception):
    status = 404


class FakeOci:
    def __init__(self, *, access="NoPublicAccess", tier="Standard"):
        self.access = access
        self.tier = tier
        self.objects = {}

    def get_bucket(self, namespace, bucket):
        return SimpleNamespace(data=SimpleNamespace(
            public_access_type=self.access, storage_tier=self.tier,
        ))

    def put_object(self, namespace, bucket, key, body, **kwargs):
        assert kwargs["content_length"] >= 0
        self.objects[key] = body.read()

    def get_object(self, namespace, bucket, key):
        return SimpleNamespace(data=SimpleNamespace(content=self.objects[key]))

    def delete_object(self, namespace, bucket, key):
        self.objects.pop(key, None)

    def head_object(self, namespace, bucket, key):
        if key not in self.objects:
            raise NotFound()


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "document_storage_backend", "oci")
    monkeypatch.setattr(settings, "oci_region", "eu-frankfurt-1")
    monkeypatch.setattr(settings, "oci_namespace", "pilotnamespace")
    monkeypatch.setattr(settings, "oci_bucket_documents", "private-documents")
    monkeypatch.setattr(settings, "document_storage_production_strict", False)


def test_oci_document_round_trip_and_access(configured, monkeypatch):
    client = FakeOci()
    monkeypatch.setattr(storage, "_oci_client", lambda: client)
    saved = storage.document_storage_client().put_document(
        content=b"synthetic", lead_id="lead", document_type="identity",
        filename="passport.pdf", mime_type="application/pdf",
    )
    assert saved.storage_provider == "oci"
    assert storage.document_storage_client("oci").get_document(saved.storage_key) == b"synthetic"
    assert storage.public_document_metadata(SimpleNamespace(
        storage_provider="oci", storage_key=saved.storage_key,
        file_hash=saved.file_hash, file_size_bytes=saved.file_size_bytes,
    ))["signed_access_supported"] is True
    client.access = "ObjectReadWithoutList"
    with pytest.raises(RuntimeError, match="public access"):
        storage.document_storage_client().get_document(saved.storage_key)


def test_oci_posture_requires_region_namespace_and_bucket(configured, monkeypatch):
    for name, failure in (
        ("oci_region", "oci_region_required"),
        ("oci_namespace", "oci_namespace_required"),
        ("oci_bucket_documents", "oci_bucket_required"),
    ):
        original = getattr(settings, name)
        monkeypatch.setattr(settings, name, "")
        assert failure in storage.document_storage_posture()["failures"]
        monkeypatch.setattr(settings, name, original)


def test_oci_probe_current_object_cleanup(configured):
    client = FakeOci()
    result = probe_oci_object(client, "pilotnamespace", "private-documents", "documents/probe", b"test")
    assert result["passed"] is True
    assert result["object_encryption_independently_verified"] is False
    assert client.objects == {}
