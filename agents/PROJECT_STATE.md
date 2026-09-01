# Global Mobility AIOS — Project State Dashboard

**Purpose:** One-page navigation/state summary of the entire project. Read this first, then `agents/SESSION_HANDOFF.md` for recovery commands and branch details. This dashboard summarizes canonical sources; it does not replace ROADMAP, accepted proof records, the Radar/ledger, or actual git remotes.

**Last updated:** 2026-08-31
**Main branch:** `roadmap/global-mobility-aios-v12`
**Current V12 generation:** V12.50 — CI diff-hygiene full-history repair + V12.48 local-state investigation pending
**Current HEAD:** verify with `git rev-parse origin/roadmap/global-mobility-aios-v12`

---

## 1. Executive snapshot

```text
Milestone L — Live Organization is IMPLEMENTED but NOT SEALED.
The only release-critical external gate is genuine independent Austria professional review.
Blind reviewer handoff is hardened and locally proven at d969c7d; real reviewer evidence still pending.
All evaluation hardening (E2/E3/E4), Track B refinements, and R3 research are supporting work.
No M or N work may start until L is sealed.
No Radar candidate has caused runtime adoption.
```

---

## 2. Milestone board

| Milestone | Status | Blocker / next action |
|-----------|--------|------------------------|
| K.1 Bounded Specialist Execution | **SEALED** | None. Canonical proof recorded. |
| L Live Organization | **IMPLEMENTED / ACCEPTANCE PENDING** | Genuine independent Austria professional review + final exact-current-head proof after review reconciliation. |
| M Board Transparency Experience | **NOT STARTED** | Wait for L seal. |
| N Learning & Optimization | **NOT STARTED** | Wait for M. |

---

## 3. Active workstreams

| Workstream | Branch / location | Status | Do not... |
|------------|-------------------|--------|-----------|
| **V12 main** | `roadmap/global-mobility-aios-v12` | Active; L acceptance in progress | Do not add M/N features. |
| **Track B Product Experience** | `roadmap/...v12` (`apps/web/`) | Anti-duplication complete; runtime economics + durable activity lineage implemented | Do not add Munder collaboration/presence/event state. |
| **Wave E1 Secrets** | `roadmap/...v12` (`docs/...WAVE_E1...`) | Pilot complete / trial-eligible | Do not claim production OpenBao adoption. |
| **Wave E2 Adversarial** | `roadmap/...v12` (`scripts/check_ai_domain_*.py`) | Implemented; historical exact-head proof observed | Do not treat as professional review. |
| **Wave E3 Properties** | `roadmap/...v12` (`scripts/check_*_properties.py`) | Implemented; Hypothesis test-only | Do not promote Hypothesis to runtime. |
| **Wave E4 Mutation** | `roadmap/...v12` (`scripts/check_ai_domain_mutation_strength.py`) | Implemented; first-party bounded gate; mutmut deferred | Do not claim full mutation coverage. |
| **Blind professional review** | `roadmap/...v12` (`scripts/prepare_austria_professional_review.py`) | Hardened; local exact-head proof observed at `d969c7d`; reviewer packet + blank return template successfully generated locally | Generated files are handoff artifacts only; do not fabricate reviewer evidence. |
| **R3 Authority** | `radar/r3-authority` | Deep validation implemented; execution pending | Do not expand beyond closure runbook. |
| **R3 Security** | `radar/r3-security` | Deep state-diff corpus + external-tool shootout defined; execution pending | Do not add more scanners. |
| **R3 Interoperability** | `radar/r3-interop` | Checkpointed at `aad377e`; pushed to origin | Do not merge to V12 until scheduled. |

---

## 4. Branch / worktree map

| Branch | Worktree | Purpose | Origin | Recovery |
|--------|----------|---------|--------|----------|
| `roadmap/global-mobility-aios-v12` | `D:/global-mobility-aios` | Canonical V12 product | Yes | `git fetch && git reset --hard origin/...` |
| `radar/r3-authority` | `D:/gmai-r3-authority` | Isolated R3 authorization research | Yes | `git pull --ff-only origin/radar/r3-authority` |
| `radar/r3-security` | `D:/gmai-r3-security` | Isolated R3 security research | Yes | `git pull --ff-only origin/radar/r3-security` |
| `radar/r3-interop` | `D:/gmai-r3-interop` | Isolated R3 interoperability research | Yes (pushed) | `git pull --ff-only origin/radar/r3-interop` |
| `roadmap/global-mobility-aios-v11` | n/a | Frozen V11 reference | Yes | Read-only; do not modify. |

