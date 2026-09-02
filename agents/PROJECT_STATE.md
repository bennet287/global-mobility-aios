# Global Mobility AIOS — Project State Dashboard

**Purpose:** One-page navigation/state summary of the entire project. Read this first, then `agents/SESSION_HANDOFF.md` for recovery commands and branch details. This dashboard summarizes canonical sources; it does not replace ROADMAP, accepted proof records, the Radar/ledger, or actual git remotes.

**Last updated:** 2026-09-02
**Main branch:** `roadmap/global-mobility-aios-v12`
**Current V12 generation:** V12.71 — M.4.0 renderer bootstrap COMPLETE / PASS; M.4.1 Animated Employees V1 next
**Current HEAD:** verify with `git rev-parse origin/roadmap/global-mobility-aios-v12`

---

## 1. Executive snapshot

```text
Milestone L — Live Organization is COMPLETE / PASS / SEALED on accepted evidence head `a95f3f5...`.
The genuine independent Austria professional-review gate promoted all three current cases, and Repository Policy plus both push/PR V12 Production Proof runs are green for that exact evidence head.
M — Board Transparency Experience is IN PROGRESS; M.1–M.3 and M.4.0 are COMPLETE / PASS. M.4.0 is accepted at exact head `e6640755...` with five-job Production Proof and seven-test Chromium renderer proof; M.4.1 Animated Employees V1 is next.
All evaluation hardening (E2/E3/E4), Track B refinements, and R3 research are supporting work.
N remains blocked behind M.
No Radar candidate has caused runtime adoption.
```

---

## 2. Milestone board

| Milestone | Status | Blocker / next action |
|-----------|--------|------------------------|
| K.1 Bounded Specialist Execution | **SEALED** | None. Canonical proof recorded. |
| L Live Organization | **COMPLETE / PASS / SEALED** | Accepted evidence head `a95f3f5...`; no open gate. |
| M Board Transparency Experience | **IN PROGRESS — M.1–M.3 + M.4.0 COMPLETE / PASS; M.4.1 NEXT** | M.4.0 exact-head Production Proof #1085 PASS 5/5; browser suite PASS 7/7. |
| N Learning & Optimization | **NOT STARTED** | Wait for M. |

---

## 3. Active workstreams

