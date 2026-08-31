# Track B — Product Experience Anti-Duplication Audit

**Date:** 2026-08-31
**Branch:** `roadmap/global-mobility-aios-v12`
**Audit baseline:** `ac337c958da3873184a702329d82c3c4fcef7735`
**Classification:** Track B parallel product-experience groundwork; **M remains NOT STARTED**

## 1. Purpose

This audit establishes what Global Mobility AIOS already implements for Track B before additional UX or Munder-derived work is introduced.

The objective is to prevent a second information architecture, navigation model, design system, organization-state store, telemetry authority, event truth, or donor-owned runtime representation from being created beside capabilities that already exist.

Permanent boundaries remain:

```text
UI INTENT != COMMAND AUTHORIZATION
TELEMETRY != CANONICAL ORGANIZATION ACTIVITY
AGENT FRAMEWORK STATE != ORGANIZATION TRUTH
CAN DO != MAY DO
```

Track B work may improve the existing L product experience while L acceptance continues, but it does not start or partially accept milestone M.

## 2. Audit result

| Track B capability | Repository truth | Anti-duplication decision |
|---|---|---|
| B1 information architecture | Existing frontend UX programme defines Cockpit / Board Room / Operations / My Mobility / department hierarchy | EXTEND; do not create a second IA |
| B1 navigation | `apps/web/lib/workspace-navigation.ts` is the shared workspace navigation model and `Sidebar.tsx` consumes the product shell | EXTEND canonical navigation only |
| B1 design system | Existing repository-owned design foundation, Cockpit classes/components and `design-foundation.test.mjs` are already present | REFINE; do not restart a design system |
| B1 Cockpit refinement | Existing Cockpit surfaces, `cockpit-refinements.test.mjs`, and `/cockpit/live-organization` already implement premium/product-state refinement | CONTINUE incrementally |
| B1 responsive/accessibility | Frontend programme defines explicit responsive/accessibility gates and existing design-foundation tests cover frontend contracts | STRENGTHEN where concrete gaps are found; do not invent a parallel framework |
| B2 donor capability audit | `MUNDER_DIFFLIN_AIOS_ADOPTION_V1.md` already classifies donor capabilities as ADAPT / REIMPLEMENT / REJECT and defines sovereignty boundaries | EXISTING; do not duplicate donor architecture |
| B2 presence / heartbeat | Munder programme identifies this as a future ADAPT slice; no canonical Munder presence runtime is installed in the web dependency set | GAP / demand-gated; derive future UI only from AIOS-owned runtime state |
| B2 event synchronization | Munder programme identifies event synchronization as donor mechanics only; AIOS must own event semantics | GAP / demand-gated; no parallel event truth |
| B2 transcripts / tool activity | Munder programme identifies transcripts/tool timelines as future transparency inputs; existing `OrganizationActivity` transparency already provides durable activity lineage | PARTIAL NATIVE FOUNDATION; do not map provider transcripts directly to canonical activity |
| B2 live employee/runtime representation | `/api/v1/organization/transparency/live-organization/austria/latest` and `/cockpit/live-organization` already project persisted owner/specialist execution, readiness, blockers, latency, retries, lineage and authority posture | IMPLEMENTED for current Austria L slice; extend rather than replace |
| B2 collaboration visualization | No accepted current Cockpit collaboration visualization was identified in this audit | GENUINE FUTURE GAP; must derive from canonical activity/work relationships |
| B2 cost/runtime telemetry | Backend `AustriaLiveRuntimeQualityRead` already exposes provider/model outcome, tokens, estimated cost, grounding/provenance and fallback state, but the web client previously omitted the runtime-quality type and UI | NATIVE DATA EXISTS; expose it rather than import donor telemetry state |
| Munder/CopilotKit/AG-UI runtime dependency | `apps/web/package.json` contains Next/React/Tesseract only for runtime dependencies; no Munder, CopilotKit or AG-UI package is installed on this canonical line | NOT ADOPTED; do not infer adoption from Radar/donor docs |

## 3. Existing canonical Track B foundations

### 3.1 Product experience / B1

The active frontend programme already defines UX0 through UX5 and establishes the design dependency chain:

```text
canonical state
→ information architecture
→ interaction semantics
→ reusable design-system capability
→ repository-owned React implementation
→ accessibility/responsive/browser proof
```

The current implementation already has a repository-owned workspace shell, centralized navigation, Cockpit surfaces, design-foundation tests and a persisted Live Organization surface. Track B must therefore proceed as refinement and gap closure, not as a frontend rewrite.

### 3.2 Live Organization / B2

The backend transparency route already exposes a Board-safe Austria Live Organization projection from persisted AIOS records. The projection includes:

- owner/specialist WorkItem state;
- owner synthesis readiness/result;
- blockers;
- durable OrganizationActivity records;
- latency and retries;
- Evidence and VerifiedRule references;
- provider/model authority posture;
- runtime-quality records including provider outcome, token usage, estimated provider cost, grounding provenance and fallback state.

The existing frontend already renders the core cycle, specialists, blockers, authority/readiness and provenance. Therefore importing Munder state to create a second live-organization model would be duplication and is prohibited.

## 4. First genuine gap selected

The smallest verified Track B gap is **frontend exposure of already-canonical runtime economics and quality**.

Before this tranche:

```text
backend runtime-quality projection = PRESENT
frontend TypeScript runtime-quality contract = MISSING
frontend token/cost/grounding/fallback presentation = MISSING
```

The selected implementation therefore does **not** add a new telemetry backend, donor state store, Munder package, event system or authority model.

It mirrors the existing `AustriaLiveRuntimeQualityRead` contract into the frontend and renders its persisted values inside the current Live Organization Cockpit.

Displayed signals include:

- observed runtime-quality record coverage;
- total recorded tokens;
- estimated provider cost when recorded;
- fresh-retrieval provenance count;
- template-fallback count;
- per-specialist provider/model outcome;
- per-specialist tokens/cost;
- grounding state.

Missing measurements remain `Not recorded`; they are not converted to zero or inferred.

## 5. Authority and truth boundary

```text
canonical execution / evidence / activity records
        ↓
Board-safe AIOS transparency projection
        ↓
repository-owned web client type
        ↓
Cockpit presentation
```

The presentation layer cannot create OrganizationActivity, provider/model authority, external-action authorization, Evidence or professional correctness.

This tranche intentionally implements the permanent rule:

> **TELEMETRY != CANONICAL ORGANIZATION ACTIVITY**

## 6. Deferred Track B gaps

The following remain separate future slices and are not claimed by this tranche:

- canonical employee presence / heartbeat mechanics;
- event synchronization transport;
- transcript and tool-activity visualization beyond current durable activity lineage;
- collaboration visualization;
- Living Organization scene mechanics;
- broader AI Economics aggregation/history;
- Storybook adoption;
- CopilotKit / AG-UI adoption;
- Munder runtime/provider integration.

These should be implemented only after another anti-duplication check demonstrates a concrete gap and a bounded acceptance test.

## 7. Acceptance scope

The Track B tranche is accepted only when repository/local proof confirms:

1. frontend runtime-quality types match the existing backend projection;
2. the Live Organization surface renders only persisted runtime-quality fields;
3. missing token/cost records are not treated as zero;
4. telemetry is explicitly non-authoritative;
5. no simulated presence/activity timer is introduced;
6. frontend tests/type/build remain green;
7. repository policy and diff hygiene remain green.

This is **not** evidence that milestone M started or that Munder/CopilotKit/AG-UI were adopted.
