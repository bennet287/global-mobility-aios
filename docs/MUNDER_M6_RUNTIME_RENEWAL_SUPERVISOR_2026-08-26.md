# Munder M6 — Runtime Renewal Supervisor

Date: 2026-08-26  
Status: **BOUNDED IMPLEMENTATION / EXACT-HEAD PROOF PENDING**  
Base: `work/b-munder-runtime-session-fencing-20260826` / PR #21  
Classification: **ADAPT**

## Purpose

PR #20 established durable AIOS-owned heartbeat leases. PR #21 added execution-session
fencing and explicit stale-session takeover. This slice connects that fencing contract to
real bounded execution: while the Austria K.1 controlled-agent call is actively running,
a scoped supervisor can renew the current lease from a separate database session.

The supervisor exists only for the guarded execution section. It is not an always-on
presence daemon and it is not evidence that a human, provider, model, or AI employee is
continuously online.

## Runtime contract

```text
attempt_started
  -> durable generation-1 session claim

controlled-agent execution begins
  -> scoped renewal supervisor starts

while the guarded call is still active
  -> supervisor renews the same execution token + fence + writer

renewal loses fence / token / writer / running state
  -> supervisor records failure
  -> caller fails closed before terminal output commit

controlled-agent execution returns
  -> supervisor stops
  -> no further renewal is emitted

terminal completion
  -> requires current fresh fence + writer + execution token
```

Default production timing remains bounded by the existing heartbeat lease: a 120-second
lease with a 40-second renewal interval. The interval must stay below half of the lease,
leaving explicit headroom for scheduling and database latency.

## Takeover-owner completion

This slice also adds a fenced terminal-completion primitive. The terminal
`agent_completed` checkpoint is no longer conceptually restricted to generation 1: a
legitimate takeover worker may complete only when it presents the current fresh fence,
current execution token, correct tenant/WorkItem/position binding, and current writer
identity.

An older worker holding a superseded fence cannot stage the terminal checkpoint and
therefore cannot use the normal K.1 transaction to commit a late result.

The current Austria K.1 path still starts as generation 1. A separate resume/re-execution
entry point for a takeover worker is not introduced by this slice.

## Truth and authority boundary

Runtime renewal data is technical execution-health provenance only. It does not:

- grant authority or autonomy;
- change Evidence, SourceSnapshot, VerifiedRule, case, or WorkItem meaning;
- authorize client communication or any other external action;
- become canonical OrganizationActivity automatically;
- infer human/model/provider online status;
- create UI activity when no real guarded execution is running.

Provider execution remains review-gated and all existing K.1 blocked external actions
remain blocked.

## Persistence

No new table and no migration are introduced. Renewal and takeover observations continue
to use `organization_execution_heartbeats`. The supervisor itself is process-local and
contains no canonical state.

## M6 status

M6 remains **PARTIAL**.

Established by this slice:

- scoped real renewal during the bounded K.1 controlled-agent call;
- fail-closed propagation of renewal/fence loss before terminal commit;
- terminal completion for the current fenced owner, including a legitimate takeover
  generation;
- no renewal after the guarded execution context exits;
- runtime fence/renewal provenance in the K.1 internal output and audit trail;
- no migration or parallel source of truth.

Still required before M6 can be called broadly complete:

- an explicit takeover-worker resume/re-execution entry point, rather than only the
  terminal primitive;
- coverage for additional organization worker/runtime paths beyond Austria K.1;
- production/PostgreSQL concurrency proof for the integrated renewal writer;
- exact-head Woodpecker/production acceptance where available.

## Required proof

Before this slice leaves Draft, prove on the exact branch head:

- runtime supervisor unit tests;
- takeover terminal fencing tests;
- PR #21 runtime-session fencing/safety tests;
- heartbeat/presence/K.1/Live Organization/platform-hardening regressions;
- frontend design/live-surface and request-auth tests;
- TypeScript, Next.js production build, compiled-auth and Chromium E2E;
- repository policy and release consistency;
- `git diff --check` and an empty final working tree.

CI/Woodpecker status remains a separate claim and must only be recorded when observed.
