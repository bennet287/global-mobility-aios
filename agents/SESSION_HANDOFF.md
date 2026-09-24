# Global Mobility AIOS — Session Handoff

**Purpose:** minimal cold-start recovery pointer. This file must not duplicate project history, architecture, roadmap sequencing, or CI ledgers.

**Last reconciled:** 2026-09-24

## Resume coordinates

Canonical integration branch:

`design/aios-v2-complete-redesign`

Do not trust a copied “current head” in prose. Resolve the branch SHA directly from GitHub before branching, reviewing, or merging.

Current programme:

`Phase 16 — Runtime Reliability, Metering and Orchestration Foundations`

Next bounded slice:

`governed allocation and hard per-call budget enforcement after reconciling other paid paths and billing evidence`

Last meaningful runtime implementation checkpoint:

- PR #179 — controlled AgentRun provider-attempt ledger, merge `b42a0126aa5ee7c6e9733c1a6dd9240321af08ae`.

This is a recovery checkpoint, not a claim about the live integration head after later documentation or implementation merges.

## Fresh-session procedure

1. Start at `AGENTS.md` and follow its canonical chain.
2. Read `agents/PROJECT_STATE.md` for the active Phase 16 boundary and budget/metering guardrails.
3. Read the Phase 16 scheduling and immediate-order sections of `docs/ROADMAP.md`.
4. Inspect the sealed Phase 16.3A controlled-AgentRun ledger, every other real paid execution path, and any existing budget/allocation models before designing new state.
5. Resolve the live integration branch and any active PR from GitHub before changing code.
6. Search for existing cost, usage, allocation, budget, retry and cancellation evidence before adding models or abstractions.

## Runtime cost truth boundary

`estimated_cost_usd` remains diagnostic evidence, not billing truth. The sealed ledger accounts for controlled AgentRun attempts only; other provider consumers need separately governed attribution. Keep authorized budget, observed actual provider/tool spend, and estimates/unattributed cost separate. Budget exhaustion may stop or pause new paid execution only through an explicit governed runtime boundary; an agent may request more allocation but may not grant itself budget. Cancellation does not imply refund or rollback of spend already incurred.

Explicit AgentRun cancellation is already sealed by PR #176. Its non-terminating Celery revoke and no-rollback semantics remain intact while budget controls are added.

No Jev, Laya, or Google AX production dependency is approved by the current programme state.

## Handoff discipline

If the next session needs more than this pointer, follow `AGENTS.md` to the owning source. Do not expand this file into another `PROJECT_STATE`, roadmap, architecture document, or acceptance history.
