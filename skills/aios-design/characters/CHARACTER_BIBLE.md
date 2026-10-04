# AIOS V2 Character Bible

## Art direction

AIOS employees are **original stylized miniature adult professionals**.

They are not realistic humans, children, generic avatars, or direct copies of any franchise.

Core proportions:
- adult facial structure
- slightly enlarged expressive head
- compact torso
- slightly shortened limbs
- expressive hands
- readable footwear
- clean silhouette
- high-quality 3D materials

Exact head/body ratio remains open until prototype review.

## Character communication goals

Every persistent employee should communicate:

1. role
2. department
3. seniority
4. personality
5. supported current state

without depending entirely on labels.

## Identity source

Character design maps from real AIOS organizational role identity.

A frontend presentation registry may define:
- asset key
- silhouette archetype
- wardrobe
- accessories
- rig
- idle personality
- animation capabilities

but may never redefine canonical:
- role
- authority
- reporting line
- WorkItem
- presence
- semantic state

Registry identity is explicit:
- exact canonical positions may carry the guaranteed `canonicalPositionKey`
- role-family presentations must keep `canonicalPositionKey = null` and use a separate presentation-only key
- neutral/unknown fallbacks must keep `canonicalPositionKey = null`
- resolver precedence is exact position → supported family fallback → neutral fallback

See `presentation-registry-contract.md` for the binding, immutability, rig/LOD, animation-set and future asset-manifest rules.

## Required character record

Each character defines:
- canonical position key
- display name
- role/title
- department
- seniority
- personality
- silhouette
- head shape
- facial language
- hair
- eye/brow language
- wardrobe
- footwear
- accessories
- signature object
- default posture
- locomotion personality
- gaze behavior
- idle behavior
- work behavior
- review behavior
- waiting behavior
- blocker behavior
- conversation behavior
- authority behavior
- handoff behavior
- completion behavior
- reduced-motion equivalent
- accessibility description
- LOD class
- rig/skeleton class
- animation set

## Hero role direction

### CEO
- clean executive silhouette
- contemporary tailoring
- calm stance
- measured gestures
- slower deliberate locomotion
- strategy/briefing object
- high seniority without stereotypical extravagance

### CTO
- architectural technical jacket/overshirt
- compact technical device
- quicker analytical gestures
- system-surface interaction
- kinetic thinking posture

### CISO
- sharper geometric visual language
- controlled stance
- restrained movement
- alert gaze
- security-surface interaction
- disciplined dark material cues

### Regulatory Intelligence
- evidence/source motifs
- reading/comparison gestures
- research-table behavior
- deliberate precision

### Operations
- practical contemporary wardrobe
- higher movement frequency
- desk ↔ Mission ↔ colleague movement
- case/work objects
- collaborative stance

## Runtime presentation integrity

Presentation registry records are configuration and must be deeply immutable at runtime. Freezing only the top-level record is insufficient: registration metadata, behavior profiles, cue arrays, accessories, reduced-motion metadata and semantic-capability arrays must also be frozen.

Rig class, LOD class, material profile and animation-set keys are presentation bindings only. They must never become sources of canonical role, presence, authority or semantic state.

Every persistent archetype requires a substantive accessibility description, and all essential organization meaning remains available through structured UI without 3D or motion.

## Acceptance test

Hide labels.

A user should still broadly distinguish:
- executive
- technical
- security
- regulatory
- operations

## Ambient behavior

Presentation-only:
- breathe
- blink
- glance
- stretch
- local desk gestures
- tablet interaction
- coffee
- local walking
- lounge behavior

Ambient behavior must not create a work/conversation/presence claim.

## Semantic behavior

Requires supported event/state:
- handoff
- Mission collaboration
- governed conversation
- blocker response
- Owner escalation
- Board interaction
- completion

See `governance/semantic-animation-contract.md`.
