from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    OrganizationActivity,
    OrganizationActivityClass,
    OrganizationActorType,
    now_utc,
)
from app.services.organization_activity import stage_activity
from app.services.organization_command import OrganizationCommandContext, canonical_fingerprint, require_human
from app.services.organization_transparency import TransparencyDataError, transparency_activity_record


ELIGIBILITY_IMMUNE_SYSTEM_SCHEMA_VERSION = "eligibility-immune-system.v1"
ELIGIBILITY_IMMUNE_CAPABILITY = "mobility.eligibility"
ELIGIBILITY_IMMUNE_INCIDENT_ACTIVITY_TYPE = "organization.immune.eligibility_incident.v1"
ELIGIBILITY_IMMUNE_CIRCUIT_OPEN_ACTIVITY_TYPE = "organization.immune.eligibility_circuit_opened.v1"
ELIGIBILITY_IMMUNE_CIRCUIT_CLOSED_ACTIVITY_TYPE = "organization.immune.eligibility_circuit_closed.v1"


class EligibilityImmuneSystemError(RuntimeError):
    """Base error for the bounded H.1 eligibility immune-system slice."""


class EligibilityCircuitOpen(EligibilityImmuneSystemError):
    """The governed eligibility capability is circuit-broken for this aggregate."""


class EligibilityCircuitRecoveryError(EligibilityImmuneSystemError):
    """A circuit recovery command is invalid or insufficiently authorized."""


class EligibilityImmuneIncidentKind(str, Enum):
    CANONICAL_AGGREGATE_INTEGRITY = "canonical_aggregate_integrity"
    DURABLE_LINEAGE_INTEGRITY = "durable_lineage_integrity"
    RUNTIME_HEALTH_FAILURE = "runtime_health_failure"
    REVISION_CONFLICT = "revision_conflict"
    VERIFIER_DISAGREEMENT = "verifier_disagreement"
    REASSESSMENT_ROLLBACK = "reassessment_rollback"


class EligibilityImmuneIncidentSeverity(str, Enum):
    WARNING = "warning"
    CRITICAL = "critical"


class EligibilityCircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"


@dataclass(frozen=True)
class EligibilityCircuitStatus:
    schema_version: str
    tenant_key: str
    aggregate_key: str
    capability: str
    state: EligibilityCircuitState
    control_activity_id: UUID | None
    cause_incident_activity_id: UUID | None


@dataclass(frozen=True)
class EligibilityImmuneIncidentResult:
    schema_version: str
    incident_activity: OrganizationActivity
    severity: EligibilityImmuneIncidentSeverity
    circuit_status: EligibilityCircuitStatus
    circuit_opened: bool
    replayed: bool


def eligibility_immune_system_context(
    *,
    tenant_key: str,
    correlation_key: str | None = None,
) -> OrganizationCommandContext:
    """Return the infrastructure actor used only to reduce eligibility execution.

    This context never creates CapabilityAuthority and never grants autonomy. The
    infrastructure actor may append an incident and open a circuit because both actions
    are restrictive. Circuit recovery is intentionally excluded and requires an
    authenticated human admin through ``close_eligibility_circuit``.
    """

    return OrganizationCommandContext(
        tenant_key=tenant_key,
        actor_id="organization-immune-system",
        actor_type=OrganizationActorType.system,
        authenticated_user_id="system",
        role="operator",
        department="Governance",
        position_key=None,
        authority_level=None,
        correlation_key=correlation_key,
    )


def _severity(kind: EligibilityImmuneIncidentKind) -> EligibilityImmuneIncidentSeverity:
    if kind in {
        EligibilityImmuneIncidentKind.CANONICAL_AGGREGATE_INTEGRITY,
        EligibilityImmuneIncidentKind.DURABLE_LINEAGE_INTEGRITY,
    }:
        return EligibilityImmuneIncidentSeverity.CRITICAL
    return EligibilityImmuneIncidentSeverity.WARNING


def _stream_key(aggregate_key: str) -> str:
    return f"immune:eligibility:{aggregate_key}"


