"""Read-only procedural-learning signals from existing governed records."""

from __future__ import annotations

import json
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlmodel import Session, func, select

from app.models.domain import (
    AgentRun,
    AgentRunStatus,
    OrganizationActorType,
    OrganizationContribution,
    OrganizationContributionImpactKind,
    OrganizationContributionRecordKind,
    OrganizationContributionVerificationMethod,
    OrganizationExecutionAttempt,
    OrganizationalActionOutput,
    OrganizationalWorkItem,
    now_utc,
)
from app.models.skill_registry import OrganizationSkill
from app.services.organization_mobility_objective_runtime import (
    AUSTRIA_MOBILITY_PATHWAY_POSITION,
    AUSTRIA_MOBILITY_SPECIALIST_AGENT_NAMES,
    AUSTRIA_MOBILITY_SPECIALIST_EXECUTION_CONTRACT_VERSION,
    austria_completed_work_fingerprint,
    austria_specialist_output_key,
)


URL = "/api/v1/organization/observatory/learning-recurrence"


def _work(session: Session, *, key: str, tenant: str = "default", status: str = "completed") -> OrganizationalWorkItem:
    work = OrganizationalWorkItem(
        idempotency_key=f"learning:{tenant}:{key}",
        tenant_key=tenant,
        work_type="source_review",
        objective_key="source_quality",
        phase_key="review",
        title=f"Synthetic source review {key}",
        objective="Review a synthetic source.",
        department="compliance",
        authority_level="L1",
        assigned_position_key="reviewer",
        status=status,
        completed_at=now_utc() if status == "completed" else None,
    )
    session.add(work)
    session.commit()
    return work


def _outcome(
    session: Session,
    work: OrganizationalWorkItem,
    *,
    source_id: str,
    kind: OrganizationContributionRecordKind = OrganizationContributionRecordKind.outcome,
    supersedes_id=None,
) -> OrganizationContribution:
    row = OrganizationContribution(
        contribution_key=f"learning:{work.tenant_key}:{work.id}:{source_id}:{kind.value}",
        record_fingerprint="b" * 64,
        tenant_key=work.tenant_key,
        contribution_type="source_certification_review_completed",
        title="Synthetic reviewed source",
        outcome_summary="A governed source review was recorded.",
        actor_type=OrganizationActorType.human,
        actor_id="reviewer",
        department="compliance",
        accountable_position_key="reviewer",
        authority_level="L1",
        objective_key=work.objective_key,
        phase_key=work.phase_key,
        work_item_id=work.id,
        source_object_type="jurisdiction_source_certification",
        source_object_id=source_id,
        source_object_version="v1",
        source_state="approved",
        verification_method=OrganizationContributionVerificationMethod.human_attestation,
        record_kind=kind,
        verified_by="reviewer",
        verified_at=now_utc(),
        human_review_state="completed",
        impact_kind=OrganizationContributionImpactKind.knowledge,
        effective_at=now_utc(),
        supersedes_contribution_id=supersedes_id,
        retraction_reason="Withdrawn reviewed source." if kind == OrganizationContributionRecordKind.retraction else None,
        created_by="reviewer",
    )
    session.add(row)
    session.commit()
    return row


def _get(client: TestClient, role: str = "admin"):
    return client.get(URL, headers={"X-GMAI-Role": role, "X-GMAI-User": "learning-reader"})


def test_recurrence_requires_distinct_completed_work_and_sources_and_grants_nothing(
    raw_client: TestClient, db_session: Session,
) -> None:
    first = _work(db_session, key="first")
    second = _work(db_session, key="second")
    pending = _work(db_session, key="pending", status="running")
    other_tenant = _work(db_session, key="other", tenant="other-tenant")
    first_outcome = _outcome(db_session, first, source_id="source-1")
    _outcome(db_session, first, source_id="source-1-duplicate")
    _outcome(db_session, second, source_id="source-2")
    _outcome(db_session, pending, source_id="source-3")
    _outcome(db_session, other_tenant, source_id="source-4")

    assert _get(raw_client, "read_only").status_code == 403
    assert _get(raw_client, "operator").status_code == 403
    assert raw_client.get(URL).status_code == 401
    before = db_session.exec(select(func.count()).select_from(OrganizationSkill)).one()
    response = _get(raw_client)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["tenant_scope"] == "default"
    assert body["basis"] == "active_contribution_linked_completed_work"
    assert body["observation_only"] is True
    assert body["skill_registry_mutated"] is False
    assert body["active_outcomes"] == 4
    assert body["outcomes_with_work_item"] == 4
    assert body["outcomes_without_work_item"] == 0
    assert len(body["repeated_patterns"]) == 1
    pattern = body["repeated_patterns"][0]
    assert pattern["distinct_work_items"] == 2
    assert pattern["distinct_sources"] == 3
    assert set(pattern["work_item_ids"]) == {str(first.id), str(second.id)}
    assert str(first_outcome.id) in pattern["outcome_ids"]
    assert pattern["learned_skill_eligible"] is False
    assert pattern["remaining_gate"] == "procedure_and_outcome_attribution_unverified"
    assert {item["state"] for item in pattern["execution_lineage"]} == {"not_available"}
    assert db_session.exec(select(func.count()).select_from(OrganizationSkill)).one() == before


