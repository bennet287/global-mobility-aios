# AIOS UI Design-System Methodology

## Purpose

This document converts the generic "build a scalable UI kit" methodology into the AIOS-specific operating method for visible UI/UX redesign work.

AIOS is not a generic dashboard and this method must never be used to flatten the product into a reusable-but-anonymous SaaS kit. The goal is a coherent, production-ready design language that makes every AIOS surface more distinctive, more usable, and easier to extend without design drift.

Product thesis:

> **AIOS = Executive Intelligence × Living Organization × Spatial Computing × Architectural Character World**

Design-system thesis:

> **Do not create an isolated attractive component. Create the smallest reusable piece of the AIOS design language that makes the current surface better and makes every future surface easier to build consistently.**

---

## 1. Context

AIOS is being redesigned under competing pressures:

- rapid product delivery
- strict truth/governance constraints
- multiple user experiences: Owner/Board, Professional/Operator, Mobility User
- structured 2D work surfaces plus a Living Organization spatial world
- responsive, touch, keyboard and assistive-technology requirements
- a need for visual distinction without fragile one-off styling
- a need to prevent repeated UI rewrites, inconsistent spacing, conflicting component states, and local CSS drift

Previous UI evolution produced useful functionality but too much module-shaped presentation and insufficiently distinctive visual identity. The redesign must therefore create a shared language rather than another collection of screens.

---

## 2. Design role

When performing AIOS UI work, operate as a **senior design-systems architect and product designer**, not as a component decorator.

Responsibilities:

- protect system coherence while improving the specific screen
- prefer reusable primitives and product patterns over one-off CSS
- preserve domain truth and authority boundaries
- preserve accessibility and structured fallback
- make the interface recognizably AIOS rather than generically modern
- document the rule created by the implementation, not only the implementation itself
- optimize for maintainability and future migration across all three user experiences

---

## 3. Required design order

Before implementing a visible surface, determine:

1. user/role
2. task and success condition
3. canonical data and truth class
4. authority/mutation posture
5. primary information hierarchy
6. L0-L4 information depth
7. interaction model
8. reusable pattern/component opportunities
9. token requirements
10. responsive/touch behavior
11. keyboard/assistive behavior
12. motion behavior and reduced-motion equivalent
13. spatial relationship, if any
14. loading/empty/partial/unavailable/error states
15. visual composition/material hierarchy
16. browser acceptance scenarios

Aesthetic implementation comes after these decisions, not before them.

---

## 4. System hierarchy

AIOS UI must be built hierarchically.

### 4.1 Foundations

- color
- typography
- spacing
- sizing
- radius
- border
- elevation
- material
- grid/layout
- iconography
- motion
- focus
- semantic state
- truth class
- department accent

### 4.2 UI primitives

- button
- link
- icon button
- input/select/checkbox/radio
- badge/status
- tabs/segmented controls
- list/table row
- section heading
- disclosure/details
- dialog
- drawer/inspector
- toast/notice
- loading/empty/error state

### 4.3 AIOS product components

- Mission Surface
- Work Object
- Owner Attention Object
- Employee Identity
- Evidence Object
- Source Object
- Decision Object
- Authority Gate
- Friction/Risk Signal
- Handoff Signal
- Temporal Lens
- Replay Cursor
- Compare Delta
- Provenance Drawer
- Command Surface
- Department Surface

### 4.4 Product patterns

- executive situation room
- Mission workspace
- evidence inspection
- decision/authority review
- replay/history exploration
- contextual command/search
- operator dense-work pattern
- mobility-user guided case pattern

### 4.5 Living Organization design language

- character grammar
- role/seniority/department identity
- employee state grammar
- Mission-room grammar
- semantic collaboration/handoff grammar
- ambient behavior grammar

### 4.6 Spatial architecture language

- architectural materials
- room grammar
- wing grammar
- lighting
- atmosphere
- smart objects
- wayfinding
- HQ composition

The hierarchy flows downward from foundations. Product work may extend the system, but must not bypass it with unexplained local values.

---

## 5. Token methodology

Prefer semantic tokens over component-specific magic values.

Required token families include:

- canvas/surface/material
- text hierarchy
- border hierarchy
- spacing and sizing
- radius/elevation
- interaction/focus
- semantic status
- truth class
- department identity
- motion duration/easing/emphasis

Motion token direction:

