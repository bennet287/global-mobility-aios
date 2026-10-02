from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from app.models.domain import (
    ExecutiveDecision,
    OrganizationBlocker,
    OrganizationHumanAction,
    OrganizationHumanActionRequest,
    OrganizationHumanActionType,
    OrganizationRecordReference,
    OrganizationReferenceRole,
    OrganizationalWorkItem,
)
from app.models.organization_improvement_evaluation import OrganizationImprovementEvaluationCampaign
from app.models.organization_improvement_lineage import (
    OrganizationImprovementCandidate,
    OrganizationImprovementProposal,
)
from app.models.organization_improvement_review import OrganizationImprovementReviewPackage
from app.schemas_organization_improvement_review import (
    ImprovementReviewArtifactRead,
    ImprovementReviewBindingCreate,
    ImprovementReviewPackageRead,
    ImprovementReviewRequirementRead,
)
from app.services.organization_command import (
    AuditMutation,
    InvalidReference,
    InvalidTransition,
    OrganizationCommandContext,
    canonical_fingerprint,
    canonical_json,
    commit_mutations,
    idempotent_existing,
    require_human,
    tenant_record,
)
from app.services.organization_improvement_lineage import _proposal_is_current


REVIEW_POLICY_KEY = "grsi-cross-team-review"
REVIEW_POLICY_VERSION = 1
REVIEW_POLICY_REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "low": ("qa", "domain"),
    "medium": ("qa", "domain", "platform_sre", "governance"),
    "high": ("security_red_team", "qa", "domain", "platform_sre", "governance"),
    "critical": ("security_red_team", "qa", "domain", "platform_sre", "governance"),
}
REVIEW_POLICY_FINGERPRINT = canonical_fingerprint(
    {
        "policy_key": REVIEW_POLICY_KEY,
        "policy_version": REVIEW_POLICY_VERSION,
        "requirements": {key: list(value) for key, value in REVIEW_POLICY_REQUIREMENTS.items()},
        "semantics": "review evidence requirements only; no authority or promotion granted",
    }
)

_CANDIDATE_SOURCE_TYPE = "organization_improvement_candidate"
_EVIDENCE_ROLES = frozenset(
    {
        OrganizationReferenceRole.evidence,
        OrganizationReferenceRole.supports,
        OrganizationReferenceRole.governance_mapping,
    }
)
_ALLOWED_REVIEW_POSITIONS: dict[str, frozenset[str] | None] = {
    "security_red_team": frozenset(
        {
            "ciso",
            "security_lead",
            "application_security_engineer",
            "threat_analyst",
            "vulnerability_management_engineer",
        }
    ),
    "qa": frozenset({"qa_automation_engineer", "vp_engineering", "lead_software_engineer"}),
    "domain": None,
    "platform_sre": frozenset(
        {"platform_engineer", "site_reliability_engineer", "vp_engineering", "cto"}
    ),
    "governance": frozenset({"security_grc_lead", "ciso", "clo", "ceo", "board", "owner"}),
}
_ARTIFACT_MODELS = {
    "human_action_request": OrganizationHumanActionRequest,
    "human_action": OrganizationHumanAction,
    "decision": ExecutiveDecision,
    "work_item": OrganizationalWorkItem,
    "blocker": OrganizationBlocker,
}
_REFERENCE_OWNER_FIELDS = {
    "human_action_request": OrganizationRecordReference.human_action_request_id,
    "human_action": OrganizationRecordReference.human_action_id,
    "decision": OrganizationRecordReference.decision_id,
    "work_item": OrganizationRecordReference.work_item_id,
    "blocker": OrganizationRecordReference.blocker_id,
}


