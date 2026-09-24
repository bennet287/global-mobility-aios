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

`itemized provider billing evidence and verified per-attempt reconciliation; paid-tool vendor contracts and attributable costs before governed USD allocation; verify Gemini output-cap compatibility separately`

Last meaningful runtime implementation checkpoint:

- PR #189 — optional provider completion IDs on the direct-model attempt ledger and an external-call cost-exposure inventory, merge `67a667181fbdb8b875fd6557589bb94649013f76`.

This is a recovery checkpoint, not a claim about the live integration head after later documentation or implementation merges.

## Fresh-session procedure

1. Start at `AGENTS.md` and follow its canonical chain.
2. Read `agents/PROJECT_STATE.md` for the active Phase 16 boundary and budget/metering guardrails.
3. Read the Phase 16 scheduling and immediate-order sections of `docs/ROADMAP.md`.
4. Inspect the sealed Phase 16.3A–F ledger, capacity, optional adapter limits, cost-evidence readout, response identity and external-call inventory alongside paid-tool contracts and existing budget/allocation models before designing new state.
5. Resolve the live integration branch and any active PR from GitHub before changing code.
6. Search for existing cost, usage, allocation, budget, retry and cancellation evidence before adding models or abstractions.

## Runtime cost truth boundary

`estimated_cost_usd` remains diagnostic evidence, not billing truth. The sealed ledger covers direct model calls through AgentRun or unique operation identity; request-local calls have no invented WorkItem owner. For enrolled providers, an admin-operated cumulative call count is reserved before each direct model call, including retries; it is no monetary grant. Independently, optional DeepSeek/Moonshot settings cap generated tokens per call; Gemini has no verified cap on its current compatibility path. The admin-only cost-evidence readout reports partial estimates, optional provider completion IDs, and unknown actual spend; neither an ID nor a populated billed-cost column has authoritative invoice provenance at this boundary. The roadmap inventories external-call paths, but paid-tool vendor charges remain to be reconciled. Keep authorized budget, observed actual provider/tool spend, and estimates/unattributed cost separate. A hard monetary budget requires source-linked cost evidence, Board authority, paid-tool coverage, and a provable pre-call ceiling. Cancellation does not imply refund or rollback of spend already incurred.

Explicit AgentRun cancellation is already sealed by PR #176. Its non-terminating Celery revoke and no-rollback semantics remain intact while budget controls are added.

No Jev, Laya, or Google AX production dependency is approved by the current programme state.

## Handoff discipline

If the next session needs more than this pointer, follow `AGENTS.md` to the owning source. Do not expand this file into another `PROJECT_STATE`, roadmap, architecture document, or acceptance history.
