# AIOS V2 Phase 2N — Living HQ Character Integration V1

## Scope

Phase 2N connects the already accepted Living HQ visual stage, character-presentation registry, character-art prototype, ambient behavior contract, ambient renderer, and HQ atmosphere presentation into the visible V2 Organization workspace.

This phase is presentation-only. It does not change canonical organization semantics, authority, persistence, backend APIs, database schemas, or sealed Phase 2I/2J/2K/2L/2M contracts.

## Starting point

Exact accepted base:

`b728e9d9475a6e1dbd175fe521f990d3ed268213`

Branch:

`design/aios-v2-living-hq-character-integration`

## Reused sealed contracts

- Phase 2I `hq-visual-presentation.ts`
- HQ roster adapter `hq-character-layout.ts`
- character presentation resolver `character-mission-presentation.ts`
- Phase 2J `character-art-prototype.ts`
- Phase 2K `character-ambient-behavior.ts`
- Phase 2L `hq-atmosphere-presentation.ts`
- Phase 2M `ambient-character-renderer.ts`

No sealed contract is widened or rewritten by this phase.

## Character data flow

```text
LivingSceneEmployee[]
  -> buildV2HqCharacterLayout()
  -> HqWingCharacterInput[]
  -> resolveV2CharacterPresentation()
  -> buildV2AmbientCharacterBehavior()
  -> buildV2AmbientCharacterRenderer()
  -> V2AmbientCharacterSurface
  -> V2CharacterArtPrototype
  -> V2LivingHqVisualStage
```

The Organization workspace explicitly adapts canonical roster records to the visual-stage DTO. Raw `LivingSceneEmployee` records are never passed directly into the HQ visual-stage contract.

### Placement

Placement continues to be governed by `buildV2HqCharacterLayout()` and therefore by the existing canonical department-to-presentation-zone mapping. The integration does not derive a wing from title, authority, semantic state, workload, or random/default heuristics.

Unmapped or ambiguous employees remain represented as unplaced presentation records with `presentationWing: null`.

## Wing metrics

`V2ArchitectureZone` records are explicitly adapted to the Phase 2I metric DTO:

- `departmentCount = zone.departments.length`
- `employeeCount = zone.employeeRosterCount`
- `workItemCount = zone.workItemCount`
- `activeBlockerCount = zone.activeBlockerCount`

The underlying organization overview interfaces remain unchanged.

## Character presentation

For every placed character, Phase 2N resolves the existing canonical identity fields through `resolveV2CharacterPresentation()`. The resolver remains responsible for choosing exact CEO/CTO registrations, supported role-family fallbacks, or the neutral presentation.

Phase 2N does not duplicate role-family or art-selection logic.

## Ambient behavior and renderer

Ambient behavior uses the accepted Phase 2K builder with fixed presentation density `normal`.

The phase deliberately does not derive ambient density from:

- work-item counts
- blockers
- authority
- semantic state
- presence
- workload

Phase-slot staggering is deterministic and derived only from stable visual ordering using `characterIndex % 4`.

No clock, random source, canonical timestamp, or semantic state controls phase staggering.

## HQ atmosphere

The Living HQ stage builds the accepted Phase 2L atmosphere descriptor with:

- theme: `presentation`
- emphasis: `balanced`
- selected zone: current view-only wing selection
- reduced-motion: operating-system reduced-motion preference

Atmosphere selection is presentation state only. It does not derive urgency, work activity, presence, blockers, or collaboration truth.

The atmosphere layer is mounted inside the existing decorative HQ floor layer, so it cannot intercept character/wing pointer interaction.

## Selection synchronization

The Organization workspace keeps one canonical presentation selection key:

`selectedPositionKey`

The same employee-selection path is used by the Living HQ and Mission Room. Selecting an employee updates the inspector selection and, when a governed HQ placement exists, focuses the corresponding presentation wing.

Wing selection itself remains view-only and cannot mutate AIOS.

## Reduced motion

Phase 2N introduces the small client-only `useReducedMotion()` hook based on `prefers-reduced-motion: reduce`.

The resulting boolean is supplied to both:

- `buildV2AmbientCharacterBehavior()`
- `buildV2HqAtmospherePresentation()`

Existing component CSS reduced-motion protections remain in force. No essential information is encoded only by motion.

## Truth invariants

The integrated surface preserves the existing presentation-only truth posture:

- canonical state writable: false
- physical presence claimed: false
- physical location claimed: false
- physical travel claimed: false
- conversation claimed: false
- collaboration claimed: false
- work activity claimed: false
- completion claimed: false
- handoff claimed by ambient behavior: false
- blocker resolution claimed: false

Phase 2N does not add walking, room traversal, fake conversation, coffee behavior, semantic work animation, completion animation, handoff animation, or autonomous locomotion.

## Accessibility and responsive posture

The existing structured Organization section remains available independently of the spatial renderer. Existing keyboard-operable wing and character controls remain intact, as do Mission Room and Employee Inspector selection flows.

The existing Living HQ responsive and `prefers-reduced-motion` CSS remains unchanged.

## Deliberate exclusions

Phase 2N does not implement:

- canonical handoff visualization
- canonical conversation visualization
- Mission collaboration animation
- physical employee location/presence
- backend or API writes
- shell/Owner Home redesign
- new 3D/WebGL rendering

Those belong to subsequent semantic or UI/UX phases.

## Automated test

`apps/web/scripts/aios-v2-living-hq-character-integration.test.mjs` verifies the integration seams, explicit DTO adapters, deterministic phase staggering, reduced-motion propagation, atmosphere selection basis, shared employee selection, structured accessible fallback, no direct mutation machinery, and preservation of the accepted Phase 2J/2K/2L/2M test wiring.

The test is registered in `test:design-foundation` without removing prior accepted design tests.

## Acceptance requirements

Before merge, Phase 2N requires:

1. TypeScript compilation PASS.
2. `test:design-foundation` PASS.
3. request-auth tests PASS.
4. production Next.js build PASS.
5. compiled-auth tests PASS.
6. exact-head repository-policy PASS.
7. exact-head backend-sqlite PASS.
8. exact-head frontend PASS.
9. exact-head postgres-governance PASS.
10. real-browser visual review of the integrated Living HQ, including selection and reduced-motion behavior.

Browser/visual acceptance is not claimed by this implementation commit itself.
