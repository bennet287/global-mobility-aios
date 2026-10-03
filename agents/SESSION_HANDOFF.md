# Global Mobility AIOS — Session Handoff

**Purpose:** minimal cold-start recovery pointer. This file must not duplicate project history, architecture, roadmap sequencing, or CI ledgers.

**Last reconciled:** 2026-10-03

## Resume coordinates

Canonical integration branch:

`design/aios-v2-complete-redesign`

Resolve the live branch SHA directly from GitHub before branching, reviewing, or merging. The latest reconciled implementation checkpoint is PR #287 merge `4c5ab9787500d1de56bf3f9a346e0e0622e4cd21`; do not treat that copied SHA as self-updating truth.

Current programme:

`Governed Recursive Self-Improvement (GRSI)`

Next bounded slice:

`Phase 22 target-host acceptance executor / receipt writer for GRSI.E canary.`

GRSI.A–GRSI.D are sealed. GRSI.E code-shadow qualification, code-canary evidence binding, shadow/canary dependency policy and Phase 22 release identity are implemented, but GRSI.E is not sealed because no canonical service currently writes the six target-host `ProductionDeploymentAcceptanceCheckReceipt` records. Migration head is `0099_grsi_canary_dependency_policy` at this checkpoint.

The candidate/evaluation/review/shadow/canary path remains authority-neutral. A code canary may become qualified only after qualified shadow evidence, a current exact canary Decision, a satisfied canary-scoped Board dependency policy, and six satisfied Phase 22 target-host receipts whose observed environment/release identities match the prepared run. Phase 22 owns deployment/acceptance truth; GRSI only binds that evidence. No live canary or production readiness is currently proven.

## Fresh-session procedure

1. Start at `AGENTS.md` and follow its canonical read chain.
2. Read `agents/PROJECT_STATE.md` for current programme truth and unresolved cross-cutting prerequisites.
3. Read the GRSI section of `docs/ROADMAP.md`; keep its A–H ordering and invariants authoritative.
4. Resolve the live integration head and active PRs from GitHub before changing code.
5. For the next Phase 22 slice, reuse the existing deployment-acceptance run/receipt models and six gate keys. Do not create a second deployment/canary evidence owner.
6. The executor must independently observe the target environment and running release identity; caller-supplied success booleans, placeholder release IDs or CI status are not target-host acceptance evidence.
7. Keep the canary synthetic-data-only and inside existing authority/resource ceilings. Do not start GRSI.F until the Phase 22 receipt writer is proven and GRSI.E canary qualification can be satisfied from real canonical receipts.

## Handoff discipline

If a fresh session needs more detail, follow `AGENTS.md` to the owning source. Do not expand this file into another `PROJECT_STATE`, roadmap, architecture document, acceptance history or CI ledger.
