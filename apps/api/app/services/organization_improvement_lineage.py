from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    OrganizationRecordReference,
    OrganizationReferenceRole,
    OrganizationalWorkItem,
    now_utc,
)
from app.models.organization_improvement_lineage import (
    OrganizationImprovementCandidate,
    OrganizationImprovementProposal,
)
from app.schemas_organization_improvement_lineage import (
    ImprovementCandidateRead,
    ImprovementProposalRead,
)
from app.services.organization_command import (
    AuditMutation,
    InvalidReference,
    InvalidTransition,
    OrganizationCommandContext,
    canonical_fingerprint,
    canonical_json,
    canonical_payload_json,
    commit_mutations,
    idempotent_existing,
    require_human,
    tenant_record,
)


TARGET_TYPES = frozenset(
    {
        "organization_agent",
        "native_skill",
        "instruction_contract",
        "workflow",
        "context_policy",
        "runtime_profile",
        "evaluation_suite",
        "tool_adapter",
        "code_configuration",
        "training_recipe",
    }
)


def _required(label: str, value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise InvalidReference(f"{label} is required")
    return normalized


def _sha256(label: str, value: str) -> str:
    normalized = value.strip().lower()
    if len(normalized) != 64 or any(ch not in "0123456789abcdef" for ch in normalized):
        raise InvalidReference(f"{label} must be a lowercase SHA-256 hex digest")
    return normalized


def _evidence_ids(
    session: Session,
    context: OrganizationCommandContext,
    reference_ids: list[UUID],
) -> tuple[UUID, ...]:
    if not reference_ids or len(set(reference_ids)) != len(reference_ids):
        raise InvalidReference("improvement proposal requires unique concrete evidence references")
    resolved: list[UUID] = []
    for reference_id in reference_ids:
        row = tenant_record(
            session,
            OrganizationRecordReference,
            reference_id,
            context.tenant_key,
            label="improvement proposal evidence",
        )
        if row.reference_role is not OrganizationReferenceRole.evidence:
            raise InvalidReference("improvement proposal evidence must use evidence references")
        resolved.append(row.id)
    return tuple(sorted(resolved, key=str))


def _proposal_is_current(
    session: Session,
    proposal: OrganizationImprovementProposal,
) -> bool:
    if proposal.status != "open":
        return False
    successor = session.exec(
        select(OrganizationImprovementProposal.id).where(
            OrganizationImprovementProposal.tenant_key == proposal.tenant_key,
            OrganizationImprovementProposal.supersedes_proposal_id == proposal.id,
        )
    ).first()
    return successor is None


def create_improvement_proposal(
    session: Session,
    context: OrganizationCommandContext,
    *,
    proposal_key: str,
    work_item_id: UUID,
    target_type: str,
    target_reference: str,
    baseline_version: str,
    baseline_fingerprint: str,
    problem_statement: str,
    hypothesis: str,
    expected_improvement: str,
    acceptance_constraints: dict[str, Any],
    evidence_reference_ids: list[UUID],
    supersedes_proposal_id: UUID | None = None,
) -> OrganizationImprovementProposal:
    require_human(context, admin=True)
    proposal_key = _required("proposal key", proposal_key)
    target_type = _required("target type", target_type)
    if target_type not in TARGET_TYPES:
        raise InvalidReference("improvement proposal target type is not allowlisted")
    target_reference = _required("target reference", target_reference)
    baseline_version = _required("baseline version", baseline_version)
    baseline_fingerprint = _sha256("baseline fingerprint", baseline_fingerprint)
    problem_statement = _required("problem statement", problem_statement)
    hypothesis = _required("hypothesis", hypothesis)
    expected_improvement = _required("expected improvement", expected_improvement)
    if not acceptance_constraints:
        raise InvalidReference("improvement proposal requires acceptance constraints")

    work_item = tenant_record(
        session,
        OrganizationalWorkItem,
        work_item_id,
        context.tenant_key,
        label="improvement objective work item",
    )
    evidence_ids = _evidence_ids(session, context, evidence_reference_ids)

    predecessor: OrganizationImprovementProposal | None = None
    if supersedes_proposal_id is not None:
        predecessor = tenant_record(
            session,
            OrganizationImprovementProposal,
            supersedes_proposal_id,
            context.tenant_key,
            label="superseded improvement proposal",
        )
        if (predecessor.target_type, predecessor.target_reference) != (
            target_type,
            target_reference,
        ):
            raise InvalidReference("proposal supersession must retain the same target identity")

    command = {
        "tenant_key": context.tenant_key,
        "proposal_key": proposal_key,
        "work_item_id": str(work_item.id),
        "target_type": target_type,
        "target_reference": target_reference,
        "baseline_version": baseline_version,
        "baseline_fingerprint": baseline_fingerprint,
        "problem_statement": problem_statement,
        "hypothesis": hypothesis,
        "expected_improvement": expected_improvement,
        "acceptance_constraints": acceptance_constraints,
        "evidence_reference_ids": [str(value) for value in evidence_ids],
        "supersedes_proposal_id": str(supersedes_proposal_id) if supersedes_proposal_id else None,
        "status": "open",
    }
    fingerprint = canonical_fingerprint(command)
    existing = session.exec(
        select(OrganizationImprovementProposal).where(
            OrganizationImprovementProposal.tenant_key == context.tenant_key,
            OrganizationImprovementProposal.proposal_key == proposal_key,
        )
    ).first()
    replay = idempotent_existing(
        existing,
        fingerprint,
        fingerprint_field="record_fingerprint",
        label="improvement proposal",
    )
    if replay is not None:
        return replay

    if predecessor is not None and not _proposal_is_current(session, predecessor):
        raise InvalidTransition("only a current open improvement proposal can be superseded")

    row = OrganizationImprovementProposal(
        tenant_key=context.tenant_key,
        proposal_key=proposal_key,
        work_item_id=work_item.id,
        target_type=target_type,
        target_reference=target_reference,
        baseline_version=baseline_version,
        baseline_fingerprint=baseline_fingerprint,
        problem_statement=problem_statement,
        hypothesis=hypothesis,
        expected_improvement=expected_improvement,
        acceptance_constraints_json=canonical_payload_json(acceptance_constraints),
        evidence_reference_ids_json=canonical_json([str(value) for value in evidence_ids]),
        supersedes_proposal_id=supersedes_proposal_id,
        status="open",
        record_fingerprint=fingerprint,
        created_by=context.actor_id,
    )
    session.add(row)
    commit_mutations(
        session,
        mutations=[
            AuditMutation(
                "organization.improvement.proposal.create",
                "organization_improvement_proposal",
                row.id,
                after_state=row,
                reason="authority-neutral improvement proposal lineage created",
            )
        ],
        context=context,
        refresh=(row,),
    )
    return row


def create_improvement_candidate(
    session: Session,
    context: OrganizationCommandContext,
    *,
    proposal_id: UUID,
    candidate_key: str,
    parent_candidate_id: UUID | None,
    candidate_version: str,
    candidate_fingerprint: str,
    artifact_reference: str,
    implementation_provenance: dict[str, Any],
    candidate_hypothesis: str,
    expected_improvement: str,
    acceptance_constraints: dict[str, Any],
) -> OrganizationImprovementCandidate:
    require_human(context, admin=True)
    proposal = tenant_record(
        session,
        OrganizationImprovementProposal,
        proposal_id,
        context.tenant_key,
        label="improvement proposal",
    )

    candidate_key = _required("candidate key", candidate_key)
    candidate_version = _required("candidate version", candidate_version)
    candidate_fingerprint = _sha256("candidate fingerprint", candidate_fingerprint)
    artifact_reference = _required("artifact reference", artifact_reference)
    candidate_hypothesis = _required("candidate hypothesis", candidate_hypothesis)
    expected_improvement = _required("expected improvement", expected_improvement)
    if not implementation_provenance:
        raise InvalidReference("improvement candidate requires implementation provenance")
    if not acceptance_constraints:
        raise InvalidReference("improvement candidate requires acceptance constraints")
    parent: OrganizationImprovementCandidate | None = None
    if parent_candidate_id is not None:
        parent = tenant_record(
            session,
            OrganizationImprovementCandidate,
            parent_candidate_id,
            context.tenant_key,
            label="parent improvement candidate",
        )
        if parent.proposal_id != proposal.id:
            raise InvalidReference("parent candidate must belong to the same improvement proposal")
        if parent.candidate_fingerprint == candidate_fingerprint:
            raise InvalidReference("child candidate fingerprint must differ from its parent")

    baseline_version = parent.candidate_version if parent is not None else proposal.baseline_version
    baseline_fingerprint = (
        parent.candidate_fingerprint if parent is not None else proposal.baseline_fingerprint
    )
    if candidate_fingerprint == baseline_fingerprint:
        raise InvalidReference("candidate fingerprint must differ from its effective baseline fingerprint")

    command = {
        "tenant_key": context.tenant_key,
        "proposal_id": str(proposal.id),
        "candidate_key": candidate_key,
        "parent_candidate_id": str(parent_candidate_id) if parent_candidate_id else None,
        "target_type": proposal.target_type,
        "target_reference": proposal.target_reference,
        "baseline_version": baseline_version,
        "baseline_fingerprint": baseline_fingerprint,
        "candidate_version": candidate_version,
        "candidate_fingerprint": candidate_fingerprint,
        "artifact_reference": artifact_reference,
        "implementation_provenance": implementation_provenance,
        "candidate_hypothesis": candidate_hypothesis,
        "expected_improvement": expected_improvement,
        "acceptance_constraints": acceptance_constraints,
        "status": "prepared",
    }
    fingerprint = canonical_fingerprint(command)
    existing = session.exec(
        select(OrganizationImprovementCandidate).where(
            OrganizationImprovementCandidate.tenant_key == context.tenant_key,
            OrganizationImprovementCandidate.candidate_key == candidate_key,
        )
    ).first()
    replay = idempotent_existing(
        existing,
        fingerprint,
        fingerprint_field="record_fingerprint",
        label="improvement candidate",
    )
    if replay is not None:
        return replay

    if not _proposal_is_current(session, proposal):
        raise InvalidTransition("candidate creation requires a current open improvement proposal")
    if parent is not None and parent.status != "prepared":
        raise InvalidTransition("withdrawn candidate cannot be used as a parent")

    row = OrganizationImprovementCandidate(
        tenant_key=context.tenant_key,
        candidate_key=candidate_key,
        proposal_id=proposal.id,
        parent_candidate_id=parent_candidate_id,
        target_type=proposal.target_type,
        target_reference=proposal.target_reference,
        baseline_version=baseline_version,
        baseline_fingerprint=baseline_fingerprint,
        candidate_version=candidate_version,
        candidate_fingerprint=candidate_fingerprint,
        artifact_reference=artifact_reference,
        implementation_provenance_json=canonical_payload_json(implementation_provenance),
        candidate_hypothesis=candidate_hypothesis,
        expected_improvement=expected_improvement,
        acceptance_constraints_json=canonical_payload_json(acceptance_constraints),
        status="prepared",
        record_fingerprint=fingerprint,
        created_by=context.actor_id,
    )
    session.add(row)
    commit_mutations(
        session,
        mutations=[
            AuditMutation(
                "organization.improvement.candidate.create",
                "organization_improvement_candidate",
                row.id,
                after_state=row,
                reason="authority-neutral improvement candidate lineage created",
            )
        ],
        context=context,
        refresh=(row,),
    )
    return row


def withdraw_improvement_proposal(
    session: Session,
    context: OrganizationCommandContext,
    *,
    proposal_id: UUID,
    reason: str,
) -> OrganizationImprovementProposal:
    require_human(context, admin=True)
    row = tenant_record(
        session,
        OrganizationImprovementProposal,
        proposal_id,
        context.tenant_key,
        label="improvement proposal",
    )
    reason = _required("withdrawal reason", reason)
    if row.status == "withdrawn":
        if row.withdrawn_by == context.actor_id and row.withdrawn_reason == reason:
            return row
        raise InvalidTransition("improvement proposal is already withdrawn")
    before = row.model_dump()
    row.status = "withdrawn"
    row.withdrawn_by = context.actor_id
    row.withdrawn_reason = reason
    row.withdrawn_at = now_utc()
    session.add(row)
    commit_mutations(
        session,
        mutations=[
            AuditMutation(
                "organization.improvement.proposal.withdraw",
                "organization_improvement_proposal",
                row.id,
                before_state=before,
                after_state=row,
                reason=reason,
            )
        ],
        context=context,
        refresh=(row,),
    )
    return row


def withdraw_improvement_candidate(
    session: Session,
    context: OrganizationCommandContext,
    *,
    candidate_id: UUID,
    reason: str,
) -> OrganizationImprovementCandidate:
    require_human(context, admin=True)
    row = tenant_record(
        session,
        OrganizationImprovementCandidate,
        candidate_id,
        context.tenant_key,
        label="improvement candidate",
    )
    reason = _required("withdrawal reason", reason)
    if row.status == "withdrawn":
        if row.withdrawn_by == context.actor_id and row.withdrawn_reason == reason:
            return row
        raise InvalidTransition("improvement candidate is already withdrawn")
    before = row.model_dump()
    row.status = "withdrawn"
    row.withdrawn_by = context.actor_id
    row.withdrawn_reason = reason
    row.withdrawn_at = now_utc()
    session.add(row)
    commit_mutations(
        session,
        mutations=[
            AuditMutation(
                "organization.improvement.candidate.withdraw",
                "organization_improvement_candidate",
                row.id,
                before_state=before,
                after_state=row,
                reason=reason,
            )
        ],
        context=context,
        refresh=(row,),
    )
    return row


def project_improvement_proposal(row: OrganizationImprovementProposal) -> ImprovementProposalRead:
    return ImprovementProposalRead(
        **row.model_dump(),
        acceptance_constraints=json.loads(row.acceptance_constraints_json),
        evidence_reference_ids=tuple(UUID(value) for value in json.loads(row.evidence_reference_ids_json)),
    )


def project_improvement_candidate(row: OrganizationImprovementCandidate) -> ImprovementCandidateRead:
    return ImprovementCandidateRead(
        **row.model_dump(),
        implementation_provenance=json.loads(row.implementation_provenance_json),
        acceptance_constraints=json.loads(row.acceptance_constraints_json),
    )


def list_improvement_proposals(
    session: Session,
    context: OrganizationCommandContext,
) -> tuple[ImprovementProposalRead, ...]:
    require_human(context, admin=True)
    rows = session.exec(
        select(OrganizationImprovementProposal)
        .where(OrganizationImprovementProposal.tenant_key == context.tenant_key)
        .order_by(OrganizationImprovementProposal.created_at.desc(), OrganizationImprovementProposal.id.desc())
    ).all()
    return tuple(project_improvement_proposal(row) for row in rows)


def list_improvement_candidates(
    session: Session,
    context: OrganizationCommandContext,
    *,
    proposal_id: UUID,
) -> tuple[ImprovementCandidateRead, ...]:
    require_human(context, admin=True)
    tenant_record(
        session,
        OrganizationImprovementProposal,
        proposal_id,
        context.tenant_key,
        label="improvement proposal",
    )
    rows = session.exec(
        select(OrganizationImprovementCandidate)
        .where(
            OrganizationImprovementCandidate.tenant_key == context.tenant_key,
            OrganizationImprovementCandidate.proposal_id == proposal_id,
        )
        .order_by(OrganizationImprovementCandidate.created_at, OrganizationImprovementCandidate.id)
    ).all()
    return tuple(project_improvement_candidate(row) for row in rows)
