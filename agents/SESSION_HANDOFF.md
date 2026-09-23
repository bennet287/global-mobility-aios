# Global Mobility AIOS — Session Handoff

**Purpose:** minimal cold-start recovery pointer. This file must not duplicate project history, architecture, roadmap sequencing, or CI ledgers.

**Last reconciled:** 2026-09-23

## Resume coordinates

Canonical integration branch:

`design/aios-v2-complete-redesign`

Do not trust a copied “current head” in prose. Resolve the branch SHA directly from GitHub before branching, reviewing, or merging.

Current programme:

`Phase 16 — Runtime Reliability, Metering and Orchestration Foundations`

Next bounded slice:

`explicit AgentRun cancellation semantics through the existing AgentRun/Celery boundary`

Last meaningful runtime implementation checkpoint:

- PR #173 — stale-running reconciliation, merge `c4ff75f24801eb52a82da2ac09cc724ffe872534`.
- PR #174 — documentation closure for that implementation, merge `7e107b1689c576546f56812d280edc4c6c9f6558`.

These are recovery checkpoints, not claims about the live integration head after later documentation or implementation merges.

## Fresh-session procedure

1. Start at `AGENTS.md` and follow its canonical chain.
2. Read `agents/PROJECT_STATE.md` for the active programme boundary and cancellation guardrails.
3. Read the Phase 16 scheduling section of `docs/ROADMAP.md`.
4. For the cancellation slice, read `docs/PHASE_16_SYSTEM1_ORCHESTRATION_DECISIONS_2026-09-23.md` only as relevant architectural/decision context, then inspect the actual AgentRun/Celery enqueue/task/status/API paths and focused tests.
5. Resolve the live integration branch and any active PR from GitHub before changing code.
6. Search for existing cancellation/task-identity/audit patterns before adding state or abstractions.

## Cancellation truth boundary

Keep explicit cancellation separate from the already-sealed cooperative soft timeout and stale-running reconciliation paths. Existing `OrganizationalWorkItem.cancel_requested_at` belongs to WorkItem governance and is not AgentRun cancellation truth. A Celery revoke/cancel request does not prove rollback or prove that no external side effect occurred.

No Jev, Laya, or Google AX production dependency is approved by the current programme state.

## Handoff discipline

If the next session needs more than this pointer, follow `AGENTS.md` to the owning source. Do not expand this file into another `PROJECT_STATE`, roadmap, architecture document, or acceptance history.