def _control_activities(
    session: Session,
    *,
    tenant_key: str,
    aggregate_key: str,
) -> tuple[OrganizationActivity, ...]:
    return tuple(
        session.exec(
            select(OrganizationActivity)
            .where(
                OrganizationActivity.tenant_key == tenant_key,
                OrganizationActivity.source_object_type == "eligibility_aggregate",
                OrganizationActivity.source_object_id == aggregate_key,
                OrganizationActivity.activity_type.in_(
                    [
                        ELIGIBILITY_IMMUNE_CIRCUIT_OPEN_ACTIVITY_TYPE,
                        ELIGIBILITY_IMMUNE_CIRCUIT_CLOSED_ACTIVITY_TYPE,
                    ]
                ),
            )
            .order_by(OrganizationActivity.stream_sequence.desc())
        ).all()
    )


def eligibility_circuit_status(
    session: Session,
    *,
    tenant_key: str,
    aggregate_key: str,
) -> EligibilityCircuitStatus:
    controls = _control_activities(
        session,
        tenant_key=tenant_key,
        aggregate_key=aggregate_key,
    )
    if not controls:
        return EligibilityCircuitStatus(
            schema_version=ELIGIBILITY_IMMUNE_SYSTEM_SCHEMA_VERSION,
            tenant_key=tenant_key,
            aggregate_key=aggregate_key,
            capability=ELIGIBILITY_IMMUNE_CAPABILITY,
            state=EligibilityCircuitState.CLOSED,
            control_activity_id=None,
            cause_incident_activity_id=None,
        )

    current = controls[0]
    state = (
        EligibilityCircuitState.OPEN
        if current.activity_type == ELIGIBILITY_IMMUNE_CIRCUIT_OPEN_ACTIVITY_TYPE
        else EligibilityCircuitState.CLOSED
    )
    cause = current.causation_activity_id if state is EligibilityCircuitState.OPEN else None
    return EligibilityCircuitStatus(
        schema_version=ELIGIBILITY_IMMUNE_SYSTEM_SCHEMA_VERSION,
        tenant_key=tenant_key,
        aggregate_key=aggregate_key,
        capability=ELIGIBILITY_IMMUNE_CAPABILITY,
        state=state,
        control_activity_id=current.id,
        cause_incident_activity_id=cause,
    )


def require_eligibility_circuit_closed(
    session: Session,
    *,
    tenant_key: str,
    aggregate_key: str,
) -> EligibilityCircuitStatus:
    status = eligibility_circuit_status(
        session,
        tenant_key=tenant_key,
        aggregate_key=aggregate_key,
    )
    if status.state is EligibilityCircuitState.OPEN:
        raise EligibilityCircuitOpen(
            "governed eligibility execution is circuit-broken for this canonical aggregate"
        )
    return status


def _matching_existing_incident(
    existing: OrganizationActivity,
    *,
    kind: EligibilityImmuneIncidentKind,
    severity: EligibilityImmuneIncidentSeverity,
    summary: str,
) -> bool:
    try:
        record = transparency_activity_record(existing)
    except TransparencyDataError as exc:
        raise EligibilityImmuneSystemError("persisted eligibility incident Activity is malformed") from exc
    return (
        record.activity_type == ELIGIBILITY_IMMUNE_INCIDENT_ACTIVITY_TYPE
        and existing.summary == summary
        and record.payload.get("incident_kind") == kind.value
        and record.payload.get("severity") == severity.value
    )


