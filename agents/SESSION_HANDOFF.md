# Global Mobility AIOS — Session Handoff

**Purpose:** minimal cold-start recovery pointer. This file must not duplicate project history, architecture, roadmap sequencing, or CI ledgers.

**Last reconciled:** 2026-09-25

## Resume coordinates

Canonical integration branch:

`design/aios-v2-complete-redesign`

Do not trust a copied “current head” in prose. Resolve the branch SHA directly from GitHub before branching, reviewing, or merging.

Current programme:

`Phase 17 — Agent Security Assurance`

Next bounded slice:

`inspect why /debug is currently included in the public-path authentication policy, enumerate the actual debug-route payloads and production exposure, then select the smallest justified Phase 17 hardening without creating parallel identity/authority/security truth. Phase 16 billing/vendor-cost attribution, Board USD allocation/pre-call monetary enforcement, and Gemini output-cap verification remain separate open prerequisites.`

Last meaningful runtime implementation checkpoint:

- PR #198 — bounded authenticated session lifetime, merged as `b553d067160130b6b6b56bb710691697bc3bf8d0`. Existing signed application sessions are versioned and expire under one bounded TTL policy; old timeless cookies fail closed and require a fresh login.

This is a recovery checkpoint, not a claim about the live integration head after later documentation or implementation merges.

## Fresh-session procedure

1. Start at `AGENTS.md` and follow its canonical chain.
2. Read `agents/PROJECT_STATE.md` for the active Phase 17 boundary and the still-open Phase 16 monetary-evidence guardrails.
3. Read the Phase 17 and immediate-order sections of `docs/ROADMAP.md`.
4. Inspect the existing auth public-path rules and concrete `/debug` routes before changing exposure; keep public client/partner APIs distinct from debug surfaces.
5. Resolve the live integration branch and any active PR from GitHub before changing code.
6. Search for existing security, authority, permission, credential, tool, skill, provenance, incident and audit evidence before adding models or abstractions.

## Runtime cost truth boundary

`estimated_cost_usd` remains diagnostic evidence, not billing truth. The sealed ledger covers direct model calls through AgentRun or unique operation identity. The in-house consultant and business advisory now record explicit owner-completion evidence keyed by their existing request operation identities, allowing a still-`started` attempt to reconcile to `outcome_unknown` only after its real owner signal. Other request-local paths without an explicit real owner signal remain unreconciled by age alone. No owner-completion marker infers provider failure, refund, zero usage, completed external effect, or releases its call slot; no invented WorkItem or AgentRun owner is permitted.

For enrolled providers, an admin-operated cumulative call count is reserved before each direct model call, including retries; it is no monetary grant. Independently, optional DeepSeek/Moonshot settings cap generated tokens per call; Gemini has no verified cap on its current compatibility path. The admin-only cost-evidence readout reports partial estimates, optional provider completion IDs, and unknown actual spend; neither an ID nor a populated billed-cost column has authoritative invoice provenance at this boundary. The roadmap inventories external-call paths, but paid-tool vendor charges remain to be reconciled. Keep authorized budget, observed actual provider/tool spend, and estimates/unattributed cost separate. A hard monetary budget requires source-linked cost evidence, Board authority, paid-tool coverage, and a provable pre-call ceiling. Cancellation does not imply refund or rollback of spend already incurred.

Explicit AgentRun cancellation is already sealed by PR #176. Its non-terminating Celery revoke and no-rollback semantics remain intact while later security and budget controls are added.

No Jev, Laya, or Google AX production dependency is approved by the current programme state.

## Handoff discipline

If the next session needs more than this pointer, follow `AGENTS.md` to the owning source. Do not expand this file into another `PROJECT_STATE`, roadmap, architecture document, or acceptance history.
