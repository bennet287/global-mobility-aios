# AIOS V2 Migration and Final Acceptance Checklist

**Baseline date:** 2026-09-10
**Current sealed redesign base:** `e3fd0b162bff3ab725f402fedbbb0b5ce8efe7ff` (actual merge SHA of PR #135)
**Accepted Living HQ Phase 13G.1H visual/live-behavior head:** `8b92aa09d81f21808492b0bab4178c1ca9ebad3e` (Owner acceptance recorded on PR #147 after Browser Proof #111 desktop + phone inspection)

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

Active execution authorities:

- `docs/aios-v2/AIOS_V2_VISUAL_REDESIGN_EXECUTION_DIRECTIVE_2026-09-09.md`
- `docs/aios-v2/AIOS_V2_EFFICIENT_PROOF_LADDER.md`

Execution method: **Tier A targeted iteration → visual/UX acceptance → normalized candidate → Tier B exact-head seal proof**. Full Repository Policy + V12 are final seal gates, not the default feedback loop for every visual adjustment. No final quality gate is removed.

- [ ] establish material before/after visual improvement, not only V2 shell wrapping
- [ ] reject generic SaaS/admin-dashboard composition
- [ ] converge typography scale, density, hierarchy and rhythm
- [ ] replace generic card-grid thinking with AIOS-native product composition where appropriate
- [ ] consolidate recurring motion durations/easings into V2 motion tokens
- [ ] consolidate recurring shadows/elevation/material values into shared tokens/primitives
- [ ] converge radius, spacing and typography values where recurring
- [ ] verify reusable component contracts for hover/focus/pressed/selected/disabled/loading/empty/unavailable/error states
- [ ] Operator visual transformation accepted as first proving ground
- [x] Owner/Living HQ flagship visual review accepted — 13G.1H Owner acceptance on exact head `8b92aa09d81f21808492b0bab4178c1ca9ebad3e`
- [x] character system visibly communicates role/state/personality beyond labels — accepted Living HQ miniature workforce direction
- [x] modern HQ architecture visibly supports organizational/spatial memory — accepted continuous-office world direction
- [x] ambient and semantic motion feel alive without violating truth contracts — canonical-only live behavior + presentation-only ambient life accepted
- [ ] inspect responsive composition on desktop/tablet/phone
- [x] verify mobile is recomposed, not scaled desktop — Browser Proof #111 phone accepted
- [x] save and inspect desktop + phone screenshots for each major visible slice — final 13G.1H proof inspected and accepted
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
- [x] re-run Q17 performance profile after convergence — exact accepted head profiled by V12 #1906
- [x] re-run Q18 asset profile after convergence — exact accepted head profiled by V12 #1906

### Living HQ Phase 13G closure record

- [x] 13G.1A continuous architectural world accepted
- [x] 13G.1B distinct workplace interiors accepted
- [x] 13G.1C integrated miniature workforce direction accepted
- [x] 13G.1D canonical real-time scene binding proven without page reload
- [x] 13G.1E canonical event reactions remain record-driven only
- [x] 13G.1F safe ambient life/cinematic depth accepted without fabricated organizational facts
- [x] 13G.1G dedicated phone composition accepted
- [x] 13G.1H explicit Owner visual + live-behavior acceptance recorded on PR #147
- [x] Repository Policy #1276 PASS on accepted 13G.1H head
- [x] Living HQ Browser Proof #111 PASS on accepted 13G.1H head
- [x] V12 Production Proof #1906 PASS on accepted 13G.1H head
- [x] Q17 and Q18 artifacts produced by V12 #1906 on accepted 13G.1H head
- [ ] 13G.2 companion-spec reconciliation committed on a new exact candidate head
- [ ] 13G.2 exact-head Repository Policy + Living HQ Browser Proof + V12 final seal PASS
- [ ] PR #147 promoted from Draft only after the exact 13G.2 candidate is accepted
- [ ] actual Phase 13G merge SHA/tree/parents/signature recorded after merge

The accepted Living HQ boundary remains one-way and presentation-only: canonical organization state may drive visible state; animation, spatial selection, room/character placement, ambient motion, or HUD interaction may not create canonical work, evidence, decisions, authority, physical presence, occupancy, availability, handoffs, conversations, or Board action.

## Phase 11 — Mobility User migration

Primary navigation target: **Overview · My Case · Documents · Timeline · Messages**.

Phase 11A navigation foundation was sealed at actual merge SHA `5259892dbf1fa1e9cdff238deb0492d4e846eaa2`. Visual Redesign Convergence then established the presentation language used by the accepted Overview, My Case and Documents surfaces through PR #131; Timeline was accepted and merged in PR #135 at `e3fd0b162bff3ab725f402fedbbb0b5ce8efe7ff`. Messages desktop and phone visible-review artifacts were inspected on exact normalized candidate `d765914244bff4d13e5eb7477252df6b6fd1da14` after all targeted Mobility browser proofs and V12 passed; this checklist update becomes part of the final Messages candidate and therefore requires a fresh exact-head seal before merge.

- [x] Phase 11A five-domain navigation foundation sealed
- [x] Mobility shell built on accepted converged V2 visual language
- [x] Overview migrated
- [x] My Case secure portal integration accepted
- [x] Documents client-safe surface accepted
- [x] Timeline accepted
- [x] Messages accepted
- [ ] internal governance terminology does not leak unless needed for transparency
- [ ] recommendations remain visibly distinct from official/human-authoritative outcomes
- [ ] document/evidence status remains truthful without unnecessary internals
- [x] mobile-first composition reviewed as a distinct mode, not scaled desktop
- [ ] task completion, next action, uncertainty and waiting states are explicit
- [x] privacy-safe information presentation accepted
- [ ] keyboard/touch/screen-reader/reduced-motion acceptance
- [x] saved desktop + phone screenshots and task walkthrough accepted before merge

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

> **implementation → Tier A targeted checks/browser → desktop screenshots → phone screenshots → visual inspection → UX/reference/accessibility review → iterate → normalize candidate → Tier B exact-head final CI/regression → merge**

A green build or Playwright run cannot by itself close a visible redesign phase. Conversely, full repository CI should not be repeatedly used merely to iterate on visual composition; it belongs at the normalized final-seal boundary unless a governing phase explicitly requires otherwise.

## Completion law

AIOS V2 is not complete because the Owner UI looks finished, routes migrated, shells exist, or one CI run is green. Completion requires explicit visible redesign acceptance, Mobility completion on the converged system, whole-product hardening, legacy retirement, and final acceptance.
