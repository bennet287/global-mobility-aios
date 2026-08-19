# V1.3-C.2 — Non-Executing Material Attempt Transparency

**Date:** 2026-08-20  
**Branch:** `roadmap/global-mobility-aios-v12`  
**State:** **IMPLEMENTED / CANONICAL REPOSITORY ACCEPTANCE PENDING**

## Purpose

C.1 made successful governed material actions reconstructable. C.2 closes the next visibility gap: material actions that governance blocks or routes to review must also remain inspectable.

The required behavior is:

```text
Material action attempt
        ↓
Governance Kernel
        ↓
BLOCK or REVIEW_REQUIRED
        ↓
NO domain mutation
        +
trace-scoped durable governance Attempt Activity
        ↓
Board-inspectable reconstruction
```

This matters because transparency is incomplete if the Board can see only what AIOS executed but cannot see consequential actions that policy, authority, risk, concurrency or autonomy controls prevented.

## B.2 compatibility

C.2 does **not** rewrite the sealed B.2 command service.

Instead it adds a transparency facade:

```text
apps/api/app/services/organization_governed_work_transparency.py
```

The facade calls the sealed:

```text
governed_assign_work_item(...)
```

and preserves its behavior for:

```text
AUTO_EXECUTE
IDEMPOTENT_REPLAY
```

For:

```text
BLOCK
REVIEW_REQUIRED
```

C.2 appends a separate governance attempt Activity.

## Critical idempotency separation

A denied or review-routed attempt must not become the successful-command replay record.

Successful B.2 command identity remains:

```text
governance:<idempotency_key>
```

C.2 attempt identity is:

```text
governance:attempt:<trace_id>
```

Therefore:

```text
A2 review-required attempt
        ↓
recorded as attempt
        ↓
authority later legitimately increases to A4
        ↓
same requested idempotency key can still be evaluated
        ↓
AUTO_EXECUTE may create governance:<idempotency_key>
```

A past denial does not masquerade as a successful replay record.

## Attempt payload

The durable attempt record preserves structured governance state including:

- action type;
- capability;
- outcome;
- governance reason;
- constitutional Activity class;
- effective risk tier;
- consequence class;
- HumanReviewReason where applicable;
- action fingerprint;
- trace ID;
- requested idempotency key;
- requested assignment target;
- requested expected version;
- requested reason.

It does not store hidden model chain-of-thought.

## Mutation rule

`BLOCK` and `REVIEW_REQUIRED` remain non-mutating outcomes.

The attempt Activity is transparency/audit state only. It does not imply that the requested WorkItem assignment occurred.

## Fail-closed visibility rule

If C.2 cannot persist the durable attempt Activity, the transparency-aware facade raises rather than silently reporting a material attempt that disappears from organizational visibility.

Because the underlying B.2 `BLOCK`/`REVIEW_REQUIRED` path has not mutated the WorkItem, rollback preserves the domain state.

## Focused tests

Added:

```text
apps/api/tests/test_organization_transparency_attempts.py
```

Five tests cover:

1. A2 `REVIEW_REQUIRED` attempt persists a Board-inspectable trace without mutation;
2. stale-version `BLOCK` persists while the accepted WorkItem state remains unchanged;
3. scope-denied material attempt remains visible;
4. a review attempt does not poison later successful-command idempotency after legitimate authority increase;
5. attempt-Activity storage failure cannot silently hide a material attempt.

## Non-claims

C.2 does not yet implement:

- a generic MaterialAction persistence table;
- HTTP/Cockpit transparency endpoints;
- Board notification or alerting policy;
- aggregation/deduplication of repeated denied attempts;
- AgentConversation / AgentMessage persistence;
- ToolActionRecord;
- Evidence/VerifiedRule/SourceSnapshot DecisionLineage;
- sensitivity-tier filtering;
- Decision Readiness;
- independent verification;
- Organizational Immune System;
- canonical C.2 PASS;
- GitHub CI PASS.

Repeated denied attempts are intentionally durable at this stage. Later Board-facing surfaces should summarize normal/repetitive attempts rather than flooding the Board while retaining drill-down access.

## Acceptance gate

From the canonical Windows V12 checkout:

```text
pytest apps/api/tests/test_organization_governance_kernel.py \
       apps/api/tests/test_organization_governed_work.py \
       apps/api/tests/test_organization_transparency.py \
       apps/api/tests/test_organization_transparency_attempts.py -q

python scripts/check_repo_policy.py --root .

pytest apps/api/tests -q

python scripts/check_database_migrations.py

python scripts/check_local_db_schema.py \
  --database-url "sqlite:///D:/global-mobility-aios/gmai.db"

git diff --check
git status -sb
```

The protected `v10.22` roadmap regression must remain green after roadmap synchronization.

## Next direction after acceptance

If C.2 passes, the next transparency decision should be made against the first real mobility vertical. Strong candidates are:

1. explicit causation links between governance records and resulting effects;
2. bounded Board/Cockpit transparency query DTO/API;
3. ToolActionRecord and Evidence/rule lineage required by an actual mobility case.

Do not expand all of V1.3-C horizontally before the vertical workflow requires it.
