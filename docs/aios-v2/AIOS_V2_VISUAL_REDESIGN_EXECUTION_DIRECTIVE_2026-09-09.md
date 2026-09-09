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

> **AIOS must not look AI-generated. Polished AI slop is still slop.**

This directive strengthens, and does not replace, the existing AIOS Design Constitution, Master Plan, `skills/aios-design/SKILL.md`, and truth/authority contracts.

## Anti-AI-slop acceptance rule

Visible work must feel intentionally authored and product-specific. Reject output that is merely fashionable, glossy, or technically clean but visually interchangeable with generic AI/SaaS templates.

Common rejection signatures include:

- card farms and repetitive rounded boxes as the default composition;
- generic AI purple/blue gradients, neon, glow, or glass used without product meaning;
- oversized hero sections, metrics, badges, pills, charts, and icon clusters added because they look modern rather than because they answer a user question;
- equal visual weight across unrelated sections;
- excessive labels/microcopy compensating for weak hierarchy;
- arbitrary one-off styling with no reusable AIOS system rule;
- new chrome wrapped around legacy composition;
- motion that animates boxes but does not express supported organizational state;
- generic avatars/characters with insufficient role, department, seniority, personality, or state distinction;
- HQ/3D that functions as wallpaper rather than organizational spatial memory;
- desktop layouts simply stacked into mobile;
- visual novelty that weakens readability, accessibility, provenance, authority, uncertainty, or action clarity.

A strong AIOS screen should visibly answer why it is composed this way for this user, this task, this canonical state, and this authority posture.

Every visible screenshot review must ask:

1. Could another AI/SaaS product use this screenshot by swapping the logo and copy? If yes, reject it.
2. Does the visual structure expose the user’s real mental model and current task rather than module/storage topology? If no, redesign it.
3. Does every prominent visual element do product work? If no, simplify it.
4. Are repeated patterns governed by reusable AIOS rules rather than local decoration? If no, converge them.
5. Does the result look deliberately designed by a product team rather than generated from common visual tropes? If no, continue iterating.

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

## Living Organization capability direction

The Living HQ must anticipate the persistent employee/capability model defined in `docs/aios-v2/AIOS_V2_EMPLOYEE_CAPABILITY_AND_SKILLS_ARCHITECTURE.md`.

Employees are not character skins over generic agents. The target organizational model is:

`Department → Position → Employee → Skills → Tools → Permissions → Memory → Objectives → Runtime → Work → Evidence → Outcome`

Spatial design should therefore support organization → department → employee → work → interaction/handoff → evidence/detail, with real capability/authority/work state behind what is shown. Repeated successful procedures are intended to become reusable organizational skills automatically through recurrence detection, extraction, machine validation, versioning, and reuse; automatic capability learning must never imply automatic authority escalation.

## Efficient proof ladder — same quality bar, faster iteration

The active execution method is:

`docs/aios-v2/AIOS_V2_EFFICIENT_PROOF_LADDER.md`

The program separates **development/visual iteration proof** from **final seal proof**.

### Tier A — Fast Development / Visual Gate

During active visual iteration, use the narrowest trustworthy proof for the affected surface: targeted build/type/unit checks, targeted browser routes, desktop + phone screenshots, overflow/page-error/no-write checks, relevant accessibility assertions, real visual/UX inspection, and the anti-AI-slop review above. Iterate here until the result is worth sealing.

Do **not** use Repository Policy + full V12 as the visual-design feedback loop for every CSS/composition adjustment. Full CI is not a substitute for screenshot inspection.

### Tier B — Final Seal Gate

Once Tier A is visually and functionally acceptable, normalize the candidate onto the latest actual sealed base, keep it bounded/clean, and then run the mandatory exact-head seal gates: Repository Policy, V12 Production Proof, relevant cross-route browser regression, final screenshots, final anti-AI-slop inspection, and any additional phase-specific gates.

> **Iterate narrowly; seal broadly.**

No final quality gate is removed. The efficiency gain comes from moving expensive broad proof to the normalized candidate rather than repeating it during every design adjustment. If the normalized exact head changes after final proof, the required seal gates must run again.

## Required visible acceptance gate

