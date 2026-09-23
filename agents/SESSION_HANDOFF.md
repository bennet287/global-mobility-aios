# Global Mobility AIOS — Session Handoff

**Purpose:** minimal recovery instructions for a fresh engineering session. Do not copy historical programme narratives into this file.

**Last reconciled:** 2026-09-23

## Start here

1. Read `agents/PROJECT_STATE.md`.
2. Fetch `design/aios-v2-complete-redesign` and verify its actual SHA.
3. Inspect the active Phase 16 PR/branch and its exact head before changing code.
4. Read the current scheduling section of `docs/ROADMAP.md` plus `docs/PHASE_16_SYSTEM1_ORCHESTRATION_DECISIONS_2026-09-23.md`.
5. If the active branch is stale against a newer integration merge, reconstruct it before proof rather than accepting stale CI.

## Current recovery coordinates

Canonical integration branch:

`design/aios-v2-complete-redesign`

Verified base for the current slice:

`896e338e77c9ecf797a7f26f676cb10b18ae5c18` — PR #167 merge

Active programme:

`Phase 16 — Runtime Reliability & Economic Metering`

Sealed Phase 16 foundations:

- Phase 16.1 provider usage observation — merge `8b13f8b8fc3a4bf922a873fe35ab7490307132b0`.
- Phase 16.2 deterministic failure classification/retry policy — merge `9ca583cb3a38c2cee33d2558ada9995106758cd9`.
- PR #167 Jev/Laya/AX architectural decision record — merge `896e338e77c9ecf797a7f26f676cb10b18ae5c18`.

Active branch:

`phase-16-runtime-timeout-reconciliation`

Current slice:

Reuse the existing Celery timeout envelope (`task_soft_time_limit=240`, `task_time_limit=300`) and make a cooperative soft timeout explicit AgentRun failure evidence: `runtime_timeout`, non-retryable by default. Do not create a second timeout configuration or imply that hard-kill reconciliation/cancellation is solved.

## Exact-head rule

Acceptance requires one immutable implementation head:

`capture exact head -> run required proof -> verify exact same head -> inspect patch/scope -> merge with expected head -> fetch actual merge SHA -> reconcile living docs`

Never use historical green CI to certify a changed head.

## Active architectural boundary

- Celery configuration owns the existing worker timeout envelope.
- AgentRun owns execution-history truth.
- Phase 16 classification records why execution failed and whether automatic retry is allowed.
- Timeout does not prove zero prior side effects or progress; automatic retry therefore remains fail-closed.
- Hard process-kill reconciliation and explicit cancellation are not claimed by the current slice.
- Jev/Laya remain benchmark candidates; AX remains deferred.
- No runtime reliability mechanism grants authority, permissions, credentials, autonomy, budget, work assignment or external execution rights.

## Closure hygiene

Before calling the slice sealed:

- verify exact-head CI;
- inspect the complete patch and changed-file list;
- verify no duplicate timeout/cancellation/budget/runtime truth was introduced;
- reconcile stale current-state claims in `PROJECT_STATE.md`, `SESSION_HANDOFF.md`, and the roadmap where appropriate;
- record actual merge SHA;
- ensure the next session can identify sealed state, deliberate deferrals and the next slice without reconstructing old PR history.

Do not create another handoff/status document. Git history remains the archive.

## CI / proof expectation

Backend/governance changes require Repository Policy and V12 Production Proof on the exact candidate head, including the backend regression lanes represented by that workflow. Frontend/browser proof is required only when affected. Inspect actual jobs rather than inferring coverage from a workflow title.
