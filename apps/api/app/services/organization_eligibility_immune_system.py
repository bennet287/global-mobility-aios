from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    MobilityPathwayVersion,
    OrganizationActivity,
    OrganizationActivityClass,
    OrganizationActorType,
    OrganizationalWorkItem,
    now_utc,
)
from app.services.organization_activity import stage_activity
from app.services.organization_command import (
    AuthorityDenied,
    OrganizationCommandContext,
    canonical_fingerprint,
    require_human,
)
from app.services.organization_eligibility_lineage import (
    CanonicalEligibilityLineageError,
    validate_canonical_eligibility_aggregate_lineage,
)
from app.services.organization_eligibility_revision_precondition import eligibility_aggregate_key
from app.services.organization_transparency import TransparencyDataError, transparency_activity_record


ELIGIBILITY_IMMUNE_SYSTEM_SCHEMA_VERSION = "eligibility-immune-system.v1"
ELIGIBILITY_IMMUNE_CAPABILITY = "mobility.eligibility"
ELIGIBILITY_IMMUNE_INCIDENT_ACTIVITY_TYPE = "organization.immune.eligibility_incident.v1"
ELIGIBILITY_IMMUNE_CIRCUIT_OPEN_ACTIVITY_TYPE = "organization.immune.eligibility_circuit_opened.v1"
ELIGIBILITY_IMMUNE_CIRCUIT_CLOSED_ACTIVITY_TYPE = "organization.immune.eligibility_circuit_closed.v1"
ELIGIBILITY_IMMUNE_RECURRENCE_POLICY_VERSION = "eligibility-immune-recurrence.v1"
ELIGIBILITY_VERIFIER_DISAGREEMENT_RECURRENCE_THRESHOLD = 3


class EligibilityImmuneSystemError(RuntimeError):
    """Base error for the bounded eligibility immune-system capability."""


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
class EligibilityCircuitScope:
    schema_version: str
    tenant_key: str
    aggregate_key: str
    proposal_work_item_id: UUID
    lead_id: UUID
    pathway_id: UUID


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


@dataclass(frozen=True)
class _EligibilityWarningRecurrenceState:
    observed_count: int
    threshold: int
    epoch_boundary_activity_id: UUID | None


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


def eligibility_circuit_scope_for_work_item(
    session: Session,
    *,
    tenant_key: str,
    proposal_work_item_id: UUID,
    producer_position_key: str,
) -> EligibilityCircuitScope:
    """Resolve the stable eligibility aggregate for G.4 circuit preflight.

    This helper is deliberately read-only and authorization-neutral. It verifies that
    the proposal WorkItem belongs to the tenant and trusted producer position, then
    resolves only enough canonical identity to derive the same aggregate key used by
    G.3/G.5. Full ContextBundle, Evidence, rule, profile, runtime and authority checks
    remain mandatory in E.2 and later stages.
    """

    tenant = str(tenant_key or "").strip()
    producer_position = str(producer_position_key or "").strip()
    if not tenant or not producer_position:
        raise EligibilityImmuneSystemError(
            "tenant_key and producer_position_key are required for eligibility circuit scope"
        )

    work_item = session.get(OrganizationalWorkItem, proposal_work_item_id)
    if work_item is None or work_item.tenant_key != tenant:
        raise EligibilityImmuneSystemError(
            "proposal WorkItem is unavailable in the supplied tenant for eligibility circuit scope"
        )
    if work_item.assigned_position_key != producer_position:
        raise EligibilityImmuneSystemError(
            "proposal WorkItem is not assigned to the trusted producer position"
        )
    if work_item.lead_id is None:
        raise EligibilityImmuneSystemError(
            "proposal WorkItem has no Lead for eligibility circuit scope"
        )
    if work_item.source_object_type != "mobility_pathway_version" or not work_item.source_object_id:
        raise EligibilityImmuneSystemError(
            "proposal WorkItem does not identify a mobility_pathway_version"
        )

    try:
        pathway_version_id = UUID(str(work_item.source_object_id))
    except (TypeError, ValueError, AttributeError) as exc:
        raise EligibilityImmuneSystemError(
            "proposal WorkItem pathway-version source identity is invalid"
        ) from exc
    pathway_version = session.get(MobilityPathwayVersion, pathway_version_id)
    if pathway_version is None:
        raise EligibilityImmuneSystemError(
            "proposal WorkItem pathway-version source could not be resolved"
        )

    aggregate = eligibility_aggregate_key(
        tenant_key=tenant,
        lead_id=work_item.lead_id,
        pathway_id=pathway_version.pathway_id,
    )
    return EligibilityCircuitScope(
        schema_version=ELIGIBILITY_IMMUNE_SYSTEM_SCHEMA_VERSION,
        tenant_key=tenant,
        aggregate_key=aggregate,
        proposal_work_item_id=work_item.id,
        lead_id=work_item.lead_id,
        pathway_id=pathway_version.pathway_id,
    )


