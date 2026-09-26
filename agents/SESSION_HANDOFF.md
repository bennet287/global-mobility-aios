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

`inspect remaining model-input/output trust crossings plus native-skill/tool provenance and entitlement enforcement, then select the smallest concrete Phase 17 control from repository evidence. Reuse existing identity, authority, permission, provenance and audit truth. Phase 16 billing/vendor-cost attribution, Board USD allocation/pre-call monetary enforcement, and Gemini output-cap verification remain separate open prerequisites.`

Last meaningful runtime implementation checkpoint:

- PR #208 — controlled-agent prompt trust boundary, merged as `61af5338f086321d2c739296496d86c1ffc633b3`. The role-card system prompt keeps trusted guardrails and canonical output schema; the provider user envelope carries only `operator_task` and `untrusted_context`, with adversarial regression proving injected context cannot enter the trusted system message.
- PR #207 — business-advisory prompt trust boundary, merged as `7071abdc65d75054f17154d5ac6d2dc5024ef5e7`.
- PR #206 — regulatory classifier prompt trust boundary, merged as `e2e2436ff18743108a7c5c190bac36b8ce282a37`.
- Phase 17C is sealed through PR #205 at merge `c6816dc59e754db3e8ec8fa36551d065a9ca6a10`: admin connector control remains separate from webhook HTTPS/public-address validation and pinned-IP connection-time egress enforcement.

This is a recovery checkpoint, not a claim about the live integration head after later documentation or implementation merges.

## Fresh-session procedure

1. Start at `AGENTS.md` and follow its canonical chain.
2. Read `agents/PROJECT_STATE.md` for the active Phase 17 boundary and the still-open Phase 16 monetary-evidence guardrails.
3. Read the Phase 17 and immediate-order sections of `docs/ROADMAP.md`.
4. Inspect remaining concrete model-input/output crossings and native-skill/tool provenance/entitlement checks before changing security semantics; keep existing deterministic, human-review, authority and audit boundaries intact.
5. Resolve the live integration branch and any active PR from GitHub before changing code.
6. Search for existing security, authority, permission, credential, tool, skill, provenance, incident and audit evidence before adding models or abstractions.

## Runtime cost truth boundary

`estimated_cost_usd` remains diagnostic evidence, not billing truth. The sealed ledger covers direct model calls through AgentRun or unique operation identity. The in-house consultant and business advisory now record explicit owner-completion evidence keyed by their existing request operation identities, allowing a still-`started` attempt to reconcile to `outcome_unknown` only after its real owner signal. Other request-local paths without an explicit real owner signal remain unreconciled by age alone. No owner-completion marker infers provider failure, refund, zero usage, completed external effect, or releases its call slot; no invented WorkItem or AgentRun owner is permitted.

For enrolled providers, an admin-operated cumulative call count is reserved before each direct model call, including retries; it is no monetary grant. Independently, optional DeepSeek/Moonshot settings cap generated tokens per call; Gemini has no verified cap on its current compatibility path. The admin-only cost-evidence readout reports partial estimates, optional provider completion IDs, and unknown actual spend; neither an ID nor a populated billed-cost column has authoritative invoice provenance at this boundary. The roadmap inventories external-call paths, but paid-tool vendor charges remain to be reconciled. Keep authorized budget, observed actual provider/tool spend, and estimates/unattributed cost separate. A hard monetary budget requires source-linked cost evidence, Board authority, paid-tool coverage, and a provable pre-call ceiling. Cancellation does not imply refund or rollback of spend already incurred.

## Phase 17 trust boundary

Phase 17A/17B bound session replay lifetime and debug-route exposure using existing authentication and role policy. Phase 17C closes the identified connector configuration and webhook egress boundary without creating a second connector or permission store. Phase 17D/17E/17F keep trusted policy/output contracts in provider system prompts while treating regulatory evidence, client/business evidence and controlled-agent context as lower-trust user content. These prompt controls do not grant tool use, external mutation, canonical truth changes or authority; existing deterministic and human-review gates remain authoritative.

Explicit AgentRun cancellation is already sealed by PR #176. Its non-terminating Celery revoke and no-rollback semantics remain intact while later security and budget controls are added.

No Jev, Laya, or Google AX production dependency is approved by the current programme state.

## Handoff discipline

If the next session needs more than this pointer, follow `AGENTS.md` to the owning source. Do not expand this file into another `PROJECT_STATE`, roadmap, architecture document, or acceptance history.
