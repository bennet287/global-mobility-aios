# Global Mobility AIOS — Session Handoff

**Purpose:** minimal cold-start recovery pointer. This file must not duplicate project history, architecture, roadmap sequencing, or CI ledgers.

**Last reconciled:** 2026-10-04

## Resume coordinates

Canonical integration branch:

`design/aios-v2-complete-redesign`

Resolve the live branch SHA directly from GitHub before branching, reviewing, or merging. The latest reconciled implementation checkpoint is PR #291 merge `829de64b57ed4ae1a30e0f6fae0a8903f34ba0a8`; do not treat that copied SHA as self-updating truth.

Current programme:

`Governed Recursive Self-Improvement (GRSI)`

Next bounded slice:

`Phase 22 satisfied-capable release_networking target-host gate executor for GRSI.E canary.`

GRSI.A–GRSI.D are sealed. GRSI.E code-shadow qualification, code-canary evidence binding, shadow/canary dependency policy, Phase 22 release identity and the bounded target-host foundation receipt writer are implemented. GRSI.E is not sealed because foundation v1 intentionally records only `blocked`, `failed` or `unknown`; no target-host gate can yet become `satisfied`. Migration head remains `0099_grsi_canary_dependency_policy`.

The candidate/evaluation/review/shadow/canary path remains authority-neutral. A code canary may become qualified only after qualified shadow evidence, a current exact canary Decision, a satisfied canary-scoped Board dependency policy, and six satisfied Phase 22 target-host receipts whose observed environment/release identities match the prepared run. Phase 22 owns deployment/acceptance truth; GRSI only binds that evidence. PR #291 establishes real fail-closed target-host receipt provenance, not a live canary or production-ready claim.

## Fresh-session procedure

1. Start at `AGENTS.md` and follow its canonical read chain.
2. Read `agents/PROJECT_STATE.md` for current programme truth and unresolved cross-cutting prerequisites.
3. Read the GRSI section of `docs/ROADMAP.md`; keep its A–H ordering and invariants authoritative.
4. Resolve the live integration head and active PRs from GitHub before changing code.
5. For the next Phase 22 slice, extend only the existing `release_networking` gate with satisfied-capable real-host probes. Reuse the deployment run/receipt owner and the PR #291 bounded executor pattern; do not create a second deployment/canary evidence owner.
6. A satisfied `release_networking` receipt must be derived from independently observed target-host evidence for the exact prepared environment/release plus intended HTTPS/network exposure and restart/rollback behavior. Caller-supplied success booleans, placeholder release IDs or CI status are not target-host acceptance evidence.
7. Keep the canary synthetic-data-only and inside existing authority/resource ceilings. Foundation blocked receipts remain immutable; use a fresh prepared run for satisfied-capable evidence. Do not start GRSI.F until all six Phase 22 gates can be satisfied from real canonical receipts and GRSI.E canary qualification is proven.

## Handoff discipline

If a fresh session needs more detail, follow `AGENTS.md` to the owning source. Do not expand this file into another `PROJECT_STATE`, roadmap, architecture document, acceptance history or CI ledger.
