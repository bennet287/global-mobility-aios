# Munder M6 — PostgreSQL Runtime Fencing Race Proof

Date: 2026-08-26
Status: IMPLEMENTED / REAL POSTGRESQL PROOF PENDING
Track: B
Base: PR #23 / `work/b-munder-takeover-resume-20260826`

## Purpose

PRs #20–#23 established the AIOS-owned runtime-liveness chain for the bounded Austria K.1 path: durable checkpoint lease, runtime-session fencing, active bounded renewal, and stale-session takeover/re-execution.

This slice does not add another runtime state model. It adds a real PostgreSQL concurrency contract for the existing durable `organization_execution_heartbeats` ledger so M6 race behavior is tested against production-grade unique-constraint and transaction semantics rather than inferred from SQLite.

## Added PostgreSQL contracts

`apps/api/tests/test_organization_execution_runtime_session_postgres.py` is PostgreSQL-only and requires `GMAI_TEST_DATABASE_URL`.

It forces two independent database sessions to calculate the same next heartbeat sequence before either transaction commits, producing a real database race rather than a sequential simulation.

The contracts require:

1. two different workers racing to reclaim the same stale execution session produce exactly one new fencing generation;
2. the losing claimant receives a bounded `DependencyConflict`, not a leaked raw database `IntegrityError`;
3. the durable ledger contains exactly one takeover claim at the next sequence;
4. the losing worker remains unable to renew the superseded fence;
5. two concurrent renewals for the same writer/fence produce exactly one durable renewal heartbeat and one bounded concurrency conflict;
6. renewal races never manufacture another fence generation.

The existing `(execution_attempt_id, sequence)` uniqueness invariant remains the durable serialization backstop. No database constraint is weakened.

## CI adoption

The PostgreSQL-only race contract is added to the existing `postgres-governance` job in `.github/workflows/v12-production-proof.yml`, which already provisions PostgreSQL 16 and exports both `DATABASE_URL` and `GMAI_TEST_DATABASE_URL`.

This is an extension of the existing production-proof lane, not a separate test framework.

## Truth and authority boundary

Runtime lease/fence state remains technical execution-health provenance only.

A successful claim or renewal does not mean a human, provider, model, or AI employee is online. It grants no organizational authority or autonomy, changes no Evidence/VerifiedRule/domain truth, authorizes no external action, and does not become canonical `OrganizationActivity` merely because the heartbeat ledger changed.

## Proof boundary

Repository implementation alone is not real PostgreSQL proof.

Before this slice can be marked proven, the PostgreSQL-only test must actually execute against PostgreSQL and pass on the exact branch head. A normal SQLite run that skips the file does not satisfy this gate.

Expected exact-head evidence should include:

- PostgreSQL 16 reachable through `GMAI_TEST_DATABASE_URL`;
- `test_organization_execution_runtime_session_postgres.py` executes rather than skips;
- both forced race contracts pass;
- the surrounding runtime-session/takeover regression surface remains green;
- repository policy, release consistency, and diff hygiene remain green;
- no CI/Woodpecker PASS is claimed unless observed on the same exact SHA.

## M6 status

M6 remains **PARTIAL**.

Passing this slice will establish real PostgreSQL concurrency evidence for the current heartbeat/fencing primitives. Broader adoption across additional organization worker/runtime paths remains separate work and should proceed only after the race contract proves or exposes the current persistence semantics.
