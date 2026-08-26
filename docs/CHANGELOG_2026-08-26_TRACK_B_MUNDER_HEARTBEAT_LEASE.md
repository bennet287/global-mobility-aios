# Track B — Munder M6 heartbeat lease foundation

Date: 2026-08-26  
Status: **IMPLEMENTED / EXACT-HEAD PROOF PENDING**  
Programme: Track B UX2 / Munder Difflin controlled adoption  
Base: `work/b-live-org-presence-integration-20260825` / PR #18  
Adoption state: **M6 PARTIAL — durable checkpoint freshness added; continuous liveness not established**

## What changed

This slice advances the AIOS-owned employee-presence contract from execution presence only to a durable, bounded worker-checkpoint lease.

- Added `organization_execution_heartbeats`, a first-party durable record bound to tenant, OrganizationPosition assignment, WorkItem, and OrganizationExecutionAttempt.
- Added migration `0082_organization_execution_heartbeat_lease` on top of `0081_capability_autonomy_evidence_evaluation_policy`.
- Added strict writer semantics with bounded 15–300 second leases and fixed trusted checkpoints.
- K.1 Austria specialist execution now records `attempt_started` and `agent_completed` checkpoints in its existing durable execution transactions.
- Presence contract advances to `organization-position-presence.v2`.
- A running execution can report heartbeat `fresh`, `stale`, or `not_established`; a non-running execution reports `inactive`.
- The Board-facing presence API evaluates all specialist freshness against one snapshot timestamp.
- Cockpit surfaces show fresh/stale checkpoint state without translating it into online/offline status.
- Added backend contract/integration tests and refreshed frontend truth-boundary tests.
- Corrected the platform-hardening router inventory to include the already-landed `organization-presence-transparency` router as the 70th registered feature.

## Truth boundary

A heartbeat is not a generic liveness ping. It means only that a trusted AIOS worker reached a specific durable execution checkpoint and that the bounded lease derived from that checkpoint has or has not expired.

```text
fresh
  = latest durable AIOS worker checkpoint is inside its lease

stale
  = latest durable AIOS worker checkpoint lease expired while execution is still running

not_established
  = running execution has no durable heartbeat checkpoint

inactive
  = no running execution attempt, therefore no active heartbeat lease
```

Permanent non-inferences:

- `fresh` does not mean a human employee is online;
- `fresh` does not prove provider/model connectivity between checkpoints;
- `stale` does not mean the employee/provider/model is offline;
- browser refresh, animation, page visibility, provider identity, and model activity are not heartbeat evidence;
- heartbeat has `authority_effect=false` and never grants autonomy, Evidence status, or external-action permission.

Because the current K.1 controlled-agent call is synchronous, a long provider call can legitimately outlive the lease and become stale before the next trusted checkpoint is reached. No background thread or synthetic keepalive is introduced to conceal that fact.

## Munder adoption boundary

This remains an `ADAPT`. AIOS owns the heartbeat persistence, writer rules, tenant binding, freshness semantics, and presentation vocabulary. No donor runtime state becomes authoritative.

M6 remains **PARTIAL** rather than complete. Continuous worker liveness, failure/recovery evidence across a production worker runtime, and broader runtime coverage beyond the bounded K.1 path remain future work.

## Acceptance proof required

Before this slice is Ready for Review, verify the exact remote head in an isolated Track B worktree with:

- heartbeat/presence and K.1 focused backend tests;
- existing Austria Live Organization tests;
- platform hardening;
- migration/release consistency;
- frontend design-foundation and request-auth tests;
- TypeScript and production build;
- compiled-auth verification;
- Chromium browser E2E;
- repository policy;
- `git diff --check`;
- an empty final `git status --short`.

Local proof must not be presented as Woodpecker/CI proof.
