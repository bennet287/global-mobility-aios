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

## 2026-08-20 — V1.3-C.4 BOARD/COCKPIT TRANSPARENCY READ CONTRACT — IMPLEMENTED / CANONICAL ACCEPTANCE PENDING

### Status

**The fourth V1.3-C slice is implemented on V12. The first governed material-action trace can now be read through a bounded, authenticated Board-facing API contract without exposing arbitrary raw Activity/governance payloads. Canonical Windows-checkout acceptance is still required before C.4 is marked PASS.**

Implementation commits:

```text
4c8267bfa91e7cdc38b6e485792d72bdd39b3df3
feat: add board transparency read schemas

b9d59d403bfb53efdc2f235478ba5e0c31d67639
feat: add board transparency read contract

a17d81b6ad5af6259c40f1bd6c4184b944e37a8b
feat: register organization transparency router

40e04a86b06dc2e0e3b1a573c17d6cad67a03e92
test: cover board transparency read contract

f7572eb491e33bca2175f64eb99c701c7fd956f0
docs: define v1.3-c.4 board transparency contract

01ea83594938b5b819e17a40025ed04e1343ab96
docs: advance roadmap to v12.8 board transparency
```

### Product-facing API

Added under the existing organization API namespace:

```text
GET /api/v1/organization/transparency/traces/{trace_id}
GET /api/v1/organization/transparency/work-items/{work_item_id}
```

The router is registered through the canonical router registry rather than creating a parallel application surface.

### Board-safe projection

The trace endpoint returns a typed, whitelisted governance decision projection including:

- action type and capability;
- gateway outcome/reason;
- effective risk tier and consequence class;
- human-review/post-review semantics;
- constitutional Activity class;
- actor/department/position/authority context;
- source and WorkItem identity;
- action fingerprint and idempotency key;
- timestamp.

The associated records expose bounded Activity metadata, trace identity and explicit `causation_activity_id`.

Raw internal payload JSON is **not** part of the response schema.

### Current access boundary

C.4 is deliberately limited to the existing trusted:

```text
role = admin
position_key = board
```

mapping. Other authenticated organization roles receive `403`.

This is not claimed as final sensitivity/retention/privilege policy. Broader access remains deferred until explicit data-class policy exists.

### Tenant and integrity behavior

C.4 preserves strict tenant isolation. Foreign trace IDs and foreign WorkItems are non-disclosing.

Malformed durable governance data fails closed with a safe `409` response instead of returning persistence details or traceback content.

### Focused tests added

Five API-level tests cover:

1. Board trace reads expose whitelisted governance semantics and C.3 explicit causation;
2. non-Board authenticated roles are denied;
3. trace reads remain tenant-scoped and non-disclosing;
4. WorkItem transparency history is bounded and rejects foreign/missing WorkItems;
5. malformed governance data fails closed without leaking internals.

No canonical pytest PASS is claimed yet.

### Non-claims

C.4 does not yet implement:

- Cockpit UI rendering;
- generalized organization-wide search;
- final sensitivity/privilege policy;
- ToolActionRecord;
- AgentConversation / AgentMessage transparency;
- Evidence/VerifiedRule/SourceSnapshot decision lineage;
- a migration;
- canonical C.4 PASS;
- GitHub CI PASS.

See `docs/V1_3_C4_BOARD_TRANSPARENCY_READ_CONTRACT.md`.

---

## 2026-08-20 — V1.3-C.3 EXPLICIT GOVERNANCE → EFFECT CAUSATION — COMPLETE / PASS / SEALED

### Status

**Canonical C.3 acceptance was reported all green by the Human Owner from the prescribed Windows V12 checkout sequence. Exact final pytest counts were not restated, so they are not invented.**

Implementation commits:

```text
d40e5a2aa7b662129d674851f2854f29a6d635c8
feat: link governed work effect to authorization

ef28c75a457a298e3194a8ae3ce0ed4638ab30e6
test: cover explicit governance effect causation

e05c8da5892cecc108af632ceef16906f9208b63
docs: define v1.3-c.3 explicit causation
```