def record_eligibility_immune_incident(
    session: Session,
    *,
    tenant_key: str,
    aggregate_key: str,
    incident_key: str,
    kind: EligibilityImmuneIncidentKind | str,
    summary: str,
    source_activity_id: UUID | None = None,
    correlation_key: str | None = None,
) -> EligibilityImmuneIncidentResult:
    """Append one deterministic eligibility incident and open only on critical integrity loss.

    Verifier disagreement, ordinary revision conflicts, runtime-health failures and a
    successfully-contained reassessment rollback are observable warning signals in H.1;
    they do not independently disable the aggregate. Structural canonical-state or
    durable-lineage integrity failures are critical and immediately open the circuit.

    For a new critical incident, the incident Activity and mandatory circuit-open
    Activity are staged and committed as one transaction. An incident can therefore not
    become durable while its required restrictive side effect is lost.
    """

    incident_kind = EligibilityImmuneIncidentKind(kind)
    severity = _severity(incident_kind)
    key = str(incident_key or "").strip()
    if not key:
        raise EligibilityImmuneSystemError("incident_key is required")
    detail = str(summary or "").strip()
    if not detail:
        raise EligibilityImmuneSystemError("incident summary is required")

    context = eligibility_immune_system_context(
        tenant_key=tenant_key,
        correlation_key=correlation_key,
    )
    incident_fingerprint = canonical_fingerprint(
        {
            "schema_version": ELIGIBILITY_IMMUNE_SYSTEM_SCHEMA_VERSION,
            "tenant_key": tenant_key,
            "aggregate_key": aggregate_key,
            "incident_key": key,
            "kind": incident_kind.value,
            "severity": severity.value,
            "summary": detail,
            "source_activity_id": source_activity_id,
        }
    )
    activity_key = f"immune:eligibility:{aggregate_key}:incident:{key}"
    existing = session.exec(
        select(OrganizationActivity).where(
            OrganizationActivity.tenant_key == tenant_key,
            OrganizationActivity.activity_key == activity_key,
        )
    ).first()
    if existing is not None:
        if not _matching_existing_incident(
            existing,
            kind=incident_kind,
            severity=severity,
            summary=detail,
        ):
            raise EligibilityImmuneSystemError(
                "eligibility incident idempotency key conflicts with persisted incident"
            )
        return EligibilityImmuneIncidentResult(
            schema_version=ELIGIBILITY_IMMUNE_SYSTEM_SCHEMA_VERSION,
            incident_activity=existing,
            severity=severity,
            circuit_status=eligibility_circuit_status(
                session,
                tenant_key=tenant_key,
                aggregate_key=aggregate_key,
            ),
            circuit_opened=False,
            replayed=True,
        )

    before = eligibility_circuit_status(
        session,
        tenant_key=tenant_key,
        aggregate_key=aggregate_key,
    )
    circuit_opened = False
    try:
        incident = stage_activity(
            session,
            context,
            activity_key=activity_key,
            stream_key=_stream_key(aggregate_key),
            activity_class=OrganizationActivityClass.blocker,
            activity_type=ELIGIBILITY_IMMUNE_INCIDENT_ACTIVITY_TYPE,
            title="Eligibility immune-system incident",
            summary=detail,
            source_object_type="eligibility_aggregate",
            source_object_id=aggregate_key,
            source_object_version=ELIGIBILITY_IMMUNE_SYSTEM_SCHEMA_VERSION,
            causation_activity_id=source_activity_id,
            occurred_at=now_utc(),
            payload={
                "immune_contract": ELIGIBILITY_IMMUNE_SYSTEM_SCHEMA_VERSION,
                "capability": ELIGIBILITY_IMMUNE_CAPABILITY,
                "aggregate_key": aggregate_key,
                "incident_key": key,
                "incident_kind": incident_kind.value,
                "severity": severity.value,
                "incident_fingerprint": incident_fingerprint,
                "automatic_circuit_action": (
                    "open" if severity is EligibilityImmuneIncidentSeverity.CRITICAL else "none"
                ),
                "authority_effect": "restrict_only",
            },
            correlation_key=correlation_key,
        )

        if (
            severity is EligibilityImmuneIncidentSeverity.CRITICAL
            and before.state is EligibilityCircuitState.CLOSED
        ):
            open_key = f"immune:eligibility:{aggregate_key}:circuit:open:{key}"
            stage_activity(
                session,
                context,
                activity_key=open_key,
                stream_key=_stream_key(aggregate_key),
                activity_class=OrganizationActivityClass.blocker,
                activity_type=ELIGIBILITY_IMMUNE_CIRCUIT_OPEN_ACTIVITY_TYPE,
                title="Eligibility circuit opened",
                summary=(
                    "Governed eligibility execution is disabled for this canonical aggregate "
                    "until an authorized recovery closes the circuit."
                ),
                source_object_type="eligibility_aggregate",
                source_object_id=aggregate_key,
                source_object_version=ELIGIBILITY_IMMUNE_SYSTEM_SCHEMA_VERSION,
                causation_activity_id=incident.id,
                occurred_at=now_utc(),
                payload={
                    "immune_contract": ELIGIBILITY_IMMUNE_SYSTEM_SCHEMA_VERSION,
                    "capability": ELIGIBILITY_IMMUNE_CAPABILITY,
                    "aggregate_key": aggregate_key,
                    "state": EligibilityCircuitState.OPEN.value,
                    "cause_incident_activity_id": str(incident.id),
                    "authority_effect": "restrict_only",
                },
                correlation_key=correlation_key,
            )
            circuit_opened = True

        session.commit()
        session.refresh(incident)
    except Exception:
        session.rollback()
        raise

    return EligibilityImmuneIncidentResult(
        schema_version=ELIGIBILITY_IMMUNE_SYSTEM_SCHEMA_VERSION,
        incident_activity=incident,
        severity=severity,
        circuit_status=eligibility_circuit_status(
            session,
            tenant_key=tenant_key,
            aggregate_key=aggregate_key,
        ),
        circuit_opened=circuit_opened,
        replayed=False,
    )