---

## 5. Open decisions / blockers

```text
1. L professional review
   → Need a qualified independent Austria immigration/legal reviewer.
   → Blind packet + blank return template generation has been exercised successfully.
   → Generated local files are reproducible handoff artifacts, not professional evidence.
   → V12.47 administration/recovery proof passed at exact head `80deef2...`.
   → V12.48 acceptance at `b079428...` failed the clean-worktree gate because additional untracked `.local/` content was exposed after local exclude cleanup.
   → GitHub policy CI separately failed because shallow checkout depth 64 omitted diff-hygiene baseline `8624d7f...`; policy checkouts now use full history and CI rerun is pending.
   → No fabricated or AI-generated review allowed.

2. R3 authority closure
   → Run closure runbook on D:/gmai-r3-authority.
   → Capture real OpenFGA/OPA/Cedar/SpiceDB evidence.
   → Do not add new engine challengers.

3. R3 security execution
   → Run external tool shootout (Inspect/Promptfoo/garak) or record CLI blockers.
   → Do not add more scanners.

4. R3 interop next step
   → Decide whether to extend interop or move to integration stress.
```

---

## 6. Next 30-day priorities

In order:

1. **Obtain L professional review.** This is the only release-critical item.
2. **Run V12 exact-current-head acceptance** after review evidence is committed.
3. **Close R3 authority** evidence capture (bounded supporting work).
4. **Execute or explicitly defer** R3 security external-tool shootout.
5. **Seal L.** Only then consider M.

---

## 7. Frozen / archived streams

```text
V11                              frozen at ac130deaafa7aa44068e9459facbda2b4df327d6
Munder collaboration state       REJECT for V12
CopilotKit / AG-UI runtime       deferred to post-L M
presence / heartbeat             deferred — no canonical semantics
provider transcript truth        REJECTED as canonical
Kubernetes policy tooling        WATCH only
mutmut                           deferred to Linux/CI
LangGraph / Agno runtime         DONOR_ONLY
OpenViking                       DONOR_ONLY
```

---

## 8. Key document index

| Document | Why read it |
|----------|-------------|
| `agents/PROJECT_STATE.md` | This file — current map. |
| `agents/SESSION_HANDOFF.md` | Recovery commands and exact recent decisions. |
| `AGENTS.md` | Conventions, proof rules, boundaries. |
| `docs/ROADMAP.md` | Scheduling authority. |
| `docs/CHANGELOG.md` | Delivered change history. |
| `docs/TECHNOLOGY_RADAR_V1_3_8.md` | Consolidated technology decisions. |
| `docs/TECHNOLOGY_ADOPTION_LEDGER.md` | Implementation truth vs Radar presence. |
| `docs/L_AUSTRIA_BLIND_PROFESSIONAL_REVIEW_HANDOFF_2026-08-31.md` | L reviewer handoff spec. |
| `docs/L_BLIND_PROFESSIONAL_REVIEW_LOCAL_PROOF_2026-08-31.md` | L blind-review local exact-head proof record. |
| `docs/V12_47_PROJECT_STATE_ADMIN_LOCAL_PROOF_2026-08-31.md` | V12.47 administration/recovery exact-head proof and local `.git/info/exclude` note. |
| `docs/V12_48_ADMIN_ACCEPTANCE_FAILED_UNTRACKED_LOCAL_2026-09-01.md` | Failed V12.48 acceptance record and required `.local/` inspection procedure. |
| `docs/V12_50_CI_DIFF_HYGIENE_FULL_HISTORY_FIX_2026-09-01.md` | CI shallow-history root cause, repair, regression guard, and acceptance boundary. |
| `labs/r3/authority/README.md` | R3 authority closure runbook. |
| `labs/r3/security/README.md` | R3 security execution instructions. |
| `labs/r3/interoperability/README.md` | R3 interop checkpoint. |

---

## 9. Update rule

Update this file when any of the following change:

- Milestone status (K/L/M/N)
- Active workstream added, completed, or frozen
- Branch/worktree HEADs or origin presence
- Open blocker resolved or new blocker added
- Priority order changes
- Professional-review handoff / evidence state changes

Do not encode this file's own commit SHA as the "current HEAD". Always require verification against origin.
