# Global Mobility AIOS — Frontend Design & UX Programme V1

**Date:** 2026-08-22
**Status:** ACTIVE PRODUCT-DESIGN CAPABILITY / SUBORDINATE TO MASTER ROADMAP
**Active branch:** `roadmap/global-mobility-aios-v12`
**Master scheduling authority:** `ROADMAP.md`
**Preferred current design environment:** Penpot — replaceable; not product authority
**Production frontend authority:** repository-owned Next.js/React frontend
**Component-workbench candidate:** Storybook — adoption requires bounded proof
**Related product milestones:** L — Live Organization; M — Board Transparency Experience
**Related donor programme:** `MUNDER_DIFFLIN_AIOS_ADOPTION_V1.md`

This programme defines how product experience should evolve. It does not independently determine which product capability is implemented next; `ROADMAP.md` does.

The requirement is coherent, accessible, truthful product design. Penpot, Storybook or any future tool is an implementation choice, not a constitutional dependency.

---

## 1. Why this programme exists

Global Mobility AIOS has strong domain, governance, Evidence and organization-runtime architecture, but frontend product design must be a first-class product workstream rather than an implementation afterthought.

Permanent rule:

> **A technically correct AI organization is not a complete product until humans can understand, supervise and operate it through a coherent experience.**

Frontend design must not invent truth. It must make canonical AIOS truth legible, actionable and calm under uncertainty.

---

## 2. Design dependency model

```text
product need
→ canonical domain / organization state
→ real read/write contracts
→ information architecture
→ interaction semantics
→ reusable design-system capability
→ repository-owned React implementation
→ accessibility / responsive / interaction verification
→ browser/product proof
```

Tools may support this sequence but do not define it.

Penpot may be used for intended layouts, flows, components and token exploration. Storybook may be used as a component workbench if a bounded repository adoption proves value. Neither is runtime or business-state authority.

Generated design code may never bypass normal repository review, accessibility, tests or canonical data contracts.

---

## 3. Visual direction

The target remains premium enterprise software with a distinct AI operating-system identity rather than generic SaaS/admin presentation or dark sci-fi styling.

Direction:

- deep navy / graphite with warm ivory foundations;
- selective editorial serif paired with modern operational sans;
- restrained glass/depth, not decorative translucency everywhere;
- high-quality iconography;
- subtle semantic motion;
- luxury-level spacing and typography;
- information-dense but calm operational composition;
- visible Evidence, provenance, authority, autonomy, risk and blocked-state semantics;
- modern 2D/2.5D Living Organization only where it improves operational understanding.

The visual system must never imply activity, evidence or authority that canonical state does not contain.

---

## 4. Design-system capability layers

```text
Foundations
  typography / spacing / radius / elevation / motion / breakpoints

Semantic tokens
  surface / text / evidence / authority / autonomy / risk / status / activity / focus

Primitives
  controls / fields / badges / cards / tables / timelines / overlays / navigation

Governance patterns
  Evidence provenance / authority gate / blocked work / Decision Readiness / review / escalation

Organization patterns
  employee presence / WorkItem / objective / execution / activity / runtime lineage / collaboration

Product surfaces
  Cockpit / Board Room / Operations / My Mobility / department workspaces
```

Build only the layers required by active and immediately next product surfaces. Do not create a speculative complete component library before a product need exists.

---

## 5. UX capability slices

These slices describe design maturity. Their scheduling and priority are controlled by `ROADMAP.md`.

### UX0 — Product experience audit and information architecture

Current L-related work includes:

- inventory existing frontend routes/components and historical UI concepts;
- map user roles and jobs-to-be-done;
- reconcile Cockpit, Board Room, Operations, My Mobility and department workspaces;
- identify duplicate/legacy dashboard concepts;
- establish navigation/information hierarchy;
- define responsive/accessibility constraints;
- audit the existing `/cockpit/live-organization` surface against the real L contract.

### UX1 — Bounded design-system foundation

Build only foundations required by L/M:

- semantic tokens;
- component naming/state conventions;
- loading/empty/error/blocked/authority patterns;
- reusable primitives actually repeated by current surfaces;
- accessibility acceptance floors;
- component-workbench adoption only if repository evidence justifies it.

Penpot is the preferred current design environment for this work, but Penpot adoption itself is not an L acceptance gate.

Storybook remains a candidate workbench. It must not become a second application architecture.

### UX2 — Live Organization experience

Design against real L contracts rather than fictional product state.

Required states include, as applicable:

- objective and organizational topology;
- specialist WorkItems;
- employee/runtime presence;
- execution state;
- durable outputs;
- owner synthesis readiness/result;
- blocked work and fail-closed reason;
- Evidence/rule provenance;
- authority/autonomy/risk;
- retry/latency/runtime lineage;
- deterministic refresh/replay semantics;
- explicit missing/not-connected states.

