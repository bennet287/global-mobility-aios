# Global Mobility AIOS — Roadmap V12.26 Frontend Design Addendum

**Date:** 2026-08-22
**Status:** DESIGN-DIRECTION RECORD / SCHEDULING SUPERSEDED BY V12.27 MASTER ROADMAP
**Master scheduling authority:** `ROADMAP.md`
**Runtime acceptance baseline:** K.1 COMPLETE / PASS / SEALED
**Current product milestone:** L — Live Organization
**Canonical UX detail:** `AIOS_FRONTEND_DESIGN_UX_PROGRAMME_V1.md`

This addendum records why frontend product design became a first-class workstream during L/M planning.

Its original independent `NOW / DURING L / WITH M` scheduling language is superseded by the necessity-driven V12.27 master roadmap. It remains useful as design-history/context, but it no longer schedules work.

---

## 1. Preserved design direction

Frontend product design must begin early enough to shape real interactions rather than being applied only after backend completion.

The intended capability progression remains conceptually useful:

```text
UX0 experience / information-architecture audit
→ bounded UX1 design-system foundation
→ UX2 Live Organization design against real L contracts
→ UX3 Cockpit + Board Transparency design/implementation with M
→ UX4 Operations + My Mobility convergence
→ UX5 Living Organization visualization where proven useful
```

`ROADMAP.md` determines which of these slices is PRIMARY, REQUIRED ENABLEMENT, SUPPORTING PARALLEL or deferred at any given time.

---

## 2. Tooling posture correction

Penpot remains the preferred current open-source design environment, but is replaceable and is not product authority.

Storybook remains a candidate implemented-component workbench subject to bounded repository/adoption proof.

Next.js/React remains production frontend authority until explicitly changed through the necessity-driven decision process.

Generated design code is never automatically production code.

---

## 3. Munder Difflin relationship

Munder Difflin remains a strategic donor, not a competing roadmap.

Potentially useful concepts include:

- presence/heartbeat;
- live scene/event synchronization;
- collaboration grouping;
- transcripts;
- tool signals;
- runtime-driven animation;
- token/cost telemetry.

Rejected assumptions remain:

- pixel-art/game-like target presentation;
- GOD metaphor;
- donor state as canonical authority;
- direct donor mutation of authoritative AIOS state;
- decorative activity that implies work not present in canonical state.

Any donor adoption is activated only by a demonstrated product/UX gap identified through the master roadmap.

---

## 4. Acceptance rule

Frontend acceptance remains capability/evidence based:

```text
real canonical/read-write contract
→ designed interaction
→ reusable implementation where justified
→ accessibility/responsive/state verification
→ browser E2E where interaction is material
→ frontend tests/types/build
→ repository policy
→ Woodpecker proof
→ documentation reconciliation
```

No design mock may be presented as real Live Organization state.

No design tool or component workbench is accepted merely because it is named in a roadmap document.

---

## 5. Current authority

For current scheduling and priority, use:

```text
docs/ROADMAP.md
```

For detailed UX capability/design rules, use:

```text
docs/AIOS_FRONTEND_DESIGN_UX_PROGRAMME_V1.md
```

For donor-specific rules, use:

```text
docs/MUNDER_DIFFLIN_AIOS_ADOPTION_V1.md
```

This document should not be used as an independent implementation chronology.
