"""Read-only procedural-learning signals from existing governed records."""

from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient
from sqlmodel import Session, func, select

from app.models.domain import (
    OrganizationActorType,
    OrganizationContribution,
    OrganizationContributionImpactKind,
    OrganizationContributionRecordKind,
    OrganizationContributionVerificationMethod,
    OrganizationalWorkItem,
    now_utc,
)
from app.models.skill_registry import OrganizationSkill


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
    assert len(body["repeated_patterns"]) == 1
    pattern = body["repeated_patterns"][0]
    assert pattern["distinct_work_items"] == 2
    assert pattern["distinct_sources"] == 3
    assert set(pattern["work_item_ids"]) == {str(first.id), str(second.id)}
    assert str(first_outcome.id) in pattern["outcome_ids"]
    assert pattern["learned_skill_eligible"] is False
    assert pattern["remaining_gate"] == "procedure_and_outcome_attribution_unverified"
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
