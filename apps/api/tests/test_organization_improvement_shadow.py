from __future__ import annotations

from types import SimpleNamespace
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
from app.models.production_deployment_acceptance import (
    ProductionDeploymentAcceptanceCheckReceipt,
)
from app.models.runtime_economics import MonetaryAllocation
from app.services.organization_command import (
    InvalidReference,
    OrganizationCommandContext,
    canonical_json,
)
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
    CANARY_PHASE_KEY,
    CANARY_WORK_TYPE,
    SHADOW_WORK_TYPE,
    ShadowCiProofUnavailable,
    _dependency_contract_projection,
    project_code_canary_evidence,
    project_code_shadow_ci_proof,
)
from app.services.production_deployment_acceptance import (
    DEPLOYMENT_ACCEPTANCE_GATES,
    deployment_acceptance_receipt_fingerprint,
    prepare_deployment_acceptance_run,
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

def _canary_work_and_run(
    session: Session,
    *,
    candidate,
    decision_status: str = "approved",
):
    context = _admin_context()
    suffix = str(uuid4())
    work = OrganizationalWorkItem(
        idempotency_key=f"grsi-e-canary-{suffix}",
        tenant_key="default",
        work_type=CANARY_WORK_TYPE,
        objective_key=f"grsi-e-canary-objective-{suffix}",
        phase_key=CANARY_PHASE_KEY,
        title="Run bounded candidate canary acceptance",
        objective="Bind exact code candidate to Phase 22 synthetic-only canary acceptance.",
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

    decision = ExecutiveDecision(
        decision_key=f"grsi-e-canary-decision-{suffix}",
        tenant_key="default",
        decision_type=OrganizationDecisionType.board_reserved,
        work_item_id=work.id,
        source_object_type=work.source_object_type,
        source_object_id=work.source_object_id,
        source_object_version=work.source_object_version,
        authority_level=work.authority_level,
        requested_by_position="cto",
        decision_owner_position="board",
        title="Admit bounded GRSI.E canary acceptance",
        question="May the exact candidate enter synthetic-only Phase 22 canary acceptance?",
        recommendation="Allow only the bounded candidate-bound canary acceptance run.",
        status=decision_status,
        decided_by="pytest-board" if decision_status == "approved" else None,
        decision_reason="Pytest governed candidate canary admission." if decision_status == "approved" else None,
    )
    session.add(decision)
    session.commit()
    session.refresh(decision)

    run = prepare_deployment_acceptance_run(
        session,
        context,
        deployment_run_key=f"grsi-e-canary-run-{suffix}",
        environment_key="canary-single-vps",
        target_environment_fingerprint="7" * 64,
        release_commit_sha=COMMIT_SHA,
        release_configuration_fingerprint="8" * 64,
        rollback_release_commit_sha="b" * 40,
        rollback_configuration_fingerprint="9" * 64,
        work_item_id=work.id,
        admission_decision_id=decision.id,
        reason="Prepare exact candidate-bound Phase 22 canary acceptance identity.",
    )
    return work, decision, run


def _canary_policy(session: Session) -> None:
    establish_improvement_admission_dependency_policy(
        session,
        _admin_context(),
        target_type="code_configuration",
        execution_mode="canary",
        candidate_risk_class="high",
        phase_requirements=[
            {
                "phase_key": "phase16",
                "disposition": "not_required",
                "dependency_contract_keys": [],
                "rationale": "Synthetic-only canary prohibits paid autonomous execution.",
            },
            {
                "phase_key": "phase17",
                "disposition": "not_required",
                "dependency_contract_keys": [],
                "rationale": "Exact-head CodeQL and V12 remain mandatory shadow prerequisites.",
            },
            {
                "phase_key": "phase19",
                "disposition": "not_required",
                "dependency_contract_keys": [],
                "rationale": "Bounded canary does not claim production outcome attribution.",
            },
            {
                "phase_key": "phase20",
                "disposition": "not_required",
                "dependency_contract_keys": [],
                "rationale": "Canary grants no autonomy, resource or authority expansion.",
            },
        ],
        policy_reason="Board permits bounded synthetic-only code canary after qualified shadow and Phase 22 acceptance.",
        idempotency_key=f"grsi-canary-policy-{uuid4()}",
    )


def _add_canary_receipts(session: Session, run) -> None:
    for gate in DEPLOYMENT_ACCEPTANCE_GATES:
        details = {"synthetic_test": True, "secret_values_recorded": False}
        receipt = ProductionDeploymentAcceptanceCheckReceipt(
            tenant_key=run.tenant_key,
            deployment_run_id=run.id,
            gate_key=gate.gate_key,
            gate_version=gate.gate_version,
            status="satisfied",
            observed_target_environment_fingerprint=run.target_environment_fingerprint,
            observed_release_commit_sha=run.release_commit_sha,
            observed_release_configuration_fingerprint=run.release_configuration_fingerprint,
            executor_contract_key="pytest-target-host-executor",
            executor_contract_version=1,
            executor_identity_fingerprint="c" * 64,
            evidence_digest="d" * 64,
            evidence_reference=f"pytest://grsi-canary/{run.id}/{gate.gate_key}",
            redacted_details_json=canonical_json(details),
            observed_at=run.created_at,
            record_fingerprint="0" * 64,
            created_by="pytest-target-host-executor",
        )
        receipt.record_fingerprint = deployment_acceptance_receipt_fingerprint(
            tenant_key=receipt.tenant_key,
            deployment_run_id=receipt.deployment_run_id,
            gate_key=receipt.gate_key,
            gate_version=receipt.gate_version,
            status=receipt.status,
            observed_target_environment_fingerprint=receipt.observed_target_environment_fingerprint,
            observed_release_commit_sha=receipt.observed_release_commit_sha,
            observed_release_configuration_fingerprint=receipt.observed_release_configuration_fingerprint,
            executor_contract_key=receipt.executor_contract_key,
            executor_contract_version=receipt.executor_contract_version,
            executor_identity_fingerprint=receipt.executor_identity_fingerprint,
            evidence_digest=receipt.evidence_digest,
            evidence_reference=receipt.evidence_reference,
            redacted_details=details,
            observed_at=receipt.observed_at,
            created_by=receipt.created_by,
        )
        session.add(receipt)
    session.commit()


def test_code_canary_qualifies_only_with_current_canary_policy(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context, candidate, shadow_work = _candidate_and_shadow_work(db_session)
    canary_work, decision, run = _canary_work_and_run(db_session, candidate=candidate)
    _add_canary_receipts(db_session, run)
    _canary_policy(db_session)
    monkeypatch.setattr(
        "app.services.organization_improvement_shadow.project_code_shadow_ci_proof",
        lambda *args, **kwargs: SimpleNamespace(
            grsi_e_qualified=True,
            grsi_e_admission_conclusion="qualified_for_bounded_code_shadow",
            candidate_risk_class="high",
            workflows=(),
        ),
    )

    proof = project_code_canary_evidence(
        db_session,
        context,
        candidate_id=candidate.id,
        shadow_work_item_id=shadow_work.id,
        deployment_run_id=run.id,
    )

    assert proof.candidate_id == candidate.id
    assert proof.canary_work_item_id == canary_work.id
    assert proof.deployment_run_id == run.id
    assert proof.artifact_commit_sha == COMMIT_SHA
    assert proof.release_commit_sha == COMMIT_SHA
    assert proof.shadow_qualified is True
    assert proof.canary_decision_id == decision.id
    assert proof.canary_decision_status == "approved"
    assert proof.phase22_canary_evidence_satisfied is True
    assert proof.pre_policy_canary_ready is True
    assert proof.canary_admission_policy_id is not None
    assert proof.canary_admission_policy_version == 1
    assert len(proof.canary_dependency_phases) == 4
    assert proof.canary_dependency_policy_status == ROADMAP_DEPENDENCY_GATE_SATISFIED
    assert proof.admission_blockers == ()
    assert proof.grsi_e_canary_qualified is True
    assert proof.grsi_e_canary_conclusion == "qualified_for_bounded_code_canary"
    assert proof.production_ready is False
    assert proof.promotion_conclusion == "not_assessed"
    assert proof.authority_conclusion == "none_granted"


def test_code_canary_rejects_unrelated_candidate_work_or_release(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context, candidate, shadow_work = _candidate_and_shadow_work(db_session)
    canary_work, _decision, run = _canary_work_and_run(db_session, candidate=candidate)
    monkeypatch.setattr(
        "app.services.organization_improvement_shadow.project_code_shadow_ci_proof",
        lambda *args, **kwargs: SimpleNamespace(
            grsi_e_qualified=True,
            grsi_e_admission_conclusion="qualified_for_bounded_code_shadow",
            candidate_risk_class="high",
            workflows=(),
        ),
    )

    canary_work.source_object_version = "3" * 64
    db_session.add(canary_work)
    db_session.commit()
    with pytest.raises(InvalidReference, match="exact improvement candidate"):
        project_code_canary_evidence(
            db_session,
            context,
            candidate_id=candidate.id,
            shadow_work_item_id=shadow_work.id,
            deployment_run_id=run.id,
        )

    canary_work.source_object_version = candidate.candidate_fingerprint
    db_session.add(canary_work)
    db_session.commit()
    run.release_commit_sha = "e" * 40
    db_session.add(run)
    db_session.commit()
    with pytest.raises(InvalidReference, match="release commit"):
        project_code_canary_evidence(
            db_session,
            context,
            candidate_id=candidate.id,
            shadow_work_item_id=shadow_work.id,
            deployment_run_id=run.id,
        )


def test_code_canary_current_decision_supersession_blocks_readiness(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context, candidate, shadow_work = _candidate_and_shadow_work(db_session)
    canary_work, decision, run = _canary_work_and_run(db_session, candidate=candidate)
    _add_canary_receipts(db_session, run)
    superseding = ExecutiveDecision(
        decision_key=f"grsi-e-canary-superseding-{uuid4()}",
        tenant_key="default",
        decision_type=OrganizationDecisionType.board_reserved,
        work_item_id=canary_work.id,
        source_object_type=canary_work.source_object_type,
        source_object_id=canary_work.source_object_id,
        source_object_version=canary_work.source_object_version,
        supersedes_decision_id=decision.id,
        authority_level=canary_work.authority_level,
        requested_by_position="cto",
        decision_owner_position="board",
        title="Withdraw candidate canary admission",
        question="Should the prior canary admission be superseded?",
        recommendation="Do not use the prior canary Decision.",
        status="rejected",
        decided_by="pytest-board",
        decision_reason="Superseded for test.",
    )
    db_session.add(superseding)
    db_session.commit()
    monkeypatch.setattr(
        "app.services.organization_improvement_shadow.project_code_shadow_ci_proof",
        lambda *args, **kwargs: SimpleNamespace(
            grsi_e_qualified=True,
            grsi_e_admission_conclusion="qualified_for_bounded_code_shadow",
            candidate_risk_class="high",
            workflows=(),
        ),
    )

    proof = project_code_canary_evidence(
        db_session,
        context,
        candidate_id=candidate.id,
        shadow_work_item_id=shadow_work.id,
        deployment_run_id=run.id,
    )

    assert proof.canary_decision_id == superseding.id
    assert proof.canary_decision_status == "denied"
    assert proof.phase22_canary_evidence_satisfied is True
    assert proof.pre_policy_canary_ready is False
    assert "canary_work_decision:denied" in proof.admission_blockers
    assert proof.grsi_e_canary_qualified is False


def test_code_canary_incomplete_phase22_receipts_remain_fail_closed(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context, candidate, shadow_work = _candidate_and_shadow_work(db_session)
    _canary_work, _decision, run = _canary_work_and_run(db_session, candidate=candidate)
    monkeypatch.setattr(
        "app.services.organization_improvement_shadow.project_code_shadow_ci_proof",
        lambda *args, **kwargs: SimpleNamespace(
            grsi_e_qualified=True,
            grsi_e_admission_conclusion="qualified_for_bounded_code_shadow",
            candidate_risk_class="high",
            workflows=(),
        ),
    )

    proof = project_code_canary_evidence(
        db_session,
        context,
        candidate_id=candidate.id,
        shadow_work_item_id=shadow_work.id,
        deployment_run_id=run.id,
    )

    assert proof.deployment_observed is False
    assert proof.canary_evidence_status == "absent"
    assert proof.phase22_canary_evidence_satisfied is False
    assert proof.pre_policy_canary_ready is False
    assert "phase22_canary:absent" in proof.admission_blockers


def test_code_canary_endpoint_is_no_store_and_authority_neutral(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _context, candidate, shadow_work = _candidate_and_shadow_work(db_session)
    _canary_work, _decision, run = _canary_work_and_run(db_session, candidate=candidate)
    _add_canary_receipts(db_session, run)
    monkeypatch.setattr(
        "app.services.organization_improvement_shadow.project_code_shadow_ci_proof",
        lambda *args, **kwargs: SimpleNamespace(
            grsi_e_qualified=True,
            grsi_e_admission_conclusion="qualified_for_bounded_code_shadow",
            candidate_risk_class="high",
            workflows=(),
        ),
    )

    response = client.get(
        f"/api/v1/organization/improvements/shadow/code-canary/candidates/{candidate.id}",
        params={
            "shadow_work_item_id": str(shadow_work.id),
            "deployment_run_id": str(run.id),
        },
    )

    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    body = response.json()
    assert body["candidate_id"] == str(candidate.id)
    assert body["phase22_canary_evidence_satisfied"] is True
    assert body["pre_policy_canary_ready"] is True
    assert body["grsi_e_canary_qualified"] is False
    assert body["canary_dependency_policy_status"] == ROADMAP_DEPENDENCY_GATE_POLICY_ABSENT
    assert body["production_ready"] is False
    assert body["deployment_authorized"] is False