def close_eligibility_circuit(
    session: Session,
    *,
    context: OrganizationCommandContext,
    aggregate_key: str,
    recovery_key: str,
    reason: str,
) -> EligibilityCircuitStatus:
    """Close one open eligibility circuit through an authenticated human-admin command.

    H.1 deliberately has no automatic recovery. Closing a circuit restores the ability
    to attempt execution, so the first slice requires retained human admin authority.
    It still does not grant CapabilityAuthority, autonomy or permission for any material
    action; downstream governance remains unchanged.
    """

    try:
        require_human(context, admin=True)
    except Exception as exc:
        raise EligibilityCircuitRecoveryError(
            "eligibility circuit recovery requires an authenticated human admin"
        ) from exc

    key = str(recovery_key or "").strip()
    detail = str(reason or "").strip()
    if not key or not detail:
        raise EligibilityCircuitRecoveryError("recovery_key and reason are required")

    activity_key = f"immune:eligibility:{aggregate_key}:circuit:closed:{key}"
    existing = session.exec(
        select(OrganizationActivity).where(
            OrganizationActivity.tenant_key == context.tenant_key,
            OrganizationActivity.activity_key == activity_key,
        )
    ).first()
    if existing is not None:
        if existing.summary != detail:
            raise EligibilityCircuitRecoveryError(
                "eligibility recovery idempotency key conflicts with persisted recovery"
            )
        return eligibility_circuit_status(
            session,
            tenant_key=context.tenant_key,
            aggregate_key=aggregate_key,
        )

    current = eligibility_circuit_status(
        session,
        tenant_key=context.tenant_key,
        aggregate_key=aggregate_key,
    )
    if current.state is not EligibilityCircuitState.OPEN or current.control_activity_id is None:
        raise EligibilityCircuitRecoveryError("eligibility circuit is not currently open")

    try:
        stage_activity(
            session,
            context,
            activity_key=activity_key,
            stream_key=_stream_key(aggregate_key),
            activity_class=OrganizationActivityClass.operational,
            activity_type=ELIGIBILITY_IMMUNE_CIRCUIT_CLOSED_ACTIVITY_TYPE,
            title="Eligibility circuit closed",
            summary=detail,
            source_object_type="eligibility_aggregate",
            source_object_id=aggregate_key,
            source_object_version=ELIGIBILITY_IMMUNE_SYSTEM_SCHEMA_VERSION,
            supersedes_activity_id=current.control_activity_id,
            occurred_at=now_utc(),
            payload={
                "immune_contract": ELIGIBILITY_IMMUNE_SYSTEM_SCHEMA_VERSION,
                "capability": ELIGIBILITY_IMMUNE_CAPABILITY,
                "aggregate_key": aggregate_key,
                "state": EligibilityCircuitState.CLOSED.value,
                "recovery_key": key,
                "reason": detail,
                "restores_execution_attempts_only": True,
                "grants_authority": False,
            },
            correlation_key=context.correlation_key,
        )
        session.commit()
    except Exception:
        session.rollback()
        raise

    return eligibility_circuit_status(
        session,
        tenant_key=context.tenant_key,
        aggregate_key=aggregate_key,
    )
