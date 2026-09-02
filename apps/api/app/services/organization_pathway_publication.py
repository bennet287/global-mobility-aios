from __future__ import annotations

from sqlmodel import Session

from app.models.domain import (
    MobilityPathway,
    MobilityPathwayVersion,
    OrganizationActorType,
    OrganizationContribution,
    OrganizationContributionImpactKind,
)
from app.services.organization_command import AuthorityDenied, OrganizationCommandContext
from app.services.organization_contribution import (
    stage_contribution,
    validate_pathway_version_publication_outcome,
)


DEFAULT_ORGANIZATION_TENANT = "default"
_PUBLICATION_ROLE_CONTEXT: dict[str, tuple[str, str, str]] = {
    "admin": ("executive", "board", "L4"),
    "operator": ("operations", "pathway_operator", "L2"),
    "reviewer": ("compliance", "reviewer", "L1"),
}


def pathway_publication_organization_context(
    *,
    actor: str,
    role: str,
) -> OrganizationCommandContext:
    """Build trusted organization context for authenticated pathway publication."""

    identity = actor.strip()
    normalized_role = role.strip().lower()
    if not identity:
        raise AuthorityDenied("authenticated pathway publisher is required")
    if normalized_role not in _PUBLICATION_ROLE_CONTEXT:
        raise AuthorityDenied(
            "pathway publication Contribution emission requires admin, operator, or reviewer authority"
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
        request_id=f"pathway-publication:{identity}",
    )


def pathway_version_publication_contribution_key(
    version: MobilityPathwayVersion,
) -> str:
    return f"pathway-version-publication:{version.id}"


def stage_pathway_version_publication_contribution(
    session: Session,
    context: OrganizationCommandContext,
    *,
    pathway: MobilityPathway,
    version: MobilityPathwayVersion,
) -> OrganizationContribution:
    """Stage one governed pathway-version publication outcome without committing.

    The pathway catalogue remains transaction owner. The version publication,
    supersession of any previously published version, pathway activation, publication
    audit, Contribution, and Contribution audit commit together.
    """

    if version.pathway_id != pathway.id:
        raise AuthorityDenied("pathway version does not belong to the publication pathway")
    descriptor = validate_pathway_version_publication_outcome(
        session,
        context,
        pathway_version_id=version.id,
        verification_basis=(
            "Authenticated independent publication of an evidence-backed pathway version "
            "after the catalogue publication gate validated official-source evidence, "
            "required source certification, and active human-published verified rules"
        ),
    )
    published_at = descriptor.verified_at
    evidence_roles = list(descriptor.provenance.get("evidence_roles") or [])
    rule_state = list(descriptor.provenance.get("verified_rules") or [])
    outcome_summary = (
        f"Published governed pathway {pathway.pathway_key!r} version {version.version_number}. "
        "This Contribution records a catalogue publication outcome only; it does not "
        "establish applicant eligibility, occupation eligibility, visa approval, or an "
        "authority decision for any mobility case."
    )
    impact = {
        "pathway_id": str(pathway.id),
        "pathway_key": pathway.pathway_key,
        "pathway_name": pathway.name,
        "pathway_version_id": str(version.id),
        "version_number": version.version_number,
        "country": pathway.country,
        "domain": pathway.domain,
        "catalogue_status": pathway.catalogue_status,
        "lifecycle_status": version.lifecycle_status,
        "evidence_roles": evidence_roles,
        "verified_rule_ids": [str(item.get("id")) for item in rule_state],
        "published": True,
    }
    evidence_summary = [
        {
            "source_type": "mobility_pathway_version",
            "source_id": str(version.id),
            "source_version": descriptor.source_version,
            "pathway_id": str(pathway.id),
            "pathway_key": pathway.pathway_key,
            "version_number": version.version_number,
            "approved_by": version.approved_by,
            "published_at": published_at,
            "evidence_roles": evidence_roles,
            "verified_rule_ids": [str(item.get("id")) for item in rule_state],
        }
    ]
    return stage_contribution(
        session,
        context,
        contribution_key=pathway_version_publication_contribution_key(version),
        descriptor=descriptor,
        contribution_type="pathway_version_published",
        title="Pathway version publication completed",
        outcome_summary=outcome_summary,
        department=context.department or "operations",
        accountable_position_key=context.position_key or "pathway_operator",
        authority_level=context.authority_level or "L2",
        impact_kind=OrganizationContributionImpactKind.knowledge,
        effective_at=published_at,
        impact=impact,
        evidence_summary=evidence_summary,
        human_action_required=False,
    )