For any PR whose purpose includes visible UI/UX improvement, the quality sequence remains mandatory, but iteration and sealing are deliberately separated:

> **implementation → targeted browser/checks → desktop screenshots → phone screenshots → visual/UX + anti-AI-slop inspection → task walkthrough → reference/accessibility/responsive review → iterate until accepted → normalize candidate → exact-head final CI/regression → merge**

A green workflow is necessary but insufficient, and full repository CI should normally occur at the final seal stage rather than on every visual iteration.

### Required evidence

A visible-redesign PR must retain or link evidence for:

- exact candidate head SHA;
- desktop screenshot(s);
- phone screenshot(s), normally around 390 px width;
- before/after comparison or a clearly identified previous accepted screenshot;
- named visual/UX findings;
- explicit anti-AI-slop findings;
- accessibility/responsive findings;
- exact-head final CI results;
- actual merge SHA after acceptance.

If screenshots are generated in CI, upload both desktop and phone artifacts. Geometry-only phone checks are not enough for final visual acceptance.

## Rejection conditions

Reject or continue iterating when any of the following is true:

- the redesign is materially indistinguishable from the previous accepted UI;
- the page still reads as a generic SaaS/admin dashboard;
- the result looks like generic AI-generated UI or common AI-design tropes;
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

The Living HQ must also be capable of becoming a spatial capability graph: departments, reporting relationships, persistent employees, real skills, current missions, supported tools, evidence-backed work, and canonical handoffs should be inspectable at appropriate detail levels. External AI-office references may inform spatial organization, but generic neon department tiles, card farms, meaningless network lines, and decorative agent activity are not the target.

### Mobility User

Mobility should be visually calmer and less dense than Operator, case-first, reassuring, privacy-safe, mobile-first, and explicit about next step, waiting, uncertainty, user action, reviewed/confirmed outcomes, and recommendation boundaries. It must inherit the accepted V2 design language rather than reproduce legacy portal composition.

## Reference-lens rule

External references remain subordinate to AIOS authority:

`canonical truth → AIOS Design Constitution → Master Plan → this execution directive / phase specification → external reference → implementation convenience`

Use references as audit lenses, not as templates to copy. External skill ecosystems such as skills.sh are capability-discovery sources, not authority sources; see the Employee Capability & Skills Architecture for ingestion and automatic-learning direction.

## Session handoff rule

A new implementation session should read, in this order before continuing visible redesign or Living Organization work:

1. `skills/aios-design/SKILL.md`
2. `docs/aios-v2/AIOS_V2_VISUAL_REDESIGN_EXECUTION_DIRECTIVE_2026-09-09.md`
3. `docs/aios-v2/AIOS_V2_EFFICIENT_PROOF_LADDER.md`
4. `docs/aios-v2/AIOS_V2_EMPLOYEE_CAPABILITY_AND_SKILLS_ARCHITECTURE.md`
5. `docs/aios-v2/AIOS_V2_MASTER_PLAN_EXECUTION_RECONCILIATION_2026-09-08.md`
6. `docs/aios-v2/AIOS_V2_MIGRATION_AND_FINAL_ACCEPTANCE_CHECKLIST.md`
7. the relevant product/phase specification and reference-adoption ledger.

A new session must default to **Tier A targeted iteration while actively designing/correcting a bounded slice**, apply the **anti-AI-slop gate during screenshot review**, and promote to **Tier B exact-head seal proof only when the focused browser/screenshots are acceptable enough to justify final CI**.

For AI employee, department, Living HQ, skills, tool/integration, memory, work-routing, automation, or cross-department work, the Employee Capability & Skills Architecture is mandatory context. New sessions must not reduce the automatic organizational-learning requirement back to a manual approval workflow.

If any older roadmap text says to finish broad Mobility migration before visual convergence, this directive takes precedence for execution sequencing while preserving all higher truth/authority rules.

## Completion boundary

The redesign is not visually complete because routes migrated, tests passed, or a V2 shell exists. Visual completion requires demonstrated material improvement in real browser screenshots across desktop and phone, accepted UX behavior, explicit anti-AI-slop acceptance, reusable design-system convergence, and preserved truth/authority semantics.