Acceptance record:

```text
3c0cca1dc4fa0526ac04a8f60efd8370bf090683
docs: seal v1.3-c.3 acceptance

docs/V1_3_C3_ACCEPTANCE_2026-08-20.md
```

### Accepted behavior

The successful governed WorkItem path now records explicit authorization-to-effect lineage:

```text
Governance authorization Activity
        │
        │ activity.id
        ▼
organization.work.assigned.v1
causation_activity_id = governance Activity id
```

Accepted properties:

- governance authorization is staged first inside the atomic unit;
- WorkItem mutation, audit and semantic effect remain in the same transaction;
- the effect explicitly points to its governance cause;
- trace correlation remains intact;
- exact successful replay does not duplicate the causal chain;
- effect-storage failure rolls back authorization and mutation together;
- no migration/new domain table was required.

### Canonical acceptance truth

The prescribed C.3 sequence covered:

- `v10.22` roadmap compatibility regression;
- focused B.1/B.2/C.1/C.2/C.3 suite;
- repository policy;
- full API regression;
- migration check;
- local schema check;
- `git diff --check`;
- clean/synchronized status.

The Human Owner reported all checks green. Exact final counts were not restated and are therefore deliberately omitted.

The last separately evidenced API baseline before C.3 remains C.2's `922 passed / 5 skipped / 1 warning / 0 failed`; it is not relabeled as a C.3 result.

No GitHub CI PASS is claimed.

---

## 2026-08-20 — V1.3-C.2 NON-EXECUTING MATERIAL ATTEMPT TRANSPARENCY — COMPLETE / PASS / SEALED

### Status

**C.2 is sealed. Material governance attempts that are blocked or routed to review remain durable and Board-inspectable even when no domain mutation occurs.**

Accepted API evidence:

```text
Repository policy             PASS
Full API regression           922 passed / 5 skipped / 1 warning / 0 failed in 320.37s
Migration check               PASS
Migration head                0076_organization_position_active_identity
Registered tables             118
Local DB schema               PASS / 118 actual tables
Physical tables               119 incl. alembic_version
git diff --check              clean
git status                    clean / synchronized
```

The focused C.2 chain and protected roadmap regression were reported green; exact focused counts were not restated and are not invented.

### Accepted behavior

```text
BLOCK / REVIEW_REQUIRED
        ↓
NO domain mutation
        +
durable governance-attempt Activity
        ↓
Board-inspectable trace
```

Successful-command idempotency remains:

```text
governance:<idempotency_key>
```

Attempt identity remains:

```text
governance:attempt:<trace_id>
```

This prevents denied/review attempts from poisoning later legitimate successful-command replay semantics.

See `docs/V1_3_C2_NON_EXECUTING_ATTEMPT_TRANSPARENCY.md` and `docs/V1_3_C2_ACCEPTANCE_2026-08-20.md`.

---

## 2026-08-20 — V1.3-C.1 TRANSPARENCY TRACE FOUNDATION — COMPLETE / PASS / SEALED

### Status

**C.1 established the accepted tenant-scoped durable transparency projection over the existing `OrganizationActivity` substrate.**

Canonical evidence:

```text
Focused B.1+B.2+C.1          31 passed / 1 warning / 0 failed in 5.40s
Repository policy             PASS
Full API regression           917 passed / 5 skipped / 1 warning / 0 failed in 317.64s
Migration check               PASS
Migration head                0076_organization_position_active_identity
Registered tables             118
Local DB schema               PASS / 118 actual tables
Physical tables               119 incl. alembic_version
git diff --check              clean
git status                    clean / synchronized
```

Accepted behavior includes shared trace correlation across governance authorization and WorkItem effect, typed Board-inspectable reconstruction, tenant isolation, legacy/unclassified Activity treatment without fake constitutional semantics, fail-closed malformed trace handling, and WorkItem history visibility.