def _required(label: str, value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise InvalidReference(f"{label} is required")
    return normalized


def _risk_basis_ids(
    session: Session,
    context: OrganizationCommandContext,
    reference_ids: list[UUID],
) -> tuple[UUID, ...]:
    if not reference_ids or len(set(reference_ids)) != len(reference_ids):
        raise InvalidReference("review package requires unique risk-basis evidence references")
    resolved: list[UUID] = []
    for reference_id in reference_ids:
        row = tenant_record(
            session,
            OrganizationRecordReference,
            reference_id,
            context.tenant_key,
            label="review package risk-basis evidence",
        )
        if row.reference_role not in _EVIDENCE_ROLES:
            raise InvalidReference(
                "review package risk-basis references must be evidence, supports or governance-mapping references"
            )
        resolved.append(row.id)
    return tuple(sorted(resolved, key=str))


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
        raise InvalidTransition("cross-team review requires a prepared improvement candidate")
    proposal = tenant_record(
        session,
        OrganizationImprovementProposal,
        candidate.proposal_id,
        context.tenant_key,
        label="improvement proposal",
    )
    if not _proposal_is_current(session, proposal):
        raise InvalidTransition("cross-team review requires a current open improvement proposal")
    return candidate, proposal


def _candidate_source_values(candidate: OrganizationImprovementCandidate) -> tuple[str, str, str]:
    return _CANDIDATE_SOURCE_TYPE, str(candidate.id), candidate.candidate_fingerprint


def _assert_candidate_source(row: Any, candidate: OrganizationImprovementCandidate) -> None:
    expected = _candidate_source_values(candidate)
    actual = (
        getattr(row, "source_object_type", None),
        getattr(row, "source_object_id", None),
        getattr(row, "source_object_version", None),
    )
    if actual != expected:
        raise InvalidReference(
            "review artifact must point to the exact improvement candidate id and candidate fingerprint"
        )


def _artifact_reviewer_position(artifact_type: str, row: Any) -> str | None:
    if artifact_type == "human_action_request":
        return row.required_role
    if artifact_type == "human_action":
        return row.actor_position_key
    if artifact_type == "decision":
        return row.decision_owner_position
    if artifact_type == "work_item":
        return row.assigned_position_key
    if artifact_type == "blocker":
        return row.accountable_position_key
    return None


def _validate_review_position(review_kind: str, reviewer_position_key: str) -> None:
    reviewer_position_key = _required("reviewer position key", reviewer_position_key)
    allowed = _ALLOWED_REVIEW_POSITIONS[review_kind]
    if allowed is not None and reviewer_position_key not in allowed:
        raise InvalidReference(
            f"{review_kind} review requires a reviewer position from the canonical review-owner set"
        )


def _resolve_binding(
    session: Session,
    context: OrganizationCommandContext,
    candidate: OrganizationImprovementCandidate,
    raw: ImprovementReviewBindingCreate | dict[str, Any],
    required_review_kinds: tuple[str, ...],
) -> dict[str, str]:
    item = raw.model_dump() if isinstance(raw, ImprovementReviewBindingCreate) else dict(raw)
    review_kind = str(item.get("review_kind") or "").strip()
    artifact_type = str(item.get("artifact_type") or "").strip()
    artifact_id = item.get("artifact_id")
    reviewer_position_key = str(item.get("reviewer_position_key") or "").strip()

    if review_kind not in required_review_kinds:
        raise InvalidReference("review binding kind is not required by this candidate risk class")
    if artifact_type not in _ARTIFACT_MODELS:
        raise InvalidReference("review binding artifact type is unsupported")
    if not isinstance(artifact_id, UUID):
        try:
            artifact_id = UUID(str(artifact_id))
        except (TypeError, ValueError) as exc:
            raise InvalidReference("review binding artifact id is invalid") from exc

    _validate_review_position(review_kind, reviewer_position_key)
    row = tenant_record(
        session,
        _ARTIFACT_MODELS[artifact_type],
        artifact_id,
        context.tenant_key,
        label=f"{review_kind} review artifact",
    )
    _assert_candidate_source(row, candidate)
    actual_position = _artifact_reviewer_position(artifact_type, row)
    if actual_position != reviewer_position_key:
        raise InvalidReference(
            "review binding reviewer position must match the canonical artifact reviewer/owner position"
        )
    return {
        "review_kind": review_kind,
        "artifact_type": artifact_type,
        "artifact_id": str(artifact_id),
        "reviewer_position_key": reviewer_position_key,
    }


def _normalize_bindings(
    session: Session,
    context: OrganizationCommandContext,
    candidate: OrganizationImprovementCandidate,
    bindings: list[ImprovementReviewBindingCreate | dict[str, Any]],
    required_review_kinds: tuple[str, ...],
) -> tuple[dict[str, str], ...]:
    normalized = tuple(
        _resolve_binding(session, context, candidate, raw, required_review_kinds)
        for raw in bindings
    )
    identities = {
        (item["review_kind"], item["artifact_type"], item["artifact_id"])
        for item in normalized
    }
    if len(identities) != len(normalized):
        raise InvalidReference("review bindings must be unique")
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item["review_kind"],
                item["artifact_type"],
                item["artifact_id"],
            ),
        )
    )


