from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from uuid import UUID

from sqlmodel import Session

from app.models.domain import (
    AgentRun,
    ExecutiveDecision,
    OrganizationContribution,
    OrganizationExecutionAttempt,
    OrganizationalActionOutput,
    OrganizationalWorkItem,
)
from app.services.organization_command import canonical_fingerprint
from app.services.organization_mobility_objective_runtime import (
    AUSTRIA_MOBILITY_SPECIALIST_EXECUTION_CONTRACT_VERSION,
    AUSTRIA_MOBILITY_SPECIALIST_POSITIONS,
    austria_specialist_execution_evidence_reason,
)
from app.services.organization_observatory import _active_outcomes, _outcomes_and_corrections


_REVIEWED_INTERNAL_ANALYSIS_CONTRIBUTION = "reviewed_internal_analysis_accepted"


@dataclass(frozen=True)
class AcceptedProcedureSupport:
    contribution_id: UUID
    decision_id: UUID
    root_work_item_id: UUID
    work_item_id: UUID
    action_output_id: UUID
    execution_attempt_id: UUID
    agent_run_id: UUID


@dataclass(frozen=True)
class LearnedProcedureReproducibility:
    procedure_fingerprint: str
    contract_version: str
    position_key: str
    phase_key: str
    work_type: str
    agent_name: str
    independent_support_count: int
    required_independent_supports: int
    reproducibility_requirement_satisfied: bool
    reasons: tuple[str, ...]
    supports: tuple[AcceptedProcedureSupport, ...]


def _json_object(raw: str) -> dict[str, object] | None:
    try:
        value = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _accepted_evidence(raw: str) -> dict[str, str] | None:
    """Return the exact K.1 acceptance evidence record emitted by the decision boundary."""

    try:
        value = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return None
    if not isinstance(value, list) or len(value) != 1 or not isinstance(value[0], dict):
        return None
    required = (
        "accepted_action_output_id",
        "accepted_action_output_sha256",
        "agent_run_id",
        "execution_attempt_id",
    )
    if any(not isinstance(value[0].get(key), str) or not value[0][key] for key in required):
        return None
    return {key: value[0][key] for key in required}


def _uuid(value: str) -> UUID | None:
    try:
        return UUID(value)
    except (TypeError, ValueError):
        return None


def _accepted_procedure_support(
    session: Session,
    *,
    tenant_key: str,
    position_key: str,
    contribution: OrganizationContribution,
) -> tuple[str, dict[str, str], AcceptedProcedureSupport] | None:
    """Resolve one accepted analysis to current K.1 execution lineage, fail-closed.

    A matching fingerprint is repeatability evidence for one governed execution contract.
    It is not proof that the procedure caused the accepted outcome.
    """

    if (
        contribution.tenant_key != tenant_key
        or contribution.contribution_type != _REVIEWED_INTERNAL_ANALYSIS_CONTRIBUTION
        or contribution.accountable_position_key != position_key
        or contribution.work_item_id is None
        or contribution.decision_id is None
        or contribution.source_object_type != "executive_decision"
        or contribution.source_state != "approved"
    ):
        return None

    evidence = _accepted_evidence(contribution.evidence_summary_json)
    if evidence is None:
        return None
    output_id = _uuid(evidence["accepted_action_output_id"])
    run_id = _uuid(evidence["agent_run_id"])
    attempt_id = _uuid(evidence["execution_attempt_id"])
    if output_id is None or run_id is None or attempt_id is None:
        return None

    decision = session.get(ExecutiveDecision, contribution.decision_id)
    work = session.get(OrganizationalWorkItem, contribution.work_item_id)
    output = session.get(OrganizationalActionOutput, output_id)
    run = session.get(AgentRun, run_id)
    attempt = session.get(OrganizationExecutionAttempt, attempt_id)
    if any(item is None for item in (decision, work, output, run, attempt)):
        return None
    assert decision is not None
    assert work is not None
    assert output is not None
    assert run is not None
    assert attempt is not None

    if (
        decision.status != "approved"
        or decision.work_item_id != work.id
        or decision.accepted_action_output_id != output.id
        or contribution.source_object_id != str(decision.id)
        or work.tenant_key != tenant_key
        or work.work_type != "mobility_specialist_work"
        or work.status != "completed"
        or work.assigned_position_key != position_key
        or work.parent_work_item_id is None
        or output.work_item_id != work.id
        or output.accountable_position_key != position_key
        or output.status != "completed"
        or run.status not in {"pending_review", "completed", "approved"}
        or attempt.work_item_id != work.id
        or attempt.status != "completed"
    ):
        return None

    root = session.get(OrganizationalWorkItem, work.parent_work_item_id)
    if root is None or root.tenant_key != tenant_key:
        return None
    if austria_specialist_execution_evidence_reason(
        session,
        root=root,
        child=work,
        position_key=position_key,
    ) is not None:
        return None

    output_sha256 = hashlib.sha256(output.output_json.encode("utf-8")).hexdigest()
    if (
        evidence["accepted_action_output_sha256"] != output_sha256
        or decision.accepted_action_output_sha256 != output_sha256
    ):
        return None

    payload = _json_object(output.output_json)
    if payload is None or (
        payload.get("contract_version") != AUSTRIA_MOBILITY_SPECIALIST_EXECUTION_CONTRACT_VERSION
        or payload.get("root_work_item_id") != str(root.id)
        or payload.get("work_item_id") != str(work.id)
        or payload.get("position_key") != position_key
        or payload.get("agent_run_id") != str(run.id)
        or payload.get("execution_attempt_id") != str(attempt.id)
        or payload.get("agent_name") != run.agent_name
        or evidence["agent_run_id"] != str(run.id)
        or evidence["execution_attempt_id"] != str(attempt.id)
    ):
        return None

    phase_key = (work.phase_key or "").strip()
    if not phase_key:
        return None
    identity = {
        "contract_version": AUSTRIA_MOBILITY_SPECIALIST_EXECUTION_CONTRACT_VERSION,
        "position_key": position_key,
        "phase_key": phase_key,
        "work_type": work.work_type,
        "agent_name": run.agent_name,
    }
    support = AcceptedProcedureSupport(
        contribution_id=contribution.id,
        decision_id=decision.id,
        root_work_item_id=root.id,
        work_item_id=work.id,
        action_output_id=output.id,
        execution_attempt_id=attempt.id,
        agent_run_id=run.id,
    )
    return canonical_fingerprint(identity), identity, support


