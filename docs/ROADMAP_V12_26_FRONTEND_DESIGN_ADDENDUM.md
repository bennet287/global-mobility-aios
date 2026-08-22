# Global Mobility AIOS — Roadmap V12.26 Frontend Design Addendum

**Date:** 2026-08-22
**Status:** ACTIVE ROADMAP ADDENDUM / DOCUMENTATION DIRECTION
**Parent roadmap:** `ROADMAP.md` V12.25
**Runtime acceptance baseline:** K.1 COMPLETE / PASS / SEALED
**Current product milestone:** L — Live Organization

This addendum closes a roadmap gap: frontend product design and UX were represented mainly as product surfaces and the later M Board Transparency milestone, but were not scheduled as a first-class design programme with explicit design sprints.

It does not reorder the accepted runtime sequence. It adds a parallel UX track that starts now and converges with L/M.

## Roadmap correction

```text
Product/runtime
  L Live Organization
  → M Board Transparency Experience
  → N Learning & Optimization

Frontend product design
  UX0 Experience audit + information architecture        NOW
  → UX1 AIOS Design System foundation                    DURING L
  → UX2 Live Organization co-design                      WITH L
  → UX3 Cockpit + Board Transparency design/implementation WITH M
  → UX4 Operations + My Mobility convergence
  → UX5 Living Organization visualization

Enterprise integration
  E1 observability / backup / secrets
  → E2 identity / communications
  → E3 e-signature / governed communications
  → E4 ERP/accounting/payments demand gated

Strategic donor
  Munder Difflin v0.4.4 controlled adoption
  → presence/runtime/event mechanics where useful
  → M17/M18 Living Organization mechanics only behind AIOS truth/design boundaries
```

## Design tooling direction

- Penpot is the preferred open-source design environment.
- Start cloud-first to avoid infrastructure distraction; retain self-hosting as a future option.
- AIOS owns design tokens, information architecture and visual identity.
- Storybook is the preferred implemented-component workbench direction, subject to a bounded dependency/repository audit before adoption.
- Next.js/React remains production frontend authority.
- Generated design code is never automatically production code.

Canonical detail: `docs/AIOS_FRONTEND_DESIGN_UX_PROGRAMME_V1.md`.

## Munder Difflin correction

Munder Difflin is not merely a historical donor label. Its controlled-adoption programme must remain visible during L/M planning.

For frontend/runtime work, explicitly evaluate its presence/heartbeat, live scene/event synchronization, collaboration grouping, transcripts, tool signals and runtime-driven animation. Do not inherit its pixel-art/game-like presentation, GOD metaphor or donor state authority.

Canonical donor record: `docs/MUNDER_DIFFLIN_AIOS_ADOPTION_V1.md`.

## Acceptance rule

This addendum is documentation direction only. It does not claim Penpot, Storybook or any Munder-derived frontend mechanism is production adopted.

Frontend acceptance remains:

```text
real canonical/read-model contract
→ designed interaction
→ reusable implementation
→ accessibility/responsive/state verification
→ frontend tests/types/build
→ repository policy
→ Woodpecker proof
→ documentation reconciliation
```

No design mock may be presented as real Live Organization state.