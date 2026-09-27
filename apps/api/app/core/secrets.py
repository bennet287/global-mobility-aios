"""Bounded runtime secret-reference boundary for Technology Radar Wave E1.

A configured reference is authoritative and fails closed: the resolver never falls
back to a plaintext setting when a reference exists but cannot be resolved. File
references are restricted to the production AIOS runtime secret mount, while the
OpenBao adapter remains intentionally limited to non-production use until the
roadmap explicitly promotes a secrets backend beyond pilot status.
"""

from __future__ import annotations

import ipaddress
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from urllib.parse import quote, urlsplit

import httpx

from app.core.config import settings


_FILE_SECRET_ROOT = Path("/run/secrets/aios")
_MAX_FILE_SECRET_BYTES = 64 * 1024


class SecretResolutionError(RuntimeError):
    """A configured secret reference could not be resolved safely."""


@dataclass(frozen=True)
class SecretReference:
    backend: str
    locator: str
    field: str | None = None

    @classmethod
    def parse(cls, raw: str) -> "SecretReference":
        value = raw.strip()
        if "://" not in value:
            raise SecretResolutionError("Secret reference must use '<backend>://<locator>'.")
        backend, locator = value.split("://", 1)
        backend = backend.strip().lower()
        locator = locator.strip()
        if not backend or not locator:
            raise SecretResolutionError("Secret reference backend and locator are required.")

        field: str | None = None
        if backend == "openbao":
            locator, separator, field_value = locator.partition("#")
            locator = locator.strip().strip("/")
            field = field_value.strip() if separator else None
            if not locator or not field:
                raise SecretResolutionError(
                    "OpenBao references must use 'openbao://<path>#<field>'."
                )
        elif backend == "env":
            if "#" in locator or "/" in locator:
                raise SecretResolutionError("Environment references must use 'env://VARIABLE_NAME'.")
        elif backend == "file":
            if "#" in locator or not Path(locator).is_absolute():
                raise SecretResolutionError(
                    "File references must use an absolute 'file:///run/secrets/aios/<scope>/<name>' path."
                )
        else:
            raise SecretResolutionError(f"Unsupported secret backend: {backend}.")

        return cls(backend=backend, locator=locator, field=field)


class SecretsPort(Protocol):
    def resolve(self, reference: SecretReference) -> str:
        """Resolve one secret reference without persisting or logging its value."""


class EnvironmentSecretsPort:
    def resolve(self, reference: SecretReference) -> str:
        if reference.backend != "env":
            raise SecretResolutionError("EnvironmentSecretsPort only accepts env:// references.")
        value = os.environ.get(reference.locator)
        if value is None or value == "":
            raise SecretResolutionError(
                f"Environment secret reference is unavailable: {reference.locator}."
            )
        return value


class FileSecretsPort:
    """Read one bounded Docker-style file secret without exposing arbitrary files."""

    def __init__(self, *, root: str | Path | None = None) -> None:
        self.root = Path(root) if root is not None else _FILE_SECRET_ROOT

    def resolve(self, reference: SecretReference) -> str:
        if reference.backend != "file":
            raise SecretResolutionError("FileSecretsPort only accepts file:// references.")

        try:
            root = self.root.resolve(strict=False)
            resolved = Path(reference.locator).resolve(strict=True)
        except (OSError, RuntimeError, ValueError) as exc:
            raise SecretResolutionError("File secret reference is unavailable.") from exc

        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise SecretResolutionError(
                "File secret reference is outside the allowed /run/secrets/aios scope."
            ) from exc

        if not resolved.is_file():
            raise SecretResolutionError("File secret reference must resolve to a regular file.")

        try:
            with resolved.open("rb") as handle:
                raw_value = handle.read(_MAX_FILE_SECRET_BYTES + 1)
        except OSError as exc:
            raise SecretResolutionError("File secret reference could not be read.") from exc

        if len(raw_value) > _MAX_FILE_SECRET_BYTES:
            raise SecretResolutionError("File secret exceeds the 64 KiB safety limit.")
        try:
            value = raw_value.decode("utf-8").rstrip("\r\n")
        except UnicodeDecodeError as exc:
            raise SecretResolutionError("File secret must be UTF-8 text.") from exc
        if not value.strip():
            raise SecretResolutionError("File secret value must be a non-empty string.")
        return value


def _openbao_segments(value: str) -> tuple[str, ...]:
    segments = tuple(value.split("/"))
    if any(
        segment in {"", ".", ".."} or "%" in segment or "\\" in segment
        for segment in segments
    ):
        raise SecretResolutionError("OpenBao path contains unsafe segments.")
    return segments


