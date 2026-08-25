# Track B — Munder Presence Foundation

Date: 2026-08-25
Status: IMPLEMENTED / EXACT-HEAD PROOF PENDING
Programme: Track B UX2 / Munder Difflin controlled adoption
Donor slice: M6 presence + heartbeat
Adoption state: PARTIAL — execution-derived presence implemented; heartbeat remains NOT ESTABLISHED

## What changed

This bounded slice adapts the useful Munder Difflin presence mechanic without importing donor authority or donor state as AIOS truth.

- Added `organization-position-presence.v1`, an AIOS-owned read contract derived only from durable `OrganizationExecutionAttempt` records.
- Added a Board-safe Austria latest-presence endpoint at `/api/v1/organization/transparency/presence/austria/latest`.
- Added fail-closed consistency checks for impossible execution-presence states such as multiple running attempts or a running WorkItem without a running attempt.
- Added a first-party Cockpit surface at `/cockpit/live-organization/presence`.
- Added an Owner navigation entry for Employee Presence under Live Organization.
- Added motion-safe execution-presence styling. The animated executing indicator is rendered only when canonical presence state is `executing`; reduced-motion disables the animation.
- Added backend and frontend-focused tests.

## Truth boundary

`presence_state=executing` means only that AIOS currently has a durable running `OrganizationExecutionAttempt` for that position's WorkItem. It does not mean the employee is continuously online, the provider connection is healthy, or a heartbeat freshness lease exists.

The contract therefore reports:

- `heartbeat_state=not_established`;
- `heartbeat_observed_at=null`;
- `heartbeat_fresh_until=null`;
- `authority_effect=false`.

Projection time, browser refresh time, provider/model identity, animation, and UI visibility are never accepted as heartbeat evidence.

## Munder adoption boundary

This is an `ADAPT`, not a runtime/framework adoption. AIOS retains ownership of OrganizationPosition identity, WorkItem state, execution lineage, authority, autonomy, evidence, risk, and transparency semantics.

M6 is **not complete**. A real heartbeat substrate, freshness/lease semantics, durable heartbeat observation, and failure/recovery evidence remain future work. Until those exist, UI copy must not say an employee is online/offline based on this projection.

## Acceptance proof required

Before this slice can be treated as accepted, run exact-head backend tests for the new presence service, existing Austria Live Organization tests, frontend design-foundation/request-auth checks, TypeScript/build/compiled-auth, repository policy, release consistency, `git diff --check`, and a clean working tree. Do not convert local proof into CI/Woodpecker proof.
