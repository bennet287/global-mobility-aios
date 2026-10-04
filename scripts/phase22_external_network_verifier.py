#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import base64
import hashlib
import http.client
import ipaddress
import json
import os
import re
import socket
import ssl
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


CONTRACT_KEY = "phase22.external-network-verifier"
CONTRACT_VERSION = 1
TRUSTED_REPOSITORY = "bennet287/global-mobility-aios"
TRUSTED_WORKFLOW_PATH = ".github/workflows/phase22-external-network-verifier.yml"
TRUSTED_VERIFIER_REF = "refs/heads/main"
PRIVATE_KEY_ENV = "PHASE22_EXTERNAL_VERIFIER_ED25519_PRIVATE_KEY_B64"
_HOST_LABEL = r"(?!-)[a-z0-9-]{1,63}(?<!-)"
_PUBLIC_HOSTNAME = re.compile(rf"^(?:{_HOST_LABEL}\.)+{_HOST_LABEL}$")
_HEX40 = re.compile(r"^[0-9a-f]{40}$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_RESERVED_HOST_SUFFIXES = (
    ".localhost",
    ".local",
    ".test",
    ".invalid",
    ".example",
    ".example.com",
    ".example.net",
    ".example.org",
)
_RESERVED_HOST_EXACT = frozenset({"localhost", "example.com", "example.net", "example.org"})
_ALLOWED_PORT_SETS = ({80, 443}, {22, 80, 443})
_USER_AGENT = "global-mobility-aios-phase22-external-network-verifier/1"
_MAX_REDIRECT_LOCATION_LENGTH = 2048


