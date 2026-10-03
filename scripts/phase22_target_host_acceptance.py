#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import socket
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from sqlmodel import Session

from app.core.db import engine, register_models
from app.models.domain import OrganizationActorType
from app.models.production_deployment_acceptance import ProductionDeploymentAcceptanceRun
from app.services.organization_command import (
    OrganizationCommandContext,
    canonical_fingerprint,
    tenant_record,
)
from app.services.production_deployment_acceptance import (
    DEPLOYMENT_ACCEPTANCE_GATES,
    TARGET_HOST_FOUNDATION_EXECUTOR_ACTOR,
    TARGET_HOST_FOUNDATION_EXECUTOR_CONTRACT_KEY,
    TARGET_HOST_FOUNDATION_EXECUTOR_CONTRACT_VERSION,
    record_target_host_foundation_receipt,
)


HOST_IDENTITY_CONTRACT = "phase22.target-host-environment.v1"
RELEASE_IDENTITY_CONTRACT = "phase22.release-identity.v1"
RELEASE_REVISION_LABEL = "org.opencontainers.image.revision"
RELEASE_CONFIGURATION_LABEL = (
    "com.global-mobility-aios.release-configuration-fingerprint"
)
RELEASE_CONTRACT_LABEL = "com.global-mobility-aios.release-identity-contract"
PRODUCTION_APPLICATION_CONTAINERS = (
    "gmai-api-prod",
    "gmai-web-prod",
    "gmai-worker-prod",
    "gmai-beat-prod",
)
MACHINE_ID_PATHS = (
    Path("/etc/machine-id"),
    Path("/var/lib/dbus/machine-id"),
)


@dataclass(frozen=True)
class RunningContainerIdentity:
    container_name: str
    image_id: str


def _sha256_json(value: dict[str, Any]) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def read_machine_id(paths: tuple[Path, ...] = MACHINE_ID_PATHS) -> str:
    for path in paths:
        if path.is_file():
            value = path.read_text(encoding="utf-8").strip()
            if value:
                return value
    raise RuntimeError("Target host machine-id is unavailable")


def target_environment_fingerprint(
    *,
    machine_id: str,
    hostname: str,
    system_name: str,
    machine_architecture: str,
) -> str:
    values = {
        "contract": HOST_IDENTITY_CONTRACT,
        "machine_id": machine_id.strip(),
        "hostname": hostname.strip().lower(),
        "system": system_name.strip().lower(),
        "machine": machine_architecture.strip().lower(),
    }
    if not all(values[key] for key in ("machine_id", "hostname", "system", "machine")):
        raise RuntimeError("Target host identity inputs must be non-empty")
    return _sha256_json(values)


def resolve_target_environment_fingerprint() -> str:
    return target_environment_fingerprint(
        machine_id=read_machine_id(),
        hostname=socket.gethostname(),
        system_name=platform.system(),
        machine_architecture=platform.machine(),
    )


def _run_text(command: list[str]) -> str:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "command failed"
        raise RuntimeError(f"{' '.join(command[:3])} failed: {detail[:2000]}")
    return completed.stdout.strip()


def _container_labels(container_name: str) -> dict[str, str]:
    payload = _run_text(
        ["docker", "inspect", "--format", "{{json .Config.Labels}}", container_name]
    )
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Container {container_name} labels were not valid JSON"
        ) from exc
    if not isinstance(parsed, dict):
        raise RuntimeError(f"Container {container_name} labels are unavailable")
    return {str(key): str(value) for key, value in parsed.items()}


def verify_running_release_identity(
    *,
    expected_commit_sha: str,
    expected_configuration_fingerprint: str,
) -> tuple[RunningContainerIdentity, ...]:
    observed: list[RunningContainerIdentity] = []
    for container_name in PRODUCTION_APPLICATION_CONTAINERS:
        running = _run_text(
            ["docker", "inspect", "--format", "{{.State.Running}}", container_name]
        ).strip().lower()
        if running != "true":
            raise RuntimeError(f"Container {container_name} is not running")

        labels = _container_labels(container_name)
        if labels.get(RELEASE_REVISION_LABEL) != expected_commit_sha:
            raise RuntimeError(
                f"Container {container_name} release revision does not match the prepared run"
            )
        if (
            labels.get(RELEASE_CONFIGURATION_LABEL)
            != expected_configuration_fingerprint
        ):
            raise RuntimeError(
                f"Container {container_name} release configuration does not match the prepared run"
            )
        if labels.get(RELEASE_CONTRACT_LABEL) != RELEASE_IDENTITY_CONTRACT:
            raise RuntimeError(
                f"Container {container_name} release identity contract is unsupported"
            )
        image_id = _run_text(
            ["docker", "inspect", "--format", "{{.Image}}", container_name]
        )
        if not image_id:
            raise RuntimeError(f"Container {container_name} image identity is missing")
        observed.append(
            RunningContainerIdentity(
                container_name=container_name,
                image_id=image_id,
            )
        )
    return tuple(observed)


def _executor_context(tenant_key: str) -> OrganizationCommandContext:
    return OrganizationCommandContext(
        tenant_key=tenant_key,
        actor_id=TARGET_HOST_FOUNDATION_EXECUTOR_ACTOR,
        actor_type=OrganizationActorType.system,
        authenticated_user_id="system",
        role="operator",
        department="Technology",
        position_key=None,
        authority_level=None,
    )


