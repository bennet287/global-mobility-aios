// AIOS V2 Q2 — session-only destination recency for the command palette.
//
// This module keeps an in-memory list of recently followed workspace
// destinations. The state is module-scoped: it survives client-side App Router
// navigation and is cleared by a full page reload. It is never persisted to
// storage, never sent to the backend, and never derived from canonical state.
// Recency is a navigation convenience, not an organization fact.

const MAX_RECENT_DESTINATIONS = 5;

/**
 * Pure recency update: most-recent-first, deduplicated by href, capped.
 * Kept pure so the contract is testable without module state.
 */
export function updateRecentDestinations(
  current: readonly string[],
  href: string,
  limit: number = MAX_RECENT_DESTINATIONS,
): string[] {
  const normalized = href.trim();
  if (!normalized) return [...current];
  return [normalized, ...current.filter((entry) => entry !== normalized)].slice(0, limit);
}

let sessionRecentDestinations: string[] = [];

/** Record a followed workspace destination for this session. */
export function recordRecentDestination(href: string): void {
  sessionRecentDestinations = updateRecentDestinations(sessionRecentDestinations, href);
}

/** Read the session recency list (most recent first). */
export function getRecentDestinations(): readonly string[] {
  return sessionRecentDestinations;
}
