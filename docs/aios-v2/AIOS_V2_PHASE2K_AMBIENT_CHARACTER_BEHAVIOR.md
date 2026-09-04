# AIOS V2 — Phase 2K — Ambient Character Behavior Contract V1

Status: **REVIEWED IMPLEMENTATION / ACCEPTANCE PENDING**

- Contract: `aios-v2.character-ambient-behavior` v1.0.0
- Integration base: `adae689f879d9864d1cc0aa2fe332f58bd8abe17`
- Base branch: `design/aios-v2-complete-redesign`
- Scope: presentation-only ambient character behavior planning

## Purpose

Phase 2K defines a pure deterministic descriptor for safe ambient character aliveness: blink, breathing, micro-posture, gaze shift, focus glow, device idle, stationary prop idle, and a reserved selection-emphasis vocabulary.

The planner does not render, schedule, fetch, write, or mutate canonical state.

Core rule:

> The organization may inform presentation. Presentation never creates organization truth.

## Input authority

The planner consumes `V2CharacterPresentationResolution`, but does not trust a top-level `presentationKey` by itself. Runtime JavaScript can forge an object that satisfies a TypeScript-looking shape, so the planner verifies that:

- the resolution posture remains presentation-only/non-writable;
- `resolutionKind` matches the nested registry registration kind;
- exact-position registration key equals the resolution presentation key;
- role-family presentation key equals the registered presentation-position key;
- supported Regulatory/Operations families agree with the nested role family;
- neutral fallback is exactly `neutral-professional`;
- the nested presentation record also preserves presentation-only/no-presence/no-write posture.

Inconsistent or malformed input produces a frozen `static` descriptor with no ambient actions and limitation `presentation-resolution-missing-or-inconsistent`.

## Presentation profiles

| Profile | Normal-density actions |
| --- | --- |
| CEO | blink, breathing, gaze-shift, device-idle |
| CTO | blink, breathing, device-idle, focus-glow, micro-posture |
| Regulatory / Compliance | blink, breathing, device-idle, gaze-shift, focus-glow |
| Operations | blink, breathing, micro-posture, device-idle |
| Neutral | blink, breathing |

`selection-emphasis` remains in the closed safe vocabulary for future explicit selection-driven rendering, but Phase 2K does **not** schedule it because the planner has no selection input. This prevents ambient motion from fabricating selection.

## Density

`low`, `normal`, and `high` are presentation density only.

- low: tier-1 subset with reduced presentation weight;
- normal: tier-1 and tier-2 default;
- high: available tiers with increased presentation weight.

Density can change the presentation action subset and cadence weight, but it never changes truth posture. The timing descriptor therefore states:

- `densityAffectsPresentationOnly = true`
- `densityMayChangeActionSubset = true`
- `densityNeverChangesTruth = true`

## Reduced motion

Reduced motion is first-class. Transform-class actions (`breathing`, `micro-posture`, `gaze-shift`) are removed. Remaining opacity-class actions preserve the same presentation identity. No semantic information is lost because ambient behavior never carries canonical semantics.

## Timing

All timing values are bounded constants. No duration or interval is derived from canonical timestamps, event age, work-item age, system time, or employee state.

The production module contains no `Math.random`, clock access, timers, network calls, React/DOM/WebGL/Three.js dependency, or mutable external state.

## Truth boundaries

Every descriptor preserves:

- `presentationOnly = true`
- `semanticAnimationActive = false`
- `canonicalStateWritable = false`
- `physicalPresenceClaimed = false`
- `physicalLocationClaimed = false`
- `physicalTravelClaimed = false`
- `conversationClaimed = false`
- `collaborationClaimed = false`
- `workActivityClaimed = false`
- `completionClaimed = false`
- `handoffClaimed = false`
- `blockerResolutionClaimed = false`

The registry is recorded as `presentationBasis`, not `canonicalBasis`, because the Character Presentation Registry is presentation authority only.

## Independent review of the GLM draft

The GLM-5.3-Flash submission was useful as a draft and correctly withheld test claims because its environment had no shell, git, Node, TypeScript, or filesystem.

Independent execution of the raw planner/test design in an isolated Node 22.16 / TypeScript 5.8.3 harness produced **25 passed / 0 failed / 0 skipped**.

Adversarial probes then found gaps not covered by the draft tests:

1. a forged `presentationKey: "ceo"` could unlock CEO ambient behavior without a coherent registry registration;
2. mismatched registration and presentation key could produce contradictory output identity;
3. Operations scheduled `selection-emphasis` even though no selection input existed;
4. the registry was mislabeled as a canonical basis;
5. density metadata claimed cadence-only effects while low density also changes the action subset.

The reviewed implementation hardens all five issues.

Reviewed isolated verification:

```text
Node 22.16.0
Phase 2K executable tests: 25 passed / 0 failed / 0 skipped
TypeScript 5.8.3 strict noEmit harness: PASS
```

This is preflight evidence only. Repository acceptance requires the real Woodpecker exact-head proof after the Phase 2K test is wired into `test:design-foundation`.

## Non-goals

Phase 2K does not implement:

- visible React animation;
- CSS motion;
- walking/pathfinding/room traversal;
- conversation or spoken content;
- coffee consumption;
- handoff/blocker/completion/Board animation;
- backend/API/database changes;
- canonical state writes.

## Future renderer integration

A later renderer may interpret the frozen descriptor read-only. It must use the closed action vocabulary, honor reduced-motion mode, and never convert ambient presentation into organization truth. Explicit selection, handoff, conversation, blocker, completion, or Board interactions require their own governed inputs.
