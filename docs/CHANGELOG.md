# Global Mobility AIOS — V12 Active Changelog

This changelog records meaningful delivery on:

```text
roadmap/global-mobility-aios-v12
```

Repository lineage:

```text
V12 fork origin
  dd2f2cd6e9e47179b1fd744ba3f56daf7c787449

Frozen V11 reference branch final documentation head
  ac130deaafa7aa44068e9459facbda2b4df327d6
```

The V12 fork origin remains `dd2f2cd`; the later `ac130dea` V11 commit only cleaned V11's own roadmap/documentation after V12 had already branched.

Earlier history remains available through V11, Git history and the archived changelogs.

> **V11 preserves the reference product checkpoint. V12 is the active implementation line.**

---

## 2026-08-20 — V1.3-C.1 TRANSPARENCY TRACE FOUNDATION — IMPLEMENTED / CANONICAL ACCEPTANCE PENDING

### Status

**The first V1.3-C transparency slice is implemented on V12. It reuses the existing durable `OrganizationActivity` substrate and must still pass canonical Windows-checkout acceptance before being marked PASS.**

Delivered commits:

```text
a05b5c9c9fd0f3b6dc70df2591cc21244cf18a44
feat: correlate governed work transparency trace

1fe877db6a4e35338a4832add23b04952e87c851
feat: start v1.3-c transparency trace foundation

7317bc35b50ed235f67b18e525bd12cf7ea8234b
test: cover v1.3-c governed transparency trace

2c0af621c76f5407cb464ee5bfad7c5387f90bdd
docs: define v1.3-c.1 transparency trace foundation

f620febbe0b69fdf0ad70b87124ff77226405e0d
docs: advance roadmap to v12.5 transparency foundation
```

### Purpose

C.1 makes the first real governed material action reconstructable without introducing a second event store or prematurely adding the entire future Transparency schema.

The governed WorkItem assignment now propagates its Governance Kernel `trace_id` into the command context used to stage the resulting semantic WorkItem Activity.

Therefore:

```text
governance.work_item.assignment.auto_execute
        +
organization.work.assigned.v1
        ↓
shared correlation / trace identity
        ↓
tenant-scoped durable query
        ↓
structured Board-inspectable reconstruction
```

### Added

```text
apps/api/app/services/organization_transparency.py
apps/api/tests/test_organization_transparency.py
docs/V1_3_C1_TRANSPARENCY_TRACE_FOUNDATION.md
```

The transparency service adds:

- `TransparencyActivityRecord`;
- `GovernedActionTrace`;
- `transparency_activity_record(...)`;
- `activities_for_trace(...)`;
- `activities_for_work_item(...)`;
- `governed_action_trace(...)`.

### Constitutional transparency behavior

V1.3 governance Activities already carry the constitutional activity class in their durable payload. C.1 applies the frozen constitutional transparency policy to those explicit classes.

For the current R1 WorkItem assignment:

```text
constitutional class       MATERIAL
Board inspectable          YES
durable record required    YES
full lineage required      YES
policy compaction           NO
```

Existing pre-V1.3/legacy Activities remain Board-inspectable but are **not silently assigned a constitutional retention/lineage class**. Unknown historical semantics stay unknown until explicitly classified.

### Fail-closed behavior

C.1 rejects ambiguous durable governance traces including:

- invalid JSON/non-object payloads;
- unsupported constitutional activity class;
- invalid trace identity;
- governance `trace_id` / `correlation_key` mismatch;
- zero or multiple governance roots for a governed trace.

### Focused tests added

Six tests cover:

- shared trace across governance authorization and resulting WorkItem effect;
- governed action reconstruction;
- tenant isolation;
- legacy/unclassified activity handling;
- malformed governance trace failure;
- WorkItem-history visibility.

No canonical pytest PASS is claimed yet. Raw-clone validation was unavailable in the assistant execution environment, so the canonical local checkout remains the acceptance source of truth.

### Non-claims

C.1 does not yet implement:

- AgentConversation / AgentMessage persistence;
- ToolActionRecord;
- complete ActivityLineage graph traversal;
- full DecisionLineage across Evidence / VerifiedRules / SourceSnapshots;
- blocked/review-required attempt persistence;
- Board/Cockpit HTTP transparency endpoints;
- sensitivity-tier enforcement;
- hidden chain-of-thought logging;
- a new transparency database schema;
- a migration;
- Decision Readiness;
- independent verification;
- Organizational Immune System;
- canonical C.1 PASS;
- GitHub CI PASS.

---

## 2026-08-20 — V1.3-B.2 GOVERNED WORKITEM ASSIGNMENT — COMPLETE / PASS / SEALED

### Status

**Canonical V12 checkout acceptance completed successfully. B.2 is sealed as the first real material domain mutation executed through the V1.3 Governance Kernel.**

Implementation commits:

```text
e21585b4d50495c6dbddd52563e60757dfd9cfc3
feat: route work assignment through governance kernel

3779a8e4507d4c98d07aa818d5e71e20c1123e8c
test: cover governed work assignment path
```

Acceptance record:

```text
58572770b482c6654d556fe1846d87d2b1233cfe
docs: seal v1.3-b.2 acceptance

docs/V1_3_B2_ACCEPTANCE_2026-08-20.md
```

### Canonical acceptance evidence

Focused B.1 + B.2 suite:

```text
25 passed, 1 warning in 3.08s
```

Repository policy:

```text
Repository policy check passed.
```

Full API regression:

```text
911 passed, 5 skipped, 1 warning in 316.36s (0:05:16)
```

Database/migration integrity:

