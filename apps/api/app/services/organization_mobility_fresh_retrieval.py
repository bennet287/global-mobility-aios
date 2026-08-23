from __future__ import annotations

import socket
from dataclasses import dataclass
from typing import Mapping
from uuid import UUID

import httpx
from sqlmodel import Session, select

from app.models.domain import SourceMonitor, SourceRetrievalRun, SourceSnapshot
from app.services.organization_command import DependencyConflict, canonical_fingerprint
from app.services.organization_context_broker import (
    ContextPurpose,
    ContextReference,
    build_work_item_context_bundle,
)
from app.services.organization_mobility_objective_runtime import (
    AUSTRIA_MOBILITY_PATHWAY_POSITION,
    AUSTRIA_MOBILITY_REGULATORY_POSITION,
    AUSTRIA_MOBILITY_SPECIALIST_POSITIONS,
    AustriaMobilityObjectivePlan,
)
from app.services.source_retrieval import Resolver, execute_source_monitor


FRESH_RETRIEVAL_SCOPE = "pre_k1_official_source_equivalence"
_ACCEPTED_FRESH_RUN_STATUSES = frozenset({"baseline", "unchanged", "not_modified"})
_SNAPSHOT_PRODUCING_STATUSES = frozenset({"baseline", "unchanged", "changed"})


@dataclass(frozen=True, slots=True)
class AustriaFreshRetrievalAttestation:
    governed_source_snapshot_id: UUID
    governed_source_snapshot_version: str
    official_source_id: UUID
    source_monitor_id: UUID
    source_retrieval_run_id: UUID
    source_retrieval_run_version: str
    retrieval_status: str
    retrieval_completed_at: str
    checked_source_snapshot_id: UUID
    checked_source_snapshot_version: str
    snapshot_basis_retrieval_run_id: UUID
    snapshot_basis_retrieval_run_version: str
    content_hash: str
    freshness_scope: str = FRESH_RETRIEVAL_SCOPE
    content_equivalent_to_governed: bool = True
    freshness_verified: bool = True

    def payload(self) -> dict[str, object]:
        return {
            "governed_source_snapshot_id": str(self.governed_source_snapshot_id),
            "governed_source_snapshot_version": self.governed_source_snapshot_version,
            "official_source_id": str(self.official_source_id),
            "source_monitor_id": str(self.source_monitor_id),
            "source_retrieval_run_id": str(self.source_retrieval_run_id),
            "source_retrieval_run_version": self.source_retrieval_run_version,
            "retrieval_status": self.retrieval_status,
            "retrieval_completed_at": self.retrieval_completed_at,
            "checked_source_snapshot_id": str(self.checked_source_snapshot_id),
            "checked_source_snapshot_version": self.checked_source_snapshot_version,
            "snapshot_basis_retrieval_run_id": str(self.snapshot_basis_retrieval_run_id),
            "snapshot_basis_retrieval_run_version": self.snapshot_basis_retrieval_run_version,
            "content_hash": self.content_hash,
            "freshness_scope": self.freshness_scope,
            "content_equivalent_to_governed": self.content_equivalent_to_governed,
            "freshness_verified": self.freshness_verified,
        }


def _specialist_work(plan: AustriaMobilityObjectivePlan, position_key: str):
    if position_key == AUSTRIA_MOBILITY_PATHWAY_POSITION:
        return plan.pathway_work_item
    if position_key == AUSTRIA_MOBILITY_REGULATORY_POSITION:
        return plan.regulatory_work_item
    raise DependencyConflict(f"unsupported Austria specialist position: {position_key}")


