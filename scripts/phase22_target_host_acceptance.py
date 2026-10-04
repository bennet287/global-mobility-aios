#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import socket
import ssl
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
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
from app.schemas_phase22_external_network_verifier import Phase22ExternalNetworkManifestEnvelope
from app.services.organization_command import (
    OrganizationCommandContext,
    canonical_fingerprint,
    tenant_record,
)
from app.services.phase22_external_network_verifier import (
    ExternalNetworkVerifierEvidenceError,
    verify_external_network_manifest,
)
from app.services.production_deployment_acceptance import (
    DEPLOYMENT_ACCEPTANCE_GATES,
    TARGET_HOST_FOUNDATION_EXECUTOR_ACTOR,
    TARGET_HOST_FOUNDATION_EXECUTOR_CONTRACT_KEY,
    TARGET_HOST_FOUNDATION_EXECUTOR_CONTRACT_VERSION,
    TARGET_HOST_RELEASE_NETWORKING_EXECUTOR_ACTOR,
    TARGET_HOST_RELEASE_NETWORKING_EXECUTOR_CONTRACT_KEY,
    TARGET_HOST_RELEASE_NETWORKING_EXECUTOR_CONTRACT_VERSION,
    TARGET_HOST_RELEASE_NETWORKING_VERIFIER_REF,
    record_target_host_foundation_receipt,
    record_target_host_release_networking_receipt,
    validated_deployment_networking_contract,
)
from scripts.production_release_identity import compute_release_configuration_fingerprint


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
INGRESS_CONTAINER = "gmai-ingress-prod"
COMPOSE_PROJECT_LABEL = "com.docker.compose.project"
RELEASE_SWITCH_SERVICES = ("api", "worker", "beat", "web", "ingress")
LOCAL_HTTPS_PATHS = (("web_hostname", "/"), ("api_hostname", "/health"))


@dataclass(frozen=True)
class RunningContainerIdentity:
    container_name: str
    image_id: str


@dataclass(frozen=True)
class DatabaseCompatibilityObservation:
    schema_revision: str
    stable_leads_count: int


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


def _run_process(
    command: list[str],
    *,
    cwd: Path = ROOT,
    env: dict[str, str] | None = None,
    timeout: int = 300,
    label: str = "command",
) -> str:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"{label}:timeout") from exc
    if completed.returncode != 0:
        raise RuntimeError(f"{label}:exit_{completed.returncode}")
    return completed.stdout.strip()


def _git_text(root: Path, *args: str) -> str:
    return _run_process(
        ["git", *args],
        cwd=root,
        timeout=30,
        label="git",
    )


def trusted_executor_commit_sha(root: Path = ROOT) -> str:
    branch = _git_text(root, "rev-parse", "--abbrev-ref", "HEAD")
    if branch != "main":
        raise RuntimeError("executor_checkout:not_main")
    if _git_text(root, "status", "--porcelain", "--untracked-files=all"):
        raise RuntimeError("executor_checkout:dirty")
    commit = _git_text(root, "rev-parse", "HEAD").lower()
    if len(commit) != 40 or any(ch not in "0123456789abcdef" for ch in commit):
        raise RuntimeError("executor_checkout:invalid_commit")
    return commit


def verify_release_checkout(
    root: Path,
    *,
    expected_commit_sha: str,
    expected_configuration_fingerprint: str,
) -> None:
    root = root.resolve()
    if not (root / ".git").exists() and not (root / ".git").is_file():
        raise RuntimeError("release_checkout:not_git")
    if _git_text(root, "status", "--porcelain", "--untracked-files=all"):
        raise RuntimeError("release_checkout:dirty")
    observed_commit = _git_text(root, "rev-parse", "HEAD").lower()
    if observed_commit != expected_commit_sha:
        raise RuntimeError("release_checkout:commit_mismatch")
    observed_configuration = compute_release_configuration_fingerprint(root)
    if observed_configuration != expected_configuration_fingerprint:
        raise RuntimeError("release_checkout:configuration_mismatch")
    if not (root / "docker-compose.prod.yml").is_file():
        raise RuntimeError("release_checkout:compose_missing")


