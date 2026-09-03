# AIOS V2 — Phase 2D Character × Mission Room Integration

**Status:** IMPLEMENTED / CI PROOF PENDING  
**Branch:** `design/aios-v2-character-mission-integration`  
**Stacked Mission Room head:** `46fc01c31c5e7ac0813360558bc5c4c5fbe510aa`  
**Accepted Character Registry head copied for integration:** `e77766fc63e17d5776b8a4bd5d55d25b20d1ea99`

## Purpose

Phase 2D connects the read-only Mission Room and Employee Inspector to the accepted Character Presentation Registry.

This is the first slice where a canonical Living Organization employee can select a deterministic character presentation that is actually rendered in the V2 Organization UI.

It deliberately does **not** add GLB assets, physical-presence claims, cross-room locomotion, semantic handoff animation, conversation animation, Board animation, or canonical mutation.

## Flow

```text
LivingSceneEmployee / Mission participant
        ↓
canonical position_key + title + department
        ↓
presentation-only family hint
        ↓
Character Presentation Registry
        ↓
exact position
   or role-family fallback
   or neutral fallback
        ↓
V2CharacterMiniature
        ↓
Mission Room + Employee Inspector
```

The flow is one-way. Presentation never writes back into organization state.

## Resolver precedence

The adapter calls the accepted registry resolver using:

1. canonical `positionKey`
2. presentation-only role-family hint
3. neutral fallback

The registry itself preserves exact-position precedence.

Initial visible outcomes include:

- `ceo` → exact CEO presentation
- `cto` → exact CTO presentation
- supported regulatory/compliance identities → regulatory/compliance family presentation
- supported operations identities → operations family presentation
- unsupported identities → neutral professional presentation

Role-family inference is explicitly presentation-only. It is not stored as canonical role, department, authority, or identity.

## Visible UI integration

### Mission Room

Each rostered Mission participant now includes a compact character miniature next to its canonical text identity.

Selection remains view-only.

The miniature is decorative inside the participant control; the accessible button text continues to expose department, title, authority, semantic state, and the no-presence posture.

### Employee Inspector

The selected canonical employee now receives a larger character presentation card.

The presentation card exposes:

- presentation key
- resolution kind
- silhouette
- locomotion personality
- rig class
- LOD class
- animation-set key

Those fields describe visual presentation compatibility only.

## Rendering posture

Every character renderer instance exposes:

```text
data-presentation-only="true"
data-presence-claimed="false"
data-canonical-state-writable="false"
data-semantic-animation-active="false"
```

The renderer may not activate semantic behavior.

## Ambient motion

This slice introduces one bounded ambient cue: a subtle miniature breathing motion.

Breathing is presentation-only and does not claim work, physical presence, conversation, collaboration, handoff, or authority.

A `prefers-reduced-motion: reduce` rule disables the animation entirely.

No semantic walk, handoff, conversation, blocker, Board, escalation, or completion animation is introduced here.

## Character differentiation

The placeholder miniature renderer already respects presentation metadata instead of rendering identical avatars.

The current CSS prototype differentiates silhouette/prop language for:

- tailored executive
- architectural technical
- evidence researcher
- practical operator
- neutral professional

These are integration placeholders for future versioned character assets. They are not the final art assets.

## Files

Added:

- `apps/web/lib/v2/character-mission-presentation.ts`
- `apps/web/components/v2/V2CharacterMiniature.tsx`
- `apps/web/scripts/aios-v2-character-mission-integration.test.mjs`

Updated:

- `apps/web/components/v2/V2MissionRoomPanel.tsx`
- `apps/web/components/v2/V2EmployeeInspector.tsx`
- `apps/web/styles/v2/foundation.css`
- `apps/web/package.json`

The integration branch also contains the accepted Character Registry source/test needed to build the stacked slice without altering PR #37.

## Tests

The new integration contract test verifies:

- canonical identity drives character selection
- deterministic presentation-family inference
- accepted exact/family/neutral registry boundary remains intact
- Mission Room renders the character miniature
- Employee Inspector renders the selected character
- no presence claim is added
- semantic animation remains inactive
- rig/LOD/animation-set metadata is presentation-only
- ambient breathing has a reduced-motion equivalent

`test:design-foundation` now retains both earlier Mission Room coverage and the accepted Character Registry test while adding the Phase 2D integration test.

## Next phase

Phase 2E should implement the first **governed semantic motion descriptor** for canonical `LivingSceneHandoff` events.

Phase 2E must remain pure/read-only first: prove the canonical-input → capability-gate → bounded visual-descriptor contract before wiring any transfer animation into the renderer.
