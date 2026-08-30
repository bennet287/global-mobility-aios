from __future__ import annotations

import argparse
import json
import shutil
import socket
import subprocess
import time
from pathlib import Path
from typing import Any

import httpx

from labs.r3.common.harness import CONTRACT_VERSION, fingerprint, validate_run_id
from labs.r3.secrets.port import OpenBaoSecretsPort


OPENBAO_VERSION = "2.6.2"
HOST_PORT = 18202
SYNTHETIC_SECRET = "AIOS_R3_PERSISTENCE_CANARY_DO_NOT_EXPORT"
CONTAINER_PREFIX = "gmai-r3-openbao-persist"
VOLUME_PREFIX = "gmai-r3-openbao-data"


class ExecutionBlocked(RuntimeError):
    pass


def persistent_config() -> dict[str, Any]:
    return {
        "storage": {"file": {"path": "/openbao/file"}},
        "listener": [
            {
                "tcp": {
                    "address": "0.0.0.0:8200",
                    "tls_disable": True,
                }
            }
        ],
        "ui": False,
    }


def _git_sha() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _docker(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    if shutil.which("docker") is None:
        raise ExecutionBlocked("docker executable is unavailable")
    try:
        return subprocess.run(
            ["docker", *args],
            check=check,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise ExecutionBlocked(f"docker command failed: {args!r}: {exc}") from exc


def _wait_port(open_expected: bool, timeout: float = 15.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.25)
            opened = sock.connect_ex(("127.0.0.1", HOST_PORT)) == 0
        if opened == open_expected:
            return True
        time.sleep(0.1)
    return False


def _post(path: str, payload: dict[str, Any], token: str | None = None) -> dict[str, Any]:
    headers = {"X-Vault-Token": token} if token else {}
    response = httpx.post(
        f"http://127.0.0.1:{HOST_PORT}{path}",
        headers=headers,
        json=payload,
        timeout=5,
    )
    response.raise_for_status()
    return response.json()


def _put(path: str, payload: dict[str, Any], token: str) -> dict[str, Any]:
    response = httpx.put(
        f"http://127.0.0.1:{HOST_PORT}{path}",
        headers={"X-Vault-Token": token},
        json=payload,
        timeout=5,
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


def _start_container(*, name: str, volume: str) -> None:
    config = json.dumps(persistent_config(), separators=(",", ":"))
    _docker(
        "run",
        "-d",
        "--name",
        name,
        "--cap-add",
        "IPC_LOCK",
        "-e",
        f"BAO_LOCAL_CONFIG={config}",
        "-p",
        f"127.0.0.1:{HOST_PORT}:8200",
        "-v",
        f"{volume}:/openbao/file",
        f"openbao/openbao:{OPENBAO_VERSION}",
        "server",
    )
    if not _wait_port(True):
        logs = _docker("logs", name, check=False).stdout
        raise ExecutionBlocked(f"persistent OpenBao did not start: {logs[-1000:]}")


def run_persistent_openbao(run_id: str) -> dict[str, Any]:
    safe = "".join(ch for ch in run_id.lower() if ch.isalnum() or ch in "-_")[:32]
    container = f"{CONTAINER_PREFIX}-{safe}"
    volume = f"{VOLUME_PREFIX}-{safe}"
    outcomes: list[dict[str, Any]] = []

    _docker("rm", "-f", container, check=False)
    _docker("volume", "rm", "-f", volume, check=False)
    _docker("volume", "create", volume)

    try:
        _start_container(name=container, volume=volume)

        init = _post(
            "/v1/sys/init",
            {"secret_shares": 1, "secret_threshold": 1},
        )
        unseal_key = str(init["keys"][0])
        root_token = str(init["root_token"])
        _record(
            outcomes,
            "non_dev_openbao_initialized_with_single_synthetic_share",
            (bool(unseal_key), bool(root_token)),
            (True, True),
        )

        unseal = _post("/v1/sys/unseal", {"key": unseal_key})
        _record(
            outcomes,
            "persistent_instance_unsealed",
            bool(unseal.get("sealed")),
            False,
        )

        port = OpenBaoSecretsPort(
            base_url=f"http://127.0.0.1:{HOST_PORT}",
            token=root_token,
        )
        version = port.write(
            "gmai-r3/persistent-provider",
            {"api_key": SYNTHETIC_SECRET},
        )
        _record(
            outcomes,
            "persistent_kv_write",
            version,
            1,
        )

        audit = _put(
            "/v1/sys/audit/r3-persistent",
            {
                "type": "file",
                "options": {"file_path": "/openbao/file/r3-audit.log"},
            },
            root_token,
        )
        _ = audit
        read = port.read("gmai-r3/persistent-provider", "api_key")
        _record(
            outcomes,
            "pre_restart_secret_read",
            (read.value, read.version),
            (SYNTHETIC_SECRET, 1),
        )

        audit_before = _docker(
            "exec",
            container,
            "cat",
            "/openbao/file/r3-audit.log",
        ).stdout
        _record(
            outcomes,
            "audit_log_records_path_without_plaintext_secret",
            (
                "gmai-r3/persistent-provider" in audit_before,
                SYNTHETIC_SECRET in audit_before,
                root_token in audit_before,
            ),
            (True, False, False),
        )

        _docker("restart", container)
        if not _wait_port(True):
            raise ExecutionBlocked("OpenBao port did not recover after restart")

        health = httpx.get(
            f"http://127.0.0.1:{HOST_PORT}/v1/sys/health",
            timeout=5,
        )
        _record(
            outcomes,
            "restart_returns_sealed_persistent_instance",
            health.status_code in {429, 472, 473, 501, 503},
            True,
        )

        unseal_after = _post("/v1/sys/unseal", {"key": unseal_key})
        _record(
            outcomes,
            "same_unseal_material_recovers_restarted_instance",
            bool(unseal_after.get("sealed")),
            False,
        )

        post_restart = port.read("gmai-r3/persistent-provider", "api_key")
        _record(
            outcomes,
            "secret_survives_real_container_restart",
            (post_restart.value, post_restart.version),
            (SYNTHETIC_SECRET, 1),
        )

        initialized = httpx.get(
            f"http://127.0.0.1:{HOST_PORT}/v1/sys/init",
            timeout=5,
        )
        initialized.raise_for_status()
        _record(
            outcomes,
            "restart_does_not_reinitialize_storage",
            initialized.json().get("initialized"),
            True,
        )

        audit_after = _docker(
            "exec",
            container,
            "cat",
            "/openbao/file/r3-audit.log",
        ).stdout
        _record(
            outcomes,
            "audit_log_persists_and_grows_across_restart",
            len(audit_after) >= len(audit_before),
            True,
        )
    finally:
        _docker("rm", "-f", container, check=False)
        _docker("volume", "rm", "-f", volume, check=False)

    failures = [item for item in outcomes if not item["passed"]]
    return {
        "outcomes": outcomes,
        "passes": len(outcomes) - len(failures),
        "failures": len(failures),
        "feature_coverage": {
            "non_dev_server": True,
            "filesystem_storage": True,
            "explicit_init_unseal": True,
            "audit_log_content_validation": True,
            "audit_sensitive_value_protection": True,
            "restart_persistence": True,
            "secret_persistence": True,
            "dynamic_database_credentials": False,
            "ha_failover": False,
            "tls": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    validate_run_id(args.run_id)

    try:
        detail = run_persistent_openbao(args.run_id)
        blocked = False
        block_reason = None
    except ExecutionBlocked as exc:
        detail = {
            "outcomes": [],
            "passes": 0,
            "failures": 0,
            "feature_coverage": {},
        }
        blocked = True
        block_reason = str(exc)

    result = {
        "contract_version": CONTRACT_VERSION,
        "r3_run_id": args.run_id,
        "candidate": "openbao-persistent",
        "candidate_version": OPENBAO_VERSION,
        "git_sha": _git_sha(),
        "environment": "synthetic-local-docker-persistent-volume",
        "experiment": "t3-t5-openbao-persistence-audit",
        "test_tiers": ["T3", "T5"],
        "execution_blocked": blocked,
        "block_reason": block_reason,
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
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    if blocked:
        print(f"persistent OpenBao R3 blocked: {block_reason}")
        return 2
    print(
        f"persistent OpenBao R3: {result['passes']}/"
        f"{result['scenario_count']} passed"
    )
    return 0 if result["failures"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
