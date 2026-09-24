# Global Mobility AIOS — Project State

**Purpose:** concise current programme truth and the next bounded slice. This file is a living state pointer, not an acceptance ledger, read-order document, or historical changelog.

**Last reconciled:** 2026-09-24
**Canonical integration branch:** `design/aios-v2-complete-redesign`
**Live integration head:** resolve from GitHub before dependent work; do not treat a SHA copied into this file as self-updating truth.
**Current programme:** Phase 16 — Runtime Reliability, Metering and Orchestration Foundations
**Active implementation:** none; direct model-call coverage, call capacity, opt-in output caps, and read-only cost-evidence visibility are sealed
**Next scheduled slice:** source-linked billing reconciliation and paid-tool cost inventory before governed USD allocation; verify Gemini's output-cap contract separately

## Current programme state

- Phase 13G Living HQ flagship convergence — SEALED.
- Autonomous Regulatory Intelligence RI.A1–RI.A8 — SEALED. Production machine publication and machine recovery remain OFF unless separately authorized.
- Phase 14 Native Skills Registry — SEALED.
- Phase 15 Agent Lifecycle Governance Hooks — SEALED through lifecycle, connector/tool signals, and real background `AgentRun` lifecycle evidence.
- Phase 16.1 Runtime Metering — SEALED by PR #165; provider/model/token/estimated-cost observations are diagnostic evidence, not billing truth.
- Phase 16.2 Runtime Reliability — SEALED by PR #166; deterministic failure classification precedes retry and only provider transport failures retry.
- Phase 16.3A Runtime Economics Ledger — SEALED by PR #179 at merge `b42a0126aa5ee7c6e9733c1a6dd9240321af08ae`. Controlled AgentRun provider attempts are durably recorded before the paid call and settled with observed usage or unknown outcome. Estimates remain non-billing evidence.
- Phase 16.3B Provider-call Coverage — SEALED by PR #181 at merge `258678f0ba13af2401d5039f8d5c5e6d97a56d2d`. The same attempt ledger covers every direct model-call site, including E.1/E.2/G.1 WorkItems, regulatory classification, consultant, and business advisory. Existing AgentRun evidence survives the table migration. Calls without AgentRuns carry an operation identity and honest work-item or request-local context. This grants no allocation or hard monetary budget; billed cost remains unknown without authoritative evidence.
- Phase 16.3C Provider Call Capacity — SEALED by PR #183 at merge `c4ff79ff189d7f4a1521e226365cacc9b1c9f5e8`. An admin may enroll a provider with a cumulative call allowance or pause it. Each direct model-call attempt atomically consumes one slot before the provider call; exhausted or paused providers fail closed. Retry, failed, and unknown-outcome attempts retain their slot. Unenrolled providers keep their existing behavior. This operational call-count allowance grants no monetary budget or Board spending authority.
- Phase 16.3D Provider Output Caps — SEALED by PR #185 at merge `15735f3815d007390b1c5c87530881527450ae19`. Optional positive environment settings send DeepSeek `max_tokens` or Moonshot `max_completion_tokens` on each adapter request; invalid values stop before network egress. No cap is configured by default. Gemini's OpenAI-compatibility output-cap contract remains unverified. These caps do not bound input tokens, billed cost, or paid tools.
- Phase 16.3E Cost Evidence Visibility — SEALED by PR #187 at merge `c2cf9614742f2d1338761946380f50a58756a39e`. An admin-only, read-only report aggregates the existing direct-model attempt ledger by provider, distinguishing observed usage, partial estimates, unknown outcomes, and unaudited billed values. Actual billed spend, authorized/remaining USD, and monetary enforceability stay unknown/blocked. Paid-tool cost coverage remains unreconciled.
- System-1 / orchestration evaluation — PR #167 MERGED. Jev and Laya remain benchmark candidates; Google AX remains a deferred execution-substrate evaluation. None is a production dependency.
- AgentRun cooperative soft-timeout semantics — SEALED by PR #171. Existing Celery limits remain canonical: 240s soft / 300s hard. Soft timeout records durable `agent_run_runtime_timeout` evidence, terminates the existing AgentRun as `failed`, and is non-retryable.
- AgentRun stale-running reconciliation — SEALED by PR #173 at merge `c4ff75f24801eb52a82da2ac09cc724ffe872534`. It uses existing AgentRun + AuditLog truth, waits for the 300s hard limit plus 60s grace, requires durable running-state evidence, records stale-running reconciliation, and deliberately does not infer that the underlying cause was definitely a hard kill.
- PR #174 merged the living-document closure for PR #173 at `7e107b1689c576546f56812d280edc4c6c9f6558`; it changed documentation only and does not represent an additional runtime capability.
- Explicit AgentRun cancellation — SEALED by PR #176 at merge `b867fb28c06c2f25390574b4e1a69211d1f622dd`. It reuses `AgentRun` + `AuditLog`, adds canonical `cancel_requested` / `cancelled` statuses, binds Celery task identity deterministically to `AgentRun.id`, serializes worker claim and cancellation on the AgentRun row, and keeps broker revoke non-terminating (`terminate=False`). Queued work becomes terminal `cancelled`; running work becomes `cancel_requested` until the worker observes durable intent and finalizes `cancelled`. Cancellation intent outranks timeout/failure classification once durable evidence exists, and stale `cancel_requested` runs reconcile after the existing hard-limit + grace boundary. No rollback of already-performed side effects is claimed.

