# Application Engine v1.3

Application Engine v1.3 fixes draft creation for the current `ApplicationRecord` schema.

## Problem

Draft creation failed with:

```text
NOT NULL constraint failed: applications.domain
```

The current model requires `domain`, but the draft payload only attempted generic keys such as `application_type`, `type`, and `kind`. Those keys are ignored when they are not part of the active model fields.

## Fix

The draft payload now includes:

- `domain`: mapped from the requested application type, for example `visa`, `study`, or `job`
- `risk_score`: defaulted to `0.5` for the current baseline application workflow

## Invariant

Computed readiness stages such as `blocked_truth_rejected` remain guardrail/readiness values only. Persisted `ApplicationRecord.status` remains a workflow value such as `draft`, `approved`, or `submitted`.
