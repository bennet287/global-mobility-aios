# V1.3-E.2 — Governed Eligibility Transition Intent Acceptance

**Date:** 2026-08-20  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Status:** COMPLETE / PASS / SEALED

## Accepted scope

V1.3-E.2 proves the second half of the first governed Global Mobility AIOS execution loop:

```text
persistent OrganizationPosition employee
→ governed case/pathway ContextBundle
→ EmployeeRuntimeBinding
→ bounded runtime proposal
→ typed EligibilityTransitionIntent
→ deterministic domain validation
→ MaterialAction(eligibility.transition)
→ Command Gateway
→ REVIEW_REQUIRED / BLOCK
→ durable Board-inspectable OrganizationActivity attempt
```

E.2 deliberately does **not** mutate eligibility state. It proves that a model-generated material recommendation remains a proposal until AIOS independently validates and governs it.

Permanent rule:

> **The runtime proposes. AIOS validates. The Command Gateway authorizes or refuses organizational action.**

## Canonical local acceptance evidence

The Human Owner ran the canonical local V12 acceptance on 2026-08-20 and supplied the following exact results:

```text
Repository policy check        PASS
Full API regression            984 passed / 5 skipped / 1 warning / 0 failed
Duration                       355.85s
Database migration check       PASS
Migration head                 0076_organization_position_active_identity
Registered tables              118
Physical schema                ok
Local DB schema check          PASS
Actual tables                  118
Physical tables                119
Infrastructure tables          ["alembic_version"]
git diff --check               clean
V12 branch                     clean / synchronized
```

Known non-blocking warning:

```text
StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.
```

No dependency change is implied by this warning.

## Accepted governance behavior

E.2 is accepted with the following safety semantics:

- `OrganizationPosition.position_key` is the organizational actor identity;
- provider/model/runtime identity never becomes the authority bearer;
- the runtime can emit only the narrow typed proposal fields;
- provider/model identity comes from the D.2 runtime binding and provider response, not model output;
- case/profile state participates in ContextBundle freshness;
- `Profile.profile_version` remains the material eligibility precondition;
- governed Evidence and VerifiedRule citations must remain inside the ContextBundle authority set;
- stale, forged, malformed, wrong-country or out-of-authority references fail closed;
- WorkItem working context cannot self-promote Evidence, rules, policy, tools, provider identity or authority;
- confidence is informational only and cannot relax deterministic gates;
- authority, scope, risk, expected-version, idempotency and autonomy authorization remain Command Gateway responsibilities;
- A0 remains `BLOCK / AUTONOMY_PROHIBITED`;
- A1–A5 cannot execute the R3 eligibility transition while independent verification is unsatisfied;
- E.2 therefore supplies `PolicyDisposition.HUMAN_REQUIRED` for the current R3 verification floor;
- REVIEW_REQUIRED/BLOCK attempts are durable and Board-inspectable through existing transparency readers;
- no `EligibilityAssessment`, Lead eligibility truth, application state, client-facing recommendation or external action is mutated.

## Case-data provider boundary

E.2 performs bounded data minimization and excludes direct contact fields such as full name, email and phone from the runtime payload.

E.2 does **not** claim that provider-egress/sensitivity policy is complete. For this reason the case-scoped pilot requires an explicitly supplied `LLMProvider` adapter rather than automatically selecting an external provider through `LLMProviderFactory`.

## What E.2 proves

The accepted vertical demonstrates:

```text
AI employee reasoning
        ↓
typed material proposal
        ↓
AIOS-owned deterministic validation
        ↓
AIOS-owned MaterialAction construction
        ↓
Command Gateway evaluation
        ↓
R3 verification floor prevents execution
        ↓
durable transparent organizational attempt
```

This is the first accepted proof that a model can propose a material eligibility action and AIOS can durably refuse to execute it while preserving Board-visible lineage.

## Non-claims

This acceptance does not claim:

- canonical eligibility decision execution;
- Decision Readiness completion;
- independent verification completion;
- client-facing legal advice or eligibility recommendation;
- provider-egress authorization for case data;
- generic intent dispatch;
- AgentRun / Flight Recorder completion;
- Munder runtime adoption;
- GitHub CI PASS.

No GitHub CI PASS is claimed because no attached GitHub status/check evidence exists for this checkpoint.

## Next bounded stage

The next stage is V1.3-F Decision Readiness.

F must remain routing/quality infrastructure rather than authorization:

> **Scores route; deterministic gates authorize.**

F should assess whether a material eligibility proposal has enough governed case facts, Evidence, rule coverage, contradiction resolution, policy state and verification readiness to proceed to V1.3-G independent verification. It must not itself authorize the eligibility mutation.

Only after F and genuinely independent G verification are accepted should a later bounded slice consider an authorized canonical eligibility effect.