def _governed_snapshot_references(
    session: Session,
    plan: AustriaMobilityObjectivePlan,
) -> dict[UUID, ContextReference]:
    references: dict[UUID, ContextReference] = {}
    for position_key in AUSTRIA_MOBILITY_SPECIALIST_POSITIONS:
        work = _specialist_work(plan, position_key)
        context = build_work_item_context_bundle(
            session,
            tenant_key=work.tenant_key,
            position_key=position_key,
            work_item_id=work.id,
            purpose=ContextPurpose.COLLABORATION,
        )
        for reference in context.source_snapshot_refs:
            if reference.kind != "source_snapshot" or reference.version is None:
                raise DependencyConflict("Austria authority snapshot provenance is incomplete")
            try:
                snapshot_id = UUID(reference.identifier)
            except ValueError as exc:
                raise DependencyConflict("Austria authority snapshot identifier is invalid") from exc
            existing = references.get(snapshot_id)
            if existing is not None and existing.version != reference.version:
                raise DependencyConflict("Austria specialists resolved conflicting snapshot versions")
            references[snapshot_id] = reference
    if not references:
        raise DependencyConflict("Austria live evaluation requires governed source snapshots")
    return references


def _monitor_for_source(session: Session, official_source_id: UUID) -> SourceMonitor:
    monitors = list(
        session.exec(
            select(SourceMonitor).where(SourceMonitor.official_source_id == official_source_id)
        ).all()
    )
    if len(monitors) != 1:
        raise DependencyConflict(
            "fresh retrieval requires exactly one source monitor for every governed official source"
        )
    return monitors[0]


def _snapshot_basis_run_for_not_modified(
    session: Session,
    run: SourceRetrievalRun,
) -> SourceRetrievalRun:
    candidates = list(
        session.exec(
            select(SourceRetrievalRun)
            .where(
                SourceRetrievalRun.monitor_id == run.monitor_id,
                SourceRetrievalRun.id != run.id,
                SourceRetrievalRun.snapshot_id.is_not(None),
                SourceRetrievalRun.status.in_(_SNAPSHOT_PRODUCING_STATUSES),
                SourceRetrievalRun.completed_at.is_not(None),
            )
            .order_by(SourceRetrievalRun.completed_at.desc())
        ).all()
    )
    if not candidates:
        raise DependencyConflict(
            "HTTP 304 freshness cannot be proven without a prior snapshot-producing retrieval run"
        )
    return candidates[0]


def _attestation_for_run(
    session: Session,
    *,
    governed_snapshot: SourceSnapshot,
    governed_snapshot_version: str,
    monitor: SourceMonitor,
    run: SourceRetrievalRun,
) -> AustriaFreshRetrievalAttestation:
    if run.status == "failed":
        detail = run.error_code or "retrieval_failed"
        raise DependencyConflict(f"fresh official-source retrieval failed: {detail}")
    if run.status == "changed":
        raise DependencyConflict(
            "fresh official-source retrieval detected changed content; governance review is required before K.1"
        )
    if run.status not in _ACCEPTED_FRESH_RUN_STATUSES or run.completed_at is None:
        raise DependencyConflict("fresh official-source retrieval did not reach an accepted terminal state")

    if run.status == "not_modified":
        if run.snapshot_id is not None:
            raise DependencyConflict("not-modified retrieval unexpectedly produced a snapshot")
        basis_run = _snapshot_basis_run_for_not_modified(session, run)
        checked_snapshot_id = basis_run.snapshot_id
    else:
        if run.snapshot_id is None:
            raise DependencyConflict("fresh retrieval did not persist its checked snapshot")
        basis_run = run
        checked_snapshot_id = run.snapshot_id

    if checked_snapshot_id is None:
        raise DependencyConflict("fresh retrieval lacks checked snapshot provenance")
    checked_snapshot = session.get(SourceSnapshot, checked_snapshot_id)
    if checked_snapshot is None:
        raise DependencyConflict("fresh retrieval checked snapshot is unavailable")
    if governed_snapshot.official_source_id is None:
        raise DependencyConflict("governed source snapshot lacks official-source provenance")
    if (
        checked_snapshot.official_source_id != governed_snapshot.official_source_id
        or run.official_source_id != governed_snapshot.official_source_id
        or basis_run.official_source_id != governed_snapshot.official_source_id
        or monitor.official_source_id != governed_snapshot.official_source_id
    ):
        raise DependencyConflict("fresh retrieval crossed official-source provenance")
    if not governed_snapshot.content_hash or not checked_snapshot.content_hash:
        raise DependencyConflict("fresh retrieval requires content hashes on governed and checked snapshots")
    if checked_snapshot.content_hash != governed_snapshot.content_hash:
        raise DependencyConflict(
            "fresh official-source content does not match the governed snapshot; governance update is required"
        )

    return AustriaFreshRetrievalAttestation(
        governed_source_snapshot_id=governed_snapshot.id,
        governed_source_snapshot_version=governed_snapshot_version,
        official_source_id=governed_snapshot.official_source_id,
        source_monitor_id=monitor.id,
        source_retrieval_run_id=run.id,
        source_retrieval_run_version=canonical_fingerprint(run),
        retrieval_status=run.status,
        retrieval_completed_at=run.completed_at.isoformat(),
        checked_source_snapshot_id=checked_snapshot.id,
        checked_source_snapshot_version=canonical_fingerprint(checked_snapshot),
        snapshot_basis_retrieval_run_id=basis_run.id,
        snapshot_basis_retrieval_run_version=canonical_fingerprint(basis_run),
        content_hash=governed_snapshot.content_hash,
    )


