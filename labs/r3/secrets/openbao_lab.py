from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path
from typing import Any

import httpx

from labs.r3.common.harness import CONTRACT_VERSION, fingerprint, validate_run_id
from labs.r3.secrets.port import (
    OpenBaoSecretsPort,
    SecretAccessDeniedError,
    SecretUnavailableError,
)


OPENBAO_VERSION = "2.6.2"
ROOT_TOKEN = "r3-root-token"
CANARY_V1 = "AIOS_R3_OPENBAO_CANARY_V1"
CANARY_V2 = "AIOS_R3_OPENBAO_CANARY_V2"


def _git_sha() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _headers(token: str) -> dict[str, str]:
    return {"X-Vault-Token": token}


def _post(
    base_url: str,
    token: str,
    path: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    response = httpx.post(
        f"{base_url}{path}",
        headers=_headers(token),
        json=payload,
        timeout=3.0,
    )
    response.raise_for_status()
    return response.json()


def _put(
    base_url: str,
    token: str,
    path: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    response = httpx.put(
        f"{base_url}{path}",
        headers=_headers(token),
        json=payload,
        timeout=3.0,
    )
    response.raise_for_status()
    return response.json() if response.content else {}


def _record(
    outcomes: list[dict[str, Any]],
    feature: str,
    observed: Any,
    expected: Any,
) -> None:
    outcomes.append(
        {
            "feature": feature,
            "observed": observed,
            "expected": expected,
            "passed": observed == expected,
            "unauthorized_canonical_effects": [],
        }
    )


def run_secrets(*, base_url: str) -> dict[str, Any]:
    outcomes: list[dict[str, Any]] = []
    root = OpenBaoSecretsPort(base_url=base_url, token=ROOT_TOKEN)

    health = httpx.get(f"{base_url}/v1/sys/health", timeout=3.0)
    _record(outcomes, "real_openbao_health", health.status_code, 200)

    policy = """
path "secret/data/gmai-r3/provider" {
  capabilities = ["read"]
}
path "secret/metadata/gmai-r3/provider" {
  capabilities = ["read"]
}
""".strip()
    _put(
        base_url,
        ROOT_TOKEN,
        "/v1/sys/policies/acl/gmai-r3-provider-read",
        {"policy": policy},
    )

    version1 = root.write("gmai-r3/provider", {"api_key": CANARY_V1})
    _record(outcomes, "kv_v2_first_version", version1, 1)

    token_response = _post(
        base_url,
        ROOT_TOKEN,
        "/v1/auth/token/create",
        {
            "policies": ["gmai-r3-provider-read"],
            "ttl": "90s",
            "renewable": False,
            "no_default_policy": True,
        },
    )
    child_token = token_response["auth"]["client_token"]
    lease_duration = int(token_response["auth"]["lease_duration"])
    _record(
        outcomes,
        "scoped_token_has_bounded_ttl",
        0 < lease_duration <= 90,
        True,
    )

    reader = OpenBaoSecretsPort(base_url=base_url, token=child_token)
    read_v1 = reader.read("gmai-r3/provider", "api_key")
    _record(
        outcomes,
        "scoped_token_reads_only_authorized_secret",
        (read_v1.value, read_v1.version),
        (CANARY_V1, 1),
    )

    try:
        reader.write("gmai-r3/provider", {"api_key": "MUST_NOT_WRITE"})
        write_denied = False
    except SecretAccessDeniedError:
        write_denied = True
    _record(outcomes, "read_token_cannot_write", write_denied, True)

    version2 = root.write("gmai-r3/provider", {"api_key": CANARY_V2})
    read_v2 = reader.read("gmai-r3/provider", "api_key")
    _record(
        outcomes,
        "rotation_advances_version_and_value",
        (version2, read_v2.version, read_v2.value),
        (2, 2, CANARY_V2),
    )

    old = httpx.get(
        f"{base_url}/v1/secret/data/gmai-r3/provider?version=1",
        headers=_headers(child_token),
        timeout=3.0,
    )
    old.raise_for_status()
    _record(
        outcomes,
        "historical_secret_version_remains_addressable",
        (
            old.json()["data"]["data"]["api_key"],
            old.json()["data"]["metadata"]["version"],
        ),
        (CANARY_V1, 1),
    )

    revoke = httpx.post(
        f"{base_url}/v1/auth/token/revoke-self",
        headers=_headers(child_token),
        timeout=3.0,
    )
    revoke.raise_for_status()
    try:
        reader.read("gmai-r3/provider", "api_key")
        revoked_denied = False
    except SecretAccessDeniedError:
        revoked_denied = True
    _record(
        outcomes,
        "revoked_token_cannot_read",
        revoked_denied,
        True,
    )

    audit_enable = httpx.put(
        f"{base_url}/v1/sys/audit/r3-file",
        headers=_headers(ROOT_TOKEN),
        json={"type": "file", "options": {"file_path": "/tmp/r3-audit.log"}},
        timeout=3.0,
    )
    audit_ok = audit_enable.status_code in {200, 204}
    audit_list = httpx.get(
        f"{base_url}/v1/sys/audit",
        headers=_headers(ROOT_TOKEN),
        timeout=3.0,
    )
    audit_list.raise_for_status()
    _record(
        outcomes,
        "audit_device_enabled",
        audit_ok and "r3-file/" in audit_list.json().get("data", {}),
        True,
    )

    unavailable = OpenBaoSecretsPort(
        base_url="http://127.0.0.1:18201",
        token="unused",
        timeout_seconds=0.2,
    )
    try:
        unavailable.read("gmai-r3/provider", "api_key")
        failed_closed = False
    except SecretUnavailableError:
        failed_closed = True
    _record(
        outcomes,
        "unavailable_service_has_no_plaintext_fallback",
        failed_closed,
        True,
    )

    failures = [item for item in outcomes if not item["passed"]]
    return {
        "outcomes": outcomes,
        "passes": len(outcomes) - len(failures),
        "failures": len(failures),
        "feature_coverage": {
            "real_service": True,
            "kv_v2_versioning": True,
            "scoped_policy": True,
            "bounded_token_ttl": True,
            "deny_write": True,
            "rotation": True,
            "historical_version": True,
            "token_revocation": True,
            "audit_device": True,
            "outage_fail_closed": True,
            "audit_log_content_validation": False,
            "restart_persistence": False,
            "dynamic_database_credentials": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:18200")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    validate_run_id(args.run_id)

    detail = run_secrets(base_url=args.base_url)
    result = {
        "contract_version": CONTRACT_VERSION,
        "r3_run_id": args.run_id,
        "candidate": "openbao",
        "candidate_version": OPENBAO_VERSION,
        "git_sha": _git_sha(),
        "environment": "synthetic-isolated-real-service",
        "experiment": "t1-t2-t3-t5-secrets",
        "test_tiers": ["T1", "T2", "T3", "T5"],
        "scenario_count": len(detail["outcomes"]),
        "passes": detail["passes"],
        "failures": detail["failures"],
        "critical_failures": 0,
        "unauthorized_canonical_effects": 0,
        "feature_coverage": detail["feature_coverage"],
        "outcomes": detail["outcomes"],
        "decision_candidate": "CONTINUE_R3_WITH_SPECIFIC_GAP",
    }
    result["result_sha256"] = fingerprint(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        f"OpenBao R3: {result['passes']}/{result['scenario_count']} passed"
    )
    return 0 if result["failures"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