def _package_is_current(
    session: Session,
    row: OrganizationImprovementReviewPackage,
) -> bool:
    successor = session.exec(
        select(OrganizationImprovementReviewPackage.id).where(
            OrganizationImprovementReviewPackage.tenant_key == row.tenant_key,
            OrganizationImprovementReviewPackage.supersedes_package_id == row.id,
        )
    ).first()
    return successor is None


def create_review_package(
    session: Session,
    context: OrganizationCommandContext,
    *,
    package_key: str,
    package_version: int,
    candidate_id: UUID,
    evaluation_campaign_id: UUID,
    risk_class: str,
    risk_basis_reference_ids: list[UUID],
    review_bindings: list[ImprovementReviewBindingCreate | dict[str, Any]],
    supersedes_package_id: UUID | None = None,
) -> OrganizationImprovementReviewPackage:
    require_human(context, admin=True)
    package_key = _required("review package key", package_key)
    if package_version < 1:
        raise InvalidReference("review package version must be positive")
    if risk_class not in REVIEW_POLICY_REQUIREMENTS:
        raise InvalidReference("candidate risk class is unsupported")

    candidate, proposal = _candidate_and_proposal(session, context, candidate_id)
    campaign = tenant_record(
        session,
        OrganizationImprovementEvaluationCampaign,
        evaluation_campaign_id,
        context.tenant_key,
        label="improvement evaluation campaign",
    )
    if campaign.candidate_id != candidate.id or campaign.proposal_id != proposal.id:
        raise InvalidReference("review package evaluation campaign must belong to the same candidate")
    if campaign.candidate_fingerprint != candidate.candidate_fingerprint:
        raise InvalidReference("review package evaluation campaign candidate fingerprint is stale")

    risk_basis_ids = _risk_basis_ids(session, context, risk_basis_reference_ids)
    required_review_kinds = REVIEW_POLICY_REQUIREMENTS[risk_class]
    normalized_bindings = _normalize_bindings(
        session,
        context,
        candidate,
        review_bindings,
        required_review_kinds,
    )

    predecessor: OrganizationImprovementReviewPackage | None = None
    if package_version == 1:
        if supersedes_package_id is not None:
            raise InvalidReference("first review package version cannot supersede another package")
    else:
        if supersedes_package_id is None:
            raise InvalidReference("later review package versions must identify the package they supersede")
        predecessor = tenant_record(
            session,
            OrganizationImprovementReviewPackage,
            supersedes_package_id,
            context.tenant_key,
            label="superseded review package",
        )
        if predecessor.candidate_id != candidate.id:
            raise InvalidReference("review package supersession must retain the same candidate")
        if predecessor.package_version + 1 != package_version:
            raise InvalidReference("review package versions must advance consecutively")

    command = {
        "tenant_key": context.tenant_key,
        "package_key": package_key,
        "package_version": package_version,
        "candidate_id": str(candidate.id),
        "proposal_id": str(proposal.id),
        "evaluation_campaign_id": str(campaign.id),
        "candidate_fingerprint": candidate.candidate_fingerprint,
        "risk_class": risk_class,
        "risk_basis_reference_ids": [str(value) for value in risk_basis_ids],
        "review_policy_key": REVIEW_POLICY_KEY,
        "review_policy_version": REVIEW_POLICY_VERSION,
        "review_policy_fingerprint": REVIEW_POLICY_FINGERPRINT,
        "required_review_kinds": list(required_review_kinds),
        "review_bindings": list(normalized_bindings),
        "supersedes_package_id": str(supersedes_package_id) if supersedes_package_id else None,
    }
    fingerprint = canonical_fingerprint(command)
    existing = session.exec(
        select(OrganizationImprovementReviewPackage).where(
            OrganizationImprovementReviewPackage.tenant_key == context.tenant_key,
            OrganizationImprovementReviewPackage.package_key == package_key,
        )
    ).first()
    replay = idempotent_existing(
        existing,
        fingerprint,
        fingerprint_field="record_fingerprint",
        label="improvement review package",
    )
    if replay is not None:
        return replay

    if predecessor is not None and not _package_is_current(session, predecessor):
        raise InvalidTransition("only the current review package may be superseded")

    version_collision = session.exec(
        select(OrganizationImprovementReviewPackage.id).where(
            OrganizationImprovementReviewPackage.tenant_key == context.tenant_key,
            OrganizationImprovementReviewPackage.candidate_id == candidate.id,
            OrganizationImprovementReviewPackage.package_version == package_version,
        )
    ).first()
    if version_collision is not None:
        raise InvalidTransition("review package version already exists for this candidate")

    row = OrganizationImprovementReviewPackage(
        tenant_key=context.tenant_key,
        package_key=package_key,
        package_version=package_version,
        candidate_id=candidate.id,
        proposal_id=proposal.id,
        evaluation_campaign_id=campaign.id,
        candidate_fingerprint=candidate.candidate_fingerprint,
        risk_class=risk_class,
        risk_basis_reference_ids_json=canonical_json([str(value) for value in risk_basis_ids]),
        review_policy_key=REVIEW_POLICY_KEY,
        review_policy_version=REVIEW_POLICY_VERSION,
        review_policy_fingerprint=REVIEW_POLICY_FINGERPRINT,
        required_review_kinds_json=canonical_json(list(required_review_kinds)),
        review_bindings_json=canonical_json(list(normalized_bindings)),
        supersedes_package_id=supersedes_package_id,
        record_fingerprint=fingerprint,
        created_by=context.actor_id,
    )
    session.add(row)
    commit_mutations(
        session,
        mutations=[
            AuditMutation(
                "organization.improvement.review_package.create",
                "organization_improvement_review_package",
                row.id,
                after_state=row,
                reason="candidate-bound cross-team review requirements recorded; no approval or authority granted",
            )
        ],
        context=context,
        refresh=(row,),
    )
    return row


