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
    OrganizationDecisionType,
    OrganizationHumanAction,
    OrganizationRecordReference,
    OrganizationReferenceRole,
    OrganizationReferenceTargetType,
    OrganizationalWorkItem,
)
from app.models.organization_improvement_evaluation import OrganizationImprovementEvaluationCampaign
from app.models.organization_improvement_review import OrganizationImprovementReviewPackage
from app.models.runtime_economics import MonetaryAllocation
from app.services.organization_command import InvalidReference, OrganizationCommandContext
from app.services.organization_improvement_admission_policy import (
    PHASE16_HARD_MONETARY_CEILING_CONTRACT,
    PHASE17_CODEQL_EXACT_HEAD_CONTRACT,
    establish_improvement_admission_dependency_policy,
)
from app.services.organization_improvement_lineage import (
    create_improvement_candidate,
    create_improvement_proposal,
)
from app.services.organization_improvement_shadow import (
    GITHUB_REPOSITORY_TARGET,
    REQUIRED_WORKFLOWS,
    ROADMAP_DEPENDENCY_GATE_POLICY_ABSENT,
    ROADMAP_DEPENDENCY_GATE_RISK_UNAVAILABLE,
    ROADMAP_DEPENDENCY_GATE_SATISFIED,
    SHADOW_WORK_TYPE,
    ShadowCiProofUnavailable,
    _dependency_contract_projection,
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
    assert proof.cross_team_review_status == "absent"
    assert proof.admission_decision_status == "absent"
    assert proof.pre_dependency_admission_ready is False
    assert proof.admission_policy_id is None
    assert proof.admission_policy_version is None
    assert proof.dependency_phases == ()
    assert proof.roadmap_dependency_gate_status == ROADMAP_DEPENDENCY_GATE_RISK_UNAVAILABLE
    assert proof.admission_blockers == (
        "grsi_d_review:absent",
        "shadow_work_decision:absent",
        f"roadmap_dependencies:{ROADMAP_DEPENDENCY_GATE_RISK_UNAVAILABLE}",
    )
    assert proof.grsi_e_qualified is False
    assert proof.grsi_e_admission_conclusion == "blocked_missing_required_evidence"
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

def _complete_review_package(
    session: Session,
    candidate,
) -> OrganizationImprovementReviewPackage:
    campaign = OrganizationImprovementEvaluationCampaign(
        tenant_key=candidate.tenant_key,
        campaign_key=f"grsi-e-eval-{uuid4()}",
        campaign_version=1,
        candidate_id=candidate.id,
        proposal_id=candidate.proposal_id,
        target_type=candidate.target_type,
        target_reference=candidate.target_reference,
        baseline_version=candidate.baseline_version,
        baseline_fingerprint=candidate.baseline_fingerprint,
        candidate_version=candidate.candidate_version,
        candidate_fingerprint=candidate.candidate_fingerprint,
        candidate_author_identities_json="[]",
        candidate_author_evidence_reference_ids_json="[]",
        evaluation_set_key="grsi-e-eval-set",
        evaluation_set_version="v1",
        evaluation_set_fingerprint="3" * 64,
        evaluation_set_reference_ids_json="[]",
        regression_constraints_json="[]",
        required_structurally_separate_evaluators=1,
        status="closed",
        comparison_conclusion="constraints_met",
        record_fingerprint="4" * 64,
        created_by="pytest",
    )
    session.add(campaign)
    session.commit()
    session.refresh(campaign)
    package = OrganizationImprovementReviewPackage(
        tenant_key=candidate.tenant_key,
        package_key=f"grsi-e-review-{uuid4()}",
        package_version=1,
        candidate_id=candidate.id,
        proposal_id=candidate.proposal_id,
        evaluation_campaign_id=campaign.id,
        candidate_fingerprint=candidate.candidate_fingerprint,
        risk_class="high",
        risk_basis_reference_ids_json="[]",
        review_policy_key="pytest-review",
        review_policy_version=1,
        review_policy_fingerprint="5" * 64,
        required_review_kinds_json="[]",
        review_bindings_json="[]",
        record_fingerprint="6" * 64,
        created_by="pytest",
    )
    session.add(package)
    session.commit()
    session.refresh(package)
    return package


def _approved_shadow_decision(
    session: Session,
    candidate,
    work: OrganizationalWorkItem,
    *,
    status: str = "approved",
    supersedes_decision_id: UUID | None = None,
) -> ExecutiveDecision:
    row = ExecutiveDecision(
        decision_key=f"grsi-e-admission-{uuid4()}",
        tenant_key=candidate.tenant_key,
        decision_type=OrganizationDecisionType.board_reserved,
        work_item_id=work.id,
        source_object_type="organization_improvement_candidate",
        source_object_id=str(candidate.id),
        source_object_version=candidate.candidate_fingerprint,
        supersedes_decision_id=supersedes_decision_id,
        authority_level=work.authority_level,
        requested_by_position="cto",
        decision_owner_position="board",
        title="Admit bounded GRSI.E code shadow validation",
        question="May the exact candidate be observed through non-active repository CI?",
        recommendation="Admit only the bounded shadow-validation WorkItem.",
        status=status,
        decided_by="pytest-board" if status in {"approved", "rejected"} else None,
        decision_reason="Pytest governed admission." if status in {"approved", "rejected"} else None,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def _admission_policy(
    session: Session,
    *,
    require_phase16: bool = False,
):
    requirements = [
        {
            "phase_key": "phase16",
            "disposition": "required" if require_phase16 else "not_required",
            "dependency_contract_keys": (
                [PHASE16_HARD_MONETARY_CEILING_CONTRACT]
                if require_phase16
                else []
            ),
            "rationale": (
                "Require a provable monetary ceiling for paid shadow behavior."
                if require_phase16
                else "This repository-only shadow does not cross a paid-provider boundary."
            ),
        },
        {
            "phase_key": "phase17",
            "disposition": "required",
            "dependency_contract_keys": [PHASE17_CODEQL_EXACT_HEAD_CONTRACT],
            "rationale": "Exact-head CodeQL must pass for code/configuration shadow evidence.",
        },
        {
            "phase_key": "phase19",
            "disposition": "not_required",
            "dependency_contract_keys": [],
            "rationale": "This bounded repository shadow does not claim learned procedure evidence.",
        },
        {
            "phase_key": "phase20",
            "disposition": "not_required",
            "dependency_contract_keys": [],
            "rationale": "This bounded repository shadow does not expand autonomy or resources.",
        },
    ]
    return establish_improvement_admission_dependency_policy(
        session,
        _admin_context(),
        target_type="code_configuration",
        execution_mode="shadow",
        candidate_risk_class="high",
        phase_requirements=requirements,
        policy_reason="Pytest bounded GRSI.E code shadow dependency policy.",
        idempotency_key=f"grsi-e-shadow-policy-{uuid4()}",
    )


def test_code_shadow_admission_surfaces_review_and_decision_but_keeps_dependency_gate_closed(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context, candidate, work = _candidate_and_shadow_work(db_session)
    package = _complete_review_package(db_session, candidate)
    decision = _approved_shadow_decision(db_session, candidate, work)
    monkeypatch.setattr(
        "app.services.organization_improvement_shadow.request_public_webhook",
        lambda *args, **kwargs: _response(_runs()),
    )

    proof = project_code_shadow_ci_proof(
        db_session,
        context,
        candidate_id=candidate.id,
        work_item_id=work.id,
    )

    assert proof.review_package_id == package.id
    assert proof.candidate_risk_class == "high"
    assert proof.cross_team_review_status == "complete"
    assert proof.admission_decision_id == decision.id
    assert proof.admission_decision_status == "approved"
    assert proof.pre_dependency_admission_ready is True
    assert proof.admission_policy_id is None
    assert proof.dependency_phases == ()
    assert proof.roadmap_dependency_gate_status == ROADMAP_DEPENDENCY_GATE_POLICY_ABSENT
    assert proof.admission_blockers == (
        f"roadmap_dependencies:{ROADMAP_DEPENDENCY_GATE_POLICY_ABSENT}",
    )
    assert proof.grsi_e_qualified is False
    assert proof.grsi_e_admission_conclusion == "blocked_unverified_phase_dependencies"
    assert proof.authority_conclusion == "none_granted"
    assert proof.deployment_authorized is False


def test_code_shadow_admission_uses_current_superseding_decision_fail_closed(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context, candidate, work = _candidate_and_shadow_work(db_session)
    _complete_review_package(db_session, candidate)
    approved = _approved_shadow_decision(db_session, candidate, work)
    rejected = _approved_shadow_decision(
        db_session,
        candidate,
        work,
        status="rejected",
        supersedes_decision_id=approved.id,
    )
    monkeypatch.setattr(
        "app.services.organization_improvement_shadow.request_public_webhook",
        lambda *args, **kwargs: _response(_runs()),
    )

    proof = project_code_shadow_ci_proof(
        db_session,
        context,
        candidate_id=candidate.id,
        work_item_id=work.id,
    )

    assert proof.admission_decision_id == rejected.id
    assert proof.admission_decision_status == "denied"
    assert proof.pre_dependency_admission_ready is False
    assert "shadow_work_decision:denied" in proof.admission_blockers
    assert proof.grsi_e_qualified is False

def test_code_shadow_admission_qualifies_only_when_current_dependency_policy_is_satisfied(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context, candidate, work = _candidate_and_shadow_work(db_session)
    _complete_review_package(db_session, candidate)
    _approved_shadow_decision(db_session, candidate, work)
    policy = _admission_policy(db_session)
    monkeypatch.setattr(
        "app.services.organization_improvement_shadow.request_public_webhook",
        lambda *args, **kwargs: _response(_runs()),
    )

    proof = project_code_shadow_ci_proof(
        db_session,
        context,
        candidate_id=candidate.id,
        work_item_id=work.id,
    )

    assert proof.pre_dependency_admission_ready is True
    assert proof.admission_policy_id == policy.id
    assert proof.admission_policy_version == 1
    assert proof.roadmap_dependency_gate_status == ROADMAP_DEPENDENCY_GATE_SATISFIED
    assert [item.evidence_status for item in proof.dependency_phases] == [
        "not_required",
        "satisfied",
        "not_required",
        "not_required",
    ]
    phase17 = next(item for item in proof.dependency_phases if item.phase_key == "phase17")
    assert phase17.contracts[0].contract_key == PHASE17_CODEQL_EXACT_HEAD_CONTRACT
    assert phase17.contracts[0].evidence_status == "satisfied"
    assert proof.admission_blockers == ()
    assert proof.grsi_e_qualified is True
    assert proof.grsi_e_admission_conclusion == "qualified_for_bounded_code_shadow"
    assert proof.authority_conclusion == "none_granted"
    assert proof.deployment_authorized is False
    assert proof.external_action_authorized is False


def test_code_shadow_admission_keeps_phase16_hard_monetary_ceiling_fail_closed(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context, candidate, work = _candidate_and_shadow_work(db_session)
    _complete_review_package(db_session, candidate)
    _approved_shadow_decision(db_session, candidate, work)
    _admission_policy(db_session, require_phase16=True)
    monkeypatch.setattr(
        "app.services.organization_improvement_shadow.request_public_webhook",
        lambda *args, **kwargs: _response(_runs()),
    )

    proof = project_code_shadow_ci_proof(
        db_session,
        context,
        candidate_id=candidate.id,
        work_item_id=work.id,
    )

    phase16 = next(item for item in proof.dependency_phases if item.phase_key == "phase16")
    assert phase16.evidence_status == "unsatisfied"
    assert phase16.contracts[0].contract_key == PHASE16_HARD_MONETARY_CEILING_CONTRACT
    assert phase16.contracts[0].evidence_status == "unsatisfied"
    assert "provable_pre_call_monetary_ceiling_missing" in phase16.contracts[0].reasons
    assert (
        f"roadmap_dependency:{PHASE16_HARD_MONETARY_CEILING_CONTRACT}:unsatisfied"
        in proof.admission_blockers
    )
    assert proof.grsi_e_qualified is False
    assert proof.grsi_e_admission_conclusion == "blocked_unverified_phase_dependencies"

def test_phase16_dependency_does_not_reuse_global_economics_for_other_tenant(
    db_session: Session,
) -> None:
    context = OrganizationCommandContext(
        tenant_key="other-tenant",
        actor_id="other-board",
        actor_type=OrganizationActorType.human,
        authenticated_user_id="other-board",
        role="admin",
        department="executive",
        position_key="board",
        authority_level="L4",
    )
    evidence = _dependency_contract_projection(
        db_session,
        context,
        contract_key=PHASE16_HARD_MONETARY_CEILING_CONTRACT,
        workflows=(),
    )

    assert evidence.evidence_status == "unknown"
    assert evidence.reasons == ("phase16_runtime_economics_not_tenant_scoped",)
