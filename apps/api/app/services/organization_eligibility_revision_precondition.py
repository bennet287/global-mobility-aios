from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlmodel import Session, select

from app.models.eligibility_revision import EligibilityAssessmentRevision


class EligibilityRevisionPreconditionError(RuntimeError):
    """Base error for G.5 canonical eligibility revision concurrency checks."""


class EligibilityRevisionPreconditionRequired(EligibilityRevisionPreconditionError):
    """A canonical eligibility aggregate exists but no expected revision was supplied."""


class EligibilityRevisionPreconditionStale(EligibilityRevisionPreconditionError):
    """The supplied canonical eligibility revision expectation is no longer current."""


class EligibilityRevisionPreconditionConflict(EligibilityRevisionPreconditionStale):
    """A previously current revision was superseded before this reassessment began.

    H.2.3 consumes this narrow subtype only for pre-provider optimistic-concurrency
    attribution. It is deliberately not raised for missing expectations, future/invalid
    expectations, a missing canonical revision, aggregate corruption, or the later
    post-provider revalidation boundary.
    """

    def __init__(
        self,
        *,
        tenant_key: str,
        aggregate_key: str,
        expected_revision_version: int,
        current_revision_id: UUID,
        current_revision_version: int,
    ) -> None:
        super().__init__("canonical eligibility revision precondition is stale")
        self.tenant_key = tenant_key
        self.aggregate_key = aggregate_key
        self.expected_revision_version = expected_revision_version
        self.current_revision_id = current_revision_id
        self.current_revision_version = current_revision_version


class EligibilityRevisionAggregateIntegrityError(EligibilityRevisionPreconditionError):
    """Canonical eligibility aggregate lifecycle state is internally inconsistent."""


@dataclass(frozen=True)
class EligibilityRevisionPrecondition:
    """Resolved optimistic-concurrency contract for one eligibility aggregate.

    ``expected_revision_version`` is deliberately distinct from the Governance
    Kernel's ``MaterialAction.expected_version``. The existing generic slot protects
    the immutable Profile version used by the eligibility action. G.5 needs a second,
    eligibility-specific precondition so reassessment cannot silently trade away that
    Profile guard.
    """

    tenant_key: str
    aggregate_key: str
    expected_revision_version: int | None
    current_revision_id: UUID | None
    current_revision_version: int | None
    next_revision_version: int
    supersedes_revision_id: UUID | None

    @property
    def is_reassessment(self) -> bool:
        return self.current_revision_id is not None


def eligibility_aggregate_key(
    *,
    tenant_key: str,
    lead_id: UUID,
    pathway_id: UUID,
) -> str:
    tenant = str(tenant_key or "").strip()
    if not tenant:
        raise EligibilityRevisionAggregateIntegrityError("tenant_key is required")
    return f"eligibility:{tenant}:{lead_id}:{pathway_id}"


def active_eligibility_revisions(
    session: Session,
    *,
    tenant_key: str,
    aggregate_key: str,
) -> tuple[EligibilityAssessmentRevision, ...]:
    return tuple(
        session.exec(
            select(EligibilityAssessmentRevision).where(
                EligibilityAssessmentRevision.tenant_key == tenant_key,
                EligibilityAssessmentRevision.aggregate_key == aggregate_key,
                EligibilityAssessmentRevision.lifecycle_status == "active",
            )
        ).all()
    )


def resolve_eligibility_revision_precondition(
    session: Session,
    *,
    tenant_key: str,
    lead_id: UUID,
    pathway_id: UUID,
    expected_revision_version: int | None,
) -> EligibilityRevisionPrecondition:
    """Resolve the only legal initial-create or reassessment revision transition.

    Contract:

    * no active revision + no expectation -> initial canonical revision v1;
    * active revision + no expectation -> fail closed; reassessment must be explicit;
    * no active revision + expectation -> stale expectation;
    * active revision version != expectation -> stale expectation;
    * active revision newer than expectation -> narrow pre-egress conflict subtype;
    * exact active revision expectation -> next revision supersedes that exact row.

    Multiple active revisions are always an aggregate-integrity failure. This helper
    does not mutate lifecycle state; the future G.5 effect transaction must revalidate
    this precondition immediately before staging supersession + the new revision.
    """

    if expected_revision_version is not None and expected_revision_version < 1:
        raise EligibilityRevisionPreconditionStale(
            "expected canonical eligibility revision version must be at least 1"
        )

    aggregate_key = eligibility_aggregate_key(
        tenant_key=tenant_key,
        lead_id=lead_id,
        pathway_id=pathway_id,
    )
    active = active_eligibility_revisions(
        session,
        tenant_key=tenant_key,
        aggregate_key=aggregate_key,
    )
    if len(active) > 1:
        raise EligibilityRevisionAggregateIntegrityError(
            "canonical eligibility aggregate has multiple active revisions"
        )

    current = active[0] if active else None
    if current is None:
        if expected_revision_version is not None:
            raise EligibilityRevisionPreconditionStale(
                "expected canonical eligibility revision does not exist"
            )
        return EligibilityRevisionPrecondition(
            tenant_key=tenant_key,
            aggregate_key=aggregate_key,
            expected_revision_version=None,
            current_revision_id=None,
            current_revision_version=None,
            next_revision_version=1,
            supersedes_revision_id=None,
        )

    if expected_revision_version is None:
        raise EligibilityRevisionPreconditionRequired(
            "canonical eligibility reassessment requires expected revision version"
        )
    if current.version != expected_revision_version:
        if expected_revision_version < current.version:
            raise EligibilityRevisionPreconditionConflict(
                tenant_key=tenant_key,
                aggregate_key=aggregate_key,
                expected_revision_version=expected_revision_version,
                current_revision_id=current.id,
                current_revision_version=current.version,
            )
        raise EligibilityRevisionPreconditionStale(
            "canonical eligibility revision precondition is stale"
        )

    return EligibilityRevisionPrecondition(
        tenant_key=tenant_key,
        aggregate_key=aggregate_key,
        expected_revision_version=expected_revision_version,
        current_revision_id=current.id,
        current_revision_version=current.version,
        next_revision_version=current.version + 1,
        supersedes_revision_id=current.id,
    )


def require_eligibility_revision_precondition_current(
    session: Session,
    *,
    precondition: EligibilityRevisionPrecondition,
    lead_id: UUID,
    pathway_id: UUID,
) -> EligibilityRevisionPrecondition:
    """Re-resolve a previously accepted precondition and reject any intervening change."""

    try:
        current = resolve_eligibility_revision_precondition(
            session,
            tenant_key=precondition.tenant_key,
            lead_id=lead_id,
            pathway_id=pathway_id,
            expected_revision_version=precondition.expected_revision_version,
        )
    except EligibilityRevisionPreconditionError as exc:
        # Deliberately collapse any later race back to the generic stale type. H.2.3
        # attributes only conflicts known before provider egress; a revision change
        # discovered after runtime latency is a separate failure model.
        raise EligibilityRevisionPreconditionStale(
            "canonical eligibility revision changed after precondition resolution"
        ) from exc

    if (
        current.aggregate_key != precondition.aggregate_key
        or current.current_revision_id != precondition.current_revision_id
        or current.current_revision_version != precondition.current_revision_version
        or current.next_revision_version != precondition.next_revision_version
        or current.supersedes_revision_id != precondition.supersedes_revision_id
    ):
        raise EligibilityRevisionPreconditionStale(
            "canonical eligibility revision changed after precondition resolution"
        )
    return current