def test_correction_and_same_source_remove_recurrence(
    raw_client: TestClient, db_session: Session,
) -> None:
    first = _work(db_session, key="corrected-1")
    second = _work(db_session, key="corrected-2")
    _outcome(db_session, first, source_id="same-source")
    original = _outcome(db_session, second, source_id="same-source")
    assert _get(raw_client).json()["repeated_patterns"] == []

    distinct = _outcome(db_session, second, source_id="new-source")
    assert len(_get(raw_client).json()["repeated_patterns"]) == 1
    _outcome(
        db_session, second, source_id="withdrawn-source",
        kind=OrganizationContributionRecordKind.retraction,
        supersedes_id=distinct.id,
    )
    assert _get(raw_client).json()["repeated_patterns"] == []
    assert original.id != distinct.id


def test_unlinked_governed_outcome_is_counted_but_cannot_become_recurrence(
    raw_client: TestClient, db_session: Session,
) -> None:
    work = _work(db_session, key="unlinked")
    row = _outcome(db_session, work, source_id="unlinked-source")
    row.work_item_id = None
    db_session.add(row)
    db_session.commit()

    body = _get(raw_client).json()
    assert body["active_outcomes"] == 1
    assert body["outcomes_with_work_item"] == 0
    assert body["outcomes_without_work_item"] == 1
    assert body["repeated_patterns"] == []


def test_valid_internal_agent_lineage_still_cannot_attribute_outcome_or_promote_skill(
    raw_client: TestClient, db_session: Session,
) -> None:
    root = _work(db_session, key="root", status="running")
    children = []
    for key in ("specialist-1", "specialist-2"):
        child = _work(db_session, key=key)
        child.work_type = "mobility_specialist_work"
        child.parent_work_item_id = root.id
        child.assigned_position_key = AUSTRIA_MOBILITY_PATHWAY_POSITION
        db_session.add(child)
        db_session.commit()
        children.append(child)
    first, second = children
    _outcome(db_session, first, source_id="source-1")
    _outcome(db_session, second, source_id="source-2")

    attempt = OrganizationExecutionAttempt(
        attempt_key=f"learning:{first.id}:1", work_item_id=first.id, attempt_number=1,
        execution_token="bounded-attempt", status="completed", completed_at=now_utc(),
    )
    run = AgentRun(
        agent_name=AUSTRIA_MOBILITY_SPECIALIST_AGENT_NAMES[AUSTRIA_MOBILITY_PATHWAY_POSITION],
        task="Internal analysis", status=AgentRunStatus.pending_review.value,
        input_json="{}",
    )
    db_session.add(attempt)
    db_session.add(run)
    db_session.commit()
    provenance = {
        "work_item_id": str(first.id), "position_key": AUSTRIA_MOBILITY_PATHWAY_POSITION,
        "context_hash": "context-1", "runtime_binding_hash": "runtime-1",
    }
    run.input_json = json.dumps({"context": {"k1_provenance": provenance}})
    payload = {
        "contract_version": AUSTRIA_MOBILITY_SPECIALIST_EXECUTION_CONTRACT_VERSION,
        "root_work_item_id": str(root.id), "work_item_id": str(first.id),
        "position_key": AUSTRIA_MOBILITY_PATHWAY_POSITION,
        "completed_work_fingerprint": austria_completed_work_fingerprint(first),
        "agent_name": run.agent_name, "agent_run_id": str(run.id),
        "execution_attempt_id": str(attempt.id), "execution_token": attempt.execution_token,
        "context_hash": "context-1", "runtime_binding_hash": "runtime-1",
    }
    output = OrganizationalActionOutput(
        output_key=austria_specialist_output_key(first.id), work_item_id=first.id,
        accountable_position_key=AUSTRIA_MOBILITY_PATHWAY_POSITION,
        authority_basis="Bounded internal analysis", confidence_basis="Review required",
        rollback_posture="Discard internal output", status="completed",
        output_json=json.dumps(payload),
        impact_json='{"external_action_authorized":false,"client_facing":false}',
    )
    db_session.add(run)
    db_session.add(output)
    db_session.commit()

    body = _get(raw_client).json()
    pattern = body["repeated_patterns"][0]
    lineage = {item["work_item_id"]: item for item in pattern["execution_lineage"]}
    assert lineage[str(first.id)]["state"] == "bounded_internal_execution_observed"
    assert lineage[str(first.id)]["agent_run_id"] == str(run.id)
    assert lineage[str(first.id)]["execution_attempt_id"] == str(attempt.id)
    assert lineage[str(second.id)]["state"] == "incomplete"
    assert all(item["outcome_attribution_verified"] is False for item in lineage.values())
    assert all(item["procedure_reproducible"] is False for item in lineage.values())
    assert pattern["learned_skill_eligible"] is False

    run.status = AgentRunStatus.failed.value
    db_session.add(run)
    db_session.commit()
    changed = _get(raw_client).json()["repeated_patterns"][0]["execution_lineage"]
    assert all(item["state"] != "bounded_internal_execution_observed" for item in changed)