def _image_labels(image_reference: str) -> dict[str, str]:
    payload = _run_text(
        ["docker", "image", "inspect", "--format", "{{json .Config.Labels}}", image_reference]
    )
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise RuntimeError("release_image:labels_invalid") from exc
    if not isinstance(parsed, dict):
        raise RuntimeError("release_image:labels_missing")
    return {str(key): str(value) for key, value in parsed.items()}


def verify_release_images(
    *,
    commit_sha: str,
    configuration_fingerprint: str,
) -> None:
    for image_reference in (
        f"global-mobility-aios-api:{commit_sha}-{configuration_fingerprint}",
        f"global-mobility-aios-web:{commit_sha}-{configuration_fingerprint}",
    ):
        labels = _image_labels(image_reference)
        if labels.get(RELEASE_REVISION_LABEL) != commit_sha:
            raise RuntimeError("release_image:commit_mismatch")
        if labels.get(RELEASE_CONFIGURATION_LABEL) != configuration_fingerprint:
            raise RuntimeError("release_image:configuration_mismatch")
        if labels.get(RELEASE_CONTRACT_LABEL) != RELEASE_IDENTITY_CONTRACT:
            raise RuntimeError("release_image:contract_mismatch")


def resolve_compose_project_name() -> str:
    projects: set[str] = set()
    for container_name in (*PRODUCTION_APPLICATION_CONTAINERS, INGRESS_CONTAINER):
        labels = _container_labels(container_name)
        project = labels.get(COMPOSE_PROJECT_LABEL, "").strip()
        if not project:
            raise RuntimeError("compose_project:missing")
        projects.add(project)
    if len(projects) != 1:
        raise RuntimeError("compose_project:mismatch")
    return next(iter(projects))


def _release_environment(
    *,
    commit_sha: str,
    configuration_fingerprint: str,
) -> dict[str, str]:
    env = dict(os.environ)
    env["AIOS_RELEASE_COMMIT_SHA"] = commit_sha
    env["AIOS_RELEASE_CONFIGURATION_FINGERPRINT"] = configuration_fingerprint
    return env


def _compose_base(
    release_root: Path,
    *,
    env_file: Path,
    project_name: str,
) -> list[str]:
    return [
        "docker",
        "compose",
        "-p",
        project_name,
        "--env-file",
        str(env_file.resolve()),
        "-f",
        str((release_root / "docker-compose.prod.yml").resolve()),
    ]


def _container_running(container_name: str) -> bool:
    return (
        _run_text(
            ["docker", "inspect", "--format", "{{.State.Running}}", container_name]
        ).strip().lower()
        == "true"
    )


def _container_health(container_name: str) -> str:
    return _run_text(
        [
            "docker",
            "inspect",
            "--format",
            "{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}",
            container_name,
        ]
    ).strip().lower()


def wait_release_ready(
    *,
    expected_commit_sha: str,
    expected_configuration_fingerprint: str,
    timeout_seconds: int = 180,
) -> tuple[RunningContainerIdentity, ...]:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            if (
                _container_running("gmai-api-prod")
                and _container_health("gmai-api-prod") == "healthy"
                and _container_running("gmai-web-prod")
                and _container_health("gmai-web-prod") == "healthy"
                and _container_running("gmai-worker-prod")
                and _container_running("gmai-beat-prod")
                and _container_running(INGRESS_CONTAINER)
            ):
                return verify_running_release_identity(
                    expected_commit_sha=expected_commit_sha,
                    expected_configuration_fingerprint=expected_configuration_fingerprint,
                )
        except RuntimeError:
            pass
        time.sleep(2)
    raise RuntimeError("release_health:timeout")


