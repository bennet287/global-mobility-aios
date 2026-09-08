# AIOS V2 Migration and Final Acceptance Checklist

**Baseline date:** 2026-09-08
**Sealed redesign base:** `d031e0d12feac0e82faafdf2efa66b51ba56212e` (actual merge SHA of PR #100)

This checklist prevents Owner/Living Organization completion from being mistaken for whole-product V2 completion.

## Phase 10 — Professional / Operator migration

Primary navigation target: **Work · Profiles · Pathways · Evidence · Communication · Tools**.

- [ ] `/` → Operator Work V2
- [ ] `/profiles` → Profiles V2
- [ ] `/eligibility` → Work / Eligibility
- [ ] `/planning` → Work / Planning
- [ ] `/pathways` → Pathways V2
- [ ] `/timelines` → Work / Timeline
- [ ] `/communications` → Communication V2
- [ ] `/coaching` → Tools / Agent Coaching
- [ ] `/corporate-mobility` → Tools / Corporate
- [ ] `/business-advisory` → Tools / Advisory
- [ ] `/investment-mobility` and `/investment-suitability` → audited Tools / Investment model
- [ ] `/family-office` → Tools / Family Office
- [ ] `/tax-residency` → Tools / Tax
- [ ] authority/submission/agency workflows contextualized under Work / Authority
- [ ] deep links preserved or explicitly redirected
- [ ] long-content, partial, unavailable, loading and error states reviewed
- [ ] keyboard, touch, screen reader, 200% zoom/reflow and reduced-motion acceptance
- [ ] Operator browser screenshots and task walkthrough accepted before merge

## Phase 11 — Mobility User migration

Primary navigation target: **Overview · My Case · Documents · Timeline · Messages**.

- [ ] internal governance terminology does not leak unless needed for transparency
- [ ] recommendations remain visibly distinct from official/human-authoritative outcomes
- [ ] document/evidence status remains truthful without unnecessary internals
- [ ] mobile-first composition reviewed as a distinct mode, not scaled desktop
- [ ] task completion, next action, uncertainty and waiting states are explicit
- [ ] keyboard/touch/screen-reader/reduced-motion acceptance
- [ ] real browser screenshots and task walkthrough accepted before merge

## Whole-system convergence / hardening

- [ ] consolidate recurring local motion durations/easings into V2 motion tokens
- [ ] consolidate recurring shadows/elevation/material values into shared tokens/primitives
- [ ] audit PR #91–#100 CSS modules for reusable patterns vs one-off drift
- [ ] verify reusable component contracts for hover/focus/pressed/selected/disabled/loading/empty/unavailable/error states
- [ ] inspect responsive composition on desktop/tablet/phone
- [ ] verify 200% zoom/reflow
- [ ] verify forced-colors/high-contrast behavior where applicable
- [ ] verify reduced motion across semantic and presentation-only motion
- [ ] verify structured non-3D equivalents for essential spatial information
- [ ] re-run Q15 visual contracts and inspect intentional deltas
- [ ] re-run Q17 performance profile
- [ ] re-run Q18 asset profile
- [ ] perform Refactoring UI / UX Heuristics / Taste / Impeccable whole-product review
- [ ] resolve Driver.js vs custom guided-experience decision; do not install competing tour engines
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
- [ ] Operator usability review PASS
- [ ] Mobility usability review PASS
- [ ] legacy-retirement proof PASS
- [ ] release notes and migration notes complete
- [ ] actual final merge SHA recorded

## Completion law

AIOS V2 is not complete because the Owner UI looks finished or because one CI run is green. Completion requires explicit closure of Operator migration, Mobility migration, convergence/hardening, legacy retirement, and final acceptance.