def _validate_openbao_address(address: str) -> None:
    try:
        parsed = urlsplit(address)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError as exc:
        raise SecretResolutionError("OpenBao address is invalid.") from exc
    if (
        parsed.scheme not in {"http", "https"}
        or not hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
        or (port is not None and port == 0)
    ):
        raise SecretResolutionError("OpenBao address must be a plain HTTP(S) origin.")
    if parsed.scheme == "http":
        try:
            loopback = ipaddress.ip_address(hostname).is_loopback
        except ValueError:
            loopback = False
        if not loopback:
            raise SecretResolutionError("OpenBao HTTP requires a loopback IP address.")


class OpenBaoSecretsPort:
    """Minimal KV-v2 reader for the non-production OpenBao pilot."""

    def __init__(
        self,
        *,
        address: str,
        token: str,
        mount: str = "secret",
        namespace: str = "",
        allowed_prefix: str = "aios/nonprod/",
        app_env: str = "local",
        timeout_seconds: int = 5,
    ) -> None:
        self.address = address.rstrip("/")
        self.token = token
        self.mount = mount.strip("/")
        self.namespace = namespace.strip()
        self.allowed_prefix = allowed_prefix.strip().strip("/") + "/"
        self.app_env = app_env.strip().lower()
        self.timeout_seconds = timeout_seconds

    def resolve(self, reference: SecretReference) -> str:
        if reference.backend != "openbao":
            raise SecretResolutionError("OpenBaoSecretsPort only accepts openbao:// references.")
        if self.app_env in {"production", "prod"}:
            raise SecretResolutionError(
                "OpenBao secret resolution is a non-production Technology Radar pilot."
            )
        if not self.token:
            raise SecretResolutionError("OpenBao bootstrap token is not configured.")
        if not self.mount:
            raise SecretResolutionError("OpenBao KV mount is not configured.")
        _validate_openbao_address(self.address)
        _openbao_segments(self.mount)
        path = reference.locator.strip("/")
        path_segments = _openbao_segments(path)
        allowed_segments = _openbao_segments(self.allowed_prefix.rstrip("/"))
        if (
            path_segments[: len(allowed_segments)] != allowed_segments
            or len(path_segments) <= len(allowed_segments)
        ):
            raise SecretResolutionError(
                f"OpenBao secret path is outside the allowed pilot scope: {path}."
            )

        headers = {"X-Vault-Token": self.token}
        if self.namespace:
            headers["X-Vault-Namespace"] = self.namespace
        url = f"{self.address}/v1/{quote(self.mount, safe='')}/data/{quote(path, safe='/')}"
        try:
            with httpx.Client(
                timeout=self.timeout_seconds, trust_env=False, follow_redirects=False
            ) as client:
                response = client.get(url, headers=headers, follow_redirects=False)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise SecretResolutionError("OpenBao secret retrieval failed.") from exc

        try:
            value = response.json()["data"]["data"][reference.field]
        except (KeyError, TypeError, ValueError) as exc:
            raise SecretResolutionError("OpenBao response did not contain the requested secret field.") from exc
        if not isinstance(value, str) or value == "":
            raise SecretResolutionError("OpenBao secret value must be a non-empty string.")
        return value


def _setting_text(name: str) -> str:
    value = getattr(settings, name, "")
    return value if isinstance(value, str) else ""


def build_secrets_port(reference: SecretReference) -> SecretsPort:
    if reference.backend == "env":
        return EnvironmentSecretsPort()
    if reference.backend == "file":
        return FileSecretsPort()
    if reference.backend == "openbao":
        return OpenBaoSecretsPort(
            address=_setting_text("secrets_openbao_address") or "http://127.0.0.1:8200",
            token=_setting_text("secrets_openbao_token"),
            mount=_setting_text("secrets_openbao_mount") or "secret",
            namespace=_setting_text("secrets_openbao_namespace"),
            allowed_prefix=_setting_text("secrets_openbao_allowed_prefix") or "aios/nonprod/",
            app_env=_setting_text("app_env") or "local",
            timeout_seconds=getattr(settings, "secrets_openbao_timeout_seconds", 5),
        )
    raise SecretResolutionError(f"Unsupported secret backend: {reference.backend}.")


def resolve_runtime_secret(*, reference: str, fallback: str) -> str:
    """Resolve a reference when configured, otherwise preserve the current direct value."""
    if not reference.strip():
        return fallback
    parsed = SecretReference.parse(reference)
    if settings.is_production() and parsed.backend != "file":
        raise SecretResolutionError(
            "Production runtime secret references must use the bounded file:// backend."
        )
    return build_secrets_port(parsed).resolve(parsed)
