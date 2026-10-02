from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any
from uuid import UUID

import httpx
from sqlmodel import Session, select

from app.models.domain import ExecutiveDecision, OrganizationalWorkItem
from app.models.organization_improvement_lineage import (
    OrganizationImprovementCandidate,
    OrganizationImprovementProposal,
)
from app.models.organization_improvement_review import OrganizationImprovementReviewPackage
from app.schemas_organization_improvement_shadow import (
    ImprovementCodeShadowCiProofRead,
    ImprovementCodeShadowCiWorkflowRead,
    ImprovementCodeShadowDependencyContractRead,
    ImprovementCodeShadowDependencyPhaseRead,
)
from app.services.organization_command import (
    InvalidReference,
    InvalidTransition,
    OrganizationCommandContext,
    OrganizationCommandError,
    require_human,
    tenant_record,
)
from app.services.organization_improvement_admission_policy import (
    PHASE16_HARD_MONETARY_CEILING_CONTRACT,
    PHASE17_CODEQL_EXACT_HEAD_CONTRACT,
    maybe_current_improvement_admission_dependency_policy,
)
from app.services.organization_improvement_lineage import _proposal_is_current
from app.services.organization_improvement_review import project_review_package
from app.services.runtime_economics import summarize_cost_evidence
from app.services.webhook_egress import WebhookEgressPolicyError, request_public_webhook


GITHUB_REPOSITORY = "bennet287/global-mobility-aios"
GITHUB_REPOSITORY_TARGET = f"github:{GITHUB_REPOSITORY}"
GITHUB_API_BASE = "https://api.github.com"
GITHUB_API_MAX_RESPONSE_BYTES = 1_000_000
SHADOW_WORK_TYPE = "improvement_shadow_validation"
CANDIDATE_SOURCE_TYPE = "organization_improvement_candidate"
ROADMAP_DEPENDENCY_GATE_RISK_UNAVAILABLE = "candidate_risk_class_unavailable"
ROADMAP_DEPENDENCY_GATE_POLICY_ABSENT = "policy_absent"
ROADMAP_DEPENDENCY_GATE_BLOCKED = "blocked"
ROADMAP_DEPENDENCY_GATE_SATISFIED = "satisfied"
_COMMIT_REFERENCE = re.compile(r"^git:commit:([0-9a-f]{40})$")


@dataclass(frozen=True)
class RequiredWorkflow:
    name: str
    path: str


REQUIRED_WORKFLOWS: tuple[RequiredWorkflow, ...] = (
    RequiredWorkflow("Repository Policy Check", ".github/workflows/repo-policy-check.yml"),
    RequiredWorkflow("CodeQL", ".github/workflows/codeql.yml"),
    RequiredWorkflow("V12 Production Proof", ".github/workflows/v12-production-proof.yml"),
)


class ShadowCiProofUnavailable(OrganizationCommandError):
    """The external CI owner could not provide trustworthy exact-head evidence."""


def _candidate_and_proposal(
    session: Session,
    context: OrganizationCommandContext,
    candidate_id: UUID,
) -> tuple[OrganizationImprovementCandidate, OrganizationImprovementProposal]:
    candidate = tenant_record(
        session,
        OrganizationImprovementCandidate,
        candidate_id,
        context.tenant_key,
        label="improvement candidate",
    )
    if candidate.status != "prepared":
        raise InvalidTransition("shadow CI proof requires a prepared improvement candidate")
    proposal = tenant_record(
        session,
        OrganizationImprovementProposal,
        candidate.proposal_id,
        context.tenant_key,
        label="improvement proposal",
    )
    if not _proposal_is_current(session, proposal):
        raise InvalidTransition("shadow CI proof requires a current open improvement proposal")
    if candidate.target_type != "code_configuration":
        raise InvalidReference("shadow CI proof is currently supported only for code_configuration candidates")
    if candidate.target_reference != GITHUB_REPOSITORY_TARGET:
        raise InvalidReference("code_configuration candidate does not target the canonical repository")
    return candidate, proposal


def _artifact_commit_sha(candidate: OrganizationImprovementCandidate) -> str:
    match = _COMMIT_REFERENCE.fullmatch(candidate.artifact_reference)
    if match is None:
        raise InvalidReference("code_configuration candidate artifact_reference must be git:commit:<40 lowercase hex sha>")
    return match.group(1)


