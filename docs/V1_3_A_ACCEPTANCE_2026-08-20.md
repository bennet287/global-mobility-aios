# V1.3-A Constitutional Contracts — Final Acceptance

**Date:** 2026-08-20  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Implementation commit:** `7779c1f8e5d3db2e72e047667774284d7cc5f5af`  
**Status:** **COMPLETE / PASS / SEALED**

## Scope

V1.3-A freezes the runtime-facing constitutional vocabulary required before the V1.3 Governance Kernel may authorize material organizational actions.

The delivered contract covers:

- Human Owner / Board supremacy;
- Board Transparency;
- A0–A5 capability-specific autonomy;
- R0–R5 action risk;
- `HumanReviewReason`;
- consequence/recovery classes;
- reserved authority classes;
- material action types and immutable Materiality Registry;
- organization activity transparency classes;
- the invariant that scores may route, while deterministic gates authorize.

## Canonical Windows V12 acceptance evidence

The following evidence was produced from the user's canonical local checkout after synchronizing to the V12.2 roadmap compatibility correction.

### Focused constitutional tests

```text
pytest apps/api/tests/test_organization_constitution.py -q
13 passed, 1 warning in 0.14s
```

### Repository policy

```text
scripts/check_repo_policy.py --root .
Repository policy check passed.
```

### Historical roadmap compatibility regression

The earlier broad run exposed a single documentation continuity failure because the V12 roadmap rewrite omitted protected historical v10.22 markers. V12.2 restored:

```text
v10.22
multi-batch tranche operations
0032_initial_rule_assertions
```

After synchronizing the local checkout, the previously failing test passed:

```text
1 passed, 1 warning in 0.08s
```

### Full API regression

```text
pytest apps/api/tests -q
886 passed, 5 skipped, 1 warning in 337.70s (0:05:37)
```

### Migration integrity

```text
Database migration check passed.
database_url=sqlite:///./gmai.db
migration_heads=0076_organization_position_active_identity
registered_tables=118
physical_schema=ok
database_revision=0076_organization_position_active_identity
```

### Preserved local database schema parity

```text
Local DB schema check passed.
database_url=sqlite:///D:/global-mobility-aios/gmai.db
registered_tables=118
actual_tables=118
physical_tables=119
infrastructure_tables=["alembic_version"]
```

### Git integrity

```text
git diff --check
# no output

git status -sb
## roadmap/global-mobility-aios-v12...origin/roadmap/global-mobility-aios-v12
```

The worktree was clean and the local V12 branch was synchronized with its remote at acceptance time.

## Warning disposition

The suite emitted one existing/non-blocking warning:

```text
StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.
```

This warning did not cause a test failure and is not treated as a V1.3-A blocker. Dependency remediation should be handled as a separate bounded maintenance task rather than changing test-client dependencies inside the constitutional-contract phase.

## Non-claims

This acceptance does not claim:

- GitHub Actions / CI PASS; no attached status evidence is used here;
- a new database migration;
- a change to the 118 registered domain tables;
- Decision Readiness implementation;
- independent-verification implementation;
- Organizational Immune System implementation;
- earned-autonomy promotion/demotion;
- full Board Transparency runtime/UI;
- external agent/execution runtime integration.

## Final decision

All acceptance conditions required for the bounded V1.3-A contract slice are satisfied.

```text
V1.3-A — Constitutional Contracts
COMPLETE
PASS
SEALED
```

The active Track C implementation may therefore proceed to **V1.3-B — Minimal Governance Kernel** while preserving the V1.3-A contract as the constitutional floor.
