from __future__ import annotations

from uuid import UUID, uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, func, select

from app.models.agent_lifecycle import OrganizationAgent
from app.models.autonomy_profile import CapabilityAutonomyProfile
from app.models.domain import (
    ExecutiveDecision,
    OfficialSource,
    OrganizationActorType,
    OrganizationHumanAction,
    OrganizationRecordReference,
    OrganizationReferenceRole,
    OrganizationReferenceTargetType,
    OrganizationalWorkItem,
)
from app.models.runtime_economics import MonetaryAllocation
from app.services.organization_command import InvalidReference, OrganizationCommandContext
from app.services.organization_improvement_lineage import (
    create_improvement_candidate,
    create_improvement_proposal,
)
from app.services.organization_improvement_shadow import (
    GITHUB_REPOSITORY_TARGET,
    REQUIRED_WORKFLOWS,
    SHADOW_WORK_TYPE,
    ShadowCiProofUnavailable,
    project_code_shadow_ci_proof,
)


COMMIT_SHA = "a" * 40


def _admin_context() -> OrganizationCommandContext:
    return OrganizationCommandContext(
        tenant_key="default",
        actor_id="pytest-admin",
        actor_type=OrganizationActorType.human,
        authenticated_user_id="pytest-admin",
        role="admin",
        department="executive",
        position_key="board",
        authority_level="L4",
    )


