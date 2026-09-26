# Global Mobility AIOS — Session Handoff

**Purpose:** minimal cold-start recovery pointer. This file must not duplicate project history, architecture, roadmap sequencing, or CI ledgers.

**Last reconciled:** 2026-09-27

## Resume coordinates

Canonical integration branch:

`design/aios-v2-complete-redesign`

Do not trust a copied “current head” in prose. Resolve the branch SHA directly from GitHub before branching, reviewing, or merging.

Current programme:

`Phase 17 — Agent Security Assurance`

Next bounded slice:

`Inspect the next concrete Phase 17 agent tool-invocation or skill/tool provenance boundary. The governed allowed_tools intersection exists in the runtime binding, but current inspected execution paths expose no agent tool_id/action dispatch API to enforce it. Introduce a bounded check only at a real executable seam; keep Phase 16 billing/vendor-cost attribution, Board USD allocation/pre-call monetary enforcement, and Gemini output-cap verification separate and open.`

Last meaningful runtime implementation checkpoint:

- PR #210 — in-house consultant prompt trust boundary, merged as `1c7fd864f9c6d84339b3d4b651dfe2e819ab32a2`. The operator message, recent conversation, lead records, and UI lead hint remain in the lower-trust provider user envelope; trusted role/output instructions and existing validation, accounting, and owner-completion boundaries remain intact. Earlier Phase 17D–17F prompt boundaries are sealed by PR #206–#208.

This is a recovery checkpoint, not a claim about the live integration head after later documentation or implementation merges.

## Fresh-session procedure

1. Start at `AGENTS.md` and follow its canonical chain.
2. Read `agents/PROJECT_STATE.md` for the active Phase 17 boundary and the still-open Phase 16 monetary-evidence guardrails.
3. Read the Phase 17 and immediate-order sections of `docs/ROADMAP.md`.
4. Inspect the actual runtime router, skill, and external-action paths on the verified live base for a concrete tool invocation seam. `organization_agent_runtime.py` derives a binding allowance, while the current Austria live provider profile has no tools and the controlled-agent model call has no tool dispatch. Keep automation delivery's separate human-review/connector gates distinct. Do not infer an agent authorization boundary from a diagnostic binding alone.
5. Resolve the live integration branch and any active PR from GitHub before changing code.
6. Search for existing security, authority, permission, credential, tool, skill, provenance, incident and audit evidence before adding models or abstractions.

## Runtime cost truth boundary

`estimated_cost_usd` remains diagnostic evidence, not billing truth. The sealed ledger covers direct model calls through AgentRun or unique operation identity. The in-house consultant and business advisory now record explicit owner-completion evidence keyed by their existing request operation identities, allowing a still-`started` attempt to reconcile to `outcome_unknown` only after its real owner signal. Other request-local paths without an explicit real owner signal remain unreconciled by age alone. No owner-completion marker infers provider failure, refund, zero usage, completed external effect, or releases its call slot; no invented WorkItem or AgentRun owner is permitted.

For enrolled providers, an admin-operated cumulative call count is reserved before each direct model call, including retries; it is no monetary grant. Independently, optional DeepSeek/Moonshot settings cap generated tokens per call; Gemini has no verified cap on its current compatibility path. The admin-only cost-evidence readout reports partial estimates, optional provider completion IDs, and unknown actual spend; neither an ID nor a populated billed-cost column has authoritative invoice provenance at this boundary. The roadmap inventories external-call paths, but paid-tool vendor charges remain to be reconciled. Keep authorized budget, observed actual provider/tool spend, and estimates/unattributed cost separate. A hard monetary budget requires source-linked cost evidence, Board authority, paid-tool coverage, and a provable pre-call ceiling. Cancellation does not imply refund or rollback of spend already incurred.

Explicit AgentRun cancellation is already sealed by PR #176. Its non-terminating Celery revoke and no-rollback semantics remain intact while later security and budget controls are added.

No Jev, Laya, or Google AX production dependency is approved by the current programme state.

## Handoff discipline

If the next session needs more than this pointer, follow `AGENTS.md` to the owning source. Do not expand this file into another `PROJECT_STATE`, roadmap, architecture document, or acceptance history.