def _shadow_work_item(
    session: Session,
    context: OrganizationCommandContext,
    *,
    work_item_id: UUID,
    candidate: OrganizationImprovementCandidate,
) -> OrganizationalWorkItem:
    row = tenant_record(
        session,
        OrganizationalWorkItem,
        work_item_id,
        context.tenant_key,
        label="GRSI.E shadow work item",
    )
    if row.work_type != SHADOW_WORK_TYPE or row.phase_key != "GRSI.E":
        raise InvalidReference("shadow CI proof requires a GRSI.E improvement_shadow_validation WorkItem")
    expected = (CANDIDATE_SOURCE_TYPE, str(candidate.id), candidate.candidate_fingerprint)
    actual = (row.source_object_type, row.source_object_id, row.source_object_version)
    if actual != expected:
        raise InvalidReference("shadow WorkItem must reference the exact improvement candidate id and fingerprint")
    return row


def _github_actions_url(commit_sha: str) -> str:
    return (
        f"{GITHUB_API_BASE}/repos/{GITHUB_REPOSITORY}/actions/runs"
        f"?head_sha={commit_sha}&event=pull_request&per_page=30"
    )


def _fetch_runs(commit_sha: str) -> list[dict[str, Any]]:
    try:
        response = request_public_webhook(
            "GET",
            _github_actions_url(commit_sha),
            headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "global-mobility-aios-grsi-shadow-proof",
            },
            timeout=10,
        )
    except (WebhookEgressPolicyError, httpx.HTTPError) as exc:
        raise ShadowCiProofUnavailable("GitHub Actions evidence could not be retrieved safely") from exc

    if response.status_code != 200:
        raise ShadowCiProofUnavailable(
            f"GitHub Actions evidence returned unexpected HTTP status {response.status_code}"
        )
    if len(response.content) > GITHUB_API_MAX_RESPONSE_BYTES:
        raise ShadowCiProofUnavailable("GitHub Actions evidence response exceeded the bounded size")
    try:
        payload = response.json()
    except (json.JSONDecodeError, ValueError) as exc:
        raise ShadowCiProofUnavailable("GitHub Actions evidence response was not valid JSON") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("workflow_runs"), list):
        raise ShadowCiProofUnavailable("GitHub Actions evidence response did not contain workflow_runs")
    runs = payload["workflow_runs"]
    if len(runs) > 30:
        raise ShadowCiProofUnavailable("GitHub Actions evidence response exceeded the requested run bound")
    return [item for item in runs if isinstance(item, dict)]


