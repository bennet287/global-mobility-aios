# Global Mobility AIOS — Project State Dashboard

**Purpose:** One-page navigation/state summary of the entire project. Read this first, then `agents/SESSION_HANDOFF.md` for recovery commands and branch details. This dashboard summarizes canonical sources; it does not replace ROADMAP, accepted proof records, the Radar/ledger, or actual git remotes.

**Last updated:** 2026-08-31
**Main branch:** `roadmap/global-mobility-aios-v12`
**Current V12 generation:** V12.60 — anonymous reviewer privacy boundary enforced
**Current HEAD:** verify with `git rev-parse origin/roadmap/global-mobility-aios-v12`

---

## 1. Executive snapshot

```text
Milestone L — Live Organization is IMPLEMENTED but NOT SEALED.
The only release-critical external gate is genuine independent Austria professional review.
A genuine independent Austria professional review was completed against the V12.55/v2 fingerprints; earlier `independent_review=false` values were operator transcription mistakes. V12.57 incorporated the review's semantic corrections and superseded v2 with reviewer contract v3; current v3 reaffirmation + privacy-safe reviewer/credential aliases remain pending; real identity/credential verification stays confidential outside Git.
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
| **Blind professional review** | `roadmap/...v12` (`scripts/prepare_austria_professional_review.py`) | Genuine independent review preserved; v3 compiler + anonymous reviewer privacy contract enforced; current-fingerprint reaffirmation pending | Do not expose reviewer identity, registration data, contact data, firm identity, or public-profile links in Git. |
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
   → Regenerate the exact current v3 packet/template and obtain same-reviewer reaffirmation using those enforced fields.
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

1. **Complete anonymous current-v3 professional-review reaffirmation.** This is the only release-critical item.
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
| `docs/V12_51_POST_BASELINE_DIFF_HYGIENE_CLEANUP_2026-09-01.md` | Exact 22-line post-baseline whitespace cleanup and remaining acceptance boundary. |
| `docs/V12_52_LOCAL_ARTIFACT_CLASSIFICATION_2026-09-01.md` | Eight-bucket `.local/` classification, narrow ignore policy, and external archive rule. |
| `docs/V12_53_SECONDARY_LOCAL_ARTIFACT_ARCHIVE_2026-09-01.md` | Secondary archives/discovery classification and fail-fast PowerShell acceptance correction. |
| `docs/V12_53_LOCAL_ACCEPTANCE_PROOF_2026-09-01.md` | Exact-head fail-fast local acceptance proof at `b2cc754...`. |
| `docs/L_AUSTRIA_NON_BLIND_LEGAL_QUALITY_FEEDBACK_2026-09-01.md` | Non-blind legal feedback, source verification, benchmark hardening and stale-packet boundary. |
| `docs/L_V12_55_PROFESSIONAL_REVIEW_HANDOFF_LOCAL_PROOF_2026-09-01.md` | Historical exact-head V12.55 v2 handoff proof. |
| `docs/L_AUSTRIA_PRELIMINARY_BLIND_RETURN_RECONCILIATION_2026-09-01.md` | Historical v2 return/contract analysis; independence rejection superseded by V12.58. |
| `docs/L_AUSTRIA_GENUINE_BLIND_REVIEW_OPERATOR_CORRECTION_2026-09-01.md` | Corrects review independence classification and defines v3 reaffirmation/provenance requirements. |
| `docs/L_AUSTRIA_V3_RETURN_VALIDATION_ATTEMPT_2026-09-01.md` | Genuine review preserved; supplied v3-style return rejected for stale fingerprint / legacy vocab / incomplete ASSESSED labels. |
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
