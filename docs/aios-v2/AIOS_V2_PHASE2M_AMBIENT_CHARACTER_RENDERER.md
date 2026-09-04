# AIOS V2 — Phase 2M — Ambient Character Renderer V1

**Status:** independently reviewed implementation candidate; repository CI pending.

- Contract identity: `aios-v2.ambient-character-renderer` (`1.0.0`)
- Base branch: `design/aios-v2-complete-redesign`
- Exact integration base: `1fb39d2e819acde99c9af531e76ee0e7efbdcce1`
- Presentation posture: read-only, presentation-only, no canonical writes

## Purpose

Phase 2K decides which safe ambient presentation actions a character may express.
Phase 2M renders only those already-approved actions through a small React/CSS
wrapper. It never resolves identity, reads organization state, claims physical
presence/location, or activates semantic work/conversation/handoff/completion.

## Architecture

`ambient-character-renderer.ts` is a pure adapter. It validates an incoming
Phase 2K descriptor, maps its mode and safe action vocabulary into a deeply
frozen renderer descriptor, preserves Phase 2K timing metadata, and applies a
parent-supplied deterministic phase slot.

`V2AmbientCharacterSurface.tsx` is a dumb wrapper around arbitrary child art.
It consumes only the prepared renderer descriptor, applies CSS-module classes
and timing variables, and renders the child unchanged.

## Fail-closed trust boundary

Motion is enabled only when the source descriptor matches the real Phase 2K
shape:

- `kind === "ambient-character-behavior"`
- source contract id/version exactly match Phase 2K
- `presentationBasis === "character-presentation-registry"`
- presentation key is non-empty
- mode is one of `standard`, `reduced-motion`, `static`
- `presentationOnly === true`
- all canonical/presence/location/travel/conversation/collaboration/work/
  completion/handoff/blocker-resolution claims are exactly `false`
- reduced-motion envelope is coherent

Any envelope failure produces a static renderer with no actions. Individual
unknown or malformed actions are ignored rather than repaired.

## Safe action vocabulary

The renderer recognizes only:

`blink`, `breathing`, `micro-posture`, `gaze-shift`, `focus-glow`,
`device-idle`, `prop-idle`, `selection-emphasis`.

Walking, travel, room-entry, coffee consumption, conversation, handoff, work,
completion and blocker-resolution actions are never renderer fallbacks.

## Motion composition

The wrapper uses separate shallow carriers so independent transform channels do
not overwrite each other:

- root: blink / focus glow / device glint / selection outline
- breath layer: bounded `translateY`
- posture layer: bounded rotation
- drift layer: bounded `translateX`

`prop-idle` deterministically takes precedence over `gaze-shift` if both exist.

The visual envelope is intentionally restrained:

- translate <= 1.2 px
- rotation <= 0.45 degrees
- no scale
- no path movement
- no timers, requestAnimationFrame, observers, canvas or WebGL

Phase 2K `durationMs` and `minIntervalMs` remain metadata in the renderer plan.
The React wrapper derives bounded CSS cycle variables using
`max(durationMs, minIntervalMs)` rather than silently replacing source timing.

## Deterministic crowd desynchronization

Parent-supplied `phaseSlot` values `0..3` map to `[0, 140, 280, 420]` ms.
CSS uses negative phase delays, so many visible employees do not start their
ambient loops on the same frame. No names, roles, timestamps, randomness or
canonical state determine the phase slot.

## Reduced motion

Reduced motion is enforced twice:

1. descriptor-driven `.modeReducedMotion` gating;
2. OS-level `prefers-reduced-motion: reduce`.

Both root-level animation classes and descendant transform carriers are covered.
Static focus/selection equivalents remain available without requiring motion.

## Independent review corrections over the ChatHub/Qwen draft

The external draft explicitly reported that it had no shell, git, Node, tsc or
filesystem access, so its output was treated as untrusted design input.

Repository review found and corrected:

1. the React component import path was one directory too shallow;
2. draft tests mutated a non-existent nested `truth` object, while Phase 2K
   truth flags are top-level;
3. the draft expected Operations to emit `selection-emphasis`, but the real
   Phase 2K Operations profile does not;
4. root-level blink/device animations were not actually disabled by the draft's
   descendant-only reduced-motion selectors;
5. the component source test banned semantic words that the component itself
   intentionally exposes in `data-*-claimed` truth markers;
6. source contract id/version were not validated before enabling motion;
7. malformed allowed actions were coerced instead of ignored;
8. Phase 2K `minIntervalMs` timing was discarded and durations were silently
   clamped;
9. static source mode could carry actions into renderer processing.

The reviewed implementation adds executable guards for all of the above plus a
control-byte integrity check for CSS.

## Independent preflight before upstreaming

A local isolated harness using the real Phase 2K descriptor shape and profile
sets executed the Phase 2M contract suite:

- 28 passed
- 0 failed
- 0 skipped

Strict TypeScript isolated compile for the adapter/component contract:

- PASS

These are preflight results only. Acceptance requires fresh exact-head
repository CI. Combined real-browser proof is deferred to the Living HQ
character-integration phase because Phase 2M intentionally adds no HQ-stage
wiring of its own.

## Files

- `apps/web/lib/v2/ambient-character-renderer.ts`
- `apps/web/components/v2/V2AmbientCharacterSurface.tsx`
- `apps/web/components/v2/V2AmbientCharacterSurface.module.css`
- `apps/web/scripts/aios-v2-ambient-character-renderer.test.mjs`
- `apps/web/package.json`
- `docs/aios-v2/AIOS_V2_PHASE2M_AMBIENT_CHARACTER_RENDERER.md`

## Non-goals

No canonical state mutation, no backend/API/database changes, no character art
replacement, no Three.js/GLB asset loading, no HQ stage integration, no
semantic walking/conversation/handoff/completion/Board/blocker animation.