class VerifierInputError(ValueError):
    """The verifier invocation does not satisfy the bounded Phase 22 contract."""


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _required(value: str, *, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise VerifierInputError(f"{field} is required")
    return normalized


def _hex(value: str, *, field: str, length: int) -> str:
    normalized = _required(value, field=field)
    matcher = _HEX40 if length == 40 else _HEX64
    if matcher.fullmatch(normalized) is None:
        raise VerifierInputError(f"{field} must be {length} lowercase hexadecimal characters")
    return normalized


def normalize_public_hostname(value: str, *, field: str) -> str:
    normalized = _required(value, field=field).lower()
    if len(normalized) > 253 or _PUBLIC_HOSTNAME.fullmatch(normalized) is None:
        raise VerifierInputError(
            f"{field} must be a public DNS hostname without scheme, port or path"
        )
    if normalized in _RESERVED_HOST_EXACT or any(
        normalized.endswith(suffix) for suffix in _RESERVED_HOST_SUFFIXES
    ):
        raise VerifierInputError(f"{field} must not use a reserved/local hostname")
    try:
        ipaddress.ip_address(normalized)
    except ValueError:
        return normalized
    raise VerifierInputError(f"{field} must be a DNS hostname, not an IP literal")


def normalize_public_ipv4(value: str) -> str:
    normalized = _required(value, field="expected_public_ipv4")
    try:
        address = ipaddress.ip_address(normalized)
    except ValueError as exc:
        raise VerifierInputError("expected_public_ipv4 must be a valid IPv4 address") from exc
    if not isinstance(address, ipaddress.IPv4Address) or not address.is_global:
        raise VerifierInputError(
            "expected_public_ipv4 must be one globally routable IPv4 address"
        )
    return str(address)


def parse_allowed_ports(value: str) -> list[int]:
    raw = [item.strip() for item in _required(value, field="allowed_public_tcp_ports").split(",")]
    if any(not item or not item.isdigit() for item in raw):
        raise VerifierInputError("allowed_public_tcp_ports must be comma-separated integers")
    ports = sorted(int(item) for item in raw)
    if len(set(ports)) != len(ports):
        raise VerifierInputError("allowed_public_tcp_ports must be unique")
    if set(ports) not in _ALLOWED_PORT_SETS:
        raise VerifierInputError(
            "allowed_public_tcp_ports must be exactly 80,443 with optional SSH 22"
        )
    return ports


def strict_private_key(value: str) -> Ed25519PrivateKey:
    try:
        raw = base64.b64decode(value.encode("ascii"), validate=True)
    except (UnicodeEncodeError, ValueError) as exc:
        raise VerifierInputError("verifier private key is not strict base64") from exc
    if len(raw) != 32:
        raise VerifierInputError("verifier private key must decode to exactly 32 raw bytes")
    try:
        return Ed25519PrivateKey.from_private_bytes(raw)
    except ValueError as exc:
        raise VerifierInputError("verifier private key is not a valid Ed25519 key") from exc


def public_key_material(private_key: Ed25519PrivateKey) -> tuple[str, str]:
    raw = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return base64.b64encode(raw).decode("ascii"), hashlib.sha256(raw).hexdigest()


def _error_code(prefix: str, exc: BaseException) -> str:
    return f"{prefix}:{type(exc).__name__}"[:200]


def dns_observation(hostname: str) -> dict[str, Any]:
    ipv4: set[str] = set()
    ipv6: set[str] = set()
    try:
        answers = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
    except OSError as exc:
        return {
            "hostname": hostname,
            "ipv4_answers": [],
            "ipv6_answers": [],
            "error_code": _error_code("dns", exc),
        }
    for family, _socktype, _proto, _canonname, sockaddr in answers:
        try:
            address = ipaddress.ip_address(sockaddr[0])
        except (ValueError, IndexError, TypeError):
            continue
        if family == socket.AF_INET and isinstance(address, ipaddress.IPv4Address):
            ipv4.add(str(address))
        elif family == socket.AF_INET6 and isinstance(address, ipaddress.IPv6Address):
            ipv6.add(str(address))
    return {
        "hostname": hostname,
        "ipv4_answers": sorted(ipv4),
        "ipv6_answers": sorted(ipv6),
        "error_code": None,
    }


async def _port_open(loop: asyncio.AbstractEventLoop, target_ipv4: str, port: int, timeout: float) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setblocking(False)
    try:
        await asyncio.wait_for(loop.sock_connect(sock, (target_ipv4, port)), timeout=timeout)
        return True
    except (asyncio.TimeoutError, ConnectionError, OSError):
        return False
    finally:
        sock.close()


async def _scan_all_tcp_ports(
    target_ipv4: str,
    *,
    timeout_seconds: float,
    concurrency: int,
) -> dict[str, Any]:
    loop = asyncio.get_running_loop()
    open_ports: list[int] = []
    scan_complete = True
    error_code: str | None = None
    for first in range(1, 65536, concurrency):
        batch = list(range(first, min(first + concurrency, 65536)))
        try:
            results = await asyncio.gather(
                *(_port_open(loop, target_ipv4, port, timeout_seconds) for port in batch)
            )
        except Exception as exc:  # pragma: no cover - defensive fail-closed boundary
            scan_complete = False
            error_code = _error_code("tcp_scan", exc)
            break
        open_ports.extend(port for port, is_open in zip(batch, results, strict=True) if is_open)
    return {
        "target_ipv4": target_ipv4,
        "first_port": 1,
        "last_port": 65535,
        "scan_complete": scan_complete,
        "open_tcp_ports": sorted(open_ports),
        "error_code": error_code,
    }


def scan_all_tcp_ports(
    target_ipv4: str,
    *,
    timeout_seconds: float = 0.5,
    concurrency: int = 512,
) -> dict[str, Any]:
    if not 0.05 <= timeout_seconds <= 5.0:
        raise VerifierInputError("TCP scan timeout must be between 0.05 and 5 seconds")
    if not 32 <= concurrency <= 2048:
        raise VerifierInputError("TCP scan concurrency must be between 32 and 2048")
    return asyncio.run(
        _scan_all_tcp_ports(
            target_ipv4,
            timeout_seconds=timeout_seconds,
            concurrency=concurrency,
        )
    )


def http_redirect_observation(hostname: str, target_ipv4: str) -> dict[str, Any]:
    connection = http.client.HTTPConnection(target_ipv4, 80, timeout=8)
    try:
        connection.request(
            "GET",
            "/",
            headers={
                "Host": hostname,
                "User-Agent": _USER_AGENT,
                "Connection": "close",
            },
        )
        response = connection.getresponse()
        raw_location = response.getheader("Location")
        response.read(1024)
        if raw_location is not None and len(raw_location) > _MAX_REDIRECT_LOCATION_LENGTH:
            location = None
            error_code = "http:location_too_long"
        else:
            location = raw_location
            error_code = None
        return {
            "hostname": hostname,
            "target_ipv4": target_ipv4,
            "status_code": response.status,
            "location": location,
            "error_code": error_code,
        }
    except Exception as exc:
        return {
            "hostname": hostname,
            "target_ipv4": target_ipv4,
            "status_code": None,
            "location": None,
            "error_code": _error_code("http", exc),
        }
    finally:
        connection.close()


def _certificate_time(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return datetime.fromtimestamp(
            ssl.cert_time_to_seconds(value),
            tz=timezone.utc,
        ).isoformat()
    except (ValueError, OverflowError):
        return None


def tls_https_observation(hostname: str, target_ipv4: str, path: str) -> dict[str, Any]:
    context = ssl.create_default_context()
    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED
    context.set_alpn_protocols(["http/1.1"])
    raw_socket: socket.socket | None = None
    tls_socket: ssl.SSLSocket | None = None
    try:
        raw_socket = socket.create_connection((target_ipv4, 443), timeout=10)
        tls_socket = context.wrap_socket(raw_socket, server_hostname=hostname)
        raw_socket = None
        peer_der = tls_socket.getpeercert(binary_form=True)
        peer = tls_socket.getpeercert()
        request = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {hostname}\r\n"
            f"User-Agent: {_USER_AGENT}\r\n"
            "Connection: close\r\n\r\n"
        ).encode("ascii")
        tls_socket.sendall(request)
        response_file = tls_socket.makefile("rb")
        status_line = response_file.readline(4096).decode("iso-8859-1", errors="replace").strip()
        parts = status_line.split(" ", 2)
        status_code = int(parts[1]) if len(parts) >= 2 and parts[1].isdigit() else None
        return {
            "hostname": hostname,
            "target_ipv4": target_ipv4,
            "path": path,
            "https_status_code": status_code,
            "certificate_sha256": hashlib.sha256(peer_der).hexdigest() if peer_der else None,
            "certificate_not_before": _certificate_time(peer.get("notBefore")),
            "certificate_not_after": _certificate_time(peer.get("notAfter")),
            "hostname_valid": True,
            "chain_valid": True,
            "error_code": None,
        }
    except Exception as exc:
        return {
            "hostname": hostname,
            "target_ipv4": target_ipv4,
            "path": path,
            "https_status_code": None,
            "certificate_sha256": None,
            "certificate_not_before": None,
            "certificate_not_after": None,
            "hostname_valid": False,
            "chain_valid": False,
            "error_code": _error_code("tls_https", exc),
        }
    finally:
        if tls_socket is not None:
            tls_socket.close()
        if raw_socket is not None:
            raw_socket.close()


def build_manifest(
    *,
    deployment_run_id: str,
    networking_contract_fingerprint: str,
    web_hostname: str,
    api_hostname: str,
    expected_public_ipv4: str,
    allowed_public_tcp_ports: list[int],
    observed_started_at: str,
    observed_completed_at: str,
    repository: str,
    workflow_path: str,
    verifier_ref: str,
    verifier_commit_sha: str,
    github_actions_run_id: int,
    github_actions_run_attempt: int,
    dns_observations: list[dict[str, Any]],
    tcp_observation: dict[str, Any],
    http_redirect_observations: list[dict[str, Any]],
    tls_https_observations: list[dict[str, Any]],
) -> dict[str, Any]:
    UUID(deployment_run_id)
    return {
        "contract_key": CONTRACT_KEY,
        "contract_version": CONTRACT_VERSION,
        "deployment_run_id": deployment_run_id,
        "networking_contract_fingerprint": _hex(
            networking_contract_fingerprint,
            field="networking_contract_fingerprint",
            length=64,
        ),
        "web_hostname": web_hostname,
        "api_hostname": api_hostname,
        "expected_public_ipv4": expected_public_ipv4,
        "allowed_public_tcp_ports": allowed_public_tcp_ports,
        "observed_started_at": observed_started_at,
        "observed_completed_at": observed_completed_at,
        "provenance": {
            "repository": repository,
            "workflow_path": workflow_path,
            "verifier_ref": verifier_ref,
            "verifier_commit_sha": _hex(
                verifier_commit_sha,
                field="verifier_commit_sha",
                length=40,
            ),
            "github_actions_run_id": github_actions_run_id,
            "github_actions_run_attempt": github_actions_run_attempt,
        },
        "dns_observations": dns_observations,
        "tcp_observation": tcp_observation,
        "http_redirect_observations": http_redirect_observations,
        "tls_https_observations": tls_https_observations,
    }


def sign_manifest(
    manifest: dict[str, Any],
    *,
    private_key_b64: str,
    expected_public_key_fingerprint: str,
) -> tuple[dict[str, Any], str, str]:
    private_key = strict_private_key(private_key_b64)
    public_key_b64, fingerprint = public_key_material(private_key)
    expected = _hex(
        expected_public_key_fingerprint,
        field="expected_verifier_public_key_fingerprint",
        length=64,
    )
    if fingerprint != expected:
        raise VerifierInputError(
            "derived verifier public-key fingerprint does not match the prepared trust root"
        )
    manifest_bytes = canonical_json_bytes(manifest)
    signature = private_key.sign(manifest_bytes)
    envelope = {
        "manifest": manifest,
        "public_key_b64": public_key_b64,
        "signature_b64": base64.b64encode(signature).decode("ascii"),
    }
    return envelope, hashlib.sha256(manifest_bytes).hexdigest(), fingerprint


def _probe_error_codes(manifest: dict[str, Any]) -> list[str]:
    codes: list[str] = []
    for item in manifest["dns_observations"]:
        if item["error_code"]:
            codes.append(item["error_code"])
    if manifest["tcp_observation"]["error_code"]:
        codes.append(manifest["tcp_observation"]["error_code"])
    for key in ("http_redirect_observations", "tls_https_observations"):
        for item in manifest[key]:
            if item["error_code"]:
                codes.append(item["error_code"])
    return codes


def write_json(path: str, value: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the bounded off-host Phase 22 public-network verifier and sign its manifest."
    )
    parser.add_argument("--deployment-run-id", required=True)
    parser.add_argument("--networking-contract-fingerprint", required=True)
    parser.add_argument("--web-hostname", required=True)
    parser.add_argument("--api-hostname", required=True)
    parser.add_argument("--expected-public-ipv4", required=True)
    parser.add_argument("--allowed-public-tcp-ports", required=True)
    parser.add_argument("--expected-verifier-public-key-fingerprint", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--workflow-path", required=True)
    parser.add_argument("--verifier-ref", required=True)
    parser.add_argument("--verifier-commit-sha", required=True)
    parser.add_argument("--github-actions-run-id", required=True, type=int)
    parser.add_argument("--github-actions-run-attempt", required=True, type=int)
    parser.add_argument("--envelope-out", default="phase22-external-network-envelope.json")
    parser.add_argument("--summary-out", default="phase22-external-network-summary.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.repository != TRUSTED_REPOSITORY:
        raise VerifierInputError("verifier repository is not the trusted repository")
    if args.workflow_path != TRUSTED_WORKFLOW_PATH:
        raise VerifierInputError("verifier workflow path is not the trusted workflow")
    if args.verifier_ref != TRUSTED_VERIFIER_REF:
        raise VerifierInputError("operational verifier must execute from refs/heads/main")
    if args.github_actions_run_id <= 0 or args.github_actions_run_attempt <= 0:
        raise VerifierInputError("GitHub Actions run identity must be positive")

    web_hostname = normalize_public_hostname(args.web_hostname, field="web_hostname")
    api_hostname = normalize_public_hostname(args.api_hostname, field="api_hostname")
    if web_hostname == api_hostname:
        raise VerifierInputError("web_hostname and api_hostname must be distinct")
    expected_public_ipv4 = normalize_public_ipv4(args.expected_public_ipv4)
    allowed_ports = parse_allowed_ports(args.allowed_public_tcp_ports)

    private_key_b64 = os.environ.get(PRIVATE_KEY_ENV, "").strip()
    if not private_key_b64:
        raise VerifierInputError(
            f"{PRIVATE_KEY_ENV} is required from the protected GitHub Environment"
        )

    started = datetime.now(timezone.utc)
    dns = [dns_observation(web_hostname), dns_observation(api_hostname)]
    tcp = scan_all_tcp_ports(expected_public_ipv4)
    redirects = [
        http_redirect_observation(web_hostname, expected_public_ipv4),
        http_redirect_observation(api_hostname, expected_public_ipv4),
    ]
    tls = [
        tls_https_observation(web_hostname, expected_public_ipv4, "/"),
        tls_https_observation(api_hostname, expected_public_ipv4, "/health"),
    ]
    completed = datetime.now(timezone.utc)

    manifest = build_manifest(
        deployment_run_id=args.deployment_run_id,
        networking_contract_fingerprint=args.networking_contract_fingerprint,
        web_hostname=web_hostname,
        api_hostname=api_hostname,
        expected_public_ipv4=expected_public_ipv4,
        allowed_public_tcp_ports=allowed_ports,
        observed_started_at=started.isoformat(),
        observed_completed_at=completed.isoformat(),
        repository=args.repository,
        workflow_path=args.workflow_path,
        verifier_ref=args.verifier_ref,
        verifier_commit_sha=args.verifier_commit_sha,
        github_actions_run_id=args.github_actions_run_id,
        github_actions_run_attempt=args.github_actions_run_attempt,
        dns_observations=dns,
        tcp_observation=tcp,
        http_redirect_observations=redirects,
        tls_https_observations=tls,
    )
    envelope, manifest_sha256, public_key_fingerprint = sign_manifest(
        manifest,
        private_key_b64=private_key_b64,
        expected_public_key_fingerprint=args.expected_verifier_public_key_fingerprint,
    )
    write_json(args.envelope_out, envelope)
    write_json(
        args.summary_out,
        {
            "contract_key": CONTRACT_KEY,
            "contract_version": CONTRACT_VERSION,
            "deployment_run_id": args.deployment_run_id,
            "networking_contract_fingerprint": args.networking_contract_fingerprint,
            "manifest_sha256": manifest_sha256,
            "verifier_public_key_fingerprint": public_key_fingerprint,
            "verifier_ref": args.verifier_ref,
            "verifier_commit_sha": args.verifier_commit_sha,
            "github_actions_run_id": args.github_actions_run_id,
            "github_actions_run_attempt": args.github_actions_run_attempt,
            "open_tcp_ports": tcp["open_tcp_ports"],
            "tcp_scan_complete": tcp["scan_complete"],
            "probe_error_codes": _probe_error_codes(manifest),
            "signed_manifest_created": True,
            "phase22_receipt_written": False,
            "network_acceptance_conclusion": "not_assessed_import_and_target_host_reconciliation_required",
        },
    )
    print(f"signed external-network manifest written: {args.envelope_out}")
    print(f"manifest sha256: {manifest_sha256}")
    print(f"verifier public-key fingerprint: {public_key_fingerprint}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
