from __future__ import annotations

import base64
import hashlib
import importlib.util
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from app.schemas_phase22_external_network_verifier import (
    Phase22ExternalNetworkManifestEnvelope,
)
from app.services.phase22_external_network_verifier import (
    external_network_manifest_bytes,
)


SCRIPT_PATH = Path(__file__).resolve().parents[3] / "scripts" / "phase22_external_network_verifier.py"
SPEC = importlib.util.spec_from_file_location("phase22_external_network_verifier_script", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
verifier = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verifier)


def _manifest() -> dict:
    return verifier.build_manifest(
        deployment_run_id="11111111-1111-4111-8111-111111111111",
        networking_contract_fingerprint="1" * 64,
        web_hostname="app.example-valid.org",
        api_hostname="api.example-valid.org",
        expected_public_ipv4="8.8.8.8",
        allowed_public_tcp_ports=[80, 443],
        observed_started_at="2026-10-04T00:00:00+00:00",
        observed_completed_at="2026-10-04T00:05:00+00:00",
        repository="bennet287/global-mobility-aios",
        workflow_path=".github/workflows/phase22-external-network-verifier.yml",
        verifier_ref="refs/heads/main",
        verifier_commit_sha="a" * 40,
        github_actions_run_id=123,
        github_actions_run_attempt=1,
        dns_observations=[
            {
                "hostname": "app.example-valid.org",
                "ipv4_answers": ["8.8.8.8"],
                "ipv6_answers": [],
                "error_code": None,
            },
            {
                "hostname": "api.example-valid.org",
                "ipv4_answers": ["8.8.8.8"],
                "ipv6_answers": [],
                "error_code": None,
            },
        ],
        tcp_observation={
            "target_ipv4": "8.8.8.8",
            "first_port": 1,
            "last_port": 65535,
            "scan_complete": True,
            "open_tcp_ports": [80, 443],
            "error_code": None,
        },
        http_redirect_observations=[
            {
                "hostname": "app.example-valid.org",
                "target_ipv4": "8.8.8.8",
                "status_code": 308,
                "location": "https://app.example-valid.org/",
                "error_code": None,
            },
            {
                "hostname": "api.example-valid.org",
                "target_ipv4": "8.8.8.8",
                "status_code": 308,
                "location": "https://api.example-valid.org/",
                "error_code": None,
            },
        ],
        tls_https_observations=[
            {
                "hostname": "app.example-valid.org",
                "target_ipv4": "8.8.8.8",
                "path": "/",
                "https_status_code": 200,
                "certificate_sha256": "2" * 64,
                "certificate_not_before": "2026-10-01T00:00:00+00:00",
                "certificate_not_after": "2026-11-01T00:00:00+00:00",
                "hostname_valid": True,
                "chain_valid": True,
                "error_code": None,
            },
            {
                "hostname": "api.example-valid.org",
                "target_ipv4": "8.8.8.8",
                "path": "/health",
                "https_status_code": 200,
                "certificate_sha256": "3" * 64,
                "certificate_not_before": "2026-10-01T00:00:00+00:00",
                "certificate_not_after": "2026-11-01T00:00:00+00:00",
                "hostname_valid": True,
                "chain_valid": True,
                "error_code": None,
            },
        ],
    )


def test_workflow_signing_bytes_match_api_validator_contract() -> None:
    private_raw = bytes(range(1, 33))
    private_b64 = base64.b64encode(private_raw).decode("ascii")
    private_key = verifier.strict_private_key(private_b64)
    public_b64, fingerprint = verifier.public_key_material(private_key)

    envelope, manifest_sha256, observed_fingerprint = verifier.sign_manifest(
        _manifest(),
        private_key_b64=private_b64,
        expected_public_key_fingerprint=fingerprint,
    )
    parsed = Phase22ExternalNetworkManifestEnvelope.model_validate(envelope)
    api_bytes = external_network_manifest_bytes(parsed.manifest)

    assert verifier.canonical_json_bytes(envelope["manifest"]) == api_bytes
    assert hashlib.sha256(api_bytes).hexdigest() == manifest_sha256
    assert observed_fingerprint == fingerprint
    assert parsed.public_key_b64 == public_b64
    Ed25519PublicKey.from_public_bytes(base64.b64decode(public_b64)).verify(
        base64.b64decode(parsed.signature_b64),
        api_bytes,
    )


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("80,443", [80, 443]),
        ("22,80,443", [22, 80, 443]),
        ("443,80", [80, 443]),
    ],
)
def test_allowed_public_ports_are_normalized_to_v1_contract(value: str, expected: list[int]) -> None:
    assert verifier.parse_allowed_ports(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        "22,443",
        "80",
        "80,443,443",
        "0,80,443",
        "80,443,8443",
        "abc,443",
    ],
)
def test_allowed_public_ports_fail_closed(value: str) -> None:
    with pytest.raises(verifier.VerifierInputError):
        verifier.parse_allowed_ports(value)


