# V1.3-C.1 — Transparency Trace Foundation

**Date:** 2026-08-20  
**Branch:** `roadmap/global-mobility-aios-v12`  
**State:** **IMPLEMENTED / CANONICAL REPOSITORY ACCEPTANCE PENDING**

## Purpose

C.1 starts the V1.3 Transparency Foundation by making the first real governed material action reconstructable from the durable organization Activity substrate that already exists.

The goal is deliberately narrower than the complete V1.3-C architecture.

C.1 proves:

```text
Governance authorization
        +
resulting organization effect
        ↓
shared trace identity
        ↓
tenant-scoped durable Activity query
        ↓
Board-inspectable structured reconstruction
```

It does not introduce a second event store or prematurely add conversation/tool/decision-lineage tables before runtime evidence requires them.

## Existing substrate reused

`OrganizationActivity` already provides:

- tenant ownership;
- durable activity identity;
- streams and sequence numbers;
- actor identity/type;
- department/position/authority context;
- source object identity/version;
- WorkItem links;
- correlation keys;
- causation/supersession link fields;
- immutable-ish semantic payload fingerprints;
- occurred/created timestamps.

C.1 therefore builds a typed transparency projection/query layer over this accepted substrate.

## Runtime changes

### Trace correlation for governed WorkItem assignment

`governed_assign_work_item(...)` now derives a command context whose `correlation_key` is the Governance Kernel `trace_id` before staging the actual WorkItem mutation.

Therefore both:

```text
organization.work.assigned.v1
```

and:

```text
governance.work_item.assignment.auto_execute
```

share the same durable correlation identity.

The existing atomic transaction guarantee remains unchanged: failure in the staged unit prevents the mutation/audit/Activity unit from committing.

### Transparency service

Added:

```text
apps/api/app/services/organization_transparency.py
```

The service provides:

- `TransparencyActivityRecord`;
- `GovernedActionTrace`;
- `transparency_activity_record(...)`;
- `activities_for_trace(...)`;
- `activities_for_work_item(...)`;
- `governed_action_trace(...)`.

## Constitutional classification

V1.3 Governance Activities already carry their constitutional class explicitly in the durable payload:

```text
MATERIAL
AUTHORITY
```

C.1 reads that class and applies the frozen constitutional transparency policy.

For example, the current governed WorkItem assignment is `MATERIAL`, so its governance record is:

```text
Board inspectable       YES
Durable record required YES
Full lineage required   YES
Policy compaction       NO
```

Existing pre-V1.3 Activities that do not carry a constitutional class remain Board-inspectable but are **not silently reclassified**. Their constitutional retention/lineage fields remain unknown (`None`) until an explicit later migration/classification policy exists.

This preserves repository truth instead of manufacturing historical semantics.

## Fail-closed transparency rules

C.1 fails closed when a durable governance record is structurally ambiguous, including:

- invalid Activity payload JSON;
- non-object payload;
- unsupported constitutional activity class;
- invalid trace identity;
- governance `trace_id` / `correlation_key` mismatch;
- a governed trace containing zero or multiple governance roots.

## Tenant isolation

All trace and WorkItem-history queries require an explicit tenant key and filter on it at the database query boundary.

A correlation identifier is not globally authoritative and cannot be used to cross tenant boundaries.

## Focused tests

Added:

```text
apps/api/tests/test_organization_transparency.py
```

Six focused tests cover:

1. governed WorkItem assignment shares one trace across governance authorization and organization effect;
2. `governed_action_trace(...)` reconstructs the material action;
3. trace queries remain strictly tenant-scoped;
4. legacy/unclassified Activity remains Board-inspectable without fake constitutional classification;
5. malformed governance trace data fails closed;
6. WorkItem history includes creation, governed assignment effect and governance record.

## Non-claims

C.1 does not yet implement:

- AgentConversation / AgentMessage persistence;
- ToolActionRecord;
- complete ActivityLineage graph traversal;
- full DecisionLineage across Evidence / VerifiedRules / SourceSnapshots;
- blocked/review-required attempt persistence;
- Board/Cockpit HTTP transparency endpoints;
- sensitivity-tier enforcement for privileged/legal/identity/credential/personnel records;
- raw model chain-of-thought capture;
- a new transparency database schema;
- a database migration;
- Decision Readiness;
- independent verification;
- Organizational Immune System;
- canonical repository PASS;
- GitHub CI PASS.

Hidden chain-of-thought is explicitly **not** the audit mechanism. Transparency is based on structured decisions, evidence, authority, actions and durable lineage.

## Acceptance gate

From the canonical Windows V12 checkout:

```text
pytest apps/api/tests/test_organization_governance_kernel.py \
       apps/api/tests/test_organization_governed_work.py \
       apps/api/tests/test_organization_transparency.py -q

python scripts/check_repo_policy.py --root .

pytest apps/api/tests -q

python scripts/check_database_migrations.py

python scripts/check_local_db_schema.py \
  --database-url "sqlite:///D:/global-mobility-aios/gmai.db"

git diff --check
git status -sb
```

The previously protected `v10.22` roadmap regression should also remain green after the roadmap synchronization for this slice.

## Next C direction after acceptance

If C.1 passes canonical acceptance, the next transparency work should be selected based on the real vertical-slice needs. The likely next candidates are:

1. durable persistence of blocked/review-required governance attempts so rejected material actions are also inspectable;
2. explicit causation links between governance authorization and domain effect;
3. bounded Board/Cockpit transparency query contract;
4. ToolActionRecord / Evidence / decision lineage where the first real mobility case requires them.

Do not expand all of C at once.
