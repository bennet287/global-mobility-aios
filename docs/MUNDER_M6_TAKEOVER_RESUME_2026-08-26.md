# Munder M6 — Fenced Takeover Resume

Date: 2026-08-26  
Track: B — controlled Munder adoption  
Base: PR #22 / `work/b-munder-runtime-renewal-supervisor-20260826`  
Status: **BOUNDED IMPLEMENTATION / EXACT-HEAD PROOF PENDING**

## Purpose

PR #20 established durable execution heartbeat leases. PR #21 added fenced runtime-session claim/renewal semantics. PR #22 connected the current fence to an active bounded renewal supervisor around the Austria K.1 controlled-agent call.

This slice addresses the next M6 gap: a trusted worker that observes an expired K.1 runtime session can explicitly reclaim that exact interrupted execution and re-execute it under a newer fencing generation, while a superseded worker remains unable to commit a late result.

## Adopted behavior

The takeover entry point is intentionally narrow:

- it accepts only the existing Austria K.1 specialist positions;
- the specialist WorkItem and the exact `OrganizationExecutionAttempt` must both still be `running`;
- the caller must provide the exact durable execution-attempt ID, execution token, and previously observed fence token;
- the attempt must still be the only canonical running attempt for the WorkItem;
- a current K.1 `OrganizationalActionOutput` must not already exist;
- the current runtime-session lease must be expired before takeover is allowed;
- the takeover claim must advance the durable heartbeat-ledger fence;
- the resumed worker reuses the same bounded `OrganizationExecutionAttempt`; it does not manufacture another retry/attempt number;
- the controlled-agent call runs under the PR #22 renewal supervisor using the new fence;
- terminal `agent_completed` is staged only by the current fresh fenced owner;
- failure after takeover marks the same attempt failed and leaves no completed K.1 output.

## Context and runtime continuity

A naive rebind cannot be compared directly with the original K.1 context hash because `_start_attempt` itself advances `WorkItem.updated_at` after the original ContextBundle was bound. Treating that technical timestamp change as domain drift would make every legitimate resume stale.

The takeover path therefore fails closed against durable original provenance instead of guessing:

1. It resolves the unique `austria_specialist_execution_started` audit record for the exact WorkItem/attempt number/position.
2. That audit must contain the original 64-character `context_hash` and `runtime_binding_hash` used to form the execution token.
3. The immediately preceding audited WorkItem state supplies the exact pre-attempt `updated_at` value used by the original ContextBundle.
4. Current governed context is rebuilt normally. Only the known `_start_attempt` `WorkItem.updated_at` mutation is normalized back to the audited pre-attempt value.
5. All other current ContextBundle material remains current: position contract/version, working context, canonical subject fingerprints, Evidence references, VerifiedRule references, source snapshots, unknowns, contradictions, allowed tools and policy version.
6. The normalized current context must reproduce the original context hash exactly.
7. The current supplied runtime profile is reconstructed against that original context hash and must reproduce the original runtime-binding hash exactly.
8. Those original hashes must reproduce the durable execution token exactly.

Audit timestamps are checked in both offset-preserving and SQLite-compatible naive forms. Exactly one representation must reproduce the original hash, so the continuity check remains deterministic across the repository's SQLite developer tests and PostgreSQL production direction.

Missing, malformed, ambiguous or non-reproducible provenance is a hard refusal.

## WorkItem mutation guard

The normal K.1 start path sets `WorkItem.execution_started_at` and `WorkItem.updated_at` to the same start timestamp. Heartbeat claims and renewals do not mutate WorkItem state.

Takeover therefore additionally requires the current `WorkItem.updated_at` to still equal `execution_started_at`. A later canonical WorkItem mutation invalidates resume even if the WorkItem eventually appears `running` again.

## Output provenance

A successful resumed K.1 output records, as technical provenance only:

- original context hash;
- current resume context hash;
- original runtime-binding hash;
- current resume runtime-binding hash;
- continuity verification flag;
- exact execution-attempt ID and execution token;
- previous fence and new fence;
- takeover writer;
- renewal count;
- `runtime_takeover_resume=true`;
- `provider_model_authority=false` and runtime-session `authority_effect=false`.

The existing K.1 review gate and blocked external-action posture remain unchanged.

## Explicit non-claims

This slice does **not** mean an employee, provider, model or human is online.

It does not grant authority or autonomy, change Evidence/VerifiedRule truth, authorize external actions, create a second canonical runtime-state model, or convert heartbeat events into organizational contribution/activity merely because they occurred.

No browser refresh, page visibility, animation, provider identity or synthetic keepalive is accepted as employee-presence evidence.

## Migration impact

None. The durable heartbeat ledger, execution attempt, WorkItem state and existing audit log are reused. Migration head remains `0082_organization_execution_heartbeat_lease`.

## Focused proof expectations

Before this slice can be Ready for Review, exact-head local proof should cover at least:

- successful same-attempt takeover under a newer fence;
- renewal under the takeover fence;
- terminal completion only by the current fence owner;
- fresh-session refusal;
- stale previously observed fence refusal;
- runtime-profile/binding drift refusal;
- WorkItem mutation refusal;
- wrong execution-token refusal;
- takeover-worker failure marking the same attempt failed without a completed output;
- PR #22 supervisor regressions;
- PR #21 fencing/safety regressions;
- heartbeat, presence, K.1, Live Organization and platform-hardening regressions;
- frontend design/live-surface, request-auth, TypeScript, production build, compiled-auth and Chromium E2E;
- repository policy, release consistency, whitespace and a clean final worktree.

Local proof is not Woodpecker/CI proof.

## M6 status after this slice

M6 remains **PARTIAL**.

The Austria K.1 path now has durable lease observation, fencing generations, active bounded renewal, stale-session takeover, same-attempt re-execution and current-fence terminal completion. Broader organization-worker adoption, PostgreSQL concurrency evidence for integrated takeover/renewal races, and exact-head production/Woodpecker acceptance remain outstanding before a broader runtime-liveness claim is justified.
