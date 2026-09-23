# Global Mobility AIOS — Project State

**Purpose:** concise recovery dashboard. This is a living pointer, not an acceptance ledger. Historical proof remains in Git history and phase-specific records.

**Last reconciled:** 2026-09-23
**Canonical integration branch:** `design/aios-v2-complete-redesign`
**Verified integration head before the active slice:** `896e338e77c9ecf797a7f26f676cb10b18ae5c18` (PR #167 merge)
**Current programme:** Phase 16 — Runtime Reliability & Economic Metering
**Active implementation:** `phase-16-runtime-timeout-reconciliation`
**Next acceptance action:** exact-head CI and patch/scope audit; merge only after the candidate is green and unchanged.

## Current programme state

- Phase 13G Living HQ flagship convergence — SEALED.
- Autonomous Regulatory Intelligence RI.A1–RI.A8 — SEALED. Production machine publication and machine recovery remain OFF unless separately authorized.
- Phase 14 Native Skills Registry — SEALED through governed skill-informed work assignment.
- Phase 15 Agent Lifecycle Governance — SEALED through lifecycle, connector/tool-use and AgentRun runtime signals.
- Phase 16.1 provider usage observation — SEALED; merge `8b13f8b8fc3a4bf922a873fe35ab7490307132b0`.
- Phase 16.2 failure classification/retry policy — SEALED; merge `9ca583cb3a38c2cee33d2558ada9995106758cd9`.
- PR #167 System-1 / execution-substrate decision record — MERGED at `896e338e77c9ecf797a7f26f676cb10b18ae5c18`.
- Current slice reuses the existing global Celery worker timeout envelope (`task_soft_time_limit=240`, `task_time_limit=300`) rather than creating a duplicate timeout configuration. It adds AgentRun semantic classification for cooperative soft timeout as `runtime_timeout`, fail-closed and non-retryable by default.

## Runtime reliability boundary

The existing concepts remain separate:

- `CONTROLLED_AGENT_REGISTRY` = static implementation-definition truth.
- `AgentRun` = execution-history truth.
- `OrganizationAgent` = durable lifecycle/identity truth.
- Celery worker configuration = existing runtime timeout enforcement boundary.
- Phase 16 failure classification = evidence about why a run failed and whether automatic retry is permitted.

A timeout does not prove that no work occurred before interruption. Therefore timeout is not automatically retryable. The hard Celery limit remains a worker safety backstop; durable reconciliation after a hard process kill is a separate future concern and must not be falsely claimed by this slice.

No runtime reliability slice grants authority, permissions, credentials, autonomy, budget, tool access, work assignment or external execution rights.

## System-1 / execution candidates

PR #167 records the current architecture:

- Jev — HOLD; benchmark candidate for bounded System-1 decisions.
- Laya — HOLD; preferred self-hosted System-1 benchmark candidate.
- Google AX — DEFER until AIOS runtime contracts are mature.
- deterministic AIOS policy and canonical state remain authoritative.

Do not install or promote Jev, Laya or AX merely because they are documented candidates.

## Canonical read order

1. `agents/PROJECT_STATE.md` — current recovery dashboard.
2. `agents/SESSION_HANDOFF.md` — minimal fresh-session coordinates.
3. `docs/ROADMAP.md` — product/programme scheduler and architectural law; dated status lines may lag this dashboard until closure reconciliation.
4. `docs/PHASE_16_SYSTEM1_ORCHESTRATION_DECISIONS_2026-09-23.md` — Jev/Laya/AX decision record.
5. `docs/aios-v2/README.md` and companion architecture specifications.
6. `AGENTS.md` and `agents/AIOS_AGENT_EXECUTION_PLAYBOOK.md` — engineering/proof discipline.
7. Actual GitHub PR, commit and workflow state — authoritative for implementation status.

## Permanent project laws

- Canonical truth changes require evidence stronger than the proposing AI.
- Memory is not truth; conversation is not authority; telemetry is not canonical organization state.
- Capability != authority; authority != autonomy; autonomy != risk.
- Living HQ is a projection of canonical state, never a second operational truth.
- Prefer deterministic logic around model reasoning.
- External side effects require explicit authority, idempotency and reconciliation.
- Every new abstraction must remove more complexity from the user's life than it adds to AIOS.
- Finish existing capability chains before inventing new ones.
- Reuse existing canonical controls before creating another store, configuration or abstraction.
- Failure classification happens before retry; Unknown fails closed.

## Exact-head acceptance

For every slice:

`verified sealed base -> duplicate/reuse audit -> bounded feature branch -> focused tests -> Draft PR -> exact-head CI -> independent patch/scope audit -> Ready -> merge with expected head SHA -> verify actual merge SHA -> reconcile living docs -> seal`

A historical green run never proves a newer head.

## Repository hygiene

Before closure, inspect for stale current-state claims and duplicate abstractions. Historical phase records remain for traceability, but only designated living entry points should describe current state. Update this dashboard and `SESSION_HANDOFF.md`; reconcile the roadmap when a programme checkpoint changes instead of creating another status document.

Old feature/reconstruction branches are historical refs, not current work. New programme work starts only from the latest verified integration merge.
