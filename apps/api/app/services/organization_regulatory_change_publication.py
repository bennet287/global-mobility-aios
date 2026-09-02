from __future__ import annotations

from sqlmodel import Session

from app.models.domain import (
    OrganizationActorType,
    OrganizationContribution,
    OrganizationContributionImpactKind,
    RegulatoryChange,
    VerifiedRule,
)
from app.services.organization_command import AuthorityDenied, OrganizationCommandContext
from app.services.organization_contribution import (
    stage_contribution,
    validate_regulatory_change_publication_outcome,
)


DEFAULT_ORGANIZATION_TENANT = "default"
_PUBLICATION_ROLE_CONTEXT: dict[str, tuple[str, str, str]] = {
    "admin": ("executive", "board", "L4"),
    "reviewer": ("compliance", "reviewer", "L1"),
}


def regulatory_change_publication_organization_context(
    *,
    actor: str,
    role: str,
) -> OrganizationCommandContext:
    """Build the trusted organization context for authenticated regulatory publication."""

    identity = actor.strip()
    normalized_role = role.strip().lower()
    if not identity:
        raise AuthorityDenied("authenticated regulatory-change publisher is required")
    if normalized_role not in _PUBLICATION_ROLE_CONTEXT:
        raise AuthorityDenied(
            "regulatory-change publication Contribution emission requires admin or reviewer authority"
        )
    department, position_key, authority_level = _PUBLICATION_ROLE_CONTEXT[normalized_role]
    return OrganizationCommandContext(
        tenant_key=DEFAULT_ORGANIZATION_TENANT,
        actor_id=identity,
        actor_type=OrganizationActorType.human,
        authenticated_user_id=identity,
        role=normalized_role,
        department=department,
        position_key=position_key,
        authority_level=authority_level,
        request_id=f"regulatory-change-publication:{identity}",
    )


def regulatory_change_publication_contribution_key(
    change: RegulatoryChange,
    rule: VerifiedRule,
) -> str:
    return f"regulatory-change-publication:{change.id}:{rule.id}"


def stage_regulatory_change_publication_contribution(
    session: Session,
    context: OrganizationCommandContext,
    *,
    change: RegulatoryChange,
    rule: VerifiedRule,
) -> OrganizationContribution:
    """Stage one reviewed regulatory-change publication outcome without committing.

    The regulatory publication workflow remains transaction owner. The source state,
    supersession (when present), knowledge-graph projection, source audits,
    Contribution, and Contribution audit commit together.
    """

    descriptor = validate_regulatory_change_publication_outcome(
        session,
        context,
        change_id=change.id,
        rule_id=rule.id,
        verification_basis=(
            "Authenticated publication of a previously reviewed regulatory change from "
            "its immutable official-source snapshot into an active VerifiedRule"
        ),
    )
    published_at = descriptor.verified_at
    outcome_summary = (
        f"Published reviewed regulatory change {change.id} as verified rule {rule.id}. "
        "This Contribution records a governed regulatory-knowledge publication outcome "
        "only; it does not establish applicant eligibility, occupation eligibility, visa "
        "approval, or pathway publication."
    )
    impact = {
        "jurisdiction_id": str(change.jurisdiction_id),
        "official_source_id": str(change.official_source_id),
        "previous_snapshot_id": str(change.previous_snapshot_id) if change.previous_snapshot_id else None,
        "current_snapshot_id": str(change.current_snapshot_id),
        "regulatory_change_id": str(change.id),
        "verified_rule_id": str(rule.id),
        "supersedes_rule_id": str(rule.supersedes_rule_id) if rule.supersedes_rule_id else None,
        "domain": change.domain,
        "change_type": change.change_type,
        "materiality": change.materiality,
        "published": True,
    }
    evidence_summary = [
        {
            "source_type": "regulatory_change",
            "source_id": str(change.id),
            "source_version": descriptor.source_version,
            "reviewed_by": change.reviewed_by,
            "reviewed_at": change.reviewed_at,
            "published_by": rule.approved_by,
            "published_at": published_at,
            "verified_rule_id": str(rule.id),
            "source_snapshot_id": str(change.current_snapshot_id),
            "supersedes_rule_id": str(rule.supersedes_rule_id) if rule.supersedes_rule_id else None,
        }
    ]
    return stage_contribution(
        session,
        context,
        contribution_key=regulatory_change_publication_contribution_key(change, rule),
        descriptor=descriptor,
        contribution_type="regulatory_change_publication_completed",
        title="Regulatory change publication completed",
        outcome_summary=outcome_summary,
        department=context.department or "compliance",
        accountable_position_key=context.position_key or "reviewer",
        authority_level=context.authority_level or "L1",
        impact_kind=OrganizationContributionImpactKind.knowledge,
        effective_at=published_at,
        impact=impact,
        evidence_summary=evidence_summary,
        human_action_required=False,
    )
