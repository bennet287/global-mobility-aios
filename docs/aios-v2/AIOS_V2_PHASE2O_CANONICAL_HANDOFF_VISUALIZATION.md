# AIOS V2 — Phase 2O Canonical Handoff Visualization V1

## Status

Reconstructed after the accepted Phase 2N merge and based directly on:

`6c4529d0e51e0472a60cd6760aec8a7f731d8550`

Phase 2O is a bounded presentation-contract slice. It does not modify canonical organization state and it does not yet wire semantic handoff motion into the visible Living HQ renderer.

## Purpose

Phase 2O defines the renderer-ready visual grammar for a **canonical handoff**.

It consumes the sealed Phase 2E `V2HandoffMotionDescriptor`, which is authorized only by a canonical `LivingSceneHandoff`, and translates that descriptor into a presentation-only sequence suitable for a later visible integration slice.

The governing law remains:

> The organization causes the animation. Animation never causes the organization.

## Canonical authority chain

`LivingSceneHandoff` → Phase 2E `buildV2HandoffMotionDescriptor` → Phase 2O `buildV2HandoffVisualization`

Phase 2O never infers a handoff from room placement, employee state, title, department, proximity, animation, or UI selection. Unsupported or truth-invalid Phase 2E descriptors fail closed.

## Full-motion visual grammar

When the source descriptor is supported, the presentation sequence is:

1. sender emphasis
2. work-object activation
3. bounded transfer relation/path
4. receiver emphasis
5. settle

The transfer path represents a canonical relationship between sender, work object and receiver. It is **not** a physical route and does not mean that an employee walked, travelled, entered a room or physically transferred an object.

Timing uses presentation tokens only:

- `micro`
- `standard`
- `spatial-focus`

Canonical `occurred_at` is preserved as event time and never becomes an animation duration.

## Reduced motion

Reduced motion removes the bounded transfer-path sequence and preserves the semantic information using:

1. brief sender emphasis
2. static sender → receiver relation
3. brief receiver emphasis

No long-travel animation is permitted.

## Replay policy

Replay visualization is fail-closed. It requires both:

- supported replay coverage; and
- replay cursor activity ID equal to the canonical handoff activity ID.

Unsupported coverage or a different replay cursor produces an unsupported descriptor with no semantic visualization steps. Historical handoffs are never inferred from surrounding events.

## Permanent truth boundaries

Phase 2O never claims:

- canonical writes
- physical presence
- physical location
- physical travel
- physical transfer duration
- room traversal
- conversation
- transcript or spoken words
- collaboration
- work completion
- dependency resolution
- authority change
- approval or rejection

`semanticAnimationActive` remains `false`. This contract describes renderer permission and presentation grammar; it does not start animation itself.

## Files

- `apps/web/lib/v2/handoff-visualization.ts`
- `apps/web/scripts/aios-v2-handoff-visualization.test.mjs`
- `apps/web/package.json`
- `docs/aios-v2/AIOS_V2_PHASE2O_CANONICAL_HANDOFF_VISUALIZATION.md`

## Relationship to Phase 2N

Phase 2N is sealed and provides the accepted Living HQ, character-art, atmosphere, ambient-renderer, wing-navigation and Employee Inspector integration surface.

Phase 2O deliberately does not alter those accepted components. It establishes the semantic handoff visualization descriptor first so a later integration slice can connect only supported canonical handoffs to the Living HQ without reopening the Phase 2N truth boundary.

## Acceptance requirements

Before Phase 2O can merge:

1. branch must be exactly one commit ahead / zero behind the accepted Phase 2N merge;
2. `aios-v2-handoff-visualization.test.mjs` must remain registered in `test:design-foundation`;
3. focused design-foundation, request-auth, build and compiled-auth validation must pass;
4. Woodpecker exact-head lanes must pass:
   - repository-policy
   - backend-sqlite
   - frontend
   - postgres-governance
5. no backend/API/database mutation contract may be introduced;
6. no visible semantic animation may be claimed until a later integration slice explicitly wires the descriptor into the renderer and receives its own browser acceptance.
