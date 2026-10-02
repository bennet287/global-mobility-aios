from __future__ import annotations

import json
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.models.domain import OrganizationActivity, OrganizationActorType, now_utc
from app.models.organization_improvement_admission_policy import (
    OrganizationImprovementAdmissionDependencyPolicy,
)
from app.schemas_organization_improvement_admission_policy import (
    ImprovementAdmissionDependencyPolicyRead,
    ImprovementAdmissionPhaseRequirementCreate,
    ImprovementAdmissionPhaseRequirementRead,
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
)


POLICY_CONTRACT_VERSION = "grsi-admission-dependency-policy.v1"
POLICY_ACTIVITY_TYPE = "organization.improvement_admission_dependency_policy.established.v1"
POLICY_SOURCE_TYPE = "organization_improvement_admission_dependency_policy"
POLICY_GOVERNANCE_SOURCE = "human_board"
SUPPORTED_TARGET_TYPE = "code_configuration"
SUPPORTED_EXECUTION_MODE = "shadow"
PHASE_ORDER = ("phase16", "phase17", "phase19", "phase20")
RISK_CLASSES = frozenset({"low", "medium", "high", "critical"})
PHASE16_HARD_MONETARY_CEILING_CONTRACT = "phase16.runtime_economics.hard_monetary_ceiling.v1"
PHASE17_CODEQL_EXACT_HEAD_CONTRACT = "phase17.repository.codeql_exact_head.v1"
SUPPORTED_DEPENDENCY_CONTRACT_PHASE: dict[str, str] = {
    PHASE16_HARD_MONETARY_CEILING_CONTRACT: "phase16",
    PHASE17_CODEQL_EXACT_HEAD_CONTRACT: "phase17",
}


class ImprovementAdmissionPolicyIntegrityError(InvalidTransition):
    """Durable GRSI admission-policy lineage no longer reconciles."""