| Workstream | Branch / location | Status | Do not... |
|------------|-------------------|--------|-----------|
| **V12 main** | `roadmap/global-mobility-aios-v12` | Active; L sealed; M.1–M.3 + M.4.0 COMPLETE / PASS; M.4.1 next | Preserve renderer non-authority and Structured fallback while adding animation. |
| **Track B Product Experience** | `roadmap/...v12` (`apps/web/`) | Anti-duplication complete; runtime economics + durable activity lineage implemented | Do not add Munder collaboration/presence/event state. |
| **Wave E1 Secrets** | `roadmap/...v12` (`docs/...WAVE_E1...`) | Pilot complete / trial-eligible | Do not claim production OpenBao adoption. |
| **Wave E2 Adversarial** | `roadmap/...v12` (`scripts/check_ai_domain_*.py`) | Implemented; historical exact-head proof observed | Do not treat as professional review. |
| **Wave E3 Properties** | `roadmap/...v12` (`scripts/check_*_properties.py`) | Implemented; Hypothesis test-only | Do not promote Hypothesis to runtime. |
| **Wave E4 Mutation** | `roadmap/...v12` (`scripts/check_ai_domain_mutation_strength.py`) | Implemented; first-party bounded gate; mutmut deferred | Do not claim full mutation coverage. |
| **Blind professional review** | `roadmap/...v12` (`scripts/prepare_austria_professional_review.py`) | **COMPLETE for sealed L** — current-v3 return compiled; 3/3 professionally reviewed promotions; privacy-safe aliases committed; final exact-evidence-head proof accepted | Do not expose reviewer identity, registration data, contact data, firm identity, or public-profile links in Git. |
| **M.1 Decision Explorer** | `roadmap/...v12` (`apps/web/app/cockpit/decisions/page.tsx`, `apps/api/app/routers/organization_records.py`) | **COMPLETE / PASS** at `9f00124c...`; Policy #517 PASS; Production Proof #1054 4/4 PASS | Do not reopen without regression; no command-surface or decision-domain unification. |
| **M.2 Decision reconstruction** | `roadmap/...v12` | **COMPLETE / PASS** at `d9294b2...`; Policy #521 PASS; Production Proof #1062 4/4 PASS; backend 1340/22, PostgreSQL 105, frontend 42/42 | Do not reopen without regression; reconstruction remains read-only. |
| **M.3 Scene Foundation** | `roadmap/...v12` (`apps/web/app/cockpit/live-organization/`) | **COMPLETE / PASS** at `d72ba0b6...`; Policy #527 PASS; Production Proof #1074 4/4 PASS | Do not reopen without regression; scene remains projection-only. |
| **M.4–M.10 Living Organization V2** | `roadmap/...v12` | **M.4.0 COMPLETE / PASS; M.4.1 NEXT**; WebGPU/Three.js = ADOPT; fluid FLOW = TRIAL; reaction-diffusion = EXPERIMENT; M.10 = cross-view closure | Structured surface remains permanent; animation must consume explicit presentation state only. |
| **Post-M Cognitive Ecology / Organica** | unscheduled research | **OPTIONAL / NOT AN M DELIVERABLE** | May return only for a proven unmet task; does not block N. |
| **R3 Authority** | `radar/r3-authority` | Deep validation implemented; execution pending | Do not expand beyond closure runbook. |
| **R3 Security** | `radar/r3-security` | Deep state-diff corpus + external-tool shootout defined; execution pending | Do not add more scanners. |
| **R3 Interoperability** | `radar/r3-interop` | Checkpointed at `aad377e`; pushed to origin | Do not merge to V12 until scheduled. |

---

## 3.1 Frozen product direction — Living Organization V2

Default experience: a recognizable animated digital organization, not an abstract ecosystem.

~~~text
canonical AIOS
    ↓
Live Organization projection
    ↓
scene state
    ↓
animated office / mission-control world
~~~

Permanent rule:

> **The organization causes the animation. The animation never silently causes the organization.**

M.4–M.9 add truthful movement, conversations, handoffs, Mission Rooms, blockers, Smart Objects, live Board Room, analytical lenses, Owner command mode, replay, Phantom Futures and environmental memory on top of the proven M.3 scene contract.

M.10 is now the cross-view product-value/closure gate for Organization, Analytical and Structured surfaces. Cognitive Ecology / Organica is Post-M optional research and does not block N.

N owns learned/adaptive behavior such as learned routing, predictive blocker models, adaptive Phantom Futures and bounded Dreamtime. N remains blocked behind M.

### Three-view product taxonomy

~~~text
ORGANIZATION
  operating interface
  recognizable employees / departments / Mission Rooms / Evidence Lab / Board Room

ANALYTICAL
  pattern/problem lenses
  FLOW / RISK / COST / EVIDENCE / BLOCKERS / bounded experiments

STRUCTURED
  named permanent Cockpit reference surface
  canonical records + core operations
  tables / lineage / dependency graph / timelines / matrices
  accessibility + low-power guarantee
~~~

All three views consume the same governed AIOS truth. No one surface is expected to perform every cognitive job.

### Advanced rendering adoption

**Architecture decision:** MIXED CLASSIFICATION.

~~~text
WebGPU                    ADOPT — renderer/compute substrate
Three.js WebGPU/compute   ADOPT — scene + interaction + compute layer
GPU flow/fluid fields     TRIAL — M.7 FLOW representation
reaction-diffusion fields EXPERIMENT — M.9 research bet
Cognitive Ecology         POST-M OPTIONAL RESEARCH
~~~

