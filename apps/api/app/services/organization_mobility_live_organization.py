from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    OrganizationActivity,
    OrganizationActivityClass,
    OrganizationBlocker,
    OrganizationBlockerStatus,
    OrganizationalActionOutput,
    OrganizationalWorkItem,
    now_utc,
)
from app.services.audit_log import record_audit
from app.services.organization_activity import stage_activity
from app.services.organization_command import (
    DependencyConflict,
    InvalidTransition,
    canonical_fingerprint,
    system_bound_agent_command_context,
)
from app.services.organization_mobility_objective_runtime import (
    AUSTRIA_MOBILITY_OBJECTIVE_OWNER_POSITION,
    AUSTRIA_MOBILITY_PATHWAY_POSITION,
    AUSTRIA_MOBILITY_REGULATORY_POSITION,
    AUSTRIA_MOBILITY_SPECIALIST_POSITIONS,
    _specialist_execution_evidence_reason,
    austria_objective_readiness,
    austria_specialist_output_key,
)
from app.services.organization_transparency import (
    TransparencyActivityRecord,
    activities_for_work_item,
)
from app.services.organization_work import complete_work_item


AUSTRIA_LIVE_ORGANIZATION_CONTRACT_VERSION = "austria-live-organization-owner-synthesis.v1"
AUSTRIA_LIVE_ORGANIZATION_ACTIVITY_TYPE = "organization.mobility.owner_synthesis.completed.v1"
SOURCE = "organization_mobility_live_organization"


@dataclass(frozen=True, slots=True)
class AustriaLiveSpecialistSnapshot:
    position_key: str
    work_item_id: UUID
    status: str
    evidence_valid: bool
    evidence_reason: str | None
    action_output_id: UUID | None
    execution_attempt_id: UUID | None
    agent_run_id: UUID | None
    context_hash: str | None
    runtime_binding_hash: str | None
    latency_ms: int | None
    retry_count: int | None
    confidence: float | None
    provider_model_authority: bool
    external_action_authorized: bool


@dataclass(frozen=True, slots=True)
class AustriaLiveBlockerSnapshot:
    blocker_id: UUID
    work_item_id: UUID | None
    blocker_type: str
    severity: str
    status: str
    title: str
    description: str
    accountable_position_key: str | None
    requires_human_action: bool
    created_at: datetime


@dataclass(frozen=True, slots=True)
class AustriaOwnerSynthesisSnapshot:
    action_output_id: UUID
    activity_id: UUID
    disposition: str
    recommendation: str
    confidence: float
    total_latency_ms: int
    max_latency_ms: int
    total_retry_count: int
    external_action_authorized: bool
    human_review_required: bool
    completed_at: datetime | None


@dataclass(frozen=True, slots=True)
class AustriaOwnerSynthesisResult:
    root_work_item_id: UUID
    action_output_id: UUID
    activity_id: UUID
    disposition: str
    replayed: bool


@dataclass(frozen=True, slots=True)
class AustriaLiveOrganizationSnapshot:
    generated_at: datetime
    root_work_item_id: UUID
    objective_key: str
    owner_position_key: str
    root_status: str
    cycle_status: str
    owner_synthesis_state: str
    ready_for_owner_synthesis: bool
    readiness_reasons: tuple[str, ...]
    authority_level: str
    authority_posture: str
    autonomy_profile_state: str | None
    provider_model_authority: bool
    external_action_authorized: bool
    specialist_outputs: tuple[AustriaLiveSpecialistSnapshot, ...]
    owner_synthesis: AustriaOwnerSynthesisSnapshot | None
    blockers: tuple[AustriaLiveBlockerSnapshot, ...]
    total_latency_ms: int
    max_latency_ms: int
    total_retry_count: int
    activity_count: int
    activities: tuple[TransparencyActivityRecord, ...]
    domain_evidence_refs: tuple[str, ...]
    verified_rule_refs: tuple[str, ...]


def austria_owner_synthesis_output_key(root_work_item_id: UUID) -> str:
    return f"l1:austria-owner-synthesis:{root_work_item_id}"


