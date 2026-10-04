from __future__ import annotations

import base64
import hashlib
import ipaddress
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from sqlmodel import Session

from app.schemas_phase22_external_network_verifier import (
    Phase22ExternalNetworkManifest,
    Phase22ExternalNetworkManifestEnvelope,
    Phase22VerifiedExternalNetworkObservation,
)
from app.services.organization_command import (
    InvalidReference,
    OrganizationCommandContext,
    canonical_json,
)
from app.services.production_deployment_acceptance import (
    validated_deployment_networking_contract,
)


EXTERNAL_NETWORK_VERIFIER_CONTRACT_KEY = "phase22.external-network-verifier"
EXTERNAL_NETWORK_VERIFIER_CONTRACT_VERSION = 1
EXTERNAL_NETWORK_VERIFIER_REPOSITORY = "bennet287/global-mobility-aios"
EXTERNAL_NETWORK_VERIFIER_WORKFLOW_PATH = ".github/workflows/phase22-external-network-verifier.yml"
MAX_SIGNED_MANIFEST_BYTES = 32_768
MAX_OBSERVATION_AGE = timedelta(hours=2)
MAX_OBSERVATION_DURATION = timedelta(minutes=30)
MAX_CLOCK_SKEW = timedelta(minutes=5)
_REDIRECT_STATUSES = frozenset({301, 302, 307, 308})


class ExternalNetworkVerifierEvidenceError(InvalidReference):
    """The signed external-network evidence is untrusted or outside its prepared contract."""


