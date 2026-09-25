from __future__ import annotations

import socket
from typing import Any

import httpx
import pytest

from app.services.webhook_egress import (
    WebhookEgressPolicyError,
    _pin_public_webhook_target,
    request_public_webhook,
)


def _answer(address: str, port: int = 443) -> tuple[Any, ...]:
    family = socket.AF_INET6 if ":" in address else socket.AF_INET
    sockaddr = (address, port, 0, 0) if family == socket.AF_INET6 else (address, port)
    return (family, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", sockaddr)


def test_webhook_egress_requires_https() -> None:
    with pytest.raises(WebhookEgressPolicyError, match="must use https"):
        _pin_public_webhook_target("http://hooks.example.com/event")


def test_webhook_egress_rejects_embedded_credentials() -> None:
    with pytest.raises(WebhookEgressPolicyError, match="embedded credentials"):
        _pin_public_webhook_target("https://user:secret@hooks.example.com/event")


def test_webhook_egress_rejects_zero_port() -> None:
    with pytest.raises(WebhookEgressPolicyError, match="port is invalid"):
        _pin_public_webhook_target("https://hooks.example.com:0/event")


@pytest.mark.parametrize(
    "address",
    [
        "127.0.0.1",
        "10.20.30.40",
        "169.254.169.254",
        "::1",
        "fc00::1",
        "fe80::1",
    ],
)
def test_webhook_egress_rejects_non_public_resolution(
    monkeypatch: pytest.MonkeyPatch,
    address: str,
) -> None:
    monkeypatch.setattr(
        "app.services.webhook_egress.socket.getaddrinfo",
        lambda *args, **kwargs: [_answer(address)],
    )

    with pytest.raises(WebhookEgressPolicyError, match="non-public address"):
        _pin_public_webhook_target("https://hooks.example.com/event")


def test_webhook_egress_rejects_mixed_public_and_private_dns_answers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.services.webhook_egress.socket.getaddrinfo",
        lambda *args, **kwargs: [
            _answer("93.184.216.34"),
            _answer("127.0.0.1"),
        ],
    )

    with pytest.raises(WebhookEgressPolicyError, match="non-public address"):
        _pin_public_webhook_target("https://hooks.example.com/event")


def test_webhook_request_pins_validated_address_and_preserves_tls_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    resolution_calls: list[tuple[str, int]] = []
    captured: dict[str, Any] = {}

    def fake_getaddrinfo(host: str, port: int, **kwargs):
        resolution_calls.append((host, port))
        return [_answer("93.184.216.34", port)]

    class FakeClient:
        def __init__(self, **kwargs: Any) -> None:
            captured["client_kwargs"] = kwargs

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def request(
            self,
            method: str,
            url: str,
            *,
            content: bytes | None = None,
            headers: dict[str, str] | None = None,
            extensions: dict[str, Any] | None = None,
            follow_redirects: bool = False,
        ):
            request = httpx.Request(
                method,
                url,
                content=content,
                headers=headers,
                extensions=extensions,
            )
            captured["request"] = request
            captured["request_follow_redirects"] = follow_redirects
            return httpx.Response(204, request=request)

    monkeypatch.setattr(
        "app.services.webhook_egress.socket.getaddrinfo",
        fake_getaddrinfo,
    )
    monkeypatch.setattr("app.services.webhook_egress.httpx.Client", FakeClient)

    response = request_public_webhook(
        "POST",
        "https://hooks.example.com/events?id=42",
        content=b"{}",
        headers={"Content-Type": "application/json"},
        timeout=30,
    )

    assert response.status_code == 204
    assert resolution_calls == [("hooks.example.com", 443)]

    request = captured["request"]
    assert str(request.url) == "https://93.184.216.34/events?id=42"
    assert request.headers["Host"] == "hooks.example.com"
    assert request.headers["Content-Type"] == "application/json"
    assert request.extensions["sni_hostname"] == "hooks.example.com"
    assert captured["client_kwargs"] == {
        "timeout": 30,
        "follow_redirects": False,
        "trust_env": False,
    }
    assert captured["request_follow_redirects"] is False


def test_webhook_request_preserves_non_default_port_in_host_header(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.services.webhook_egress.socket.getaddrinfo",
        lambda host, port, **kwargs: [_answer("93.184.216.34", port)],
    )

    pinned_url, host_header, sni_hostname = _pin_public_webhook_target(
        "https://hooks.example.com:8443/events"
    )

    assert pinned_url == "https://93.184.216.34:8443/events"
    assert host_header == "hooks.example.com:8443"
    assert sni_hostname == "hooks.example.com"