def _gate_blocker(gate_key: str) -> str:
    blockers = {
        "release_networking": (
            "release identity was verified, but HTTPS/network exposure, restart and rollback "
            "probes are not implemented by foundation v1"
        ),
        "identity_boundaries": (
            "browser sign-in, expiry, role denial, CORS, cookie and secret-boundary probes "
            "are not implemented by foundation v1"
        ),
        "core_journey": (
            "the real synthetic web-to-worker durable journey is not implemented by foundation v1"
        ),
        "documents_integrations": (
            "real document-store and enabled external-integration probes are not implemented "
            "by foundation v1"
        ),
        "failure_recovery": (
            "backup/restore and dependency-outage recovery probes are not implemented by foundation v1"
        ),
        "operations": (
            "health, observability, incident, rotation, capacity and cost drills are not implemented "
            "by foundation v1"
        ),
    }
    return blockers[gate_key]


def record_foundation_receipts(
    session: Session,
    *,
    tenant_key: str,
    run_id: UUID,
) -> dict[str, Any]:
    context = _executor_context(tenant_key)
    run = tenant_record(
        session,
        ProductionDeploymentAcceptanceRun,
        run_id,
        tenant_key,
        label="deployment acceptance run",
    )
    observed_environment = resolve_target_environment_fingerprint()
    if observed_environment != run.target_environment_fingerprint:
        raise RuntimeError(
            "Observed target-host fingerprint does not match the prepared deployment run"
        )
    containers = verify_running_release_identity(
        expected_commit_sha=run.release_commit_sha,
        expected_configuration_fingerprint=run.release_configuration_fingerprint,
    )
    container_evidence = [
        {
            "container_name": item.container_name,
            "image_id": item.image_id,
        }
        for item in containers
    ]
    for gate in DEPLOYMENT_ACCEPTANCE_GATES:
        details = {
            "executor_contract_key": TARGET_HOST_FOUNDATION_EXECUTOR_CONTRACT_KEY,
            "executor_contract_version": TARGET_HOST_FOUNDATION_EXECUTOR_CONTRACT_VERSION,
            "target_environment_fingerprint_verified": True,
            "release_identity_verified": True,
            "running_application_containers": container_evidence,
            "gate_probe_implemented": False,
            "blocker": _gate_blocker(gate.gate_key),
            "secret_values_recorded": False,
        }
        record_target_host_foundation_receipt(
            session,
            context,
            deployment_run_id=run.id,
            gate_key=gate.gate_key,
            status="blocked",
            observed_target_environment_fingerprint=observed_environment,
            observed_release_commit_sha=run.release_commit_sha,
            observed_release_configuration_fingerprint=run.release_configuration_fingerprint,
            redacted_details=details,
        )

    return {
        "deployment_run_id": str(run.id),
        "target_environment_fingerprint": observed_environment,
        "release_commit_sha": run.release_commit_sha,
        "release_configuration_fingerprint": run.release_configuration_fingerprint,
        "executor_contract_key": TARGET_HOST_FOUNDATION_EXECUTOR_CONTRACT_KEY,
        "executor_contract_version": TARGET_HOST_FOUNDATION_EXECUTOR_CONTRACT_VERSION,
        "checks_complete": True,
        "canary_evidence_status": "blocked",
        "canary_evidence_satisfied": False,
        "gate_statuses": {
            gate.gate_key: "blocked"
            for gate in DEPLOYMENT_ACCEPTANCE_GATES
        },
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Phase 22 target-host foundation executor. It can derive the canonical host "
            "fingerprint and persist fail-closed receipts, but cannot satisfy any acceptance gate."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    fingerprint = subparsers.add_parser(
        "fingerprint",
        help="Print the deterministic target-host fingerprint used by a prepared acceptance run",
    )
    fingerprint.add_argument("--json", action="store_true")

    record = subparsers.add_parser(
        "record-foundation",
        help=(
            "Verify target-host and running release identity, then persist six blocked foundation receipts"
        ),
    )
    record.add_argument("--run-id", type=UUID, required=True)
    record.add_argument("--tenant-key", default="default")
    record.add_argument("--json", action="store_true")
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        if args.command == "fingerprint":
            value = resolve_target_environment_fingerprint()
            payload = {
                "contract": HOST_IDENTITY_CONTRACT,
                "target_environment_fingerprint": value,
                "limitations": [
                    "This is a deterministic host identity hash, not cryptographic remote attestation.",
                    "The host operator remains inside the trust boundary.",
                ],
            }
        else:
            register_models()
            with Session(engine) as session:
                payload = record_foundation_receipts(
                    session,
                    tenant_key=args.tenant_key,
                    run_id=args.run_id,
                )

        if getattr(args, "json", False):
            print(json.dumps(payload, sort_keys=True))
        elif args.command == "fingerprint":
            print(payload["target_environment_fingerprint"])
        else:
            print(
                "Phase 22 foundation receipts recorded: "
                f"run={payload['deployment_run_id']} "
                f"status={payload['canary_evidence_status']} "
                f"satisfied={payload['canary_evidence_satisfied']}"
            )
        return 0
    except Exception as exc:
        print(f"Phase 22 target-host foundation executor failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