def _https_status(hostname: str, path: str) -> int:
    context = ssl.create_default_context()
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    raw_socket: socket.socket | None = None
    tls_socket: ssl.SSLSocket | None = None
    try:
        raw_socket = socket.create_connection(("127.0.0.1", 443), timeout=10)
        tls_socket = context.wrap_socket(raw_socket, server_hostname=hostname)
        raw_socket = None
        request = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {hostname}\r\n"
            "User-Agent: global-mobility-aios-phase22-target-host/2\r\n"
            "Connection: close\r\n\r\n"
        ).encode("ascii")
        tls_socket.sendall(request)
        status_line = tls_socket.makefile("rb").readline(4096).decode(
            "iso-8859-1",
            errors="replace",
        )
        parts = status_line.split(" ", 2)
        if len(parts) < 2 or not parts[1].isdigit():
            raise RuntimeError("local_https:invalid_status")
        return int(parts[1])
    finally:
        if tls_socket is not None:
            tls_socket.close()
        if raw_socket is not None:
            raw_socket.close()


def verify_local_https(networking_contract: dict[str, Any]) -> None:
    for hostname_key, path in LOCAL_HTTPS_PATHS:
        hostname = str(networking_contract[hostname_key])
        status = _https_status(hostname, path)
        if status < 200 or status >= 400:
            raise RuntimeError("local_https:unexpected_status")


_DATABASE_COMPATIBILITY_CODE = r"""
import json
from sqlalchemy import inspect, text
from sqlmodel import SQLModel
from app.core.db import engine, register_models

register_models()
inspector = inspect(engine)
observed_tables = set(inspector.get_table_names())
missing_tables = []
missing_columns = {}
unsafe_extra_columns = {}
for table_name, table in SQLModel.metadata.tables.items():
    if table_name not in observed_tables:
        missing_tables.append(table_name)
        continue
    expected = {column.name for column in table.columns}
    live_columns = inspector.get_columns(table_name)
    observed = {column["name"] for column in live_columns}
    unsafe = sorted(
        column["name"] for column in live_columns
        if column["name"] not in expected
        and not column.get("nullable", True)
        and column.get("default") is None
        and not column.get("computed")
        and not column.get("identity")
        and not column.get("autoincrement")
    )
    if unsafe:
        unsafe_extra_columns[table_name] = unsafe
    missing = sorted(expected - observed)
    if missing:
        missing_columns[table_name] = missing

with engine.connect() as connection:
    connection.execute(text("SET TRANSACTION READ ONLY"))
    connection.execute(text("SELECT 1"))
    revisions = [str(row[0]) for row in connection.execute(text("SELECT version_num FROM alembic_version"))]
    leads_count = int(connection.execute(text("SELECT COUNT(*) FROM leads")).scalar_one())

print(json.dumps({
    "missing_tables": sorted(missing_tables),
    "missing_columns": missing_columns,
    "unsafe_extra_columns": unsafe_extra_columns,
    "schema_revisions": revisions,
    "leads_count": leads_count,
}, sort_keys=True))
"""


def database_compatibility_probe() -> DatabaseCompatibilityObservation:
    payload = _run_process(
        [
            "docker",
            "exec",
            "gmai-api-prod",
            "python",
            "-c",
            _DATABASE_COMPATIBILITY_CODE,
        ],
        timeout=60,
        label="database_compatibility_probe",
    )
    try:
        parsed = json.loads(payload.splitlines()[-1])
    except (json.JSONDecodeError, IndexError) as exc:
        raise RuntimeError("database_compatibility_probe:invalid_json") from exc
    if not isinstance(parsed, dict):
        raise RuntimeError("database_compatibility_probe:invalid_payload")
    if parsed.get("missing_tables") or parsed.get("missing_columns") or parsed.get("unsafe_extra_columns"):
        raise RuntimeError("database_compatibility_probe:model_schema_mismatch")
    revisions = parsed.get("schema_revisions")
    if not isinstance(revisions, list) or len(revisions) != 1 or not str(revisions[0]).strip():
        raise RuntimeError("database_compatibility_probe:revision_invalid")
    leads_count = parsed.get("leads_count")
    if not isinstance(leads_count, int) or leads_count < 0:
        raise RuntimeError("database_compatibility_probe:stable_data_invalid")
    return DatabaseCompatibilityObservation(
        schema_revision=str(revisions[0]),
        stable_leads_count=leads_count,
    )


