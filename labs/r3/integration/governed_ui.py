from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class GovernedUiState:
    canonical_status: str
    authority_state: str
    human_approval_required: bool
    human_approved: bool
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
    return state


def reconcile_with_canonical(
    state: GovernedUiState,
    *,
    canonical_status: str,
    authority_state: str,
    human_approval_required: bool,
) -> GovernedUiState:
    """Canonical server truth always overwrites optimistic presentation state."""
    return GovernedUiState(
        canonical_status=canonical_status,
        authority_state=authority_state,
        human_approval_required=human_approval_required,
        human_approved=state.human_approved,
        pending_intent=None,
        optimistic=False,
    )