def evaluate_learned_procedure_reproducibility(
    session: Session,
    *,
    tenant_key: str,
    position_key: str,
    required_independent_supports: int = 2,
) -> tuple[LearnedProcedureReproducibility, ...]:
    """Derive a bounded Phase 19 reproducibility prerequisite without learning a skill.

    Active-outcome semantics are owned by the existing Observatory projection, including
    correction/retraction removal. This adapter then narrows those outcomes to exact
    human-accepted K.1 lineages. Supports are independent only when root objective,
    specialist WorkItem, ActionOutput, execution attempt and AgentRun are all distinct.

    Procedure identity intentionally excludes result content, case ContextBundle,
    provider/model routing and ``allowed_tools``. Those values either vary per case or are
    technical routing/entitlement rather than evidence of an executed tool procedure.
    Satisfying this prerequisite does not generate, validate, version, activate, assign,
    bind or authorize a learned skill.
    """

    normalized_tenant = tenant_key.strip()
    if not normalized_tenant:
        raise ValueError("tenant_key is required")
    if position_key not in AUSTRIA_MOBILITY_SPECIALIST_POSITIONS:
        raise ValueError("position_key is not a bounded Austria K.1 specialist")
    if required_independent_supports < 2:
        raise ValueError("at least two independent accepted executions are required")

    outcomes, corrections = _outcomes_and_corrections(session, normalized_tenant)
    rows = _active_outcomes(outcomes, corrections)

    groups: dict[str, tuple[dict[str, str], list[AcceptedProcedureSupport]]] = {}
    for contribution in sorted(rows, key=lambda row: (row.effective_at, str(row.id))):
        resolved = _accepted_procedure_support(
            session,
            tenant_key=normalized_tenant,
            position_key=position_key,
            contribution=contribution,
        )
        if resolved is None:
            continue
        fingerprint, identity, support = resolved
        if fingerprint not in groups:
            groups[fingerprint] = (identity, [])
        supports = groups[fingerprint][1]

        # Re-acceptance or replay of one execution is one support, never a new sample.
        if any(
            support.root_work_item_id == existing.root_work_item_id
            or support.work_item_id == existing.work_item_id
            or support.action_output_id == existing.action_output_id
            or support.execution_attempt_id == existing.execution_attempt_id
            or support.agent_run_id == existing.agent_run_id
            for existing in supports
        ):
            continue
        supports.append(support)

    proofs: list[LearnedProcedureReproducibility] = []
    for fingerprint in sorted(groups):
        identity, supports = groups[fingerprint]
        satisfied = len(supports) >= required_independent_supports
        reasons = () if satisfied else ("insufficient_independent_human_accepted_executions",)
        proofs.append(
            LearnedProcedureReproducibility(
                procedure_fingerprint=fingerprint,
                contract_version=identity["contract_version"],
                position_key=identity["position_key"],
                phase_key=identity["phase_key"],
                work_type=identity["work_type"],
                agent_name=identity["agent_name"],
                independent_support_count=len(supports),
                required_independent_supports=required_independent_supports,
                reproducibility_requirement_satisfied=satisfied,
                reasons=reasons,
                supports=tuple(supports),
            )
        )
    return tuple(proofs)
