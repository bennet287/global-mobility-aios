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

## 2026-08-19 — V1.3-A BROADER ACCEPTANCE — ROADMAP COMPATIBILITY REGRESSION IDENTIFIED AND FIXED / RERUN PENDING

### Status

**Constitutional contract tests PASS. Repository policy PASS. Broader API regression exposed one documentation-roadmap compatibility failure; the roadmap has been corrected and the broader suite must be rerun before V1.3-A is sealed PASS.**

### Canonical local acceptance evidence

Reported from the canonical Windows V12 checkout:

```text
pytest apps/api/tests/test_organization_constitution.py -q
13 passed, 1 warning in 0.14s
```

Repository policy:

```text
scripts/check_repo_policy.py --root .
Repository policy check passed.
```

Broader API regression:

```text
pytest apps/api/tests -q
885 passed, 5 skipped, 1 failed, 1 warning in 334.06s
```

### Sole failing test

```text
apps/api/tests/test_coverage_tranche_operations_script.py::
test_v10_22_documentation_and_roadmap_are_present
```

Failure condition:

```text
assert "v10.22" in roadmap
```

The same protected regression also requires the active roadmap to retain:

```text
multi-batch tranche operations
0032_initial_rule_assertions
```

### Root cause

The V12 roadmap rewrite correctly preserved the active product/architecture direction, but accidentally removed selected historical Phase 10.22 markers that are intentionally encoded as repository continuity contracts.

The underlying v10.22 implementation documentation remained present at:

```text
docs/COVERAGE_TRANCHE_OPERATIONS_V10_22.md
```

and the failure did not indicate a defect in the new constitutional contract module.

### Fix

Roadmap advanced to **V12.2** and now preserves a concise historical compatibility section documenting:

- `v10.22`;
- **multi-batch tranche operations**;
- preserved human-review / no-automatic-certification boundaries;
- canonical v10.22 operations documentation;
- historical migration marker `0032_initial_rule_assertions`.

Roadmap fix commit:

```text
2f1fe6774e8681cc98448680b1a8e315d8ebe4a0
docs: restore v10.22 roadmap compatibility milestone
```

### Acceptance posture

V1.3-A remains:

```text
IMPLEMENTED
FOCUSED CONTRACT TEST PASS
REPOSITORY POLICY PASS
BROADER API RERUN PENDING
```

It is **not** yet sealed PASS.

Required next evidence:

1. pull the latest V12 head;
2. rerun `test_v10_22_documentation_and_roadmap_are_present`;
3. rerun the complete API test suite;
4. confirm migration/schema invariants;
5. confirm clean repository state;
6. record the final exact results before starting V1.3-B runtime delivery.

### Runtime truth

This roadmap compatibility correction does not:

- change application behavior;
- change database schema;
- change migration head `0076_organization_position_active_identity`;
- mutate preserved `gmai.db`;
- change route authorization;
- implement the Governance Kernel;
- implement Decision Readiness;
- implement the Organizational Immune System;
- resolve Phase 13.17 findings;
- establish GitHub CI PASS.

---

## 2026-08-19 — V1.3-A CONSTITUTIONAL CONTRACTS — IMPLEMENTED / FOCUSED TEST PASS

### Status

**Runtime-facing contract implementation delivered. Focused contract tests PASS. Full repository regression/CI PASS is not claimed at this checkpoint.**

Implementation commit:

```text
7779c1f8e5d3db2e72e047667774284d7cc5f5af
feat: freeze v1.3 constitutional contracts
```

### Purpose

Started the actual V12 Track C implementation with the first roadmap slice:

> **V1.3-A — Constitutional Contracts**

The existing runtime already has deterministic route/role authorization and organization-governance schemas, but future V1.3 concepts still needed a single machine-readable vocabulary before the Governance Kernel could safely use them.

This slice freezes the constitutional vocabulary without prematurely changing current API/database behavior.

### Added

```text
apps/api/app/core/organization_constitution.py
apps/api/tests/test_organization_constitution.py
docs/ORGANIZATION_CONSTITUTIONAL_CONTRACTS_V1_3.md
```

### Constitutional invariants encoded

The new runtime-facing module freezes:

> **The Human Owner / Board is the supreme authority of Global Mobility AIOS.**

> **Operational autonomy must never create organizational opacity.**

> **Scores route decisions; deterministic gates authorize decisions.**

It also formalizes the permanent separation:

```text
Capability != Authority != Autonomy != Risk
CAN DO != MAY DO
```

### A0–A5 autonomy contract

```text
A0  Prohibited
A1  Human executes
A2  AI prepares; approval required
A3  Autonomous with mandatory review
A4  Autonomous with monitoring and valid recovery controls
A5  Fully autonomous bounded operation
```

The contract intentionally remains capability/context-specific rather than assigning one global autonomy score to an agent.

