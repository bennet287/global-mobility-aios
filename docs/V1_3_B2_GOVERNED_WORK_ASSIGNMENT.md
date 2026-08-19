# V1.3-B.2 — Governed WorkItem Assignment

**Status:** IMPLEMENTED / CANONICAL CHECKOUT ACCEPTANCE PENDING  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Date:** 2026-08-20

## Goal

Prove that the accepted B.1 Governance Kernel can govern one real existing organization mutation rather than remaining an isolated policy evaluator.

The bounded first action is:

```text
work_item.assignment
risk = R1
consequence = REVERSIBLE
```

## Runtime path

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
existing audit row
        +
existing semantic assignment Activity
        +
Governance Activity / trace
        ↓
ONE TRANSACTION COMMIT
```

## Delivered runtime adapter

```text
apps/api/app/services/organization_governed_work.py
```

The adapter does not create a second WorkItem model, a second Activity store, or a new authorization universe. It composes the B.1 evaluator with the existing `OrganizationalWorkItem`, audit utilities, semantic Activity utilities and staged Activity writer.

## Precondition contract

The current WorkItem model has no dedicated integer aggregate-version column. B.2 therefore derives a deterministic integer precondition token from canonical `updated_at` without a migration.

A successful assignment advances `updated_at`, making stale competing commands fail closed.

This is a bounded compatibility bridge. A later schema phase may replace the timestamp-derived token with an explicit aggregate version if runtime evidence justifies the migration.

## Idempotency ordering correction

A successful mutation necessarily advances the aggregate precondition. Therefore an exact retry using the original expected version must first be recognized against the durable governance Activity fingerprint.

B.2 persisted evaluation follows:

```text
identity / authority / capability / scope / risk
        ↓
existing durable idempotency result?
        ├── exact fingerprint → IDEMPOTENT_REPLAY
        └── conflicting fingerprint → BLOCK
        ↓
new command only: expected-version check
```

This prevents a legitimate network/process retry from being misclassified as stale merely because the first execution succeeded.

## Atomicity

For `AUTO_EXECUTE`, B.2 stages all of the following before one caller-owned commit:

- WorkItem assignee mutation;
- existing `organization.work.assign` audit row;
- existing semantic WorkItem assignment Activity;
- governance decision Activity with trace/fingerprint.

Any exception rolls the full unit of work back.

This preserves the V1.3 invariant that autonomous truth-changing work must not commit successfully while its material governance trace silently fails.

## Test coverage

```text
apps/api/tests/test_organization_governed_work.py
```

The focused tests cover:

- real R1 assignment AUTO_EXECUTE;
- durable governance Activity correlation;
- existing audit creation;
- exact replay after state/version advancement;
- stale competing command rejection;
- conflicting idempotency-key reuse rejection;
- A2 review-required path with no mutation;
- rollback of WorkItem, audit and Activity when governance Activity storage fails.

## Important non-claims

B.2 does not yet:

- expose this governed command through a public HTTP route;
- convert every WorkItem transition to MaterialAction;
- persist blocked/review-only gateway attempts as the final Transparency model;
- add a MaterialAction database table;
- add a database migration;
- add Decision Readiness;
- add independent R3+ verification;
- add Organizational Immune System behavior;
- add earned-autonomy promotion/demotion;
- implement V1.3-C Transparency Foundation;
- claim canonical checkout PASS until the user reruns the tests on the actual V12 checkout;
- claim GitHub CI PASS.

## Acceptance gate

After pulling the latest V12 head, run:

```text
pytest apps/api/tests/test_organization_governance_kernel.py apps/api/tests/test_organization_governed_work.py -q
scripts/check_repo_policy.py --root .
pytest apps/api/tests -q
scripts/check_database_migrations.py
scripts/check_local_db_schema.py --database-url sqlite:///D:/global-mobility-aios/gmai.db
git diff --check
git status -sb
```

If all checks pass, B.2 can be sealed and V1.3-B can proceed to the next bounded integration decision rather than expanding horizontally without evidence.
