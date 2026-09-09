# AIOS V2 Efficient Proof Ladder

**Status:** ACTIVE EXECUTION METHOD
**Effective:** 2026-09-09
**Applies to:** AIOS V2 visible redesign and other bounded implementation slices where repeated full CI would slow iteration without adding useful signal.

## Purpose

AIOS keeps the same quality bar while moving expensive proof to the point where it is most informative.

The program must not use full repository CI as the visual-design iteration engine. A candidate should first become good through focused implementation, focused browser proof, real screenshot inspection, and correction. Full exact-head proof is then used once the candidate is clean and visually accepted enough to seal.

This method changes **when** proof runs, not **what must ultimately pass**.

## Permanent efficiency law

> **Iterate narrowly; seal broadly.**

> **Do not spend full CI to discover a problem that a targeted browser run or screenshot review could have found first.**

> **No final quality gate is removed. Expensive repository-wide proof moves to the normalized merge candidate.**

The Visual Redesign Execution Directive remains authoritative for what counts as an acceptable visible redesign.

## Anti-AI-slop quality gate

Fast iteration must not become fast generic output. Every visible Tier A review must explicitly reject **AI slop**: interfaces that look plausibly polished but feel automatically assembled, interchangeable, over-decorated, under-authored, or disconnected from the product's actual mental model.

Reject a candidate when it shows one or more of these signatures:

- generic card-grid/dashboard composition with no AIOS-native information architecture;
- repetitive rounded rectangles, pills, gradients, glow, glass, or oversized hero blocks used as default styling rather than serving hierarchy;
- decorative metrics, charts, labels, icons, or motion that do not answer a user question or communicate canonical state;
- generic "AI product" purple/blue/neon aesthetics or copy that could belong to any SaaS product;
- excessive microcopy, section labels, badges, or explanatory text compensating for weak composition;
- every section receiving equal visual weight, producing template-like rhythm rather than deliberate hierarchy;
- arbitrary visual novelty without a reusable system rule;
- duplicated navigation, headers, controls, cards, or status indicators caused by wrapping legacy UI in new chrome;
- animations that merely make static boxes move instead of expressing supported organizational state;
- stock-avatar or generic-character treatment that fails to communicate role, department, seniority, personality, or state;
- architecture/3D used as wallpaper rather than as spatial memory and organizational interaction;
- mobile layouts that simply stack desktop cards vertically;
- visually impressive output that weakens readability, accessibility, provenance, authority, uncertainty, or action clarity.

A visible candidate should instead demonstrate authored intent: a clear primary question, purposeful hierarchy, AIOS-native product objects, restrained materials, meaningful spatial relationships, disciplined motion, distinctive role-specific composition, and obvious reasons for each major visual decision.

During Tier A screenshot review ask:

1. Could this screenshot plausibly be a generic AI dashboard template with the logo swapped? If yes, reject it.
2. Does the composition visibly reflect the user's role, current task, canonical state, and authority posture? If no, continue iterating.
3. Is every prominent visual element doing product work rather than merely adding polish? If no, simplify or redesign it.
4. Are repeated patterns governed by reusable AIOS rules rather than local styling improvisation? If no, converge the system.
5. Does desktop and phone each feel intentionally composed? If no, do not promote to Tier B.

## Two-tier proof system

### Tier A — Fast Development / Visual Gate

Use during active iteration. Scope proof to the surface and contracts actually being changed.

Normally include:

- affected route(s) or component(s) only;
- targeted TypeScript/build/lint/unit checks where relevant;
- targeted Playwright/browser proof;
- desktop screenshot(s);
- 390px phone screenshot(s) for visible responsive work;
- overflow/bounds checks;
- page-error checks;
- forbidden-write / mutation-boundary checks where applicable;
- targeted keyboard/touch/accessibility assertions relevant to the slice;
- reduced-motion behavior when the slice changes motion;
- human visual inspection and UX walkthrough;
- explicit anti-AI-slop review using the criteria above;
- comparison against the previous accepted screenshot/state.

Tier A may run locally or in a narrowly scoped workflow. It does **not** require Repository Policy + full V12 on every design adjustment.

If Tier A exposes a visual, UX, accessibility, truth, authority, responsive, browser, or anti-slop defect, fix it and repeat Tier A. Do not promote the candidate merely because an earlier broad CI run happened to be green.

### Tier B — Final Seal Gate

Run only after the slice has converged and the candidate has been normalized onto the current sealed base.

Required final proof remains:

- clean/reviewable normalized candidate, normally one bounded commit;
- exact candidate SHA recorded;
- Repository Policy PASS on that exact head;
- V12 Production Proof PASS on that exact head;
- relevant cross-route/browser regression PASS;
- final desktop + phone screenshot artifact for visible work;
- final visual/UX and anti-AI-slop inspection;
- accessibility/responsive checks required by the slice;
- truth/authority/mutation contracts preserved;
- actual merge SHA recorded after merge.

Where a phase has additional mandatory gates such as Q15, Q17, Q18, SQLite, PostgreSQL, full E2E, or product-specific proof, those remain required at the phase/final boundary defined by the governing plan. This ladder does not waive them.

## Required execution order

For visible redesign work use:

`implement → targeted checks → targeted browser → desktop + phone screenshots → visual/UX + anti-slop inspection → iterate as needed → normalize candidate → final targeted regression → exact-head Repository Policy + V12 → merge`

For a shared-foundation change, the final targeted regression should cover all affected routes. For a route-specific change, iteration may stay route-specific; broaden only when the candidate is ready to seal or when shared code creates credible cross-route risk.

## CI trigger discipline

During iteration:

- prefer local or narrowly scoped tests;
- avoid pushing cosmetic micro-adjustments solely to obtain full V12 feedback;
- batch related visual corrections before promoting a new seal candidate;
- use screenshots as first-class evidence, not decoration;
- do not rerun broad suites when the changed dimension cannot affect them unless a governing gate explicitly requires it.

At sealing:

- normalize onto the latest actual sealed merge SHA;
- ensure the PR is clean and bounded;
- run the mandatory exact-head gates once on that normalized candidate;
- if the exact head changes afterward, its required seal gates must be rerun.

## Failure handling

A failure should be handled at the narrowest trustworthy level:

- visual/composition/AI-slop failure → redesign and rerun targeted browser/screenshots;
- route/browser regression → rerun affected browser proof;
- focused unit/type failure → rerun focused test after correction;
- infrastructure flake → retry the failed proof when evidence supports flakiness;
- semantic/governance failure → fix the contract; never weaken the test merely to get green;
- final exact-head failure → candidate is not sealable until the required final gate passes.

## Quality-bar invariants

This efficiency method must never be used to:

- skip screenshot inspection for visible redesign;
- merge a materially generic, AI-slop, or broken UI because tests are green;
- bypass truth or authority review;
- remove accessibility/responsive acceptance;
- avoid reduced-motion or structured-fallback obligations;
- merge without exact-head final proof required by the current phase;
- treat a development-only targeted run as final production acceptance;
- weaken tests to reduce runtime.

## Session handoff rule

A new session working on AIOS V2 must understand the distinction:

- **Tier A is the fast iteration loop.**
- **Tier B is the final merge/seal proof.**
- **Anti-AI-slop review is mandatory in both.**

Default to Tier A while actively designing or correcting a bounded slice. Promote to Tier B only when screenshots and focused checks indicate that the candidate is worth sealing and the result is visibly authored, role-specific, and recognizably AIOS rather than generically "AI-designed."

This is the standard execution method until superseded by a later repository-level directive.