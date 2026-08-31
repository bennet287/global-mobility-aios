# Global Mobility AIOS — V12 Active Changelog

This changelog records current meaningful delivery on `roadmap/global-mobility-aios-v12`.

Frozen V11 reference head remains `ac130deaafa7aa44068e9459facbda2b4df327d6`.

The active changelog was rotated after V12.33. Exact older detail remains in Git history and `docs/archive/CHANGELOG_THROUGH_V12_33_2026-08-31.md`.

---

## 2026-08-31 — V12.41 TRACK B DURABLE ACTIVITY LINEAGE

### Status

**IMPLEMENTED / CURRENT-HEAD LOCAL + BROWSER PROOF PENDING / CANONICAL AIOS ACTIVITY REUSED / NO MUNDER RUNTIME ADOPTION / L ACCEPTANCE STATUS UNCHANGED / M NOT STARTED**

A Track B anti-duplication pass found that the Austria Live Organization backend already returned durable Board-safe `OrganizationActivity` records, trace identifiers and causation fields, while the Cockpit only displayed the activity count. The missing product capability was presentation of existing lineage, not a new event/transcript system.

Implemented:

```text
apps/web/lib/live-organization.ts
  mirror existing causation_activity_id

apps/web/app/cockpit/live-organization/page.tsx
  render snapshot.activities as Durable activity lineage
  show actor/position, activity type, WorkItem, trace and persisted causation
  retain explicit non-authority wording for provider transcripts/tool logs/donor events
  tolerate null/absent legacy runtime_quality fixture values

apps/web/scripts/live-organization-surface.test.mjs
  guard canonical activities/causation presentation
  guard provider transcript/tool/donor non-authority boundary

apps/web/e2e/tests/live-organization.spec.ts
  refresh stale runtime_quality fixture
  exercise runtime-economics presentation
  exercise persisted activity-lineage presentation
```

No backend persistence/schema, donor event bus, transcript database, presence timer, Munder package, CopilotKit/AG-UI package or collaboration authority was added.

Permanent boundary:

```text
provider transcript != canonical OrganizationActivity automatically
TELEMETRY != CANONICAL ORGANIZATION ACTIVITY
```

The previous V12.40 runtime-economics tranche was locally exercised at exact head `693c9975995bf8fc6388773d120594e5a1a75447` with 30/30 design-foundation tests, 4/4 request-auth tests, compiled-auth, TypeScript, Next.js build, repository policy, release consistency, dependency constraints, diff hygiene and git diff checks all passing. That run did not execute Playwright E2E and does not prove this later V12.41 head.

Dedicated record:

`docs/TRACK_B_DURABLE_ACTIVITY_LINEAGE_2026-08-31.md`

Remaining Track B gaps stay demand-gated: canonical presence/heartbeat, event synchronization transport, provider transcript/tool capture beyond durable activity lineage, semantic collaboration visualization, Living Organization scene mechanics and broader AI Economics history.

L remains `IMPLEMENTED / ACCEPTANCE PENDING`; genuine independent professional Austria review and final post-review exact-current-head proof remain release-critical. M remains `NOT STARTED`.

---

## 2026-08-31 — V12.39 WAVE E4 LOCAL PROOF OBSERVED

### Status

**LOCAL EXACT-HEAD TECHNICAL PROOF OBSERVED AT `5d8e940e3e979b097e20bba1b6c002ba6a0d8d72` / WAVE E4 PASS / FULL BACKEND PASS / CI RUNNER STARTUP FAILURE REMAINS INFRASTRUCTURE-ONLY / L ACCEPTANCE STATUS UNCHANGED / M NOT STARTED**

Observed local proof on Windows PowerShell / CPython at exact head `5d8e940e3e979b097e20bba1b6c002ba6a0d8d72`:

```text
dependency install/check                       PASS — no broken requirements
compileall                                     PASS
Wave E2 adversarial contract                   PASS — 17 / 17 scenarios
Wave E4 bounded semantic mutation strength     PASS — 8 / 8 mutants killed; 0 survived
focused AI-domain + v10.22 regression suite    PASS — 25 tests
full backend suite                             PASS — 1328 passed / 22 skipped
repository policy                              PASS
release consistency                            PASS
Python dependency constraints                  PASS — 27 direct dependencies
diff hygiene                                   PASS
git diff --check                               PASS
working tree / local-vs-origin                  clean and synchronized
```

The recurring Pydantic `model_metadata_json` protected-namespace warning remained non-failing and is not promoted to a source defect by this proof.

GitHub Actions for this exact head reported failure labels but the observed jobs had zero executed steps / no runner identity. Per repository proof semantics, those runs are infrastructure/runner-startup evidence rather than repository-test failures and do not negate the local technical proof.

This checkpoint does **not** seal L. Genuine independent professional Austria review and the final post-review exact-current-head technical proof remain mandatory.

---

