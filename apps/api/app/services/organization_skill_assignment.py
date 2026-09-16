from __future__ import annotations

from uuid import UUID

from sqlmodel import Session

from app.models.domain import OrganizationalWorkItem
from app.services.organization_command import (
    AuthorityDenied,
    OrganizationCommandContext,
    require_human,
    tenant_record,
)
from app.services.organization_skill_work_matching import find_skill_work_candidates
from app.services.organization_work import assign_work_item


class SkillAssignmentDenied(AuthorityDenied):
    """The requested skill-informed assignment did not satisfy the governed gate."""


def assign_skill_candidate_to_work(
    session: Session,
    context: OrganizationCommandContext,
    *,
    work_item_id: UUID,
    assigned_position_key: str,
    capability_family: str,
    reason: str,
) -> OrganizationalWorkItem:
    """Assign an eligible skill candidate only after explicit human-admin approval.

    Candidate matching remains capability evidence, never authority. Phase 14.7
    deliberately requires an authenticated internal human administrator before the
    existing canonical work-assignment mutation may run. This gate grants no tool,
    permission, credential, autonomy, or execution rights; those remain separate
    governed concerns and unresolved skill prerequisites continue to fail closed in
    the Phase 14.6 matcher.
    """
    require_human(context, admin=True)
    position_key = assigned_position_key.strip()
    if not position_key:
        raise SkillAssignmentDenied("assigned_position_key is required")
    if not reason.strip():
        raise SkillAssignmentDenied("assignment reason is required")

    work_item = tenant_record(
        session,
        OrganizationalWorkItem,
        work_item_id,
        context.tenant_key,
        label="work item",
    )
    candidate_set = find_skill_work_candidates(
        session,
        work_item=work_item,
        capability_family=capability_family,
    )
    if not any(candidate.position_key == position_key for candidate in candidate_set.candidates):
        raise SkillAssignmentDenied(
            "position is not an eligible validated skill candidate for this work item"
        )

    # Reuse the canonical assignment transaction, audit evidence and semantic
    # activity path. Do not create a second assignment truth or execution path.
    return assign_work_item(
        session,
        context,
        work_item_id=work_item_id,
        assigned_position_key=position_key,
        reason=reason.strip(),
    )
