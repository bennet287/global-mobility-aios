# Global Mobility AIOS — V12 Active Changelog

This changelog records current meaningful delivery on `roadmap/global-mobility-aios-v12`.

Frozen V11 reference head remains `ac130deaafa7aa44068e9459facbda2b4df327d6`.

The active changelog was rotated after V12.33. Exact older detail remains in Git history and `docs/archive/CHANGELOG_THROUGH_V12_33_2026-08-31.md`.

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
| V12.35 | 2026-08-31 | Technology Radar V1.3.7 consolidated current-horizon frontier complete |
| V12.34 | 2026-08-31 | Technology Radar V1.3.6 + Wave E2 adversarial contract hardening |
| V12.33 | 2026-08-31 | bounded SecretsPort / non-production OpenBao pilot |
| V12.32 | 2026-08-30 | supplemental blind Austria AI domain-corroboration harness |
| V12.31 | 2026-08-30 | Technology Radar V1.3.5 external-agent infrastructure classification |
| V12.30 | 2026-08-30 | L live-runtime acceptance evidence reconciliation |
| V12.19 | 2026-08-21 | canonical combined architecture + H→I direction; R3–R5 protected-context rule |
