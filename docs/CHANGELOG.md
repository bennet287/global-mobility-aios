# Global Mobility AIOS — V12 Active Changelog

This changelog records current meaningful delivery on `roadmap/global-mobility-aios-v12`.

Frozen V11 reference head remains `ac130deaafa7aa44068e9459facbda2b4df327d6`.

The active changelog was rotated after V12.33. Exact older detail remains in Git history and `docs/archive/CHANGELOG_THROUGH_V12_33_2026-08-31.md`.

---

## 2026-08-31 — V12.37 TECHNOLOGY RADAR WAVE E4 — MUTATION-STRENGTH TESTING

### Status

**IMPLEMENTED / LOCAL-CURRENT-HEAD PROOF PENDING / NO EXTERNAL MUTATION ENGINE ADOPTION / L ACCEPTANCE STATUS UNCHANGED / M NOT STARTED**

Wave E4 advances evaluation hardening from adversarial input mutation and generated properties into mutation of selected implementation logic itself.

Implemented:

```text
scripts/check_ai_domain_mutation_strength.py
apps/api/tests/test_ai_domain_mutation_strength.py
docs/TECHNOLOGY_RADAR_WAVE_E4_MUTATION_TESTING_2026-08-31.md
```

The first-party gate applies exact semantic source mutations to `scripts/evaluate_austria_ai_domain_review.py`, loads each mutant in isolation and requires the corresponding safety probe to detect the regression. The selected mutation classes cover:

```text
weakened false-only authority enforcement
inverted pathway/review-scope enforcement
weakened mixed valid+forged source rejection
weakened non-empty rationale enforcement
changed distinct-provider corroboration threshold
weakened unanimity cardinality
weakened all-provider source-label agreement
weakened provider-identity qualification
```

A mutant is counted as `KILLED` only when the baseline probe passes and the mutated implementation fails that same safety property. Any surviving declared mutant fails the Wave E4 gate.

The named `mutmut` challenger was rechecked before implementation. Current public package metadata reports mutmut 3.7.0 and Python 3.13 support, but current mutmut 3 documentation requires operating-system `fork` support and therefore WSL on Windows. Because the canonical local proof operator is Windows PowerShell/CPython and this tranche only needs bounded high-value semantic mutation, mutmut is **not** added to the dependency contract. It remains a future Linux/CI challenger.

Observed prior checkpoint:

```text
exact head 285a7f08eb5289b9f037c28293a65ad94eede91b
Wave E2 adversarial gate                  PASS — 17/17 scenarios
focused E2+E3 pytest                      PASS — 16 tests
repository policy                         PASS
release consistency                       PASS
Python direct-dependency constraints      PASS — 27 dependencies
diff hygiene                              PASS
```

That proof is historical exact-head evidence only. It does not automatically prove the later Wave E4 head.

Permanent proof boundary:

```text
bounded semantic mutation strength
!= exhaustive mutation coverage
!= fuzzing
!= live-model adversarial resistance
!= professional Austria correctness
!= operational Red Team proof
!= L acceptance
```

Current truth:

```text
Technology Radar V1.3.7                  COMPLETE / ACTIVE CANONICAL RADAR
Wave E2 deterministic adversarial gate   IMPLEMENTED / LOCAL PROOF OBSERVED AT 285a7f08...
Wave E3 property/invariant testing        IMPLEMENTED / LOCAL PROOF OBSERVED AT 285a7f08...
Wave E4 mutation-strength testing         IMPLEMENTED / LOCAL-CURRENT-HEAD PROOF PENDING
external mutation engine adoption         NONE
professional Austria review               PENDING
final exact-current-head proof            PENDING
L                                          IMPLEMENTED / ACCEPTANCE PENDING
M                                          NOT STARTED
```

After E4 local proof, the product path should return to the genuine professional Austria review unless a concrete source defect or prerequisite is discovered.

---

## 2026-08-31 — V12.36 TECHNOLOGY RADAR WAVE E3 — PROPERTY / INVARIANT TESTING

### Status

**IMPLEMENTED / LOCAL PROOF OBSERVED AT EXACT HEAD 285a7f08... / NO PRODUCTION RUNTIME ADOPTION / L ACCEPTANCE STATUS UNCHANGED / M NOT STARTED**

Wave E3 advances the evaluation-hardening ladder from one-example deterministic adversarial cases into generated property/invariant testing.

Implemented:

```text
apps/api/requirements.txt
apps/api/constraints.txt
apps/api/tests/test_ai_domain_property_invariants.py
docs/TECHNOLOGY_RADAR_WAVE_E3_PROPERTY_INVARIANT_TESTING_2026-08-31.md
```

Hypothesis is a bounded test dependency only. The repository dependency policy requires an exact constraint, and the accepted local checkpoint uses:

```text
requirement: hypothesis>=6.112
constraint:  hypothesis==6.167.1
```

The property suite reuses the existing Austria AI-domain validation/corroboration seams instead of introducing another evaluator stack. Generated tests cover:

```text
non-False final_authority_decision values fail closed
undeclared pathway substitutions fail closed
unknown source references fail closed
case-set substitutions fail closed
valid provider-review ordering canonicalizes to benchmark order
same-provider repetition never creates independent corroboration
identity / structural / source-label gates remain conjunctive
cross-provider classification disagreement cannot corroborate
professional_review_status_effect remains NONE
```

Permanent proof boundary:

```text
property/invariant test proof
!= exhaustive state-space proof
!= mutation-test strength proof
!= fuzz proof
!= live-model adversarial resistance
!= professional Austria correctness
!= operational Red Team proof
!= L acceptance
```