def _int_value(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _run_order(run: dict[str, Any]) -> tuple[int, int, int]:
    return (
        _int_value(run.get("run_number")) or -1,
        _int_value(run.get("run_attempt")) or -1,
        _int_value(run.get("id")) or -1,
    )


def _run_evidence_status(run: dict[str, Any] | None) -> str:
    if run is None:
        return "absent"
    status = run.get("status")
    conclusion = run.get("conclusion")
    if status != "completed":
        return "pending" if isinstance(status, str) else "unknown"
    if conclusion == "success":
        return "satisfied"
    if conclusion in {
        "failure",
        "cancelled",
        "timed_out",
        "action_required",
        "startup_failure",
        "stale",
    }:
        return "failed"
    return "unknown"


def _workflow_projection(
    required: RequiredWorkflow,
    runs: list[dict[str, Any]],
    *,
    commit_sha: str,
) -> ImprovementCodeShadowCiWorkflowRead:
    matching = [
        run
        for run in runs
        if run.get("name") == required.name
        and run.get("path") == required.path
        and run.get("head_sha") == commit_sha
        and run.get("event") == "pull_request"
    ]
    selected = max(matching, key=_run_order) if matching else None
    return ImprovementCodeShadowCiWorkflowRead(
        workflow_name=required.name,
        workflow_path=required.path,
        run_id=_int_value(selected.get("id")) if selected else None,
        run_number=_int_value(selected.get("run_number")) if selected else None,
        run_attempt=_int_value(selected.get("run_attempt")) if selected else None,
        status=selected.get("status") if selected and isinstance(selected.get("status"), str) else None,
        conclusion=(
            selected.get("conclusion")
            if selected and isinstance(selected.get("conclusion"), str)
            else None
        ),
        evidence_status=_run_evidence_status(selected),
        head_sha=selected.get("head_sha") if selected and isinstance(selected.get("head_sha"), str) else None,
        event=selected.get("event") if selected and isinstance(selected.get("event"), str) else None,
        html_url=selected.get("html_url") if selected and isinstance(selected.get("html_url"), str) else None,
    )


def _aggregate_status(workflows: tuple[ImprovementCodeShadowCiWorkflowRead, ...]) -> str:
    statuses = [item.evidence_status for item in workflows]
    if all(status == "satisfied" for status in statuses):
        return "complete"
    if "failed" in statuses:
        return "failed"
    if "pending" in statuses:
        return "pending"
    if "absent" in statuses:
        return "partial"
    return "unknown"


def _current_review_summary(
    session: Session,
    context: OrganizationCommandContext,
    *,
    candidate: OrganizationImprovementCandidate,
) -> tuple[UUID | None, str | None, str]:
    rows = session.exec(
        select(OrganizationImprovementReviewPackage)
        .where(
            OrganizationImprovementReviewPackage.tenant_key == context.tenant_key,
            OrganizationImprovementReviewPackage.candidate_id == candidate.id,
        )
        .order_by(OrganizationImprovementReviewPackage.package_version.desc())
    ).all()
    if not rows:
        return None, None, "absent"

    superseded_ids = {
        row.supersedes_package_id
        for row in rows
        if row.supersedes_package_id is not None
    }
    current = [row for row in rows if row.id not in superseded_ids]
    if len(current) != 1:
        return None, None, "unknown"

    row = current[0]
    projection = project_review_package(session, context, row)
    if projection.promotion_evidence_complete_for_decision:
        return row.id, row.risk_class, "complete"

    requirement_statuses = [item.status for item in projection.review_requirements]
    if projection.evaluation_status == "failed" or "failed" in requirement_statuses:
        status = "failed"
    elif projection.evaluation_status == "pending" or any(
        value in {"absent", "pending"} for value in requirement_statuses
    ):
        status = "incomplete"
    else:
        status = "unknown"
    return row.id, row.risk_class, status


def _current_admission_decision(
    session: Session,
    context: OrganizationCommandContext,
    *,
    candidate: OrganizationImprovementCandidate,
    work_item: OrganizationalWorkItem,
) -> tuple[UUID | None, str]:
    rows = session.exec(
        select(ExecutiveDecision).where(
            ExecutiveDecision.tenant_key == context.tenant_key,
            ExecutiveDecision.work_item_id == work_item.id,
            ExecutiveDecision.source_object_type == CANDIDATE_SOURCE_TYPE,
            ExecutiveDecision.source_object_id == str(candidate.id),
            ExecutiveDecision.source_object_version == candidate.candidate_fingerprint,
        )
    ).all()
    if not rows:
        return None, "absent"

    superseded_ids = {
        row.supersedes_decision_id
        for row in rows
        if row.supersedes_decision_id is not None
    }
    current = [row for row in rows if row.id not in superseded_ids]
    if len(current) != 1:
        return None, "unknown"

    row = current[0]
    if row.authority_level != work_item.authority_level:
        return row.id, "unknown"
    if row.status == "approved":
        return row.id, "approved"
    if row.status in {"rejected", "returned", "expired", "superseded"}:
        return row.id, "denied"
    if row.status in {"pending_ceo", "coordinating_ceo", "pending_board"}:
        return row.id, "pending"
    return row.id, "unknown"


def _dependency_contract_projection(
    session: Session,
    context: OrganizationCommandContext,
    *,
    contract_key: str,
    workflows: tuple[ImprovementCodeShadowCiWorkflowRead, ...],
) -> ImprovementCodeShadowDependencyContractRead:
    if contract_key == PHASE17_CODEQL_EXACT_HEAD_CONTRACT:
        workflow = next(
            (
                item
                for item in workflows
                if item.workflow_name == "CodeQL"
                and item.workflow_path == ".github/workflows/codeql.yml"
            ),
            None,
        )
        if workflow is None:
            return ImprovementCodeShadowDependencyContractRead(
                contract_key=contract_key,
                evidence_status="absent",
                reasons=("exact_head_codeql_workflow_not_projected",),
            )
        return ImprovementCodeShadowDependencyContractRead(
            contract_key=contract_key,
            evidence_status=workflow.evidence_status,
            reasons=(
                ()
                if workflow.evidence_status == "satisfied"
                else (f"exact_head_codeql:{workflow.evidence_status}",)
            ),
        )

    if contract_key == PHASE16_HARD_MONETARY_CEILING_CONTRACT:
        if context.tenant_key != "default":
            return ImprovementCodeShadowDependencyContractRead(
                contract_key=contract_key,
                evidence_status="unknown",
                reasons=("phase16_runtime_economics_not_tenant_scoped",),
            )
        summary = summarize_cost_evidence(session)
        budget = summary.get("monetary_budget")
        if not isinstance(budget, dict):
            return ImprovementCodeShadowDependencyContractRead(
                contract_key=contract_key,
                evidence_status="unknown",
                reasons=("phase16_monetary_budget_projection_invalid",),
            )
        enforceable = budget.get("enforceable") is True
        raw_blockers = budget.get("blockers")
        reasons = (
            tuple(str(item) for item in raw_blockers)
            if isinstance(raw_blockers, list)
            else ()
        )
        return ImprovementCodeShadowDependencyContractRead(
            contract_key=contract_key,
            evidence_status="satisfied" if enforceable else "unsatisfied",
            reasons=() if enforceable else (reasons or ("hard_monetary_ceiling_not_proven",)),
        )

    return ImprovementCodeShadowDependencyContractRead(
        contract_key=contract_key,
        evidence_status="unknown",
        reasons=("dependency_contract_resolver_not_implemented",),
    )


def _phase_dependency_status(
    contracts: tuple[ImprovementCodeShadowDependencyContractRead, ...],
) -> str:
    statuses = [item.evidence_status for item in contracts]
    if statuses and all(status == "satisfied" for status in statuses):
        return "satisfied"
    if "failed" in statuses:
        return "failed"
    if "unsatisfied" in statuses:
        return "unsatisfied"
    if "pending" in statuses:
        return "pending"
    if "absent" in statuses:
        return "absent"
    return "unknown"


def _dependency_projection(
    session: Session,
    context: OrganizationCommandContext,
    *,
    risk_class: str | None,
    workflows: tuple[ImprovementCodeShadowCiWorkflowRead, ...],
) -> tuple[
    UUID | None,
    int | None,
    tuple[ImprovementCodeShadowDependencyPhaseRead, ...],
    str,
    tuple[str, ...],
]:
    if risk_class is None:
        return (
            None,
            None,
            (),
            ROADMAP_DEPENDENCY_GATE_RISK_UNAVAILABLE,
            (f"roadmap_dependencies:{ROADMAP_DEPENDENCY_GATE_RISK_UNAVAILABLE}",),
        )

    policy = maybe_current_improvement_admission_dependency_policy(
        session,
        context,
        target_type="code_configuration",
        execution_mode="shadow",
        candidate_risk_class=risk_class,
    )
    if policy is None:
        return (
            None,
            None,
            (),
            ROADMAP_DEPENDENCY_GATE_POLICY_ABSENT,
            (f"roadmap_dependencies:{ROADMAP_DEPENDENCY_GATE_POLICY_ABSENT}",),
        )

    phases: list[ImprovementCodeShadowDependencyPhaseRead] = []
    blockers: list[str] = []
    for requirement in policy.phase_requirements:
        if requirement.disposition == "not_required":
            phases.append(
                ImprovementCodeShadowDependencyPhaseRead(
                    phase_key=requirement.phase_key,
                    disposition=requirement.disposition,
                    evidence_status="not_required",
                    rationale=requirement.rationale,
                    contracts=(),
                )
            )
            continue

        contracts = tuple(
            _dependency_contract_projection(
                session,
                context,
                contract_key=contract_key,
                workflows=workflows,
            )
            for contract_key in requirement.dependency_contract_keys
        )
        phase_status = _phase_dependency_status(contracts)
        phases.append(
            ImprovementCodeShadowDependencyPhaseRead(
                phase_key=requirement.phase_key,
                disposition=requirement.disposition,
                evidence_status=phase_status,
                rationale=requirement.rationale,
                contracts=contracts,
            )
        )
        for contract in contracts:
            if contract.evidence_status != "satisfied":
                blockers.append(
                    f"roadmap_dependency:{contract.contract_key}:{contract.evidence_status}"
                )

    gate_status = (
        ROADMAP_DEPENDENCY_GATE_SATISFIED
        if not blockers
        else ROADMAP_DEPENDENCY_GATE_BLOCKED
    )
    return policy.id, policy.policy_version, tuple(phases), gate_status, tuple(blockers)


def _admission_blockers(
    *,
    ci_status: str,
    review_status: str,
    decision_status: str,
    dependency_blockers: tuple[str, ...],
) -> tuple[str, ...]:
    blockers: list[str] = []
    if ci_status != "complete":
        blockers.append(f"shadow_ci:{ci_status}")
    if review_status != "complete":
        blockers.append(f"grsi_d_review:{review_status}")
    if decision_status != "approved":
        blockers.append(f"shadow_work_decision:{decision_status}")
    blockers.extend(dependency_blockers)
    return tuple(blockers)


def project_code_shadow_ci_proof(
    session: Session,
    context: OrganizationCommandContext,
    *,
    candidate_id: UUID,
    work_item_id: UUID,
) -> ImprovementCodeShadowCiProofRead:
    """Verify exact-head repository CI without creating execution or authority truth."""

    require_human(context, admin=True)
    candidate, proposal = _candidate_and_proposal(session, context, candidate_id)
    commit_sha = _artifact_commit_sha(candidate)
    work_item = _shadow_work_item(
        session,
        context,
        work_item_id=work_item_id,
        candidate=candidate,
    )
    runs = _fetch_runs(commit_sha)
    workflows = tuple(
        _workflow_projection(required, runs, commit_sha=commit_sha)
        for required in REQUIRED_WORKFLOWS
    )
    aggregate = _aggregate_status(workflows)
    review_package_id, risk_class, review_status = _current_review_summary(
        session,
        context,
        candidate=candidate,
    )
    decision_id, decision_status = _current_admission_decision(
        session,
        context,
        candidate=candidate,
        work_item=work_item,
    )
    pre_dependency_ready = (
        aggregate == "complete"
        and review_status == "complete"
        and decision_status == "approved"
    )
    (
        admission_policy_id,
        admission_policy_version,
        dependency_phases,
        dependency_gate_status,
        dependency_blockers,
    ) = _dependency_projection(
        session,
        context,
        risk_class=risk_class,
        workflows=workflows,
    )
    blockers = _admission_blockers(
        ci_status=aggregate,
        review_status=review_status,
        decision_status=decision_status,
        dependency_blockers=dependency_blockers,
    )
    qualified = (
        pre_dependency_ready
        and dependency_gate_status == ROADMAP_DEPENDENCY_GATE_SATISFIED
    )
    admission_conclusion = (
        "qualified_for_bounded_code_shadow"
        if qualified
        else (
            "blocked_unverified_phase_dependencies"
            if pre_dependency_ready
            else "blocked_missing_required_evidence"
        )
    )
    return ImprovementCodeShadowCiProofRead(
        candidate_id=candidate.id,
        proposal_id=proposal.id,
        work_item_id=work_item.id,
        candidate_version=candidate.candidate_version,
        candidate_fingerprint=candidate.candidate_fingerprint,
        artifact_commit_sha=commit_sha,
        repository=GITHUB_REPOSITORY,
        work_item_status=work_item.status,
        ci_evidence_status=aggregate,
        workflows=workflows,
        shadow_execution_observed=any(item.run_id is not None for item in workflows),
        shadow_ci_evidence_complete=aggregate == "complete",
        review_package_id=review_package_id,
        candidate_risk_class=risk_class,
        cross_team_review_status=review_status,
        admission_decision_id=decision_id,
        admission_decision_status=decision_status,
        pre_dependency_admission_ready=pre_dependency_ready,
        admission_policy_id=admission_policy_id,
        admission_policy_version=admission_policy_version,
        dependency_phases=dependency_phases,
        roadmap_dependency_gate_status=dependency_gate_status,
        admission_blockers=blockers,
        grsi_e_qualified=qualified,
        grsi_e_admission_conclusion=admission_conclusion,
        cross_team_review_conclusion=review_status,
    )