@pytest.mark.parametrize(
    "value",
    [
        "localhost",
        "app.local",
        "app.test",
        "https://app.example-valid.org",
        "8.8.8.8",
    ],
)
def test_public_hostname_validation_rejects_non_public_contract_shapes(value: str) -> None:
    with pytest.raises(verifier.VerifierInputError):
        verifier.normalize_public_hostname(value, field="hostname")


@pytest.mark.parametrize("value", ["127.0.0.1", "10.0.0.1", "192.168.1.1", "::1", "not-an-ip"])
def test_public_ipv4_validation_rejects_non_global_targets(value: str) -> None:
    with pytest.raises(verifier.VerifierInputError):
        verifier.normalize_public_ipv4(value)


def test_signing_rejects_key_not_pinned_by_prepared_contract() -> None:
    private_b64 = base64.b64encode(bytes(range(1, 33))).decode("ascii")
    with pytest.raises(verifier.VerifierInputError, match="prepared trust root"):
        verifier.sign_manifest(
            _manifest(),
            private_key_b64=private_b64,
            expected_public_key_fingerprint="f" * 64,
        )


def test_tcp_scan_contract_rejects_unsafe_runtime_bounds() -> None:
    with pytest.raises(verifier.VerifierInputError):
        verifier.scan_all_tcp_ports("8.8.8.8", timeout_seconds=0.01)
    with pytest.raises(verifier.VerifierInputError):
        verifier.scan_all_tcp_ports("8.8.8.8", concurrency=4096)


WORKFLOW_PATH = (
    Path(__file__).resolve().parents[3]
    / ".github"
    / "workflows"
    / "phase22-external-network-verifier.yml"
)


def test_workflow_separates_no_secret_ref_guard_from_signing_environment() -> None:
    text = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "workflow_dispatch:" in text
    assert "pull_request:" not in text
    assert "\npush:" not in text
    assert "protected-verifier-ref:" in text
    assert "needs: protected-verifier-ref" in text
    guard_start = text.index("  protected-verifier-ref:")
    signing_start = text.index("  verify-public-network:")
    guard_section = text[guard_start:signing_start]
    signing_section = text[signing_start:]

    assert "environment:" not in guard_section
    assert "secrets." not in guard_section
    assert 'refs/heads/main' in guard_section
    assert (
        "bennet287/global-mobility-aios/.github/workflows/"
        "phase22-external-network-verifier.yml@refs/heads/main"
    ) in guard_section

    assert "environment: phase22-external-network-verifier" in signing_section
    assert signing_section.count("secrets.") == 1
    assert "PHASE22_EXTERNAL_VERIFIER_ED25519_PRIVATE_KEY_B64" in signing_section
    assert "persist-credentials: false" in signing_section
    assert "ref: ${{ github.sha }}" in signing_section
    assert "--verifier-commit-sha \"$GITHUB_SHA\"" in signing_section
    assert "candidate_sha" not in text
    assert "pull_request.head" not in text


def test_http_redirect_overflow_is_signed_as_bounded_failure_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeResponse:
        status = 308

        @staticmethod
        def getheader(name: str):
            assert name == "Location"
            return "https://app.example-valid.org/" + ("x" * 3000)

        @staticmethod
        def read(_limit: int):
            return b""

    class FakeConnection:
        def __init__(self, *_args, **_kwargs):
            pass

        def request(self, *_args, **_kwargs):
            return None

        def getresponse(self):
            return FakeResponse()

        def close(self):
            return None

    monkeypatch.setattr(verifier.http.client, "HTTPConnection", FakeConnection)
    observed = verifier.http_redirect_observation(
        "app.example-valid.org",
        "8.8.8.8",
    )

    assert observed["status_code"] == 308
    assert observed["location"] is None
    assert observed["error_code"] == "http:location_too_long"
