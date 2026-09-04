# AIOS V2 — Phase 2H: Governed Handoff Choreography Planner

**Status:** IMPLEMENTED / FRESH REPOSITORY PROOF PENDING  
**Current integration base:** `design/aios-v2-complete-redesign` @ `0ec206b29aff0bda0ad2b5c2222f39b5b3c77f39`  
**Source authority:** hardened Phase 2E `V2HandoffMotionDescriptor`

> **The organization causes the animation. Animation never causes the organization.**

## Purpose

Phase 2E determines whether an already-recorded canonical handoff is eligible for semantic presentation. Phase 2H produces the bounded presentation-only choreography plan a future renderer may use after that descriptor passes every gate.

Phase 2H renders nothing, activates nothing and writes nothing. It is a pure, deterministic, deeply frozen, renderer-independent planner.

## Input authority and gates

The only accepted authority is `V2HandoffMotionDescriptor` from `apps/web/lib/v2/character-semantic-motion.ts`. Raw handoff objects are not alternate authority.

A choreography is supported only when the descriptor is the expected handoff kind, reports `supported === true`, carries complete canonical identity (`activityId`, `workItemId`, `fromPositionKey`, `toPositionKey`, `occurredAt`, `canonicalBasis`), establishes `truth.canonicalEvent === true`, matches both canonical endpoints, supports both presentation capabilities, and still reports `semanticAnimationActive === false`.

Any malformed, unsupported, forged, endpoint-mismatched or already-active descriptor fails closed with `mode = "unsupported"`, no stages and a deterministic limitation code.

## Standard choreography

A supported standard handoff uses fixed presentation timing only:

| # | Stage | Duration | Target | Intent |
|---:|---|---:|---|---|
| 1 | `sender-emphasis` | 180 ms | sender | emphasize |
| 2 | `transfer-emphasis` | 260 ms | relation | transfer-relation |
| 3 | `receiver-emphasis` | 180 ms | receiver | emphasize |
| 4 | `settle` | 160 ms | both | settle |

Total: **780 ms**, within the fixed **900 ms** budget.

`transfer-emphasis` is a symbolic relationship cue. It does not claim walking, pathfinding, room traversal, physical travel, physical object transfer or conversation.

## Reduced motion

With `reducedMotion: true`, the planner returns:

| # | Stage | Duration | Target | Intent |
|---:|---|---:|---|---|
| 1 | `static-relation` | 240 ms | relation | static-relation |
| 2 | `brief-target-emphasis` | 180 ms | both | emphasize |
| 3 | `settle` | 160 ms | both | settle |

Total: **580 ms**. Canonical identity remains structured and visible while spatial/transfer emphasis is removed.

## Timing and truth posture

All durations are bounded constants. Canonical timestamps never control presentation timing:

```text
timingCanonical = false
occurredAtControlsDuration = false
derivesFromCanonicalTimestamp = false
```

The choreography never claims physical presence, location/travel, room traversal, conversation/spoken words/transcript, physical object transfer, work completion, dependency resolution, authority change, approval/rejection or canonical mutation. `semanticAnimationActive` and `canonicalStateWritable` remain false in every result.

## Immutability and determinism

Every result and nested value is recursively frozen. The planner contains no randomness, clock reads, timers, animation scheduler, DOM/browser APIs, React, Three.js, network access or mutation API. Identical input yields deeply equal output.

## Independent hardening retained in this reconstruction

The earlier reviewed implementation closed a forged-descriptor gap where a caller could claim handoff support while omitting canonical identity. The current regression suite preserves that adversarial case along with endpoint swap rejection, already-active descriptor rejection, reduced-motion behavior, deep freezing, fixed timing, capability gating and truth invariants.

Phase 2H has now been reconstructed as a clean descendant of the current Phase 2K redesign base. The existing test is wired into the real `test:design-foundation` strip-types group. Fresh exact-head Woodpecker proof is still required before merge.

## Files

- `apps/web/lib/v2/character-handoff-choreography.ts`
- `apps/web/scripts/aios-v2-character-handoff-choreography.test.mjs`
- `docs/aios-v2/AIOS_V2_PHASE2H_GOVERNED_HANDOFF_CHOREOGRAPHY.md`
- `apps/web/package.json` (test wiring only)

## Non-goals

Phase 2H does not implement visible React animation, CSS, assets, walking/pathfinding, room movement, conversation, Board interaction, blocker/completion effects, backend/API/database changes or canonical writes.

## Future renderer integration

A later renderer may consume the plan only after this contract is accepted. It must honor `mode`, `supported`, `stages`, `timing`, `truth`, `reducedMotion` and limitation codes; keep event time separate from presentation time; and retain canonical handoff information when choreography is unsupported rather than inventing animation.
