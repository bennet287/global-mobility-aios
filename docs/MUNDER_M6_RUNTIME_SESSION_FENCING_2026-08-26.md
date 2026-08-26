# Munder M6 — AIOS Runtime Session Fencing Foundation

Date: 2026-08-26  
Status: **BOUNDED FOUNDATION / LOCAL PROOF PENDING**  
Base: `work/b-munder-heartbeat-lease-20260826` / PR #20  
Classification: **ADAPT**

## Purpose

This slice strengthens the AIOS-owned M6 presence/heartbeat implementation without
adopting donor runtime state as authority and without manufacturing continuous online
status.

PR #20 established durable execution-checkpoint heartbeat leases. This follow-up adds a
runtime-session fencing contract on top of the same durable heartbeat ledger so an
expired worker lease can be taken over explicitly and a worker holding an older fence can
no longer renew silently.

## Canonical mechanics

The existing `organization_execution_heartbeats` ledger remains the persistence model.
No new migration or parallel runtime-state table is introduced by this slice.

For one `OrganizationExecutionAttempt`:

```text
attempt_started
  = initial durable session claim
  = fencing generation 1

runtime_session_renewed
  = extends only the current unexpired generation
  = fence token does not change

runtime_session_claimed after expiry
  = explicit takeover
  = its heartbeat sequence becomes the new fence token
```

The current fence token is therefore the durable heartbeat sequence of the latest claim
event. A later claim invalidates every worker still holding an older token.

## Fail-closed bindings

Runtime-session claim/renewal re-resolves and checks:

- tenant-scoped `OrganizationalWorkItem`;
- exact `OrganizationExecutionAttempt`;
- WorkItem assignment / `position_key`;
- canonical WorkItem and attempt `execution_token` equality;
- caller-held expected execution token;
- running WorkItem + running execution-attempt state for mutation;
- current fencing generation;
- current claim writer;
- lease freshness before renewal.

A fresh session cannot be stolen. An expired session cannot be renewed; it must be
reclaimed, which creates a new fencing generation. A stale fence or stale execution token
fails closed.

## Authority and truth boundary

Runtime-session state is technical execution health only.

It does **not**:

- make a human, provider, model, or AI employee "online";
- grant authority or autonomy;
- change Evidence or VerifiedRule truth;
- authorize external action;
- become canonical `OrganizationActivity` merely because a heartbeat occurred;
- prove continuous worker liveness between durable observations.

Provider/model identity, browser refresh, page visibility, animation, and client polling
remain non-evidence for employee presence.

## M6 status

M6 remains **PARTIAL** after this slice.

What this slice establishes:

- durable generation/fence semantics for one execution attempt;
- guarded lease renewal;
- explicit stale-session takeover;
- stale-worker renewal rejection;
- execution-token and tenant/position fail-closed checks;
- deterministic same-writer idempotent claim behavior;
- bounded lease limits inherited from the PR #20 heartbeat contract.

What remains before M6 can be described as continuous trusted runtime liveness:

- a production worker loop or runtime adapter that actually renews the current fence while
  useful execution is progressing;
- exact fencing of terminal attempt/output mutation so a superseded worker cannot commit
  a late result after takeover;
- broader runtime coverage beyond the bounded Austria K.1 execution path;
- production/Woodpecker evidence for the final integrated writer path.

No background keepalive or synthetic activity is added here merely to make the UI appear
alive.

## Required proof

Before this slice leaves draft status, prove on the exact branch head:

- focused runtime-session fencing tests;
- existing heartbeat/presence/K.1/platform-hardening tests;
- frontend design/live-surface + request-auth regressions;
- TypeScript, Next.js production build and compiled-auth verification;
- Chromium E2E;
- repository policy and release consistency;
- `git diff --check`;
- empty final working tree.

CI/Woodpecker status must be reported separately and only when actually observed.
