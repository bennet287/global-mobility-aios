# Track B — Durable Activity Lineage Cockpit Tranche

**Date:** 2026-08-31
**Branch:** `roadmap/global-mobility-aios-v12`
**Classification:** Track B parallel product-experience refinement; **M remains NOT STARTED**
**Implementation checkpoint before documentation:** `cc58d872424dc3d27ee9b5d9290c2093bcf8d3c0`
**Local proof state for this tranche:** OBSERVED at exact head `958b7965483878dbde6fcc91c75c5ed0b4049fc0`

## 1. Why this tranche exists

The Track B anti-duplication audit identified transcript/tool-activity presentation and collaboration visualization as future product-experience gaps, while also proving that AIOS already owns a durable `OrganizationActivity` transparency model.

Repository inspection before this implementation confirmed:

```text
canonical OrganizationActivity persistence                  EXISTING
Board-safe TransparencyActivityRecord projection            EXISTING
Austria Live Organization snapshot activities[]             EXISTING
frontend AustriaLiveActivity contract                       EXISTING / PARTIAL
Cockpit durable activity count                              EXISTING
Cockpit rendering of snapshot.activities                    MISSING
Munder/CopilotKit/AG-UI runtime dependency                  NONE
parallel donor event / transcript / activity store          NONE REQUIRED
```

Therefore the correct Track B action is to expose the existing AIOS activity lineage, not to introduce Munder event state or a second activity truth model.

## 2. Anti-duplication decision

Selected implementation:

```text
AIOS OrganizationActivity
        ↓
existing Board-transparency projection
        ↓
existing Austria Live Organization activities[]
        ↓
repository-owned TypeScript contract
        ↓
Cockpit durable activity-lineage presentation
```

Rejected for this tranche:

- Munder event synchronization runtime;
- provider transcript ingestion as canonical activity;
- donor-owned collaboration state;
- a new activity/event database;
- simulated presence or heartbeat;
- client-side activity timers;
- CopilotKit / AG-UI adoption;
- a new authority or workflow model.

Permanent boundary:

> **Provider transcript != canonical OrganizationActivity automatically.**

and:

> **TELEMETRY != CANONICAL ORGANIZATION ACTIVITY.**

## 3. Implementation

### Frontend activity contract

`apps/web/lib/live-organization.ts` now mirrors the already-existing backend `causation_activity_id` field for durable activity records.

No backend schema or persistence model was added.

### Cockpit durable lineage

`apps/web/app/cockpit/live-organization/page.tsx` now renders the snapshot's persisted `activities` as **Durable activity lineage**.

Each rendered record is sourced from the existing Board-safe projection and may show:

- persisted occurrence time;
- title and summary;
- canonical position/actor;
- transparency role;
- activity type;
- WorkItem reference;
- trace identifier when present;
- persisted causation activity when present.

When no activities exist, the UI states that no durable `OrganizationActivity` is persisted. It does not generate substitute activity.

The surface explicitly states that provider transcripts, tool logs and donor event streams are not promoted to organizational truth.

### Runtime-quality fixture robustness

The runtime-economics summary now treats both null and absent legacy/test-fixture runtime-quality values as unavailable rather than dereferencing an undefined record.

The Playwright fixture was updated to include the current `runtime_quality` contract so browser proof exercises the actual Track B runtime-economics path instead of relying on a stale pre-V12.40 fixture.

### Tests

`apps/web/scripts/live-organization-surface.test.mjs` now requires:

- `snapshot.activities` rendering;
- durable activity-lineage labels;
- `causation_activity_id` client typing;
- the explicit provider-transcript/tool-log/donor-event non-authority statement;
- continued absence of simulated timers/random activity.

`apps/web/e2e/tests/live-organization.spec.ts` now:

- supplies runtime-quality fields in the canonical browser fixture;
- verifies runtime-quality presentation;
- supplies activity causation shape;
- verifies the persisted activity-lineage surface after bounded owner synthesis.

## 4. Relationship to the previous Track B tranche

The preceding runtime-economics tranche was locally exercised by the user at exact head:

`693c9975995bf8fc6388773d120594e5a1a75447`

Observed there:

```text
design-foundation tests                 30 / 30 PASS
request-auth tests                       4 / 4 PASS
compiled-auth contract                   PASS
TypeScript noEmit                        PASS
Next.js production build                 PASS
repository policy                        PASS
release consistency                      PASS
Python dependency constraints            PASS
diff hygiene                             PASS
git diff --check                         PASS
local V12 == origin V12                  PASS
frozen V11 head                          ac130deaafa7aa44068e9459facbda2b4df327d6
deep-R3 local backup                     3a6fea2cbbf87d424459b81f1b168ecd6baaa312
```

That exact-head run did **not** include the Playwright E2E suite. It is therefore source/type/build/repository proof for `693c997...`, not browser proof and not proof for this later activity-lineage tranche.

GitHub Actions observed for `693c997...` ended with jobs that exposed no executable steps, so those labels remain infrastructure/runner-startup evidence rather than source-test results.

## 5. Observed exact-head acceptance proof

The user executed the tranche acceptance path on Windows PowerShell at exact head:

`958b7965483878dbde6fcc91c75c5ed0b4049fc0`

Observed:

```text
frontend npm audit                       PASS — 0 vulnerabilities
design-foundation tests                  PASS — 30 / 30
request-auth tests                       PASS — 4 / 4
TypeScript noEmit                        PASS
Next.js production build                 PASS — 41 routes generated
compiled-auth contract                   PASS
Playwright Chromium E2E                  PASS — 5 / 5
E2E npm audit                            PASS — 0 vulnerabilities
repository policy                        PASS
release consistency                      PASS
Python dependency constraints            PASS — 27 direct dependencies
diff hygiene                             PASS
git diff --check                         PASS
working tree / origin synchronization    PASS
frozen V11                               PASS — ac130deaafa7aa44068e9459facbda2b4df327d6
deep-R3 local backup                     PASS — 3a6fea2cbbf87d424459b81f1b168ecd6baaa312
```

The Node `MODULE_TYPELESS_PACKAGE_JSON` message during the request-auth test was a warning only; all four tests passed.

This proof belongs only to `958b796...`. Later documentation or implementation commits do not inherit exact-head PASS automatically.

## 6. What remains genuinely open

This tranche does not claim:

- canonical employee presence/heartbeat;
- event-synchronization transport;
- provider transcript ingestion;
- tool-call capture beyond existing durable OrganizationActivity;
- semantic collaboration-group visualization;
- Living Organization scene mechanics;
- historical AI Economics analytics;
- Storybook adoption;
- Munder runtime adoption;
- CopilotKit / AG-UI adoption;
- milestone M activation;
- L acceptance.

A future collaboration slice must first prove that the required relationship cannot already be derived safely from canonical WorkItem, OrganizationPosition and OrganizationActivity lineage.

## 7. Milestone boundary

```text
L    IMPLEMENTED / ACCEPTANCE PENDING
M    NOT STARTED
N    NOT STARTED
```

Track B remains supporting parallel product-experience work. The release-critical L gate remains genuine independent professional Austria review followed by final exact-current-head technical proof.
