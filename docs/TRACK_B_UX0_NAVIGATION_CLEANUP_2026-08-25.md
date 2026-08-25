# Track B — UX0 Navigation Cleanup

**Date:** 2026-08-25  
**Status:** IMPLEMENTED / ACCEPTANCE NOT CLAIMED  
**Branch:** `work/b-ux0-navigation-cleanup-20260825`  
**Parent Track B slice:** PR #15 / `work/b-ux0-ux1-foundation-20260825`

## Purpose

Continue UX0 with a bounded information-architecture cleanup proven by the repository rather than by speculative redesign.

## Finding

The Owner / Board navigation exposed `/cockpit` twice:

- `Cockpit Overview` in the primary Cockpit group;
- `Open from Cockpit` inside `Department workspaces`.

Both entries resolved to the same route and did not represent separate product capabilities or authorization boundaries.

## Change

The duplicate `Open from Cockpit` navigation item was removed. `Cockpit Overview` remains the single explicit `/cockpit` destination in the Owner / Board rail.

The `Department workspaces` group remains because `Cross-department friction` is a distinct owner-facing route and dynamic department workspaces continue to be opened contextually from the Cockpit rather than advertised as a duplicate Cockpit destination.

No route was deleted, redirected, or re-authorized. This is navigation information architecture only.

## Guardrail

A focused Track B test now asserts that the Owner / Board navigation does not repeat an `href` and that `/cockpit` appears exactly once. This prevents the same IA duplication from silently returning.

## Boundaries

- No Milestone M status change.
- No backend authorization change.
- No route removal.
- No fake state or Munder-derived runtime state introduced.
- PR #15 remains the parent UX0/UX1 foundation; this is a dependent bounded UX0 slice until that parent lands.

## Next

The next Track B product slice should address one of the remaining proven gaps:

1. reusable truthful page/surface states where loading, empty, unavailable, blocked, authority and not-connected semantics are repeated; or
2. the canonical employee-presence/heartbeat read contract required before Munder-derived Live Organization presence visualization can be implemented truthfully.
