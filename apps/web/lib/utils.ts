export type Tone = "good" | "warn" | "bad" | "neutral";

export function titleCase(value: string | undefined | null): string {
  if (!value) return "—";
  return value.replaceAll("_", " ").replace(/\b\w/g, (match) => match.toUpperCase());
}

export function compactNumber(value: number | undefined | null): string {
  return new Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 1 }).format(value || 0);
}

export function statusTone(value: string | undefined | null): Tone {
  const normalized = (value || "").toLowerCase();
  if (
    [
      "verified",
      "approved",
      "converted",
      "completed",
      "ready",
      "ready_for_human_approval",
      "truth_clear",
      "qualified",
      "ok",
      "online",
      "active",
      "published",
      "baseline",
      "unchanged",
      "not_modified",
      "low_risk",
      "coverage_ready",
      "eligible",
      "likely_eligible",
    ].includes(normalized)
  ) {
    return "good";
  }
  if (
    [
      "pending",
      "needs_review",
      "human_review",
      "human_review_required",
      "documents_incomplete",
      "draft",
      "submitted",
      "decision_pending",
      "new",
      "partial",
      "pending_review",
      "changed",
      "medium_risk",
      "ready_for_review",
      "needs_profile_review",
      "needs_documents",
      "coverage_gap",
      "warning",
      "simulation_candidate",
      "internal_simulation_only",
      "unpublished",
      "disabled",
      "loading",
      "insufficient_information",
      "insufficient_profile",
      "ambiguous",
      "unresolved",
    ].includes(normalized)
  ) {
    return "warn";
  }
  if (
    ["rejected", "blocked_truth_rejected", "rejected_by_authority", "withdrawn", "failed", "error", "closed", "offline", "high_risk", "restricted", "blocking", "ineligible"].includes(
      normalized
    )
  ) {
    return "bad";
  }
  return "neutral";
}