def restart_candidate_release(
    candidate_root: Path,
    *,
    env_file: Path,
    project_name: str,
    commit_sha: str,
    configuration_fingerprint: str,
    networking_contract: dict[str, Any],
    timeout_seconds: int,
) -> None:
    env = _release_environment(
        commit_sha=commit_sha,
        configuration_fingerprint=configuration_fingerprint,
    )
    _run_process(
        [
            *_compose_base(candidate_root, env_file=env_file, project_name=project_name),
            "restart",
            *RELEASE_SWITCH_SERVICES,
        ],
        cwd=candidate_root,
        env=env,
        timeout=timeout_seconds,
        label="candidate_restart",
    )
    wait_release_ready(
        expected_commit_sha=commit_sha,
        expected_configuration_fingerprint=configuration_fingerprint,
        timeout_seconds=timeout_seconds,
    )
    verify_local_https(networking_contract)


def switch_release(
    release_root: Path,
    *,
    env_file: Path,
    project_name: str,
    commit_sha: str,
    configuration_fingerprint: str,
    networking_contract: dict[str, Any],
    timeout_seconds: int,
) -> None:
    env = _release_environment(
        commit_sha=commit_sha,
        configuration_fingerprint=configuration_fingerprint,
    )
    base = _compose_base(release_root, env_file=env_file, project_name=project_name)
    _run_process(
        [*base, "config", "--quiet"],
        cwd=release_root,
        env=env,
        timeout=60,
        label="compose_config",
    )
    _run_process(
        [
            *base,
            "up",
            "-d",
            "--no-build",
            "--pull",
            "never",
            "--no-deps",
            "--force-recreate",
            *RELEASE_SWITCH_SERVICES,
        ],
        cwd=release_root,
        env=env,
        timeout=timeout_seconds,
        label="release_switch",
    )
    wait_release_ready(
        expected_commit_sha=commit_sha,
        expected_configuration_fingerprint=configuration_fingerprint,
        timeout_seconds=timeout_seconds,
    )
    verify_local_https(networking_contract)


def _release_networking_executor_context(tenant_key: str) -> OrganizationCommandContext:
    return OrganizationCommandContext(
        tenant_key=tenant_key,
        actor_id=TARGET_HOST_RELEASE_NETWORKING_EXECUTOR_ACTOR,
        actor_type=OrganizationActorType.system,
        authenticated_user_id="system",
        role="operator",
        department="Technology",
        position_key=None,
        authority_level=None,
    )


def _load_external_envelope(path: Path) -> Phase22ExternalNetworkManifestEnvelope:
    try:
        return Phase22ExternalNetworkManifestEnvelope.model_validate_json(
            path.read_text(encoding="utf-8")
        )
    except Exception as exc:
        raise RuntimeError("external_network_envelope:invalid") from exc


def wait_post_restore_external_observation(
    session: Session,
    context: OrganizationCommandContext,
    *,
    run_id: UUID,
    path: Path,
    candidate_restored_at: datetime,
    previous_manifest_sha256: str,
    timeout_seconds: int,
):
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            envelope = _load_external_envelope(path)
            observation = verify_external_network_manifest(
                session, context, deployment_run_id=run_id, envelope=envelope,
            )
        except (RuntimeError, ValueError, ExternalNetworkVerifierEvidenceError):
            time.sleep(2)
            continue
        if (
            observation.manifest_sha256 != previous_manifest_sha256
            and observation.observed_started_at >= candidate_restored_at
            and observation.verifier_ref == TARGET_HOST_RELEASE_NETWORKING_VERIFIER_REF
        ):
            return observation
        time.sleep(2)
    raise RuntimeError("external_network:post_restore_evidence_timeout")


def _failure_code(exc: BaseException) -> str:
    message = str(exc)
    if ":" in message and len(message) <= 200:
        return message
    return f"{type(exc).__name__}"[:200]


