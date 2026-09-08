# AIOS V2 Migration and Final Acceptance Checklist

**Baseline date:** 2026-09-08
**Current sealed redesign base:** `5259892dbf1fa1e9cdff238deb0492d4e846eaa2` (actual merge SHA of PR #111)

This checklist prevents structural migration or green CI from being mistaken for whole-product V2 completion.

## Phase 10 — Professional / Operator migration

Primary navigation target: **Work · Profiles · Pathways · Evidence · Communication · Tools**.

- [x] six-domain Operator navigation model established
- [x] Work V2 shell migration
- [x] Profiles V2 bridge
- [x] Pathways V2 bridge
- [x] Evidence V2 bridge
- [x] Communication V2 bridge
- [x] Tools V2 workspace
- [x] targeted Operator browser proof across desktop and phone geometry
- [x] no-write/fail-closed browser fixture proof
- [ ] visual redesign convergence of all six primary Operator routes
- [ ] remove visible migration scaffolding where no longer user-serving
- [ ] inspect duplicate shell/topbar/theme-control layering and correct if present
- [ ] deep links preserved or explicitly redirected
- [ ] long-content, partial, unavailable, loading and error states visually reviewed
- [ ] keyboard, touch, screen reader, 200% zoom/reflow and reduced-motion acceptance after visual convergence
- [ ] saved desktop **and phone** Operator screenshots visually accepted before final Operator closure

## Visual Redesign Convergence — MUST PRECEDE BROAD MOBILITY MIGRATION

Active execution authority:

`docs/aios-v2/AIOS_V2_VISUAL_REDESIGN_EXECUTION_DIRECTIVE_2026-09-09.md`

- [ ] establish material before/after visual improvement, not only V2 shell wrapping
- [ ] reject generic SaaS/admin-dashboard composition
- [ ] converge typography scale, density, hierarchy and rhythm
- [ ] replace generic card-grid thinking with AIOS-native product composition where appropriate
- [ ] consolidate recurring motion durations/easings into V2 motion tokens
- [ ] consolidate recurring shadows/elevation/material values into shared tokens/primitives
- [ ] converge radius, spacing and typography values where recurring
- [ ] verify reusable component contracts for hover/focus/pressed/selected/disabled/loading/empty/unavailable/error states
- [ ] Operator visual transformation accepted as first proving ground
- [ ] Owner/Living HQ flagship visual review accepted
- [ ] character system visibly communicates role/state/personality beyond labels
- [ ] modern HQ architecture visibly supports organizational/spatial memory
- [ ] ambient and semantic motion feel alive without violating truth contracts
- [ ] inspect responsive composition on desktop/tablet/phone
- [ ] verify mobile is recomposed, not scaled desktop
- [ ] save and inspect desktop + phone screenshots for each major visible slice
- [ ] verify 200% zoom/reflow
- [ ] verify forced-colors/high-contrast behavior where applicable
- [ ] verify reduced motion across semantic and presentation-only motion
- [ ] verify structured non-3D equivalents for essential spatial information
- [ ] perform Refactoring UI whole-product lens
- [ ] perform UX Heuristics whole-product lens
- [ ] perform Taste anti-template lens
- [ ] perform Impeccable late-polish lens
- [ ] resolve Driver.js vs custom guided-experience decision; do not install competing tour engines
- [ ] re-run Q15 visual contracts and inspect intentional deltas
- [ ] re-run Q17 performance profile after convergence
- [ ] re-run Q18 asset profile after convergence

## Phase 11 — Mobility User migration

Primary navigation target: **Overview · My Case · Documents · Timeline · Messages**.

Phase 11A navigation foundation is sealed at actual merge SHA `5259892dbf1fa1e9cdff238deb0492d4e846eaa2`, but **broad Mobility implementation resumes only after Visual Redesign Convergence is accepted**.

- [x] Phase 11A five-domain navigation foundation sealed
- [ ] Mobility shell built on accepted converged V2 visual language
- [ ] Overview migrated
- [ ] My Case secure portal integration accepted
- [ ] Documents client-safe surface accepted
- [ ] Timeline accepted
- [ ] Messages accepted
- [ ] internal governance terminology does not leak unless needed for transparency
- [ ] recommendations remain visibly distinct from official/human-authoritative outcomes
- [ ] document/evidence status remains truthful without unnecessary internals
- [ ] mobile-first composition reviewed as a distinct mode, not scaled desktop
- [ ] task completion, next action, uncertainty and waiting states are explicit
- [ ] privacy-safe information presentation accepted
- [ ] keyboard/touch/screen-reader/reduced-motion acceptance
- [ ] saved desktop + phone screenshots and task walkthrough accepted before merge

## Whole-system convergence / hardening

- [ ] audit late V2 CSS modules for reusable patterns vs one-off drift
- [ ] verify visual consistency across Owner, Operator and Mobility
- [ ] verify route/deep-link matrix
- [ ] verify desktop/tablet/phone composition
- [ ] verify 200% zoom/reflow
- [ ] verify forced-colors/high-contrast behavior where applicable
- [ ] verify reduced motion and structured fallbacks
- [ ] final Q15 visual regression review
- [ ] final Q17 performance profile
- [ ] final Q18 asset profile
- [ ] synchronize canonical Master Plan Markdown + DOCX in one reviewed commit

## Phase 13 — Legacy retirement

Do not delete legacy surfaces until replacement coverage is proven.

- [ ] complete route migration matrix with `keep / alias / redirect / contextualize / retire`
- [ ] preserve required deep links and workflow capability
- [ ] remove legacy command/search entries only after replacements exist
- [ ] remove dead components after reference search proves no consumers
- [ ] remove legacy CSS only after selectors have no references
- [ ] remove unused assets only after build/browser verification
- [ ] clean navigation aliases and stale docs
- [ ] measure CSS/bundle change after retirement

## Phase 14 — Final AIOS V2 acceptance

- [ ] Repository Policy PASS on exact final head
- [ ] SQLite regression PASS
- [ ] PostgreSQL governance PASS
- [ ] frontend tests/types/build PASS
- [ ] full V2 browser E2E PASS
- [ ] Q15 visual regression PASS with reviewed baselines
- [ ] Q17 performance PASS / accepted profile
- [ ] Q18 asset optimization PASS / accepted profile
- [ ] accessibility acceptance PASS
- [ ] responsive/mobile acceptance PASS
- [ ] reduced-motion and structured-fallback acceptance PASS
- [ ] design-system conformity audit PASS
- [ ] truth/governance review PASS
- [ ] Operator usability + visual review PASS
- [ ] Mobility usability + visual review PASS
- [ ] Owner/Living HQ flagship visual review PASS
- [ ] legacy-retirement proof PASS
- [ ] release notes and migration notes complete
- [ ] actual final merge SHA recorded

## Visible acceptance law

For visible UI/UX phases:

> **implementation → production browser → desktop screenshots → phone screenshots → visual inspection → UX walkthrough → reference-lens review → accessibility/responsive review → automated tests → exact-head CI → merge**

A green build or Playwright run cannot by itself close a visible redesign phase.

## Completion law

AIOS V2 is not complete because the Owner UI looks finished, routes migrated, shells exist, or one CI run is green. Completion requires explicit visible redesign acceptance, Mobility completion on the converged system, whole-product hardening, legacy retirement, and final acceptance.
