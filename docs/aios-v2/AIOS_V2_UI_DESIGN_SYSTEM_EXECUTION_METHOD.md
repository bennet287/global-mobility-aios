# AIOS V2 — UI Design-System Execution Method

**Document status:** NORMATIVE V2 EXECUTION ADDENDUM
**Date:** 2026-09-07
**Applies to:** `AIOS_V2_COMPLETE_REDESIGN_MASTER_PLAN.md`
**Canonical design method:** `skills/aios-design/ui/design-system-methodology.md`

---

## 1. Decision

The AIOS V2 complete-redesign program adopts the AIOS-specific UI design-system methodology as the mandatory execution method for all future visible UI/UX redesign work.

This addendum does **not** replace the master plan. It strengthens how the UI portions of that plan are executed and accepted.

The generic methodology supplied as reference—systematic tokens, reusable components, consistent states, responsive/accessibility behavior, documentation, composability, and hierarchical construction—is adopted only after being specialized for AIOS.

The operative AIOS rule is:

> **Do not create an isolated attractive component. Create the smallest reusable piece of the AIOS design language that makes the current surface better and makes every future surface easier to build consistently.**

---

## 2. Why this is now explicit

The current V2 program has built substantial truth, accessibility, fallback, responsive, testing, performance and design-system foundations. However, future visible redesign work must not become another sequence where implementation/CI progress is mistaken for visual or UX transformation.

From the visible-redesign phase onward:

- reusable system quality and visible product quality are both required
- screenshots and task walkthroughs are first-class acceptance evidence
- a green CI run cannot by itself prove a redesign succeeded
- a component must strengthen the shared AIOS language rather than create local design debt

---

## 3. AIOS design-system hierarchy

The master-plan UI work is executed in this hierarchy:

```text
AIOS DESIGN SYSTEM
│
├── Foundations
│   ├── color / truth color
│   ├── typography
│   ├── spacing / sizing
│   ├── radius / borders / elevation
│   ├── materials
│   ├── grid / layout
│   ├── iconography
│   ├── focus
│   ├── motion
│   └── semantic / truth states
│
├── UI primitives
│   ├── buttons / links
│   ├── fields / controls
│   ├── status / badges
│   ├── navigation
│   ├── dialogs
│   ├── inspectors / drawers
│   ├── disclosures
│   └── loading / empty / unavailable / error
│
├── AIOS product components
│   ├── Mission Surface
│   ├── Work Object
│   ├── Owner Attention Object
│   ├── Employee Identity
│   ├── Evidence / Source Object
│   ├── Decision / Authority Gate
│   ├── Friction / Risk / Handoff Signal
│   ├── Temporal Lens / Replay Cursor
│   └── Provenance Drawer / Command Surface
│
├── Product patterns
│   ├── executive situation room
│   ├── Mission workspace
│   ├── evidence inspection
│   ├── decision / Board review
│   ├── replay / history
│   ├── operator dense work
│   └── mobility guided-case flow
│
├── Living Organization language
│   ├── character grammar
│   ├── role / seniority / department identity
│   ├── employee state grammar
│   ├── Mission-room grammar
│   └── semantic collaboration / handoff grammar
│
└── Spatial architecture language
    ├── architectural materials
    ├── room / wing grammar
    ├── lighting / atmosphere
    ├── smart objects / wayfinding
    └── HQ composition
```

Product implementation may extend this system, but may not bypass it with unexplained one-off visual values.

---

## 4. Relationship to master-plan phases

### Foundation work

Any future foundation refinement must strengthen tokens/primitives rather than restart them from scratch.

### Owner / Board visible redesign

Owner Home, Missions, Evidence, Decisions, Intelligence and History must use shared product components/patterns and must be evaluated as a coherent executive operating system rather than individual dashboard pages.

### Character production

Character identity must be systematic: shared artistic DNA plus role, seniority, department, silhouette, wardrobe, prop and behavior grammar.

### HQ architecture

The HQ must use a reusable architectural grammar—materials → objects → rooms → zones → wings → whole HQ—rather than a one-off scene.

### Living Organization V2

