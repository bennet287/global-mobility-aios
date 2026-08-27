# Munder M6 — G.4 Fenced E.2 Orchestration Wiring

Date: 2026-08-26

Status: BOUNDED IMPLEMENTATION / PROOF PENDING

## Purpose

PR #26 established a proven, domain-specific fenced runtime envelope around the governed E.2 eligibility producer. This slice makes that envelope the production G.4 producer path instead of leaving it as an alternate entry point.

The change is deliberately narrow: G.4 still owns the same E.2 → F.1 → G.1 → G.2 → canonical-effect sequence and the same trusted execution-plan boundary. Only the producer invocation is routed through the already-proven E.2 runtime envelope.

## What changes

`orchestrate_governed_eligibility` now invokes `execute_fenced_governed_eligibility_transition_intent` for the producer stage and consumes its governed E.2 result.

That means a fresh G.4 producer execution now also records:

- the existing queued-to-running WorkItem transition;
- one bounded `OrganizationExecutionAttempt`;
- generation-one `attempt_started` runtime provenance;
- active runtime-session renewal while the producer is executing;
- fenced `agent_completed` terminal provenance on success;
- shared `runtime_session_failed` failure provenance through PR #25's finalizer when the producer fails.

The completed-effect replay path remains before fresh producer execution, so an exact durable replay does not create another runtime attempt or call either provider.

## Deliberate non-changes

This slice does not:

- change E.2 truth, Evidence, VerifiedRule, revision-precondition, typed-output, Command Gateway, or canonical-effect semantics;
- change G.4 authority or request trust boundaries;
- fence the independent verifier yet;
- add eligibility takeover/resume yet;
- add a migration or a second runtime-state model;
- treat heartbeat/runtime-session state as human, provider, model, or employee online/offline state.

Runtime-session data remains technical execution-health provenance only and grants no authority or autonomy.

## Failure and immune-system continuity

Existing G.4 producer runtime failures still propagate through E.2's typed runtime errors, so H.2.2 runtime-health attribution remains driven by the trusted execution plan. The new runtime envelope adds fenced failure provenance around that same failure; it does not replace the existing immune-system attribution contract.

## F.1 lifecycle compatibility

The first focused G.4 proof exposed one real integration invariant: the fenced E.2 envelope intentionally completes the producer WorkItem after a successful `agent_completed` checkpoint, while F.1 previously required the entire post-E.2 ContextBundle hash to remain identical. Because the ContextBundle includes WorkItem `status` and `updated_at`, a legitimate `running -> completed` runtime lifecycle transition looked like stale governed context.

The fix does **not** weaken F.1 to ignore arbitrary context changes. F.1 accepts that hash drift only when:

- the accepted E.2 context was `running` and the current WorkItem is `completed`;
- all ContextBundle fields other than the expected WorkItem status/timestamp transition remain identical;
- the original runtime binding still matches the accepted E.2 context;
- the canonical WorkItem carries the exact recomputed E.2 execution token;
- exactly one matching `OrganizationExecutionAttempt` is completed without error; and
- its durable heartbeat ledger begins with `attempt_started`, ends with `agent_completed`, and contains no `runtime_session_failed`.

An unfenced/manual WorkItem completion therefore remains stale-context failure. This preserves F.1's case/pathway/Evidence/rule freshness boundary while allowing the already-governed runtime lifecycle to finish before downstream deterministic review.

The second focused proof exposed a deeper token-binding invariant. The runtime envelope originally advanced the generic WorkItem `updated_at` while creating `OrganizationExecutionAttempt`. Because `updated_at` participates in the ContextBundle hash, the execution token was derived from the pre-attempt running context while E.2 immediately re-resolved and consumed a different post-attempt context. The F.1 exception correctly refused to treat that as an exact fenced completion.

The correction keeps the generic WorkItem `updated_at` stable during attempt creation. Runtime timing remains durable in `OrganizationExecutionAttempt.started_at`, `execution_started_at`, and the heartbeat ledger. E.2 therefore consumes the exact ContextBundle/runtime binding used to derive the execution token. A focused runtime contract now recomputes the execution token from the returned E.2 context hash and runtime-binding hash and requires an exact match.

## WorkItem lifecycle across reassessment

The broader regression exposed a separate lifecycle assumption in the pre-fencing tests: multiple canonical eligibility revisions were being produced by repeatedly reusing the same proposal/verification WorkItems after the first G.4 operation had completed them.

That is no longer a valid execution model once G.4 is wired through a durable runtime envelope. A completed WorkItem is terminal organizational history and must not be reopened merely because the eligibility aggregate is being reassessed. Each fresh G.4 operation therefore uses a fresh proposal WorkItem and a fresh verification WorkItem bound to the same canonical Lead/Profile/pathway authority.

G.4 now resolves exact committed-effect replay first. For non-replay execution it rejects a terminal proposal WorkItem before provider egress. It also performs the deterministic G.5 revision precondition before opening a runtime session; E.2 still re-resolves that precondition inside the fenced execution, preserving the existing pre-provider and post-provider race boundaries.

This keeps three identities separate:

- eligibility aggregate identity survives across revisions;
- orchestration idempotency identifies one requested canonical operation/replay;
- WorkItem/execution-token identity belongs to one bounded organizational execution.

Known stale/missing/future revision expectations therefore do not consume a fresh execution attempt or provider call, while a valid reassessment receives its own fenced WorkItem/attempt ledger.

## Required exact-head proof

Before this PR leaves Draft:

1. G.4 accepted-path tests must prove exactly one producer execution attempt and `attempt_started -> agent_completed`;
2. committed-effect replay must prove no second producer execution attempt;
3. producer runtime failure must preserve H.2.2 attribution and prove `attempt_started -> runtime_session_failed`;
4. existing eligibility orchestration, runtime-health, revision-race, failure-finalization, runtime-session, supervisor, and takeover regressions must remain green;
5. real PostgreSQL governance/runtime contracts must execute rather than skip where applicable;
6. repository policy, release consistency, dependency constraints, diff hygiene, and clean Git status must pass on the exact head.

## M6 status

M6 remains PARTIAL.

After this slice, the next bounded M6 adoption targets are independent-verifier runtime fencing, eligibility takeover/resume, and one additional real organization worker path.