def _required(value: str, *, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise InvalidReference(f"{field} is required")
    return normalized


def _normalize_phase_requirements(
    values: list[ImprovementAdmissionPhaseRequirementCreate | dict[str, Any]],
) -> tuple[dict[str, Any], ...]:
    normalized: list[dict[str, Any]] = []
    seen_phases: set[str] = set()
    for raw in values:
        item = raw.model_dump() if isinstance(raw, ImprovementAdmissionPhaseRequirementCreate) else dict(raw)
        phase_key = str(item.get("phase_key") or "").strip()
        disposition = str(item.get("disposition") or "").strip()
        rationale = _required(str(item.get("rationale") or ""), field="phase requirement rationale")
        raw_keys = item.get("dependency_contract_keys") or []
        if not isinstance(raw_keys, (list, tuple)):
            raise InvalidReference("dependency_contract_keys must be a list")
        keys = tuple(sorted(str(value).strip() for value in raw_keys if str(value).strip()))

        if phase_key not in PHASE_ORDER:
            raise InvalidReference("unsupported GRSI admission phase key")
        if phase_key in seen_phases:
            raise InvalidReference("each GRSI admission phase must appear exactly once")
        seen_phases.add(phase_key)
        if disposition not in {"required", "not_required"}:
            raise InvalidReference("unsupported GRSI admission phase disposition")
        if len(set(keys)) != len(keys):
            raise InvalidReference("dependency contract keys must be unique")
        if disposition == "required" and not keys:
            raise InvalidReference("required phase must declare at least one dependency contract key")
        if disposition == "not_required" and keys:
            raise InvalidReference("not_required phase cannot declare dependency contract keys")

        for key in keys:
            owner_phase = SUPPORTED_DEPENDENCY_CONTRACT_PHASE.get(key)
            if owner_phase is None:
                raise InvalidReference(f"unsupported dependency contract key: {key}")
            if owner_phase != phase_key:
                raise InvalidReference(
                    f"dependency contract {key} belongs to {owner_phase}, not {phase_key}"
                )

        normalized.append(
            {
                "phase_key": phase_key,
                "disposition": disposition,
                "dependency_contract_keys": list(keys),
                "rationale": rationale,
            }
        )

    if seen_phases != set(PHASE_ORDER) or len(normalized) != len(PHASE_ORDER):
        raise InvalidReference("policy must address phase16, phase17, phase19 and phase20 exactly once")
    by_phase = {item["phase_key"]: item for item in normalized}
    return tuple(by_phase[phase] for phase in PHASE_ORDER)


def _scope_payload(
    *,
    target_type: str,
    execution_mode: str,
    candidate_risk_class: str,
) -> dict[str, str]:
    return {
        "target_type": target_type,
        "execution_mode": execution_mode,
        "candidate_risk_class": candidate_risk_class,
    }


def _record_fingerprint(
    *,
    tenant_key: str,
    target_type: str,
    execution_mode: str,
    candidate_risk_class: str,
    policy_version: int,
    phase_requirements: tuple[dict[str, Any], ...],
    policy_reason: str,
    supersedes_policy_id: UUID | None,
    idempotency_key: str,
) -> str:
    return canonical_fingerprint(
        {
            "contract_version": POLICY_CONTRACT_VERSION,
            "tenant_key": tenant_key,
            **_scope_payload(
                target_type=target_type,
                execution_mode=execution_mode,
                candidate_risk_class=candidate_risk_class,
            ),
            "policy_version": policy_version,
            "phase_requirements": list(phase_requirements),
            "policy_reason": policy_reason,
            "supersedes_policy_id": str(supersedes_policy_id) if supersedes_policy_id else None,
            "governance_source": POLICY_GOVERNANCE_SOURCE,
            "idempotency_key": idempotency_key,
        }
    )


def _activity_payload(
    *,
    policy_id: UUID,
    target_type: str,
    execution_mode: str,
    candidate_risk_class: str,
    policy_version: int,
    phase_requirements: tuple[dict[str, Any], ...],
    policy_reason: str,
    record_fingerprint: str,
) -> dict[str, Any]:
    return {
        "contract_version": POLICY_CONTRACT_VERSION,
        "constitutional_activity_class": "AUTHORITY",
        "governance_source": POLICY_GOVERNANCE_SOURCE,
        "policy_id": str(policy_id),
        **_scope_payload(
            target_type=target_type,
            execution_mode=execution_mode,
            candidate_risk_class=candidate_risk_class,
        ),
        "policy_version": policy_version,
        "phase_requirements": list(phase_requirements),
        "policy_reason": policy_reason,
        "policy_record_fingerprint": record_fingerprint,
        "candidate_qualified": False,
        "authority_mutated": False,
        "autonomy_mutated": False,
        "deployment_authorized": False,
        "external_action_authorized": False,
    }


def _scope_statement(
    *,
    tenant_key: str,
    target_type: str,
    execution_mode: str,
    candidate_risk_class: str,
):
    return select(OrganizationImprovementAdmissionDependencyPolicy).where(
        OrganizationImprovementAdmissionDependencyPolicy.tenant_key == tenant_key,
        OrganizationImprovementAdmissionDependencyPolicy.target_type == target_type,
        OrganizationImprovementAdmissionDependencyPolicy.execution_mode == execution_mode,
        OrganizationImprovementAdmissionDependencyPolicy.candidate_risk_class == candidate_risk_class,
    )


def _normalize_scope(
    *,
    target_type: str,
    execution_mode: str,
    candidate_risk_class: str,
) -> tuple[str, str, str]:
    target_type = _required(target_type, field="target_type")
    execution_mode = _required(execution_mode, field="execution_mode")
    candidate_risk_class = _required(candidate_risk_class, field="candidate_risk_class")
    if target_type != SUPPORTED_TARGET_TYPE:
        raise InvalidReference("GRSI admission dependency policy currently supports code_configuration only")
    if execution_mode != SUPPORTED_EXECUTION_MODE:
        raise InvalidReference("GRSI admission dependency policy currently supports shadow mode only")
    if candidate_risk_class not in RISK_CLASSES:
        raise InvalidReference("unsupported GRSI candidate risk class")
    return target_type, execution_mode, candidate_risk_class


def _stored_phase_requirements(
    row: OrganizationImprovementAdmissionDependencyPolicy,
) -> tuple[dict[str, Any], ...]:
    try:
        value = json.loads(row.phase_requirements_json)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ImprovementAdmissionPolicyIntegrityError(
            "admission dependency policy requirements JSON is invalid"
        ) from exc
    if not isinstance(value, list):
        raise ImprovementAdmissionPolicyIntegrityError(
            "admission dependency policy requirements are not a list"
        )
    try:
        return _normalize_phase_requirements(value)
    except (InvalidReference, TypeError, ValueError) as exc:
        raise ImprovementAdmissionPolicyIntegrityError(
            "admission dependency policy requirements no longer satisfy the contract"
        ) from exc


def _activity_json(activity: OrganizationActivity) -> dict[str, Any]:
    try:
        value = json.loads(activity.payload_json or "{}")
    except (TypeError, json.JSONDecodeError) as exc:
        raise ImprovementAdmissionPolicyIntegrityError(
            "admission dependency policy Activity payload is invalid"
        ) from exc
    if not isinstance(value, dict):
        raise ImprovementAdmissionPolicyIntegrityError(
            "admission dependency policy Activity payload is invalid"
        )
    return value


def _validated_scope_rows(
    session: Session,
    *,
    tenant_key: str,
    target_type: str,
    execution_mode: str,
    candidate_risk_class: str,
) -> list[OrganizationImprovementAdmissionDependencyPolicy]:
    target_type, execution_mode, candidate_risk_class = _normalize_scope(
        target_type=target_type,
        execution_mode=execution_mode,
        candidate_risk_class=candidate_risk_class,
    )
    rows = list(
        session.exec(
            _scope_statement(
                tenant_key=tenant_key,
                target_type=target_type,
                execution_mode=execution_mode,
                candidate_risk_class=candidate_risk_class,
            ).order_by(OrganizationImprovementAdmissionDependencyPolicy.policy_version)
        ).all()
    )
    previous: OrganizationImprovementAdmissionDependencyPolicy | None = None
    for expected_version, row in enumerate(rows, start=1):
        if row.policy_version != expected_version:
            raise ImprovementAdmissionPolicyIntegrityError(
                "admission dependency policy version chain is not contiguous"
            )
        if expected_version == 1:
            if row.supersedes_policy_id is not None:
                raise ImprovementAdmissionPolicyIntegrityError(
                    "first admission dependency policy unexpectedly supersedes another policy"
                )
        elif previous is None or row.supersedes_policy_id != previous.id:
            raise ImprovementAdmissionPolicyIntegrityError(
                "admission dependency policy supersession chain drifted"
            )

        requirements = _stored_phase_requirements(row)
        expected_fingerprint = _record_fingerprint(
            tenant_key=row.tenant_key,
            target_type=row.target_type,
            execution_mode=row.execution_mode,
            candidate_risk_class=row.candidate_risk_class,
            policy_version=row.policy_version,
            phase_requirements=requirements,
            policy_reason=row.policy_reason,
            supersedes_policy_id=row.supersedes_policy_id,
            idempotency_key=row.idempotency_key,
        )
        if row.record_fingerprint != expected_fingerprint:
            raise ImprovementAdmissionPolicyIntegrityError(
                "admission dependency policy record fingerprint drifted"
            )

        activity = session.exec(
            select(OrganizationActivity).where(
                OrganizationActivity.tenant_key == row.tenant_key,
                OrganizationActivity.id == row.decision_activity_id,
            )
        ).first()
        if activity is None:
            raise ImprovementAdmissionPolicyIntegrityError(
                "admission dependency policy Board Activity is missing"
            )
        if activity.record_fingerprint != row.decision_activity_fingerprint:
            raise ImprovementAdmissionPolicyIntegrityError(
                "admission dependency policy Activity fingerprint drifted"
            )
        if (
            str(getattr(activity.activity_class, "value", activity.activity_class)) != "decision"
            or str(getattr(activity.actor_type, "value", activity.actor_type)) != OrganizationActorType.human.value
            or activity.position_key != "board"
            or activity.authority_level != "L4"
            or activity.activity_type != POLICY_ACTIVITY_TYPE
            or activity.source_object_type != POLICY_SOURCE_TYPE
            or activity.source_object_id != str(row.id)
            or activity.source_object_version != str(row.policy_version)
            or activity.supersedes_activity_id != (
                previous.decision_activity_id if previous is not None else None
            )
        ):
            raise ImprovementAdmissionPolicyIntegrityError(
                "admission dependency policy Board Activity lineage drifted"
            )
        expected_payload = _activity_payload(
            policy_id=row.id,
            target_type=row.target_type,
            execution_mode=row.execution_mode,
            candidate_risk_class=row.candidate_risk_class,
            policy_version=row.policy_version,
            phase_requirements=requirements,
            policy_reason=row.policy_reason,
            record_fingerprint=row.record_fingerprint,
        )
        if _activity_json(activity) != expected_payload:
            raise ImprovementAdmissionPolicyIntegrityError(
                "admission dependency policy Board Activity payload drifted"
            )
        previous = row
    return rows


def _project_row(
    row: OrganizationImprovementAdmissionDependencyPolicy,
    *,
    requirements: tuple[dict[str, Any], ...],
    lifecycle_status: str,
) -> ImprovementAdmissionDependencyPolicyRead:
    return ImprovementAdmissionDependencyPolicyRead(
        id=row.id,
        tenant_key=row.tenant_key,
        target_type=row.target_type,
        execution_mode=row.execution_mode,
        candidate_risk_class=row.candidate_risk_class,
        policy_version=row.policy_version,
        phase_requirements=tuple(
            ImprovementAdmissionPhaseRequirementRead(
                phase_key=item["phase_key"],
                disposition=item["disposition"],
                dependency_contract_keys=tuple(item["dependency_contract_keys"]),
                rationale=item["rationale"],
            )
            for item in requirements
        ),
        policy_reason=row.policy_reason,
        supersedes_policy_id=row.supersedes_policy_id,
        decision_activity_id=row.decision_activity_id,
        decision_activity_fingerprint=row.decision_activity_fingerprint,
        idempotency_key=row.idempotency_key,
        record_fingerprint=row.record_fingerprint,
        lifecycle_status=lifecycle_status,
        created_by=row.created_by,
        created_at=row.created_at,
    )


def project_improvement_admission_dependency_policy(
    session: Session,
    context: OrganizationCommandContext,
    row: OrganizationImprovementAdmissionDependencyPolicy,
) -> ImprovementAdmissionDependencyPolicyRead:
    require_human(context, admin=True)
    if row.tenant_key != context.tenant_key:
        raise InvalidReference("admission dependency policy tenant does not match command context")
    rows = _validated_scope_rows(
        session,
        tenant_key=context.tenant_key,
        target_type=row.target_type,
        execution_mode=row.execution_mode,
        candidate_risk_class=row.candidate_risk_class,
    )
    ids = {candidate.id for candidate in rows}
    if row.id not in ids:
        raise ImprovementAdmissionPolicyIntegrityError(
            "admission dependency policy row is outside its validated scope"
        )
    return _project_row(
        row,
        requirements=_stored_phase_requirements(row),
        lifecycle_status="CURRENT" if rows and rows[-1].id == row.id else "HISTORICAL",
    )


def maybe_current_improvement_admission_dependency_policy(
    session: Session,
    context: OrganizationCommandContext,
    *,
    target_type: str,
    execution_mode: str,
    candidate_risk_class: str,
) -> ImprovementAdmissionDependencyPolicyRead | None:
    require_human(context, admin=True)
    target_type, execution_mode, candidate_risk_class = _normalize_scope(
        target_type=target_type,
        execution_mode=execution_mode,
        candidate_risk_class=candidate_risk_class,
    )
    rows = _validated_scope_rows(
        session,
        tenant_key=context.tenant_key,
        target_type=target_type,
        execution_mode=execution_mode,
        candidate_risk_class=candidate_risk_class,
    )
    if not rows:
        return None
    row = rows[-1]
    return _project_row(
        row,
        requirements=_stored_phase_requirements(row),
        lifecycle_status="CURRENT",
    )


def current_improvement_admission_dependency_policy(
    session: Session,
    context: OrganizationCommandContext,
    *,
    target_type: str,
    execution_mode: str,
    candidate_risk_class: str,
) -> ImprovementAdmissionDependencyPolicyRead:
    current = maybe_current_improvement_admission_dependency_policy(
        session,
        context,
        target_type=target_type,
        execution_mode=execution_mode,
        candidate_risk_class=candidate_risk_class,
    )
    if current is None:
        raise InvalidReference("current GRSI admission dependency policy was not found")
    return current


def establish_improvement_admission_dependency_policy(
    session: Session,
    context: OrganizationCommandContext,
    *,
    target_type: str,
    execution_mode: str,
    candidate_risk_class: str,
    phase_requirements: list[ImprovementAdmissionPhaseRequirementCreate | dict[str, Any]],
    policy_reason: str,
    idempotency_key: str,
    expected_policy_version: int | None = None,
) -> OrganizationImprovementAdmissionDependencyPolicy:
    """Append Board-authored prerequisite policy without qualifying any candidate."""

    require_human(context, admin=True)
    if context.position_key != "board":
        raise AuthorityDenied("only the persistent Board position may establish GRSI admission policy")
    target_type, execution_mode, candidate_risk_class = _normalize_scope(
        target_type=target_type,
        execution_mode=execution_mode,
        candidate_risk_class=candidate_risk_class,
    )
    requirements = _normalize_phase_requirements(phase_requirements)
    policy_reason = _required(policy_reason, field="policy_reason")
    idempotency_key = _required(idempotency_key, field="idempotency_key")

    existing = session.exec(
        select(OrganizationImprovementAdmissionDependencyPolicy).where(
            OrganizationImprovementAdmissionDependencyPolicy.tenant_key == context.tenant_key,
            OrganizationImprovementAdmissionDependencyPolicy.idempotency_key == idempotency_key,
        )
    ).first()
    if existing is not None:
        expected = _record_fingerprint(
            tenant_key=context.tenant_key,
            target_type=target_type,
            execution_mode=execution_mode,
            candidate_risk_class=candidate_risk_class,
            policy_version=existing.policy_version,
            phase_requirements=requirements,
            policy_reason=policy_reason,
            supersedes_policy_id=existing.supersedes_policy_id,
            idempotency_key=idempotency_key,
        )
        if existing.record_fingerprint != expected:
            raise IdempotencyConflict(
                "GRSI admission policy idempotency key was already used with different semantics"
            )
        _validated_scope_rows(
            session,
            tenant_key=context.tenant_key,
            target_type=existing.target_type,
            execution_mode=existing.execution_mode,
            candidate_risk_class=existing.candidate_risk_class,
        )
        return existing

    statement = _scope_statement(
        tenant_key=context.tenant_key,
        target_type=target_type,
        execution_mode=execution_mode,
        candidate_risk_class=candidate_risk_class,
    ).order_by(OrganizationImprovementAdmissionDependencyPolicy.policy_version.desc())
    if session.get_bind().dialect.name == "postgresql":
        statement = statement.with_for_update()
    current = session.exec(statement).first()
    if current is None:
        if expected_policy_version not in {None, 0}:
            raise InvalidTransition("expected policy version is stale")
        next_version = 1
    else:
        if expected_policy_version is None:
            raise InvalidTransition("expected_policy_version is required for policy supersession")
        if expected_policy_version != current.policy_version:
            raise InvalidTransition("expected policy version is stale")
        _validated_scope_rows(
            session,
            tenant_key=context.tenant_key,
            target_type=target_type,
            execution_mode=execution_mode,
            candidate_risk_class=candidate_risk_class,
        )
        next_version = current.policy_version + 1

    policy_id = uuid4()
    record_fingerprint = _record_fingerprint(
        tenant_key=context.tenant_key,
        target_type=target_type,
        execution_mode=execution_mode,
        candidate_risk_class=candidate_risk_class,
        policy_version=next_version,
        phase_requirements=requirements,
        policy_reason=policy_reason,
        supersedes_policy_id=current.id if current is not None else None,
        idempotency_key=idempotency_key,
    )
    occurred_at = now_utc()
    scope_digest = canonical_fingerprint(
        {
            "tenant_key": context.tenant_key,
            **_scope_payload(
                target_type=target_type,
                execution_mode=execution_mode,
                candidate_risk_class=candidate_risk_class,
            ),
        }
    )
    activity = stage_activity(
        session,
        context,
        activity_key=f"grsi-admission-policy:{policy_id}",
        stream_key=f"grsi-admission-policy:{scope_digest}",
        activity_class="decision",
        activity_type=POLICY_ACTIVITY_TYPE,
        title="GRSI admission dependency policy established",
        summary=(
            f"Human Board established GRSI {execution_mode} dependency policy v{next_version} "
            f"for {target_type}/{candidate_risk_class}; no candidate qualification or authority changed."
        ),
        source_object_type=POLICY_SOURCE_TYPE,
        source_object_id=str(policy_id),
        source_object_version=str(next_version),
        occurred_at=occurred_at,
        supersedes_activity_id=current.decision_activity_id if current is not None else None,
        payload=_activity_payload(
            policy_id=policy_id,
            target_type=target_type,
            execution_mode=execution_mode,
            candidate_risk_class=candidate_risk_class,
            policy_version=next_version,
            phase_requirements=requirements,
            policy_reason=policy_reason,
            record_fingerprint=record_fingerprint,
        ),
    )
    row = OrganizationImprovementAdmissionDependencyPolicy(
        id=policy_id,
        tenant_key=context.tenant_key,
        target_type=target_type,
        execution_mode=execution_mode,
        candidate_risk_class=candidate_risk_class,
        policy_version=next_version,
        phase_requirements_json=canonical_json(list(requirements)),
        policy_reason=policy_reason,
        supersedes_policy_id=current.id if current is not None else None,
        decision_activity_id=activity.id,
        decision_activity_fingerprint=activity.record_fingerprint,
        idempotency_key=idempotency_key,
        record_fingerprint=record_fingerprint,
        created_by=context.actor_id,
        created_at=occurred_at,
    )
    session.add(row)
    try:
        commit_mutations(
            session,
            mutations=(
                AuditMutation(
                    action="organization.improvement.admission_dependency_policy.establish",
                    entity_type=POLICY_SOURCE_TYPE,
                    entity_id=row.id,
                    after_state=row,
                    reason="Board-authored GRSI prerequisite policy recorded; no candidate qualification granted.",
                ),
            ),
            context=context,
            refresh=(row,),
        )
    except IntegrityError as exc:
        session.rollback()
        replay = session.exec(
            select(OrganizationImprovementAdmissionDependencyPolicy).where(
                OrganizationImprovementAdmissionDependencyPolicy.tenant_key == context.tenant_key,
                OrganizationImprovementAdmissionDependencyPolicy.idempotency_key == idempotency_key,
            )
        ).first()
        if replay is not None and replay.record_fingerprint == record_fingerprint:
            return replay
        raise DependencyConflict("GRSI admission policy changed concurrently") from exc
    return row
