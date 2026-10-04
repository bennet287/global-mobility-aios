from __future__ import annotations

import ipaddress
import json
import re
from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.models.domain import (
    ExecutiveDecision,
    OrganizationActivity,
    OrganizationActorType,
    OrganizationalWorkItem,
    now_utc,
)
from app.models.production_deployment_acceptance import (
    ProductionDeploymentAcceptanceCheckReceipt,
    ProductionDeploymentAcceptanceRun,
)
from app.schemas_production_deployment_acceptance import (
    ProductionDeploymentAcceptanceGateRead,
    ProductionDeploymentAcceptanceRunRead,
    ProductionDeploymentNetworkingContract,
)
from app.services.organization_activity import stage_activity
from app.services.organization_command import (
    AuditMutation,
    AuthorityDenied,
    DependencyConflict,
    IdempotencyConflict,
    InvalidReference,
    InvalidTransition,
    OrganizationCommandContext,
    canonical_fingerprint,
    canonical_json,
    commit_mutations,
    require_human,
    tenant_record,
)


DEPLOYMENT_ACCEPTANCE_SOURCE_TYPE = "production_deployment_acceptance_run"
DEPLOYMENT_ACCEPTANCE_ACTIVITY_TYPE = "production.deployment_acceptance.prepared.v1"
DEPLOYMENT_ACCEPTANCE_CONTRACT_KEY = "phase22.single_vps_compose.canary_acceptance"
DEPLOYMENT_ACCEPTANCE_CONTRACT_VERSION = 1
EXECUTION_MODE = "canary"
ENVIRONMENT_CLASS = "canary"
ALLOWED_PREPARER_POSITIONS = frozenset(
    {
        "platform_engineer",
        "site_reliability_engineer",
        "vp_engineering",
        "cto",
        "board",
    }
)
TERMINAL_WORK_STATUSES = frozenset({"completed", "cancelled", "failed"})
TARGET_HOST_FOUNDATION_EXECUTOR_ACTOR = "phase22-target-host-foundation"
TARGET_HOST_FOUNDATION_EXECUTOR_CONTRACT_KEY = "phase22.target-host-foundation.v1"
TARGET_HOST_FOUNDATION_EXECUTOR_CONTRACT_VERSION = 1
TARGET_HOST_FOUNDATION_STATUSES = frozenset({"blocked", "failed", "unknown"})
NETWORKING_CONTRACT_KEY = "phase22.single_vps.public_networking"
NETWORKING_CONTRACT_VERSION = 1
_NETWORKING_CONTRACT_FIELDS = frozenset(
    {
        "web_hostname",
        "api_hostname",
        "expected_public_ipv4",
        "allowed_public_tcp_ports",
        "external_verifier_public_key_fingerprint",
    }
)
_HOST_LABEL = r"(?!-)[a-z0-9-]{1,63}(?<!-)"
_PUBLIC_HOSTNAME = re.compile(rf"^(?:{_HOST_LABEL}\.)+{_HOST_LABEL}$")
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
_HEX40 = re.compile(r"^[0-9a-f]{40}$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class DeploymentAcceptanceGateSpec:
    gate_key: str
    gate_version: int
    label: str


DEPLOYMENT_ACCEPTANCE_GATES: tuple[DeploymentAcceptanceGateSpec, ...] = (
    DeploymentAcceptanceGateSpec("release_networking", 1, "Release and networking"),
    DeploymentAcceptanceGateSpec("identity_boundaries", 1, "Identity and boundaries"),
    DeploymentAcceptanceGateSpec("core_journey", 1, "Core journey"),
    DeploymentAcceptanceGateSpec("documents_integrations", 1, "Documents and integrations"),
    DeploymentAcceptanceGateSpec("failure_recovery", 1, "Failure and recovery"),
    DeploymentAcceptanceGateSpec("operations", 1, "Operations"),
)

CANARY_ENVIRONMENT_CONSTRAINTS: dict[str, Any] = {
    "environment_class": ENVIRONMENT_CLASS,
    "synthetic_data_only": True,
    "real_client_data_allowed": False,
    "external_consequential_actions_allowed": False,
    "paid_autonomous_execution_allowed": False,
    "production_traffic_allowed": False,
}


class DeploymentAcceptanceIntegrityError(InvalidTransition):
    """Stored Phase 22 deployment evidence no longer satisfies its immutable contract."""


def _required(value: str, *, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise InvalidReference(f"{field} is required")
    return normalized


def _hex(value: str, *, field: str, length: int) -> str:
    normalized = value.strip()
    matcher = _HEX40 if length == 40 else _HEX64
    if matcher.fullmatch(normalized) is None:
        raise InvalidReference(f"{field} must be {length} lowercase hexadecimal characters")
    return normalized


def _public_hostname(value: str, *, field: str) -> str:
    normalized = _required(value, field=field).lower()
    if len(normalized) > 253 or _PUBLIC_HOSTNAME.fullmatch(normalized) is None:
        raise InvalidReference(f"{field} must be a public DNS hostname without scheme, port or path")
    if normalized in _RESERVED_HOST_EXACT or any(
        normalized.endswith(suffix) for suffix in _RESERVED_HOST_SUFFIXES
    ):
        raise InvalidReference(f"{field} must not use a reserved/local hostname")
    try:
        ipaddress.ip_address(normalized)
    except ValueError:
        pass
    else:
        raise InvalidReference(f"{field} must be a DNS hostname, not an IP literal")
    return normalized


def _normalize_networking_contract(
    value: ProductionDeploymentNetworkingContract | dict[str, Any],
) -> dict[str, Any]:
    raw = value.model_dump() if isinstance(value, ProductionDeploymentNetworkingContract) else dict(value)
    if set(raw) != _NETWORKING_CONTRACT_FIELDS:
        raise InvalidReference("networking contract fields do not match the v1 contract")
    web_hostname = _public_hostname(str(raw["web_hostname"]), field="web_hostname")
    api_hostname = _public_hostname(str(raw["api_hostname"]), field="api_hostname")
    if web_hostname == api_hostname:
        raise InvalidReference("web_hostname and api_hostname must be distinct")

    address_text = _required(str(raw["expected_public_ipv4"]), field="expected_public_ipv4")
    try:
        address = ipaddress.ip_address(address_text)
    except ValueError as exc:
        raise InvalidReference("expected_public_ipv4 must be a valid IPv4 address") from exc
    if not isinstance(address, ipaddress.IPv4Address) or not address.is_global:
        raise InvalidReference("expected_public_ipv4 must be one globally routable IPv4 address")

    raw_ports = raw["allowed_public_tcp_ports"]
    if not isinstance(raw_ports, (list, tuple)):
        raise InvalidReference("allowed_public_tcp_ports must be a list")
    if any(isinstance(port, bool) or not isinstance(port, int) for port in raw_ports):
        raise InvalidReference("allowed_public_tcp_ports must contain integer TCP ports")
    ports = tuple(sorted(raw_ports))
    if len(set(ports)) != len(ports):
        raise InvalidReference("allowed_public_tcp_ports must be unique")
    if set(ports) not in ({80, 443}, {22, 80, 443}):
        raise InvalidReference("allowed_public_tcp_ports must be exactly 80/443 with optional SSH 22")

    verifier_fingerprint = _hex(
        str(raw["external_verifier_public_key_fingerprint"]),
        field="external_verifier_public_key_fingerprint",
        length=64,
    )
    normalized = {
        "web_hostname": web_hostname,
        "api_hostname": api_hostname,
        "expected_public_ipv4": str(address),
        "allowed_public_tcp_ports": list(ports),
        "external_verifier_public_key_fingerprint": verifier_fingerprint,
    }
    if len(canonical_json(normalized).encode("utf-8")) > 4096:
        raise InvalidReference("networking contract exceeds the bounded v1 size")
    return normalized


def networking_contract_fingerprint(contract: dict[str, Any]) -> str:
    return canonical_fingerprint(
        {
            "contract_key": NETWORKING_CONTRACT_KEY,
            "contract_version": NETWORKING_CONTRACT_VERSION,
            "contract": contract,
        }
    )


def _stored_networking_contract(
    run: ProductionDeploymentAcceptanceRun,
) -> dict[str, Any] | None:
    values = (
        run.networking_contract_key,
        run.networking_contract_version,
        run.networking_contract_fingerprint,
        run.networking_contract_json,
    )
    if all(value is None for value in values):
        return None
    if any(value is None for value in values):
        raise DeploymentAcceptanceIntegrityError(
            "deployment networking contract is only partially populated"
        )
    if (
        run.networking_contract_key != NETWORKING_CONTRACT_KEY
        or run.networking_contract_version != NETWORKING_CONTRACT_VERSION
    ):
        raise DeploymentAcceptanceIntegrityError("deployment networking contract identity drifted")
    try:
        parsed = json.loads(run.networking_contract_json or "")
    except (TypeError, json.JSONDecodeError) as exc:
        raise DeploymentAcceptanceIntegrityError("deployment networking contract JSON is invalid") from exc
    if not isinstance(parsed, dict):
        raise DeploymentAcceptanceIntegrityError("deployment networking contract must be a JSON object")
    try:
        normalized = _normalize_networking_contract(parsed)
    except InvalidReference as exc:
        raise DeploymentAcceptanceIntegrityError(
            "stored deployment networking contract no longer satisfies v1"
        ) from exc
    if run.networking_contract_json != canonical_json(normalized):
        raise DeploymentAcceptanceIntegrityError("deployment networking contract JSON is not canonical")
    expected = networking_contract_fingerprint(normalized)
    if run.networking_contract_fingerprint != expected:
        raise DeploymentAcceptanceIntegrityError("deployment networking contract fingerprint drifted")
    return normalized


def _gate_contract_payload() -> dict[str, Any]:
    return {
        "contract_key": DEPLOYMENT_ACCEPTANCE_CONTRACT_KEY,
        "contract_version": DEPLOYMENT_ACCEPTANCE_CONTRACT_VERSION,
        "execution_mode": EXECUTION_MODE,
        "environment_constraints": CANARY_ENVIRONMENT_CONSTRAINTS,
        "gates": [
            {
                "gate_key": gate.gate_key,
                "gate_version": gate.gate_version,
                "label": gate.label,
            }
            for gate in DEPLOYMENT_ACCEPTANCE_GATES
        ],
    }


def deployment_acceptance_contract_fingerprint() -> str:
    return canonical_fingerprint(_gate_contract_payload())


def _required_gate_keys() -> tuple[str, ...]:
    return tuple(gate.gate_key for gate in DEPLOYMENT_ACCEPTANCE_GATES)


def _run_fingerprint(
    *,
    tenant_key: str,
    deployment_run_key: str,
    environment_key: str,
    target_environment_fingerprint: str,
    release_commit_sha: str,
    release_configuration_fingerprint: str,
    rollback_release_commit_sha: str,
    rollback_configuration_fingerprint: str,
    work_item_id: UUID,
    admission_decision_id: UUID,
    reason: str,
    networking_contract_key: str | None = None,
    networking_contract_version: int | None = None,
    networking_contract_fingerprint_value: str | None = None,
    networking_contract: dict[str, Any] | None = None,
) -> str:
    payload: dict[str, Any] = {
        "tenant_key": tenant_key,
        "deployment_run_key": deployment_run_key,
        "execution_mode": EXECUTION_MODE,
        "environment_key": environment_key,
        "environment_class": ENVIRONMENT_CLASS,
        "target_environment_fingerprint": target_environment_fingerprint,
        "environment_constraints": CANARY_ENVIRONMENT_CONSTRAINTS,
        "release_commit_sha": release_commit_sha,
        "release_configuration_fingerprint": release_configuration_fingerprint,
        "rollback_release_commit_sha": rollback_release_commit_sha,
        "rollback_configuration_fingerprint": rollback_configuration_fingerprint,
        "acceptance_contract": _gate_contract_payload(),
        "work_item_id": str(work_item_id),
        "admission_decision_id": str(admission_decision_id),
        "reason": reason,
    }
    if networking_contract is not None:
        payload["networking_contract"] = {
            "contract_key": networking_contract_key,
            "contract_version": networking_contract_version,
            "contract_fingerprint": networking_contract_fingerprint_value,
            "contract": networking_contract,
        }
    return canonical_fingerprint(payload)


def deployment_acceptance_receipt_fingerprint(
    *,
    tenant_key: str,
    deployment_run_id: UUID,
    gate_key: str,
    gate_version: int,
    status: str,
    observed_target_environment_fingerprint: str,
    observed_release_commit_sha: str,
    observed_release_configuration_fingerprint: str,
    executor_contract_key: str,
    executor_contract_version: int,
    executor_identity_fingerprint: str,
    evidence_digest: str,
    evidence_reference: str,
    redacted_details: dict[str, Any],
    observed_at: Any,
    created_by: str,
) -> str:
    return canonical_fingerprint(
        {
            "tenant_key": tenant_key,
            "deployment_run_id": str(deployment_run_id),
            "gate_key": gate_key,
            "gate_version": gate_version,
            "status": status,
            "observed_target_environment_fingerprint": observed_target_environment_fingerprint,
            "observed_release_commit_sha": observed_release_commit_sha,
            "observed_release_configuration_fingerprint": observed_release_configuration_fingerprint,
            "executor_contract_key": executor_contract_key,
            "executor_contract_version": executor_contract_version,
            "executor_identity_fingerprint": executor_identity_fingerprint,
            "evidence_digest": evidence_digest,
            "evidence_reference": evidence_reference,
            "redacted_details": redacted_details,
            "observed_at": observed_at,
            "created_by": created_by,
        }
    )


def _prepared_activity_payload(
    *,
    run_id: UUID,
    deployment_run_key: str,
    environment_key: str,
    target_environment_fingerprint: str,
    release_commit_sha: str,
    release_configuration_fingerprint: str,
    rollback_release_commit_sha: str,
    rollback_configuration_fingerprint: str,
    work_item_id: UUID,
    admission_decision_id: UUID,
    reason: str,
    record_fingerprint: str,
    networking_contract_key: str | None = None,
    networking_contract_version: int | None = None,
    networking_contract_fingerprint_value: str | None = None,
    networking_contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "deployment_run_id": str(run_id),
        "deployment_run_key": deployment_run_key,
        "execution_mode": EXECUTION_MODE,
        "environment_key": environment_key,
        "environment_class": ENVIRONMENT_CLASS,
        "target_environment_fingerprint": target_environment_fingerprint,
        "environment_constraints": CANARY_ENVIRONMENT_CONSTRAINTS,
        "release_commit_sha": release_commit_sha,
        "release_configuration_fingerprint": release_configuration_fingerprint,
        "rollback_release_commit_sha": rollback_release_commit_sha,
        "rollback_configuration_fingerprint": rollback_configuration_fingerprint,
        "acceptance_contract_key": DEPLOYMENT_ACCEPTANCE_CONTRACT_KEY,
        "acceptance_contract_version": DEPLOYMENT_ACCEPTANCE_CONTRACT_VERSION,
        "acceptance_contract_fingerprint": deployment_acceptance_contract_fingerprint(),
        "required_gate_keys": list(_required_gate_keys()),
        "work_item_id": str(work_item_id),
        "admission_decision_id": str(admission_decision_id),
        "reason": reason,
        "record_fingerprint": record_fingerprint,
        "deployment_observed": False,
        "acceptance_evidence_recorded": False,
        "authority_mutated": False,
        "promotion_authorized": False,
        "production_ready": False,
    }
    if networking_contract is not None:
        payload["networking_contract"] = {
            "contract_key": networking_contract_key,
            "contract_version": networking_contract_version,
            "contract_fingerprint": networking_contract_fingerprint_value,
            "contract": networking_contract,
        }
    return payload


def _validate_authority_lineage(
    session: Session,
    context: OrganizationCommandContext,
    *,
    work_item_id: UUID,
    admission_decision_id: UUID,
) -> tuple[OrganizationalWorkItem, ExecutiveDecision]:
    require_human(context)
    if context.position_key not in ALLOWED_PREPARER_POSITIONS:
        raise AuthorityDenied("current organization position is not a deployment-preparation owner")

    work = tenant_record(
        session,
        OrganizationalWorkItem,
        work_item_id,
        context.tenant_key,
        label="deployment work item",
    )
    if work.assigned_position_key != context.position_key:
        raise AuthorityDenied("deployment run must be prepared by the WorkItem's assigned position")
    if work.status in TERMINAL_WORK_STATUSES:
        raise InvalidTransition("terminal WorkItem cannot prepare a deployment acceptance run")

    decision = tenant_record(
        session,
        ExecutiveDecision,
        admission_decision_id,
        context.tenant_key,
        label="deployment admission decision",
    )
    if decision.work_item_id != work.id:
        raise InvalidReference("deployment admission decision does not belong to the WorkItem")
    if decision.status != "approved":
        raise InvalidTransition("deployment acceptance preparation requires an approved decision")
    if decision.authority_level != work.authority_level:
        raise InvalidReference("deployment admission decision authority does not match the WorkItem")
    work_source = (work.source_object_type, work.source_object_id, work.source_object_version)
    decision_source = (
        decision.source_object_type,
        decision.source_object_id,
        decision.source_object_version,
    )
    if decision_source != work_source:
        raise InvalidReference("deployment admission decision source lineage does not match the WorkItem")
    if decision.expires_at is not None and decision.expires_at <= now_utc():
        raise InvalidTransition("deployment admission decision has expired")
    superseding = session.exec(
        select(ExecutiveDecision).where(
            ExecutiveDecision.tenant_key == context.tenant_key,
            ExecutiveDecision.supersedes_decision_id == decision.id,
        )
    ).first()
    if superseding is not None:
        raise InvalidTransition("deployment admission decision has been superseded")
    return work, decision


def _json_object(value: str, *, field: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError) as exc:
        raise DeploymentAcceptanceIntegrityError(f"{field} JSON is invalid") from exc
    if not isinstance(parsed, dict):
        raise DeploymentAcceptanceIntegrityError(f"{field} must be a JSON object")
    return parsed


def _json_list(value: str, *, field: str) -> list[Any]:
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError) as exc:
        raise DeploymentAcceptanceIntegrityError(f"{field} JSON is invalid") from exc
    if not isinstance(parsed, list):
        raise DeploymentAcceptanceIntegrityError(f"{field} must be a JSON list")
    return parsed


def _validate_run_integrity(
    session: Session,
    context: OrganizationCommandContext,
    run: ProductionDeploymentAcceptanceRun,
) -> None:
    if run.tenant_key != context.tenant_key:
        raise InvalidReference("deployment acceptance run tenant does not match command context")
    if (
        run.execution_mode != EXECUTION_MODE
        or run.environment_class != ENVIRONMENT_CLASS
        or run.acceptance_contract_key != DEPLOYMENT_ACCEPTANCE_CONTRACT_KEY
        or run.acceptance_contract_version != DEPLOYMENT_ACCEPTANCE_CONTRACT_VERSION
        or run.acceptance_contract_fingerprint != deployment_acceptance_contract_fingerprint()
    ):
        raise DeploymentAcceptanceIntegrityError("deployment acceptance contract identity drifted")
    if _json_object(run.environment_constraints_json, field="environment constraints") != CANARY_ENVIRONMENT_CONSTRAINTS:
        raise DeploymentAcceptanceIntegrityError("deployment environment constraints drifted")
    if _json_list(run.required_gate_keys_json, field="required gate keys") != list(_required_gate_keys()):
        raise DeploymentAcceptanceIntegrityError("deployment acceptance gate set drifted")

    networking_contract = _stored_networking_contract(run)
    expected_record = _run_fingerprint(
        tenant_key=run.tenant_key,
        deployment_run_key=run.deployment_run_key,
        environment_key=run.environment_key,
        target_environment_fingerprint=run.target_environment_fingerprint,
        release_commit_sha=run.release_commit_sha,
        release_configuration_fingerprint=run.release_configuration_fingerprint,
        rollback_release_commit_sha=run.rollback_release_commit_sha,
        rollback_configuration_fingerprint=run.rollback_configuration_fingerprint,
        work_item_id=run.work_item_id,
        admission_decision_id=run.admission_decision_id,
        reason=run.reason,
        networking_contract_key=run.networking_contract_key,
        networking_contract_version=run.networking_contract_version,
        networking_contract_fingerprint_value=run.networking_contract_fingerprint,
        networking_contract=networking_contract,
    )
    if run.record_fingerprint != expected_record:
        raise DeploymentAcceptanceIntegrityError("deployment acceptance run fingerprint drifted")

    activity = session.exec(
        select(OrganizationActivity).where(
            OrganizationActivity.tenant_key == run.tenant_key,
            OrganizationActivity.id == run.prepared_activity_id,
        )
    ).first()
    if activity is None:
        raise DeploymentAcceptanceIntegrityError("deployment preparation Activity is missing")
    if activity.record_fingerprint != run.prepared_activity_fingerprint:
        raise DeploymentAcceptanceIntegrityError("deployment preparation Activity fingerprint drifted")
    if (
        str(getattr(activity.activity_class, "value", activity.activity_class)) != "operational"
        or activity.activity_type != DEPLOYMENT_ACCEPTANCE_ACTIVITY_TYPE
        or activity.source_object_type != DEPLOYMENT_ACCEPTANCE_SOURCE_TYPE
        or activity.source_object_id != str(run.id)
        or activity.source_object_version != run.release_commit_sha
        or activity.work_item_id != run.work_item_id
    ):
        raise DeploymentAcceptanceIntegrityError("deployment preparation Activity lineage drifted")
    try:
        payload = json.loads(activity.payload_json or "{}")
    except (TypeError, json.JSONDecodeError) as exc:
        raise DeploymentAcceptanceIntegrityError("deployment preparation Activity payload is invalid") from exc
    expected_payload = _prepared_activity_payload(
        run_id=run.id,
        deployment_run_key=run.deployment_run_key,
        environment_key=run.environment_key,
        target_environment_fingerprint=run.target_environment_fingerprint,
        release_commit_sha=run.release_commit_sha,
        release_configuration_fingerprint=run.release_configuration_fingerprint,
        rollback_release_commit_sha=run.rollback_release_commit_sha,
        rollback_configuration_fingerprint=run.rollback_configuration_fingerprint,
        work_item_id=run.work_item_id,
        admission_decision_id=run.admission_decision_id,
        reason=run.reason,
        record_fingerprint=run.record_fingerprint,
        networking_contract_key=run.networking_contract_key,
        networking_contract_version=run.networking_contract_version,
        networking_contract_fingerprint_value=run.networking_contract_fingerprint,
        networking_contract=networking_contract,
    )
    if payload != expected_payload:
        raise DeploymentAcceptanceIntegrityError("deployment preparation Activity payload drifted")


def validated_deployment_networking_contract(
    session: Session,
    context: OrganizationCommandContext,
    *,
    deployment_run_id: UUID,
) -> tuple[ProductionDeploymentAcceptanceRun, dict[str, Any]]:
    """Resolve an integrity-checked prepared run and its immutable networking contract."""

    run = tenant_record(
        session,
        ProductionDeploymentAcceptanceRun,
        deployment_run_id,
        context.tenant_key,
        label="deployment acceptance run",
    )
    _validate_run_integrity(session, context, run)
    networking_contract = _stored_networking_contract(run)
    if networking_contract is None:
        raise InvalidTransition(
            "external network verification requires a prepared networking contract"
        )
    return run, networking_contract


def _receipt_map(
    session: Session,
    run: ProductionDeploymentAcceptanceRun,
) -> dict[str, ProductionDeploymentAcceptanceCheckReceipt]:
    receipts = session.exec(
        select(ProductionDeploymentAcceptanceCheckReceipt).where(
            ProductionDeploymentAcceptanceCheckReceipt.tenant_key == run.tenant_key,
            ProductionDeploymentAcceptanceCheckReceipt.deployment_run_id == run.id,
        )
    ).all()
    supported = {gate.gate_key: gate for gate in DEPLOYMENT_ACCEPTANCE_GATES}
    result: dict[str, ProductionDeploymentAcceptanceCheckReceipt] = {}
    for receipt in receipts:
        gate = supported.get(receipt.gate_key)
        if gate is None or receipt.gate_version != gate.gate_version:
            raise DeploymentAcceptanceIntegrityError("deployment receipt references an unsupported gate")
        if receipt.gate_key in result:
            raise DeploymentAcceptanceIntegrityError("deployment receipt gate is duplicated")
        if (
            receipt.observed_target_environment_fingerprint != run.target_environment_fingerprint
            or receipt.observed_release_commit_sha != run.release_commit_sha
            or receipt.observed_release_configuration_fingerprint != run.release_configuration_fingerprint
        ):
            raise DeploymentAcceptanceIntegrityError("deployment receipt observed identity does not match the prepared run")
        try:
            details = json.loads(receipt.redacted_details_json or "{}")
        except (TypeError, json.JSONDecodeError) as exc:
            raise DeploymentAcceptanceIntegrityError("deployment receipt details JSON is invalid") from exc
        if not isinstance(details, dict):
            raise DeploymentAcceptanceIntegrityError("deployment receipt details must be a JSON object")
        expected = deployment_acceptance_receipt_fingerprint(
            tenant_key=receipt.tenant_key,
            deployment_run_id=receipt.deployment_run_id,
            gate_key=receipt.gate_key,
            gate_version=receipt.gate_version,
            status=receipt.status,
            observed_target_environment_fingerprint=receipt.observed_target_environment_fingerprint,
            observed_release_commit_sha=receipt.observed_release_commit_sha,
            observed_release_configuration_fingerprint=receipt.observed_release_configuration_fingerprint,
            executor_contract_key=receipt.executor_contract_key,
            executor_contract_version=receipt.executor_contract_version,
            executor_identity_fingerprint=receipt.executor_identity_fingerprint,
            evidence_digest=receipt.evidence_digest,
            evidence_reference=receipt.evidence_reference,
            redacted_details=details,
            observed_at=receipt.observed_at,
            created_by=receipt.created_by,
        )
        if receipt.record_fingerprint != expected:
            raise DeploymentAcceptanceIntegrityError("deployment receipt fingerprint drifted")
        result[receipt.gate_key] = receipt
    return result


def _evidence_status(statuses: list[str]) -> str:
    if all(status == "satisfied" for status in statuses):
        return "satisfied"
    if "failed" in statuses:
        return "failed"
    if "blocked" in statuses:
        return "blocked"
    if all(status == "absent" for status in statuses):
        return "absent"
    if "absent" in statuses:
        return "partial"
    if "unknown" in statuses:
        return "unknown"
    return "partial"


def project_deployment_acceptance_run(
    session: Session,
    context: OrganizationCommandContext,
    run: ProductionDeploymentAcceptanceRun,
) -> ProductionDeploymentAcceptanceRunRead:
    require_human(context)
    _validate_run_integrity(session, context, run)
    networking_contract = _stored_networking_contract(run)
    receipts = _receipt_map(session, run)
    gate_reads: list[ProductionDeploymentAcceptanceGateRead] = []
    statuses: list[str] = []
    for gate in DEPLOYMENT_ACCEPTANCE_GATES:
        receipt = receipts.get(gate.gate_key)
        if receipt is None:
            status = "absent"
            gate_reads.append(
                ProductionDeploymentAcceptanceGateRead(
                    gate_key=gate.gate_key,
                    gate_version=gate.gate_version,
                    label=gate.label,
                    status=status,
                    receipt_id=None,
                    evidence_digest=None,
                    evidence_reference=None,
                    redacted_details={},
                    observed_at=None,
                )
            )
        else:
            status = receipt.status
            gate_reads.append(
                ProductionDeploymentAcceptanceGateRead(
                    gate_key=gate.gate_key,
                    gate_version=gate.gate_version,
                    label=gate.label,
                    status=status,
                    receipt_id=receipt.id,
                    evidence_digest=receipt.evidence_digest,
                    evidence_reference=receipt.evidence_reference,
                    redacted_details=json.loads(receipt.redacted_details_json or "{}"),
                    observed_at=receipt.observed_at,
                )
            )
        statuses.append(status)

    aggregate = _evidence_status(statuses)
    return ProductionDeploymentAcceptanceRunRead(
        id=run.id,
        tenant_key=run.tenant_key,
        deployment_run_key=run.deployment_run_key,
        execution_mode=EXECUTION_MODE,
        environment_key=run.environment_key,
        environment_class=ENVIRONMENT_CLASS,
        target_environment_fingerprint=run.target_environment_fingerprint,
        environment_constraints=_json_object(run.environment_constraints_json, field="environment constraints"),
        release_commit_sha=run.release_commit_sha,
        release_configuration_fingerprint=run.release_configuration_fingerprint,
        rollback_release_commit_sha=run.rollback_release_commit_sha,
        rollback_configuration_fingerprint=run.rollback_configuration_fingerprint,
        acceptance_contract_key=run.acceptance_contract_key,
        acceptance_contract_version=run.acceptance_contract_version,
        acceptance_contract_fingerprint=run.acceptance_contract_fingerprint,
        networking_contract_key=run.networking_contract_key,
        networking_contract_version=run.networking_contract_version,
        networking_contract_fingerprint=run.networking_contract_fingerprint,
        networking_contract=networking_contract,
        work_item_id=run.work_item_id,
        admission_decision_id=run.admission_decision_id,
        reason=run.reason,
        record_fingerprint=run.record_fingerprint,
        prepared_activity_id=run.prepared_activity_id,
        prepared_activity_fingerprint=run.prepared_activity_fingerprint,
        created_by=run.created_by,
        created_at=run.created_at,
        gates=tuple(gate_reads),
        deployment_observed=bool(receipts),
        checks_complete=all(status != "absent" for status in statuses),
        canary_evidence_status=aggregate,
        canary_evidence_satisfied=aggregate == "satisfied",
    )


def target_host_foundation_executor_identity_fingerprint(
    release_commit_sha: str,
) -> str:
    release_commit_sha = _hex(
        release_commit_sha,
        field="release_commit_sha",
        length=40,
    )
    return canonical_fingerprint(
        {
            "executor_contract_key": TARGET_HOST_FOUNDATION_EXECUTOR_CONTRACT_KEY,
            "executor_contract_version": TARGET_HOST_FOUNDATION_EXECUTOR_CONTRACT_VERSION,
            "release_commit_sha": release_commit_sha,
        }
    )


def _require_target_host_foundation_executor(
    context: OrganizationCommandContext,
) -> None:
    if (
        context.actor_type is not OrganizationActorType.system
        or context.actor_id != TARGET_HOST_FOUNDATION_EXECUTOR_ACTOR
        or context.authenticated_user_id != "system"
        or context.role != "operator"
    ):
        raise AuthorityDenied(
            "deployment acceptance receipt writes are reserved for the canonical target-host executor"
        )


def _target_host_foundation_receipt_semantics(
    *,
    run: ProductionDeploymentAcceptanceRun,
    gate: DeploymentAcceptanceGateSpec,
    status: str,
    observed_target_environment_fingerprint: str,
    observed_release_commit_sha: str,
    observed_release_configuration_fingerprint: str,
    redacted_details: dict[str, Any],
) -> dict[str, Any]:
    base = {
        "deployment_run_id": str(run.id),
        "gate_key": gate.gate_key,
        "gate_version": gate.gate_version,
        "status": status,
        "observed_target_environment_fingerprint": observed_target_environment_fingerprint,
        "observed_release_commit_sha": observed_release_commit_sha,
        "observed_release_configuration_fingerprint": observed_release_configuration_fingerprint,
        "executor_contract_key": TARGET_HOST_FOUNDATION_EXECUTOR_CONTRACT_KEY,
        "executor_contract_version": TARGET_HOST_FOUNDATION_EXECUTOR_CONTRACT_VERSION,
        "executor_identity_fingerprint": target_host_foundation_executor_identity_fingerprint(
            run.release_commit_sha
        ),
        "redacted_details": redacted_details,
    }
    return {
        **base,
        "evidence_digest": canonical_fingerprint(
            {
                **base,
                "evidence_contract": "phase22.target-host-foundation.evidence.v1",
            }
        ),
        "evidence_reference": (
            f"phase22-target-host-foundation://{run.id}/{gate.gate_key}"
        ),
        "created_by": TARGET_HOST_FOUNDATION_EXECUTOR_ACTOR,
    }


def _receipt_matches_foundation_semantics(
    receipt: ProductionDeploymentAcceptanceCheckReceipt,
    *,
    semantics: dict[str, Any],
) -> bool:
    try:
        stored_details = json.loads(receipt.redacted_details_json or "{}")
    except (TypeError, json.JSONDecodeError):
        return False
    return (
        receipt.gate_key == semantics["gate_key"]
        and receipt.gate_version == semantics["gate_version"]
        and receipt.status == semantics["status"]
        and receipt.observed_target_environment_fingerprint
        == semantics["observed_target_environment_fingerprint"]
        and receipt.observed_release_commit_sha
        == semantics["observed_release_commit_sha"]
        and receipt.observed_release_configuration_fingerprint
        == semantics["observed_release_configuration_fingerprint"]
        and receipt.executor_contract_key == semantics["executor_contract_key"]
        and receipt.executor_contract_version == semantics["executor_contract_version"]
        and receipt.executor_identity_fingerprint == semantics["executor_identity_fingerprint"]
        and receipt.evidence_digest == semantics["evidence_digest"]
        and receipt.evidence_reference == semantics["evidence_reference"]
        and receipt.created_by == semantics["created_by"]
        and stored_details == semantics["redacted_details"]
    )


def record_target_host_foundation_receipt(
    session: Session,
    context: OrganizationCommandContext,
    *,
    deployment_run_id: UUID,
    gate_key: str,
    status: str,
    observed_target_environment_fingerprint: str,
    observed_release_commit_sha: str,
    observed_release_configuration_fingerprint: str,
    redacted_details: dict[str, Any],
) -> ProductionDeploymentAcceptanceCheckReceipt:
    """Persist fail-closed target-host evidence without any path to a satisfied gate."""

    _require_target_host_foundation_executor(context)
    run = tenant_record(
        session,
        ProductionDeploymentAcceptanceRun,
        deployment_run_id,
        context.tenant_key,
        label="deployment acceptance run",
    )
    _validate_run_integrity(session, context, run)

    supported = {gate.gate_key: gate for gate in DEPLOYMENT_ACCEPTANCE_GATES}
    gate = supported.get(gate_key)
    if gate is None:
        raise InvalidReference("target-host receipt references an unsupported gate")
    if status not in TARGET_HOST_FOUNDATION_STATUSES:
        raise InvalidReference(
            "target-host foundation executor cannot record a satisfied acceptance gate"
        )
    if not isinstance(redacted_details, dict):
        raise InvalidReference("target-host receipt details must be a JSON object")
    details_json = canonical_json(redacted_details)
    if len(details_json.encode("utf-8")) > 16_384:
        raise InvalidReference("target-host receipt details exceed the bounded evidence size")

    observed_target_environment_fingerprint = _hex(
        observed_target_environment_fingerprint,
        field="observed_target_environment_fingerprint",
        length=64,
    )
    observed_release_commit_sha = _hex(
        observed_release_commit_sha,
        field="observed_release_commit_sha",
        length=40,
    )
    observed_release_configuration_fingerprint = _hex(
        observed_release_configuration_fingerprint,
        field="observed_release_configuration_fingerprint",
        length=64,
    )
    if (
        observed_target_environment_fingerprint != run.target_environment_fingerprint
        or observed_release_commit_sha != run.release_commit_sha
        or observed_release_configuration_fingerprint
        != run.release_configuration_fingerprint
    ):
        raise InvalidReference(
            "target-host foundation executor observed an identity that does not match the prepared run"
        )

    semantics = _target_host_foundation_receipt_semantics(
        run=run,
        gate=gate,
        status=status,
        observed_target_environment_fingerprint=observed_target_environment_fingerprint,
        observed_release_commit_sha=observed_release_commit_sha,
        observed_release_configuration_fingerprint=observed_release_configuration_fingerprint,
        redacted_details=redacted_details,
    )
    existing = session.exec(
        select(ProductionDeploymentAcceptanceCheckReceipt).where(
            ProductionDeploymentAcceptanceCheckReceipt.tenant_key == context.tenant_key,
            ProductionDeploymentAcceptanceCheckReceipt.deployment_run_id == run.id,
            ProductionDeploymentAcceptanceCheckReceipt.gate_key == gate.gate_key,
        )
    ).first()
    if existing is not None:
        if not _receipt_matches_foundation_semantics(existing, semantics=semantics):
            raise IdempotencyConflict(
                "deployment acceptance gate already has immutable evidence with different semantics"
            )
        _receipt_map(session, run)
        return existing

    # The persisted DateTime contract is timezone-naive across the supported
    # SQLite/PostgreSQL schemas. Normalize the UTC instant before fingerprinting so
    # the immutable receipt fingerprint survives a database round-trip.
    observed_at = now_utc().replace(tzinfo=None)
    receipt = ProductionDeploymentAcceptanceCheckReceipt(
        tenant_key=context.tenant_key,
        deployment_run_id=run.id,
        gate_key=gate.gate_key,
        gate_version=gate.gate_version,
        status=status,
        observed_target_environment_fingerprint=observed_target_environment_fingerprint,
        observed_release_commit_sha=observed_release_commit_sha,
        observed_release_configuration_fingerprint=observed_release_configuration_fingerprint,
        executor_contract_key=TARGET_HOST_FOUNDATION_EXECUTOR_CONTRACT_KEY,
        executor_contract_version=TARGET_HOST_FOUNDATION_EXECUTOR_CONTRACT_VERSION,
        executor_identity_fingerprint=semantics["executor_identity_fingerprint"],
        evidence_digest=semantics["evidence_digest"],
        evidence_reference=semantics["evidence_reference"],
        redacted_details_json=details_json,
        observed_at=observed_at,
        record_fingerprint="0" * 64,
        created_by=TARGET_HOST_FOUNDATION_EXECUTOR_ACTOR,
        created_at=observed_at,
    )
    receipt.record_fingerprint = deployment_acceptance_receipt_fingerprint(
        tenant_key=receipt.tenant_key,
        deployment_run_id=receipt.deployment_run_id,
        gate_key=receipt.gate_key,
        gate_version=receipt.gate_version,
        status=receipt.status,
        observed_target_environment_fingerprint=receipt.observed_target_environment_fingerprint,
        observed_release_commit_sha=receipt.observed_release_commit_sha,
        observed_release_configuration_fingerprint=receipt.observed_release_configuration_fingerprint,
        executor_contract_key=receipt.executor_contract_key,
        executor_contract_version=receipt.executor_contract_version,
        executor_identity_fingerprint=receipt.executor_identity_fingerprint,
        evidence_digest=receipt.evidence_digest,
        evidence_reference=receipt.evidence_reference,
        redacted_details=redacted_details,
        observed_at=receipt.observed_at,
        created_by=receipt.created_by,
    )
    session.add(receipt)
    try:
        commit_mutations(
            session,
            mutations=(
                AuditMutation(
                    action="production.deployment_acceptance.receipt.foundation",
                    entity_type="production_deployment_acceptance_check_receipt",
                    entity_id=receipt.id,
                    after_state=receipt,
                    reason=(
                        "Recorded fail-closed Phase 22 target-host evidence. "
                        "Foundation v1 cannot satisfy any acceptance gate."
                    ),
                ),
            ),
            context=context,
            refresh=(receipt,),
        )
    except IntegrityError as exc:
        session.rollback()
        concurrent = session.exec(
            select(ProductionDeploymentAcceptanceCheckReceipt).where(
                ProductionDeploymentAcceptanceCheckReceipt.tenant_key == context.tenant_key,
                ProductionDeploymentAcceptanceCheckReceipt.deployment_run_id == run.id,
                ProductionDeploymentAcceptanceCheckReceipt.gate_key == gate.gate_key,
            )
        ).first()
        if concurrent is not None and _receipt_matches_foundation_semantics(
            concurrent,
            semantics=semantics,
        ):
            _receipt_map(session, run)
            return concurrent
        raise DependencyConflict(
            "deployment acceptance receipt changed concurrently"
        ) from exc
    return receipt


def prepare_deployment_acceptance_run(
    session: Session,
    context: OrganizationCommandContext,
    *,
    deployment_run_key: str,
    environment_key: str,
    target_environment_fingerprint: str,
    release_commit_sha: str,
    release_configuration_fingerprint: str,
    rollback_release_commit_sha: str,
    rollback_configuration_fingerprint: str,
    networking_contract: ProductionDeploymentNetworkingContract | dict[str, Any],
    work_item_id: UUID,
    admission_decision_id: UUID,
    reason: str,
) -> ProductionDeploymentAcceptanceRun:
    """Prepare exact deployment identity without asserting that deployment occurred."""

    deployment_run_key = _required(deployment_run_key, field="deployment_run_key")
    environment_key = _required(environment_key, field="environment_key")
    target_environment_fingerprint = _hex(
        target_environment_fingerprint,
        field="target_environment_fingerprint",
        length=64,
    )
    release_commit_sha = _hex(release_commit_sha, field="release_commit_sha", length=40)
    release_configuration_fingerprint = _hex(
        release_configuration_fingerprint,
        field="release_configuration_fingerprint",
        length=64,
    )
    rollback_release_commit_sha = _hex(
        rollback_release_commit_sha,
        field="rollback_release_commit_sha",
        length=40,
    )
    rollback_configuration_fingerprint = _hex(
        rollback_configuration_fingerprint,
        field="rollback_configuration_fingerprint",
        length=64,
    )
    networking_contract = _normalize_networking_contract(networking_contract)
    networking_fingerprint = networking_contract_fingerprint(networking_contract)
    reason = _required(reason, field="reason")
    if release_commit_sha == rollback_release_commit_sha:
        raise InvalidReference("rollback release must differ from the candidate release")

    work, decision = _validate_authority_lineage(
        session,
        context,
        work_item_id=work_item_id,
        admission_decision_id=admission_decision_id,
    )
    fingerprint = _run_fingerprint(
        tenant_key=context.tenant_key,
        deployment_run_key=deployment_run_key,
        environment_key=environment_key,
        target_environment_fingerprint=target_environment_fingerprint,
        release_commit_sha=release_commit_sha,
        release_configuration_fingerprint=release_configuration_fingerprint,
        rollback_release_commit_sha=rollback_release_commit_sha,
        rollback_configuration_fingerprint=rollback_configuration_fingerprint,
        work_item_id=work.id,
        admission_decision_id=decision.id,
        reason=reason,
        networking_contract_key=NETWORKING_CONTRACT_KEY,
        networking_contract_version=NETWORKING_CONTRACT_VERSION,
        networking_contract_fingerprint_value=networking_fingerprint,
        networking_contract=networking_contract,
    )
    existing = session.exec(
        select(ProductionDeploymentAcceptanceRun).where(
            ProductionDeploymentAcceptanceRun.tenant_key == context.tenant_key,
            ProductionDeploymentAcceptanceRun.deployment_run_key == deployment_run_key,
        )
    ).first()
    if existing is not None:
        if existing.record_fingerprint != fingerprint:
            raise IdempotencyConflict("deployment run key was already used with different semantics")
        _validate_run_integrity(session, context, existing)
        return existing

    run_id = uuid4()
    occurred_at = now_utc()
    activity = stage_activity(
        session,
        context,
        activity_key=f"production-deployment-acceptance:{run_id}:prepared",
        stream_key=f"production-deployment-acceptance:{environment_key}",
        activity_class="operational",
        activity_type=DEPLOYMENT_ACCEPTANCE_ACTIVITY_TYPE,
        title="Deployment acceptance run prepared",
        summary=(
            "Prepared an exact canary release/environment/rollback identity and acceptance contract; "
            "no deployment or target-host acceptance is asserted."
        ),
        source_object_type=DEPLOYMENT_ACCEPTANCE_SOURCE_TYPE,
        source_object_id=str(run_id),
        source_object_version=release_commit_sha,
        work_item_id=work.id,
        occurred_at=occurred_at,
        payload=_prepared_activity_payload(
            run_id=run_id,
            deployment_run_key=deployment_run_key,
            environment_key=environment_key,
            target_environment_fingerprint=target_environment_fingerprint,
            release_commit_sha=release_commit_sha,
            release_configuration_fingerprint=release_configuration_fingerprint,
            rollback_release_commit_sha=rollback_release_commit_sha,
            rollback_configuration_fingerprint=rollback_configuration_fingerprint,
            work_item_id=work.id,
            admission_decision_id=decision.id,
            reason=reason,
            record_fingerprint=fingerprint,
            networking_contract_key=NETWORKING_CONTRACT_KEY,
            networking_contract_version=NETWORKING_CONTRACT_VERSION,
            networking_contract_fingerprint_value=networking_fingerprint,
            networking_contract=networking_contract,
        ),
    )
    run = ProductionDeploymentAcceptanceRun(
        id=run_id,
        tenant_key=context.tenant_key,
        deployment_run_key=deployment_run_key,
        execution_mode=EXECUTION_MODE,
        environment_key=environment_key,
        environment_class=ENVIRONMENT_CLASS,
        target_environment_fingerprint=target_environment_fingerprint,
        environment_constraints_json=canonical_json(CANARY_ENVIRONMENT_CONSTRAINTS),
        release_commit_sha=release_commit_sha,
        release_configuration_fingerprint=release_configuration_fingerprint,
        rollback_release_commit_sha=rollback_release_commit_sha,
        rollback_configuration_fingerprint=rollback_configuration_fingerprint,
        acceptance_contract_key=DEPLOYMENT_ACCEPTANCE_CONTRACT_KEY,
        acceptance_contract_version=DEPLOYMENT_ACCEPTANCE_CONTRACT_VERSION,
        acceptance_contract_fingerprint=deployment_acceptance_contract_fingerprint(),
        required_gate_keys_json=canonical_json(list(_required_gate_keys())),
        networking_contract_key=NETWORKING_CONTRACT_KEY,
        networking_contract_version=NETWORKING_CONTRACT_VERSION,
        networking_contract_fingerprint=networking_fingerprint,
        networking_contract_json=canonical_json(networking_contract),
        work_item_id=work.id,
        admission_decision_id=decision.id,
        reason=reason,
        record_fingerprint=fingerprint,
        prepared_activity_id=activity.id,
        prepared_activity_fingerprint=activity.record_fingerprint,
        created_by=context.actor_id,
        created_at=occurred_at,
    )
    session.add(run)
    try:
        commit_mutations(
            session,
            mutations=(
                AuditMutation(
                    action="production.deployment_acceptance.prepare",
                    entity_type=DEPLOYMENT_ACCEPTANCE_SOURCE_TYPE,
                    entity_id=run.id,
                    after_state=run,
                    reason=(
                        "Prepared Phase 22 canary acceptance identity only; no deployment, "
                        "acceptance, promotion or production-readiness claim was created."
                    ),
                ),
            ),
            context=context,
            refresh=(run,),
        )
    except IntegrityError as exc:
        session.rollback()
        concurrent = session.exec(
            select(ProductionDeploymentAcceptanceRun).where(
                ProductionDeploymentAcceptanceRun.tenant_key == context.tenant_key,
                ProductionDeploymentAcceptanceRun.deployment_run_key == deployment_run_key,
            )
        ).first()
        if concurrent is not None and concurrent.record_fingerprint == fingerprint:
            _validate_run_integrity(session, context, concurrent)
            return concurrent
        raise DependencyConflict("deployment acceptance run changed concurrently") from exc
    return run