def _empty_release_networking_details(
    run: ProductionDeploymentAcceptanceRun,
    *,
    executor_commit_sha: str,
    external_observation,
) -> dict[str, Any]:
    return {
        "executor_commit_sha": executor_commit_sha,
        "target_environment_fingerprint_verified": False,
        "candidate_release_identity_verified": False,
        "candidate_restart_verified": False,
        "candidate_restart_health_verified": False,
        "external_network_manifest_sha256": external_observation.manifest_sha256,
        "external_verifier_public_key_fingerprint": external_observation.verifier_public_key_fingerprint,
        "external_verifier_ref": external_observation.verifier_ref,
        "external_verifier_commit_sha": external_observation.verifier_commit_sha,
        "external_network_contract_satisfied": external_observation.network_contract_satisfied,
        "external_network_observed_after_restore": False,
        "rollback_release_commit_sha": run.rollback_release_commit_sha,
        "rollback_configuration_fingerprint": run.rollback_configuration_fingerprint,
        "rollback_image_identity_verified": False,
        "rollback_retained_schema_verified": False,
        "rollback_release_identity_verified": False,
        "rollback_schema_compatibility_verified": False,
        "rollback_stable_data_verified": False,
        "rollback_health_verified": False,
        "candidate_restore_retained_schema_verified": False,
        "candidate_restored": False,
        "candidate_restore_identity_verified": False,
        "candidate_restore_schema_compatibility_verified": False,
        "candidate_restore_stable_data_verified": False,
        "candidate_restore_health_verified": False,
        "candidate_schema_revision_before": None,
        "rollback_schema_revision": None,
        "candidate_schema_revision_after_restore": None,
        "failure_stage": None,
        "failure_code": None,
        "secret_values_recorded": False,
    }


