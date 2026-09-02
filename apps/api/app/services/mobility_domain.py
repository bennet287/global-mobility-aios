from __future__ import annotations

from app.models.domain import Lead


def mobility_intent_domain(lead: Lead) -> str:
    """Return the canonical first-slice mobility domain for a Lead intent.

    This contract consolidates the E.2/F.1 interpretation used by governed
    eligibility. It deliberately preserves the accepted mapping exactly; it does not
    reinterpret richer profile goals or broaden the pathway-domain taxonomy.
    """

    value = getattr(lead.intent, "value", lead.intent)
    normalized = str(value or "unknown").strip().casefold()
    if normalized in {"study_abroad", "study", "student"}:
        return "study"
    if normalized in {"overseas_job", "work", "job", "employment"}:
        return "work"
    if normalized in {"visa", "permanent", "residency", "immigration"}:
        return "visa"
    return "general"
