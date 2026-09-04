# AIOS V2 — Phase 2G Governed HQ Character Roster

**Status:** IMPLEMENTED / CI PROOF PENDING  
**Branch:** `design/aios-v2-hq-character-roster` after clean reconstruction  
**Base:** `design/aios-v2-complete-redesign` at `6850fd5fbdac0a12f8b7008138c3f6fbb7eaafb4`

## Purpose

Phase 2G makes the Living Organization HQ visibly populated by canonical rostered employees without converting presentation layout into physical-location truth.

The phase connects the canonical scene roster to already-defined architectural presentation zones through a strict department mapping contract, then reuses the existing Character Presentation system and Employee Inspector selection state.

## Flow

```text
Canonical Living Organization scene
        ↓
deterministic employee roster
        ↓
canonical employee.department
        ↓
unique normalized department key/label match
        ↓
already-defined V2 architecture zone
        ↓
truth-preserving HQ character placement
        ↓
V2CharacterMiniature
        ↓
HQ wing preview + selectable roster
        ↓
existing Employee Inspector
```

No presentation step writes back into canonical organization state.

## Placement rule

An employee may receive an HQ presentation placement only when `employee.department` has exactly one normalized exact match against a mapped zone department key or label.

Normalization is limited to case and separator differences.

Examples:

```text
employee.department = "Executive Office"
department.label     = "Executive Office"
→ allowed

employee.department = "technology_platform"
department.key       = "technology_platform"
→ allowed
```

The layout does not use fuzzy semantic matching.

## Ambiguity rule

The rebuilt Phase 2G hardens the original implementation.

If the normalized canonical employee department matches more than one presentation-zone department mapping, AIOS does **not** select the first room.

Instead:

```text
reason = ambiguous-department-mapping
placement = none
physicalLocationClaimed = false
presenceClaimed = false
```

This prevents presentation ordering from silently becoming spatial truth.

## Forbidden placement inference

The renderer must never choose a wing because of:

- title
- role name
- authority
- seniority
- WorkItem
- semantic state
- blocker state
- character archetype
- random selection
- renderer convenience

A `Chief Executive Officer` with an unmapped or ambiguous canonical department remains spatially unplaced.

## Unplaced employees

If no unique canonical department-to-zone mapping exists, the layout produces a structured unplaced record with one of:

```text
unmapped-department
ambiguous-department-mapping
```

The HQ UI surfaces the number of spatially unplaced roster items rather than fabricating a complete office.

## Visible HQ integration

Each architecture wing can display compact presentation-only character miniatures for rostered employees whose canonical department maps uniquely to that wing.

The selected wing also exposes a structured roster with:

- Character Presentation miniature
- canonical title
- canonical department
- canonical semantic presentation state
- explicit `presence not claimed` copy

Selecting a roster item reuses the existing `selectedPositionKey`, so the same governed Employee Inspector model is used by Mission Room and HQ roster selection.

No duplicate employee truth model is introduced.

## Truth posture

The HQ blockout explicitly carries:

```text
data-physical-location-claimed="false"
data-presence-claimed="false"
```

Each placement carries:

```text
presentationOnly = true
physicalLocationClaimed = false
presenceClaimed = false
placementBasis = canonical-department-zone-mapping
```

A visual anchor is not a physical location claim.

## Styling isolation

The reconstruction moves Phase 2G-specific roster styling into:

```text
apps/web/components/v2/V2OrganizationBlockout.module.css
```

instead of appending more Phase 2G rules to the global `foundation.css`.

This reduces global style collision risk and keeps the governed roster work isolated from the separate premium Living HQ visual-stage work.

## Reduced motion

The existing Character Miniature reduced-motion contract remains in force.

The Phase 2G roster interaction also removes its hover/selection transition under `prefers-reduced-motion: reduce`.

No information depends on motion.

## Files

Added:

- `apps/web/lib/v2/hq-character-layout.ts`
- `apps/web/components/v2/V2OrganizationBlockout.module.css`
- `apps/web/scripts/aios-v2-hq-character-layout.test.mjs`
- `docs/aios-v2/AIOS_V2_PHASE2G_HQ_CHARACTER_ROSTER.md`

Updated:

- `apps/web/hooks/useV2MissionRoomInspector.ts`
- `apps/web/components/v2/V2OrganizationBlockout.tsx`
- `apps/web/components/v2/V2OrganizationWorkspace.tsx`
- `apps/web/package.json`

## Test coverage

The Phase 2G executable contract test covers:

1. exact normalized canonical department key/label mapping
2. no title-based room inference
3. ambiguous mapping is rejected rather than first-match selected
4. no physical-location claim
5. no presence claim
6. deterministic sorted output
7. runtime-frozen layout and records
8. wing filtering
9. no randomness, clocks, network or mutation machinery
10. scene hook exposes canonical roster read-only
11. HQ uses `V2CharacterMiniature`
12. HQ exposes no-location/no-presence attributes
13. HQ selection synchronizes with the existing Employee Inspector key
14. Phase 2G styles are CSS-module scoped
15. reduced-motion interaction behavior
16. no walking/conversation/semantic-animation activation

The test is wired into the real `test:design-foundation` command while preserving the accepted Character Registry, Phase 2D integration, Phase 2E semantic-motion and Phase 2F asset-manifest tests.

## Non-goals

Phase 2G does not add:

- canonical employee location
- physical presence
- room-entry events
- walking paths
- pathfinding
- conversation
- semantic handoff activation
- collision logic
- 3D navigation
- GLB loading
- renderer authority
- backend writes

## Relationship to neighboring phases

```text
Phase 2E — governed handoff descriptor
  determines whether a canonical handoff is semantically presentable

Phase 2F — character asset manifest
  determines which verified asset may render a presentation

Phase 2G — governed HQ character roster
  determines which presentation wing may visually anchor a rostered employee
  using a unique canonical department mapping only

Phase 2H — handoff choreography
  creates symbolic presentation stages for a supported handoff

Phase 2I — premium Living HQ visual stage (parallel external design lane)
  may consume Phase 2G governed placements later
```

A character can be visually anchored to a presentation wing without being physically present there. Semantic motion remains governed by its separate canonical event contracts.