def _status_value(value: Any) -> str:
    return str(getattr(value, "value", value))


def _human_action_evidence_status(row: OrganizationHumanAction) -> str:
    action_type = _status_value(row.action_type)
    if action_type in {"reviewed", "approved", "attested", "resolved"}:
        return "satisfied"
    if action_type in {"rejected", "requested_changes", "declined", "cancelled"}:
        return "failed"
    if action_type in {"acknowledged", "assigned", "reassigned"}:
        return "pending"
    return "unknown"


def _aggregate_status(statuses: list[str], *, absent: str = "absent") -> str:
    if not statuses:
        return absent
    if "failed" in statuses:
        return "failed"
    if "satisfied" in statuses:
        return "satisfied"
    if "pending" in statuses:
        return "pending"
    return "unknown"


def _request_evidence_status(
    session: Session,
    row: OrganizationHumanActionRequest,
) -> str:
    actions = session.exec(
        select(OrganizationHumanAction).where(
            OrganizationHumanAction.tenant_key == row.tenant_key,
            OrganizationHumanAction.human_action_request_id == row.id,
        )
    ).all()
    if actions:
        return _aggregate_status([_human_action_evidence_status(action) for action in actions])
    status = _status_value(row.status)
    if status in {"declined", "cancelled", "expired"}:
        return "failed"
    if status == "completed":
        return "unknown"
    return "pending"


def _artifact_evidence_status(
    session: Session,
    artifact_type: str,
    row: Any,
) -> tuple[str, str]:
    if artifact_type == "human_action_request":
        return _status_value(row.status), _request_evidence_status(session, row)
    if artifact_type == "human_action":
        return _status_value(row.action_type), _human_action_evidence_status(row)
    if artifact_type == "decision":
        status = str(row.status)
        if status == "approved":
            return status, "satisfied"
        if status in {"rejected", "returned", "expired", "superseded"}:
            return status, "failed"
        return status, "pending"
    if artifact_type == "work_item":
        status = str(row.status)
        if status in {"cancelled", "failed"}:
            return status, "failed"
        if status == "completed":
            return status, "unknown"
        return status, "pending"
    if artifact_type == "blocker":
        status = _status_value(row.status)
        if status in {"open", "mitigated"}:
            return status, "failed"
        return status, "unknown"
    raise InvalidReference("review binding artifact type is unsupported")


def _artifact_evidence_reference_ids(
    session: Session,
    tenant_key: str,
    artifact_type: str,
    artifact_id: UUID,
) -> tuple[UUID, ...]:
    owner_field = _REFERENCE_OWNER_FIELDS[artifact_type]
    rows = session.exec(
        select(OrganizationRecordReference).where(
            OrganizationRecordReference.tenant_key == tenant_key,
            owner_field == artifact_id,
        )
    ).all()
    return tuple(
        sorted(
            (row.id for row in rows if row.reference_role in _EVIDENCE_ROLES),
            key=str,
        )
    )


