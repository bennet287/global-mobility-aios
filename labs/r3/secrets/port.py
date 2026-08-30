from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


class SecretUnavailableError(RuntimeError):
    pass


class SecretAccessDeniedError(RuntimeError):
    pass


@dataclass(frozen=True)
class SecretRead:
    path: str
    value: str
    version: int


class OpenBaoSecretsPort:
    """R3-only OpenBao adapter. Never falls back to plaintext/config."""

    def __init__(
        self,
        *,
        base_url: str,
        token: str,
        timeout_seconds: float = 2.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout_seconds = timeout_seconds

    def _request(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, Any] | None = None,
    ) -> httpx.Response:
        try:
            response = httpx.request(
                method,
                f"{self.base_url}{path}",
                headers={"X-Vault-Token": self.token},
                json=payload,
                timeout=self.timeout_seconds,
            )
        except httpx.HTTPError as exc:
            raise SecretUnavailableError("OpenBao unavailable") from exc

        if response.status_code in {401, 403}:
            raise SecretAccessDeniedError("OpenBao denied secret access")
        if response.status_code >= 500:
            raise SecretUnavailableError(
                f"OpenBao unavailable: HTTP {response.status_code}"
            )
        response.raise_for_status()
        return response

    def read(self, logical_path: str, key: str) -> SecretRead:
        response = self._request("GET", f"/v1/secret/data/{logical_path}")
        body = response.json()["data"]
        return SecretRead(
            path=logical_path,
            value=str(body["data"][key]),
            version=int(body["metadata"]["version"]),
        )

    def write(self, logical_path: str, data: dict[str, str]) -> int:
        response = self._request(
            "POST",
            f"/v1/secret/data/{logical_path}",
            payload={"data": data},
        )
        return int(response.json()["data"]["version"])
