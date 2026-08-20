from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import OrganizationPosition, OrganizationalWorkItem, now_utc
from app.services.organization_command import (
    canonical_fingerprint,
    canonical_json,
    tenant_record,
)


CONTEXT_BUNDLE_SCHEMA_VERSION = "context-bundle.v1"


class ContextBrokerError(RuntimeError):
    """Base error for purpose-scoped organization context assembly."""


class ContextIdentityUnavailable(ContextBrokerError):
    """The requested organizational identity is not active and usable."""


class ContextScopeDenied(ContextBrokerError):
    """The requested employee/work binding is outside the bounded context scope."""


class ContextIntegrityError(ContextBrokerError):
    """Canonical context inputs are malformed or internally inconsistent."""


class ContextPurpose(str, Enum):
    WORK_EXECUTION = "work_execution"
    COLLABORATION = "collaboration"
    REVIEW = "review"
    RESEARCH = "research"


@dataclass(frozen=True)
class ContextReference:
    kind: str
    identifier: str
    version: str | None = None


@dataclass(frozen=True)
class PositionContext:
    position_key: str
    title: str
    department: str
    reports_to_position_key: str | None
    authority_level: str
    role_card_name: str | None
    position_version: int
    contract_json: str


@dataclass(frozen=True)
class WorkItemContext:
    work_item_id: UUID
    title: str
    objective: str
    department: str
    authority_level: str
    assigned_position_key: str
    status: str
    priority: str
    risk_level: str
    is_emergency: bool
    objective_key: str | None
    phase_key: str | None
    source_object_type: str | None
    source_object_id: str | None
    source_object_version: str | None
    updated_at: datetime
    working_context_json: str


@dataclass(frozen=True)
class ContextBundle:
    """Immutable, provider-neutral context assembled from governed AIOS state.

    D.1 intentionally contains references rather than unrestricted record dumps and
    keeps working context below the Evidence/VerifiedRule trust boundary. Provider,
    model, process and session identity are deliberately absent; those belong to the
    later Agent Runtime Profile binding, not to the persistent employee identity.
    """

    schema_version: str
    tenant_key: str
    purpose: ContextPurpose
    position: PositionContext
    work_item: WorkItemContext
    canonical_references: tuple[ContextReference, ...]
    evidence_refs: tuple[ContextReference, ...]
    verified_rule_refs: tuple[ContextReference, ...]
    source_snapshot_refs: tuple[ContextReference, ...]
    unknowns: tuple[str, ...]
    contradictions: tuple[str, ...]
    allowed_tools: tuple[str, ...]
    sensitivity_labels: tuple[str, ...]
    policy_version: str | None
    context_hash: str
    generated_at: datetime


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant {value!r} is not permitted")


def _canonical_json_object(raw: str | None, *, label: str) -> str:
    candidate = raw if raw not in (None, "") else "{}"
    try:
        decoded = json.loads(candidate, parse_constant=_reject_json_constant)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ContextIntegrityError(f"{label} is not valid JSON") from exc
    if not isinstance(decoded, dict):
        raise ContextIntegrityError(f"{label} must be a JSON object")
    return canonical_json(decoded)


def _active_position(session: Session, position_key: str) -> OrganizationPosition:
    row = session.exec(
        select(OrganizationPosition).where(
            OrganizationPosition.position_key == position_key,
            OrganizationPosition.status == "active",
        )
    ).first()
    if row is None:
        raise ContextIdentityUnavailable("active organization position is unavailable")
    return row


def _canonical_references(work_item: OrganizationalWorkItem) -> tuple[ContextReference, ...]:
    refs: list[ContextReference] = []
    for kind, identifier in (
        ("lead", work_item.lead_id),
        ("profile", work_item.profile_id),
        ("application", work_item.application_id),
        ("corporate_account", work_item.corporate_account_id),
        ("corporate_mobility_case", work_item.corporate_mobility_case_id),
    ):
        if identifier is not None:
            refs.append(ContextReference(kind=kind, identifier=str(identifier)))

    source_type = work_item.source_object_type
    source_id = work_item.source_object_id
    source_version = work_item.source_object_version
    if bool(source_type) != bool(source_id):
        raise ContextIntegrityError("work item source reference is incomplete")
    if source_version is not None and not (source_type and source_id):
        raise ContextIntegrityError("work item source version has no source reference")
    if source_type and source_id:
        refs.append(
            ContextReference(
                kind=source_type,
                identifier=source_id,
                version=source_version,
            )
        )
    return tuple(refs)


