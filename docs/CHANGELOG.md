# Global Mobility AIOS — V12 Active Changelog

This changelog records current meaningful delivery on:

```text
roadmap/global-mobility-aios-v12
```

Repository lineage:

```text
V12 fork origin
  dd2f2cd6e9e47179b1fd744ba3f56daf7c787449

Frozen V11 reference branch final documentation head
  ac130deaafa7aa44068e9459facbda2b4df327d6
```

> **V11 preserves the reference product checkpoint. V12 is the active implementation line.**

The active changelog was rotated after V12.33 to keep current repository truth readable. The exact pre-rotation `CHANGELOG.md` content remains immutable in Git as blob `c9111991129cab34f5f236e85c9bc40df5bc3f59`; `docs/archive/CHANGELOG_THROUGH_V12_33_2026-08-31.md` records that archive boundary. Older detailed entries remain available through Git history and the repository's existing changelog archives.

---

## 2026-08-31 — V12.34 TECHNOLOGY RADAR V1.3.6 + WAVE E2 EVALUATION / ADVERSARIAL CONTRACT HARDENING

### Status

**BOUNDED DEFENSIVE EVALUATION TRANCHE IMPLEMENTED / PYTHON SYNTAX VALIDATED BEFORE PUSH / FOCUSED PYTEST + FULL EXACT-HEAD PROOF PENDING / PROFESSIONAL REVIEW STILL PENDING / M NOT STARTED**

This tranche responds to a known evaluation-quality concern: deterministic/mock tests were too shallow to be treated as serious AI-quality evidence. The repository had already progressed beyond that limitation through blind provider evaluation, real configured-provider execution, fresh official-source retrieval, provider failure evidence and cross-provider corroboration. V12.34 adds the missing deterministic adversarial-contract layer without pretending it proves live-model security.

Implemented:

```text
scripts/check_ai_domain_adversarial_contract.py
apps/api/tests/test_ai_domain_adversarial_contract.py
docs/TECHNOLOGY_RADAR_WAVE_E2_EVALUATION_HARDENING_2026-08-31.md
docs/TECHNOLOGY_RADAR_V1_3_6.md
docs/ROADMAP.md
docs/CHANGELOG.md
```

The new gate reuses the existing `evaluate_austria_ai_domain_review.py` contract instead of creating another provider/mock stack.

### Adversarial contract scenarios

The gate contains a positive baseline plus deterministic mutations for:

1. attempted AI authority escalation through `final_authority_decision=true`;
2. undeclared pathway/route substitution;
3. forged source references;
4. duplicate case substitution;
5. silent case omission;
6. invented authority-like classifications;
7. uncited conclusions;
8. empty review rationale;
9. single-provider pseudo-corroboration;
10. repeated runs from the same provider pretending to be independent corroboration;
11. cross-provider disagreement;
12. provider/model identity mismatch;
13. structural provider-output failure;
14. source-label/pathway mismatch;
15. positive two-distinct-provider corroboration control;
16. indirect prompt-injection instructions embedded in source text.

The prompt-injection scenario proves only that the existing system prompt explicitly treats source material as untrusted, hostile instructions remain source data, final-authority claims are forbidden at the contract boundary, and hidden benchmark labels are not introduced. It does **not** claim live-model prompt-injection resistance.

Permanent proof boundaries:

```text
deterministic adversarial contract gate
!= live-model attack resistance

AI corroboration
!= independent professional review

security knowledge / test capability
!= Red Team execution authority
```

### Technology Radar V1.3.6

The active Radar now uses the explicit posture:

> **Aggressive Radar. Conservative production authority.**

V1.3.6 preserves V1.3.5 states unless explicitly changed and adds an aggressive evaluation/security research frontier covering:

