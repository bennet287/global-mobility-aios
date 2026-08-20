# V1.3-C.3 Acceptance — Explicit Governance → Effect Causation

**Date:** 2026-08-20  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Slice:** V1.3-C.3 — Explicit Governance → Effect Causation  
**Disposition:** **COMPLETE / PASS / SEALED**

## Purpose

C.3 strengthened the first governed material action from shared trace correlation to explicit authorization-to-effect causation.

The accepted relationship is:

```text
Governance authorization Activity
        │
        │ activity.id
        ▼
organization.work.assigned.v1
causation_activity_id = governance Activity id
```

The WorkItem mutation, audit, governance Activity and semantic effect remain one atomic unit.

## Canonical acceptance evidence

The Human Owner ran the prescribed C.3 canonical acceptance sequence from the Windows V12 checkout and reported **all checks green**.

The sequence covered:

- protected `v10.22` roadmap compatibility regression;
- focused B.1/B.2/C.1/C.2/C.3 governance/transparency suite;
- repository policy;
- full API regression;
- database migration integrity;
- local database schema parity;
- `git diff --check`;
- clean/synchronized branch status.

The exact final pytest counts were not restated in the acceptance message, so they are intentionally **not invented** in this record.

The previously accepted full-API baseline before C.3 was:

```text
922 passed / 5 skipped / 1 warning / 0 failed
```

That historical C.2 baseline is not represented as a C.3 rerun count.

## Accepted behavior

C.3 accepts:

- a successful governed WorkItem assignment stages its governance authorization before its semantic effect;
- the resulting `organization.work.assigned.v1` Activity explicitly carries `causation_activity_id` pointing to the governance Activity;
- the existing shared trace/correlation identity is preserved;
- exact successful replay does not append a duplicate governance/effect chain;
- effect-storage failure rolls back the staged governance authorization and WorkItem mutation together;
- the semantic Activity type/key/version contract remains compatible;
- no migration or new registered domain table is required.

## Warning disposition

The known Starlette/httpx TestClient deprecation warning remains dependency-maintenance debt. No new warning is attributed to C.3 without explicit evidence.

## Final disposition

```text
V1.3-C.3
COMPLETE
PASS
SEALED
```

No GitHub CI PASS is claimed without attached status/check evidence.
