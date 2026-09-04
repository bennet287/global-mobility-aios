# AIOS V2 Phase 2I — Living HQ Visual Stage V1

## Status

Reviewed implementation candidate.

Base branch:

`design/aios-v2-complete-redesign`

Exact base SHA:

`6850fd5fbdac0a12f8b7008138c3f6fbb7eaafb4`

This phase was initially drafted by Qwen3.7 Plus from the exact repository sources. The model explicitly reported that it had no shell/runtime and therefore did not execute git, Node, TypeScript, or visual preview checks. The repository implementation below is a reviewed and hardened derivative, not a blind copy of that draft.

## Purpose

Phase 2I introduces a premium, presentation-only Living HQ visual stage.

It is intentionally separated from canonical organization truth. The component receives presentation assignments through props and does not fetch, mutate, infer or create organization state.

The stage provides:

- a dark architectural miniature/diorama composition;
- five governed presentation wings;
- a visually emphasized Mission Hub;
- decorative Decision Chamber and Collaboration Deck architecture;
- existing `V2CharacterMiniature` rendering;
- selected wing and selected character emphasis;
- explicit unplaced presentation handling;
- responsive laptop/tablet/mobile fallback;
- reduced-motion behavior.

## Truth posture

Permanent invariants:

```text
presentationOnly = true
physicalLocationClaimed = false
presenceClaimed = false
canonicalStateWritable = false
```

The visual stage never claims physical employee presence, physical room location, walking, travel, conversation, collaboration, handoff occurrence, work completion, blocker resolution, authority change, or canonical mutation.

Presentation assignment is an input to the stage. The stage does not infer wing placement from title, department, authority, seniority or semantic state.

## Reviewed corrections beyond the Qwen draft

Independent review found several issues in the raw draft:

1. The supplied verification script was not executed by Qwen. When independently executed, the raw script produced `23 passed / 4 failed`.
2. Character objects inside zone arrays were not runtime-frozen, so the output was not deeply immutable.
3. The component nested character `<button>` controls inside a wing `<button>`, producing invalid interactive HTML.
4. The Mission Hub badge displayed `totalWorkItemCount` as a mission count.
5. `selectedWing = null` still forced a visual hub selection.
6. Unknown/unplaced character presentations were silently dropped instead of remaining explicitly unplaced.
7. CSS Module variables were declared at `:root` rather than being scoped to the stage.

The reviewed implementation corrects all seven.

## Presentation adapter

`hq-visual-presentation.ts` is pure and deterministic. It defines stable presentation wing ordering, sanitizes numeric presentation metrics, clones and runtime-freezes every placed character presentation, preserves null/unknown presentation-wing assignments in an explicit frozen `unplacedCharacters` list, and creates deeply frozen zone and stage-layout descriptors.

No clock, random source, network call, DOM API or mutation API is used.

## Component structure

```text
stage
  ├─ header / presentation metrics
  ├─ architectural viewport
  │   ├─ decorative floor / Decision Chamber / Collaboration Deck
  │   └─ presentation wings
  │       ├─ optional native wing-selection button
  │       └─ sibling character controls/presentations
  ├─ explicit unplaced presentation tray
  └─ truth footer
```

Character controls are never nested inside wing buttons. If a callback is absent, the corresponding presentation is not rendered as a fake interactive control. Native `<button>` keyboard behavior is used rather than recreating Enter/Space handling manually.

## Visual direction

The stage uses restrained dark architectural materials, subtle perspective/grid grounding, five visually differentiated wing accents, layered platform surfaces, soft environmental light pools, compact existing Character Miniatures, a brighter central Mission Hub, and slow ambient illumination only. No WebGL/canvas/Three.js is introduced in this phase.

Decision Chamber and Collaboration Deck labels are decorative presentation architecture and are `aria-hidden` with the floor layer; they are not canonical organization zones.

## Responsive behavior

- Desktop: full architectural grid.
- Laptop: compressed diorama.
- Tablet: two-column architecture.
- Mobile: perspective removed and wings intentionally stacked vertically.
- Reduced motion: ambient loops and interaction transitions are disabled without hiding information.

## Independent local verification

Raw Qwen draft verification, executed independently:

```text
23 passed
4 failed
0 skipped
```

Reviewed implementation verification:

```text
node --experimental-strip-types --test \
  apps/web/scripts/aios-v2-hq-visual-stage.test.mjs

23 passed
0 failed
0 skipped
```

An isolated strict TypeScript harness using TypeScript 5.8.3 and the exact observed `V2CharacterMiniature` prop surface also completed with exit code `0`.

This is preflight evidence only. Full repository frontend/build/browser and Woodpecker proof remain required before merge.

## Files

```text
apps/web/components/v2/V2LivingHqVisualStage.tsx
apps/web/components/v2/V2LivingHqVisualStage.module.css
apps/web/lib/v2/hq-visual-presentation.ts
apps/web/scripts/aios-v2-hq-visual-stage.test.mjs
docs/aios-v2/AIOS_V2_PHASE2I_LIVING_HQ_VISUAL_STAGE.md
```

`apps/web/package.json` is intentionally not changed in this initial isolated Phase 2I branch because Phase 2G currently owns a parallel change to the same CI script. After Phase 2G merges, this branch must be synced and the Phase 2I test added to `test:design-foundation` before exact-head acceptance proof.

## Non-goals

This phase does not implement canonical HQ placement, backend reads/writes, 3D models, Three.js/React Three Fiber, GLB loading, walking, pathfinding, governed handoff animation, conversations, Board semantic animation, or completion animation.

Phase 2G remains the governed placement source. Phase 2H remains the governed handoff choreography source. Phase 2I is the premium visual presentation stage that will consume those reviewed contracts later.