def _base_work(session: Session) -> OrganizationalWorkItem:
    suffix = str(uuid4())
    row = OrganizationalWorkItem(
        idempotency_key=f"grsi-e-base-work-{suffix}",
        tenant_key="default",
        work_type="organizational",
        objective_key=f"grsi-e-base-objective-{suffix}",
        phase_key="GRSI.B",
        title="Prepare code candidate",
        objective="Prepare a non-active code/configuration improvement candidate.",
        department="Technology",
        authority_level="L4",
        assigned_position_key="board",
        risk_level="high",
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def _evidence(session: Session, work: OrganizationalWorkItem) -> OrganizationRecordReference:
    suffix = str(uuid4())
    source = OfficialSource(
        country="AT",
        domain="governance",
        name=f"GRSI E evidence {suffix}",
        url=f"https://example.test/grsi-e/{suffix}",
        source_type="official",
    )
    session.add(source)
    session.commit()
    session.refresh(source)
    row = OrganizationRecordReference(
        reference_key=f"grsi-e-evidence-{suffix}",
        record_fingerprint="e" * 64,
        tenant_key="default",
        work_item_id=work.id,
        reference_role=OrganizationReferenceRole.evidence,
        target_type=OrganizationReferenceTargetType.official_source,
        target_id=str(source.id),
        target_version="v1",
        target_state="current",
        content_hash="f" * 64,
        label="GRSI E evidence",
        created_by="pytest",
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def _candidate_and_shadow_work(session: Session):
    context = _admin_context()
    base_work = _base_work(session)
    evidence = _evidence(session, base_work)
    proposal = create_improvement_proposal(
        session,
        context,
        proposal_key=f"grsi-e-proposal-{uuid4()}",
        work_item_id=base_work.id,
        target_type="code_configuration",
        target_reference=GITHUB_REPOSITORY_TARGET,
        baseline_version="base",
        baseline_fingerprint="1" * 64,
        problem_statement="Code/configuration candidate requires exact-head shadow CI evidence.",
        hypothesis="The candidate preserves regressions while improving the intended capability.",
        expected_improvement="Exact-head tests pass without production activation.",
        acceptance_constraints={"repository_ci": {"required": True}},
        evidence_reference_ids=[evidence.id],
    )
    candidate = create_improvement_candidate(
        session,
        context,
        proposal_id=proposal.id,
        candidate_key=f"grsi-e-candidate-{uuid4()}",
        parent_candidate_id=None,
        candidate_version="candidate-1",
        candidate_fingerprint="2" * 64,
        artifact_reference=f"git:commit:{COMMIT_SHA}",
        implementation_provenance={"repository": "bennet287/global-mobility-aios"},
        candidate_hypothesis="Run exact candidate commit in repository CI.",
        expected_improvement="All required exact-head CI workflows succeed.",
        acceptance_constraints={"repository_ci": {"required": True}},
    )
    work = OrganizationalWorkItem(
        idempotency_key=f"grsi-e-shadow-{uuid4()}",
        tenant_key="default",
        work_type=SHADOW_WORK_TYPE,
        objective_key=f"grsi-e-shadow-objective-{uuid4()}",
        phase_key="GRSI.E",
        title="Verify exact-head code candidate in shadow CI",
        objective="Observe repository CI without activating or deploying the candidate.",
        department="Technology",
        authority_level="L4",
        assigned_position_key="board",
        risk_level="high",
        source_object_type="organization_improvement_candidate",
        source_object_id=str(candidate.id),
        source_object_version=candidate.candidate_fingerprint,
    )
    session.add(work)
    session.commit()
    session.refresh(work)
    return context, candidate, work


def _runs(*, conclusion: str = "success", head_sha: str = COMMIT_SHA) -> dict:
    return {
        "workflow_runs": [
            {
                "id": 1000 + index,
                "name": required.name,
                "path": required.path,
                "head_sha": head_sha,
                "event": "pull_request",
                "status": "completed",
                "conclusion": conclusion,
                "run_number": 2000 + index,
                "run_attempt": 1,
                "html_url": f"https://github.com/bennet287/global-mobility-aios/actions/runs/{1000 + index}",
            }
            for index, required in enumerate(REQUIRED_WORKFLOWS)
        ]
    }


def _response(payload: dict, *, status_code: int = 200) -> httpx.Response:
    request = httpx.Request("GET", "https://api.github.com/test")
    return httpx.Response(
        status_code,
        request=request,
        headers={"content-type": "application/json"},
        json=payload,
    )


def _count(session: Session, model) -> int:
    return session.exec(select(func.count()).select_from(model)).one()


def test_code_shadow_ci_proof_verifies_exact_head_without_authority_side_effects(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context, candidate, work = _candidate_and_shadow_work(db_session)
    captured: dict[str, object] = {}

    def fake_request(method: str, url: str, **kwargs):
        captured["method"] = method
        captured["url"] = url
        captured["kwargs"] = kwargs
        return _response(_runs())

    monkeypatch.setattr(
        "app.services.organization_improvement_shadow.request_public_webhook",
        fake_request,
    )
    before = {
        "agents": _count(db_session, OrganizationAgent),
        "autonomy": _count(db_session, CapabilityAutonomyProfile),
        "money": _count(db_session, MonetaryAllocation),
        "decisions": _count(db_session, ExecutiveDecision),
        "human_actions": _count(db_session, OrganizationHumanAction),
    }

    proof = project_code_shadow_ci_proof(
        db_session,
        context,
        candidate_id=candidate.id,
        work_item_id=work.id,
    )

    assert proof.artifact_commit_sha == COMMIT_SHA
    assert proof.ci_evidence_status == "complete"
    assert proof.shadow_execution_observed is True
    assert proof.shadow_ci_evidence_complete is True
    assert proof.grsi_e_qualified is False
    assert proof.authority_conclusion == "none_granted"
    assert proof.active_version_changed is False
    assert proof.deployment_authorized is False
    assert proof.external_action_authorized is False
    assert [item.evidence_status for item in proof.workflows] == [
        "satisfied",
        "satisfied",
        "satisfied",
    ]
    assert captured["method"] == "GET"
    assert f"head_sha={COMMIT_SHA}" in str(captured["url"])
    assert "event=pull_request" in str(captured["url"])
    assert {
        "agents": _count(db_session, OrganizationAgent),
        "autonomy": _count(db_session, CapabilityAutonomyProfile),
        "money": _count(db_session, MonetaryAllocation),
        "decisions": _count(db_session, ExecutiveDecision),
        "human_actions": _count(db_session, OrganizationHumanAction),
    } == before


def test_code_shadow_ci_proof_uses_latest_exact_workflow_run_fail_closed(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context, candidate, work = _candidate_and_shadow_work(db_session)
    payload = _runs()
    required = REQUIRED_WORKFLOWS[0]
    payload["workflow_runs"].append(
        {
            "id": 9999,
            "name": required.name,
            "path": required.path,
            "head_sha": COMMIT_SHA,
            "event": "pull_request",
            "status": "completed",
            "conclusion": "failure",
            "run_number": 9999,
            "run_attempt": 1,
            "html_url": "https://github.com/bennet287/global-mobility-aios/actions/runs/9999",
        }
    )
    monkeypatch.setattr(
        "app.services.organization_improvement_shadow.request_public_webhook",
        lambda *args, **kwargs: _response(payload),
    )

    proof = project_code_shadow_ci_proof(
        db_session,
        context,
        candidate_id=candidate.id,
        work_item_id=work.id,
    )

    assert proof.ci_evidence_status == "failed"
    assert proof.shadow_ci_evidence_complete is False
    policy = next(item for item in proof.workflows if item.workflow_path == required.path)
    assert policy.run_id == 9999
    assert policy.evidence_status == "failed"


def test_code_shadow_ci_proof_rejects_mismatched_work_lineage(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context, candidate, work = _candidate_and_shadow_work(db_session)
    work.source_object_version = "3" * 64
    db_session.add(work)
    db_session.commit()
    monkeypatch.setattr(
        "app.services.organization_improvement_shadow.request_public_webhook",
        lambda *args, **kwargs: _response(_runs()),
    )

    with pytest.raises(InvalidReference):
        project_code_shadow_ci_proof(
            db_session,
            context,
            candidate_id=candidate.id,
            work_item_id=work.id,
        )


def test_code_shadow_ci_proof_rejects_untrusted_external_shape(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context, candidate, work = _candidate_and_shadow_work(db_session)
    monkeypatch.setattr(
        "app.services.organization_improvement_shadow.request_public_webhook",
        lambda *args, **kwargs: _response({"not_workflow_runs": []}),
    )

    with pytest.raises(ShadowCiProofUnavailable):
        project_code_shadow_ci_proof(
            db_session,
            context,
            candidate_id=candidate.id,
            work_item_id=work.id,
        )


def test_code_shadow_ci_endpoint_is_no_store_and_authority_neutral(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _context, candidate, work = _candidate_and_shadow_work(db_session)
    monkeypatch.setattr(
        "app.services.organization_improvement_shadow.request_public_webhook",
        lambda *args, **kwargs: _response(_runs()),
    )

    response = client.get(
        f"/api/v1/organization/improvements/shadow/code-ci/candidates/{candidate.id}",
        params={"work_item_id": str(work.id)},
    )

    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    body = response.json()
    assert body["candidate_id"] == str(candidate.id)
    assert body["ci_evidence_status"] == "complete"
    assert body["grsi_e_qualified"] is False
    assert body["authority_conclusion"] == "none_granted"
    assert body["deployment_authorized"] is False