def refresh_austria_authority_snapshots(
    session: Session,
    plan: AustriaMobilityObjectivePlan,
    *,
    transport: httpx.BaseTransport | None = None,
    resolver: Resolver = socket.getaddrinfo,
) -> dict[UUID, AustriaFreshRetrievalAttestation]:
    """Fresh-check every governed Austria snapshot immediately before K.1.

    Retrieval is allowed to create monitoring snapshots/change records, but K.1 never
    switches authority to them. Execution receives an attestation only when the fresh
    official-source check is content-equivalent to the already governed snapshot. A
    detected change fails closed and remains in the regulatory-review workflow.
    """

    references = _governed_snapshot_references(session, plan)
    attestations: dict[UUID, AustriaFreshRetrievalAttestation] = {}
    for snapshot_id in sorted(references, key=str):
        reference = references[snapshot_id]
        governed_snapshot = session.get(SourceSnapshot, snapshot_id)
        if governed_snapshot is None:
            raise DependencyConflict("governed source snapshot is unavailable")
        if canonical_fingerprint(governed_snapshot) != reference.version:
            raise DependencyConflict("governed source snapshot changed after context resolution")
        if governed_snapshot.official_source_id is None:
            raise DependencyConflict("governed source snapshot lacks official-source provenance")
        monitor = _monitor_for_source(session, governed_snapshot.official_source_id)
        run = execute_source_monitor(
            session,
            monitor.id,
            transport=transport,
            resolver=resolver,
        )
        attestations[snapshot_id] = _attestation_for_run(
            session,
            governed_snapshot=governed_snapshot,
            governed_snapshot_version=reference.version,
            monitor=monitor,
            run=run,
        )
    return attestations