Mock data may be used for design exploration but may never be represented as accepted live product state.

### UX3 — Board Transparency Experience

When M becomes primary, design/implement:

- executive Cockpit overview;
- Organization view;
- objectives/work view;
- agent/position view;
- Performance / Quality / Risk / Incidents / Autonomy / Transparency;
- Board Room as a module inside Cockpit;
- drill-down from executive signal to canonical provenance;
- retained-authority and escalation interactions.

### UX4 — Operations + My Mobility convergence

After the relevant contracts stabilize:

- professional/operator workflow optimization;
- journey-centric customer experience;
- progressive disclosure of governance/technical detail;
- mobile/responsive behavior;
- accessibility and usability validation.

### UX5 — Living Organization visualization

Selective implementation only after real organization state and user need justify it.

Animation must be semantic and runtime-derived, never decorative fake activity.

---

## 6. Penpot posture

Penpot is the preferred current design environment because it aligns with open-source tooling, portability, design-token ownership and web-native layout semantics.

Current posture:

```text
use Penpot where it reduces design/implementation ambiguity
→ retain AIOS-owned token/component semantics
→ export/version material design contracts where needed
→ evaluate self-hosting only when operationally justified
```

Penpot is replaceable.

No Penpot plugin/MCP/generated-code path may directly commit production UI without normal repository review, tests and design-system boundaries.

---

## 7. Storybook posture

Storybook is a candidate component-workbench direction, not an accepted dependency merely because it is useful.

Potential value:

- explicit component states;
- accessibility checks;
- visual regression workflows;
- reusable component proof;
- reduced page-local duplication;
- bridge between design intent and React implementation.

Before adoption, prove that it solves a current component/testing gap with acceptable maintenance cost.

If adopted, Storybook remains a workbench—not product-state authority and not a second application architecture.

---

## 8. Munder Difflin relationship

Munder Difflin v0.4.4 remains a strategic donor and may be evaluated when `ROADMAP.md` identifies a relevant L/M/UX gap.

Potentially useful concepts include:

- live office scene/event synchronization;
- employee presence/heartbeat visualization;
- character positioning;
- collaboration grouping;
- live message/tool signals;
- runtime-driven animation;
- transcripts;
- tool/action timeline concepts;
- token/cost telemetry where useful to AI Economics.

Explicitly replace/reject:

- pixel-art visual language as the target UI;
- retro/game-like office presentation;
- random wandering/decorative activity;
- GOD-character metaphor;
- donor state as canonical organization truth;
- direct donor mutation of authoritative AIOS state.

Munder mechanics may accelerate a proven need, but AIOS canonical state drives every meaningful status and AIOS design semantics define the product experience.

---

## 9. Frontend acceptance gates

A frontend slice is not accepted because it resembles a design frame.

As applicable, acceptance should prove:

1. canonical read/write contract fidelity;
2. no fake live organization state;
3. loading/empty/error/blocked states;
4. authority/autonomy/risk semantics;
5. Evidence/provenance visibility;
6. keyboard operation and focus behavior;
7. semantic HTML/accessibility baseline;
8. responsive behavior at defined breakpoints;
9. reusable implementation where repetition exists;
10. deterministic rendering/refresh behavior;
11. frontend tests/types/build;
12. browser E2E for material interaction paths;
13. repository-policy compliance;
14. Woodpecker proof before acceptance claims.

Tool adoption is tested separately from product acceptance. A product can satisfy the design requirement without a particular workbench if the required evidence exists.

---

## 10. Relationship to L and M

The product/design relationship is overlapping rather than waterfall:

```text
L canonical runtime/read-write truth
        ↕
UX0 information architecture audit
        ↕
bounded UX1 foundations needed by real surfaces
        ↕
UX2 Live Organization design and implementation refinement
        ↓
L product/browser acceptance
        ↓
M becomes primary + UX3 Board Transparency work
```

This prevents both backend-first UI neglect and design-first fictional product state.

---

## 11. Scheduling authority

`ROADMAP.md` determines when UX0–UX5 are PRIMARY, REQUIRED ENABLEMENT, SUPPORTING PARALLEL or deferred.

This document intentionally does not create a second delivery chronology.

When the master roadmap changes product priority, reconcile this document only where the product-design implications change.

---

## 12. Repository truth

This document establishes product/design capability direction only.

It does not claim that Penpot, Storybook, a new component library or Munder-derived frontend mechanics are production-adopted merely because they are named here.

Any dependency/tool adoption must follow the same necessity-driven decision, bounded implementation, tests, Woodpecker proof and documentation reconciliation used elsewhere in AIOS.
