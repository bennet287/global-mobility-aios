"""AIOS-owned secret-reference contract and bounded OpenBao KV-v2 adapter.

Secret storage is infrastructure only. Resolving a secret does not grant authority,
and secret values must never enter Activity, Evidence, telemetry, logs, or errors.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Protocol
from urllib.parse import quote, urlsplit

import httpx


_SEGMENT = re.compile(r"^[a-z0-9](?:[a-z0-9._-]{0,62}[a-z0-9])?$")
_NONPRODUCTION_ENVIRONMENTS = frozenset({"development", "local", "pilot", "staging", "test"})


class SecretsPortError(RuntimeError):
    """Safe infrastructure failure whose text never contains secret material."""


@dataclass(frozen=True, slots=True)
class SecretReference:
    environment: str
    name: str

    def __post_init__(self) -> None:
        for label, value in (("environment", self.environment), ("name", self.name)):
            if not _SEGMENT.fullmatch(value):
                raise ValueError(f"secret {label} must be a bounded lowercase path segment")


class SecretMaterial:
    """Redacted wrapper requiring an explicit call to reveal process-local values."""

    __slots__ = ("_values",)

    def __init__(self, values: Mapping[str, str]) -> None:
        if not values or any(
            not isinstance(key, str) or not isinstance(value, str)
            for key, value in values.items()
        ):
            raise ValueError("secret material must contain string keys and values")
        self._values = MappingProxyType(dict(values))

    def reveal(self) -> Mapping[str, str]:
        return self._values

    def __repr__(self) -> str:
        return "SecretMaterial(<redacted>)"

    __str__ = __repr__


@dataclass(frozen=True, slots=True)
class SecretResolution:
    reference: SecretReference
    version: int
    material: SecretMaterial


class SecretsPort(Protocol):
    def read(self, reference: SecretReference, *, version: int | None = None) -> SecretResolution: ...

    def write(
        self,
        reference: SecretReference,
        material: SecretMaterial,
        *,
        expected_version: int | None = None,
    ) -> int: ...

    def soft_delete(self, reference: SecretReference, *, versions: tuple[int, ...]) -> None: ...

    def undelete(self, reference: SecretReference, *, versions: tuple[int, ...]) -> None: ...


class OpenBaoSecretsPort:
    """Minimal KV-v2 adapter restricted to an explicit non-production prefix."""

    def __init__(
        self,
        *,
        address: str,
        token: str,
        mount: str = "secret",
        path_prefix: str = "global-mobility-aios",
        allowed_environment: str = "pilot",
        namespace: str = "",
        timeout_seconds: float = 10,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        parsed = urlsplit(address.rstrip("/"))
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("OpenBao address must be an absolute HTTP(S) URL")
        if parsed.username or parsed.password:
            raise ValueError("OpenBao address must not contain credentials")
        if parsed.scheme != "https" and parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError("OpenBao requires HTTPS except on a loopback pilot endpoint")
        if not token:
            raise ValueError("OpenBao token is required")
        if not _SEGMENT.fullmatch(mount) or not _SEGMENT.fullmatch(path_prefix):
            raise ValueError("OpenBao mount and path prefix must be bounded path segments")
        if allowed_environment not in _NONPRODUCTION_ENVIRONMENTS:
            raise ValueError("OpenBao pilot is restricted to a non-production environment")
        if timeout_seconds <= 0:
            raise ValueError("OpenBao timeout must be positive")

        headers = {"X-Vault-Token": token}
        if namespace:
            headers["X-Vault-Namespace"] = namespace
        self._client = httpx.Client(
            base_url=address.rstrip("/"),
            headers=headers,
            timeout=timeout_seconds,
            transport=transport,
        )
        self._mount = mount
        self._prefix = path_prefix
        self._environment = allowed_environment

    def __repr__(self) -> str:
        return (
            f"OpenBaoSecretsPort(mount={self._mount!r}, prefix={self._prefix!r}, "
            f"environment={self._environment!r}, token=<redacted>)"
        )

    def close(self) -> None:
        self._client.close()

    def _path(self, operation: str, reference: SecretReference) -> str:
        if reference.environment != self._environment:
            raise SecretsPortError("secret reference is outside the configured pilot environment")
        name = quote(reference.name, safe="")
        return f"/v1/{self._mount}/{operation}/{self._prefix}/{reference.environment}/{name}"

    def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, object] | None = None,
    ) -> dict[str, object]:
        try:
            response = self._client.request(method, path, json=json_body)
        except httpx.HTTPError as exc:
            raise SecretsPortError("OpenBao request failed") from exc
        if response.status_code >= 400:
            raise SecretsPortError(f"OpenBao request failed with status {response.status_code}")
        if not response.content:
            return {}
        try:
            payload = response.json()
        except ValueError as exc:
            raise SecretsPortError("OpenBao returned an invalid JSON response") from exc
        if not isinstance(payload, dict):
            raise SecretsPortError("OpenBao returned an invalid response object")
        return payload

    def read(self, reference: SecretReference, *, version: int | None = None) -> SecretResolution:
        path = self._path("data", reference)
        if version is not None:
            if version <= 0:
                raise ValueError("secret version must be positive")
            path = f"{path}?version={version}"
        payload = self._request("GET", path)
        outer = payload.get("data")
        if not isinstance(outer, dict) or not isinstance(outer.get("data"), dict):
            raise SecretsPortError("OpenBao response omitted KV-v2 secret data")
        metadata = outer.get("metadata")
        resolved_version = metadata.get("version") if isinstance(metadata, dict) else None
        if not isinstance(resolved_version, int) or resolved_version <= 0:
            raise SecretsPortError("OpenBao response omitted the KV-v2 version")
        values = outer["data"]
        if not all(isinstance(key, str) and isinstance(value, str) for key, value in values.items()):
            raise SecretsPortError("OpenBao secret material is not string-valued")
        return SecretResolution(reference, resolved_version, SecretMaterial(values))

    def write(
        self,
        reference: SecretReference,
        material: SecretMaterial,
        *,
        expected_version: int | None = None,
    ) -> int:
        options: dict[str, int] = {}
        if expected_version is not None:
            if expected_version < 0:
                raise ValueError("expected secret version cannot be negative")
            options["cas"] = expected_version
        payload = self._request(
            "POST",
            self._path("data", reference),
            json_body={"data": dict(material.reveal()), "options": options},
        )
        data = payload.get("data")
        version = data.get("version") if isinstance(data, dict) else None
        if not isinstance(version, int) or version <= 0:
            raise SecretsPortError("OpenBao write response omitted the KV-v2 version")
        return version

    def _versions(
        self,
        operation: str,
        reference: SecretReference,
        versions: tuple[int, ...],
    ) -> None:
        if not versions or any(version <= 0 for version in versions):
            raise ValueError("at least one positive secret version is required")
        self._request(
            "POST",
            self._path(operation, reference),
            json_body={"versions": list(versions)},
        )

    def soft_delete(self, reference: SecretReference, *, versions: tuple[int, ...]) -> None:
        self._versions("delete", reference, versions)

    def undelete(self, reference: SecretReference, *, versions: tuple[int, ...]) -> None:
        self._versions("undelete", reference, versions)

    def delete_metadata(self, reference: SecretReference) -> None:
        self._request("DELETE", self._path("metadata", reference))