## 2026-08-31 — V12.38 WAVE E4 MUTATION-ORACLE REPAIR

### Status

**FIX IMPLEMENTED / REPAIRED-HEAD LOCAL PROOF PENDING / PRODUCTION EVALUATOR UNCHANGED / L ACCEPTANCE STATUS UNCHANGED / M NOT STARTED**

The first local Wave E4 acceptance run correctly failed with two mutation-strength test failures. Investigation showed that the production Austria AI-domain evaluator was not the defect; the route-scope mutation oracle itself could produce a false-safe result.

The `invert-route-scope-guard` probe originally changed only the first review pathway. When the implementation guard was inverted, the changed review escaped the intended route check, but the second untouched valid review then raised `ValueError` under the inverted condition. Because the probe only observed whether any validation error occurred, that unrelated rejection allowed the weakened mutant to survive.

Repair:

```text
scripts/check_ai_domain_mutation_strength.py
```

The route probe now assigns the invented pathway to every review in the payload. The baseline must reject the all-invalid payload, while the inverted mutant can no longer rely on a later untouched valid review to create a false-positive rejection.

This repair changes only the Wave E4 test-strength harness. `scripts/evaluate_austria_ai_domain_review.py` and its production authority/source/corroboration semantics are unchanged.

Observed failed-run truth:

```text
focused Wave E2/E3/E4 pytest              FAIL — 17 passed / 2 failed
failing tests                              mutation-strength aggregate + per-mutant kill assertion
failure class                              surviving route-scope mutant due oracle ambiguity
production evaluator defect               NOT OBSERVED
```

No repaired-head PASS is claimed until the local acceptance commands are rerun.

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

---

## 2026-08-31 — V12.36 TECHNOLOGY RADAR WAVE E3 — PROPERTY / INVARIANT TESTING

### Status

**IMPLEMENTED / LOCAL-CI PROOF PENDING / NO PRODUCTION RUNTIME ADOPTION / L ACCEPTANCE STATUS UNCHANGED / M NOT STARTED**

Wave E3 advances the evaluation-hardening ladder from one-example deterministic adversarial cases into generated property/invariant testing.

Implemented:

```text
apps/api/requirements.txt
apps/api/tests/test_ai_domain_property_invariants.py
docs/TECHNOLOGY_RADAR_WAVE_E3_PROPERTY_INVARIANT_TESTING_2026-08-31.md
```

Hypothesis is added as a bounded test dependency only:

```text
hypothesis>=6.112
```

The new property suite reuses the existing Austria AI-domain validation/corroboration seams instead of introducing another evaluator stack. Generated tests cover:

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

The connected GitHub implementation environment could author and push the files but did not execute the repository Python environment. Focused pytest, full backend, Woodpecker and exact-current-head proof therefore remain pending.

Current truth:

```text
Technology Radar V1.3.7                  COMPLETE / ACTIVE CANONICAL RADAR
Wave E2 deterministic adversarial gate   IMPLEMENTED / LOCAL-CI PROOF PENDING
Wave E3 property/invariant testing        IMPLEMENTED / LOCAL-CI PROOF PENDING
Hypothesis production runtime adoption    NONE
professional Austria review               PENDING
final exact-current-head proof            PENDING
L                                          IMPLEMENTED / ACCEPTANCE PENDING
M                                          NOT STARTED
```

Next evaluation-hardening candidate after E3 proof: bounded mutation testing on the same high-value evaluator/corroboration seams.

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

### Current truth

```text
Technology Radar V1.3.7                  COMPLETE / ACTIVE CANONICAL RADAR
runtime adoption caused by V1.3.7        NONE
Wave E2                                  IMPLEMENTED / LOCAL-CI PROOF PENDING
professional Austria review              PENDING
final exact-current-head proof           PENDING
L                                        IMPLEMENTED / ACCEPTANCE PENDING
M                                        NOT STARTED
```

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
| V12.38 | 2026-08-31 | Wave E4 mutation-oracle repair after first local acceptance failure |
| V12.37 | 2026-08-31 | Wave E4 bounded semantic implementation mutation-strength testing |
| V12.36 | 2026-08-31 | Wave E3 Hypothesis property/invariant testing |
| V12.35 | 2026-08-31 | Technology Radar V1.3.7 consolidated current-horizon frontier complete |
| V12.34 | 2026-08-31 | Technology Radar V1.3.6 + Wave E2 adversarial contract hardening |
| V12.33 | 2026-08-31 | bounded SecretsPort / non-production OpenBao pilot |
| V12.32 | 2026-08-30 | supplemental blind Austria AI domain-corroboration harness |
| V12.31 | 2026-08-30 | Technology Radar V1.3.5 external-agent infrastructure classification |
| V12.30 | 2026-08-30 | L live-runtime acceptance evidence reconciliation |
| V12.19 | 2026-08-21 | canonical combined architecture + H→I direction; R3–R5 protected-context rule |