def _attestation_from_payload(value: object) -> AustriaFreshRetrievalAttestation:
    if not isinstance(value, dict):
        raise DependencyConflict("fresh retrieval attestation must be an object")
    required_text = (
        "governed_source_snapshot_version",
        "source_retrieval_run_version",
        "retrieval_status",
        "retrieval_completed_at",
        "checked_source_snapshot_version",
        "snapshot_basis_retrieval_run_version",
        "content_hash",
        "freshness_scope",
    )
    for field in required_text:
        candidate = value.get(field)
        if not isinstance(candidate, str) or not candidate.strip():
            raise DependencyConflict(f"fresh retrieval attestation {field} is invalid")
    if value.get("freshness_verified") is not True or value.get("content_equivalent_to_governed") is not True:
        raise DependencyConflict("fresh retrieval attestation must explicitly prove equivalence")
    try:
        return AustriaFreshRetrievalAttestation(
            governed_source_snapshot_id=UUID(str(value["governed_source_snapshot_id"])),
            governed_source_snapshot_version=str(value["governed_source_snapshot_version"]),
            official_source_id=UUID(str(value["official_source_id"])),
            source_monitor_id=UUID(str(value["source_monitor_id"])),
            source_retrieval_run_id=UUID(str(value["source_retrieval_run_id"])),
            source_retrieval_run_version=str(value["source_retrieval_run_version"]),
            retrieval_status=str(value["retrieval_status"]),
            retrieval_completed_at=str(value["retrieval_completed_at"]),
            checked_source_snapshot_id=UUID(str(value["checked_source_snapshot_id"])),
            checked_source_snapshot_version=str(value["checked_source_snapshot_version"]),
            snapshot_basis_retrieval_run_id=UUID(str(value["snapshot_basis_retrieval_run_id"])),
            snapshot_basis_retrieval_run_version=str(value["snapshot_basis_retrieval_run_version"]),
            content_hash=str(value["content_hash"]),
            freshness_scope=str(value["freshness_scope"]),
            content_equivalent_to_governed=True,
            freshness_verified=True,
        )
    except (KeyError, ValueError) as exc:
        raise DependencyConflict("fresh retrieval attestation identifiers are invalid") from exc


def _validate_attestation(
    session: Session,
    *,
    reference: ContextReference,
    attestation: AustriaFreshRetrievalAttestation,
) -> dict[str, object]:
    try:
        reference_id = UUID(reference.identifier)
    except ValueError as exc:
        raise DependencyConflict("context source snapshot identifier is invalid") from exc
    if reference.kind != "source_snapshot" or reference.version is None:
        raise DependencyConflict("context source snapshot reference is incomplete")
    if (
        attestation.governed_source_snapshot_id != reference_id
        or attestation.governed_source_snapshot_version != reference.version
        or attestation.freshness_scope != FRESH_RETRIEVAL_SCOPE
        or not attestation.freshness_verified
        or not attestation.content_equivalent_to_governed
    ):
        raise DependencyConflict("fresh retrieval attestation does not match governed context")
    if attestation.retrieval_status not in _ACCEPTED_FRESH_RUN_STATUSES:
        raise DependencyConflict("fresh retrieval attestation has an unsafe retrieval status")

    governed = session.get(SourceSnapshot, attestation.governed_source_snapshot_id)
    checked = session.get(SourceSnapshot, attestation.checked_source_snapshot_id)
    monitor = session.get(SourceMonitor, attestation.source_monitor_id)
    run = session.get(SourceRetrievalRun, attestation.source_retrieval_run_id)
    basis_run = session.get(SourceRetrievalRun, attestation.snapshot_basis_retrieval_run_id)
    if None in (governed, checked, monitor, run, basis_run):
        raise DependencyConflict("fresh retrieval attestation durable lineage is unavailable")
    assert governed is not None and checked is not None and monitor is not None and run is not None and basis_run is not None
    if canonical_fingerprint(governed) != attestation.governed_source_snapshot_version:
        raise DependencyConflict("fresh retrieval governed snapshot fingerprint diverged")
    if canonical_fingerprint(checked) != attestation.checked_source_snapshot_version:
        raise DependencyConflict("fresh retrieval checked snapshot fingerprint diverged")
    if canonical_fingerprint(run) != attestation.source_retrieval_run_version:
        raise DependencyConflict("fresh retrieval run fingerprint diverged")
    if canonical_fingerprint(basis_run) != attestation.snapshot_basis_retrieval_run_version:
        raise DependencyConflict("fresh retrieval basis run fingerprint diverged")
    if run.status != attestation.retrieval_status or run.completed_at is None:
        raise DependencyConflict("fresh retrieval run status/completion diverged")
    if run.completed_at.isoformat() != attestation.retrieval_completed_at:
        raise DependencyConflict("fresh retrieval completion timestamp diverged")
    if (
        governed.official_source_id != attestation.official_source_id
        or checked.official_source_id != attestation.official_source_id
        or monitor.official_source_id != attestation.official_source_id
        or run.official_source_id != attestation.official_source_id
        or basis_run.official_source_id != attestation.official_source_id
        or run.monitor_id != monitor.id
        or basis_run.monitor_id != monitor.id
    ):
        raise DependencyConflict("fresh retrieval attestation crossed durable source lineage")
    if (
        not governed.content_hash
        or governed.content_hash != attestation.content_hash
        or checked.content_hash != governed.content_hash
    ):
        raise DependencyConflict("fresh retrieval content-equivalence proof diverged")
    if run.status == "not_modified":
        if run.snapshot_id is not None or basis_run.id == run.id or basis_run.snapshot_id != checked.id:
            raise DependencyConflict("fresh retrieval 304 basis lineage is invalid")
    else:
        if run.snapshot_id != checked.id or basis_run.id != run.id:
            raise DependencyConflict("fresh retrieval checked-snapshot lineage is invalid")
    return attestation.payload()


