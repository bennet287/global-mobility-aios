from __future__ import annotations

from fastapi import HTTPException, Request

from app.core.config import settings


INTERNAL_SIMULATION_ROLES = frozenset({"admin", "operator", "reviewer"})


def can_include_draft_pathways(request: Request, *, requested: bool) -> bool:
    """Return True only when all four internal/draft simulation conditions hold.

    The gate is intentionally conservative: a missing flag, disabled setting,
    or insufficient role always fails closed. The result never weakens
    publication or external-validation checks.
    """
    if not requested:
        return False
    # The local development profile is the feature-enabled simulation environment.
    # Production remains fail-closed unless explicitly enabled at process start.
    if not settings.allow_internal_draft_pathway_simulation and settings.is_production():
        return False
    auth = getattr(request.state, "auth", None)
    if auth is None:
        return False
    role = getattr(auth, "role", None)
    if role not in INTERNAL_SIMULATION_ROLES:
        return False
    return True


def require_draft_simulation_allowed(
    request: Request,
    *,
    requested: bool,
    simulation_context: str | None = None,
) -> None:
    """Raise 403 when an explicit draft pathway simulation request is not permitted.

    No exception is raised when the caller did not ask for draft simulation;
    the gate must only block explicit attempts to widen discovery.
    """
    if not requested:
        return
    if not can_include_draft_pathways(request, requested=requested):
        raise HTTPException(
            status_code=403,
            detail="Internal draft pathway simulation is not permitted.",
        )
    if not simulation_context or len(simulation_context.strip()) < 8:
        raise HTTPException(
            status_code=400,
            detail="Internal draft simulation requires an explicit auditable context.",
        )
