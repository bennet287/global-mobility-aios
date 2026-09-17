# Global Mobility AIOS — Session Handoff

**Purpose:** minimal recovery instructions for a fresh engineering session. Do not copy historical programme narratives into this file.

**Last reconciled:** 2026-09-17

## Start here

1. Read `agents/PROJECT_STATE.md`.
2. Read the current scheduling sections of `docs/ROADMAP.md` and the companion spec for the active slice.
3. Fetch `design/aios-v2-complete-redesign` from GitHub and verify its actual SHA.
4. If an active PR exists, inspect its exact head and workflow runs before changing code; otherwise branch from the verified integration head.
5. If a future PR is stale against a newly sealed base, reconstruct/rebase it before proof rather than accepting stale CI.

## Current recovery coordinates

Canonical integration branch:

`design/aios-v2-complete-redesign`

Current sealed programme checkpoint:

`eee8ac5d24808b3880e50f51e1879c4ad623021c`

Latest accepted implementation merge:

`30e6a9e691f4b82a326b2dc1cb267ef5bb938c35` — PR #158

Active programme:

`Phase 15 — Agent Lifecycle Governance Hooks`

Sealed slices at this handoff:

`Phase 15.1 — Governed Agent Lifecycle Foundation`

`Phase 15.2 — Governed Lifecycle Transition Services`

Next scheduled slice:

`governed pre/post tool-use, tool-failure and permission-request/denial signals`

There is no active implementation branch or PR recorded by this handoff. The integration branch may contain later documentation-only reconciliation commits; create the next bounded branch only from its freshly verified actual head.

Always verify these coordinates against GitHub; this file is a recovery pointer, not self-updating repository truth.

## Exact-head rule

Acceptance requires one immutable implementation head:

`capture exact head -> run required proof -> verify exact same head -> inspect patch/scope -> merge with expected head -> fetch actual merge SHA`

Never use a historical green workflow to certify a changed head. Never merge because a builder merely reports that tests passed.

## Active architectural boundary

Phase 15 must not collapse these concepts:

- controlled-agent registry: implementation definition;
- organization agent: durable lifecycle identity;
- position: organizational role/authority contract;
- skill: capability eligibility;
- tool/permission configuration: future canonical prerequisite truth;
- credential: connector/runtime secret boundary;
- AgentRun: execution history;
- autonomy profile: separately earned execution latitude.

Lifecycle state and lifecycle transitions grant none of authority, permissions, credentials, autonomy, tool access, work assignment, routing or execution. Phase 15.2 reuses `AuditLog`; it does not create another lifecycle truth store.

## Do not do

- Do not branch from old V12, Radar, reconstruction, prep, `-next`, `-work`, or historical feature branches.
- Do not create another current-state/handoff document; update `PROJECT_STATE.md` or the roadmap instead.
- Do not add a new table when an existing canonical model owns the durable business truth.
- Do not turn diagnostic skill matching into authorization.
- Do not use corporate-account connector credentials as per-position entitlement truth.
- Do not enable regulatory machine publication or machine recovery without a separate accepted authorization slice.
- Do not reopen sealed Living HQ visual work without a concrete regression or new scheduled product requirement.
- Do not treat memory, model confidence, telemetry, UI state or animation as canonical truth.

## CI / proof expectation

For backend/governance slices, the expected broad seal includes Repository Policy, V12 Production Proof, SQLite regression and PostgreSQL governance. Frontend/browser proof is required when the slice affects those surfaces. Inspect the actual workflow jobs rather than inferring coverage from a workflow title.

## Historical material

Old V12 project-state narratives, professional-review proof records, phase-specific acceptance docs and Radar research remain historical evidence. They may explain why a rule exists, but they are not current branch/status authority. Git history is the archive; living handoff files should stay short.
