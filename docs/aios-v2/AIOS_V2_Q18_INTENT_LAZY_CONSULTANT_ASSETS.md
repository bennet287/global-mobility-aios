# AIOS V2 — Q18 Intent-Lazy Consultant Asset Optimization

## Accepted base

`72809caf92d2753d15d8b4fc2d8cab11dbf72b2d` — Q17 Performance Profiling Baseline merge.

Working branch:

`design/aios-v2-q18-asset-optimization`

## Why Q18 exists

Phase 12 still requires asset optimization after the Q17 measurement baseline.

Repository inspection found a concrete eager-loading target:

- `app/layout.tsx` globally mounted `AgentChatWidget` on internal routes;
- `AgentChatWidget` is a client component and starts closed by default;
- the closed widget statically imports its consultant API dependencies;
- therefore consultant implementation code entered the global client graph before the user expressed any intent to use it.

The source size of a dependency is not a transfer-size claim. Q18 therefore measures the production-build resource delta instead of assuming savings from source-file size.

## Q18 change

The root layout now mounts only `AgentChatWidgetLoader`.

The loader:

- preserves the existing floating consultant launcher;
- preserves suppression on `/portal`, `/return`, and `/partner-portal`;
- does not statically import `AgentChatWidget` or consultant API code;
- executes `import("./AgentChatWidget")` only after explicit user activation;
- renders the loaded consultant with `initiallyOpen`, so the first click still opens the panel immediately;
- exposes loading/retry state accessibly if the dynamic import fails.

`AgentChatWidget` retains chat routing, controlled-agent confirmation, human-control boundaries, and existing API behavior. Q18 changes loading posture, not authority.

## Measurement contract

Production Chromium records two views of the same page session:

1. **before activation** — closed consultant has not been imported;
2. **after activation** — consultant panel is visible and its dynamic JS resources have loaded.

The Q18 asset profile records:

- resource count;
- transfer bytes;
- encoded and decoded body bytes;
- script count;
- script transfer / encoded / decoded bytes;
- newly observed script URLs after activation.

Artifact:

`q18-consultant-asset-profile`

File:

`apps/web/e2e/asset-results/aios-v2-consultant-assets.json`

Contract:

`aios-v2-consultant-assets.v1`

The existing Q17 performance profile also remains in V12. Its Q18-branch sample can be compared with the accepted Q17 baseline to determine whether initial V2 resource count/transfer actually changed.

## Measured production evidence

Working-head V12 Production Proof #1419 passed and produced the Q18 asset artifact from production-build Chromium.

Within the same `/cockpit/v2` page session:

- before consultant activation: 33 resources, 323,999 transferred bytes, 16 script resources, 261,139 transferred script bytes;
- after first explicit activation: 46 resources, 406,020 transferred bytes, 24 script resources, 330,116 transferred script bytes;
- activation therefore introduced 13 resources and 82,021 transferred bytes, including 8 new JS resources and 68,977 transferred JS bytes;
- the proof recorded zero AIOS writes and zero page errors.

This directly demonstrates that the consultant implementation payload is absent before user intent and enters the page only when the user opens the consultant.

As supporting—not budget-setting—evidence, the accepted Q17 clean-head performance sample observed 48 resources and 420,192 transferred bytes in its profiling scenario, while the Q18 working-head Q17-compatible sample observed 46 resources and 400,181 transferred bytes. Runner variance means this comparison is not a universal byte-saving claim; the within-session activation delta above is the stronger causal proof.

## Truth boundary

- No backend/API/canonical mutation contract changes.
- Opening the consultant performs no AIOS write.
- Dynamic-chunk resource timing is browser measurement evidence, not a universal network-cost guarantee.
- No hard transfer-size budget is introduced in Q18.
- No claimed byte saving is accepted until production-build measurement confirms it.
- Client-facing routes continue to suppress the global consultant launcher before the full consultant module is loaded.

## Acceptance gates

Q18 is acceptable only if:

1. root layout no longer statically imports the full consultant widget;
2. the full widget is loaded only on first explicit activation;
3. first activation opens the consultant without a second click;
4. production Chromium observes at least one new JS resource after activation;
5. the Q18 JSON asset profile is generated and retained;
6. no AIOS write or page error occurs merely from loading/opening the consultant;
7. client-facing route suppression remains intact;
8. Q17 profiling and all existing V2 hardening/browser/backend gates remain green;
9. measured initial-route resource evidence is inspected before any saving is claimed.