def _severity(kind: EligibilityImmuneIncidentKind) -> EligibilityImmuneIncidentSeverity:
    if kind in {
        EligibilityImmuneIncidentKind.CANONICAL_AGGREGATE_INTEGRITY,
        EligibilityImmuneIncidentKind.DURABLE_LINEAGE_INTEGRITY,
    }:
        return EligibilityImmuneIncidentSeverity.CRITICAL
    return EligibilityImmuneIncidentSeverity.WARNING


def _recurrence_threshold(kind: EligibilityImmuneIncidentKind) -> int | None:
    if kind is EligibilityImmuneIncidentKind.VERIFIER_DISAGREEMENT:
        return ELIGIBILITY_VERIFIER_DISAGREEMENT_RECURRENCE_THRESHOLD
    return None


def _validated_scope(*, tenant_key: str, aggregate_key: str) -> tuple[str, str]:
    tenant = str(tenant_key or "").strip()
    aggregate = str(aggregate_key or "").strip()
    if not tenant or not aggregate:
        raise EligibilityImmuneSystemError("tenant_key and eligibility aggregate_key are required")
    if not aggregate.startswith(f"eligibility:{tenant}:"):
        raise EligibilityImmuneSystemError(
            "eligibility aggregate key does not belong to the supplied tenant"
        )
    return tenant, aggregate


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


def _latest_recovery_boundary(
    session: Session,
    *,
    tenant_key: str,
    aggregate_key: str,
) -> OrganizationActivity | None:
    for activity in _control_activities(
        session,
        tenant_key=tenant_key,
        aggregate_key=aggregate_key,
    ):
        if activity.activity_type == ELIGIBILITY_IMMUNE_CIRCUIT_CLOSED_ACTIVITY_TYPE:
            return activity
    return None


def _warning_recurrence_state(
    session: Session,
    *,
    tenant_key: str,
    aggregate_key: str,
    kind: EligibilityImmuneIncidentKind,
) -> _EligibilityWarningRecurrenceState | None:
    """Count one supported warning kind in the current human-recovery epoch.

    ``stage_activity`` has already staged/flushed the new incident before this helper is
    called. On PostgreSQL that same staging operation locks the aggregate Activity stream,
    so concurrent warning writers serialize before recurrence is evaluated.
    """

    threshold = _recurrence_threshold(kind)
    if threshold is None:
        return None

    boundary = _latest_recovery_boundary(
        session,
        tenant_key=tenant_key,
        aggregate_key=aggregate_key,
    )
    statement = select(OrganizationActivity).where(
        OrganizationActivity.tenant_key == tenant_key,
        OrganizationActivity.source_object_type == "eligibility_aggregate",
        OrganizationActivity.source_object_id == aggregate_key,
        OrganizationActivity.activity_type == ELIGIBILITY_IMMUNE_INCIDENT_ACTIVITY_TYPE,
    )
    if boundary is not None:
        statement = statement.where(
            OrganizationActivity.stream_sequence > boundary.stream_sequence
        )
    rows = session.exec(statement.order_by(OrganizationActivity.stream_sequence)).all()

    observed = 0
    for row in rows:
        try:
            record = transparency_activity_record(row)
        except TransparencyDataError as exc:
            raise EligibilityImmuneSystemError(
                "persisted eligibility incident Activity is malformed during recurrence evaluation"
            ) from exc
        if (
            record.payload.get("incident_kind") == kind.value
            and record.payload.get("severity") == EligibilityImmuneIncidentSeverity.WARNING.value
        ):
            observed += 1

    return _EligibilityWarningRecurrenceState(
        observed_count=observed,
        threshold=threshold,
        epoch_boundary_activity_id=boundary.id if boundary is not None else None,
    )


