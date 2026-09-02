# V1.3-C.1 — Transparency Trace Foundation

**Date:** 2026-08-20  
**Branch:** `roadmap/global-mobility-aios-v12`  
**State:** **COMPLETE / PASS / SEALED**

## Purpose

C.1 starts the V1.3 Transparency Foundation by making the first real governed material action reconstructable from the durable organization Activity substrate that already exists.

Accepted shape:

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

It deliberately does not introduce a second event store or prematurely add conversation/tool/decision-lineage tables.

## Existing substrate reused

`OrganizationActivity` already provides tenant ownership, durable activity identity, streams/sequences, actor context, department/position/authority, source identity/version, WorkItem links, correlation keys, causation/supersession fields, payload fingerprints and timestamps.

C.1 builds a typed transparency projection/query layer over this accepted substrate.

## Runtime changes

The B.2 governed WorkItem assignment propagates the Governance Kernel `trace_id` into the command context used to stage the resulting semantic WorkItem Activity.

Therefore:

```text
organization.work.assigned.v1
```

and:

```text
governance.work_item.assignment.auto_execute
```

share one durable correlation identity.

Added:

```text
apps/api/app/services/organization_transparency.py
apps/api/tests/test_organization_transparency.py
```

The transparency service provides:

- `TransparencyActivityRecord`;
- `GovernedActionTrace`;
- `transparency_activity_record(...)`;
- `activities_for_trace(...)`;
- `activities_for_work_item(...)`;
- `governed_action_trace(...)`.

## Constitutional classification

V1.3 Governance Activities carry their constitutional class explicitly in durable payload:

```text
MATERIAL
AUTHORITY
```

C.1 reads that class and applies the frozen constitutional transparency policy.

For the governed WorkItem assignment (`MATERIAL`):

```text
Board inspectable       YES
Durable record required YES
Full lineage required   YES
Policy compaction       NO
```

Existing pre-V1.3 Activities remain Board-inspectable but are not silently assigned fake constitutional retention/lineage semantics.

## Fail-closed rules

C.1 rejects ambiguous durable governance data including invalid/non-object payload JSON, unsupported constitutional Activity classes, invalid trace identity, governance trace/correlation mismatch, and governed traces with zero or multiple governance roots.

All trace and WorkItem-history queries are tenant-scoped at the database boundary.

## Canonical acceptance

Dedicated record:

```text
docs/V1_3_C1_ACCEPTANCE_2026-08-20.md
```

Canonical Windows V12 evidence:

```text
Focused B.1+B.2+C.1     31 passed / 1 warning / 0 failed in 5.40s
Repository policy        PASS
Full API regression      917 passed / 5 skipped / 1 warning / 0 failed in 317.64s
Migration check          PASS
Migration head           0076_organization_position_active_identity
Registered tables        118
Local DB schema          PASS / 118 actual tables
Physical tables          119 incl. alembic_version
git diff --check         clean
git status               clean / synchronized
```

The warning remains the pre-existing Starlette/httpx TestClient deprecation warning.

## Preserved boundaries

C.1 does not implement AgentConversation/AgentMessage persistence, ToolActionRecord, complete ActivityLineage graph traversal, Evidence/VerifiedRule/SourceSnapshot DecisionLineage, Board/Cockpit HTTP transparency endpoints, sensitivity-tier enforcement, hidden chain-of-thought capture, a new transparency schema, or a migration.

## Final disposition

```text
V1.3-C.1 — Transparency Trace Foundation
COMPLETE
PASS
SEALED
```

C.2 proceeds with durable visibility for `BLOCK` and `REVIEW_REQUIRED` material attempts.
