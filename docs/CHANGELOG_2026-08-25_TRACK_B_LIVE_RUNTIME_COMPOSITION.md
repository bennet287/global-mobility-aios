# Track B — Live Organization Runtime Composition

Date: 2026-08-25
Status: IMPLEMENTATION COMPLETE / EXACT-HEAD PROOF PENDING
Programme: Track B UX2 / Munder Difflin controlled adoption
Parent: PR #17 employee-presence foundation
Adoption slices: M6 presence + M7 scene/event sync concepts, selectively ADAPT

## What changed

This slice moves the AIOS-owned presence foundation into the primary Live Organization experience without turning the Cockpit into a simulated office scene.

- The main `/cockpit/live-organization` surface now reads the canonical Austria Live Organization projection and the Board-safe presence projection independently with `Promise.allSettled`.
- Presence failure degrades the workspace to a truthful partial state rather than hiding the canonical Live Organization cycle.
- Presence is composed only when its `root_work_item_id` matches the currently rendered Live Organization root WorkItem. Cross-cycle latest-read races are shown as blocked/out-of-sync instead of being merged.
- A compact employee-execution-presence panel exposes executing count, projected positions, observation timestamps, heartbeat capability state, and a link to the detailed presence surface.
- A durable OrganizationActivity panel renders only persisted activity records from the Live Organization snapshot. It does not synthesize chat bubbles, tool-call activity, random motion, or decorative busywork when no activity exists.
- Existing authority, evidence, owner-readiness, blocker, and provenance surfaces remain unchanged in authority semantics.

## Munder boundary

The useful donor ideas are presence and scene/event synchronization. AIOS adapts those ideas as projections over first-party durable records rather than importing the donor runtime or state model.

The runtime composition therefore preserves these boundaries:

- `OrganizationExecutionAttempt` is the only source for execution presence in this slice;
- `OrganizationActivity` is the only source for the new activity stream;
- the two latest projections must identify the same root WorkItem before their data is composed;
- provider/model activity is provenance, not employee presence;
- heartbeat remains `not_established`;
- UI refresh time and animation are not evidence;
- no authority, autonomy, evidence truth, or external-action permission is added by the presentation layer.

## Acceptance proof required

Run the focused backend presence/Live Organization tests plus frontend design-foundation/request-auth checks, TypeScript, production build, compiled-auth verification, repository policy, release consistency, `git diff --check`, and a clean working tree on the exact branch head. Browser E2E remains a separate frontend acceptance gate and must not be inferred from unit/build proof.
