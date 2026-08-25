# Track B — UX0 / UX1 Execution Baseline

**Date:** 2026-08-25  
**Status:** IMPLEMENTATION STARTED / ACCEPTANCE NOT CLAIMED  
**Branch:** `work/b-ux0-ux1-foundation-20260825`  
**Scheduling authority:** `docs/ROADMAP.md`  
**Design authority:** `docs/AIOS_FRONTEND_DESIGN_UX_PROGRAMME_V1.md`  
**Donor programme:** `docs/MUNDER_DIFFLIN_AIOS_ADOPTION_V1.md`

## 1. Purpose

Track B is the active parallel product-experience workstream while Milestone L remains implemented but externally acceptance-pending.

This slice starts two allowed pieces of Track B:

1. **UX0 — product experience / information architecture audit**;
2. **UX1 — bounded design-system foundation**, beginning with a reusable truthful operational-status primitive used by the shared Topbar.

It does **not** advance Milestone M, claim UX0/UX1 complete, or substitute frontend work for the remaining L external/human/live-provider acceptance evidence.

## 2. Repository-truth audit

### 2.1 Experience architecture already present

The current first-party frontend already has three explicit experience shells:

- **Cockpit** — Owner / Board;
- **Operations** — Professional / Operator;
- **My Mobility** — Mobility User.

`apps/web/lib/workspace-navigation.ts` is the current navigation authority for these experience shells. Board Room remains a module within the Owner/Cockpit experience rather than the name of the entire control surface.

### 2.2 Shared shell foundations already present

`WorkspaceShell` already provides:

- one main landmark;
- a skip link;
- mobile navigation focus containment;
- Escape-to-close behavior;
- focus restoration to the menu trigger;
- backend-health-aware shared navigation.

This means Track B should extend the existing shell rather than introduce a second layout architecture.

### 2.3 Existing design-system foundation is real but fragmented

The current frontend already contains meaningful foundation work in `app/globals.css`, including:

- typography scales;
- spacing/radius/shadow tokens;
- semantic status colors;
- premium navy/ivory/editorial Cockpit styling;
- reduced-motion handling;
- compact control-rail behavior;
- responsive rules;
- truthful Live Organization styling.

The primary UX1 problem is therefore **not absence of design work**. It is that reusable semantics are still partially page-local and the global stylesheet mixes multiple historical generations of component styling.

Track B should progressively move new reusable semantics into narrow repository-owned primitives without attempting a risky wholesale CSS rewrite.

### 2.4 Operational status gap selected for the first UX1 slice

The current shared Topbar defines workspace state labels and descriptions locally. Its existing `.workspace-state` presentation also disappears entirely on narrow screens.

That is a suitable bounded UX1 seam because workspace availability is meaningful operational state and should have one reusable semantic contract across product surfaces.

The first implementation slice therefore extracts the state contract into a shared component and introduces a small Track-B semantic stylesheet for it. The visual state remains compact on narrow screens instead of removing the signal.

## 3. UX2 Live Organization audit

The current `/cockpit/live-organization` surface already satisfies several important UX2 rules:

- reads persisted AIOS projection state rather than invented demo activity;
- distinguishes loading, unavailable, authentication and authorization states;
- exposes owner-synthesis readiness rather than inferring it client-side;
- shows specialist evidence validity, latency and retries;
- shows blockers and human-action requirements;
- exposes Evidence / VerifiedRule absence explicitly;
- does not treat provider/model identity as authority;
- does not imply external-action authorization where none exists.

### Current presence/heartbeat boundary

The current frontend contract does **not** expose a canonical employee heartbeat or presence timestamp. `AustriaLiveSpecialist` exposes durable execution lineage, status, latency and retry data, but not a heartbeat contract.

Therefore Track B must **not** derive an "online employee" or "heartbeat healthy" state from page refresh time, latest activity time, WorkItem status, or animation.

Until a canonical presence read model exists, the truthful product behavior is to show presence as unavailable/not connected rather than manufacture live-office activity.

## 4. Munder Difflin controlled-adoption map for Track B

Munder remains a frozen strategic donor. The frontend does not inherit donor truth, authority or visual identity.

| Donor capability | Track B classification | Current AIOS destination | Decision for this slice |
|---|---|---|---|
| presence / heartbeat | ADAPT | Employee Presence / Health + Live Organization | **NEXT BOUNDED DONOR SLICE** once canonical backend/read-model presence exists |
| scene/event synchronization | ADAPT | Live Organization / Event Nervous System projection | defer until a real event stream/read model is proven |
| collaboration grouping | ADAPT | WorkItem / squad visualization | defer until canonical squad/collaboration contract is exposed |
| live message/tool signals | ADAPT | Transparency / activity timeline | study against persisted `OrganizationActivity`; no provider-log shortcut |
| transcripts | ADAPT | Transparency / Flight Recorder | not part of this first UX1 slice |
| runtime/token/cost telemetry | ADAPT | AI Economics + Transparency | not part of this first UX1 slice |
| pixel-art office presentation | REJECT | final AIOS visual identity | remains rejected |
| random wandering / decorative busywork | REJECT | Live Organization animation | remains rejected |
| donor state as canonical state | REJECT | all AIOS product surfaces | remains rejected |

## 5. Target information hierarchy

The current target remains:

```text
Global Mobility AIOS Cockpit
├── Cockpit Overview
├── Live Organization
├── Owner Inbox
├── Board Room
├── External Validation
├── Intelligence & Evidence
└── Organization / execution controls

Operations
├── case/profile work
├── planning/pathways/timelines
├── Evidence & Review
└── governed execution

My Mobility
├── case progress
├── document/evidence requests
├── timeline / next action
└── secure case workspace
```

This slice does not invent additional top-level experiences.

## 6. UX1 implementation contract for this slice

The shared operational-status primitive must:

1. accept only the established workspace states: `idle`, `loading`, `ready`, `partial`, `offline`;
2. own the human-readable label and explanation for each state;
3. remain exposed to assistive technology through `role=status` / an explicit accessible label;
4. visually distinguish connecting, healthy, partial and offline state;
5. remain visible in compact form at narrow breakpoints;
6. disable nonessential status animation under `prefers-reduced-motion`;
7. use existing AIOS semantic colors rather than introduce a new visual identity;
8. remain presentation-only and never become backend-health authority.

## 7. Acceptance boundary

This document records implementation intent and repository observations only.

Track B UX0/UX1 must not be called complete until the implemented slice has appropriate frontend tests/types/build proof and browser/product proof where material. Woodpecker remains the forward CI authority for accepted frontend proof.

Milestone L remains open independently of this work. Milestone M remains not started until the master roadmap advances it.

## 8. Next Track B slices

After this foundation lands, proceed in this order unless repository evidence changes the priority:

1. finish UX0 route/component duplication inventory and navigation simplification opportunities;
2. establish reusable truthful surface-state patterns for `loading / empty / error / blocked / authority / not-connected` where repetition is proven;
3. define a canonical employee-presence read contract before implementing Munder-derived presence/heartbeat visualization;
4. implement the first data-grounded Live Organization presence/activity visualization from that contract;
5. continue responsive/accessibility refinement of Cockpit and Live Organization;
6. defer full UX3 Board Transparency implementation until Milestone M becomes primary.
