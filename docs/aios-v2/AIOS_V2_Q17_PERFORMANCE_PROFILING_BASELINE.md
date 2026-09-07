# AIOS V2 — Q17 Performance Profiling Baseline

## Accepted base

`252b188f73af0b2fcf9636d0d0b1760193c1c23c` — Q16 Truth-State Hardening merge.

Working branch:

`design/aios-v2-q17-performance-baseline`

## Why Q17 exists

Phase 12 of the AIOS V2 master plan requires profiling and asset optimization. The performance acceptance language explicitly says to measure shell interactivity, scene load, scene memory, frame stability, route transitions, animation jank, data-heavy surfaces and low-power behavior, and to set hard numeric thresholds only after measured prototypes exist.

Q17 therefore establishes the measurement contract before any optimization or performance budget is invented.

## Measurement contract

The production-build Chromium profile records:

- Owner shell readiness
- Search / Command interaction readiness
- Owner Home → Organization client-route transition
- direct Living HQ stage readiness
- requestAnimationFrame cadence (average, p95, maximum and diagnostic intervals over 34 ms)
- Long Task API observations when supported
- Chromium CDP JavaScript heap, DOM node/document, layout, style-recalc and task-duration metrics
- resource count, transfer bytes, decoded body bytes and summed resource timing
- a synthetic low-power proxy using Chromium 4× CPU throttling with reduced motion

The profile is emitted as:

`apps/web/e2e/performance-results/aios-v2-performance-baseline.json`

with contract version:

`aios-v2-performance-baseline.v1`

CI retains this JSON as the `q17-v2-performance-profile` artifact.

## First measured evidence

Two same-head GitHub Actions samples were collected from working head `b815aee15e6861a05e24ada546eda3cb59eeafc6` using the same production-build Chromium job and frozen read-only fixture.

| Measurement | Sample 1 | Sample 2 | Observed difference |
| --- | ---: | ---: | ---: |
| Owner shell ready | 310.0 ms | 313.0 ms | +1.0% |
| Search / Command open | 175.5 ms | 182.8 ms | +4.2% |
| Home → Organization | 155.9 ms | 144.4 ms | -7.4% |
| Direct Organization stage ready | 381.0 ms | 352.5 ms | -7.5% |
| rAF average interval | 25.8 ms | 23.3 ms | -9.7% |
| rAF p95 interval | 33.4 ms | 33.4 ms | 0.0% |
| JS heap used | 9.32 MB | 9.90 MB | +6.2% |
| DOM nodes | 4,282 | 4,610 | +7.7% |
| Resource count | 48 | 48 | 0.0% |
| Transfer bytes | 420,208 | 420,217 | effectively unchanged |
| 4× CPU proxy shell ready | 818.6 ms | 803.3 ms | -1.9% |
| 4× CPU proxy Organization ready | 664.4 ms | 625.4 ms | -5.9% |

Both samples recorded zero Long Task entries during the measured window and completed with no page errors or AIOS writes.

These values are **baseline evidence only**. The observed run-to-run variance demonstrates why Q17 does not convert a single GitHub-hosted runner sample into universal product-performance budgets. Future optimization work should compare repeated measurements and user-device evidence rather than treat any one value above as a hard threshold.

## Truth boundary

This slice is measurement-only.

- It does not add product or backend mutation paths.
- Frozen fixture data is test evidence, not canonical production data.
- Runner-specific milliseconds are observations, not universal product truth.
- Q17 does not enforce arbitrary millisecond, heap, frame-rate or transfer-size budgets.
- The current visible Living HQ stage is DOM/CSS presentation. CDP heap/DOM measurements are therefore browser-runtime observations, **not WebGL/GPU memory measurements**.
- Chromium 4× CPU throttling is explicitly a synthetic low-power proxy. It is not certification for a particular phone, laptop, CPU, battery state or thermal envelope.
- Diagnostic frame intervals over 34 ms are counted for visibility only; they are not a pass/fail threshold.

## CI acceptance for Q17

Q17 passes when the profiling harness:

1. runs against the production Next.js build under Chromium;
2. uses frozen read-only governed fixtures;
3. produces finite measurement values for supported metrics;
4. records no page errors or non-GET AIOS writes;
5. creates the versioned JSON report;
6. uploads that report as a CI artifact;
7. keeps existing V2 hardening, visual-regression and backend gates green.

Performance budgets and asset-optimization decisions belong to successor work only after the measured profile is inspected. A successor optimization must compare against measured evidence rather than choosing targets by intuition.