def record_release_networking_v2(
    session: Session,
    *,
    tenant_key: str,
    run_id: UUID,
    external_network_envelope: Path,
    env_file: Path,
    candidate_root: Path,
    rollback_root: Path,
    timeout_seconds: int = 180,
) -> dict[str, Any]:
    if timeout_seconds < 30 or timeout_seconds > 900:
        raise RuntimeError("executor_timeout:out_of_bounds")
    if not env_file.is_file():
        raise RuntimeError("production_env_file:missing")

    context = _release_networking_executor_context(tenant_key)
    run, networking_contract = validated_deployment_networking_contract(
        session,
        context,
        deployment_run_id=run_id,
        require_fresh_release_networking=True,
    )
    executor_commit_sha = trusted_executor_commit_sha(ROOT)
    verify_release_checkout(
        candidate_root,
        expected_commit_sha=run.release_commit_sha,
        expected_configuration_fingerprint=run.release_configuration_fingerprint,
    )
    verify_release_checkout(
        rollback_root,
        expected_commit_sha=run.rollback_release_commit_sha,
        expected_configuration_fingerprint=run.rollback_configuration_fingerprint,
    )

    envelope = _load_external_envelope(external_network_envelope)
    external = verify_external_network_manifest(
        session,
        context,
        deployment_run_id=run.id,
        envelope=envelope,
    )
    if external.verifier_ref != TARGET_HOST_RELEASE_NETWORKING_VERIFIER_REF:
        raise RuntimeError("external_network:unprotected_verifier_ref")

    details = _empty_release_networking_details(
        run,
        executor_commit_sha=executor_commit_sha,
        external_observation=external,
    )
    observed_environment = resolve_target_environment_fingerprint()
    if observed_environment != run.target_environment_fingerprint:
        raise RuntimeError("target_environment:fingerprint_mismatch")
    details["target_environment_fingerprint_verified"] = True

    verify_release_images(
        commit_sha=run.release_commit_sha,
        configuration_fingerprint=run.release_configuration_fingerprint,
    )
    verify_release_images(
        commit_sha=run.rollback_release_commit_sha,
        configuration_fingerprint=run.rollback_configuration_fingerprint,
    )
    details["rollback_image_identity_verified"] = True

    verify_running_release_identity(
        expected_commit_sha=run.release_commit_sha,
        expected_configuration_fingerprint=run.release_configuration_fingerprint,
    )
    details["candidate_release_identity_verified"] = True
    project_name = resolve_compose_project_name()

    if not external.network_contract_satisfied:
        details["failure_stage"] = "external_network"
        details["failure_code"] = (
            external.blockers[0] if external.blockers else "external_network_contract_failed"
        )
        receipt = record_target_host_release_networking_receipt(
            session,
            context,
            deployment_run_id=run.id,
            status="failed",
            observed_target_environment_fingerprint=observed_environment,
            observed_release_commit_sha=run.release_commit_sha,
            observed_release_configuration_fingerprint=run.release_configuration_fingerprint,
            executor_commit_sha=executor_commit_sha,
            redacted_details=details,
        )
        return {
            "deployment_run_id": str(run.id),
            "receipt_id": str(receipt.id),
            "status": receipt.status,
            "release_networking_satisfied": False,
            "candidate_restored": False,
        }

    baseline: DatabaseCompatibilityObservation | None = None
    failure_stage: str | None = None
    failure_code: str | None = None
    rollback_started = False
    candidate_restored_at: datetime | None = None
    try:
        restart_candidate_release(
            candidate_root,
            env_file=env_file,
            project_name=project_name,
            commit_sha=run.release_commit_sha,
            configuration_fingerprint=run.release_configuration_fingerprint,
            networking_contract=networking_contract,
            timeout_seconds=timeout_seconds,
        )
        details["candidate_restart_verified"] = True
        details["candidate_restart_health_verified"] = True
        baseline = database_compatibility_probe()
        details["candidate_schema_revision_before"] = baseline.schema_revision

        rollback_started = True
        switch_release(
            rollback_root,
            env_file=env_file,
            project_name=project_name,
            commit_sha=run.rollback_release_commit_sha,
            configuration_fingerprint=run.rollback_configuration_fingerprint,
            networking_contract=networking_contract,
            timeout_seconds=timeout_seconds,
        )
        details["rollback_release_identity_verified"] = True
        details["rollback_health_verified"] = True
        rollback_probe = database_compatibility_probe()
        details["rollback_schema_revision"] = rollback_probe.schema_revision
        details["rollback_retained_schema_verified"] = (
            rollback_probe.schema_revision == baseline.schema_revision
        )
        details["rollback_schema_compatibility_verified"] = (
            rollback_probe.schema_revision == baseline.schema_revision
        )
        details["rollback_stable_data_verified"] = (
            rollback_probe.stable_leads_count == baseline.stable_leads_count
        )
        if not details["rollback_schema_compatibility_verified"]:
            raise RuntimeError("rollback:schema_revision_changed")
        if not details["rollback_stable_data_verified"]:
            raise RuntimeError("rollback:stable_data_changed")
    except Exception as exc:
        failure_stage = "rollback" if rollback_started else "candidate_restart"
        failure_code = _failure_code(exc)
    finally:
        try:
            switch_release(
                candidate_root,
                env_file=env_file,
                project_name=project_name,
                commit_sha=run.release_commit_sha,
                configuration_fingerprint=run.release_configuration_fingerprint,
                networking_contract=networking_contract,
                timeout_seconds=timeout_seconds,
            )
            details["candidate_restored"] = True
            details["candidate_restore_identity_verified"] = True
            details["candidate_restore_health_verified"] = True
            restored_probe = database_compatibility_probe()
            details["candidate_schema_revision_after_restore"] = restored_probe.schema_revision
            if baseline is not None:
                details["candidate_restore_retained_schema_verified"] = (
                    restored_probe.schema_revision == baseline.schema_revision
                )
                details["candidate_restore_schema_compatibility_verified"] = (
                    restored_probe.schema_revision == baseline.schema_revision
                )
                details["candidate_restore_stable_data_verified"] = (
                    restored_probe.stable_leads_count == baseline.stable_leads_count
                )
            if not details["candidate_restore_schema_compatibility_verified"]:
                raise RuntimeError("candidate_restore:schema_revision_changed")
            if not details["candidate_restore_stable_data_verified"]:
                raise RuntimeError("candidate_restore:stable_data_changed")
            candidate_restored_at = datetime.now(timezone.utc)
            print("Phase 22 candidate restored; transfer a newly signed external-network envelope "
                  f"observed after {candidate_restored_at.isoformat()}", file=sys.stderr)
        except Exception as exc:
            failure_stage = "candidate_restore"
            failure_code = _failure_code(exc)

    if candidate_restored_at is None:
        raise RuntimeError("candidate_restore:unverified_operator_intervention_required")
    if failure_stage is None:
        try:
            external = wait_post_restore_external_observation(
                session, context, run_id=run.id, path=external_network_envelope,
                candidate_restored_at=candidate_restored_at,
                previous_manifest_sha256=external.manifest_sha256,
                timeout_seconds=timeout_seconds,
            )
            details["external_network_manifest_sha256"] = external.manifest_sha256
            details["external_verifier_public_key_fingerprint"] = external.verifier_public_key_fingerprint
            details["external_verifier_ref"] = external.verifier_ref
            details["external_verifier_commit_sha"] = external.verifier_commit_sha
            details["external_network_contract_satisfied"] = external.network_contract_satisfied
            details["external_network_observed_after_restore"] = True
            if not external.network_contract_satisfied:
                raise RuntimeError("external_network:post_restore_network_failed")
        except Exception as exc:
            failure_stage = "external_network_after_restore"
            failure_code = _failure_code(exc)

    details["failure_stage"] = failure_stage
    details["failure_code"] = failure_code
    status = "satisfied" if failure_stage is None else "failed"
    receipt = record_target_host_release_networking_receipt(
        session,
        context,
        deployment_run_id=run.id,
        status=status,
        observed_target_environment_fingerprint=observed_environment,
        observed_release_commit_sha=run.release_commit_sha,
        observed_release_configuration_fingerprint=run.release_configuration_fingerprint,
        executor_commit_sha=executor_commit_sha,
        redacted_details=details,
    )
    return {
        "deployment_run_id": str(run.id),
        "receipt_id": str(receipt.id),
        "status": receipt.status,
        "release_networking_satisfied": receipt.status == "satisfied",
        "candidate_restored": details["candidate_restored"],
        "executor_contract_key": TARGET_HOST_RELEASE_NETWORKING_EXECUTOR_CONTRACT_KEY,
        "executor_contract_version": TARGET_HOST_RELEASE_NETWORKING_EXECUTOR_CONTRACT_VERSION,
    }


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

    networking = subparsers.add_parser(
        "record-release-networking",
        help=(
            "Run the satisfied-capable Phase 22 release/networking v2 drill for one fresh prepared run"
        ),
    )
    networking.add_argument("--run-id", type=UUID, required=True)
    networking.add_argument("--tenant-key", default="default")
    networking.add_argument("--external-network-envelope", type=Path, required=True)
    networking.add_argument("--env-file", type=Path, required=True)
    networking.add_argument("--candidate-root", type=Path, required=True)
    networking.add_argument("--rollback-root", type=Path, required=True)
    networking.add_argument("--timeout-seconds", type=int, default=180)
    networking.add_argument("--json", action="store_true")
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
        elif args.command == "record-foundation":
            register_models()
            with Session(engine) as session:
                payload = record_foundation_receipts(
                    session,
                    tenant_key=args.tenant_key,
                    run_id=args.run_id,
                )
        else:
            register_models()
            with Session(engine) as session:
                payload = record_release_networking_v2(
                    session,
                    tenant_key=args.tenant_key,
                    run_id=args.run_id,
                    external_network_envelope=args.external_network_envelope.resolve(),
                    env_file=args.env_file.resolve(),
                    candidate_root=args.candidate_root.resolve(),
                    rollback_root=args.rollback_root.resolve(),
                    timeout_seconds=args.timeout_seconds,
                )

        if getattr(args, "json", False):
            print(json.dumps(payload, sort_keys=True))
        elif args.command == "fingerprint":
            print(payload["target_environment_fingerprint"])
        elif args.command == "record-foundation":
            print(
                "Phase 22 foundation receipts recorded: "
                f"run={payload['deployment_run_id']} "
                f"status={payload['canary_evidence_status']} "
                f"satisfied={payload['canary_evidence_satisfied']}"
            )
        else:
            print(
                "Phase 22 release/networking v2 receipt recorded: "
                f"run={payload['deployment_run_id']} "
                f"status={payload['status']} "
                f"restored={payload['candidate_restored']}"
            )
        if args.command == "record-release-networking" and payload["status"] != "satisfied":
            return 1
        return 0
    except Exception as exc:
        print(f"Phase 22 target-host foundation executor failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
