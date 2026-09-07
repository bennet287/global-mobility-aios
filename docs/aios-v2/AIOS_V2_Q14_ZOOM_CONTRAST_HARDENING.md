# AIOS V2 Q14 — Zoom & Contrast Hardening

## Purpose

Q14 closes two explicit Phase 12 hardening requirements from the AIOS V2 master plan: contrast and 200% zoom/reflow. It is a presentation-only hardening slice. It does not change canonical organization data, semantic status mappings, authority, evidence posture, movement, presence, or backend behavior.

## Audit finding

The accepted Q13 base still had two measurable gaps:

1. The dark `text-soft` token could fall below 4.5:1 against raised V2 surfaces.
2. Several light-theme soft/semantic foreground tokens could fall below 4.5:1 against one or more core V2 light surfaces.

Q10 already contained a focused contrast check for the permanently-dark Living HQ stage, but the general V2 hardening lane did not prove the shared theme token palette or 200% zoom/reflow across the main Owner workspaces.

## Token corrections

Q14 adjusts luminance only as far as required to reach AA-level 4.5:1 contrast across the shared canvas/surface family. Existing hue families and semantic meanings are preserved.

Dark presentation:
- `text-soft`: `#757a82` → `#84888f`

Light + system-light presentation:
- `text-soft`: `#8a887f` → `#6a6962`
- `technology`: `#4777a7` → `#406c98`
- `regulatory`: `#91672f` → `#89612c`
- `operations`: `#3f7f73` → `#397268`
- `security`: `#60669a` → `#5f6599`
- `success`: `#3f7b62` → `#3b735c`
- `warning`: `#9e6928` → `#8e5f24`
- `critical`: `#a94f49` → `#a64e48`
- `info`: `#4d789f` → `#466c90`

No semantic color is reassigned to a different meaning.

## Static contract

`aios-v2-zoom-contrast.test.mjs` parses the committed dark and light solid-color tokens, computes WCAG relative luminance, and requires every core foreground token to reach at least 4.5:1 against each core V2 surface:

- canvas
- canvas-soft
- surface
- surface-raised
- surface-inset

The static contract also requires explicit-light and system-light corrected tokens to remain identical.

## Browser contract

`aios-v2-zoom-contrast.spec.ts` runs in Chromium for dark and light presentations. A 1280px desktop at 200% browser zoom exposes roughly a 640 CSS-pixel layout width; Q14 uses that effective CSS width so responsive media-query reflow is exercised rather than merely scaling pixels.

At the 640px effective width the proof verifies:

- computed dark/light token contrast remains at least 4.5:1;
- Owner Home, Organization, Missions, Evidence, Decisions and History remain free of horizontal page overflow;
- the V2 theme control remains reachable;
- governed-source degradation remains handled without page errors;
- no backend writes occur.

Reduced motion is enabled during the browser proof so zoom/contrast acceptance does not depend on animation.

## CI

Q14 adds its static test to `test:design-foundation` and its Chromium spec to the existing Living Organization + V2 hardening browser lane. Backend SQLite and PostgreSQL lanes remain unchanged and are still required for exact-head acceptance.

## Deferred

Visual-regression screenshot baselines remain a separate master-plan requirement. Q14 deliberately does not introduce binary screenshot infrastructure; that should be a dedicated deterministic slice with baseline ownership, update policy, and review evidence.