- `motion-duration-instant`
- `motion-duration-fast`
- `motion-duration-normal`
- `motion-duration-deliberate`
- `motion-ease-enter`
- `motion-ease-exit`
- `motion-ease-emphasis`
- `motion-semantic-working`
- `motion-semantic-blocked`
- `motion-semantic-handoff`
- `motion-semantic-completion`
- `motion-ambient-idle`

Exact values are implemented only after visual/prototype validation. Reduced-motion behavior is part of the token contract, not an afterthought.

---

## 6. Component contract

Every reusable component must define, where applicable:

- purpose
- allowed content
- semantic HTML/ARIA role
- size variants
- visual variants
- default/hover/focus/pressed/selected/disabled states
- loading/empty/unavailable/error states
- long-content behavior
- responsive behavior
- touch target behavior
- keyboard behavior
- reduced-motion behavior
- truth/authority implications
- composition rules
- anti-patterns

Do not create variants merely because CSS can support them. Variants exist only for recurring product needs.

---

## 7. Visual identity rules

Selected direction:

> **Contemporary architectural luxury + premium operating-system restraint.**

AIOS should feel intelligent, calm, capable, premium, deliberate, contemporary, alive and governed.

Reject:

- template SaaS card grids
- generic AI purple gradients
- cyberpunk/neon visual noise
- glass everywhere
- giant rounded rectangles without hierarchy
- arbitrary gradients or glow
- inconsistent local spacing
- random button styles
- decorative charts with no question to answer
- icons/emoji used as the sole semantic channel

If a screenshot says "generic dashboard" before it says "AIOS", the design does not pass.

---

## 8. UX composition rules

Do not optimize screens around storage/module topology. Optimize around human questions and tasks.

Owner surfaces should continuously connect:

> **What happened → why it matters → who owns it → what supports it → what can I do next?**

Use progressive disclosure:

- L0 ambient
- L1 attention
- L2 context
- L3 evidence
- L4 provenance/internals

Do not default primary surfaces to L4.

Primary action scarcity applies: a focused surface should not present many equal-weight calls to action.

---

## 9. Truth and motion rules

Truth classes must remain visually and semantically distinct:

- canonical
- human-authoritative
- AI recommendation
- memory/aggregate
- prediction
- simulation
- historical reconstruction
- partial/unavailable/unknown

Permanent motion law:

> **The organization causes the animation. Animation never causes the organization.**

Ambient motion may create life without asserting work. Semantic motion requires supported organizational state/event and must define forbidden implications plus a reduced-motion equivalent.

---

## 10. Responsive and accessibility method

Desktop, tablet and phone are composition modes, not scaled screenshots.

For every major component/pattern verify:

- content re-prioritization
- no essential hover-only interaction
- touch targets
- keyboard reachability
- visible focus
- logical heading/landmark structure
- accessible names
- 200% zoom/reflow
- screen-reader/accessibility-tree readability
- reduced motion
- structured non-3D equivalent for essential spatial information

Never communicate essential meaning through color, motion or 3D alone.

---

## 11. Implementation discipline

When redesigning a screen:

1. audit current patterns and tokens
2. reuse the closest valid primitive/pattern
3. extend the system if the need is recurring
4. avoid one-off values when a semantic token belongs in the system
5. keep components composable; avoid giant all-purpose components
6. preserve real-world long-content behavior
7. add documentation for new reusable rules
8. add regression tests for important states
9. inspect the production browser result
10. compare before/after visually and task-by-task

Do not accept a design merely because TypeScript/build/CI are green.

---

## 12. Visible redesign acceptance gate

For visible UI/UX phases, acceptance order is:

> **implementation → production browser → screenshots → visual inspection → UX walkthrough → accessibility/responsive review → automated tests → exact-head CI → merge**

A visible redesign fails acceptance when:

- before/after looks materially the same despite a redesign claim
- information hierarchy remains generic or flat
- new UI introduces local design drift
- long or unavailable content breaks composition
- accessibility or responsive behavior regresses
- motion invents organizational truth
- the result is polished but could plausibly be any SaaS product

Visual transformation is a deliverable, not a side effect of passing tests.

---

## 13. Required implementation output

A significant UI-system slice should make clear:

- **design tokens** added/changed and why
- **components/patterns** added/changed
- **typography/hierarchy** decisions
- **interaction states** covered
- **responsive/touch/accessibility** behavior
- **motion** behavior if relevant
- **component documentation / usage rules**
- **migration impact** on existing surfaces
- **browser screenshots** showing the real result
- **known limitations/deferred work**

The repository implementation remains the source of truth; documentation describes the accepted system rather than substituting for it.