```text
Promptfoo expansion              existing PILOT COMPLETE / TRIAL-ELIGIBLE
Garak                            RESEARCH / bounded live-model pilot candidate
Microsoft PyRIT                  RESEARCH / future Red Team Lab candidate
DeepEval                         RESEARCH / benchmark candidate
Ragas-style evaluation           RESEARCH / benchmark methods
Hypothesis                       BENCHMARK / high-priority property-testing candidate
mutation testing                 RESEARCH / bounded pilot candidate
Atheris / guided fuzzing         RESEARCH / bounded parser/contract candidate
Semgrep                          PRIORITY RESEARCH / pilot candidate
GitHub CodeQL                    PRIORITY RESEARCH / benchmark candidate
Trivy                            PRIORITY RESEARCH / pilot candidate
Syft + Grype                     RESEARCH / SBOM + vulnerability candidates
SLSA + Sigstore                  RESEARCH / build-provenance candidates
Gitleaks-class scanning          PRIORITY RESEARCH / pilot candidate
OWASP API assurance              PRIORITY RESEARCH / continuous-test target
Langfuse                         remains measured-gap RESEARCH / PILOT CANDIDATE
Microsandbox                     remains post-L isolated-execution candidate
CopilotKit / AG-UI               remains post-L/M interaction candidate
```

No named external candidate above became a production dependency merely by entering the Radar.

### R3 continuity clarified

Historical project progress already records that R3–R5 protected context defaults to zero semantic compression for mandatory Evidence, critical VerifiedRules, exact money/dates/identifiers, authority/autonomy/risk/policy constraints, contradictions and material action/source identifiers. The current evaluation-hardening work continues that evidence-first trajectory rather than creating a new unrelated R3 milestone.

The quality progression is now explicitly documented as:

```text
unit contracts
→ deterministic adversarial mutation
→ property / invariant testing
→ mutation testing / fuzzing
→ fault injection
→ real-provider evaluation
→ fresh-source evaluation
→ cross-provider disagreement analysis
→ poisoned/contradictory context evaluation
→ authorization/replay/tenant-isolation attacks
→ concurrency/race proof
→ independent professional domain review
→ isolated Red Team / purple-team retest
→ continuous regression
```

Each layer retains its own evidence label.

### Verification truth

The connected implementation session compiled the newly authored Python source text before pushing it, but it did not execute the repository environment's pytest suite. Therefore no focused pytest PASS, full backend PASS, Woodpecker PASS or exact-current-head acceptance is claimed here.

Canonical focused commands are:

```text
python -m compileall -q scripts/check_ai_domain_adversarial_contract.py
python scripts/check_ai_domain_adversarial_contract.py
python -m pytest -q apps/api/tests/test_ai_domain_review_cli.py apps/api/tests/test_ai_domain_adversarial_contract.py
```

### Current truth

```text
Wave E2 deterministic adversarial gate      IMPLEMENTED / PROOF PENDING
Technology Radar V1.3.6                     ACTIVE
Operational offensive Red Team runtime      NOT CLAIMED
Live-model prompt-injection resistance       NOT CLAIMED
Independent professional Austria review     PENDING
Final exact-current-head proof               PENDING
Overall L                                    IMPLEMENTED / ACCEPTANCE PENDING
M                                            NOT STARTED
```

The active roadmap advances from **V12.33 to V12.34** for this bounded supporting evaluation/security tranche only.

---

## Active recent-history index

Detailed pre-V12.34 entries remain in immutable Git history. Most recent checkpoints before rotation:

| Version | Date | Meaning |
|---|---|---|
| V12.33 | 2026-08-31 | bounded SecretsPort / non-production OpenBao pilot |
| V12.32 | 2026-08-30 | supplemental blind Austria AI domain-corroboration harness |
| V12.31 | 2026-08-30 | Technology Radar V1.3.5 external-agent infrastructure classification |
| V12.30 | 2026-08-30 | L live-runtime acceptance evidence reconciliation |
| V12.29 | 2026-08-29 | Hy4 Preview frontend-development Radar entry |
| V12.28 | 2026-08-25 | repository-truth / L acceptance + CI reconciliation |
| V12.19 | 2026-08-21 | canonical combined architecture + H→I direction; R3–R5 protected-context rule recorded |

For exact historical acceptance counts, commit identities and earlier milestone detail, use Git history and the repository's archive documents rather than reconstructing them from this compact active index.
