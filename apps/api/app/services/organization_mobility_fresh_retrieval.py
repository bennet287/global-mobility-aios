from __future__ import annotations

import json
import socket
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping
from uuid import UUID

import httpx
from sqlmodel import Session, select

from app.models.domain import (
    AgentRun,
    OrganizationalActionOutput,
    SourceMonitor,
    SourceRetrievalRun,
    SourceSnapshot,
    now_utc,
)
from app.services.audit_log import record_audit
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
FRESH_RETRIEVAL_EVIDENCE_CONTRACT_VERSION = "austria-fresh-retrieval-evidence.v1"
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


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _json_object(value: str | None, *, label: str) -> dict[str, object]:
    try:
        parsed = json.loads(value or "{}")
    except (TypeError, json.JSONDecodeError) as exc:
        raise DependencyConflict(f"{label} is invalid JSON") from exc
    if not isinstance(parsed, dict):
        raise DependencyConflict(f"{label} must be a JSON object")
    return parsed


def _json_list(value: str | None, *, label: str) -> list[object]:
    try:
        parsed = json.loads(value or "[]")
    except (TypeError, json.JSONDecodeError) as exc:
        raise DependencyConflict(f"{label} is invalid JSON") from exc
    if not isinstance(parsed, list):
        raise DependencyConflict(f"{label} must be a JSON array")
    return parsed


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
                SourceRetrievalRun.status.in_(tuple(_SNAPSHOT_PRODUCING_STATUSES)),
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
    switches authority to them. The L cycle receives an attestation only when the fresh
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
    if (
        value.get("freshness_verified") is not True
        or value.get("content_equivalent_to_governed") is not True
    ):
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
    if any(item is None for item in (governed, checked, monitor, run, basis_run)):
        raise DependencyConflict("fresh retrieval attestation durable lineage is unavailable")
    assert governed is not None
    assert checked is not None
    assert monitor is not None
    assert run is not None
    assert basis_run is not None
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
        if (
            run.snapshot_id is not None
            or basis_run.id == run.id
            or basis_run.snapshot_id != checked.id
        ):
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
    """Validate execution-cycle fresh checks against current durable DB lineage."""

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


def _source_snapshot_refs_from_output(payload: Mapping[str, object]) -> tuple[ContextReference, ...]:
    raw_refs = payload.get("context_source_snapshot_refs")
    if not isinstance(raw_refs, list):
        raise DependencyConflict("K.1 output lacks source snapshot references for freshness proof")
    references: list[ContextReference] = []
    for value in raw_refs:
        if not isinstance(value, dict):
            raise DependencyConflict("K.1 source snapshot reference is invalid")
        kind = value.get("kind")
        identifier = value.get("identifier")
        version = value.get("version")
        if not isinstance(kind, str) or not isinstance(identifier, str):
            raise DependencyConflict("K.1 source snapshot reference is incomplete")
        if version is not None and not isinstance(version, str):
            raise DependencyConflict("K.1 source snapshot version is invalid")
        references.append(ContextReference(kind=kind, identifier=identifier, version=version))
    return tuple(references)


def _ensure_retrieval_precedes_agent_run(
    session: Session,
    *,
    attestations: Mapping[UUID, AustriaFreshRetrievalAttestation],
    agent_run: AgentRun,
) -> None:
    for attestation in attestations.values():
        run = session.get(SourceRetrievalRun, attestation.source_retrieval_run_id)
        if run is None or run.completed_at is None:
            raise DependencyConflict("fresh retrieval completion lineage is unavailable")
        if _utc(run.completed_at) > _utc(agent_run.created_at):
            raise DependencyConflict("fresh retrieval occurred after the controlled AgentRun started")


