# AIOS V2 — Phase 2C Character Presentation Registry

**Status:** IMPLEMENTED / PROOF PENDING
**Branch:** `design/aios-v2-character-registry-fable`
**Original Phase 2B parent:** `1c2cd5de378ba293b4d643ec1185349440fc8790`
**Phase 2B merge:** `1f8a5e1a6f798931c152b45a4f145ba592022801`

## Purpose

The Character Presentation Registry defines **how canonical AIOS employees are visually presented** without redefining what those employees are.

It is frontend-only, read-only and presentation-only.

The registry may define silhouette, head/facial language, wardrobe, footwear, accessories, signature objects, posture, gaze, motion personality, ambient presentation behavior, supported semantic animation capabilities, reduced-motion equivalents, accessibility descriptions, rig class and LOD class.

It may never redefine canonical role, authority, reporting line, WorkItem, presence, semantic state or department.

## Relationship to Living Organization

`LivingSceneEmployee` remains the source-backed organization projection for identity and state.

| Concern | Canonical owner | Character registry |
| --- | --- | --- |
| Position / title | Living Organization | Lookup only |
| Authority | Canonical organization state | Never redefined |
| Reporting line | Canonical organization state | Never stored |
| WorkItem | Canonical organization state | Never stored |
| Presence | Canonical coverage/state | Never claimed |
| Semantic state | Canonical scene projection | Never stored as current truth |
| Department | Canonical organization state | Never redefined |
| Silhouette / wardrobe | Presentation layer | Defined here |
| Ambient style | Presentation layer | Defined here |
| Semantic capability | Presentation layer | Declared only; never activated here |

Every presentation record carries:

```text
presentationOnly        = true
presenceClaimed         = false
canonicalStateWritable  = false
```

## Registration model

### Exact position

Initial exact registrations:

- `ceo`
- `cto`

Their top-level `canonicalPositionKey` matches the exact registration.

### Role-family fallback

Initial reusable visual families:

- `regulatory-compliance`
- `operations`

Their `canonicalPositionKey` is explicitly `null`.

The canonical organization already contains concrete positions in these domains, including `public_policy_compliance_lead` and `operations_coordination`. This initial registry deliberately keeps the visual archetypes family-based so presentation does not duplicate additional organization truth. Exact bindings can be added later through the governed presentation adapter.

### Neutral fallback

Unknown positions and unregistered families receive a neutral professional presentation with no canonical position, authority, department, semantic-state or presence claim.

## Initial archetypes

| Archetype | Registration | Direction |
| --- | --- | --- |
| CEO | exact `ceo` | Contemporary tailoring, calm silhouette, measured gestures, slower deliberate movement, strategy folio |
| CTO | exact `cto` | Architectural technical overshirt, analytical silhouette, compact device, quicker analytical gestures |
| Regulatory / Compliance | role-family fallback | Evidence/source motifs, comparison gestures, deliberate precision, research-table behavior |
| Operations | role-family fallback | Practical contemporary wardrobe, collaborative stance, case/work object, higher local movement frequency |

## Ambient versus semantic behavior

Ambient presentation may include breathe, blink, glance, stretch, local desk gestures, tablet interaction, coffee and bounded local walking.

Ambient behavior must not claim canonical work, physical presence, conversation, handoff, Mission collaboration or authority action.

Semantic behaviors such as handoff, governed conversation, blocker response, Owner escalation, Board interaction and completion are represented only as **supported capabilities**. The registry does not activate them.

> The organization causes the animation. Animation never causes the organization.

## Immutability

Registered presentation records are deeply frozen across registration metadata, behavior profiles, cue arrays, accessories, semantic-capability arrays, reduced-motion metadata and the top-level record.

The registry exports only read-only resolver functions and no canonical mutation API.

## Reduced motion

Every archetype and neutral fallback defines:

```text
mode = posture-and-state-change-only
forbidsLongTravelAnimation = true
```

## Accessibility

Every presentation record provides a substantive accessibility description. Visual identity can reinforce role recognition, but canonical state and authority remain available through structured accessible UI rather than relying on character animation alone.

## Future integration

Future phases may bind:

- `animationSetKey` to versioned animation clips
- `rigClass` to a supported shared skeleton
- `lodClass` to renderer LOD policy
- archetypes to versioned GLB/material manifests

Those bindings remain presentation-only. Semantic activation still requires canonical input elsewhere.

## Non-goals

This slice does not add backend state, migrations, API mutation, live presence, 3D assets, rig authoring, semantic handoff activation, conversation activation, Board decision animation or production renderer integration.

## Verification

The external draft was independently reviewed before repository integration. The review found and corrected a false deep-freeze test claim and a TypeScript narrowing issue.

Current independent local verification:

```text
node --experimental-strip-types --test apps/web/scripts/aios-v2-character-registry.test.mjs
24 passed
0 failed
0 skipped
```

The corrected registry also passes strict standalone TypeScript compilation.

Final repository proof still requires the normal Woodpecker exact-head lanes.
