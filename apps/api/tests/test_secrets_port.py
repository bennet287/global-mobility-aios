from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import httpx
import pytest

from app.core.secrets_port import (
    OpenBaoSecretsPort,
    SecretMaterial,
    SecretReference,
    SecretsPortError,
)


ROOT = Path(__file__).resolve().parents[3]
PILOT_SPEC = importlib.util.spec_from_file_location(
    "pilot_openbao_secrets",
    ROOT / "scripts" / "pilot_openbao_secrets.py",
)
assert PILOT_SPEC is not None and PILOT_SPEC.loader is not None
pilot_openbao = importlib.util.module_from_spec(PILOT_SPEC)
PILOT_SPEC.loader.exec_module(pilot_openbao)


class _KvV2State:
    def __init__(self) -> None:
        self.versions: dict[int, dict[str, str]] = {}
        self.deleted: set[int] = set()

    def handle(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if "/data/" in path and request.method == "POST":
            body = json.loads(request.content)
            expected = body["options"].get("cas")
            current = max(self.versions, default=0)
            if expected is not None and expected != current:
                return httpx.Response(400, json={"errors": ["cas mismatch: confidential"]})
            version = current + 1
            self.versions[version] = body["data"]
            return httpx.Response(200, json={"data": {"version": version}})
        if "/data/" in path and request.method == "GET":
            version = int(request.url.params.get("version", max(self.versions, default=0)))
            if version in self.deleted or version not in self.versions:
                return httpx.Response(404, json={"errors": ["not found"]})
            return httpx.Response(
                200,
                json={"data": {"data": self.versions[version], "metadata": {"version": version}}},
            )
        if "/delete/" in path:
            self.deleted.update(json.loads(request.content)["versions"])
            return httpx.Response(204)
        if "/undelete/" in path:
            self.deleted.difference_update(json.loads(request.content)["versions"])
            return httpx.Response(204)
        if "/metadata/" in path and request.method == "DELETE":
            self.versions.clear()
            self.deleted.clear()
            return httpx.Response(204)
        return httpx.Response(404)


def _port(state: _KvV2State, *, environment: str = "pilot") -> OpenBaoSecretsPort:
    return OpenBaoSecretsPort(
        address="http://127.0.0.1:8200",
        token="super-secret-token",
        allowed_environment=environment,
        transport=httpx.MockTransport(state.handle),
    )


def test_openbao_kv2_lifecycle_preserves_scope_rotation_and_recovery() -> None:
    state = _KvV2State()
    port = _port(state)
    reference = SecretReference("pilot", "e1-sentinel")
    try:
        first = port.write(reference, SecretMaterial({"value": "first"}), expected_version=0)
        assert first == 1
        assert port.read(reference, version=first).material.reveal()["value"] == "first"

        second = port.write(reference, SecretMaterial({"value": "rotated"}), expected_version=first)
        assert second == 2
        port.soft_delete(reference, versions=(second,))
        with pytest.raises(SecretsPortError, match="status 404"):
            port.read(reference, version=second)
        port.undelete(reference, versions=(second,))
        assert port.read(reference, version=second).material.reveal()["value"] == "rotated"
        port.delete_metadata(reference)
        assert state.versions == {}
    finally:
        port.close()


def test_openbao_adapter_rejects_production_scope_and_remote_plain_http() -> None:
    state = _KvV2State()
    with pytest.raises(ValueError, match="non-production"):
        _port(state, environment="production")
    with pytest.raises(ValueError, match="requires HTTPS"):
        OpenBaoSecretsPort(address="http://bao.example.test", token="token")


def test_openbao_adapter_redacts_tokens_material_and_error_bodies() -> None:
    state = _KvV2State()
    port = _port(state)
    material = SecretMaterial({"password": "do-not-print"})
    try:
        assert "super-secret-token" not in repr(port)
        assert "do-not-print" not in repr(material)
        with pytest.raises(SecretsPortError) as raised:
            port.write(SecretReference("pilot", "missing-cas"), material, expected_version=7)
        assert "confidential" not in str(raised.value)
        with pytest.raises(SecretsPortError, match="outside"):
            port.read(SecretReference("test", "e1-sentinel"))
    finally:
        port.close()


@pytest.mark.parametrize(
    "environment,name",
    [("Production", "secret"), ("pilot", "../escape"), ("pilot", "UPPER")],
)
def test_secret_reference_rejects_unbounded_paths(environment: str, name: str) -> None:
    with pytest.raises(ValueError, match="bounded lowercase"):
        SecretReference(environment, name)


def test_pilot_does_not_clean_up_a_path_it_failed_to_create(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _CreateConflictPort:
        cleanup_called = False
        closed = False

        def write(self, *_args, **_kwargs):
            raise SecretsPortError("OpenBao request failed with status 400")

        def delete_metadata(self, *_args, **_kwargs):
            self.cleanup_called = True

        def close(self):
            self.closed = True

    port = _CreateConflictPort()
    monkeypatch.setattr(pilot_openbao, "_build_port", lambda: port)

    with pytest.raises(SecretsPortError, match="status 400"):
        pilot_openbao.execute_lifecycle(name="already-present")

    assert port.cleanup_called is False
    assert port.closed is True
