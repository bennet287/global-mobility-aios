# Global Mobility AIOS — Session Handoff

**Purpose:** minimal recovery instructions for a fresh engineering session. Do not copy historical programme narratives into this file.

**Last reconciled:** 2026-09-23

## Start here

1. Read `agents/PROJECT_STATE.md`.
2. Read the current Phase 16 scheduling sections of `docs/ROADMAP.md`.
3. Read `docs/PHASE_16_SYSTEM1_ORCHESTRATION_DECISIONS_2026-09-23.md`.
4. Fetch `design/aios-v2-complete-redesign` and verify its actual SHA.
5. If an active PR exists, inspect its exact head, changed files and workflow runs before changing code; otherwise branch only from the verified integration head.
6. Search for existing models/services/contracts before adding state or abstractions.

## Current recovery coordinates

Canonical integration branch:

`design/aios-v2-complete-redesign`

Verified integration head at this reconciliation:

`c4ff75f24801eb52a82da2ac09cc724ffe872534` — PR #173 merge

Active programme:

`Phase 16 — Runtime Reliability, Metering and Orchestration Foundations`

Sealed/runtime decisions:

- Phase 16.1 — runtime provider-usage metering, PR #165, merge `8b13f8b8fc3a4bf922a873fe35ab7490307132b0`.
- Phase 16.2 — deterministic failure classification/retry policy, PR #166, merge `9ca583cb3a38c2cee33d2558ada9995106758cd9`.
- System-1 / AX evaluation record, PR #167, merge `896e338e77c9ecf797a7f26f676cb10b18ae5c18`.
- AgentRun cooperative soft-timeout semantics, PR #171, merge `14d7bfdd238ca93a10310541702c216fc9561f4b`.
- AgentRun stale-running reconciliation, PR #173, accepted head `d1b4156e85d5b23dfa1c9ee245a32a6009acb4a1`, merge `c4ff75f24801eb52a82da2ac09cc724ffe872534`; Repository Policy #1415 and V12 Production Proof #2045 passed on the exact accepted head.

PR #171 reuses the existing Celery `task_soft_time_limit=240` and `task_time_limit=300`. A cooperative soft timeout records `agent_run_runtime_timeout`, terminates the existing AgentRun as `failed`, and is non-retryable.

PR #173 adds a periodic stale-running reconciler using the existing AgentRun and AuditLog boundaries. It waits until the 300-second hard limit plus a 60-second grace window, requires durable evidence that the latest recorded lifecycle state is still `running`, records `agent_run_stale_running_reconciled`, and fails closed. `cause_inferred=false` is permanent to this evidence: a stranded run does not prove the worker was definitely killed by the Celery hard limit.

Next scheduled slice:

`explicit AgentRun cancellation semantics through the existing AgentRun/Celery boundary`

No Jev, Laya or Google AX production dependency is approved. Jev/Laya are benchmark candidates; AX is deferred until canonical runtime controls exist.

Always verify these coordinates against GitHub; this file is a recovery pointer, not self-updating repository truth.

## Runtime architecture boundary

Do not collapse:

- controlled-agent registry = implementation definition;
- OrganizationAgent = durable lifecycle identity;
- AgentRun = execution history;
- position = organizational role/authority contract;
- skill = capability eligibility;
- connector credential = runtime secret boundary;
- autonomy profile = separately earned execution latitude;
- provider usage observation = diagnostic runtime evidence, not billing truth;
- Jev/Laya = possible future advisory System-1 decision primitives;
- AX = possible future replaceable execution substrate.

CAN DO != MAY DO != DID DO != CREATED VALUE.

Timeout/cancellation work must reuse the existing execution boundary and must not silently grant authority, permissions, credentials, autonomy, budget, assignment or external side effects. Cancellation does not imply rollback of an external side effect that already occurred.

For the next slice, inspect actual asynchronous enqueue/task identity paths before adding cancellation state. Existing `OrganizationalWorkItem.cancel_requested_at` belongs to WorkItem governance and is not AgentRun cancellation truth. Distinguish cancellation intent from a worker actually stopping; do not claim a Celery revoke proves rollback or absence of side effects.

## Closure rule

Every implementation slice must finish with:

`exact merged head -> duplicate/reuse audit -> stale-state/docs audit -> canonical living-doc reconciliation -> exact CI evidence -> actual merge SHA -> clear next slice`

Do not leave `PROJECT_STATE.md`, `SESSION_HANDOFF.md` or the roadmap materially pointing at an older active programme after a slice is sealed. Update existing living documents rather than creating duplicate handoff/status files.

## Do not do

- Do not branch from historical V12, reconstruction, prep, `-next`, `-work` or old feature branches.
- Do not create another current-state/handoff document.
- Do not add a new durable table when an existing canonical model owns the truth.
- Do not turn diagnostic confidence, System-1 output or skill matching into authorization.
- Do not treat corporate connector credentials as per-agent entitlement truth.
- Do not enable regulatory machine publication/recovery without a separate accepted authorization slice.
- Do not reopen sealed Living HQ visual work without a concrete regression or scheduled requirement.
- Do not treat memory, telemetry, UI state or animation as canonical truth.

## CI / proof expectation

For backend/governance slices, inspect the exact-head Repository Policy and V12 Production Proof jobs plus their SQLite/PostgreSQL coverage. Frontend/browser proof is required when affected. A historical green run never certifies a changed head.