### R0–R5 risk contract

```text
R0  Non-material cognition
R1  Routine internal operation
R2  Client-facing preparation / Evidence validation
R3  Material recommendation / blind independent verification
R4  Certification/regulatory publication / deeper verification + fresh sources
R5  Government submission or critical reserved action / Human-Board gate
```

### HumanReviewReason frozen

```text
UNCERTAINTY
CONTRADICTION
INSUFFICIENT_EVIDENCE
OUTSIDE_AUTHORITY
POLICY_REQUIRED
LEGAL_REQUIRED
BOARD_RESERVED
ANOMALY
EXCEPTION
```

This preserves the critical distinction between uncertainty escalation and authority/legal/policy escalation.

### Consequence/recovery classes frozen

```text
REVERSIBLE
COMPENSATABLE
IRREVERSIBLE
APPEND_ONLY_CORRECTION
```

This prevents future governance code from pretending that every real-world action can be rolled back like a database row.

### Reserved authority classes frozen

```text
CONSTITUTION
STRATEGIC_DIRECTION
AUTONOMY_CEILING
MAJOR_POLICY
EXECUTIVE_APPOINTMENT
EMERGENCY_CONTROL
BOARD_RESERVED_EXTERNAL_ACTION
```

These are constitutional categories. Later workflow/jurisdiction policy may map concrete actions into them.

### Initial immutable Materiality Registry

| Action | Material | Risk | Board reserved |
|---|---:|---:|---:|
| `official_source.search` | no | R0 | no |
| `document.summary` | no | R0 | no |
| `internal.note` | no | R0 | no |
| `work_item.assignment` | yes | R1 | no |
| `evidence.candidate` | yes | R2 | no |
| `eligibility.transition` | yes | R3 | no |
| `evidence.certification` | yes | R4 | no by base constitution |
| `verified_rule.publication` | yes | R4 | no by base constitution |
| `external_communication.consequential` | yes | R3 | no by base constitution |
| `government.submission` | yes | R5 | yes |

The registry is read-only at runtime in this phase.

### Board Transparency activity policy

Activity classes frozen:

```text
CONVERSATIONAL
COLLABORATIVE
OPERATIONAL
MATERIAL
AUTHORITY
```

Every class is Board-inspectable.

Material/Authority activity requires durable full lineage.

Lower-value conversation may compact/summarize after policy retention rather than being stored forever as regulatory-grade raw text. This preserves the design goal:

```text
Board visibility != Board interruption
Transparency != infinite raw-token retention
```

### Initial focused acceptance evidence

The implementation checkpoint initially recorded isolated focused evidence:

```text
python -m py_compile apps/api/app/core/organization_constitution.py
pytest apps/api/tests/test_organization_constitution.py
13 passed in 0.07s
```

The later canonical local checkout run supersedes the timing detail for acceptance purposes:

```text
13 passed, 1 warning in 0.14s
```

The tests cover:

- stable A0–A5 values;
- stable R0–R5 values;
- HumanReviewReason taxonomy;
- consequence/recovery classes;
- reserved authority classes;
- total Materiality Registry coverage;
- R0 defaults for non-material cognition;
- R5 + Board-reserved government submission;
- Board inspectability for every activity class;
- durable/full lineage requirements for Material/Authority activity;
- conversational compaction semantics;
- immutable registries;
- frozen Board supremacy/transparency/hard-gate invariants.

### Runtime truth / non-claims

This slice does **not**:

- add a database migration;
- change migration head `0076_organization_position_active_identity`;
- mutate preserved `gmai.db`;
- change existing route authorization;
- change existing WorkItem API compatibility;
- implement MaterialAction persistence;
- implement Command Gateway execution;
- implement Decision Readiness;
- implement independent verification;
- implement the Organizational Immune System;
- implement earned-autonomy promotion/demotion;
- implement full Transparency runtime/UI;
- integrate Munder Difflin or OpenWorker;
- resolve Phase 13.17 findings;
- claim GitHub CI PASS.

### Roadmap

Roadmap advanced to **V12.1** for the initial implementation checkpoint and then **V12.2** after broader regression exposed the historical roadmap-continuity requirement.

### Next roadmap slice

After V1.3-A is fully accepted:

> **V1.3-B — Minimal Governance Kernel**

The first B implementation should stay deliberately small: actor identity, capability authority, expected version, idempotency, MaterialAction envelope, deterministic policy evaluation, Command Gateway foundation and OrganizationActivity trace identity.

---

## 2026-08-19 — V12 ROADMAP / README ALIGNMENT

### Status

Documentation/branch-alignment checkpoint only.

V12 was created directly from the V11 checkpoint at `dd2f2cd`. The inherited README and roadmap initially still described V11 as the active line, so V12 documentation was realigned to make the branch roles explicit.

Key commits included:

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