def _artifact_projection(
    session: Session,
    context: OrganizationCommandContext,
    candidate: OrganizationImprovementCandidate,
    binding: dict[str, str],
) -> ImprovementReviewArtifactRead:
    artifact_type = binding["artifact_type"]
    artifact_id = UUID(binding["artifact_id"])
    row = tenant_record(
        session,
        _ARTIFACT_MODELS[artifact_type],
        artifact_id,
        context.tenant_key,
        label=f"{binding['review_kind']} review artifact",
    )
    _assert_candidate_source(row, candidate)
    actual_position = _artifact_reviewer_position(artifact_type, row)
    if actual_position != binding["reviewer_position_key"]:
        raise InvalidReference("review artifact reviewer/owner position no longer matches package lineage")
    canonical_status, evidence_status = _artifact_evidence_status(session, artifact_type, row)
    return ImprovementReviewArtifactRead(
        review_kind=binding["review_kind"],
        artifact_type=artifact_type,
        artifact_id=artifact_id,
        reviewer_position_key=binding["reviewer_position_key"],
        canonical_status=canonical_status,
        evidence_status=evidence_status,
        evidence_reference_ids=_artifact_evidence_reference_ids(
            session,
            context.tenant_key,
            artifact_type,
            artifact_id,
        ),
    )


def _evaluation_status(campaign: OrganizationImprovementEvaluationCampaign) -> str:
    if campaign.status != "closed":
        return "pending"
    if campaign.comparison_conclusion == "constraints_met":
        return "satisfied"
    if campaign.comparison_conclusion == "constraints_not_met":
        return "failed"
    return "unknown"


def project_review_package(
    session: Session,
    context: OrganizationCommandContext,
    row: OrganizationImprovementReviewPackage,
) -> ImprovementReviewPackageRead:
    require_human(context, admin=True)
    candidate = tenant_record(
        session,
        OrganizationImprovementCandidate,
        row.candidate_id,
        context.tenant_key,
        label="improvement candidate",
    )
    if candidate.candidate_fingerprint != row.candidate_fingerprint:
        raise InvalidReference("review package candidate fingerprint no longer matches candidate lineage")
    campaign = tenant_record(
        session,
        OrganizationImprovementEvaluationCampaign,
        row.evaluation_campaign_id,
        context.tenant_key,
        label="improvement evaluation campaign",
    )
    bindings = tuple(json.loads(row.review_bindings_json))
    required_review_kinds = tuple(json.loads(row.required_review_kinds_json))
    artifacts = tuple(
        _artifact_projection(session, context, candidate, binding)
        for binding in bindings
    )
    requirements: list[ImprovementReviewRequirementRead] = []
    for review_kind in required_review_kinds:
        matching = tuple(artifact for artifact in artifacts if artifact.review_kind == review_kind)
        requirements.append(
            ImprovementReviewRequirementRead(
                review_kind=review_kind,
                status=_aggregate_status([artifact.evidence_status for artifact in matching]),
                artifacts=matching,
            )
        )
    evaluation_status = _evaluation_status(campaign)
    is_current = _package_is_current(session, row)
    promotion_evidence_complete = (
        is_current
        and evaluation_status == "satisfied"
        and all(requirement.status == "satisfied" for requirement in requirements)
    )
    return ImprovementReviewPackageRead(
        **row.model_dump(),
        risk_basis_reference_ids=tuple(
            UUID(value) for value in json.loads(row.risk_basis_reference_ids_json)
        ),
        required_review_kinds=required_review_kinds,
        review_requirements=tuple(requirements),
        evaluation_status=evaluation_status,
        is_current=is_current,
        promotion_evidence_complete_for_decision=promotion_evidence_complete,
    )


def get_review_package(
    session: Session,
    context: OrganizationCommandContext,
    *,
    package_id: UUID,
) -> ImprovementReviewPackageRead:
    require_human(context, admin=True)
    row = tenant_record(
        session,
        OrganizationImprovementReviewPackage,
        package_id,
        context.tenant_key,
        label="improvement review package",
    )
    return project_review_package(session, context, row)


def list_review_packages(
    session: Session,
    context: OrganizationCommandContext,
) -> tuple[ImprovementReviewPackageRead, ...]:
    require_human(context, admin=True)
    rows = session.exec(
        select(OrganizationImprovementReviewPackage)
        .where(OrganizationImprovementReviewPackage.tenant_key == context.tenant_key)
        .order_by(
            OrganizationImprovementReviewPackage.created_at.desc(),
            OrganizationImprovementReviewPackage.id.desc(),
        )
    ).all()
    return tuple(project_review_package(session, context, row) for row in rows)
