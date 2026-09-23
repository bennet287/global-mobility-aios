# Global Mobility AIOS — Project State

**Purpose:** concise recovery dashboard. This is a living pointer, not an acceptance ledger. Historical proof remains in Git history and phase-specific records.

**Last reconciled:** 2026-09-23
**Canonical integration branch:** `design/aios-v2-complete-redesign`
**Current integration head:** `14d7bfdd238ca93a10310541702c216fc9561f4b` (PR #171 merge)
**Current programme:** Phase 16 — Runtime Reliability, Metering and Orchestration Foundations
**Active implementation:** none; AgentRun soft-timeout semantics are sealed by PR #171
**Next scheduled slice:** finish the bounded timeout/cancellation tranche with hard-limit/stale-run reconciliation and explicit cancellation semantics, reusing existing AgentRun/Celery truth

## Current programme state

- Phase 13G Living HQ flagship convergence — SEALED.
- Autonomous Regulatory Intelligence RI.A1–RI.A8 — SEALED. Production machine publication and machine recovery remain OFF unless separately authorized.
- Phase 14 Native Skills Registry — SEALED.
- Phase 15 Agent Lifecycle Governance Hooks — SEALED through lifecycle, connector/tool signals and AgentRun runtime signals.
- Phase 16.1 Runtime Metering — SEALED by PR #165; provider/model/token/estimated-cost observations are diagnostic evidence, not billing truth.
- Phase 16.2 Runtime Reliability — SEALED by PR #166; failure classification precedes retry and only provider transport failures retry.
- PR #167 System-1 / orchestration evaluation — MERGED at `896e338e77c9ecf797a7f26f676cb10b18ae5c18`. Jev and Laya remain benchmark candidates; Google AX remains deferred execution-substrate evaluation. None is a production dependency.
- AgentRun runtime soft-timeout semantics — SEALED by PR #171 at merge `14d7bfdd238ca93a10310541702c216fc9561f4b`. Existing Celery limits remain canonical: 240s soft / 300s hard. A soft timeout records durable `agent_run_runtime_timeout` evidence and terminates the existing AgentRun as `failed`; it is non-retryable.

## Current Phase 16 boundary

Canonical runtime truth remains in existing AIOS models and services. Do not create parallel runtime state merely to add timeout, cancellation, budget, breaker or model-decision features.

- `AgentRun` = execution-history truth.
- `OrganizationAgent` = durable lifecycle/identity truth.
- `CONTROLLED_AGENT_REGISTRY` = static implementation-definition truth.
- Phase 16.1 provider usage evidence is observed runtime telemetry; `estimated_cost_usd` is not billed spend.
- Phase 16.2 deterministic failure classification is authoritative for current retry behavior.
- PR #171 reuses existing Celery worker limits rather than introducing a second timeout configuration.
- Soft timeout is not equivalent to hard-kill reconciliation or explicit operator cancellation. Those remain unimplemented and must not be claimed as complete.
- Jev/Laya may later provide bounded advisory System-1 decisions only after benchmark evidence.
- Google AX may later provide replaceable execution infrastructure only after AIOS owns timeout/cancellation, hard runtime budgets, actual cost metering, circuit breakers and reconciliation.
- Deterministic AIOS policy remains authoritative. External decision/runtime systems receive no authority, permissions, credentials, budgets, autonomy or assignment rights.

## Next slice guardrails

Before implementing cancellation or hard-limit reconciliation, inspect existing Celery task identity, AgentRun enqueue paths, worker lifecycle, and any existing stale-run cleanup. Reuse the current AgentRun and audit boundaries. Do not introduce a second execution-state table merely to represent cancellation.

The next slice should distinguish three facts cleanly:

1. cooperative soft timeout — already sealed by PR #171;
2. hard worker termination / stale `running` reconciliation — still unresolved;
3. explicit cancellation request and observable terminal outcome — still unresolved.

No slice may imply that external side effects can be rolled back merely because an AgentRun is cancelled.

## Canonical read order

1. `docs/ROADMAP.md` — product/programme scheduler and architectural law.
2. `docs/PHASE_16_SYSTEM1_ORCHESTRATION_DECISIONS_2026-09-23.md` — current Jev/Laya/AX decision record.
3. `docs/aios-v2/README.md` — V2 companion entry point.
4. `docs/aios-v2/AIOS_V2_COMPLETE_REDESIGN_MASTER_PLAN.md` — destination and acceptance model.
5. `docs/aios-v2/AIOS_V2_EMPLOYEE_CAPABILITY_AND_SKILLS_ARCHITECTURE.md` — employee/capability architecture.
6. `AGENTS.md` and `agents/AIOS_AGENT_EXECUTION_PLAYBOOK.md` — engineering/proof discipline.
7. Actual GitHub PR, commit and workflow state — authoritative for current implementation status.

## Permanent project laws

- Canonical truth changes require evidence stronger than the proposing AI.
- Memory is not truth; conversation is not authority; telemetry is not canonical organization state.
- Capability != authority; authority != autonomy; autonomy != risk.
- Living HQ is a projection of canonical state, never a second operational truth.
- Prefer deterministic logic around model reasoning.
- External side effects require explicit authority, idempotency and reconciliation.
- Every new abstraction must remove more complexity from the user's life than it adds to AIOS.
- Finish existing capability chains before inventing new ones.
- Failure classification before retry.
- Human attention is a scarce organizational resource.
- Durability and control cost must be proportional to consequence.

## Exact-head acceptance and closure

For every slice:

`verified sealed base -> duplicate/stale archaeology -> bounded feature branch -> focused tests -> Draft PR -> exact-head CI -> independent patch/scope audit -> Ready -> merge with expected head SHA -> verify actual merge SHA -> reconcile living docs/handoff -> seal`

A slice is not closed while living recovery documents materially describe an older programme state. Historical phase records may remain for traceability, but do not create another current-state document.