```text
Database migration check passed.
database_url=sqlite:///./gmai.db
migration_heads=0076_organization_position_active_identity
registered_tables=118
physical_schema=ok
database_revision=0076_organization_position_active_identity
```

The local DB schema check and `git diff --check` were rerun separately after an initial PowerShell command concatenation error and were reported green/PASS. Git status was clean and synchronized with the V12 remote-tracking branch.

### Accepted behavior

```text
work_item.assignment
risk = R1
consequence = REVERSIBLE
capability = operations.work
```

B.2 proves:

- authorized R1/A4 assignment auto-executes;
- exact successful retries are idempotent after aggregate-state advancement;
- stale competing commands fail closed;
- conflicting idempotency-key reuse fails closed;
- A2 requires review and does not mutate;
- WorkItem mutation, assignment audit, semantic Activity and governance Activity remain one atomic transaction;
- governance Activity storage failure prevents an opaque autonomous mutation.

No migration or new registered domain table was required.

### Final disposition

```text
V1.3-B.2
COMPLETE
PASS
SEALED
```

Accepted API baseline after B.2:

```text
911 passed / 5 skipped / 1 warning / 0 failed
```

No GitHub CI PASS is claimed.

---

## 2026-08-20 — V1.3-B.1 MINIMAL GOVERNANCE KERNEL — COMPLETE / PASS / SEALED AS FOUNDATION

### Status

**Canonical V12 checkout acceptance is complete. B.1 is the accepted deterministic foundation for subsequent V1.3 material-action integration.**

Implementation commit:

```text
d351ad85f5c3464178b56dd9da6ac5c83090a27a
feat: start v1.3-b governance kernel
```

Dedicated acceptance record:

```text
docs/V1_3_B1_ACCEPTANCE_2026-08-20.md
```

### Canonical acceptance evidence

```text
Focused Governance Kernel    19 passed / 1 warning / 0 failed in 0.16s
Repository policy            PASS
Full API regression          905 passed / 5 skipped / 1 warning / 0 failed in 325.63s
Migration check              PASS
Migration head               0076_organization_position_active_identity
Registered tables            118
Local DB schema              PASS / 118 actual tables
Physical tables              119 incl. alembic_version
git diff --check             clean
git status                   clean / synchronized
```

B.1 accepts tenant/actor-bound `CapabilityAuthority`, capability/action/scope authority, A0–A5 routing, R0–R5 risk floors, typed `MaterialAction`, expected-version decisions, idempotency replay/conflict decisions, deterministic policy disposition, Board-reserved protection, trace identity and OrganizationActivity-compatible governance projection.

Government submission remains R5 + Board-reserved even for A5 capability autonomy.

### Final disposition

```text
V1.3-B.1
COMPLETE
PASS
SEALED AS B FOUNDATION
```

No GitHub CI PASS is claimed.

---

## 2026-08-20 — V1.3-A FINAL ACCEPTANCE — COMPLETE / PASS / SEALED

V1.3-A Constitutional Contracts is the sealed constitutional floor for V1.3 runtime work.

Implementation:

```text
7779c1f8e5d3db2e72e047667774284d7cc5f5af
feat: freeze v1.3 constitutional contracts
```

Dedicated acceptance record:

```text
docs/V1_3_A_ACCEPTANCE_2026-08-20.md
```

Canonical evidence:

```text
Constitutional tests       13 passed / 1 warning / 0 failed
Repository policy          PASS
v10.22 regression rerun    1 passed / 1 warning
Full API regression        886 passed / 5 skipped / 1 warning / 0 failed
Migration check            PASS
Migration head             0076_organization_position_active_identity
Registered tables          118
Local DB schema            PASS / 118 actual tables
git diff --check           clean
git status                 clean / synchronized
```

The historical v10.22 roadmap compatibility fix preserved:

```text
v10.22
multi-batch tranche operations
0032_initial_rule_assertions
```

No GitHub CI PASS was claimed.

---

## 2026-08-19 — V12 ROADMAP / README ALIGNMENT

V12 documentation was separated from the frozen V11 reference after the branch split.

Key commits:

```text
4a347d418408a199198832e211f13555cf1ee5e9
docs: align v12 readme with v1.3 direction

dac2529f4dee279cddc738c9310960afb32cc139
docs: establish v12 implementation roadmap

c894fba4fb3f04d992614952cafe843978011a21
docs: align v12 roadmap and changelog
```

Repository-generation distinction:

```text
Git branch V11/V12 = repository development generation
Architecture V1.3 = high-autonomy organization architecture version
Roadmap V12.x = active V12 delivery-plan generation
```

---

## 2026-08-19 — V12 DEVELOPMENT BRANCH OPENED

V12 forked from:

```text
roadmap/global-mobility-aios-v11
@ dd2f2cd6e9e47179b1fd744ba3f56daf7c787449
```

Initial branch-transition commit:

```text
2120ba7f509d9f556534d859628755e2608d2955
docs: record v12 development branch transition
```

The frozen V11 branch later received only its own documentation cleanup and remains the reference checkpoint.

---

## History before V12

Use Git history and the frozen V11 branch for exact pre-V12 state.

Existing archives include:

- `docs/archive/CHANGELOG_THROUGH_C192E7D_2026-08-19.md`;
- `docs/archive/CHANGELOG_THROUGH_F0688A8_2026-08-17.md`;
- `docs/archive/ROADMAP_V11_5_HIGH_AUTONOMY_DIRECTION_2026-08-19.md` on the final V11 reference branch.

Git history remains the immutable source for exact historical diffs and commit lineage.