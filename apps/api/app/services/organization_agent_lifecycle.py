from __future__ import annotations

from uuid import UUID

from sqlmodel import Session, select

from app.models.agent_lifecycle import OrganizationAgent, now_utc
from app.services.audit_log import record_audit
from app.services.organization_command import InvalidTransition, NotFound


AGENT_LIFECYCLE_AUDIT_SOURCE = "organization_agent_lifecycle_v15.2"
AGENT_LIFECYCLE_AUDIT_ACTION = "organization_agent.lifecycle_transitioned"

# Phase 15.2 implements only the sealed forward lifecycle. Recovery, authority,
# execution, assignment, autonomy and credential semantics are deliberately absent.
ALLOWED_AGENT_LIFECYCLE_TRANSITIONS: dict[str, frozenset[str]] = {
    "created": frozenset({"onboarding"}),
    "onboarding": frozenset({"inactive"}),
    "inactive": frozenset({"active"}),
    "active": frozenset({"restricted", "suspended"}),
    "restricted": frozenset({"retired"}),
    "suspended": frozenset({"retired"}),
    "retired": frozenset(),
}


def organization_agent_audit_state(
    agent: OrganizationAgent | None,
) -> dict[str, object] | None:
    """Return bounded lifecycle evidence without inventing entitlement state."""

    if agent is None:
        return None
    return {
        "id": str(agent.id),
        "agent_key": agent.agent_key,
        "registry_key": agent.registry_key,
        "registry_version": agent.registry_version,
        "department": agent.department,
        "position_key": agent.position_key,
        "status": agent.status,
        "lifecycle_reason": agent.lifecycle_reason,
        "updated_at": agent.updated_at,
        "activated_at": agent.activated_at,
        "suspended_at": agent.suspended_at,
        "retired_at": agent.retired_at,
    }


def transition_organization_agent(
    session: Session,
    *,
    agent_id: UUID,
    target_status: str,
    reason: str,
    actor: str,
) -> OrganizationAgent:
    """Stage one explicit lifecycle transition and its audit evidence.

    The caller owns the transaction. This service never grants authority,
    permissions, credentials, autonomy, tools, work, routing or execution.
    """

    clean_target = target_status.strip()
    clean_reason = reason.strip()
    clean_actor = actor.strip()
    if not clean_target:
        raise ValueError("target_status is required")
    if not clean_reason:
        raise ValueError("transition reason is required")
    if not clean_actor:
        raise ValueError("transition actor is required")

    # Serialize competing lifecycle commands so a stale source state cannot authorize
    # a transition after another transaction has already changed canonical truth.
    agent = session.exec(
        select(OrganizationAgent)
        .where(OrganizationAgent.id == agent_id)
        .with_for_update()
    ).one_or_none()
    if agent is None:
        raise NotFound("organization agent was not found")

    source_status = str(agent.status).strip()
    allowed_targets = ALLOWED_AGENT_LIFECYCLE_TRANSITIONS.get(source_status)
    if allowed_targets is None or clean_target not in allowed_targets:
        allowed = sorted(allowed_targets or ())
        raise InvalidTransition(
            f"organization agent transition {source_status!r} -> {clean_target!r} "
            f"is not allowed; allowed targets: {allowed}"
        )

    before_state = organization_agent_audit_state(agent)
    transitioned_at = now_utc()
    agent.status = clean_target
    agent.lifecycle_reason = clean_reason
    agent.updated_at = transitioned_at
    if clean_target == "active":
        agent.activated_at = transitioned_at
    elif clean_target == "suspended":
        agent.suspended_at = transitioned_at
    elif clean_target == "retired":
        agent.retired_at = transitioned_at

    session.add(agent)
    session.flush()
    record_audit(
        session,
        action=AGENT_LIFECYCLE_AUDIT_ACTION,
        entity_type="organization_agent",
        entity_id=agent.id,
        before_state=before_state,
        after_state=organization_agent_audit_state(agent),
        reason=clean_reason,
        actor=clean_actor,
        source=AGENT_LIFECYCLE_AUDIT_SOURCE,
        commit=False,
    )
    session.flush()
    return agent
