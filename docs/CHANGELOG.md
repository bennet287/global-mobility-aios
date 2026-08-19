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

## 2026-08-20 — V1.3-C.2 NON-EXECUTING MATERIAL ATTEMPT TRANSPARENCY — IMPLEMENTED / CANONICAL ACCEPTANCE PENDING

### Status

**The second V1.3-C slice is implemented on V12. Material actions that are blocked or routed to review can now be persisted as trace-scoped governance attempts without changing the sealed B.2 successful-command semantics. Canonical Windows-checkout acceptance is still required before C.2 is marked PASS.**

Implementation history:

```text
3348d1779e45a91020bad1a548627d07c2100519
feat: persist non-executing governance attempts

596688c7d9016869865fa30290057537994bc5a0
fix: preserve requested governance attempt context

e34a32f7ebf1bf4efe9937177ebda8d02698d57b
test: cover non-executing governance transparency

b5025836f1544a67a0a3136594c5b8e60ecaa1bd
docs: define v1.3-c.2 attempt transparency

504aed7fc21457203e4c68864abffcfbe7cff6f4
docs: advance roadmap to v12.6 attempt transparency
```

The first `3348d177` commit was an intermediate implementation checkpoint. `596688c7` corrected the facade before canonical acceptance by preserving the actual requested assignment target, expected version and reason in the durable attempt context. The corrected head is the implementation truth.

### Delivered

```text
apps/api/app/services/organization_governed_work_transparency.py
apps/api/tests/test_organization_transparency_attempts.py
docs/V1_3_C2_NON_EXECUTING_ATTEMPT_TRANSPARENCY.md
```

### Purpose

C.1 made successful material execution reconstructable. C.2 ensures important non-executing material attempts do not disappear:

```text
Material action attempt
        ↓
Governance Kernel
        ↓
BLOCK or REVIEW_REQUIRED
        ↓
NO domain mutation
        +
trace-scoped governance Attempt Activity
        ↓
Board-inspectable reconstruction
```

### B.2 compatibility

C.2 does not rewrite the sealed B.2 command service. It adds a transparency facade over `governed_assign_work_item(...)`.

For:

```text
AUTO_EXECUTE
IDEMPOTENT_REPLAY
```

B.2 behavior remains authoritative.

For:

```text
BLOCK
REVIEW_REQUIRED
```

C.2 appends a separate durable attempt record.

### Idempotency separation

Successful-command identity remains:

```text
governance:<idempotency_key>
```

Non-executing attempt identity is:

```text
governance:attempt:<trace_id>
```

This prevents a past denial/review result from masquerading as a successful-command replay record after legitimate authority or policy changes.

### Attempt context

The attempt payload preserves structured action/governance metadata including the outcome, governance reason, constitutional Activity class, risk, consequence class, HumanReviewReason, action fingerprint, trace ID, requested idempotency key, requested target, expected version and reason.

Hidden model chain-of-thought is not stored.

### Focused tests added

Five focused tests cover:

1. A2 `REVIEW_REQUIRED` visibility without mutation;
2. stale-version `BLOCK` visibility without changing accepted WorkItem state;
3. scope-denied attempt visibility;
4. a review attempt not poisoning later successful-command idempotency after legitimate authority increase;
5. fail-closed attempt-Activity storage behavior.

No canonical pytest PASS is claimed yet.

### Non-claims

C.2 does not yet implement a generic MaterialAction table, Board/Cockpit HTTP transparency endpoints, Board notification policy, repeated-attempt aggregation, AgentConversation/AgentMessage persistence, ToolActionRecord, Evidence/Rule/SourceSnapshot DecisionLineage, sensitivity-tier filtering, Decision Readiness, independent verification, the Organizational Immune System, or GitHub CI PASS.

---

## 2026-08-20 — V1.3-C.1 TRANSPARENCY TRACE FOUNDATION — COMPLETE / PASS / SEALED

### Status

**Canonical V12 checkout acceptance completed successfully. C.1 is sealed as the first accepted Transparency foundation.**

Implementation commits:

```text
a05b5c9c9fd0f3b6dc70df2591cc21244cf18a44
feat: correlate governed work transparency trace

1fe877db6a4e35338a4832add23b04952e87c851
feat: start v1.3-c transparency trace foundation

7317bc35b50ed235f67b18e525bd12cf7ea8234b
test: cover v1.3-c governed transparency trace

2c0af621c76f5407cb464ee5bfad7c5387f90bdd
docs: define v1.3-c.1 transparency trace foundation
```

Acceptance record:

```text
c7f90c9ff2b7e73d882d648e5267ef6731c5663d
docs: seal v1.3-c.1 acceptance

docs/V1_3_C1_ACCEPTANCE_2026-08-20.md
```

Canonical evidence:

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

Accepted behavior includes shared governance/effect trace correlation, tenant-scoped Activity queries, `GovernedActionTrace` reconstruction, explicit constitutional transparency semantics when durable governance payload carries them, no fabricated classification for legacy Activity, fail-closed malformed trace handling, and WorkItem-history visibility.

Accepted API baseline after C.1:

```text
917 passed / 5 skipped / 1 warning / 0 failed
```

No GitHub CI PASS is claimed.

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

Canonical evidence:

```text
Focused B.1+B.2          25 passed / 1 warning / 0 failed in 3.08s
Repository policy        PASS
Full API regression      911 passed / 5 skipped / 1 warning / 0 failed in 316.36s
Migration check          PASS
Migration head           0076_organization_position_active_identity
Registered tables        118
Local DB schema          PASS
git diff --check         clean
git status               clean / synchronized
```

Accepted behavior:

- authorized R1/A4 WorkItem assignment auto-executes;
- exact successful retries remain idempotent after aggregate-state advancement;
- stale competing commands fail closed;
- conflicting idempotency-key reuse fails closed;
- A2 requires review and cannot mutate;
- mutation, assignment audit, semantic Activity and governance Activity remain one atomic transaction;
- governance Activity storage failure prevents an opaque autonomous mutation.

No migration or new registered domain table was required.

---

## 2026-08-20 — V1.3-B.1 MINIMAL GOVERNANCE KERNEL — COMPLETE / PASS / SEALED AS FOUNDATION

Implementation:

```text
d351ad85f5c3464178b56dd9da6ac5c83090a27a
feat: start v1.3-b governance kernel
```

Canonical evidence:

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

See `docs/V1_3_B1_ACCEPTANCE_2026-08-20.md`.

---

## 2026-08-20 — V1.3-A CONSTITUTIONAL CONTRACTS — COMPLETE / PASS / SEALED

Implementation:

```text
7779c1f8e5d3db2e72e047667774284d7cc5f5af
feat: freeze v1.3 constitutional contracts
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

The historical roadmap compatibility correction preserved:

```text
v10.22
multi-batch tranche operations
0032_initial_rule_assertions
```

See `docs/V1_3_A_ACCEPTANCE_2026-08-20.md`.

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
