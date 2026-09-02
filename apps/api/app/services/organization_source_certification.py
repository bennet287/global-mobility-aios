from __future__ import annotations

from typing import Any, Mapping

from sqlmodel import Session

from app.models.domain import (
    JurisdictionSourceCertification,
    OrganizationActorType,
    OrganizationContribution,
    OrganizationContributionImpactKind,
)
from app.services.organization_command import (
    AuthorityDenied,
    OrganizationCommandContext,
)
from app.services.organization_contribution import (
    stage_contribution,
    validate_source_certification_outcome,
)


DEFAULT_ORGANIZATION_TENANT = "default"
_REVIEW_ROLE_CONTEXT: dict[str, tuple[str, str, str]] = {
    "admin": ("executive", "board", "L4"),
    "reviewer": ("compliance", "reviewer", "L1"),
}


def source_certification_organization_context(
    *,
    actor: str,
    role: str,
) -> OrganizationCommandContext:
    """Build the narrow trusted organization context for an authenticated review route."""

    identity = actor.strip()
    normalized_role = role.strip().lower()
    if not identity:
        raise AuthorityDenied("authenticated source-certification reviewer is required")
    if normalized_role not in _REVIEW_ROLE_CONTEXT:
        raise AuthorityDenied(
            "source-certification Contribution emission requires admin or reviewer authority"
        )
    department, position_key, authority_level = _REVIEW_ROLE_CONTEXT[normalized_role]
    return OrganizationCommandContext(
        tenant_key=DEFAULT_ORGANIZATION_TENANT,
        actor_id=identity,
        actor_type=OrganizationActorType.human,
        authenticated_user_id=identity,
        role=normalized_role,
        department=department,
        position_key=position_key,
        authority_level=authority_level,
        request_id=f"source-certification-review:{identity}",
    )


def source_certification_contribution_key(
    certification: JurisdictionSourceCertification,
) -> str:
    return (
        "source-certification-review:"
        f"{certification.id}:v{certification.certification_version}:{certification.status}"
    )


def stage_source_certification_review_contribution(
    session: Session,
    context: OrganizationCommandContext,
    *,
    certification: JurisdictionSourceCertification,
    review_evidence: Mapping[str, Any],
) -> OrganizationContribution:
    """Stage one reviewed source-certification organizational outcome.

    The source transition remains the transaction owner. This function never commits;
    the caller commits the certification transition, source-review audit, Contribution,
    and Contribution audit together.
    """

    descriptor = validate_source_certification_outcome(
        session,
        context,
        certification_id=certification.id,
        review_evidence=review_evidence,
        verification_basis=(
            "Authenticated source-certification review with distinct proposer/reviewer"
            + (
                ", deterministic structured evidence pack, immutable source snapshot, "
                "and independent-human attestation"
                if review_evidence.get("structured_review_pack_required")
                else ""
            )
        ),
    )
    decision = certification.status
    reviewed_at = descriptor.verified_at
    title = f"Source certification review {decision}"
    outcome_summary = (
        f"Source-certification review {decision} certification version "
        f"{certification.certification_version} for scope {certification.certification_scope}. "
        "This Contribution records a governed source-review outcome only; it does not "
        "establish applicant eligibility, occupation eligibility, or pathway publication."
    )
    impact = {
        "decision": decision,
        "jurisdiction_id": str(certification.jurisdiction_id),
        "regulatory_authority_id": str(certification.regulatory_authority_id),
        "official_source_id": str(certification.official_source_id),
        "certification_scope": certification.certification_scope,
        "certification_version": certification.certification_version,
        "structured_review_pack_required": bool(
            review_evidence.get("structured_review_pack_required")
        ),
    }
    evidence_summary = [
        {
            "source_type": "jurisdiction_source_certification",
            "source_id": str(certification.id),
            "source_version": descriptor.source_version,
            "reviewed_by": certification.reviewed_by,
            "reviewed_at": reviewed_at,
            "review_evidence": dict(review_evidence),
        }
    ]
    return stage_contribution(
        session,
        context,
        contribution_key=source_certification_contribution_key(certification),
        descriptor=descriptor,
        contribution_type="source_certification_review_completed",
        title=title,
        outcome_summary=outcome_summary,
        department=context.department or "compliance",
        accountable_position_key=context.position_key or "reviewer",
        authority_level=context.authority_level or "L1",
        impact_kind=OrganizationContributionImpactKind.validation,
        effective_at=reviewed_at,
        impact=impact,
        evidence_summary=evidence_summary,
        human_action_required=False,
    )
