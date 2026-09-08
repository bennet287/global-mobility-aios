# AIOS V2 Visual Redesign Execution Directive — 2026-09-09

**Status:** ACTIVE EXECUTION DIRECTIVE
**Program branch:** `design/aios-v2-complete-redesign`
**Applies after:** sealed Phase 11A / PR #111

## Why this directive exists

The Phase 10 Operator browser screenshots proved that structural migration, route correctness, accessibility contracts, and green CI do **not** by themselves constitute a successful visual redesign.

Several Operator V2 slices correctly preserved truth, authority, routing, and governed behavior, but the visible result remained too close to the legacy/generic administrative-dashboard language. This is now an explicit program finding, not a subjective afterthought.

The program must therefore stop treating "migrated into a V2 shell" as equivalent to "visually redesigned".

## Permanent visible-redesign law

> **Old content inside a V2 shell is not a completed redesign.**

> **If a screenshot says generic SaaS/admin dashboard before it says AIOS, the visual slice is rejected even if build, tests, and CI are green.**

> **A claimed visible redesign must produce a material before/after improvement in hierarchy, composition, product identity, interaction model, motion/presence, and responsive experience without weakening canonical truth.**

This directive strengthens, and does not replace, the existing AIOS Design Constitution, Master Plan, `skills/aios-design/SKILL.md`, and truth/authority contracts.

## Revised critical path

The previous order of "finish Mobility first, then converge visually" is superseded.

Use this order:

1. Phase 11A Mobility navigation foundation is sealed; pause further broad Mobility feature migration;
2. run **Visual Redesign Convergence** on the real product using the accepted design-system hierarchy;
3. use Operator as the first proving ground because its six accepted routes already expose the current visual weakness clearly;
4. review and strengthen Owner/Living HQ flagship presentation so characters, architecture, spatial composition, motion, atmosphere, and organizational life visibly deliver the intended AIOS identity;
5. produce and inspect both desktop and phone screenshots for each major visible slice;
6. apply the formal reference lenses: Refactoring UI, UX Heuristics, Taste, Impeccable, plus the subordinate anti-generic/creative execution guidance already recorded in the reference ledger;
7. seal reusable visual foundations/tokens/components/patterns only after real browser proof;
8. resume Mobility implementation on top of the accepted visual language rather than repeating migration-bridge styling;
9. complete whole-product convergence, legacy retirement, and final acceptance.

## Visual Redesign Convergence scope

The convergence pass must address at least:

- typography scale, hierarchy, density, and readable rhythm;
- layout/composition beyond generic card grids;
- AIOS-native product objects instead of generic dashboard vocabulary;
- surfaces, materials, borders, elevation, depth, and restrained atmosphere;
- iconography and visual identity;
- navigation composition and role distinction;
- empty/loading/unavailable/error states;
- hover/focus/pressed/selected/disabled states;
- micro-interactions and motion language;
- responsive recomposition rather than desktop shrinking;
- phone-first touch geometry and visual hierarchy;
- reduced-motion equivalents;
- high-contrast/forced-colors behavior where applicable;
- Operator dense-work usability;
- Owner/Living Organization flagship distinctiveness;
- Living HQ character/architecture/spatial integration;
- removal of visible migration scaffolding where it no longer serves the user;
- elimination of duplicate shell/topbar/theme controls or other layering artifacts;
- tokenization of recurring motion, shadow, elevation, material, radius, spacing, and typography values.

## Required visible acceptance gate

For any PR whose purpose includes visible UI/UX improvement, acceptance order is mandatory:

> **implementation → production browser → desktop screenshots → phone screenshots → visual inspection → task/UX walkthrough → reference-lens review → accessibility/responsive review → automated tests → exact-head CI → merge**

A green workflow is necessary but insufficient.

### Required evidence

A visible-redesign PR must retain or link evidence for:

- exact candidate head SHA;
- desktop screenshot(s);
- phone screenshot(s), normally around 390 px width;
- before/after comparison or a clearly identified previous accepted screenshot;
- named visual/UX findings;
- accessibility/responsive findings;
- exact-head CI results;
- actual merge SHA after acceptance.

If screenshots are generated in CI, upload both desktop and phone artifacts. Geometry-only phone checks are not enough for final visual acceptance.

## Rejection conditions

Reject or continue iterating when any of the following is true:

- the redesign is materially indistinguishable from the previous accepted UI;
- the page still reads as a generic SaaS/admin dashboard;
- legacy page composition is merely wrapped in new chrome;
- visual hierarchy does not communicate the user's current goal/state;
- mobile is only a compressed desktop layout;
- animation is decorative but the product still feels static/generic;
- characters or HQ are present but read as ornaments rather than organizational interaction systems;
- visual polish obscures provenance, authority, uncertainty, or canonical state;
- screenshot inspection has not happened;
- only automated tests were used to claim visible completion.

## Product-specific direction

### Professional / Operator

Operator should feel like a premium professional control environment, not a generic admin dashboard. It should emphasize current operational picture, workstream relationships, governed actions, evidence/authority state, contextual specialist tools, and dense-but-calm information hierarchy.

### Owner / Living Organization

Owner is the flagship AIOS identity surface. It should visibly express a living digital company through original miniature professional characters, modern HQ architecture, organizational spatial memory, semantically governed collaboration/handoffs/escalations, ambient life, depth, lighting, and atmosphere while preserving structured equivalents and truth boundaries.

### Mobility User

Mobility should be visually calmer and less dense than Operator, case-first, reassuring, privacy-safe, mobile-first, and explicit about next step, waiting, uncertainty, user action, reviewed/confirmed outcomes, and recommendation boundaries. It must inherit the accepted V2 design language rather than reproduce legacy portal composition.

## Reference-lens rule

External references remain subordinate to AIOS authority:

`canonical truth → AIOS Design Constitution → Master Plan → this execution directive / phase specification → external reference → implementation convenience`

Use references as audit lenses, not as templates to copy.

## Session handoff rule

A new implementation session should read, in this order before continuing visible redesign work:

1. `skills/aios-design/SKILL.md`
2. `docs/aios-v2/AIOS_V2_VISUAL_REDESIGN_EXECUTION_DIRECTIVE_2026-09-09.md`
3. `docs/aios-v2/AIOS_V2_MASTER_PLAN_EXECUTION_RECONCILIATION_2026-09-08.md`
4. `docs/aios-v2/AIOS_V2_MIGRATION_AND_FINAL_ACCEPTANCE_CHECKLIST.md`
5. the relevant product/phase specification and reference-adoption ledger.

If any older roadmap text says to finish broad Mobility migration before visual convergence, this directive takes precedence for execution sequencing while preserving all higher truth/authority rules.

## Completion boundary

The redesign is not visually complete because routes migrated, tests passed, or a V2 shell exists. Visual completion requires demonstrated material improvement in real browser screenshots across desktop and phone, accepted UX behavior, reusable design-system convergence, and preserved truth/authority semantics.
