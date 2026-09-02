# V1.3-C.3 — Explicit Governance → Effect Causation

**Date:** 2026-08-20  
**Branch:** `roadmap/global-mobility-aios-v12`  
**State:** **IMPLEMENTED / CANONICAL REPOSITORY ACCEPTANCE PENDING**

## Purpose

C.1 established shared trace correlation between governance authorization and the resulting organization effect. C.3 strengthens that relationship from correlation to explicit causation for the first governed material action.

The governed WorkItem assignment now records:

```text
Governance authorization Activity
        │
        │ activity.id
        ▼
organization.work.assigned.v1
causation_activity_id = governance Activity id
```

This lets Board/transparency consumers distinguish records that merely occurred in the same trace from the specific authorization that caused a domain effect.

## Scope

C.3 remains deliberately narrow:

```text
work_item.assignment
risk = R1
consequence = REVERSIBLE
```

No new table, migration, event store, generalized lineage graph or Cockpit endpoint is introduced.

## Runtime behavior

For `AUTO_EXECUTE`, `governed_assign_work_item(...)` now stages the governance authorization Activity first inside the caller-owned transaction.

The WorkItem mutation, assignment audit and semantic assignment Activity are then staged with the governance Activity UUID as the semantic effect's `causation_activity_id`.

The final transaction remains:

```text
Governance Activity staged
        ↓
WorkItem mutation
        +
assignment audit
        +
semantic assignment Activity
        │
        └── causation_activity_id → Governance Activity
        ↓
ONE COMMIT
```

If either authorization or effect staging fails, the entire unit rolls back.

## Semantic compatibility

The C.3 assignment effect preserves the existing semantic Activity contract:

```text
activity_type = organization.work.assigned.v1
stream_key    = work:<work_item_id>
semantic contract version = v1
```

The semantic source-object version is calculated using the same canonical event-version inputs as the accepted semantic Activity layer. The Activity record fingerprint additionally includes the explicit causal reference through the existing `stage_activity(...)` contract.

## Idempotency

The sealed B.2 successful-command replay contract remains unchanged.

An exact replay:

```text
same successful idempotency key
+ same action fingerprint
→ IDEMPOTENT_REPLAY
```

No new governance Activity or semantic effect is appended, so the original causal chain remains singular.

## Focused tests

Added:

```text
apps/api/tests/test_organization_transparency_causation.py
```

Three focused tests cover:

1. the WorkItem assignment effect explicitly points to the governance authorization Activity;
2. exact successful replay does not duplicate the causal chain;
3. effect-storage failure rolls back the staged governance authorization and WorkItem mutation together.

## Non-claims

C.3 does not yet implement:

- a complete graph traversal API for arbitrary Activity lineage;
- Evidence / VerifiedRule / SourceSnapshot decision lineage;
- ToolActionRecord;
- AgentConversation / AgentMessage lineage;
- Board/Cockpit HTTP transparency endpoints;
- sensitivity-tier enforcement;
- migration/schema changes;
- canonical repository PASS;
- GitHub CI PASS.

## Acceptance gate

From the canonical Windows V12 checkout:

```text
pytest apps/api/tests/test_coverage_tranche_operations_script.py::test_v10_22_documentation_and_roadmap_are_present -q

pytest apps/api/tests/test_organization_governance_kernel.py \
       apps/api/tests/test_organization_governed_work.py \
       apps/api/tests/test_organization_transparency.py \
       apps/api/tests/test_organization_transparency_attempts.py \
       apps/api/tests/test_organization_transparency_causation.py -q

python scripts/check_repo_policy.py --root .
pytest apps/api/tests -q
python scripts/check_database_migrations.py
python scripts/check_local_db_schema.py --database-url "sqlite:///D:/global-mobility-aios/gmai.db"
git diff --check
git status -sb
```

Only canonical results may move C.3 to PASS.

## Direction after C.3

If C.3 passes, C has enough low-level trace mechanics for the first governed action. The next step should favor a bounded **Board/Cockpit transparency read contract** or move toward the D/E vertical prerequisites rather than extending generic lineage machinery without a product consumer.