2D structured UI, characters and spatial HQ must feel like representations of the same organization and use consistent semantic state/truth language.

### Operator migration

Operator surfaces inherit the accepted AIOS foundations/components rather than creating a second design system optimized only for density.

### Mobility-user migration

Mobility surfaces inherit the same foundational system while simplifying terminology, density and interaction patterns for the end user.

### Legacy retirement

One-off legacy components and CSS should be removed only after their capability is represented by the accepted system.

---

## 5. Required design order for each visible slice

Before implementation:

1. user and role
2. task / success condition
3. canonical state and truth class
4. authority / mutation posture
5. information hierarchy
6. L0-L4 information depth
7. interaction model
8. reusable component/pattern opportunity
9. token requirements
10. responsive/touch behavior
11. keyboard/assistive behavior
12. motion/reduced-motion behavior
13. spatial implications
14. loading/empty/partial/unavailable/error states
15. visual composition/material hierarchy
16. production-browser acceptance scenarios

Do not begin by choosing card shapes, gradients or animation.

---

## 6. UI implementation requirements

Significant visible redesign slices must explicitly identify:

- tokens added/changed
- primitives/components added/changed
- product patterns introduced/reused
- typography/hierarchy decisions
- interaction states
- long-content behavior
- unavailable/partial/error behavior
- responsive/touch behavior
- keyboard/assistive behavior
- motion/reduced-motion behavior where relevant
- migration effect on existing surfaces
- documentation/usage guidance
- browser screenshots
- known limitations/deferred work

Avoid giant all-purpose components and avoid creating variants without recurring product need.

---

## 7. Visible UI/UX acceptance gate

For visible-redesign phases, acceptance order is now explicitly:

> **implementation → production browser → screenshots → visual inspection → UX walkthrough → accessibility/responsive review → automated tests → exact-head CI → merge**

The following are rejection conditions:

- a claimed redesign looks materially the same before and after
- the screen still reads as a generic SaaS/dashboard template
- information hierarchy remains flat
- product/module topology still dominates human task topology
- a new one-off component duplicates an existing system concept
- inconsistent spacing/type/button states appear
- real long content breaks the layout
- unavailable/partial truth is visually collapsed into certainty
- essential meaning depends on color, hover, motion or 3D
- semantic motion invents organizational activity
- accessibility/responsive behavior regresses

**Visual transformation is a deliverable, not a side effect of passing tests.**

---

## 8. Permanent product-specific laws

### Product thesis

> **AIOS = Executive Intelligence × Living Organization × Spatial Computing × Architectural Character World**

### Truth law

> **Visual clarity must never reduce truth clarity.**

### Motion law

> **The organization causes the animation. Animation never causes the organization.**

### Spatial law

> **Every essential spatial fact must have a structured accessible equivalent.**

### Anti-template law

> **If the screenshot says “dashboard” before it says “AIOS,” redesign it.**

### System law

> **A new surface should consume and strengthen the AIOS design language; it should not become its own design language.**

---

## 9. Immediate sequencing impact

The current program sequence remains:

1. finish the bounded remaining technical acceptance/hardening work
2. finish canonical semantic Living Organization integration
3. begin the major visible UI/UX redesign using this methodology
4. migrate Professional/Operator on the accepted UI language
5. migrate Mobility User on the accepted UI language
6. retire superseded legacy presentation
7. perform whole-product final acceptance

When step 3 begins, visible browser improvement becomes the primary design deliverable. Engineering proof supports that transformation; it does not substitute for it.

---

## 10. Source of execution truth

For future UI work, the relevant order is:

1. `docs/aios-v2/AIOS_V2_COMPLETE_REDESIGN_MASTER_PLAN.md` — overall program scope and phases
2. this document — binding UI execution/acceptance addendum
3. `skills/aios-design/SKILL.md` — design laws and required-reference routing
4. `skills/aios-design/ui/design-system-methodology.md` — detailed UI design-system method
5. specialized UI/UX/character/architecture/motion/governance skill files — implementation-specific rules
6. accepted repository implementation/tests — final technical source of truth