def eligibility_circuit_status(
    session: Session,
    *,
    tenant_key: str,
    aggregate_key: str,
) -> EligibilityCircuitStatus:
    tenant, aggregate = _validated_scope(
        tenant_key=tenant_key,
        aggregate_key=aggregate_key,
    )
    controls = _control_activities(
        session,
        tenant_key=tenant,
        aggregate_key=aggregate,
    )
    if not controls:
        return EligibilityCircuitStatus(
            schema_version=ELIGIBILITY_IMMUNE_SYSTEM_SCHEMA_VERSION,
            tenant_key=tenant,
            aggregate_key=aggregate,
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
        tenant_key=tenant,
        aggregate_key=aggregate,
        capability=ELIGIBILITY_IMMUNE_CAPABILITY,
        state=state,
        control_activity_id=current.id,
        cause_incident_activity_id=cause,
    )


def _existing_tenant_activity_id(
    session: Session,
    *,
    tenant_key: str,
    activity_id: UUID | None,
) -> UUID | None:
    if activity_id is None:
        return None
    activity = session.get(OrganizationActivity, activity_id)
    if activity is None or activity.tenant_key != tenant_key:
        return None
    return activity.id


def _eligibility_lineage_integrity_problem(
    session: Session,
    *,
    tenant_key: str,
    aggregate_key: str,
) -> tuple[EligibilityImmuneIncidentKind, str, UUID | None, str] | None:
    """Translate the canonical lineage validator into one restrictive H.1 signal."""

    try:
        validate_canonical_eligibility_aggregate_lineage(
            session,
            tenant_key=tenant_key,
            aggregate_key=aggregate_key,
        )
    except CanonicalEligibilityLineageError as exc:
        kind = (
            EligibilityImmuneIncidentKind.CANONICAL_AGGREGATE_INTEGRITY
            if exc.integrity_scope == "aggregate"
            else EligibilityImmuneIncidentKind.DURABLE_LINEAGE_INTEGRITY
        )
        summary = (
            "Canonical eligibility aggregate integrity is inconsistent; governed execution is disabled pending recovery."
            if kind is EligibilityImmuneIncidentKind.CANONICAL_AGGREGATE_INTEGRITY
            else "Canonical eligibility durable lineage is inconsistent; governed execution is disabled pending recovery."
        )
        return (
            kind,
            summary,
            _existing_tenant_activity_id(
                session,
                tenant_key=tenant_key,
                activity_id=exc.source_activity_id,
            ),
            exc.fingerprint,
        )
    return None


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

    problem = _eligibility_lineage_integrity_problem(
        session,
        tenant_key=status.tenant_key,
        aggregate_key=status.aggregate_key,
    )
    if problem is not None:
        kind, summary, source_activity_id, problem_fingerprint = problem
        control_marker = (
            str(status.control_activity_id) if status.control_activity_id is not None else "none"
        )
        incident = record_eligibility_immune_incident(
            session,
            tenant_key=status.tenant_key,
            aggregate_key=status.aggregate_key,
            incident_key=(
                f"preflight:{kind.value}:{control_marker}:{problem_fingerprint}"
            ),
            kind=kind,
            summary=summary,
            source_activity_id=source_activity_id,
        )
        if incident.circuit_status.state is not EligibilityCircuitState.OPEN:
            raise EligibilityImmuneSystemError(
                "critical eligibility integrity incident failed to restrict execution"
            )
        raise EligibilityCircuitOpen(
            "governed eligibility execution is circuit-broken by structural canonical integrity loss"
        )

    return status


