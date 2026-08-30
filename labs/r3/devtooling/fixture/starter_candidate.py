from __future__ import annotations

from typing import Any


def authorize_action(
    *,
    capability_available: bool,
    authority_granted: bool,
    human_approval_required: bool,
    human_approved: bool,
) -> str:
    """Return ALLOW or DENY. Implement the AIOS CAN DO != MAY DO boundary."""
    raise NotImplementedError


def resolve_truth(
    *,
    verified_rule: str,
    retrieved_memory: str | None,
    model_claim: str | None,
) -> str:
    """Return the governed truth value. Lower-truth context must not override it."""
    raise NotImplementedError


def replay_effect(
    *,
    command_id: str,
    seen: set[str],
    effects: list[str],
    effect: str,
) -> bool:
    """Apply one effect at most once. Return True only when newly applied."""
    raise NotImplementedError


def redact_values(text: str, secrets: list[str]) -> str:
    """Remove every exact secret value from output."""
    raise NotImplementedError


def accept_ui_state(
    *,
    canonical: dict[str, Any],
    ui_state: dict[str, Any],
) -> dict[str, Any]:
    """Merge presentation-only UI state without accepting canonical authority fields."""
    raise NotImplementedError
