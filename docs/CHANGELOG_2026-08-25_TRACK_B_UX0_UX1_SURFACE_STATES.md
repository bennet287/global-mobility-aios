# Track B UX0/UX1 — Navigation and Truthful Surface States

**Date:** 2026-08-25  
**Status:** IMPLEMENTED ON FEATURE BRANCH / ACCEPTANCE PENDING  
**Branch:** `work/b-ux0-ux1-foundation-20260825`

## Delivered

- added a reusable `SurfaceState` primitive for bounded `empty`, `error`, `blocked`, and `not-connected` presentation semantics;
- added Track B styles that reuse the existing AIOS semantic palette rather than introducing a second visual identity;
- migrated material Live Organization error, empty-cycle, Domain Evidence-not-connected, and VerifiedRules-not-connected states to the shared primitive;
- kept announcement semantics explicit: dynamic errors can announce, while static empty/not-connected presentation does not create unnecessary live-region noise;
- simplified Owner/Cockpit navigation by removing the duplicate `Open from Cockpit` entry and the duplicate `Operations Workspace` cross-experience link;
- moved `Cross-department friction` into the primary Cockpit group, while dynamic department workspaces remain entered contextually from Cockpit rather than through a placeholder navigation item;
- extended the existing Track B design-foundation tests to cover surface-state semantics and the bounded UX0 navigation cleanup.

## Truth boundary

This slice does not create employee presence, heartbeat, online/offline employee status, event-stream activity, provider authority, Evidence, or VerifiedRules. Missing canonical state remains visibly missing/not connected.

Munder Difflin remains a controlled donor. Presence/heartbeat visualization is still deferred until AIOS exposes a canonical employee-presence read contract.

## Proof boundary

The previous exact-head local frontend proof belongs to `eb06d4721315f1c66de310c7afd2023d9560c250` and is historical after this commit. The new head requires fresh focused frontend/types/build/repository proof before PR #15 returns to ready-for-review state.

GitHub Actions runs observed for the previous head failed before executable job steps: all reported `steps: []` with `runner_id: 0`. Those runs are runner/infrastructure evidence, not proof that repository tests failed.

Milestone L remains `IMPLEMENTED / ACCEPTANCE PENDING`; Milestone M is not advanced by this Track B work.