def _matching_existing_incident(
    existing: OrganizationActivity,
    *,
    kind: EligibilityImmuneIncidentKind,
    severity: EligibilityImmuneIncidentSeverity,
    summary: str,
    incident_fingerprint: str,
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
        and record.payload.get("incident_fingerprint") == incident_fingerprint
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
    """Append one deterministic eligibility incident and apply restrictive policy.

    Structural canonical-state or durable-lineage integrity failures are critical and
    immediately open the circuit under H.1. Runtime-health failures, ordinary revision
    conflicts, verifier disagreement and successfully-contained reassessment rollback
    remain warning signals.

    H.2.1 adds exactly one warning recurrence policy: the third verifier disagreement
    in the current recovery epoch opens the aggregate circuit. The individual incident
    remains WARNING; the repeated pattern causes the restrictive control transition.
    Other warning kinds remain observation-only in this slice.

    When policy requires an open, the incident Activity and circuit-open Activity are
    staged and committed as one transaction. An incident therefore cannot become durable
    while its required restrictive side effect is lost.
    """

    tenant, aggregate = _validated_scope(
        tenant_key=tenant_key,
        aggregate_key=aggregate_key,
    )
    incident_kind = EligibilityImmuneIncidentKind(kind)
    severity = _severity(incident_kind)
    recurrence_threshold = _recurrence_threshold(incident_kind)
    key = str(incident_key or "").strip()
    if not key:
        raise EligibilityImmuneSystemError("incident_key is required")
    detail = str(summary or "").strip()
    if not detail:
        raise EligibilityImmuneSystemError("incident summary is required")

    context = eligibility_immune_system_context(
        tenant_key=tenant,
        correlation_key=correlation_key,
    )
    incident_fingerprint = canonical_fingerprint(
        {
            "schema_version": ELIGIBILITY_IMMUNE_SYSTEM_SCHEMA_VERSION,
            "tenant_key": tenant,
            "aggregate_key": aggregate,
            "incident_key": key,
            "kind": incident_kind.value,
            "severity": severity.value,
            "summary": detail,
            "source_activity_id": source_activity_id,
        }
    )
    activity_key = f"immune:eligibility:{aggregate}:incident:{key}"
    existing = session.exec(
        select(OrganizationActivity).where(
            OrganizationActivity.tenant_key == tenant,
            OrganizationActivity.activity_key == activity_key,
        )
    ).first()
    if existing is not None:
        if not _matching_existing_incident(
            existing,
            kind=incident_kind,
            severity=severity,
            summary=detail,
            incident_fingerprint=incident_fingerprint,
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
                tenant_key=tenant,
                aggregate_key=aggregate,
            ),
            circuit_opened=False,
            replayed=True,
        )

    circuit_opened = False
    try:
        incident_payload: dict[str, object] = {
            "immune_contract": ELIGIBILITY_IMMUNE_SYSTEM_SCHEMA_VERSION,
            "capability": ELIGIBILITY_IMMUNE_CAPABILITY,
            "aggregate_key": aggregate,
            "incident_key": key,
            "incident_kind": incident_kind.value,
            "severity": severity.value,
            "incident_fingerprint": incident_fingerprint,
            "automatic_circuit_action": (
                "open" if severity is EligibilityImmuneIncidentSeverity.CRITICAL else "none"
            ),
            "authority_effect": "restrict_only",
        }
        if recurrence_threshold is not None:
            incident_payload.update(
                {
                    "recurrence_policy": ELIGIBILITY_IMMUNE_RECURRENCE_POLICY_VERSION,
                    "recurrence_threshold": recurrence_threshold,
                    "recurrence_epoch": "since_last_authorized_close",
                }
            )

        incident = stage_activity(
            session,
            context,
            activity_key=activity_key,
            stream_key=_stream_key(aggregate),
            activity_class=OrganizationActivityClass.blocker,
            activity_type=ELIGIBILITY_IMMUNE_INCIDENT_ACTIVITY_TYPE,
            title="Eligibility immune-system incident",
            summary=detail,
            source_object_type="eligibility_aggregate",
            source_object_id=aggregate,
            source_object_version=ELIGIBILITY_IMMUNE_SYSTEM_SCHEMA_VERSION,
            causation_activity_id=source_activity_id,
            occurred_at=now_utc(),
            payload=incident_payload,
            correlation_key=correlation_key,
        )

        # Re-read control state only after stage_activity has acquired/held the aggregate
        # Activity-stream lock on PostgreSQL. This prevents a concurrent writer from
        # acting on a stale pre-lock CLOSED snapshot and appending a redundant OPEN.
        current = eligibility_circuit_status(
            session,
            tenant_key=tenant,
            aggregate_key=aggregate,
        )
        recurrence = (
            _warning_recurrence_state(
                session,
                tenant_key=tenant,
                aggregate_key=aggregate,
                kind=incident_kind,
            )
            if severity is EligibilityImmuneIncidentSeverity.WARNING
            else None
        )
        recurrence_opens = (
            recurrence is not None
            and recurrence.observed_count >= recurrence.threshold
        )
        policy_requires_open = (
            severity is EligibilityImmuneIncidentSeverity.CRITICAL or recurrence_opens
        )

        if policy_requires_open and current.state is EligibilityCircuitState.CLOSED:
            if severity is EligibilityImmuneIncidentSeverity.CRITICAL:
                open_key = f"immune:eligibility:{aggregate}:circuit:open:{key}"
                open_summary = (
                    "Governed eligibility execution is disabled for this canonical aggregate "
                    "until an authorized recovery closes the circuit."
                )
                open_payload: dict[str, object] = {
                    "immune_contract": ELIGIBILITY_IMMUNE_SYSTEM_SCHEMA_VERSION,
                    "capability": ELIGIBILITY_IMMUNE_CAPABILITY,
                    "aggregate_key": aggregate,
                    "state": EligibilityCircuitState.OPEN.value,
                    "cause_incident_activity_id": str(incident.id),
                    "authority_effect": "restrict_only",
                }
            else:
                if recurrence is None:
                    raise EligibilityImmuneSystemError(
                        "eligibility recurrence policy required an open without recurrence state"
                    )
                open_key = f"immune:eligibility:{aggregate}:circuit:open:recurrence:{key}"
                open_summary = (
                    "Repeated independent eligibility-verifier disagreement reached the deterministic "
                    "recurrence threshold; governed execution is disabled for this canonical aggregate "
                    "until an authorized recovery closes the circuit."
                )
                open_payload = {
                    "immune_contract": ELIGIBILITY_IMMUNE_SYSTEM_SCHEMA_VERSION,
                    "capability": ELIGIBILITY_IMMUNE_CAPABILITY,
                    "aggregate_key": aggregate,
                    "state": EligibilityCircuitState.OPEN.value,
                    "cause_incident_activity_id": str(incident.id),
                    "trigger": "warning_recurrence",
                    "recurrence_policy": ELIGIBILITY_IMMUNE_RECURRENCE_POLICY_VERSION,
                    "incident_kind": incident_kind.value,
                    "recurrence_count": recurrence.observed_count,
                    "recurrence_threshold": recurrence.threshold,
                    "recurrence_epoch_boundary_activity_id": (
                        str(recurrence.epoch_boundary_activity_id)
                        if recurrence.epoch_boundary_activity_id is not None
                        else None
                    ),
                    "authority_effect": "restrict_only",
                }

            stage_activity(
                session,
                context,
                activity_key=open_key,
                stream_key=_stream_key(aggregate),
                activity_class=OrganizationActivityClass.blocker,
                activity_type=ELIGIBILITY_IMMUNE_CIRCUIT_OPEN_ACTIVITY_TYPE,
                title="Eligibility circuit opened",
                summary=open_summary,
                source_object_type="eligibility_aggregate",
                source_object_id=aggregate,
                source_object_version=ELIGIBILITY_IMMUNE_SYSTEM_SCHEMA_VERSION,
                causation_activity_id=incident.id,
                occurred_at=now_utc(),
                payload=open_payload,
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
            tenant_key=tenant,
            aggregate_key=aggregate,
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

    H.2.1 also treats the durable close Activity as the boundary of a new warning
    recurrence epoch. Historical incidents remain visible, but only post-recovery
    verifier disagreements count toward a future recurrence open.
    """

    try:
        require_human(context, admin=True)
    except AuthorityDenied as exc:
        raise EligibilityCircuitRecoveryError(
            "eligibility circuit recovery requires an authenticated human admin"
        ) from exc

    tenant, aggregate = _validated_scope(
        tenant_key=context.tenant_key,
        aggregate_key=aggregate_key,
    )
    key = str(recovery_key or "").strip()
    detail = str(reason or "").strip()
    if not key or not detail:
        raise EligibilityCircuitRecoveryError("recovery_key and reason are required")

    activity_key = f"immune:eligibility:{aggregate}:circuit:closed:{key}"
    existing = session.exec(
        select(OrganizationActivity).where(
            OrganizationActivity.tenant_key == tenant,
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
            tenant_key=tenant,
            aggregate_key=aggregate,
        )

    current = eligibility_circuit_status(
        session,
        tenant_key=tenant,
        aggregate_key=aggregate,
    )
    if current.state is not EligibilityCircuitState.OPEN or current.control_activity_id is None:
        raise EligibilityCircuitRecoveryError("eligibility circuit is not currently open")

    try:
        stage_activity(
            session,
            context,
            activity_key=activity_key,
            stream_key=_stream_key(aggregate),
            activity_class=OrganizationActivityClass.operational,
            activity_type=ELIGIBILITY_IMMUNE_CIRCUIT_CLOSED_ACTIVITY_TYPE,
            title="Eligibility circuit closed",
            summary=detail,
            source_object_type="eligibility_aggregate",
            source_object_id=aggregate,
            source_object_version=ELIGIBILITY_IMMUNE_SYSTEM_SCHEMA_VERSION,
            supersedes_activity_id=current.control_activity_id,
            occurred_at=now_utc(),
            payload={
                "immune_contract": ELIGIBILITY_IMMUNE_SYSTEM_SCHEMA_VERSION,
                "capability": ELIGIBILITY_IMMUNE_CAPABILITY,
                "aggregate_key": aggregate,
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
        tenant_key=tenant,
        aggregate_key=aggregate,
    )
