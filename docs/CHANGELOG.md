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

Earlier history remains available through V11, Git history and the existing archived changelogs.

> **V11 preserves the reference product checkpoint. V12 is the active implementation line.**

---

## 2026-08-20 — V1.3-B.1 MINIMAL GOVERNANCE KERNEL — IMPLEMENTED / CANONICAL ACCEPTANCE PENDING

### Status

**First V1.3-B runtime slice implemented on V12. Isolated focused tests PASS. Canonical V12 checkout acceptance and broader API regression are not yet claimed.**

Implementation commit:

```text
d351ad85f5c3464178b56dd9da6ac5c83090a27a
feat: start v1.3-b governance kernel
```

Roadmap synchronization:

```text
64b91e1b992a2198da034a6450d3100f110ce725
docs: advance roadmap to v12.3 governance kernel
```

### Delivered

```text
apps/api/app/services/organization_governance_kernel.py
apps/api/tests/test_organization_governance_kernel.py
docs/V1_3_A_ACCEPTANCE_2026-08-20.md
docs/V1_3_B_MINIMAL_GOVERNANCE_KERNEL.md
```

### Architectural approach

The repository already contains mature command and Activity primitives, including:

- `OrganizationCommandContext`;
- tenant/actor/role validation;
- canonical JSON/fingerprints;
- idempotency helpers;
- audited command mutation utilities;
- durable `OrganizationActivity` append/stage behavior;
- trace/correlation support.

B.1 deliberately **reuses** those primitives. It does not create a second organization command framework.

### B.1 contracts

The new kernel adds:

- `CapabilityAuthority` bound to tenant, actor, capability, actions, maximum risk, autonomy and optional scope;
- typed `MaterialAction` envelope;
- constitutional risk-floor enforcement;
- expected-version/precondition decisions;
- exact idempotent replay vs conflict decisions;
- deterministic policy disposition;
- A0–A5 routing;
- Board-reserved action protection;
- stable trace identity;
- Activity projection compatible with the current OrganizationActivity runtime.

Typed gateway outcomes:

```text
AUTO_EXECUTE
BLOCK
REVIEW_REQUIRED
IDEMPOTENT_REPLAY
```

### Board-reserved invariant implemented

A government submission remains:

```text
material = yes
risk = R5
Board reserved = yes
```

and therefore routes to:

```text
REVIEW_REQUIRED
reason = BOARD_RESERVED
```

even when the actor's capability autonomy is A5.

### Autonomy behavior in this bounded slice

Only after authority, scope, risk, version, idempotency, policy and reserved-authority checks pass:

```text
A0 → BLOCK
A1 → REVIEW_REQUIRED
A2 → REVIEW_REQUIRED
A3 → AUTO_EXECUTE + post-review-required marker
A4 → AUTO_EXECUTE
A5 → AUTO_EXECUTE
```

### Activity compatibility

The current physical OrganizationActivity model predates the V1.3 constitutional activity taxonomy. B.1 therefore keeps the existing physical `operational` class and places the constitutional `MATERIAL` / `AUTHORITY` classification in the governance payload.

This avoids an unnecessary schema migration before V1.3-C formalizes Transparency and Decision Lineage.

### Isolated focused evidence

Before publication, the bounded B.1 module/test pair was validated in an isolated package layout:

```text
19 passed in 0.05s
```

Coverage includes authority mismatch, action/scope authority, risk ceiling/floor, expected/stale versions, idempotent replay/conflict, policy deny/review, A0/A2/A3 behavior, Board reservation at A5, trace-correlated Activity projection and rejection of non-material actions from the material gateway.

This is implementation evidence only. It is **not** the final repository acceptance result.

### Non-claims

B.1 does not yet:

- execute a production domain mutation through the new gateway;
- persist a new `MaterialAction` table;
- add a database migration;
- change the 118 registered domain tables;
- replace existing route authorization;
- replace existing organization command services;
- implement Decision Readiness;
- implement independent verification;
- implement contradiction detection;
- implement the Organizational Immune System;
- implement earned-autonomy promotion/demotion;
- implement full Transparency / Decision Lineage;
- authorize government submission automatically;
- claim a canonical B.1 full API PASS;
- claim GitHub CI PASS.

### Next acceptance

From the canonical V12 checkout after pulling the B.1 commit:

```text
pytest apps/api/tests/test_organization_governance_kernel.py -q
scripts/check_repo_policy.py --root .
pytest apps/api/tests -q
git diff --check
git status -sb
```

Migration head is expected to remain:

```text
0076_organization_position_active_identity
```

After clean canonical acceptance, B.2 should wire one existing reversible low-risk organization command through the kernel and existing Activity path.

---

## 2026-08-20 — V1.3-A FINAL ACCEPTANCE — COMPLETE / PASS / SEALED

### Status

**V1.3-A Constitutional Contracts has completed canonical repository acceptance and is sealed as the constitutional floor for subsequent V1.3 runtime work.**

Dedicated record:

```text
docs/V1_3_A_ACCEPTANCE_2026-08-20.md
```

### Canonical acceptance evidence

Focused constitutional tests:

```text
13 passed, 1 warning in 0.14s
```

Repository policy:

```text
Repository policy check passed.
```

Previously failing v10.22 roadmap regression after the V12.2 compatibility correction:

