# AIOS V2 Character Presentation Registry Contract

## Purpose

This contract defines how canonical AIOS employee identity is resolved into a visual character presentation and later into versioned character assets, rigs, materials, LODs, and animation sets.

It is a **presentation contract only**.

> **The organization causes the animation. Animation never causes the organization.**

The character layer may describe how an employee looks and moves. It may never redefine what that employee is, what authority they hold, what work they own, whether they are present, or what canonical state they are in.

---

## Canonical boundary

The presentation layer must never own or synthesize canonical:

- role
- title
- authority
- reporting line
- department
- WorkItem
- semantic state
- physical presence
- decision outcome
- handoff occurrence
- conversation occurrence

Every registry record and every generated runtime presentation must preserve:

```text
presentationOnly         = true
presenceClaimed          = false
canonicalStateWritable   = false
```

---

## Identity key policy

Presentation identifiers and canonical organization identifiers are different namespaces.

### Exact-position registration

Use an exact canonical key only when that position key is guaranteed by canonical organization truth.

Initial examples:

```text
CEO  -> canonicalPositionKey = "ceo"
CTO  -> canonicalPositionKey = "cto"
```

### Role-family fallback

A role-family presentation is reusable visual metadata, not a canonical position.

Therefore:

```text
canonicalPositionKey  = null
presentationPositionKey = "role-family:<family>"
```

Examples:

```text
regulatory-compliance -> presentationPositionKey = "role-family:regulatory-compliance"
operations            -> presentationPositionKey = "role-family:operations"
```

Never place a `role-family:` identifier into `canonicalPositionKey`.

### Neutral fallback

Unknown or unsupported roles resolve to a neutral professional presentation:

```text
canonicalPositionKey = null
semantic capabilities = none
```

Echoing a requested unknown key for debugging or rendering convenience must never be represented as canonical truth.

---

## Resolver precedence

Character selection is deterministic.

```text
1. exact canonical position match
2. supported role-family fallback
3. neutral professional fallback
```

Exact position always wins over role-family fallback.

No resolver may use randomness, current time, renderer-local state, or generated guesses to choose canonical identity.

---

## Presentation vocabulary

A character presentation may define:

- silhouette
- head shape
- facial language
- hair language
- eye/brow language
- wardrobe
- footwear
- accessories
- signature object
- default posture
- gaze behavior
- locomotion personality
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
- rig class
- LOD class
- animation set key

The goal is not merely different clothing. Persistent roles should differ through **silhouette + prop language + posture + gaze + gesture rhythm + locomotion personality + behavior style**.

---

## Motion personality

Motion personality is presentation metadata, not a semantic state.

Examples:

- CEO: slower, deliberate, measured
- CTO: quicker, analytical, kinetic-thinking
- Regulatory / Compliance: precise, methodical, evidence-anchored
- Operations: brisk, practical, collaborative

Motion personality may influence timing, local gesture style, and pose selection. It must not invent work, urgency, authority, collaboration, or presence.

---

## Ambient versus semantic behavior

### Ambient presentation-only behavior

Allowed without a canonical semantic event when bounded and non-claiming:

- breathing
- blinking
- glancing
- stretching
- local desk gestures
- tablet interaction
- coffee
- bounded local walking
- lounge behavior

Ambient behavior must never create semantic data attributes or imply canonical:

- work
- conversation
- handoff
- Mission collaboration
- authority action
- physical presence

### Semantic behavior

Examples:

- handoff
- governed conversation
- blocker response
- Owner escalation
- Board interaction
- completion

A presentation record may only **declare that its rig/animation set can express a semantic capability**.

Capability declaration does not activate animation.

Activation requires canonical input and coverage according to `governance/semantic-animation-contract.md`.

---

## Rig, LOD, and animation-set bindings

Character assets must bind through versioned presentation identifiers rather than hard-coded renderer assumptions.

Recommended vocabulary:

```text
rig-hero-humanoid-v1
rig-standard-humanoid-v1

lod-hero
lod-standard
lod-background

aios-v2:animation-set:<versioned-key>
```

### Rig contract

Characters sharing a rig class should share a compatible skeleton/bone contract so animation clips can be reused safely.

Rig class is presentation metadata and cannot influence canonical identity.

### LOD contract

LOD affects rendering cost only.

Changing LOD must never:

- remove essential structured state
- change canonical meaning
- hide authority
- alter event interpretation
- change employee identity

### Animation-set contract

An animation set may include ambient clips and semantic-capability clips.

The set must never subscribe directly to backend events or mutate organization state. A governed presentation adapter selects clips only after canonical state has already been resolved.

---

## Asset manifest integration

Future GLB/material integration should use a versioned manifest rather than importing arbitrary files directly from components.

A manifest entry should eventually identify at minimum:

- presentation/archetype key
- asset version
- GLB/model URI
- rig class
- supported animation set
- material profile
- LOD variants
- optional signature prop assets
- accessibility label/description source
- fallback asset

The asset manifest remains presentation-only.

---

## Deep immutability

Registry metadata is configuration and must expose no mutation surface.

`Object.freeze()` is shallow. Therefore registered presentation records must freeze:

- top-level record
- registration object
- accessory array
- semantic-capability array
- reduced-motion object
- each behavior profile
- every behavior cue array

Read-only TypeScript types alone are insufficient runtime protection.

No exported API may register, mutate, patch, update, or write presentation records at runtime.

---

## Reduced motion

Every character archetype and every fallback must define a reduced-motion equivalent.

Default contract:

```text
mode = posture-and-state-change-only
forbidsLongTravelAnimation = true
```

Reduced motion preserves the same information and authority meaning without long travel, repeated motion, or motion-dependent interpretation.

---

## Accessibility

Character visuals reinforce meaning but never carry essential meaning alone.

Every persistent presentation should have a substantive accessibility description.

Canonical state, authority, blockers, decisions, handoffs, and work ownership must remain available through structured accessible UI.

Do not require:

- 3D
- motion
- color alone
- hover
- pointer-only interaction

to understand essential organization state.

---

## Future Living HQ integration order

Implement in this order:

```text
Canonical LivingSceneEmployee
        ↓
governed presentation adapter
        ↓
character registry resolver
        ↓
exact / family / neutral presentation
        ↓
versioned asset manifest
        ↓
rig + materials + LOD
        ↓
ambient motion controller
        ↓
canonical semantic-event adapter
        ↓
governed semantic animation
```

The renderer must never reverse this flow.

---

## Acceptance tests

Future registry/asset work must test at least:

1. exact position precedence
2. family fallback behavior
3. neutral fallback behavior
4. exact-only canonicalPositionKey policy
5. no invented canonical identity
6. deep immutability
7. no mutation exports
8. deterministic resolution
9. ambient/semantic separation
10. semantic capability declaration without activation
11. reduced-motion equivalence
12. accessibility metadata
13. rig/LOD/animation-set compatibility
14. structured fallback when assets are unavailable

---

## Non-goals

This contract does not:

- create backend state
- create physical-presence truth
- authorize decisions
- generate conversation content
- make animation canonical
- require 3D for product usability
- permit role-family aliases to masquerade as canonical position keys
