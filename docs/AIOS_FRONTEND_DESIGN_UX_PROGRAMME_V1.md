# Global Mobility AIOS — Frontend Design & UX Programme V1

**Date:** 2026-08-22
**Status:** ACTIVE PRODUCT-DESIGN DIRECTION / NO RUNTIME ACCEPTANCE CLAIM
**Active branch:** `roadmap/global-mobility-aios-v12`
**Primary design environment:** Penpot — open-source; cloud-first initially, self-hosting eligible later
**Implementation authority:** repository-owned Next.js/React frontend
**Component implementation authority:** Storybook-oriented reusable component system (adoption to be proven in a bounded implementation slice)
**Related product milestones:** L — Live Organization; M — Board Transparency Experience
**Related donor programme:** `MUNDER_DIFFLIN_AIOS_ADOPTION_V1.md`

## 1. Why this programme exists

Global Mobility AIOS has strong domain, governance, Evidence, organization-runtime and integration architecture, but frontend product design must be treated as a first-class product workstream rather than an implementation afterthought.

The permanent rule is:

> **A technically correct AI organization is not a complete product until humans can understand, supervise and operate it through a coherent experience.**

Frontend design must not invent truth. It must make canonical AIOS truth legible, actionable and appropriately calm under uncertainty.

## 2. Product-design architecture

```text
AIOS canonical domain / organization state
        ↓
read models / typed API contracts
        ↓
interaction semantics + information architecture
        ↓
AIOS Design System
        ↓
Penpot product/design source
        ↓
repository-owned React components
        ↓
Storybook component proof
        ↓
Next.js product surfaces
        ↓
accessibility / responsive / visual / interaction verification
```

Penpot is design authority for intended layouts, flows, components and tokens. It is never runtime or business-state authority.

Storybook, if adopted after the bounded foundation slice, is implementation/component authority rather than product-state authority.

## 3. Visual direction

The target remains premium enterprise software with a distinct AI operating-system identity rather than a generic SaaS/admin dashboard or dark sci-fi control panel.

Direction:

- deep navy / graphite with warm ivory foundations;
- selective editorial serif paired with modern operational sans;
- restrained glass/depth, not decorative translucency everywhere;
- high-quality iconography;
- subtle semantic motion;
- luxury-level spacing and typography;
- information-dense but calm operational composition;
- visible Evidence, provenance, authority, autonomy, risk and blocked-state semantics;
- modern 2D/2.5D Living Organization where it adds operational understanding.

## 4. Design-system layers

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

Tokens should remain portable and implementation-friendly; Penpot token semantics should map deliberately into repository-owned frontend tokens rather than through uncontrolled generated code.

## 5. Frontend design sprints

Frontend work becomes an explicit parallel product track.

### UX0 — Product experience audit and information architecture — NOW

- inventory existing frontend routes, components and historical UI documentation;
- map user roles and primary jobs-to-be-done;
- reconcile Cockpit, Board Room, Operations, My Mobility and department workspaces;
- identify duplicate/legacy dashboard concepts;
- establish navigation and information hierarchy;
- define critical responsive and accessibility constraints.

### UX1 — AIOS Design System Foundation — START DURING L

- establish Penpot project/library structure;
- define foundations and semantic design tokens;
- define component naming/state conventions;
- establish implemented component workbench/Storybook boundary after repository audit;
- build core primitives required by L/M rather than a speculative complete library;
- establish accessibility acceptance floors.

### UX2 — Live Organization Experience — CO-DESIGN WITH L

Design against real L read-model contracts, not mocked product claims.

Required states include:

- objective and organizational topology;
- specialist WorkItems;
- employee/runtime presence;
- execution state;
- current durable outputs;
- owner synthesis readiness/result;
- blocked work and fail-closed reason;
- Evidence/rule provenance;
- authority/autonomy/risk;
- retry/latency/runtime lineage;
- deterministic refresh/replay semantics.

Mock data may be used inside Penpot for design exploration but may never be represented as accepted live product state.

### UX3 — Board Transparency Experience — M

M becomes both a transparency/runtime milestone and a formal frontend design/implementation sprint.

Design and implement:

- executive Cockpit overview;
- Organization view;
- objectives/work view;
- agent/position view;
- Performance / Quality / Risk / Incidents / Autonomy / Transparency;
- Board Room as a module inside Cockpit, not the name of the whole control surface;
- drill-down from executive signal to canonical provenance;
- retained-authority and escalation interactions.

### UX4 — Operations + My Mobility convergence

After L/M contracts stabilize:

- professional/operator workflow optimization;
- journey-centric client experience;
- progressive disclosure of technical/governance detail;
- mobile/responsive behavior;
- accessibility and usability validation.

### UX5 — Living Organization visualization

Selective implementation after real organization state exists. Animation must be semantic and runtime-derived, never decorative fake activity.

## 6. Penpot decision

Penpot is the preferred design environment because it aligns with AIOS goals around open-source tooling, portability, design-token ownership, web-native Flex/Grid semantics and optional self-hosting.

Initial policy:

```text
Penpot Cloud for low-friction design-system establishment
→ export/version important design assets and token contracts
→ evaluate self-hosting when design data becomes operationally material
```

Self-hosting is an operational option, not an immediate prerequisite.

No Penpot plugin/MCP/generated-code path may directly commit production UI without normal repository review, tests and design-system boundaries.

## 7. Storybook decision

Storybook is the preferred component-workbench direction, subject to a bounded repository audit before dependency adoption.

Purpose:

- prove reusable component states independently;
- make loading/empty/error/blocked/authority states explicit;
- support accessibility and visual regression workflows;
- prevent page-local duplicate component systems;
- provide a bridge between Penpot intent and Next.js implementation.

Storybook must not become a second application architecture.

## 8. Munder Difflin relationship

Munder Difflin v0.4.4 remains a strategic donor and must be considered explicitly during L/M/UX work.

High-value frontend/runtime donor concepts to study:

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

- pixel-art visual language;
- retro/game-like office presentation;
- random wandering/decorative activity;
- GOD-character metaphor;
- donor state as canonical organization truth;
- direct donor mutation of authoritative AIOS state.

Munder mechanics may accelerate the Living Organization experience, but Penpot/AIOS Design System defines the target visual language and AIOS canonical state drives every meaningful status.

## 9. Design acceptance gates

A frontend slice is not accepted merely because it resembles a Penpot frame.

As applicable, acceptance should prove:

1. canonical read-model fidelity;
2. no fake live organization state;
3. loading/empty/error/blocked states;
4. authority/autonomy/risk semantics;
5. Evidence/provenance visibility;
6. keyboard operation and focus behavior;
7. semantic HTML/accessibility baseline;
8. responsive behavior at defined breakpoints;
9. reusable components instead of page-local duplication;
10. deterministic rendering/refresh behavior;
11. frontend tests/types/build;
12. repository-policy compliance;
13. Woodpecker proof before acceptance claims.

## 10. Relationship to L and M

The sequence is intentionally overlapping rather than waterfall:

```text
L backend/runtime truth
   ↕
UX0/UX1 information architecture + design system
   ↕
UX2 Live Organization design against real contracts
   ↓
L accepted live read model
   ↓
M + UX3 Board Transparency implementation
```

This prevents both backend-first UI neglect and design-first fictional product state.

## 11. Repository truth

This document establishes product/design direction only. It does not claim that Penpot, Storybook, a new component library or Munder-derived frontend mechanics are already production-adopted.

Any dependency or runtime adoption must follow normal bounded implementation, tests, Woodpecker proof and documentation reconciliation.