```text
1 passed, 1 warning in 0.08s
```

Full API regression:

```text
886 passed, 5 skipped, 1 warning in 337.70s (0:05:37)
```

Database migration integrity:

```text
Database migration check passed.
database_url=sqlite:///./gmai.db
migration_heads=0076_organization_position_active_identity
registered_tables=118
physical_schema=ok
database_revision=0076_organization_position_active_identity
```

Preserved local database schema parity:

```text
Local DB schema check passed.
database_url=sqlite:///D:/global-mobility-aios/gmai.db
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

### Warning disposition

One Starlette/httpx TestClient deprecation warning remains. It is non-blocking for V1.3-A and should be handled in a separate dependency-maintenance task rather than changing dependencies inside the governance phase.

### Final disposition

```text
V1.3-A — Constitutional Contracts
COMPLETE
PASS
SEALED
```

No GitHub CI PASS is claimed because no attached check/status evidence was used for this acceptance.

---

## 2026-08-19 — V1.3-A BROADER ACCEPTANCE — ROADMAP COMPATIBILITY REGRESSION IDENTIFIED AND FIXED / RERUN PENDING

### Status

**Historical intermediate checkpoint.** Constitutional contract tests and repository policy passed, while the first broader API regression exposed one documentation-roadmap compatibility failure. That failure was corrected in Roadmap V12.2 and subsequently verified by the final acceptance recorded above.

### Intermediate evidence

```text
pytest apps/api/tests/test_organization_constitution.py -q
13 passed, 1 warning in 0.14s

scripts/check_repo_policy.py --root .
Repository policy check passed.

pytest apps/api/tests -q
885 passed, 5 skipped, 1 failed, 1 warning in 334.06s
```

The sole failure was:

```text
apps/api/tests/test_coverage_tranche_operations_script.py::
test_v10_22_documentation_and_roadmap_are_present
```

The regression required the roadmap to preserve:

```text
v10.22
multi-batch tranche operations
0032_initial_rule_assertions
```

Roadmap V12.2 restored those historical continuity markers in commit:

```text
2f1fe6774e8681cc98448680b1a8e315d8ebe4a0
docs: restore v10.22 roadmap compatibility milestone
```

This checkpoint is superseded by the 2026-08-20 final V1.3-A PASS above.

---

## 2026-08-19 — V1.3-A CONSTITUTIONAL CONTRACTS — IMPLEMENTED / FOCUSED TEST PASS

### Status

**Initial runtime-facing contract implementation checkpoint.** Later canonical acceptance is recorded above.

Implementation commit:

```text
7779c1f8e5d3db2e72e047667774284d7cc5f5af
feat: freeze v1.3 constitutional contracts
```

### Purpose

Started the actual V12 Track C implementation with:

> **V1.3-A — Constitutional Contracts**

Added:

```text
apps/api/app/core/organization_constitution.py
apps/api/tests/test_organization_constitution.py
docs/ORGANIZATION_CONSTITUTIONAL_CONTRACTS_V1_3.md
```

The contract freezes Board supremacy, Board Transparency, **scores route; deterministic gates authorize**, A0–A5, R0–R5, `HumanReviewReason`, consequence/recovery classes, reserved authority, the Materiality Registry and activity transparency policy.

Initial isolated focused evidence was:

```text
13 passed in 0.07s
```

The canonical checkout later produced `13 passed, 1 warning in 0.14s` and the complete V1.3-A acceptance described above.

---

## 2026-08-19 — V12 ROADMAP / README ALIGNMENT

### Status

Documentation/branch-alignment checkpoint only.

V12 was created directly from the V11 checkpoint at `dd2f2cd`. The inherited README and roadmap initially still described V11 as the active line, so V12 documentation was realigned to make the branch roles explicit.

Key commits:

```text
4a347d418408a199198832e211f13555cf1ee5e9
docs: align v12 readme with v1.3 direction

dac2529f4dee279cddc738c9310960afb32cc139
docs: establish v12 implementation roadmap

c894fba4fb3f04d992614952cafe843978011a21
docs: align v12 roadmap and changelog
```

Resulting distinction:

```text
Git branch V11/V12 = repository development generation
Architecture V1.3 = high-autonomy organization architecture version
Roadmap V12.x = active V12 delivery-plan generation
```

No runtime/database/acceptance state changed in those documentation commits.

---

## 2026-08-19 — V12 DEVELOPMENT BRANCH OPENED

V12 was created from:

```text
roadmap/global-mobility-aios-v11
@ dd2f2cd6e9e47179b1fd744ba3f56daf7c787449
```

Initial V12 branch transition commit:

```text
2120ba7f509d9f556534d859628755e2608d2955
docs: record v12 development branch transition
```

The branch split exists so V1.3 implementation can proceed without risking the preserved V11 product/runtime reference.

---

## History before V12

Use Git history and the frozen V11 branch for exact pre-V12 state.

Existing archives include:

- `docs/archive/CHANGELOG_THROUGH_C192E7D_2026-08-19.md`;
- `docs/archive/CHANGELOG_THROUGH_F0688A8_2026-08-17.md`;
- `docs/archive/ROADMAP_V11_5_HIGH_AUTONOMY_DIRECTION_2026-08-19.md` on the final V11 reference branch.

Git history remains the immutable source for exact historical diffs and commit lineage.
