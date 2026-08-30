from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class GovernedUiState:
    canonical_status: str
    authority_state: str
    human_approval_required: bool
    human_approved: bool
    canonical_revision: int = 0
    connected: bool = True
    pending_intent: str | None = None
    optimistic: bool = False


def reduce_ui_intent(state: GovernedUiState, intent: str) -> GovernedUiState:
    """UI intent is presentation/state only; it never changes canonical authority."""
    if intent == "SUBMIT_APPLICATION":
        return replace(state, pending_intent=intent, optimistic=True)
    if intent == "CANCEL_PENDING_INTENT":
        return replace(state, pending_intent=None, optimistic=False)
    if intent == "HUMAN_APPROVED_PRESENTATION_ONLY":
        return replace(state, human_approved=True, optimistic=False)
    if intent == "CONNECTION_LOST":
        return replace(state, connected=False)
    return state


def reconcile_with_canonical(
    state: GovernedUiState,
    *,
    canonical_status: str,
    authority_state: str,
    human_approval_required: bool,
    canonical_revision: int | None = None,
) -> GovernedUiState:
    """Canonical server truth overwrites optimistic state; stale snapshots are ignored."""
    incoming_revision = (
        state.canonical_revision + 1
        if canonical_revision is None
        else canonical_revision
    )
    if incoming_revision < state.canonical_revision:
        return state
    return GovernedUiState(
        canonical_status=canonical_status,
        authority_state=authority_state,
        human_approval_required=human_approval_required,
        human_approved=state.human_approved,
        canonical_revision=incoming_revision,
        connected=True,
        pending_intent=None,
        optimistic=False,
    )


def reconnect_with_snapshot(
    state: GovernedUiState,
    *,
    canonical_status: str,
    authority_state: str,
    human_approval_required: bool,
    canonical_revision: int,
) -> GovernedUiState:
    """Reconnect accepts only non-stale canonical truth and clears optimistic intent."""
    return reconcile_with_canonical(
        state,
        canonical_status=canonical_status,
        authority_state=authority_state,
        human_approval_required=human_approval_required,
        canonical_revision=canonical_revision,
    )
