# Munder M6 — Fenced failure finalization

Date: 2026-08-26

Status: BOUNDED IMPLEMENTATION / EXACT-HEAD PROOF PENDING

## Context

PRs #20–#24 established an AIOS-owned execution heartbeat lease, runtime-session fencing, bounded renewal, stale-session takeover/re-execution, and real PostgreSQL race evidence for claim/renewal sequencing. One mutation path still sat outside that fence: the exception handler that marks an `OrganizationExecutionAttempt` failed and records `WorkItem.last_error`.

A superseded worker could therefore lose its runtime fence and still reach its late exception handler. Without a fence check, that stale worker could overwrite canonical attempt/work failure state while a legitimate takeover generation was active.

## This slice

This slice adds `finalize_execution_failure_if_fence_owned(...)` and routes both the original Austria K.1 worker and the takeover worker through it.

The finalizer:

- rolls back the failed caller transaction before attempting failure persistence;
- re-resolves the tenant-bound WorkItem and execution attempt;
- requires the WorkItem and attempt to remain `running`;
- requires canonical WorkItem/attempt execution-token agreement and the caller's exact expected token;
- requires the caller's exact current runtime fence and writer identity;
- deliberately does not require lease freshness, because an expired but unsuperseded worker still owns its generation and may accurately record its own failure;
- appends a durable `runtime_session_failed` checkpoint in the same transaction as attempt/work failure mutation;
- uses the existing unique `(execution_attempt_id, sequence)` heartbeat constraint as the commit-time concurrency fence against takeover, renewal, terminal completion, or another failure finalizer;
- retries once after a sequence collision only when ownership remains provable;
- performs no canonical failure mutation when ownership is lost or the execution is already terminal.

The existing failure semantics are preserved for a legitimate owner: the attempt becomes `failed`, its error/completion timestamp is recorded, and the still-running WorkItem clears `execution_started_at` and records `last_error` so bounded retry policy can decide what happens next. This slice does not manufacture a new WorkItem status transition.

## PostgreSQL proof contract

A PostgreSQL-only race test deliberately synchronizes a stale original worker's failure finalization against a replacement worker's takeover claim after both transactions choose the same next heartbeat sequence.

The required invariant is one durable winner:

- if takeover wins, the stale failure finalizer must return without mutating attempt/work failure state;
- if failure finalization wins first, the takeover must fail closed;
- the ledger must contain exactly one sequence-2 event, never both a takeover claim and a failure checkpoint for the same generation boundary.

The test is added to the existing `V12 Production Proof` PostgreSQL governance lane.

## Truth and authority boundary

`runtime_session_failed` is technical execution-health provenance only. It does not establish human, provider, model, or AI-employee online/offline state. It grants no authority or autonomy, changes no Evidence or VerifiedRule truth, and authorizes no external action.

No migration or parallel runtime-state table is introduced. The AIOS-owned execution heartbeat ledger remains the concurrency/fencing substrate.

## M6 status

M6 remains PARTIAL.

This slice closes the stale-worker failure-mutation hole for the Austria K.1 original and takeover paths. Broader adoption across additional organization worker/runtime paths remains separate work.

## Required exact-head proof

Before this slice is Ready for Review:

- focused failure-finalization tests must pass;
- existing runtime-session, supervisor, takeover, heartbeat/presence, K.1, Live Organization, and platform-hardening regressions must pass;
- the PostgreSQL failure-vs-takeover race must execute and pass against real PostgreSQL;
- the repository-defined PostgreSQL governance lane must remain green;
- repository policy, release consistency, dependency constraints, diff hygiene, and working-tree cleanliness must pass on the exact head.

No CI/Woodpecker PASS is claimed until separately observed on the same exact SHA.