TRIAL = strong product hypothesis with a maintained structured analytical baseline and benchmark.
EXPERIMENT = semantically uncertain hypothesis that must graduate to TRIAL before product promotion.
Two failed targeted TRIAL iterations stop default-product development for that visualization. WebGPU/Three.js remain adopted because they serve multiple product surfaces.

Canonical contract: docs/LIVING_ORGANIZATION_ADVANCED_RENDERING_ADOPTION_V1.md.

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
1. L seal transition
   → V12.47 administration/recovery proof passed at exact head `80deef2...`.
   → V12.48 acceptance at `b079428...` failed the clean-worktree gate because additional untracked `.local/` content was exposed after local exclude cleanup.
   → Full inventory classified eight local buckets.
   → `gmai-dev-cache/` + `gmai-dev-temp/` are reproducible scratch and now have narrow repository ignore rules.
   → `professional-review/` remains narrowly ignored.
   → legacy wrapper artifacts, old patches, historical runtime files, SQLite backups and the old Radar apply script were moved to the dated external archive.
   → the next run exposed `.local/archives/`, `.local/discovery/`, and `.local/13.16.6-owner-inbox-discovery.txt`; repository search found no canonical V12 references, and all three were moved to the same external archive.
   → V12.52 remains FAILED for clean-worktree proof; later interactive PASS prints after the thrown gate are invalid.
   → V12.53 fail-fast local acceptance PASSED at exact head `b2cc754...`: archive preservation, narrow ignore ownership, zero visible untracked `.local/` state, repository gates, clean worktree and stable start/end/origin SHA all passed.
   → canonical PowerShell acceptance now uses one fail-fast block with final PASS only after every gate succeeds.
   → GitHub policy shallow-history defect is repaired; full-history CI then exposed 22 post-baseline trailing-space violations, and those exact files are cleaned.
   → A legal-quality assessment agreed with all three route directions but explicitly saw an obsolete answer-revealing v1 packet, so it is useful feedback only and NOT blind professional-review evidence.
   → V12.55 adds direct RIS authorities and explicit asserted-fact/document-verification semantics without reversing the three benchmark outcomes.
   → Source fingerprints changed; previously generated reviewer packet/template artifacts became stale.
   → V12.55 fail-fast local proof PASSED at exact head `e2e27ba...`: 21 focused tests, repository gates, clean worktree, stable start/end/origin SHA, and fresh blind v2 packet/template generation all passed.
   → A genuine independent professional return matched the fresh V12.55 fingerprints. The earlier `independent_review=false` values for Cases 1/3 were operator transcription mistakes and are superseded by V12.58.
   → It exposed a v2 label-contract ambiguity: canonical pathway/evidence/source vocabularies and ELIGIBLE vs REVIEW_REQUIRED/escalation semantics were not defined for the reviewer.
   → V12.57 corrects the strong case to route-level `ELIGIBLE` / `escalation_required=false`, versions the handoff to v3, requires complete ASSESSED labels, and defines canonical reviewer vocabulary.
   → All v2 reviewer artifacts/returns are historical for acceptance because V12.57 changed fingerprint-bound labels/rationale.
   → A supplied v3-style return correctly records `independent_review=true` and non-empty reference strings, but still carries the historical Case 2 fingerprint plus legacy/free-form pathway/evidence/source labels and null contradictions.
   → V12.59 aligns the reviewer return contract to `austria-professional-review-blind-return.v3` and fail-closes on noncanonical pathway/evidence/source vocabularies.
   → Canonical checkpoint `24a00c1...` completed Repository Policy plus V12 Production Proof 4/4; source-tree-equivalent local proof passed 28 focused tests and repository gates.
   → Fresh exact-current-source v3 packet/template generation completed with all three current fingerprints and no expected-label/rationale exposure.
   → Same-reviewer current-fingerprint reaffirmation received and compiled without label translation.
   → All three cases are promoted as CORRECTED; eligibility remains INELIGIBLE / ELIGIBLE / INELIGIBLE.
   → Exact evidence head `a95f3f5...` passed Repository Policy and both push/PR V12 Production Proof runs.
   → L is COMPLETE / PASS / SEALED.
   → Reviewer anonymity is mandatory in repository artifacts: use only non-identifying opaque reviewer/professional/credential aliases; keep the real identity-to-credential mapping and supporting evidence confidential outside Git.
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

