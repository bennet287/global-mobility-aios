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

## 2026-08-20 — V1.3-B.2 GOVERNED WORKITEM ASSIGNMENT — IMPLEMENTED / CANONICAL ACCEPTANCE PENDING

### Status

**The first real existing organization mutation is now wired through the V1.3 Governance Kernel on V12. Canonical Windows-checkout acceptance is still required before B.2 is marked PASS.**

Delivered commits:

```text
e21585b4d50495c6dbddd52563e60757dfd9cfc3
feat: route work assignment through governance kernel

3779a8e4507d4c98d07aa818d5e71e20c1123e8c
test: cover governed work assignment path

a8c3f0f9d7a116238d8466aafb5c4062fbd2bf11
docs: seal v1.3-b.1 acceptance

9b554f7b253f9552c243e88f11e6adbfa8c55cda
docs: define v1.3-b.2 governed work slice
```

### Bounded action selected

```text
work_item.assignment
risk = R1
consequence = REVERSIBLE
capability = operations.work
```

B.2 deliberately starts with a low-risk reversible operation instead of pushing the new gateway directly into certification, eligibility or external/government actions.

### Runtime path

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
existing organization.work.assign audit
        +
existing semantic assignment Activity
        +
Governance Activity / trace
        ↓
ONE TRANSACTION COMMIT
```

### New runtime adapter

```text
apps/api/app/services/organization_governed_work.py
```

The adapter composes the accepted B.1 kernel with existing `OrganizationalWorkItem`, audit and semantic-Activity primitives. It does not add a parallel WorkItem model or a second organization command framework.

### Precondition compatibility

The current WorkItem schema does not expose a dedicated integer aggregate-version column. B.2 therefore derives the first governed precondition token from canonical `updated_at` without adding a migration.

A successful assignment advances `updated_at`; a new command carrying the old precondition is therefore stale and blocked.

This is a bounded compatibility bridge. A later explicit aggregate-version migration should only be introduced if broader runtime evidence justifies it.

### Durable retry correction

A successful action changes the aggregate and therefore changes its precondition. An exact retry must not become a false stale-version failure simply because the first attempt succeeded.

The persisted B.2 flow therefore resolves an existing durable governance fingerprint before applying the stale-precondition decision to a new command:

```text
exact same idempotency key + same action fingerprint
→ IDEMPOTENT_REPLAY

same idempotency key + different action fingerprint
→ BLOCK / IDEMPOTENCY_CONFLICT

new idempotency key + stale expected version
→ BLOCK / STALE_VERSION
```

Authority/capability/scope/risk checks remain mandatory before the replay path.

### Atomicity invariant

For `AUTO_EXECUTE`, WorkItem mutation, assignment audit, semantic WorkItem Activity and governance Activity are staged inside one transaction. If governance Activity storage fails, the assignment/audit/activity unit rolls back rather than allowing an autonomous mutation to become opaque.

### Focused tests added

```text
apps/api/tests/test_organization_governed_work.py
```

The six new tests cover:

- real R1 assignment AUTO_EXECUTE;
- governance trace correlation and assignment audit;
- exact durable replay after state/precondition advancement;
- stale competing-command rejection;
- conflicting idempotency-key reuse rejection;
- A2 review-required behavior without mutation;
- rollback of assignment/audit/Activity when governance Activity persistence fails.

### Non-claims

B.2 does not yet:

- expose the governed assignment through a public HTTP route;
- route every WorkItem transition through MaterialAction;
- persist blocked/review-only attempts as the final Transparency model;
- add a MaterialAction table;
- add a database migration;
- implement Decision Readiness;
- implement independent R3+ verification;
- implement the Organizational Immune System;
- implement earned-autonomy promotion/demotion;
- implement V1.3-C Transparency Foundation;
- claim canonical B.2 PASS;
- claim GitHub CI PASS.

Canonical acceptance commands are documented in `docs/V1_3_B2_GOVERNED_WORK_ASSIGNMENT.md`.

---

## 2026-08-20 — V1.3-B.1 MINIMAL GOVERNANCE KERNEL — COMPLETE / PASS / SEALED AS FOUNDATION

### Status

**Canonical V12 checkout acceptance is complete. B.1 is now the accepted deterministic foundation for subsequent V1.3-B integration slices.**

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

Focused Governance Kernel suite:

```text
19 passed, 1 warning in 0.16s
```

Repository policy:

```text
Repository policy check passed.
```

Full API regression:

```text
905 passed, 5 skipped, 1 warning in 325.63s (0:05:25)
```

Database/migration integrity:

```text
Database migration check passed.
migration_heads=0076_organization_position_active_identity
registered_tables=118
physical_schema=ok
database_revision=0076_organization_position_active_identity
```

Local preserved DB parity:

```text
Local DB schema check passed.
registered_tables=118
actual_tables=118
physical_tables=119
infrastructure_tables=["alembic_version"]
```

Git integrity:

```text
git diff --check
# no output

git status -sb
## roadmap/global-mobility-aios-v12...origin/roadmap/global-mobility-aios-v12
```

### Accepted B.1 foundation

B.1 accepts:

- tenant/actor-bound `CapabilityAuthority`;
- capability/action/scope authority;
- A0–A5 autonomy routing;
- R0–R5 constitutional risk-floor enforcement;
- typed `MaterialAction` envelope;
- expected-version/precondition decisions;
- idempotency replay/conflict decisions;
- deterministic policy disposition;
- Board-reserved protection;
- stable trace identity;
- OrganizationActivity-compatible governance projection.

Government submission remains R5 + Board-reserved even for A5 capability autonomy.

### Warning disposition

The single warning remains the pre-existing Starlette/httpx TestClient deprecation warning and is not a B.1 regression.

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
