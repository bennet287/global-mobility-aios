# Global Mobility AIOS — Project State

**Purpose:** concise recovery dashboard. This is a living pointer, not an acceptance ledger. Historical proof remains in Git history and phase-specific records.

**Last reconciled:** 2026-09-17
**Canonical integration branch:** `design/aios-v2-complete-redesign`
**Current sealed programme checkpoint:** `eee8ac5d24808b3880e50f51e1879c4ad623021c` (Phase 15.2 Roadmap reconciliation)
**Latest accepted implementation merge:** `30e6a9e691f4b82a326b2dc1cb267ef5bb938c35` (PR #158)
**Current programme:** Phase 15 — Agent Lifecycle Governance Hooks
**Active implementation:** none; Phase 15.2 is sealed
**Next scheduled slice:** governed pre/post tool-use, tool-failure and permission-request/denial signals through existing AIOS boundaries

## Current programme state

- Phase 13G Living HQ flagship convergence — SEALED.
- Autonomous Regulatory Intelligence RI.A1–RI.A8 — SEALED. Production machine publication and machine recovery remain OFF unless separately authorized.
- Phase 14 Native Skills Registry — SEALED through governed skill-informed work assignment.
- Phase 15.1 Governed Agent Lifecycle Foundation — SEALED by PR #156.
- Phase 15.2 Governed Lifecycle Transition Services — SEALED by PR #158.
- Phase 15 Agent Lifecycle Governance — ACTIVE; the next signal slice has not yet opened a branch or PR.

## Phase 14 sealed chain

`skill registry -> position binding -> applicability -> validation -> lifecycle -> mutation audit -> diagnostic work matching -> human-governed assignment`

Final Phase 14 merge: `98229c2024b44d6b65a6af7829d61209c142e7bc`.

Permanent boundary: `CAN DO != MAY DO`. Skills, validation, matching and assignment do not grant authority, permissions, credentials, autonomy or execution rights.

## Phase 15 current boundary

Phase 15 owns durable governed AI-employee lifecycle state and its explicit transition boundary:

`created -> onboarding -> inactive -> active -> restricted/suspended -> retired`

The existing concepts remain separate:

- `CONTROLLED_AGENT_REGISTRY` = static implementation-definition truth.
- `AgentRun` = execution-history truth.
- `OrganizationAgent` = durable lifecycle/identity truth introduced by sealed Phase 15.1.
- the Phase 15.2 transition service = explicit fail-closed lifecycle mutation plus bounded `AuditLog` lineage.

Phase 15.1/15.2 do not wire execution, grant autonomy, create credential truth, assign work, route work or automatically activate agents. Phase 15.2 added no migration or second lifecycle store. Migration head remains `0084_organization_agent_lifecycle`.

Phase 15.2 accepted exact-head evidence:

- candidate `6dcd1744a3c56bdab231f62bcfa76caf01df866d`;
- Repository Policy Check #1393 — PASS;
- V12 Production Proof #2023 — PASS;
- actual merge `30e6a9e691f4b82a326b2dc1cb267ef5bb938c35`;
- Roadmap reconciliation `eee8ac5d24808b3880e50f51e1879c4ad623021c`.

## Canonical read order

1. `docs/ROADMAP.md` — product/programme scheduler and architectural law. Treat dated status lines as historical when contradicted by a newer accepted exact-head merge.
2. `docs/aios-v2/README.md` — V2 companion entry point.
3. `docs/aios-v2/AIOS_V2_COMPLETE_REDESIGN_MASTER_PLAN.md` — destination and acceptance model.
4. `docs/aios-v2/AIOS_V2_EMPLOYEE_CAPABILITY_AND_SKILLS_ARCHITECTURE.md` — employee/capability architecture.
5. `AGENTS.md` and `agents/AIOS_AGENT_EXECUTION_PLAYBOOK.md` — engineering/proof discipline.
6. Actual GitHub PR, commit and workflow state — authoritative for current implementation status.

Do not use old V12 branch/worktree instructions in historical documents as current branch authority.

## Permanent project laws

- Canonical truth changes require evidence stronger than the proposing AI.
- Memory is not truth; conversation is not authority; telemetry is not canonical organization state.
- Capability != authority; authority != autonomy; autonomy != risk.
- Living HQ is a projection of canonical state, never a second operational truth.
- The organization causes the animation; animation never silently causes the organization.
- Prefer deterministic logic around model reasoning.
- External side effects require explicit authority, idempotency and reconciliation.
- Every new abstraction must remove more complexity from the user's life than it adds to AIOS.
- Finish existing capability chains before inventing new ones.

## Exact-head acceptance

For every slice:

`verified sealed base -> bounded feature branch -> focused tests -> Draft PR -> exact-head CI -> independent patch/scope audit -> Ready -> merge with expected head SHA -> verify actual merge SHA -> seal`

A historical green run never proves a newer head.

## Repository hygiene

Historical phase records may remain for traceability, but only designated living entry points should describe current state. Do not duplicate current programme status across new handoff files. Prefer updating this dashboard and the roadmap rather than adding another status document.

Old feature/reconstruction branches are historical refs, not current work. Do not branch from them. New programme work starts only from the latest verified merge on `design/aios-v2-complete-redesign`.