1. **M.4.1 Animated Employees V1 — NEXT** — add bounded semantic animation on the accepted renderer; unknown/not-asserted states remain neutral and non-presence-implying.
2. **M.5–M.6** — conversations/handoffs/Mission Rooms, then blockers/Smart Objects/live Board Room.
3. **M.5–M.6** — conversations/handoffs/Mission Rooms, then blockers/Smart Objects/live Board Room.
4. **M.7** — maintain a structured FLOW baseline and run the GPU fluid FLOW TRIAL against it.
5. **M.8** — Replay / temporal organization as a core product surface and historical baseline.
6. **M.9** — environmental-memory TRIAL with structured baseline; reaction-diffusion EXPERIMENT; Phantom Futures bounded experiment.
7. **M.10** — cross-view product-value benchmark + M closure.
8. **Post-M** — Cognitive Ecology / Organica only if a proven unmet task justifies new research.
9. **Close R3 authority / security** as bounded supporting work when it does not displace M.

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
| `docs/V12_51_POST_BASELINE_DIFF_HYGIENE_CLEANUP_2026-09-01.md` | Exact 22-line post-baseline whitespace cleanup and remaining acceptance boundary. |
| `docs/V12_52_LOCAL_ARTIFACT_CLASSIFICATION_2026-09-01.md` | Eight-bucket `.local/` classification, narrow ignore policy, and external archive rule. |
| `docs/V12_53_SECONDARY_LOCAL_ARTIFACT_ARCHIVE_2026-09-01.md` | Secondary archives/discovery classification and fail-fast PowerShell acceptance correction. |
| `docs/V12_53_LOCAL_ACCEPTANCE_PROOF_2026-09-01.md` | Exact-head fail-fast local acceptance proof at `b2cc754...`. |
| `docs/L_AUSTRIA_NON_BLIND_LEGAL_QUALITY_FEEDBACK_2026-09-01.md` | Non-blind legal feedback, source verification, benchmark hardening and stale-packet boundary. |
| `docs/L_V12_55_PROFESSIONAL_REVIEW_HANDOFF_LOCAL_PROOF_2026-09-01.md` | Historical exact-head V12.55 v2 handoff proof. |
| `docs/L_AUSTRIA_PRELIMINARY_BLIND_RETURN_RECONCILIATION_2026-09-01.md` | Historical v2 return/contract analysis; independence rejection superseded by V12.58. |
| `docs/L_AUSTRIA_GENUINE_BLIND_REVIEW_OPERATOR_CORRECTION_2026-09-01.md` | Corrects review independence classification and defines v3 reaffirmation/provenance requirements. |
| `docs/L_AUSTRIA_V3_RETURN_VALIDATION_ATTEMPT_2026-09-01.md` | Genuine review preserved; supplied v3-style return rejected for stale fingerprint / legacy vocab / incomplete ASSESSED labels. |
| `docs/L_AUSTRIA_ANONYMOUS_REVIEWER_PRIVACY_BOUNDARY_2026-09-01.md` | Binding anonymous-reviewer rule: no identifying reviewer data in Git; opaque aliases only. |
| `docs/L_V12_61_CURRENT_V3_HANDOFF_PROOF_2026-09-01.md` | Canonical CI + source-tree-equivalent local proof and fresh anonymous current-v3 handoff generation. |
| `docs/L_V12_62_ANONYMOUS_PROFESSIONAL_REVIEW_RECONCILIATION_2026-09-02.md` | Current-fingerprint anonymous review compilation, professional corrections and final-proof boundary. |
| `docs/V1_3_L_LIVE_ORGANIZATION_SEAL_2026-09-02.md` | Final L seal decision and exact evidence-head proof. |
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
