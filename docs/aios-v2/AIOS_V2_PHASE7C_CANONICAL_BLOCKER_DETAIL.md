# AIOS V2 — Phase 7C Canonical Blocker Detail Integration

Status: IMPLEMENTATION CANDIDATE — acceptance requires exact-head production proof and visual review.

## Purpose

Phase 7B made canonical employee work state visible in Living HQ but deliberately stopped at the generic `BLOCKED` state. Phase 7C adds the next bounded semantic layer: exact canonical blocker title/type/severity/status and relationship context where the Living Organization scene has explicit blocker coverage.

Phase 7C does not create blockers, infer blockers from animation, resolve blockers, or claim that a blocker physically affects a character.

## Canonical source

The only blocker-detail coverage adapter accepted by this slice is:

`organization_blocker_canonical_records`

Canonical records come from `LivingSceneBlocker` and may expose:

- blocker ID
- WorkItem ID
- blocker type
- title and description
- severity and status
- accountable position
- linked decision / risk escalation IDs
- human-action requirement
- opened / due timestamps
- elapsed / overdue state

Unknown, partial or unavailable blocker coverage fails closed. An unavailable source must never become an empty canonical blocker list or a numeric zero.

## Relationship rules

A blocker may be attached to a character presentation only when one of these deterministic relations exists:

1. `LivingSceneBlocker.accountable_position_key` uniquely matches a rostered employee; or
2. the blocker has no accountable position and its `work_item_id` uniquely matches exactly one rostered employee's `work_item_id`.

Explicit accountability has precedence. Ambiguous WorkItem-only relations fail closed.

The second case is a WorkItem relation only. AIOS must not upgrade it into an accountability claim.

## Spatial presentation

A canonical blocker marker may be shown only on a character whose sealed Phase 7B work-state kind is `blocked`.

- one attached blocker: show its exact severity marker;
- multiple attached blockers: show only the blocker count and direct the user to Employee Inspector;
- never cherry-pick the highest or most visually dramatic blocker as if it represented the whole set.

The blocker marker adds **no independent animation**. Phase 7B remains the sole work-state motion layer.

## Employee Inspector

Under established blocker coverage, Employee Inspector exposes every linked canonical blocker with:

- title
- severity
- type
- status
- description when present
- relationship basis (`Accountable position` or `Linked WorkItem`)
- human-action requirement
- overdue / due information when present

Under unavailable coverage, the inspector states that blocker details are unavailable and echoes the coverage state. It does not render zero blockers as canonical fact.

## Mission Room

Mission Room blocker counts and lists are coverage-aware in Phase 7C.

- established canonical blocker coverage + empty result → truthful zero/empty state;
- unsupported blocker coverage → explicit unavailable state;
- unsupported coverage must not display `No linked blockers` as if canonical absence were known.

## Truth posture

Phase 7C always preserves:

- `presentationOnly = true`
- `canonicalMutationAllowed = false`
- `causalBlockClaimed = false`
- `blockerResolutionClaimed = false`
- `physicalPresenceClaimed = false`
- `physicalLocationClaimed = false`

Blocker records describe governed work constraints. They do not establish physical presence, body movement, conversation, collaboration, handoff, escalation activity or resolution.

## Reduced motion and Structured Organization

Reduced-motion behavior remains static. Blocker detail is still available through Employee Inspector when Structured Organization is primary and the Living HQ renderer is not mounted.

No essential blocker meaning depends only on motion, color or the spatial renderer.

## Proof

Focused contract:

- `apps/web/scripts/aios-v2-visible-blocker.test.mjs`

Production Chromium:

- `apps/web/e2e/tests/aios-v2-blocker-detail.spec.ts`

Required visual-review artifact:

- `phase7c-blocker-detail-dark-1280.png`
- `phase7c-blocker-detail-reduced-structured-1280.png`

Acceptance follows the merged AIOS UI methodology:

1. production browser
2. generated screenshots
3. independent visual inspection
4. UX/accessibility/reduced-motion review
5. automated tests
6. exact-head Repository Policy + complete V12 Production Proof
7. merge only after all gates are green

## Deferred successor semantics

Phase 7C does not claim Phase 7 completion. Still separate:

- governed conversation rendering
- Mission collaboration semantics
- Owner / Board escalation semantics
- explicit blocker resolution and completion events
- replay-specific semantic rendering