def validate_fresh_retrieval_attestations(
    session: Session,
    *,
    source_snapshot_refs: tuple[ContextReference, ...],
    attestations: Mapping[UUID, AustriaFreshRetrievalAttestation] | None,
) -> tuple[dict[str, object], ...]:
    """Validate execution-supplied fresh checks against current durable DB lineage."""

    if not attestations:
        return ()
    payloads: list[dict[str, object]] = []
    seen: set[UUID] = set()
    for reference in source_snapshot_refs:
        try:
            snapshot_id = UUID(reference.identifier)
        except ValueError as exc:
            raise DependencyConflict("context source snapshot identifier is invalid") from exc
        attestation = attestations.get(snapshot_id)
        if attestation is None:
            raise DependencyConflict("fresh retrieval attestations do not cover every governed snapshot")
        payloads.append(
            _validate_attestation(
                session,
                reference=reference,
                attestation=attestation,
            )
        )
        seen.add(snapshot_id)
    if set(attestations) != seen:
        raise DependencyConflict("fresh retrieval attestations include snapshots outside this context")
    return tuple(payloads)


def validate_persisted_fresh_retrieval_provenance(
    session: Session,
    provenance: Mapping[str, object],
) -> int:
    """Revalidate persisted K.1 freshness claims against SourceRetrievalRun lineage."""

    raw_attestations = provenance.get("context_fresh_retrieval_attestations")
    if raw_attestations in (None, []):
        return 0
    if not isinstance(raw_attestations, list):
        raise DependencyConflict("persisted fresh retrieval provenance must be a list")
    raw_refs = provenance.get("context_source_snapshot_refs")
    if not isinstance(raw_refs, list):
        raise DependencyConflict("persisted freshness requires source snapshot references")
    references: list[ContextReference] = []
    for value in raw_refs:
        if not isinstance(value, dict):
            raise DependencyConflict("persisted source snapshot reference is invalid")
        kind = value.get("kind")
        identifier = value.get("identifier")
        version = value.get("version")
        if not isinstance(kind, str) or not isinstance(identifier, str):
            raise DependencyConflict("persisted source snapshot reference is incomplete")
        if version is not None and not isinstance(version, str):
            raise DependencyConflict("persisted source snapshot version is invalid")
        references.append(ContextReference(kind=kind, identifier=identifier, version=version))
    parsed = [_attestation_from_payload(value) for value in raw_attestations]
    by_snapshot: dict[UUID, AustriaFreshRetrievalAttestation] = {}
    for attestation in parsed:
        if attestation.governed_source_snapshot_id in by_snapshot:
            raise DependencyConflict("persisted fresh retrieval provenance contains duplicates")
        by_snapshot[attestation.governed_source_snapshot_id] = attestation
    validated = validate_fresh_retrieval_attestations(
        session,
        source_snapshot_refs=tuple(references),
        attestations=by_snapshot,
    )
    return len(validated)