def _aware_utc(value: datetime, *, field: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ExternalNetworkVerifierEvidenceError(f"{field} must be timezone-aware")
    return value.astimezone(timezone.utc)


def external_network_manifest_bytes(manifest: Phase22ExternalNetworkManifest) -> bytes:
    payload = canonical_json(manifest.model_dump(mode="python")).encode("utf-8")
    if len(payload) > MAX_SIGNED_MANIFEST_BYTES:
        raise ExternalNetworkVerifierEvidenceError("external verifier manifest exceeds the bounded v1 size")
    return payload


def external_network_manifest_digest(manifest: Phase22ExternalNetworkManifest) -> str:
    return hashlib.sha256(external_network_manifest_bytes(manifest)).hexdigest()


def _strict_b64(value: str, *, field: str, expected_length: int) -> bytes:
    try:
        decoded = base64.b64decode(value.encode("ascii"), validate=True)
    except (UnicodeEncodeError, ValueError) as exc:
        raise ExternalNetworkVerifierEvidenceError(f"{field} is not strict base64") from exc
    if len(decoded) != expected_length:
        raise ExternalNetworkVerifierEvidenceError(
            f"{field} must decode to exactly {expected_length} bytes"
        )
    return decoded


def external_verifier_public_key_fingerprint(public_key_bytes: bytes) -> str:
    if len(public_key_bytes) != 32:
        raise ExternalNetworkVerifierEvidenceError("Ed25519 public key must be exactly 32 bytes")
    return hashlib.sha256(public_key_bytes).hexdigest()


def _require_exact_host_coverage(values, expected: tuple[str, str], *, field: str) -> dict[str, object]:
    mapping: dict[str, object] = {}
    for value in values:
        hostname = value.hostname.strip().lower()
        if hostname in mapping:
            raise ExternalNetworkVerifierEvidenceError(f"{field} contains a duplicate hostname")
        mapping[hostname] = value
    if set(mapping) != set(expected):
        raise ExternalNetworkVerifierEvidenceError(
            f"{field} must contain exactly the prepared web and API hostnames"
        )
    return mapping


def _normalized_ip_answers(values: list[str], *, version: int, blocker_prefix: str, blockers: list[str]) -> set[str]:
    result: set[str] = set()
    for value in values:
        try:
            address = ipaddress.ip_address(value)
        except ValueError:
            blockers.append(f"{blocker_prefix}:invalid_ip")
            continue
        if address.version != version:
            blockers.append(f"{blocker_prefix}:wrong_ip_version")
            continue
        normalized = str(address)
        if normalized in result:
            blockers.append(f"{blocker_prefix}:duplicate_answer")
        result.add(normalized)
    return result


def _https_redirect_matches(location: str | None, hostname: str) -> bool:
    if not location:
        return False
    parsed = urlsplit(location)
    try:
        port = parsed.port
    except ValueError:
        return False
    return (
        parsed.scheme.lower() == "https"
        and (parsed.hostname or "").lower() == hostname
        and parsed.username is None
        and parsed.password is None
        and port in {None, 443}
        and parsed.path in {"", "/"}
        and not parsed.query
        and not parsed.fragment
    )


def _network_blockers(
    manifest: Phase22ExternalNetworkManifest,
    *,
    networking_contract: dict,
) -> tuple[str, ...]:
    blockers: list[str] = []
    web = networking_contract["web_hostname"]
    api = networking_contract["api_hostname"]
    expected_ipv4 = networking_contract["expected_public_ipv4"]
    allowed_ports = tuple(networking_contract["allowed_public_tcp_ports"])
    expected_hosts = (web, api)

    dns = _require_exact_host_coverage(
        manifest.dns_observations,
        expected_hosts,
        field="dns_observations",
    )
    for hostname in expected_hosts:
        observation = dns[hostname]
        if observation.error_code:
            blockers.append(f"dns:{hostname}:error")
        ipv4 = _normalized_ip_answers(
            observation.ipv4_answers,
            version=4,
            blocker_prefix=f"dns:{hostname}",
            blockers=blockers,
        )
        ipv6 = _normalized_ip_answers(
            observation.ipv6_answers,
            version=6,
            blocker_prefix=f"dns:{hostname}",
            blockers=blockers,
        )
        if ipv4 != {expected_ipv4}:
            blockers.append(f"dns:{hostname}:unexpected_ipv4_answers")
        if ipv6:
            blockers.append(f"dns:{hostname}:unexpected_ipv6_answers")

    tcp = manifest.tcp_observation
    if tcp.target_ipv4 != expected_ipv4:
        raise ExternalNetworkVerifierEvidenceError(
            "TCP observation target does not match the prepared public IPv4"
        )
    if tcp.error_code:
        blockers.append("tcp:error")
    if not tcp.scan_complete:
        blockers.append("tcp:scan_incomplete")
    if tcp.first_port != 1 or tcp.last_port != 65535:
        blockers.append("tcp:not_full_1_65535_scan")
    if any(type(port) is not int or port < 1 or port > 65535 for port in tcp.open_tcp_ports):
        blockers.append("tcp:invalid_open_port")
    if len(set(tcp.open_tcp_ports)) != len(tcp.open_tcp_ports):
        blockers.append("tcp:duplicate_open_port")
    if tuple(sorted(set(tcp.open_tcp_ports))) != allowed_ports:
        blockers.append("tcp:open_port_set_mismatch")

    redirects = _require_exact_host_coverage(
        manifest.http_redirect_observations,
        expected_hosts,
        field="http_redirect_observations",
    )
    for hostname in expected_hosts:
        observation = redirects[hostname]
        if observation.target_ipv4 != expected_ipv4:
            raise ExternalNetworkVerifierEvidenceError(
                f"HTTP redirect observation target for {hostname} does not match prepared IPv4"
            )
        if observation.error_code:
            blockers.append(f"http:{hostname}:error")
        if observation.status_code not in _REDIRECT_STATUSES:
            blockers.append(f"http:{hostname}:not_redirect")
        if not _https_redirect_matches(observation.location, hostname):
            blockers.append(f"http:{hostname}:unexpected_location")

    tls = _require_exact_host_coverage(
        manifest.tls_https_observations,
        expected_hosts,
        field="tls_https_observations",
    )
    expected_paths = {web: "/", api: "/health"}
    observed_completed = _aware_utc(
        manifest.observed_completed_at,
        field="observed_completed_at",
    )
    for hostname in expected_hosts:
        observation = tls[hostname]
        if observation.target_ipv4 != expected_ipv4:
            raise ExternalNetworkVerifierEvidenceError(
                f"TLS/HTTPS observation target for {hostname} does not match prepared IPv4"
            )
        if observation.error_code:
            blockers.append(f"tls:{hostname}:error")
        if observation.path != expected_paths[hostname]:
            blockers.append(f"tls:{hostname}:unexpected_path")
        if not observation.chain_valid:
            blockers.append(f"tls:{hostname}:chain_invalid")
        if not observation.hostname_valid:
            blockers.append(f"tls:{hostname}:hostname_invalid")
        if observation.https_status_code != 200:
            blockers.append(f"https:{hostname}:unexpected_status")
        if observation.certificate_sha256 is None:
            blockers.append(f"tls:{hostname}:certificate_digest_absent")
        if (
            observation.certificate_not_before is None
            or observation.certificate_not_after is None
        ):
            blockers.append(f"tls:{hostname}:certificate_validity_absent")
        else:
            not_before = _aware_utc(
                observation.certificate_not_before,
                field=f"{hostname}.certificate_not_before",
            )
            not_after = _aware_utc(
                observation.certificate_not_after,
                field=f"{hostname}.certificate_not_after",
            )
            if not_after <= not_before:
                blockers.append(f"tls:{hostname}:certificate_validity_invalid")
            elif not (not_before <= observed_completed <= not_after):
                blockers.append(f"tls:{hostname}:certificate_not_valid_at_observation")

    return tuple(dict.fromkeys(blockers))


def verify_external_network_manifest(
    session: Session,
    context: OrganizationCommandContext,
    *,
    deployment_run_id,
    envelope: Phase22ExternalNetworkManifestEnvelope,
    verified_at: datetime | None = None,
) -> Phase22VerifiedExternalNetworkObservation:
    """Verify signed off-host network evidence without writing a Phase 22 receipt."""

    run, networking_contract = validated_deployment_networking_contract(
        session,
        context,
        deployment_run_id=deployment_run_id,
    )
    manifest = envelope.manifest

    if (
        manifest.contract_key != EXTERNAL_NETWORK_VERIFIER_CONTRACT_KEY
        or manifest.contract_version != EXTERNAL_NETWORK_VERIFIER_CONTRACT_VERSION
    ):
        raise ExternalNetworkVerifierEvidenceError("external verifier contract identity is unsupported")
    if manifest.deployment_run_id != run.id or manifest.deployment_run_id != deployment_run_id:
        raise ExternalNetworkVerifierEvidenceError("external verifier manifest targets a different deployment run")
    if manifest.networking_contract_fingerprint != run.networking_contract_fingerprint:
        raise ExternalNetworkVerifierEvidenceError(
            "external verifier manifest networking fingerprint does not match the prepared run"
        )
    if (
        manifest.web_hostname != networking_contract["web_hostname"]
        or manifest.api_hostname != networking_contract["api_hostname"]
        or manifest.expected_public_ipv4 != networking_contract["expected_public_ipv4"]
        or tuple(manifest.allowed_public_tcp_ports)
        != tuple(networking_contract["allowed_public_tcp_ports"])
    ):
        raise ExternalNetworkVerifierEvidenceError(
            "external verifier manifest networking identity does not match the prepared contract"
        )
    if len(set(manifest.allowed_public_tcp_ports)) != len(manifest.allowed_public_tcp_ports):
        raise ExternalNetworkVerifierEvidenceError("manifest public TCP allowlist contains duplicates")

    provenance = manifest.provenance
    if provenance.repository != EXTERNAL_NETWORK_VERIFIER_REPOSITORY:
        raise ExternalNetworkVerifierEvidenceError("external verifier repository is not trusted")
    if provenance.workflow_path != EXTERNAL_NETWORK_VERIFIER_WORKFLOW_PATH:
        raise ExternalNetworkVerifierEvidenceError("external verifier workflow path is not trusted")
    if not provenance.verifier_ref.startswith("refs/heads/"):
        raise ExternalNetworkVerifierEvidenceError(
            "external verifier must report a branch ref rather than a pull-request or detached ref"
        )

    public_key = _strict_b64(
        envelope.public_key_b64,
        field="public_key_b64",
        expected_length=32,
    )
    signature = _strict_b64(
        envelope.signature_b64,
        field="signature_b64",
        expected_length=64,
    )
    key_fingerprint = external_verifier_public_key_fingerprint(public_key)
    if key_fingerprint != networking_contract["external_verifier_public_key_fingerprint"]:
        raise ExternalNetworkVerifierEvidenceError(
            "external verifier public key does not match the prepared networking trust root"
        )

    signed_bytes = external_network_manifest_bytes(manifest)
    try:
        Ed25519PublicKey.from_public_bytes(public_key).verify(signature, signed_bytes)
    except (InvalidSignature, ValueError) as exc:
        raise ExternalNetworkVerifierEvidenceError(
            "external verifier manifest signature is invalid"
        ) from exc

    started = _aware_utc(manifest.observed_started_at, field="observed_started_at")
    completed = _aware_utc(manifest.observed_completed_at, field="observed_completed_at")
    if completed < started:
        raise ExternalNetworkVerifierEvidenceError("external verifier observation completion precedes start")
    if completed - started > MAX_OBSERVATION_DURATION:
        raise ExternalNetworkVerifierEvidenceError("external verifier observation duration exceeds v1 bound")

    prepared_at = run.created_at
    if prepared_at.tzinfo is None or prepared_at.utcoffset() is None:
        prepared_at = prepared_at.replace(tzinfo=timezone.utc)
    else:
        prepared_at = prepared_at.astimezone(timezone.utc)
    if started < prepared_at:
        raise ExternalNetworkVerifierEvidenceError(
            "external verifier observation started before the deployment run was prepared"
        )

    now = _aware_utc(verified_at or datetime.now(timezone.utc), field="verified_at")
    if completed > now + MAX_CLOCK_SKEW:
        raise ExternalNetworkVerifierEvidenceError("external verifier observation is future-dated")
    if now - completed > MAX_OBSERVATION_AGE:
        raise ExternalNetworkVerifierEvidenceError("external verifier observation is stale")

    blockers = _network_blockers(manifest, networking_contract=networking_contract)
    return Phase22VerifiedExternalNetworkObservation(
        deployment_run_id=run.id,
        networking_contract_fingerprint=run.networking_contract_fingerprint or "",
        manifest_sha256=hashlib.sha256(signed_bytes).hexdigest(),
        verifier_public_key_fingerprint=key_fingerprint,
        verifier_repository=provenance.repository,
        verifier_workflow_path=provenance.workflow_path,
        verifier_ref=provenance.verifier_ref,
        verifier_commit_sha=provenance.verifier_commit_sha,
        github_actions_run_id=provenance.github_actions_run_id,
        github_actions_run_attempt=provenance.github_actions_run_attempt,
        observed_started_at=started,
        observed_completed_at=completed,
        network_contract_satisfied=not blockers,
        blockers=blockers,
    )
