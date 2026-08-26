# Munder M6 — Governed Eligibility Runtime Envelope

Date: 2026-08-26

Status: BOUNDED IMPLEMENTATION / PROOF PENDING

## Purpose

PR #24 established production-dialect PostgreSQL evidence for the durable heartbeat/fencing primitives used by the Austria K.1 path. This follow-up starts the next controlled M6 adoption surface without creating a second runtime-state model: the existing governed E.2 eligibility producer can now be invoked through an AIOS-owned fenced runtime envelope.

This is an ADAPT of the useful runtime-liveness idea only. AIOS remains the authority for WorkItems, OrganizationExecutionAttempt, heartbeat/fence state, ContextBundles, Evidence, VerifiedRules, Command Gateway decisions, and canonical eligibility effects.

## What this slice adds

`organization_eligibility_runtime_session.py` wraps the already-governed `governed_eligibility_transition_intent` function with operational execution provenance:

- validates the canonical tenant-bound proposal WorkItem and assigned OrganizationPosition;
- validates queued context/runtime binding before mutating operational WorkItem state;
- transitions queued work to running through the existing organization-work command path;
- re-resolves the running-state ContextBundle/runtime binding and uses those hashes in the execution token;
- creates a bounded `OrganizationExecutionAttempt` and generation-one `attempt_started` heartbeat;
- runs E.2 under the existing `ExecutionRuntimeSessionSupervisor`;
- stages terminal completion only for the current fresh fence;
- completes the same WorkItem through the existing organization-work transition after E.2 returns successfully;
- on failure, mutates attempt/work failure provenance only if the failing worker still owns the current execution token/fence/writer generation;
- refuses to let a superseded worker mutate canonical work state after a takeover.

No migration and no new runtime-state table are introduced.

## Deliberate non-changes

The envelope does not replace or weaken E.2. The underlying producer still owns:

- governed ContextBundle construction;
- runtime-profile/provider binding validation;
- case/pathway/Evidence/VerifiedRule validation;
- canonical eligibility revision preconditions;
- typed LLM output validation;
- post-provider context/revision revalidation;
- material-action construction;
- Command Gateway authority/autonomy/risk evaluation;
- durable governance-attempt activity.

Runtime lease/fence state remains technical execution-health provenance only. It does not establish human/provider/model/employee online status, grant authority or autonomy, change governed truth, authorize an external action, or create a canonical eligibility effect.

## Adoption boundary

This PR intentionally exposes a domain-specific fenced E.2 execution entry point rather than rewriting the existing G.4 orchestrator immediately. The current G.4 orchestration path still calls the legacy E.2 function directly. That wiring, independent-verifier adoption, stale-session takeover/resume for this second vertical, and additional organization-worker paths remain follow-up work.

This bounded step follows `AGENTS.md`: extract a proven seam from the K.1 runtime contract into a concrete second vertical, rather than performing a speculative generic runtime rewrite while Milestone L acceptance is still open.

## Required proof

Before this PR can leave Draft, prove on the exact head:

1. focused SQLite contracts for successful terminal fencing and failure ownership;
2. real PostgreSQL execution of the eligibility runtime renewal test, with `runtime_session_renewed` observed between `attempt_started` and `agent_completed`;
3. existing PR #20–#24 fencing/supervisor/takeover regression surface;
4. governed eligibility orchestration/runtime-health/revision-race contracts;
5. repository policy, release consistency, dependency constraints, diff hygiene, and clean Git status.

A PostgreSQL-only test that is skipped does not satisfy item 2.

## M6 status

M6 remains PARTIAL.

The current bounded adoption sequence is now:

1. durable checkpoint heartbeat lease;
2. runtime-session fencing;
3. bounded active renewal supervisor;
4. stale-session takeover/re-execution for Austria K.1;
5. real PostgreSQL concurrency proof;
6. eligibility E.2 fenced runtime envelope (this slice, proof pending).

Still outstanding: production-orchestrator wiring for E.2, verifier-side adoption, takeover/resume for the eligibility envelope, broader worker-path coverage, and exact-head production/Woodpecker acceptance where available.
