# Munder M6 — G.1 Independent-Verifier Runtime Fencing

Date: 2026-08-27

Status: LOCAL TECHNICAL PROOF PASS AT `b21e916ee9a6dcea0ca07b50cb9f6099791402fa` / FOLLOW-UP ACTIVE

## Purpose

PR #27 routes the governed E.2 producer through an AIOS-owned fenced runtime session.
This slice adopts the same execution-safety primitives for the independent G.1 verifier
without changing G.1's truth, independence, blind-review, or authorization semantics.

G.1 remains the owner of:

- Decision Readiness validation;
- proposer/verifier OrganizationPosition separation;
- canonical case/pathway/Evidence/VerifiedRule authority;
- separate independence-group, provider, and model requirements;
- blind verifier payload construction;
- typed verifier output validation;
- post-provider freshness checks;
- durable independent-verification Activity lineage;
- the rule that G.1 itself never authorizes or commits canonical eligibility truth.

The new runtime envelope owns only technical execution provenance.

## Runtime contract

`execute_fenced_independent_eligibility_verification`:

1. requires a fresh queued verification WorkItem assigned to the verifier position;
2. resolves the exact G.1 readiness/context/runtime basis before operational mutation;
3. transitions the verification WorkItem to running through the existing command path;
4. re-resolves the same G.1 execution basis in running state;
5. derives one execution token from:
   - contract version,
   - verification WorkItem id,
   - verifier position,
   - bounded attempt number,
   - verifier ContextBundle hash,
   - verifier runtime-binding hash;
6. creates one durable `OrganizationExecutionAttempt`;
7. appends generation-one `attempt_started`;
8. supervises lease renewal only while the verifier provider call is active;
9. requires the current fresh fence for `agent_completed`;
10. completes the verification WorkItem only after fenced terminal provenance;
11. delegates execution failure mutation to the shared PR #25 fence-aware failure finalizer.

The generic WorkItem `updated_at` is not advanced again when the attempt row is created.
The attempt timestamp and heartbeat ledger are the execution clock, so the token remains
bound to the exact running verifier ContextBundle G.1 consumes.

## G.4 adoption

G.4 now invokes the fenced verifier runtime instead of calling
`verify_eligibility_proposal_independently` directly.

The orchestration still supplies the same trusted server-side verifier position,
runtime profile, provider, and idempotency identity. H.2.2 verifier runtime failures
remain attributed from that trusted execution plan. The runtime envelope adds durable
`attempt_started -> runtime_session_failed` provenance around the same failure; it
does not replace immune-system attribution.

Exact committed-effect replay remains before fresh producer/verifier execution and
therefore creates no new verifier attempt.

## Authority boundary

Runtime-session state is technical execution-health provenance only.

It does not:

- establish human/provider/model/employee online or offline status;
- grant authority or autonomy;
- relax independent-provider/model/independence-group requirements;
- change Evidence, VerifiedRule, case, pathway, or revision truth;
- satisfy the verification floor by itself;
- authorize or commit canonical eligibility state;
- authorize external action.

## Deliberate boundary

This slice accepts only a fresh queued G.1 verification WorkItem. A failed verifier
attempt is durably fenced, but same-WorkItem retry/takeover/resume was intentionally not
introduced in PR #28.

The later takeover/resume follow-up preserves this historical boundary while adding a
new explicit entry point for an interrupted still-running attempt. It also stages G.1
verification lineage until terminal fence ownership and WorkItem completion commit
atomically. Terminal failed-attempt retry remains outside this contract.

No migration or second runtime-state model is introduced.

## Required exact-head proof

Before this PR leaves Draft:

1. focused SQLite G.1 wrapper success must prove exact token-to-consumed-context binding;
2. focused G.1 failure must prove shared `runtime_session_failed` finalization;
3. G.4 accepted/replay paths must prove exactly one verifier attempt and no replay attempt;
4. H.2.2 verifier runtime attribution must remain intact under fenced failure;
5. real PostgreSQL must prove at least one `runtime_session_renewed` event while the verifier provider call is active;
6. the current workflow PostgreSQL governance lane must include the new verifier runtime contract;
7. broader eligibility/M6 regressions must remain green;
8. repository policy, release consistency, dependency constraints, diff hygiene, and final Git status must pass on the exact head.

## M6 status

M6 remains **PARTIAL**.

After this slice, the next bounded M6 target is eligibility takeover/resume, followed by
one additional real organization worker adoption.
