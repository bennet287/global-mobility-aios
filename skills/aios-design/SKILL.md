# AIOS Design Skill

## Purpose

This skill governs all AIOS V2 frontend/product design and implementation.

AIOS V2 is not a cosmetic reskin. It is a whole-product redesign spanning:

- UX
- UI
- characters
- office/world architecture
- motion
- spatial interaction
- governance/truth presentation
- accessibility
- responsive behavior
- performance
- design QA

The product thesis is:

> **AIOS = Executive Intelligence × Living Organization × Spatial Computing × Architectural Character World**

The target experience is:

> **a premium operating system for a living digital company whose employees, missions, evidence, decisions, history, authority, and organizational state are visible, understandable, truthful, and alive.**

---

## Mandatory design order

Never begin from aesthetics alone.

For every new or redesigned surface, determine in this order:

1. user and role
2. user goal
3. canonical data/state
4. authority/mutation posture
5. information hierarchy
6. applicable UX laws
7. interaction model
8. structured accessibility equivalent
9. responsive behavior
10. spatial implications
11. motion implications
12. performance implications
13. UI composition/materials
14. implementation
15. acceptance tests

A design that looks premium but obscures truth is rejected.

---

## Six first-class systems

Every AIOS V2 design decision belongs to one or more of:

1. **UX System**
2. **UI System**
3. **Character System**
4. **Office / World Architecture System**
5. **Motion + Spatial Interaction System**
6. **Governance + Product Truth System**

Cross-cutting:
- accessibility
- responsive
- performance
- visual regression
- usability
- CI proof

Characters and architecture are not decorations. They are interaction systems of the Living Organization.

---

## Core laws

### Truth law
> Visual clarity must never reduce truth clarity.

### Motion law
> The organization causes the animation. Animation never causes the organization.

### Spatial law
> Every essential spatial fact must have a structured accessible equivalent.

### Complexity law
> Complexity is progressively disclosed, never deceptively hidden.

### Product law
> The Owner sees what matters before seeing how it is stored.

---

## Required references

Before implementation, read the relevant files in:

- `constitution/`
- `ux/`
- `ui/`
- `characters/`
- `architecture/`
- `spatial/`
- `motion/`
- `governance/`
- `quality/`

For Living Organization work, the minimum required set is:

- `characters/CHARACTER_BIBLE.md`
- `characters/presentation-registry-contract.md`
- `architecture/OFFICE_BIBLE.md`
- `spatial/spatial-interaction.md`
- `motion/motion-language.md`
- `governance/semantic-animation-contract.md`
- `constitution/truth-preserving-design.md`

---

## V2 information-depth model

Use:

- **L0 Ambient** — what is generally happening?
- **L1 Attention** — what needs action?
- **L2 Context** — who/what/where/why?
- **L3 Evidence** — what supports this?
- **L4 Provenance / internals** — exact records/contracts/versions/fingerprints/timestamps/providers.

Primary surfaces should not default to L4.

---

## V2 navigation model

### Owner
- Home
- Organization
- Missions
- Intelligence
- Evidence
- Decisions
- History

### Professional / Operator
- Work
- Profiles
- Pathways
- Evidence
- Communication
- Tools

### Mobility user
- Overview
- My Case
- Documents
- Timeline
- Messages

Existing routes may remain for compatibility, but primary navigation follows user mental models rather than module inventory.

---

## Domain-native UI objects

Prefer product objects over generic card vocabulary:

- Mission Surface
- Work Object
- Employee Identity
- Evidence Object
- Source Object
- Decision Object
- Authority Gate
- Friction Signal
- Handoff Signal
- Temporal Lens
- Environmental Pattern Surface
- Provenance Drawer
- Owner Attention Object

Generic surfaces may exist internally, but should not define the product language.

---

## Renderer/governance invariants

Living Organization presentation must preserve:

- renderer non-authority
- no canonical mutation from renderer
- explicit unsupported states
- structured fallback
- replay coverage limits
- memory/prediction distinction
- presence-claim boundaries

Never convert presentation convenience into domain truth.

---

## Character rules

Characters are original stylized miniature adult professionals.

They must communicate:

- role
- department
- seniority
- personality
- state

through silhouette, posture, wardrobe, props, and motion—not only labels.

Reject:
- childish/baby workforce
- generic avatars
- identical models with shirt colors
- photoreal uncanny-valley humans
- direct franchise imitation

---

## Office/world rules

The pixel/stacked tower metaphor is retired.

The target is a premium miniature architectural HQ/campus/diorama with:

- Executive Terrace / Board
- Central Atrium
- Mission Hub
- Regulatory / Evidence
- Technology / Security
- Operations
- case/client work areas
- coffee/lounge/courtyard/terrace

Architecture communicates organization and supports spatial memory.

---

## Motion rules

Separate:

### Ambient motion
Presentation-only life:
- breathing
- glance
- stretch
- coffee
- local walk
- desk/tablet gestures

### Semantic motion
Requires supported state/event:
- handoff
- Mission collaboration
- governed conversation
- blocker response
- Owner escalation
- Board interaction
- completion

Every semantic animation requires:
- canonical input
- allowed interpretation
- forbidden implication
- reduced-motion equivalent
- test

---

## Accessibility

Target WCAG 2.2 AA for structured UI.

Never require:
- color alone
- hover alone
- motion
- 3D
- pointer-only interaction

for essential meaning or action.

---

## Performance

The structured shell must become usable before heavy 3D finishes loading.

Exact budgets must be measured from the V2 prototype before becoming hard requirements.

---

## Anti-slop rule

Reject designs that could plausibly be any generic SaaS template.

If the screenshot says “dashboard” before it says “AIOS,” redesign it.

---

## Acceptance

A surface is not complete until it passes:

- goal clarity
- hierarchy
- UX laws
- truth review
- authority review
- accessibility
- responsive behavior
- performance
- visual consistency
- distinctiveness
- automated/visual regression where applicable