def austria_owner_synthesis_activity_key(root_work_item_id: UUID) -> str:
    return f"l1:austria-owner-synthesis-activity:{root_work_item_id}"


def _json_object(value: str | None, *, label: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value or "{}")
    except json.JSONDecodeError as exc:
        raise DependencyConflict(f"{label} is invalid JSON") from exc
    if not isinstance(parsed, dict):
        raise DependencyConflict(f"{label} must be a JSON object")
    return parsed


def _json_dump(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _canonical_objective(
    session: Session,
    *,
    tenant_key: str,
    root_work_item_id: UUID,
) -> tuple[OrganizationalWorkItem, dict[str, OrganizationalWorkItem]]:
    root = session.exec(
        select(OrganizationalWorkItem).where(
            OrganizationalWorkItem.id == root_work_item_id,
            OrganizationalWorkItem.tenant_key == tenant_key,
        )
    ).first()
    if root is None:
        raise DependencyConflict("Austria mobility objective root was not found")
    if (
        root.assigned_position_key != AUSTRIA_MOBILITY_OBJECTIVE_OWNER_POSITION
        or root.work_type != "mobility_objective"
        or root.phase_key != "J.1"
        or not root.objective_key
    ):
        raise InvalidTransition("work item is not the canonical Austria mobility objective root")

    children = session.exec(
        select(OrganizationalWorkItem).where(
            OrganizationalWorkItem.tenant_key == tenant_key,
            OrganizationalWorkItem.parent_work_item_id == root.id,
        )
    ).all()
    expected_phase = {
        AUSTRIA_MOBILITY_PATHWAY_POSITION: "J.1.pathway",
        AUSTRIA_MOBILITY_REGULATORY_POSITION: "J.1.regulatory",
    }
    by_position: dict[str, list[OrganizationalWorkItem]] = {}
    for child in children:
        by_position.setdefault(child.assigned_position_key, []).append(child)

    resolved: dict[str, OrganizationalWorkItem] = {}
    for position_key in AUSTRIA_MOBILITY_SPECIALIST_POSITIONS:
        matches = by_position.get(position_key, [])
        if len(matches) != 1:
            raise DependencyConflict(
                f"{position_key} requires exactly one child WorkItem; found {len(matches)}"
            )
        child = matches[0]
        if child.objective_key != root.objective_key or child.phase_key != expected_phase[position_key]:
            raise DependencyConflict(f"{position_key} is outside the canonical Austria objective topology")
        resolved[position_key] = child
    return root, resolved


def _current_output(
    session: Session,
    *,
    root: OrganizationalWorkItem,
    child: OrganizationalWorkItem,
    position_key: str,
) -> tuple[OrganizationalActionOutput, dict[str, Any], dict[str, Any]]:
    reason = _specialist_execution_evidence_reason(
        session,
        root=root,
        child=child,
        position_key=position_key,
    )
    if reason is not None:
        raise DependencyConflict(reason)
    output = session.exec(
        select(OrganizationalActionOutput).where(
            OrganizationalActionOutput.output_key == austria_specialist_output_key(child.id)
        )
    ).one()
    return (
        output,
        _json_object(output.output_json, label=f"{position_key} K.1 output"),
        _json_object(output.impact_json, label=f"{position_key} K.1 impact"),
    )


def _lineage_fingerprint(output: OrganizationalActionOutput) -> str:
    return canonical_fingerprint(
        {
            "id": output.id,
            "work_item_id": output.work_item_id,
            "accountable_position_key": output.accountable_position_key,
            "status": output.status,
            "confidence": output.confidence,
            "evidence_json": output.evidence_json,
            "impact_json": output.impact_json,
            "output_json": output.output_json,
        }
    )


def _specialist_reference(
    output: OrganizationalActionOutput,
    payload: dict[str, Any],
    *,
    position_key: str,
) -> dict[str, Any]:
    return {
        "position_key": position_key,
        "work_item_id": str(output.work_item_id),
        "action_output_id": str(output.id),
        "lineage_fingerprint": _lineage_fingerprint(output),
        "execution_attempt_id": payload.get("execution_attempt_id"),
        "agent_run_id": payload.get("agent_run_id"),
        "context_hash": payload.get("context_hash"),
        "runtime_binding_hash": payload.get("runtime_binding_hash"),
        "latency_ms": int(payload.get("latency_ms", 0)),
        "retry_count": int(payload.get("retry_count", 0)),
    }


def _active_blockers(
    session: Session,
    *,
    tenant_key: str,
    work_item_ids: list[UUID],
) -> list[OrganizationBlocker]:
    return list(
        session.exec(
            select(OrganizationBlocker)
            .where(
                OrganizationBlocker.tenant_key == tenant_key,
                OrganizationBlocker.work_item_id.in_(work_item_ids),
                OrganizationBlocker.status.in_([
                    OrganizationBlockerStatus.open,
                    OrganizationBlockerStatus.mitigated,
                ]),
            )
            .order_by(OrganizationBlocker.created_at)
        ).all()
    )


def _owner_output_rows(session: Session, root_work_item_id: UUID) -> list[OrganizationalActionOutput]:
    return list(
        session.exec(
            select(OrganizationalActionOutput).where(
                OrganizationalActionOutput.output_key == austria_owner_synthesis_output_key(root_work_item_id)
            )
        ).all()
    )


def _owner_activity_rows(session: Session, root_work_item_id: UUID) -> list[OrganizationActivity]:
    return list(
        session.exec(
            select(OrganizationActivity).where(
                OrganizationActivity.activity_key == austria_owner_synthesis_activity_key(root_work_item_id)
            )
        ).all()
    )


def _validate_owner_synthesis(
    session: Session,
    *,
    root: OrganizationalWorkItem,
    children: dict[str, OrganizationalWorkItem],
    output: OrganizationalActionOutput,
) -> tuple[dict[str, Any], dict[str, Any], OrganizationActivity]:
    if root.status != "completed":
        raise DependencyConflict("L.1 owner synthesis exists but the objective root is not completed")
    if (
        output.work_item_id != root.id
        or output.accountable_position_key != AUSTRIA_MOBILITY_OBJECTIVE_OWNER_POSITION
        or output.status != "completed"
    ):
        raise DependencyConflict("L.1 owner synthesis output has invalid root/owner provenance")
    payload = _json_object(output.output_json, label="L.1 owner synthesis output")
    impact = _json_object(output.impact_json, label="L.1 owner synthesis impact")
    if payload.get("contract_version") != AUSTRIA_LIVE_ORGANIZATION_CONTRACT_VERSION:
        raise DependencyConflict("L.1 owner synthesis has the wrong contract version")
    if (
        payload.get("root_work_item_id") != str(root.id)
        or payload.get("objective_key") != root.objective_key
        or payload.get("owner_position_key") != AUSTRIA_MOBILITY_OBJECTIVE_OWNER_POSITION
    ):
        raise DependencyConflict("L.1 owner synthesis has invalid objective/owner provenance")
    if (
        payload.get("provider_model_authority") is not False
        or payload.get("external_action_authorized") is not False
        or impact.get("external_action_authorized") is not False
        or impact.get("human_review_required") is not True
    ):
        raise DependencyConflict("L.1 owner synthesis exceeds the bounded internal authority")

    current_refs: list[dict[str, Any]] = []
    for position_key in AUSTRIA_MOBILITY_SPECIALIST_POSITIONS:
        specialist_output, specialist_payload, _ = _current_output(
            session,
            root=root,
            child=children[position_key],
            position_key=position_key,
        )
        current_refs.append(
            _specialist_reference(specialist_output, specialist_payload, position_key=position_key)
        )
    if payload.get("specialist_outputs") != current_refs:
        raise DependencyConflict("L.1 owner synthesis is stale for the current specialist execution lineage")

    activities = _owner_activity_rows(session, root.id)
    if len(activities) != 1:
        raise DependencyConflict(f"L.1 owner synthesis requires exactly one owner Activity; found {len(activities)}")
    activity = activities[0]
    if (
        activity.work_item_id != root.id
        or activity.source_object_type != "organizational_action_output"
        or activity.source_object_id != str(output.id)
        or activity.actor_id != AUSTRIA_MOBILITY_OBJECTIVE_OWNER_POSITION
        or activity.position_key != AUSTRIA_MOBILITY_OBJECTIVE_OWNER_POSITION
        or activity.activity_class is not OrganizationActivityClass.decision
    ):
        raise DependencyConflict("L.1 owner Activity has invalid owner/output provenance")
    return payload, impact, activity


def synthesize_austria_objective_owner(
    session: Session,
    *,
    tenant_key: str,
    root_work_item_id: UUID,
) -> AustriaOwnerSynthesisResult:
    """Complete one bounded owner-led Austria organization cycle from accepted K.1 evidence.

    The owner synthesis is deterministic, internal and review-gated. It does not claim an
    immigration/legal outcome and does not execute an external action. Persistent employee
    identity comes from the canonical mobility_operations_lead position rather than a model.
    """

    root, children = _canonical_objective(
        session,
        tenant_key=tenant_key,
        root_work_item_id=root_work_item_id,
    )
    existing = _owner_output_rows(session, root.id)
    if len(existing) > 1:
        raise DependencyConflict("multiple current L.1 owner synthesis outputs exist")
    if existing:
        payload, _, activity = _validate_owner_synthesis(
            session,
            root=root,
            children=children,
            output=existing[0],
        )
        return AustriaOwnerSynthesisResult(
            root_work_item_id=root.id,
            action_output_id=existing[0].id,
            activity_id=activity.id,
            disposition=str(payload["disposition"]),
            replayed=True,
        )
    if root.status == "completed":
        raise DependencyConflict("completed Austria objective root lacks L.1 owner synthesis evidence")

    readiness = austria_objective_readiness(
        session,
        tenant_key=tenant_key,
        root_work_item_id=root.id,
    )
    if not readiness.ready_for_owner_synthesis:
        detail = "; ".join(readiness.reasons) or "required K.1 execution evidence is incomplete"
        raise DependencyConflict(f"Austria objective is not ready for L.1 owner synthesis: {detail}")

    work_item_ids = [root.id, *(child.id for child in children.values())]
    blockers = _active_blockers(session, tenant_key=tenant_key, work_item_ids=work_item_ids)
    if blockers:
        raise DependencyConflict(
            "Austria objective has active blocker(s): " + ", ".join(blocker.title for blocker in blockers)
        )

    specialist_refs: list[dict[str, Any]] = []
    specialist_outputs: list[OrganizationalActionOutput] = []
    for position_key in AUSTRIA_MOBILITY_SPECIALIST_POSITIONS:
        specialist_output, specialist_payload, _ = _current_output(
            session,
            root=root,
            child=children[position_key],
            position_key=position_key,
        )
        specialist_outputs.append(specialist_output)
        specialist_refs.append(
            _specialist_reference(specialist_output, specialist_payload, position_key=position_key)
        )

    total_latency_ms = sum(int(item["latency_ms"]) for item in specialist_refs)
    max_latency_ms = max(int(item["latency_ms"]) for item in specialist_refs)
    total_retry_count = sum(int(item["retry_count"]) for item in specialist_refs)
    combined_confidence = min(float(output.confidence) for output in specialist_outputs)
    disposition = "ready_for_human_review"
    recommendation = (
        "Advance the bounded Austria shortage-occupation objective to Human review using both "
        "current specialist analyses and their durable execution lineage. No legal, authority, "
        "client-facing or external action is authorized by this synthesis."
    )
    output_payload = {
        "contract_version": AUSTRIA_LIVE_ORGANIZATION_CONTRACT_VERSION,
        "root_work_item_id": str(root.id),
        "objective_key": root.objective_key,
        "owner_position_key": AUSTRIA_MOBILITY_OBJECTIVE_OWNER_POSITION,
        "disposition": disposition,
        "recommendation": recommendation,
        "specialist_outputs": specialist_refs,
        "provider_model_authority": False,
        "external_action_authorized": False,
        "human_review_required": True,
        "total_latency_ms": total_latency_ms,
        "max_latency_ms": max_latency_ms,
        "total_retry_count": total_retry_count,
    }
    evidence = [
        {
            "type": "organizational_action_output",
            "position_key": item["position_key"],
            "id": item["action_output_id"],
            "lineage_fingerprint": item["lineage_fingerprint"],
        }
        for item in specialist_refs
    ]
    impact = {
        "client_facing": False,
        "external_action_authorized": False,
        "human_review_required": True,
        "workflow_effect": "owner_synthesis_recorded_and_objective_completed",
        "blocked_actions": [
            "authority_submission",
            "client_send",
            "external_provider_action",
            "payment_initiation",
            "contract_signing",
            "policy_publication",
        ],
    }
    output = OrganizationalActionOutput(
        output_key=austria_owner_synthesis_output_key(root.id),
        work_item_id=root.id,
        accountable_position_key=AUSTRIA_MOBILITY_OBJECTIVE_OWNER_POSITION,
        authority_basis=(
            "L.1 bounded internal owner synthesis over current K.1 specialist evidence. "
            "Persistent OrganizationPosition authority is canonical; provider/model identity is non-authorizing."
        ),
        evidence_json=_json_dump(evidence),
        confidence=combined_confidence,
        confidence_basis="Minimum confidence across both current provenance-valid specialist outputs.",
        impact_json=_json_dump(impact),
        rollback_posture=(
            "Discard the internal owner synthesis and reopen through an explicit later recovery contract; "
            "no external side effect occurred."
        ),
        output_json=_json_dump(output_payload),
        status="completed",
    )
    session.add(output)
    session.flush()

    owner_context = system_bound_agent_command_context(
        tenant_key=tenant_key,
        position_key=AUSTRIA_MOBILITY_OBJECTIVE_OWNER_POSITION,
        department=root.department,
        authority_level=root.authority_level,
        correlation_key=f"l1:austria:{root.id}",
    )
    activity = stage_activity(
        session,
        owner_context,
        activity_key=austria_owner_synthesis_activity_key(root.id),
        stream_key=f"organization:mobility-objective:{root.id}",
        activity_class=OrganizationActivityClass.decision,
        activity_type=AUSTRIA_LIVE_ORGANIZATION_ACTIVITY_TYPE,
        title="Austria mobility objective owner synthesis completed",
        summary=(
            "The Mobility Operations Lead synthesized both current specialist outputs into a bounded "
            "Human-review recommendation with no external-action authority."
        ),
        source_object_type="organizational_action_output",
        source_object_id=str(output.id),
        source_object_version=AUSTRIA_LIVE_ORGANIZATION_CONTRACT_VERSION,
        work_item_id=root.id,
        occurred_at=now_utc(),
        payload={
            "constitutional_activity_class": "MATERIAL",
            "contract_version": AUSTRIA_LIVE_ORGANIZATION_CONTRACT_VERSION,
            "disposition": disposition,
            "specialist_output_ids": [item["action_output_id"] for item in specialist_refs],
            "human_review_required": True,
            "external_action_authorized": False,
            "provider_model_authority": False,
        },
    )
    record_audit(
        session,
        action="austria_owner_synthesis_recorded",
        entity_type="organizational_action_output",
        entity_id=output.id,
        after_state={
            "root_work_item_id": str(root.id),
            "owner_position_key": AUSTRIA_MOBILITY_OBJECTIVE_OWNER_POSITION,
            "disposition": disposition,
            "specialist_output_ids": [item["action_output_id"] for item in specialist_refs],
            "external_action_authorized": False,
        },
        actor=AUSTRIA_MOBILITY_OBJECTIVE_OWNER_POSITION,
        source=SOURCE,
    )

    completed_root = complete_work_item(
        session,
        owner_context,
        work_item_id=root.id,
        reason="L.1 owner synthesis completed from both current K.1 specialist outputs.",
    )
    if completed_root.status != "completed":
        raise DependencyConflict("L.1 owner synthesis did not complete the objective root")
    session.refresh(output)
    session.refresh(activity)
    return AustriaOwnerSynthesisResult(
        root_work_item_id=root.id,
        action_output_id=output.id,
        activity_id=activity.id,
        disposition=disposition,
        replayed=False,
    )


def _specialist_snapshot(
    session: Session,
    *,
    root: OrganizationalWorkItem,
    child: OrganizationalWorkItem,
    position_key: str,
) -> AustriaLiveSpecialistSnapshot:
    outputs = session.exec(
        select(OrganizationalActionOutput).where(
            OrganizationalActionOutput.output_key == austria_specialist_output_key(child.id)
        )
    ).all()
    reason = _specialist_execution_evidence_reason(
        session,
        root=root,
        child=child,
        position_key=position_key,
    ) if child.status == "completed" else f"{position_key} work is {child.status}, not completed"
    if len(outputs) != 1:
        return AustriaLiveSpecialistSnapshot(
            position_key=position_key,
            work_item_id=child.id,
            status=child.status,
            evidence_valid=False,
            evidence_reason=reason,
            action_output_id=None,
            execution_attempt_id=None,
            agent_run_id=None,
            context_hash=None,
            runtime_binding_hash=None,
            latency_ms=None,
            retry_count=None,
            confidence=None,
            provider_model_authority=False,
            external_action_authorized=False,
        )
    output = outputs[0]
    try:
        payload = _json_object(output.output_json, label=f"{position_key} K.1 output")
        impact = _json_object(output.impact_json, label=f"{position_key} K.1 impact")
    except DependencyConflict:
        payload = {}
        impact = {}
    def _uuid(key: str) -> UUID | None:
        value = payload.get(key)
        try:
            return UUID(str(value)) if value else None
        except ValueError:
            return None
    latency = payload.get("latency_ms")
    retry = payload.get("retry_count")
    return AustriaLiveSpecialistSnapshot(
        position_key=position_key,
        work_item_id=child.id,
        status=child.status,
        evidence_valid=reason is None,
        evidence_reason=reason,
        action_output_id=output.id,
        execution_attempt_id=_uuid("execution_attempt_id"),
        agent_run_id=_uuid("agent_run_id"),
        context_hash=str(payload["context_hash"]) if payload.get("context_hash") else None,
        runtime_binding_hash=(
            str(payload["runtime_binding_hash"]) if payload.get("runtime_binding_hash") else None
        ),
        latency_ms=int(latency) if isinstance(latency, int) and latency >= 0 else None,
        retry_count=int(retry) if isinstance(retry, int) and retry >= 0 else None,
        confidence=float(output.confidence),
        provider_model_authority=payload.get("provider_model_authority") is True,
        external_action_authorized=impact.get("external_action_authorized") is True,
    )


def austria_live_organization_snapshot(
    session: Session,
    *,
    tenant_key: str,
    root_work_item_id: UUID,
) -> AustriaLiveOrganizationSnapshot:
    root, children = _canonical_objective(
        session,
        tenant_key=tenant_key,
        root_work_item_id=root_work_item_id,
    )
    owner_rows = _owner_output_rows(session, root.id)
    if len(owner_rows) > 1:
        raise DependencyConflict("multiple current L.1 owner synthesis outputs exist")

    owner_snapshot: AustriaOwnerSynthesisSnapshot | None = None
    if owner_rows:
        payload, impact, activity = _validate_owner_synthesis(
            session,
            root=root,
            children=children,
            output=owner_rows[0],
        )
        owner_snapshot = AustriaOwnerSynthesisSnapshot(
            action_output_id=owner_rows[0].id,
            activity_id=activity.id,
            disposition=str(payload.get("disposition", "unknown")),
            recommendation=str(payload.get("recommendation", "")),
            confidence=float(owner_rows[0].confidence),
            total_latency_ms=int(payload.get("total_latency_ms", 0)),
            max_latency_ms=int(payload.get("max_latency_ms", 0)),
            total_retry_count=int(payload.get("total_retry_count", 0)),
            external_action_authorized=impact.get("external_action_authorized") is True,
            human_review_required=impact.get("human_review_required") is True,
            completed_at=root.completed_at,
        )
        ready = False
        readiness_reasons: tuple[str, ...] = ()
        owner_state = "completed"
    elif root.status == "completed":
        raise DependencyConflict("completed Austria objective root lacks L.1 owner synthesis evidence")
    else:
        readiness = austria_objective_readiness(
            session,
            tenant_key=tenant_key,
            root_work_item_id=root.id,
        )
        ready = readiness.ready_for_owner_synthesis
        readiness_reasons = readiness.reasons
        owner_state = "ready" if ready else "not_ready"

    specialist_snapshots = tuple(
        _specialist_snapshot(
            session,
            root=root,
            child=children[position_key],
            position_key=position_key,
        )
        for position_key in AUSTRIA_MOBILITY_SPECIALIST_POSITIONS
    )
    ids = [root.id, *(child.id for child in children.values())]
    blockers = _active_blockers(session, tenant_key=tenant_key, work_item_ids=ids)
    blocker_snapshots = tuple(
        AustriaLiveBlockerSnapshot(
            blocker_id=blocker.id,
            work_item_id=blocker.work_item_id,
            blocker_type=blocker.blocker_type.value,
            severity=blocker.severity,
            status=blocker.status.value,
            title=blocker.title,
            description=blocker.description,
            accountable_position_key=blocker.accountable_position_key,
            requires_human_action=blocker.requires_human_action,
            created_at=blocker.created_at,
        )
        for blocker in blockers
    )

    activities: list[TransparencyActivityRecord] = []
    for work_item_id in ids:
        activities.extend(
            activities_for_work_item(session, tenant_key=tenant_key, work_item_id=work_item_id)
        )
    activities.sort(key=lambda item: (item.occurred_at, str(item.activity_id)))

    total_latency_ms = sum(item.latency_ms or 0 for item in specialist_snapshots)
    max_latency_ms = max((item.latency_ms or 0 for item in specialist_snapshots), default=0)
    total_retry_count = sum(item.retry_count or 0 for item in specialist_snapshots)
    if owner_snapshot is not None:
        cycle_status = "completed"
    elif blockers:
        cycle_status = "blocked"
    elif ready:
        cycle_status = "ready_for_owner_synthesis"
    elif any(item.status == "running" for item in specialist_snapshots):
        cycle_status = "specialist_execution_in_progress"
    else:
        cycle_status = "awaiting_specialist_execution"

    return AustriaLiveOrganizationSnapshot(
        generated_at=now_utc(),
        root_work_item_id=root.id,
        objective_key=root.objective_key,
        owner_position_key=AUSTRIA_MOBILITY_OBJECTIVE_OWNER_POSITION,
        root_status=root.status,
        cycle_status=cycle_status,
        owner_synthesis_state=owner_state,
        ready_for_owner_synthesis=ready,
        readiness_reasons=readiness_reasons,
        authority_level=root.authority_level,
        authority_posture="internal_analysis_review_gated",
        autonomy_profile_state=None,
        provider_model_authority=False,
        external_action_authorized=False,
        specialist_outputs=specialist_snapshots,
        owner_synthesis=owner_snapshot,
        blockers=blocker_snapshots,
        total_latency_ms=total_latency_ms,
        max_latency_ms=max_latency_ms,
        total_retry_count=total_retry_count,
        activity_count=len(activities),
        activities=tuple(activities),
        domain_evidence_refs=(),
        verified_rule_refs=(),
    )


def latest_austria_live_organization_snapshot(
    session: Session,
    *,
    tenant_key: str,
) -> AustriaLiveOrganizationSnapshot | None:
    root = session.exec(
        select(OrganizationalWorkItem)
        .where(
            OrganizationalWorkItem.tenant_key == tenant_key,
            OrganizationalWorkItem.work_type == "mobility_objective",
            OrganizationalWorkItem.phase_key == "J.1",
            OrganizationalWorkItem.assigned_position_key == AUSTRIA_MOBILITY_OBJECTIVE_OWNER_POSITION,
            OrganizationalWorkItem.parent_work_item_id.is_(None),
        )
        .order_by(OrganizationalWorkItem.created_at.desc())
        .limit(1)
    ).first()
    if root is None:
        return None
    return austria_live_organization_snapshot(
        session,
        tenant_key=tenant_key,
        root_work_item_id=root.id,
    )