def attach_fresh_retrieval_evidence(
    session: Session,
    *,
    action_output_id: UUID,
    agent_run_id: UUID,
    execution_attempt_id: UUID,
    work_item_id: UUID,
    position_key: str,
    attestations: Mapping[UUID, AustriaFreshRetrievalAttestation],
    actor: str,
) -> int:
    """Bind pre-K.1 retrieval checks to the exact durable K.1 output/AgentRun lineage."""

    output = session.get(OrganizationalActionOutput, action_output_id)
    agent_run = session.get(AgentRun, agent_run_id)
    if output is None or agent_run is None:
        raise DependencyConflict("fresh retrieval cannot attach to unavailable K.1 lineage")
    if (
        output.work_item_id != work_item_id
        or output.accountable_position_key != position_key
        or output.status != "completed"
    ):
        raise DependencyConflict("fresh retrieval target K.1 output lineage is invalid")
    payload = _json_object(output.output_json, label="K.1 output")
    if (
        payload.get("agent_run_id") != str(agent_run_id)
        or payload.get("execution_attempt_id") != str(execution_attempt_id)
        or payload.get("work_item_id") != str(work_item_id)
        or payload.get("position_key") != position_key
    ):
        raise DependencyConflict("fresh retrieval target execution identifiers diverged")
    references = _source_snapshot_refs_from_output(payload)
    validated = validate_fresh_retrieval_attestations(
        session,
        source_snapshot_refs=references,
        attestations=attestations,
    )
    if not validated:
        raise DependencyConflict("fresh retrieval evidence requires at least one governed snapshot")
    _ensure_retrieval_precedes_agent_run(
        session,
        attestations=attestations,
        agent_run=agent_run,
    )
    evidence = {
        "contract_version": FRESH_RETRIEVAL_EVIDENCE_CONTRACT_VERSION,
        "work_item_id": str(work_item_id),
        "position_key": position_key,
        "execution_attempt_id": str(execution_attempt_id),
        "agent_run_id": str(agent_run_id),
        "freshness_scope": FRESH_RETRIEVAL_SCOPE,
        "attestation_count": len(validated),
        "attestations": list(validated),
        "freshness_verified": True,
        "provider_model_authority": False,
        "external_action_authorized": False,
    }
    existing = payload.get("fresh_retrieval_evidence")
    if existing is not None:
        if existing != evidence:
            raise DependencyConflict("K.1 output already has conflicting fresh retrieval evidence")
        return len(validated)

    output_evidence = _json_list(output.evidence_json, label="K.1 evidence")
    output_evidence.append({"type": "fresh_retrieval_evidence", **evidence})
    payload["fresh_retrieval_evidence"] = evidence
    output.output_json = json.dumps(payload, default=str, sort_keys=True, separators=(",", ":"))
    output.evidence_json = json.dumps(
        output_evidence,
        default=str,
        sort_keys=True,
        separators=(",", ":"),
    )
    output.updated_at = now_utc()
    session.add(output)
    record_audit(
        session,
        action="austria_specialist_fresh_retrieval_evidence_attached",
        entity_type="organizational_action_output",
        entity_id=output.id,
        after_state={
            "work_item_id": str(work_item_id),
            "position_key": position_key,
            "execution_attempt_id": str(execution_attempt_id),
            "agent_run_id": str(agent_run_id),
            "attestation_count": len(validated),
            "external_action_authorized": False,
        },
        actor=actor,
        source="austria_live_retrieval_l_v1",
    )
    session.commit()
    session.refresh(output)
    return len(validated)


def validate_action_output_fresh_retrieval_evidence(
    session: Session,
    *,
    output: OrganizationalActionOutput,
    agent_run: AgentRun,
) -> int:
    """Revalidate persisted L-cycle freshness evidence against live DB retrieval lineage."""

    payload = _json_object(output.output_json, label="K.1 output")
    raw_evidence = payload.get("fresh_retrieval_evidence")
    if raw_evidence is None:
        return 0
    if not isinstance(raw_evidence, dict):
        raise DependencyConflict("persisted fresh retrieval evidence must be an object")
    if raw_evidence.get("contract_version") != FRESH_RETRIEVAL_EVIDENCE_CONTRACT_VERSION:
        raise DependencyConflict("persisted fresh retrieval evidence has the wrong contract version")
    if (
        raw_evidence.get("work_item_id") != str(output.work_item_id)
        or raw_evidence.get("position_key") != output.accountable_position_key
        or raw_evidence.get("agent_run_id") != str(agent_run.id)
        or raw_evidence.get("freshness_scope") != FRESH_RETRIEVAL_SCOPE
        or raw_evidence.get("freshness_verified") is not True
        or raw_evidence.get("provider_model_authority") is not False
        or raw_evidence.get("external_action_authorized") is not False
    ):
        raise DependencyConflict("persisted fresh retrieval evidence lineage/authority is invalid")
    execution_attempt_id = raw_evidence.get("execution_attempt_id")
    if not isinstance(execution_attempt_id, str) or payload.get("execution_attempt_id") != execution_attempt_id:
        raise DependencyConflict("persisted fresh retrieval execution-attempt lineage diverged")
    if payload.get("agent_run_id") != str(agent_run.id):
        raise DependencyConflict("persisted fresh retrieval AgentRun lineage diverged")

    raw_attestations = raw_evidence.get("attestations")
    if not isinstance(raw_attestations, list):
        raise DependencyConflict("persisted fresh retrieval attestations must be a list")
    parsed = [_attestation_from_payload(value) for value in raw_attestations]
    by_snapshot: dict[UUID, AustriaFreshRetrievalAttestation] = {}
    for attestation in parsed:
        if attestation.governed_source_snapshot_id in by_snapshot:
            raise DependencyConflict("persisted fresh retrieval evidence contains duplicate snapshots")
        by_snapshot[attestation.governed_source_snapshot_id] = attestation
    references = _source_snapshot_refs_from_output(payload)
    validated = validate_fresh_retrieval_attestations(
        session,
        source_snapshot_refs=references,
        attestations=by_snapshot,
    )
    if raw_evidence.get("attestation_count") != len(validated) or not validated:
        raise DependencyConflict("persisted fresh retrieval attestation count diverged")
    _ensure_retrieval_precedes_agent_run(
        session,
        attestations=by_snapshot,
        agent_run=agent_run,
    )

    evidence_items = _json_list(output.evidence_json, label="K.1 evidence")
    matching = [
        item
        for item in evidence_items
        if isinstance(item, dict) and item.get("type") == "fresh_retrieval_evidence"
    ]
    expected_item = {"type": "fresh_retrieval_evidence", **raw_evidence}
    if len(matching) != 1 or matching[0] != expected_item:
        raise DependencyConflict("persisted fresh retrieval ActionOutput evidence diverged")
    return len(validated)