Local proof was observed at exact head `285a7f08eb5289b9f037c28293a65ad94eede91b`: the 17-scenario Wave E2 gate passed; focused E2+E3 pytest reported 16 passed; repository policy, release consistency, dependency constraints and diff hygiene all passed; V12 matched remote; frozen remote V11 remained `ac130deaafa7aa44068e9459facbda2b4df327d6`.

That local proof remains exact-checkpoint evidence only after later commits.

---

## 2026-08-31 — V12.35 TECHNOLOGY RADAR V1.3.7 — CONSOLIDATED AGGRESSIVE FRONTIER COMPLETE

### Status

**RADAR INVENTORY COMPLETE FOR CURRENT PRODUCT HORIZON / NO RUNTIME ADOPTION / L ACCEPTANCE STATUS UNCHANGED / M NOT STARTED**

The user explicitly required completion of the Technology Radar before proceeding to the next product gate. V1.3.7 therefore consolidates the broad current-horizon frontier instead of continuing with product milestone work mid-Radar.

The governing posture remains:

> **Aggressive Radar. Conservative production authority.**

> **Research broadly. Benchmark ruthlessly. Adopt narrowly.**

V1.3.7 preserves V1.3.6 and adds explicit challengers/research targets across:

```text
AI evaluation / adversarial engineering
  Inspect AI
  ToolSandbox / AgentDojo-style behavioral evaluation
  DeepTeam
  FuzzyAI-class fuzzing

AI observability / experiment analysis
  OpenInference
  OpenLLMetry
  Arize Phoenix
  Opik-class challenger

application / API security
  Bandit
  OWASP ZAP
  Schemathesis
  Nuclei

supply-chain / dependency / secrets
  OSV-Scanner
  TruffleHog
  OpenSSF Scorecard
  in-toto
  GUAC

IaC / deployment assurance
  Checkov
  KICS
  Kubescape
  kube-bench

sandbox challengers
  E2B
  Daytona-class managed sandbox/workspace
  Nightona watch candidate

policy challengers
  Cedar
  Kyverno

frontend engineering
  Storybook component-workbench candidate
```

Existing incumbents and candidates remain visible, including OpenTelemetry, Promptfoo, backup/restore, ClamAV, SecretsPort/OpenBao, Wave E2, Docling, Qdrant, Langfuse, OpenFGA, OPA, CopilotKit/AG-UI, Garak, PyRIT, DeepEval, Ragas, Hypothesis, mutation/fuzzing, Semgrep, CodeQL, Trivy, Syft/Grype, SLSA/Sigstore, Gitleaks, Microsandbox, Mem0, OpenViking, Agno/AgentOS, LangGraph, Temporal, LLMLingua-2, pgvector, Presidio, urlwatch and EU DSS.

No new candidate is installed or promoted by this Radar documentation. Kubernetes-specific candidates remain WATCH until Kubernetes is a real deployment target. Sandbox, Red Team and policy-engine candidates remain subordinate to AIOS authority boundaries.

New permanent interpretation additions:

```text
EVALUATOR SCORE != PROFESSIONAL CORRECTNESS
SECURITY FINDING != EXPLOITABILITY TRUTH
```

### Radar completion definition

“Complete” means the major relevant capability lanes now have explicit incumbents, challengers or research targets for the current product horizon. It does not permanently close technology scouting. A future Radar addition should require a material new capability, materially stronger challenger, major ecosystem change or newly demonstrated AIOS gap.

---

## 2026-08-31 — V12.34 TECHNOLOGY RADAR V1.3.6 + WAVE E2 EVALUATION / ADVERSARIAL CONTRACT HARDENING

V12.34 introduced the explicit aggressive-Radar posture and the first-party deterministic adversarial mutation gate for the Austria AI-domain review contract. It added explicit Promptfoo expansion, Garak, PyRIT, DeepEval, Ragas-style methods, Hypothesis, mutation testing, fuzzing, Semgrep, CodeQL, Trivy, Syft/Grype, SLSA/Sigstore, secret scanning and OWASP API assurance candidates.

Wave E2 covers authority escalation, route substitution, forged/missing/duplicate cases and sources, invented classifications, uncited/empty conclusions, fake consensus, provider/model mismatch, structural failure, source-label mismatch and indirect prompt-injection boundary behavior.

Proof boundary remains:

```text
deterministic adversarial contract proof
!= live-model attack resistance
!= independent professional review
!= operational Red Team proof
```

### Recent-history index

| Version | Date | Meaning |
|---|---|---|
| V12.37 | 2026-08-31 | Wave E4 bounded semantic implementation-mutation strength |
| V12.36 | 2026-08-31 | Wave E3 Hypothesis property/invariant testing |
| V12.35 | 2026-08-31 | Technology Radar V1.3.7 consolidated current-horizon frontier complete |
| V12.34 | 2026-08-31 | Technology Radar V1.3.6 + Wave E2 adversarial contract hardening |
| V12.33 | 2026-08-31 | bounded SecretsPort / non-production OpenBao pilot |
| V12.32 | 2026-08-30 | supplemental blind Austria AI domain-corroboration harness |
| V12.31 | 2026-08-30 | Technology Radar V1.3.5 external-agent infrastructure classification |
| V12.30 | 2026-08-30 | L live-runtime acceptance evidence reconciliation |
| V12.19 | 2026-08-21 | canonical combined architecture + H→I direction; R3–R5 protected-context rule |