## Current Phase 16 boundary

Canonical runtime truth remains in existing AIOS models and services. Do not create parallel runtime state merely to add timeout, cancellation, budget, breaker, or model-decision features.

- `AgentRun` = execution-history truth.
- `OrganizationAgent` = durable lifecycle/identity truth.
- `CONTROLLED_AGENT_REGISTRY` = static implementation-definition truth.
- `AuditLog` = existing durable audit/evidence boundary where the accepted service uses it.
- Phase 16.1 provider usage evidence is observed runtime telemetry; `estimated_cost_usd` is not billed spend.
- Phase 16.3A/B `ProviderCallAttempt` is one paid-call accounting ledger: controlled AgentRuns are keyed by run and attempt; other model calls have unique operation keys and source contexts. It does not represent invoices; `billed_cost_usd` remains unknown without authoritative provider evidence.
- Phase 16.3C `ProviderCallAllocation` is an opt-in, admin-operated per-provider call-count ceiling, consumed atomically with the attempt record. It does not measure money, grant Board spending authority, cover paid tools, or constrain an enrolled call's output tokens.
- Phase 16.3D's independent, optional adapter settings cap generated tokens per DeepSeek/Moonshot request; they do not convert the call-count allowance into a financial budget.
- Phase 16.3E's readout uses existing attempt truth; even a non-null `billed_cost_usd` lacks invoice/reference provenance and is not authoritative spend. It grants no spending authority or new runtime control.
- Phase 16.2 deterministic failure classification is authoritative for current retry behavior.
- Cooperative soft timeout, stale-running reconciliation, and explicit cancellation are separate accepted controls with different evidence semantics.
- Explicit cancellation is admin-only for the accepted API boundary. A Celery revoke request is best-effort transport control, not proof of process termination, rollback, or absence of prior external effects.
- Existing `OrganizationalWorkItem.cancel_requested_at` remains WorkItem governance truth and is not AgentRun cancellation state.
- Jev/Laya may later provide bounded advisory System-1 decisions only after benchmark evidence.
- Google AX may later provide replaceable execution infrastructure only after AIOS owns the required canonical runtime controls.
- Deterministic AIOS policy remains authoritative. External decision/runtime systems receive no authority, permissions, credentials, budgets, autonomy, or assignment rights.

## Next slice guardrails — monetary budget prerequisites and Gemini output-cap evidence

Phase 16.3C's opt-in call-count ceiling and Phase 16.3D's optional DeepSeek/Moonshot per-call output limits are distinct controls, neither a financial allocation. Phase 16.3E exposes the missing evidence without manufacturing a spend number. Before monetary budget enforcement, inventory cost-bearing paid tools beyond direct model calls, obtain source-linked per-call provider billing/reconciliation where available, and define Board allocation authority, retry/cancellation treatment, and a provable pre-call monetary ceiling. Verify Gemini's compatible output-cap request contract before claiming a Gemini limit. Request-local calls have no invented WorkItem or AgentRun owner.

Do not promote `estimated_cost_usd` or token estimates into billing truth. Keep at least these facts separate:

1. authorized budget / allocation;
2. observed actual provider or paid-tool spend where authoritative evidence exists;
3. estimated or unattributed cost where authoritative evidence does not exist.

The slice must define how spend is attributed without double-counting retries or cancelled work, how remaining budget is computed only from authoritative evidence, which provider-specific pre-call limit can bound actual spend rather than only generated tokens, which runtime boundary pauses or stops new paid execution when budget is exhausted, and how additional allocation can be requested without self-granting authority. If no authoritative cost and enforceable monetary ceiling exist, do not claim a hard USD budget. Cancellation does not imply refund or rollback of spend already incurred.

Prefer extending existing canonical runtime/evidence models and services. Introduce a new durable budget/allocation record only if no existing canonical owner can truthfully represent authorized budget state.

## Permanent project laws relevant to the active programme

- Canonical truth changes require evidence stronger than the proposing AI.
- Memory is not truth; conversation is not authority; telemetry is not canonical organization state.
- Capability != authority; authority != autonomy; autonomy != risk.
- Prefer deterministic logic around model reasoning.
- External side effects require explicit authority, idempotency, and reconciliation.
- Reuse canonical state before introducing another table/model/store.
- Failure classification before retry.
- Human attention is a scarce organizational resource.
- Durability and control cost must be proportional to consequence.

## State-document rule

Do not add historical proof logs, universal read orders, repository mechanics, or duplicate architecture to this file. After a sealed implementation slice, update only the programme facts that materially changed and the next bounded slice. GitHub owns exact current branch/PR/workflow state; `docs/ROADMAP.md` owns remaining programme order; `agents/SESSION_HANDOFF.md` remains only the minimal recovery pointer.
