from __future__ import annotations

import socket
from dataclasses import replace
from uuid import UUID

import httpx
from sqlmodel import Session, select

from app.core.telemetry import OrganizationSpanContext, organization_span
from app.models.domain import AgentRun, OrganizationalActionOutput
from app.services.organization_command import DependencyConflict
from app.services.organization_mobility_fresh_retrieval import (
    attach_fresh_retrieval_evidence,
    refresh_austria_authority_snapshots,
    validate_action_output_fresh_retrieval_evidence,
)
from app.services.organization_mobility_live_provider_evaluation import (
    AustriaLiveProviderEvaluation,
    configured_live_provider_selection,
    execute_austria_live_provider_evaluation,
    load_austria_mobility_objective_plan,
)
from app.services.organization_mobility_objective_runtime import (
    AUSTRIA_MOBILITY_PATHWAY_POSITION,
    AUSTRIA_MOBILITY_REGULATORY_POSITION,
    austria_specialist_output_key,
)
from app.services.source_retrieval import Resolver


_MISSING_FRESHNESS_WARNING = "fresh retrieval provenance is not present in the K.1 execution contract"


def _fresh_execution_preflight(session: Session, plan) -> None:
    if plan.root_work_item.status in {"completed", "cancelled", "failed", "rejected", "returned"}:
        raise DependencyConflict("live-provider evaluation requires a non-terminal Austria objective")
    conflicts: list[str] = []
    for position_key, work in (
        (AUSTRIA_MOBILITY_PATHWAY_POSITION, plan.pathway_work_item),
        (AUSTRIA_MOBILITY_REGULATORY_POSITION, plan.regulatory_work_item),
    ):
        output_exists = session.exec(
            select(OrganizationalActionOutput.id).where(
                OrganizationalActionOutput.output_key == austria_specialist_output_key(work.id)
            )
        ).first() is not None
        if output_exists:
            conflicts.append(f"{position_key}:current_k1_output_exists")
        if work.status not in {"queued", "running"}:
            conflicts.append(f"{position_key}:status={work.status}")
        if work.execution_attempts >= work.max_execution_attempts:
            conflicts.append(f"{position_key}:execution_attempts_exhausted")
    if conflicts:
        raise DependencyConflict(
            "live-provider evaluation requires both specialists to be fresh executable candidates: "
            + ", ".join(conflicts)
        )


def _enrich_freshness(
    session: Session,
    evaluation: AustriaLiveProviderEvaluation,
) -> AustriaLiveProviderEvaluation:
    enriched = []
    for specialist in evaluation.specialist_evaluations:
        output = session.get(OrganizationalActionOutput, specialist.action_output_id)
        agent_run = session.get(AgentRun, specialist.agent_run_id)
        if output is None or agent_run is None:
            raise DependencyConflict(
                f"{specialist.position_key} fresh-retrieval evaluation lineage is unavailable"
            )
        count = validate_action_output_fresh_retrieval_evidence(
            session,
            output=output,
            agent_run=agent_run,
        )
        warnings = tuple(
            warning
            for warning in specialist.warnings
            if warning != _MISSING_FRESHNESS_WARNING
        )
        if count > 0:
            warnings = (*warnings, "fresh official-source equivalence verified before K.1")
        enriched.append(
            replace(
                specialist,
                fresh_retrieval_provenance_present=count > 0,
                warnings=warnings,
            )
        )

    specialists = tuple(enriched)
    fresh_complete = bool(specialists) and all(
        item.fresh_retrieval_provenance_present for item in specialists
    )
    return replace(
        evaluation,
        specialist_evaluations=specialists,
        fresh_retrieval_provenance_complete=fresh_complete,
        full_l_reasoning_evidence_candidate=(
            evaluation.all_specialists_live_provider_succeeded
            and evaluation.all_specialists_authority_grounded
            and fresh_complete
        ),
    )


def execute_austria_live_provider_cycle(
    session: Session,
    *,
    tenant_key: str,
    root_work_item_id: UUID,
    actor: str = "l-live-provider-evaluation",
    retrieval_transport: httpx.BaseTransport | None = None,
    retrieval_resolver: Resolver = socket.getaddrinfo,
) -> AustriaLiveProviderEvaluation:
    """Run one guarded L-cycle: fresh official-source check, then real K.1 provider execution.

    The fresh check never changes published Context Authority. It proves only that the
    just-retrieved official-source content is equivalent to the governed snapshot. A
    detected source change fails before provider execution and remains in regulatory
    review. Successful freshness attestations are bound to the exact durable K.1
    ActionOutput/AgentRun lineage after execution.
    """

    with organization_span(
        "organization.mobility.live_provider_cycle",
        OrganizationSpanContext(root_work_item_id=root_work_item_id),
    ) as telemetry:
        try:
            configured_live_provider_selection(require_api_key=True)
            plan = load_austria_mobility_objective_plan(
                session,
                tenant_key=tenant_key,
                root_work_item_id=root_work_item_id,
            )
            _fresh_execution_preflight(session, plan)
            attestations = refresh_austria_authority_snapshots(
                session,
                plan,
                transport=retrieval_transport,
                resolver=retrieval_resolver,
            )
            telemetry.fresh_snapshot_count(len(attestations))

            evaluation = execute_austria_live_provider_evaluation(
                session,
                tenant_key=tenant_key,
                root_work_item_id=root_work_item_id,
                actor=actor,
            )
            for specialist in evaluation.specialist_evaluations:
                attach_fresh_retrieval_evidence(
                    session,
                    action_output_id=specialist.action_output_id,
                    agent_run_id=specialist.agent_run_id,
                    execution_attempt_id=specialist.execution_attempt_id,
                    work_item_id=specialist.work_item_id,
                    position_key=specialist.position_key,
                    attestations=attestations,
                    actor=actor,
                )
            enriched = _enrich_freshness(session, evaluation)
        except Exception:
            telemetry.outcome("failed")
            raise
        telemetry.acceptance_candidate(enriched.full_l_reasoning_evidence_candidate)
        telemetry.outcome("completed")
        return enriched
