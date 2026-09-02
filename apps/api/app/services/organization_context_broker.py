from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import Lead, OrganizationPosition, OrganizationalWorkItem, Profile, now_utc
from app.services.organization_command import (
    canonical_fingerprint,
    canonical_json,
    tenant_record,
)
from app.services.organization_context_authority import (
    AuthorityReference,
    ContextAuthorityError,
    ContextAuthorityContribution,
    resolve_context_authority,
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

    D.1 established the trust boundary. D.3 permits authority-bearing references to
    enter the bundle only through governed ContextAuthorityAdapters. Working context
    remains below the Evidence/VerifiedRule/tool/policy trust boundary. Provider,
    model, process and session identity remain deliberately absent; those belong to
    Agent Runtime Profile binding, not persistent employee identity.
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


def _canonical_references(
    session: Session,
    work_item: OrganizationalWorkItem,
) -> tuple[ContextReference, ...]:
    """Resolve canonical subject references and bind mutable case state by fingerprint.

    Lead/Profile identifiers were already part of the D.1 bundle, but E.2 needs case
    state changes to invalidate the context hash. The reference version is therefore a
    canonical record fingerprint. Profile.profile_version remains the separate domain
    precondition used by eligibility governance; the fingerprint additionally catches
    lifecycle/supersession or other canonical-record changes.
    """

    refs: list[ContextReference] = []
    lead: Lead | None = None
    if work_item.lead_id is not None:
        lead = session.get(Lead, work_item.lead_id)
        if lead is None:
            raise ContextIntegrityError("work item lead reference was not found")
        refs.append(
            ContextReference(
                kind="lead",
                identifier=str(lead.id),
                version=canonical_fingerprint(lead),
            )
        )

    if work_item.profile_id is not None:
        profile = session.get(Profile, work_item.profile_id)
        if profile is None:
            raise ContextIntegrityError("work item profile reference was not found")
        if lead is not None and profile.lead_id != lead.id:
            raise ContextIntegrityError("work item profile does not belong to its lead")
        refs.append(
            ContextReference(
                kind="profile",
                identifier=str(profile.id),
                version=canonical_fingerprint(profile),
            )
        )

    for kind, identifier in (
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


def _context_reference(reference: AuthorityReference) -> ContextReference:
    return ContextReference(
        kind=reference.kind,
        identifier=reference.identifier,
        version=reference.version,
    )


def _authority_references(
    base_references: tuple[ContextReference, ...],
    contribution: ContextAuthorityContribution,
    work_item: OrganizationalWorkItem,
) -> tuple[ContextReference, ...]:
    refs = list(base_references)
    if contribution.source_reference_version is not None:
        source_type = work_item.source_object_type
        source_id = work_item.source_object_id
        if not source_type or not source_id:
            raise ContextIntegrityError("authority adapter returned a source version without a source reference")
        replaced = False
        for index, reference in enumerate(refs):
            if reference.kind == source_type and reference.identifier == source_id:
                refs[index] = ContextReference(
                    kind=reference.kind,
                    identifier=reference.identifier,
                    version=contribution.source_reference_version,
                )
                replaced = True
                break
        if not replaced:
            raise ContextIntegrityError("authority adapter source reference is missing from canonical context")

    refs.extend(_context_reference(item) for item in contribution.canonical_references)
    return tuple(refs)


def _bundle_hash_payload(
    *,
    tenant_key: str,
    purpose: ContextPurpose,
    position: PositionContext,
    work_item: WorkItemContext,
    canonical_references: tuple[ContextReference, ...],
    evidence_refs: tuple[ContextReference, ...],
    verified_rule_refs: tuple[ContextReference, ...],
    source_snapshot_refs: tuple[ContextReference, ...],
    unknowns: tuple[str, ...],
    contradictions: tuple[str, ...],
    allowed_tools: tuple[str, ...],
    sensitivity_labels: tuple[str, ...],
    policy_version: str | None,
) -> dict[str, Any]:
    return {
        "schema_version": CONTEXT_BUNDLE_SCHEMA_VERSION,
        "tenant_key": tenant_key,
        "purpose": purpose,
        "position": position,
        "work_item": work_item,
        "canonical_references": canonical_references,
        "evidence_refs": evidence_refs,
        "verified_rule_refs": verified_rule_refs,
        "source_snapshot_refs": source_snapshot_refs,
        "unknowns": unknowns,
        "contradictions": contradictions,
        "allowed_tools": allowed_tools,
        "sensitivity_labels": sensitivity_labels,
        "policy_version": policy_version,
    }


def build_work_item_context_bundle(
    session: Session,
    *,
    tenant_key: str,
    position_key: str,
    work_item_id: UUID,
    purpose: ContextPurpose | str = ContextPurpose.WORK_EXECUTION,
) -> ContextBundle:
    """Build a bounded ContextBundle for an assigned organization employee.

    The function is read-only. Tenant-bound WorkItem and active OrganizationPosition
    state are resolved first. Authority-bearing Evidence/rules/snapshots/policy/tools
    are then resolved only through governed ContextAuthorityAdapters. Arbitrary
    WorkItem context JSON remains working context and cannot self-promote into those
    authority-bearing fields.
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
    base_references = _canonical_references(session, work_item)

    try:
        authority = resolve_context_authority(
            session,
            position=position,
            work_item=work_item,
        )
    except ContextAuthorityError as exc:
        raise ContextIntegrityError("governed context authority could not be resolved") from exc

    references = _authority_references(base_references, authority, work_item)
    evidence_refs = tuple(_context_reference(item) for item in authority.evidence_refs)
    verified_rule_refs = tuple(_context_reference(item) for item in authority.verified_rule_refs)
    source_snapshot_refs = tuple(_context_reference(item) for item in authority.source_snapshot_refs)

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
    sensitivity_labels: tuple[str, ...] = ()
    hash_payload = _bundle_hash_payload(
        tenant_key=tenant,
        purpose=purpose_value,
        position=position_context,
        work_item=work_context,
        canonical_references=references,
        evidence_refs=evidence_refs,
        verified_rule_refs=verified_rule_refs,
        source_snapshot_refs=source_snapshot_refs,
        unknowns=authority.unknowns,
        contradictions=authority.contradictions,
        allowed_tools=authority.allowed_tools,
        sensitivity_labels=sensitivity_labels,
        policy_version=authority.policy_version,
    )
    context_hash = canonical_fingerprint(hash_payload)

    return ContextBundle(
        schema_version=CONTEXT_BUNDLE_SCHEMA_VERSION,
        tenant_key=tenant,
        purpose=purpose_value,
        position=position_context,
        work_item=work_context,
        canonical_references=references,
        evidence_refs=evidence_refs,
        verified_rule_refs=verified_rule_refs,
        source_snapshot_refs=source_snapshot_refs,
        unknowns=authority.unknowns,
        contradictions=authority.contradictions,
        allowed_tools=authority.allowed_tools,
        sensitivity_labels=sensitivity_labels,
        policy_version=authority.policy_version,
        context_hash=context_hash,
        generated_at=now_utc(),
    )