# V1.3-C.2 Acceptance — Non-Executing Material Attempt Transparency

**Date:** 2026-08-20  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Slice:** V1.3-C.2 — Non-Executing Material Attempt Transparency  
**Disposition:** **COMPLETE / PASS / SEALED**

## Purpose

C.2 closes the first transparency gap left after C.1: material governance attempts that are blocked or routed to review must remain visible even when no domain mutation occurs.

C.2 preserves the sealed B.2 successful-command idempotency contract while recording non-executing attempts under trace-scoped Activity keys.

## Canonical acceptance evidence

Reported from the canonical Windows V12 checkout on 2026-08-20.

### Focused / roadmap checks

The focused C.2 governance/transparency chain and protected roadmap compatibility check were reported green in the canonical checkout. The final pasted console excerpt did not restate their exact counts, so no exact focused-test count is invented here.

### Repository policy

```text
Repository policy check passed.
```

### Full API regression

```text
922 passed, 5 skipped, 1 warning in 320.37s (0:05:20)
```

### Database migration integrity

```text
Database migration check passed.
database_url=sqlite:///./gmai.db
migration_heads=0076_organization_position_active_identity
registered_tables=118
physical_schema=ok
database_revision=0076_organization_position_active_identity
```

### Local database schema

```text
Local DB schema check passed.
database_url=sqlite:///D:/global-mobility-aios/gmai.db
registered_tables=118
actual_tables=118
physical_tables=119
infrastructure_tables=["alembic_version"]
```

### Git integrity

```text
git diff --check
# no output

git status -sb
## roadmap/global-mobility-aios-v12...origin/roadmap/global-mobility-aios-v12
```

## Accepted behavior

C.2 accepts:

- `BLOCK` material attempts are persisted as durable governance-attempt Activities;
- `REVIEW_REQUIRED` material attempts are persisted without mutating canonical WorkItem state;
- attempt records are Board-inspectable through the C.1 trace reconstruction service;
- successful-command idempotency remains separate from rejected/review-attempt persistence;
- a prior review attempt cannot poison a later legitimately authorized execution;
- attempt storage failures fail closed rather than silently losing material governance history;
- no migration or new registered domain table is required.

Attempt keys remain trace-scoped:

```text
governance:attempt:<trace_id>
```

Successful B.2 command keys remain:

```text
governance:<idempotency_key>
```

## Warning disposition

The single warning remains the pre-existing Starlette/httpx TestClient deprecation warning and is not a C.2 regression.

## Final disposition

```text
V1.3-C.2
COMPLETE
PASS
SEALED
```

Accepted API baseline after C.2:

```text
922 passed / 5 skipped / 1 warning / 0 failed
```

No GitHub CI PASS is claimed without attached status/check evidence.
