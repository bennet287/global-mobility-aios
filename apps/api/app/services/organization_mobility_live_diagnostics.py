from __future__ import annotations

import json

from sqlmodel import Session

from app.models.domain import AgentRun, OrganizationalActionOutput
from app.services.organization_command import DependencyConflict
from app.services.organization_mobility_live_organization import AustriaLiveSpecialistSnapshot
from app.services.organization_mobility_runtime_quality import (
    AustriaMobilityRuntimeQualityError,
    AustriaSpecialistRuntimeQualitySnapshot,
    evaluate_austria_specialist_runtime_quality,
)


def austria_live_specialist_runtime_quality(
    session: Session,
    specialist: AustriaLiveSpecialistSnapshot,
) -> AustriaSpecialistRuntimeQualitySnapshot | None:
    """Compile Board-safe runtime diagnostics from the specialist's durable K.1 lineage.

    Incomplete or evidence-invalid specialists have no accepted runtime-quality projection.
    Completed evidence-valid specialists fail closed when their durable output/AgentRun lineage
    cannot be reconciled. This function performs no provider call and no retrieval.
    """

    if not specialist.evidence_valid:
        return None
    if specialist.action_output_id is None or specialist.agent_run_id is None:
        raise DependencyConflict(
            f"{specialist.position_key} accepted specialist evidence lacks runtime lineage"
        )

    output = session.get(OrganizationalActionOutput, specialist.action_output_id)
    agent_run = session.get(AgentRun, specialist.agent_run_id)
    if output is None or agent_run is None:
        raise DependencyConflict(
            f"{specialist.position_key} accepted specialist runtime lineage is unavailable"
        )
    if (
        output.work_item_id != specialist.work_item_id
        or output.accountable_position_key != specialist.position_key
        or output.status != "completed"
    ):
        raise DependencyConflict(
            f"{specialist.position_key} accepted specialist output has invalid runtime lineage"
        )

    try:
        payload = json.loads(output.output_json or "{}")
    except (TypeError, json.JSONDecodeError) as exc:
        raise DependencyConflict(
            f"{specialist.position_key} accepted specialist output is invalid JSON"
        ) from exc
    if not isinstance(payload, dict):
        raise DependencyConflict(
            f"{specialist.position_key} accepted specialist output must be a JSON object"
        )
    if payload.get("agent_run_id") != str(agent_run.id):
        raise DependencyConflict(
            f"{specialist.position_key} accepted specialist output/AgentRun lineage diverged"
        )
    controlled_output = payload.get("controlled_output")
    if not isinstance(controlled_output, dict):
        raise DependencyConflict(
            f"{specialist.position_key} accepted specialist output lacks controlled output"
        )

    try:
        return evaluate_austria_specialist_runtime_quality(
            agent_input_json=agent_run.input_json,
            agent_output_json=agent_run.output_json,
            durable_controlled_output=controlled_output,
        )
    except AustriaMobilityRuntimeQualityError as exc:
        raise DependencyConflict(
            f"{specialist.position_key} runtime-quality provenance is inconsistent"
        ) from exc
