from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlsplit, urlunsplit

import httpx


class WebhookEgressPolicyError(ValueError):
    """Raised when a webhook destination violates outbound network policy."""


def _resolve_public_addresses(host: str, port: int) -> list[str]:
    try:
        answers = socket.getaddrinfo(
            host,
            port,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
        )
    except OSError as exc:
        raise WebhookEgressPolicyError(f"Webhook host could not be resolved: {host}") from exc

    addresses: list[str] = []
    for _family, _socktype, _proto, _canonname, sockaddr in answers:
        raw_address = str(sockaddr[0]).split("%", 1)[0]
        try:
            address = ipaddress.ip_address(raw_address)
        except ValueError as exc:
            raise WebhookEgressPolicyError("Webhook host resolved to an invalid IP address") from exc
        if not address.is_global:
            raise WebhookEgressPolicyError(
                f"Webhook host resolves to a non-public address: {address}"
            )
        normalized = str(address)
        if normalized not in addresses:
            addresses.append(normalized)

    if not addresses:
        raise WebhookEgressPolicyError("Webhook host did not resolve to a public address")
    return addresses


def _pin_public_webhook_target(url: str) -> tuple[str, str, str]:
    try:
        parsed = urlsplit(url)
        parsed_port = parsed.port
    except ValueError as exc:
        raise WebhookEgressPolicyError("Webhook URL is malformed") from exc

    if parsed.scheme.lower() != "https":
        raise WebhookEgressPolicyError("Webhook URL must use https")
    if parsed.username is not None or parsed.password is not None:
        raise WebhookEgressPolicyError("Webhook URL must not contain embedded credentials")
    if not parsed.hostname:
        raise WebhookEgressPolicyError("Webhook URL must include a hostname")

    port = 443 if parsed_port is None else parsed_port
    if not 1 <= port <= 65535:
        raise WebhookEgressPolicyError("Webhook URL port is invalid")

    hostname = parsed.hostname.rstrip(".")
    if not hostname or "%" in hostname:
        raise WebhookEgressPolicyError("Webhook URL hostname is invalid")

    try:
        literal = ipaddress.ip_address(hostname)
    except ValueError:
        try:
            dns_host = hostname.encode("idna").decode("ascii")
        except UnicodeError as exc:
            raise WebhookEgressPolicyError("Webhook URL hostname is invalid") from exc
    else:
        dns_host = str(literal)

    address = _resolve_public_addresses(dns_host, port)[0]
    pinned_host = f"[{address}]" if ":" in address else address
    pinned_netloc = pinned_host if port == 443 else f"{pinned_host}:{port}"
    pinned_url = urlunsplit(
        (
            "https",
            pinned_netloc,
            parsed.path or "/",
            parsed.query,
            "",
        )
    )

    host_header_name = f"[{dns_host}]" if ":" in dns_host else dns_host
    host_header = host_header_name if port == 443 else f"{host_header_name}:{port}"
    return pinned_url, host_header, dns_host


def request_public_webhook(
    method: str,
    url: str,
    *,
    content: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: int | float = 10,
) -> httpx.Response:
    """Send one direct HTTPS request pinned to a pre-validated public address.

    The hostname is resolved once, every returned address must be globally
    routable, and the actual TCP connection uses one of those validated IPs.
    TLS SNI and the HTTP Host header retain the original hostname so certificate
    verification still authenticates the requested webhook origin. Environment
    proxies and redirects are disabled to keep the validated destination bound
    to the connection that carries the request.
    """

    pinned_url, host_header, sni_hostname = _pin_public_webhook_target(url)
    request_headers = dict(headers or {})
    request_headers["Host"] = host_header
    with httpx.Client(
        timeout=timeout,
        follow_redirects=False,
        trust_env=False,
    ) as client:
        return client.request(
            method.upper(),
            pinned_url,
            content=content,
            headers=request_headers,
            extensions={"sni_hostname": sni_hostname},
            follow_redirects=False,
        )
