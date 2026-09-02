"""Bounded runtime secret-reference boundary for Technology Radar Wave E1.

A configured reference is authoritative and fails closed: the resolver never falls
back to a plaintext setting when a reference exists but cannot be resolved. The
OpenBao adapter is intentionally limited to non-production use until the roadmap
explicitly promotes a secrets backend beyond pilot status.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import quote

import httpx

from app.core.config import settings


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
        path = reference.locator.strip("/")
        if not path.startswith(self.allowed_prefix):
            raise SecretResolutionError(
                f"OpenBao secret path is outside the allowed pilot scope: {path}."
            )

        headers = {"X-Vault-Token": self.token}
        if self.namespace:
            headers["X-Vault-Namespace"] = self.namespace
        url = f"{self.address}/v1/{quote(self.mount, safe='')}/data/{quote(path, safe='/')}"
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.get(url, headers=headers)
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
    return build_secrets_port(parsed).resolve(parsed)
