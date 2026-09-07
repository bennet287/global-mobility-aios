# AIOS V2 — Q13 Structured Fallback & Renderer Independence

## Status

Implementation candidate. Acceptance requires exact-head static, browser and repository proof before merge.

## Accepted base

Q13 is built directly from the accepted Q12 merge:

`f1a13c0e670ce6596c610a465759b4450f3caed0`

Branch:

`design/aios-v2-q13-structured-fallback`

## Why Q13 exists

The V2 master plan requires both:

- a no-3D structured fallback in the representative prototype; and
- fallback-mode E2E in the V2 CI additions.

Before Q13, Organization already rendered a structured equivalent below the Living HQ stage, but the spatial stage was always mounted first. That meant AIOS had an accessible equivalent, but not an explicit renderer-free operating mode with browser proof.

The current Living HQ stage is DOM/CSS presentation rather than a WebGL-only runtime. Q13 therefore does not invent a GPU crash condition or speculative WebGL capability detector. It establishes the product contract needed before any future renderer becomes more demanding: the Owner can select Structured mode, and that path does not mount the Living HQ stage at all.

## Scope

- Add a native Spatial / Structured representation choice to the Organization workspace.
- Default to Spatial on each page load.
- Keep the choice local to the current component; no browser storage and no backend persistence.
- In Structured mode, do not mount `V2LivingHqVisualStage`.
- Keep Mission strip, Mission Room and Employee Inspector available in either representation.
- Expand the structured equivalent with:
  - semantic wing headings;
  - governed department counts;
  - mapped roster entries;
  - intentionally unplaced roster entries;
  - wing-detail navigation;
  - employee inspection controls.
- Preserve an always-available structured equivalent below the spatial representation when Spatial is selected.
- Add static Q13 contract tests.
- Add desktop-dark and phone-light reduced-motion fallback E2E.
- Wire fallback E2E into the exact-head production browser lane.

## Truth boundary

Representation choice changes presentation only.

It must not change:

- canonical organization data;
- authority or permissions;
- employee presence;
- physical location;
- WorkItem state;
- Mission state;
- blocker state;
- decision state;
- collaboration or conversation state;
- completion, urgency, health or success semantics.

Wing mapping remains a deterministic presentation mapping from exact canonical department identity. It is not physical employee location.

Roster identity remains distinct from presence.

Selecting a structured employee row changes inspection context only.

No new API read, write or persistence path is introduced.

## Deliberate non-goal

Automatic crash recovery for a hypothetical future WebGL/WebGPU renderer is not implemented in Q13 because the current Living HQ stage does not depend on such a renderer. When a real GPU-backed renderer exists, capability detection/error-boundary behavior should be added against that actual runtime rather than simulated now.

## Required acceptance

- `npm run test:structured-fallback`
- `npm run test:design-foundation`
- `npm run test:responsive`
- `npm run test:accessibility`
- `npm run test:request-auth`
- `npm run build`
- `npm run test:compiled-auth`
- Chromium fallback E2E at desktop and phone
- existing Living Organization, Q11 responsive and Q12 accessibility browser regressions
- exact-head repository policy
- exact-head frontend
- exact-head SQLite regression
- exact-head PostgreSQL governance

Do not merge until the exact candidate passes those gates.
