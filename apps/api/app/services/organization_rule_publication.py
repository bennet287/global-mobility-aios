from __future__ import annotations

from sqlmodel import Session

from app.models.domain import (
    InitialRuleAssertion,
    OrganizationActorType,
    OrganizationContribution,
    OrganizationContributionImpactKind,
    VerifiedRule,
)
from app.services.organization_command import (
    AuthorityDenied,
    OrganizationCommandContext,
)
from app.services.organization_contribution import (
    stage_contribution,
    validate_initial_rule_publication_outcome,
)


DEFAULT_ORGANIZATION_TENANT = "default"
_PUBLICATION_ROLE_CONTEXT: dict[str, tuple[str, str, str]] = {
    "admin": ("executive", "board", "L4"),
    "reviewer": ("compliance", "reviewer", "L1"),
}


def initial_rule_publication_organization_context(
    *,
    actor: str,
    role: str,
) -> OrganizationCommandContext:
    """Build the trusted organization context for an authenticated rule publication."""

    identity = actor.strip()
    normalized_role = role.strip().lower()
    if not identity:
        raise AuthorityDenied("authenticated rule publisher is required")
    if normalized_role not in _PUBLICATION_ROLE_CONTEXT:
        raise AuthorityDenied(
            "initial-rule publication Contribution emission requires admin or reviewer authority"
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
        request_id=f"initial-rule-publication:{identity}",
    )


def initial_rule_publication_contribution_key(
    assertion: InitialRuleAssertion,
) -> str:
    if assertion.published_rule_id is None:
        raise AuthorityDenied("published rule identity is required for Contribution emission")
    return f"initial-rule-publication:{assertion.id}:{assertion.published_rule_id}"


def stage_initial_rule_publication_contribution(
    session: Session,
    context: OrganizationCommandContext,
    *,
    assertion: InitialRuleAssertion,
    rule: VerifiedRule,
) -> OrganizationContribution:
    """Stage one governed initial-rule publication outcome without committing.

    The initial-rule publication workflow remains the transaction owner. The caller
    commits the assertion transition, VerifiedRule creation, graph projection, source
    publication audits, coverage reconciliation, Contribution, and Contribution audit
    together.
    """

    descriptor = validate_initial_rule_publication_outcome(
        session,
        context,
        assertion_id=assertion.id,
        rule_id=rule.id,
        verification_basis=(
            "Authenticated publication of an independently reviewed initial rule assertion "
            "after approved coverage evidence, approved source certification, immutable "
            "source-snapshot provenance, publication attestation, and confidence gates"
        ),
    )
    published_at = descriptor.verified_at
    outcome_summary = (
        f"Published independently reviewed initial rule assertion {assertion.rule_key!r} "
        f"as verified rule {rule.id}. This Contribution records a governed knowledge "
        "publication outcome only; it does not establish applicant eligibility, occupation "
        "eligibility, visa approval, or pathway publication."
    )
    impact = {
        "jurisdiction_id": str(assertion.jurisdiction_id),
        "official_source_id": str(assertion.official_source_id),
        "source_snapshot_id": str(assertion.source_snapshot_id),
        "initial_rule_assertion_id": str(assertion.id),
        "verified_rule_id": str(rule.id),
        "domain": assertion.domain,
        "rule_key": assertion.rule_key,
        "confidence": assertion.confidence,
        "published": True,
    }
    evidence_summary = [
        {
            "source_type": "initial_rule_assertion",
            "source_id": str(assertion.id),
            "source_version": descriptor.source_version,
            "assertion_sha256": assertion.assertion_sha256,
            "reviewed_by": assertion.reviewed_by,
            "reviewed_at": assertion.reviewed_at,
            "published_by": assertion.published_by,
            "published_at": published_at,
            "verified_rule_id": str(rule.id),
            "source_snapshot_id": str(assertion.source_snapshot_id),
        }
    ]
    return stage_contribution(
        session,
        context,
        contribution_key=initial_rule_publication_contribution_key(assertion),
        descriptor=descriptor,
        contribution_type="verified_rule_publication_completed",
        title="Verified rule publication completed",
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