def _bundle_hash_payload(
    *,
    tenant_key: str,
    purpose: ContextPurpose,
    position: PositionContext,
    work_item: WorkItemContext,
    canonical_references: tuple[ContextReference, ...],
) -> dict[str, Any]:
    # D.1 deliberately leaves authority-bearing Evidence, rules, tools and policy
    # bindings empty. Their later introduction must be sourced by governed adapters,
    # not promoted from arbitrary WorkItem context JSON.
    return {
        "schema_version": CONTEXT_BUNDLE_SCHEMA_VERSION,
        "tenant_key": tenant_key,
        "purpose": purpose,
        "position": position,
        "work_item": work_item,
        "canonical_references": canonical_references,
        "evidence_refs": (),
        "verified_rule_refs": (),
        "source_snapshot_refs": (),
        "unknowns": (),
        "contradictions": (),
        "allowed_tools": (),
        "sensitivity_labels": (),
        "policy_version": None,
    }


def build_work_item_context_bundle(
    session: Session,
    *,
    tenant_key: str,
    position_key: str,
    work_item_id: UUID,
    purpose: ContextPurpose | str = ContextPurpose.WORK_EXECUTION,
) -> ContextBundle:
    """Build the first bounded ContextBundle for an assigned organization employee.

    The function is intentionally read-only. It resolves canonical WorkItem state in
    the requested tenant, binds it to the currently active OrganizationPosition, and
    produces a deterministic hash over the semantically relevant state. It does not
    create authority, Evidence, tools, memory truth, runtime identity, or provider
    identity.
    """

    tenant = tenant_key.strip()
    position_id = position_key.strip()
    if not tenant or not position_id:
        raise ContextScopeDenied("tenant and position are required")
    try:
        purpose_value = ContextPurpose(purpose)
    except ValueError as exc:
        raise ContextScopeDenied("unsupported context purpose") from exc

    work_item = tenant_record(
        session,
        OrganizationalWorkItem,
        work_item_id,
        tenant,
        label="work item",
    )
    if work_item.assigned_position_key != position_id:
        raise ContextScopeDenied("work item is not assigned to the requested position")

    position = _active_position(session, position_id)
    contract_json = _canonical_json_object(position.contract_json, label="position contract")
    working_context_json = _canonical_json_object(work_item.context_json, label="work item context")
    references = _canonical_references(work_item)

    position_context = PositionContext(
        position_key=position.position_key,
        title=position.title,
        department=position.department,
        reports_to_position_key=position.reports_to_position_key,
        authority_level=position.authority_level,
        role_card_name=position.role_card_name,
        position_version=position.version,
        contract_json=contract_json,
    )
    priority = getattr(work_item.priority, "value", work_item.priority)
    work_context = WorkItemContext(
        work_item_id=work_item.id,
        title=work_item.title,
        objective=work_item.objective,
        department=work_item.department,
        authority_level=work_item.authority_level,
        assigned_position_key=work_item.assigned_position_key,
        status=work_item.status,
        priority=str(priority),
        risk_level=work_item.risk_level,
        is_emergency=work_item.is_emergency,
        objective_key=work_item.objective_key,
        phase_key=work_item.phase_key,
        source_object_type=work_item.source_object_type,
        source_object_id=work_item.source_object_id,
        source_object_version=work_item.source_object_version,
        updated_at=work_item.updated_at,
        working_context_json=working_context_json,
    )
    hash_payload = _bundle_hash_payload(
        tenant_key=tenant,
        purpose=purpose_value,
        position=position_context,
        work_item=work_context,
        canonical_references=references,
    )
    context_hash = canonical_fingerprint(hash_payload)

    return ContextBundle(
        schema_version=CONTEXT_BUNDLE_SCHEMA_VERSION,
        tenant_key=tenant,
        purpose=purpose_value,
        position=position_context,
        work_item=work_context,
        canonical_references=references,
        evidence_refs=(),
        verified_rule_refs=(),
        source_snapshot_refs=(),
        unknowns=(),
        contradictions=(),
        allowed_tools=(),
        sensitivity_labels=(),
        policy_version=None,
        context_hash=context_hash,
        generated_at=now_utc(),
    )