See `docs/V1_3_C1_TRANSPARENCY_TRACE_FOUNDATION.md` and `docs/V1_3_C1_ACCEPTANCE_2026-08-20.md`.

---

## 2026-08-20 — V1.3-B.2 GOVERNED WORKITEM ASSIGNMENT — COMPLETE / PASS / SEALED

### Status

**B.2 is sealed as the first real material domain mutation executed through the V1.3 Governance Kernel.**

Implementation commits:

```text
e21585b4d50495c6dbddd52563e60757dfd9cfc3
feat: route work assignment through governance kernel

3779a8e4507d4c98d07aa818d5e71e20c1123e8c
test: cover governed work assignment path
```

Canonical evidence:

```text
Focused B.1 + B.2             25 passed / 1 warning / 0 failed in 3.08s
Repository policy             PASS
Full API regression           911 passed / 5 skipped / 1 warning / 0 failed in 316.36s
Migration check               PASS
Migration head                0076_organization_position_active_identity
Registered tables             118
Local DB schema               PASS
git diff --check              clean
git status                    clean / synchronized
```

Accepted behavior:

- authorized R1/A4 assignment auto-executes;
- exact successful retries are idempotent after aggregate-state advancement;
- stale competing commands fail closed;
- conflicting idempotency-key reuse fails closed;
- A2 requires review and does not mutate;
- WorkItem mutation, assignment audit, semantic Activity and governance Activity are atomic;
- governance Activity storage failure prevents an opaque autonomous mutation.

No migration or new registered domain table was required.

---

## 2026-08-20 — V1.3-B.1 MINIMAL GOVERNANCE KERNEL — COMPLETE / PASS / SEALED AS FOUNDATION

### Status

**B.1 is the accepted deterministic foundation for subsequent V1.3 material-action integration.**

Implementation:

```text
d351ad85f5c3464178b56dd9da6ac5c83090a27a
feat: start v1.3-b governance kernel
```

Canonical evidence:

```text
Focused Governance Kernel     19 passed / 1 warning / 0 failed in 0.16s
Repository policy             PASS
Full API regression           905 passed / 5 skipped / 1 warning / 0 failed in 325.63s
Migration check               PASS
Migration head                0076_organization_position_active_identity
Registered tables             118
Local DB schema               PASS / 118 actual tables
Physical tables               119 incl. alembic_version
git diff --check              clean
git status                    clean / synchronized
```

B.1 accepts tenant/actor-bound `CapabilityAuthority`, capability/action/scope authority, A0–A5 routing, R0–R5 risk floors, typed `MaterialAction`, expected-version decisions, idempotency replay/conflict decisions, deterministic policy disposition, Board-reserved protection, trace identity and `OrganizationActivity`-compatible governance projection.

Government submission remains R5 + Board-reserved even for A5 capability autonomy.

---

## 2026-08-20 — V1.3-A CONSTITUTIONAL CONTRACTS — COMPLETE / PASS / SEALED

Implementation:

```text
7779c1f8e5d3db2e72e047667774284d7cc5f5af
feat: freeze v1.3 constitutional contracts
```

Canonical evidence:

```text
Constitutional tests          13 passed / 1 warning / 0 failed
Repository policy             PASS
v10.22 regression rerun       1 passed / 1 warning
Full API regression           886 passed / 5 skipped / 1 warning / 0 failed
Migration check               PASS
Migration head                0076_organization_position_active_identity
Registered tables             118
Local DB schema               PASS / 118 actual tables
git diff --check              clean
git status                    clean / synchronized
```

The historical roadmap compatibility repair permanently preserves:

```text
v10.22
multi-batch tranche operations
0032_initial_rule_assertions
```

No GitHub CI PASS was claimed.

---

## 2026-08-19 — V12 ROADMAP / README ALIGNMENT

V12 documentation was separated from the frozen V11 reference after the branch split.

Representative alignment commits:

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
