# V1.3-B.2 Acceptance — Governed WorkItem Assignment

**Date:** 2026-08-20  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Slice:** V1.3-B.2 — Governed WorkItem Assignment  
**Disposition:** **COMPLETE / PASS / SEALED**

## Purpose

B.2 proves that the accepted V1.3 Governance Kernel can authorize and execute one real, reversible, low-risk existing organization mutation without creating a parallel domain model or bypassing existing audit/Activity semantics.

The governed action is:

```text
work_item.assignment
risk = R1
consequence = REVERSIBLE
capability = operations.work
```

## Canonical acceptance evidence

Reported from the canonical Windows V12 checkout on 2026-08-20.

### Focused B.1 + B.2 suite

```text
25 passed, 1 warning in 3.08s
```

This covers the 19 Governance Kernel tests plus the six governed WorkItem integration/atomicity tests.

### Repository policy

```text
Repository policy check passed.
```

### Full API regression

```text
911 passed, 5 skipped, 1 warning in 316.36s (0:05:16)
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

The canonical local schema check was rerun separately after an initial PowerShell command concatenation error and was reported **green / PASS**.

No new migration or registered domain table was introduced by B.2.

### Git integrity

`git diff --check` was rerun separately and reported green/clean. The V12 branch status was synchronized with its remote tracking branch.

## Accepted runtime behavior

The B.2 path now proves:

```text
OrganizationCommandContext
        ↓
CapabilityAuthority
        ↓
MaterialAction(work_item.assignment)
        ↓
constitutional risk floor
        ↓
authority / capability / scope
        ↓
durable idempotency
        ↓
expected-version precondition
        ↓
policy / autonomy
        ↓
AUTO_EXECUTE
        ↓
existing WorkItem assignment semantics
        +
existing assignment audit
        +
existing semantic OrganizationActivity
        +
Governance OrganizationActivity / trace
        ↓
ONE TRANSACTION COMMIT
```

Accepted properties include:

- authorized R1/A4 WorkItem reassignment auto-executes;
- exact retries are idempotent even after the first successful action advances the WorkItem precondition;
- conflicting idempotency-key reuse fails closed;
- stale competing commands fail closed;
- A2 routes to review and does not mutate canonical state;
- governance Activity storage failure prevents the WorkItem mutation/audit/Activity unit from committing;
- government submission remains outside this slice and remains Board-reserved under the constitutional contract.

## Warning disposition

The single warning remains the pre-existing Starlette/httpx TestClient deprecation warning:

```text
StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.
```

It is non-blocking for B.2 and remains dependency-maintenance work rather than a reason to alter dependencies inside the governance phase.

## Non-claims

B.2 does not claim:

- every WorkItem mutation is governed through `MaterialAction`;
- a public HTTP Command Gateway exists;
- blocked/review-required attempts have their final Transparency persistence model;
- full Decision Lineage exists;
- AgentConversation/AgentMessage persistence exists;
- ToolActionRecord exists;
- Decision Readiness exists;
- independent R3+ verification exists;
- Organizational Immune System exists;
- earned-autonomy promotion/demotion exists;
- GitHub CI PASS without attached check/status evidence.

## Final disposition

```text
V1.3-B.2 — Governed WorkItem Assignment
COMPLETE
PASS
SEALED
```

The accepted API baseline after this slice is:

```text
911 passed / 5 skipped / 1 warning / 0 failed
```

The next Track C work should begin V1.3-C with bounded Transparency/trace reconstruction over the existing durable OrganizationActivity substrate rather than adding more abstract Governance Kernel machinery without runtime need.
