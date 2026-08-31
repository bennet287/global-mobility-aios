# Global Mobility AIOS — Technology Adoption Ledger

**Date:** 2026-08-31  
**Status:** ACTIVE REPOSITORY-TRUTH INDEX  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Original ledger baseline head:** `74082e7296e17333027cebd7ca602d408f558f95`  
**Latest reconciliation:** V12.37 / Technology Radar Wave E4 mutation-strength pilot  
**Scheduling authority:** `docs/ROADMAP.md`  
**Technology evaluation authority:** `docs/TECHNOLOGY_RADAR_V1_3_7.md`  
**Delivery history:** `docs/CHANGELOG.md`

This ledger prevents Radar entries from being mistaken for installed technology and prevents native AIOS capability from being mistaken for missing capability merely because an external product is absent.

## 1. Permanent rules

```text
Radar presence != runtime implementation
native capability != external-provider adoption
adapter implementation != production adoption
evaluation score != professional correctness
security finding != exploitability/authority truth
```

Before implementing a named technology inspect dependencies, imports, configuration, tests, commit history, ROADMAP, Radar, CHANGELOG and this ledger.

Permanent architecture boundaries:

```text
CAN DO != MAY DO
MEMORY != EVIDENCE
SANDBOX ISOLATION != EXECUTION AUTHORITY
AGENT FRAMEWORK STATE != ORGANIZATION TRUTH
UI INTENT != COMMAND AUTHORIZATION
TELEMETRY != CANONICAL ORGANIZATION ACTIVITY
SKILL KNOWLEDGE != EXECUTION AUTHORITY
```

## 2. Implemented / existing foundations — do not duplicate

| Capability | Repository truth |
|---|---|
| OpenTelemetry | vendor-neutral telemetry foundation exists; pilot complete / trial-eligible |
| Promptfoo | pilot complete / trial-eligible; expansion candidate, not a missing pilot |
| backup + isolated restore | bounded recoverability proof implemented |
| ClamAV | malware scan/quarantine pilot complete / trial-eligible |
| SecretsPort | AIOS-owned secret-reference boundary implemented |
| OpenBao | optional non-production bounded adapter implemented; production adoption not claimed |
| Wave E2 adversarial contract | first-party deterministic input-mutation gate implemented; local proof observed at historical exact head `285a7f08...`; higher-order security proof not claimed |
| Wave E3 property/invariant testing | Hypothesis-based bounded property suite implemented; local proof observed at historical exact head `285a7f08...`; Hypothesis is test-only |
| Wave E4 mutation strength | first-party bounded semantic implementation-mutation gate implemented; current-head local proof pending |
| Docling | pilot in progress |
| Qdrant | current semantic-retrieval platform capability / comparison baseline |

## 3. V1.3.7 explicit challengers — Radar entry alone is not adoption

| Candidate | Ledger truth |
|---|---|
| Inspect AI | priority research / evaluation benchmark; no runtime adoption claimed |
| ToolSandbox / AgentDojo-style methods | behavioral tool-use benchmark research; method/candidate, not AIOS truth |
| DeepTeam | red-team benchmark research; no operational Red Team authority |
| FuzzyAI-class tooling | specialized LLM fuzz benchmark research only |
| OpenInference | interoperability/semantic-convention benchmark only |
| OpenLLMetry | instrumentation donor research only |
| Arize Phoenix | priority Langfuse/observability challenger; no integration claimed |
| Opik/equivalent | experiment/eval-observability benchmark only |
| Bandit | lightweight Python security baseline candidate |
| OWASP ZAP | authorized DAST pilot candidate only |
| Schemathesis | API property/negative-test candidate only |
| Nuclei | authorized scanner candidate only |
| OSV-Scanner | dependency vulnerability challenger only |
| TruffleHog | secret-scanner challenger only |
| OpenSSF Scorecard | upstream dependency-governance candidate only |
| in-toto | provenance-chain research candidate only |
| GUAC | watch; supply-chain graph candidate only if scale creates need |
| Checkov / KICS | IaC benchmark challengers only |
| Kubescape / kube-bench | watch; only if Kubernetes becomes a real deployment target |
| E2B | managed sandbox challenger; not adopted |
| Daytona-class sandbox | managed workspace challenger; current licensing/hosting must be rechecked at pilot time |
| Nightona | watch; self-hosted Daytona-derived candidate; maturity/license must be rechecked |
| Cedar | policy-language challenger; no policy authority granted |
| Kyverno | watch; Kubernetes policy candidate only |
| Storybook | component-workbench candidate; no product-truth role |

## 4. Existing external candidates most likely to be confused with missing capability

| Candidate | Current truth |
|---|---|
| Langfuse | research/pilot candidate; AIOS + OTel already provides baseline observability |
| OpenFGA | deferred relationship-authorization pilot; native AIOS authorization exists |
| OPA/Rego | research policy-engine candidate; native AIOS governance exists |
| CopilotKit / AG-UI | post-L M interaction candidate; not installed/adopted |
| Garak | bounded live-model adversarial research candidate |
| Microsoft PyRIT | future authorized Red Team Lab candidate |
| DeepEval | evaluation benchmark candidate |
| Ragas | retrieval-metric benchmark candidate |
| Hypothesis | bounded test-only property/invariant pilot implemented; no production runtime role |
| mutmut | external mutation-engine challenger rechecked at 3.7.0; not adopted because current mutmut 3 requires `fork`/WSL on Windows; future Linux/CI campaign remains demand-gated |
| Atheris/fuzzing | bounded parser/contract fuzz candidate |
| Semgrep | priority SAST pilot candidate |
| CodeQL | semantic security benchmark candidate |
| Trivy | container/dependency/IaC pilot candidate |
| Syft / Grype | SBOM/vulnerability candidates |
| SLSA / Sigstore | provenance/signing target controls/candidates |
| Gitleaks | secret-scanning pilot candidate |
| Microsandbox | primary future isolated-execution candidate; not adopted |
| Mem0 | continuity-memory candidate only; never Evidence |
| OpenViking | context donor research only |
| Agno / AgentOS | donor/assess only; cannot replace AIOS control plane |
| LangGraph | execution-graph donor only; cannot become WorkItem truth |
| Temporal | deferred gap-triggered durable-workflow candidate |
| LLMLingua-2 | selected compression pilot; R3–R5 protected context remains zero-semantic-compression by default |
| pgvector | retrieval benchmark challenger to Qdrant |
| Presidio | queued privacy pilot |
| urlwatch | queued source-monitoring pilot |
| EU DSS | document-signature/trust research |

## 5. Cybersecurity / Red Team truth

The governed cybersecurity donor and AIOS Red Team / Adversarial Security Lab programme has already started at architecture/Radar level. Do not redesign it from zero.

```text
Cybersecurity Skill Registry runtime       NOT YET CLAIMED
operational offensive Red Team agents      NOT YET CLAIMED
arbitrary production-target authority      REJECTED
Promptfoo                                  existing bounded evaluation pilot
Garak/PyRIT/DeepTeam/FuzzyAI               research candidates only
Microsandbox-backed lab                     future candidate only
```

`SKILL KNOWLEDGE != EXECUTION AUTHORITY`.

## 6. Mandatory anti-duplication checklist

```text
[ ] What exact product problem is being solved now?
[ ] Does first-party AIOS already solve the capability natively?
[ ] Is there already an AIOS-owned port/adapter?
[ ] Is the named technology actually present in dependencies/imports/config?
[ ] Is there an existing pilot/test/receipt/commit?
[ ] Does ROADMAP permit implementation now?
[ ] Would adoption create a second truth/authority/control plane?
[ ] What is the bounded acceptance test?
[ ] What is explicitly NOT being claimed?
[ ] Have ROADMAP / CHANGELOG / this ledger been reconciled?
```

## 7. Radar-completion interpretation

Technology Radar V1.3.7 is **complete for the broad current product horizon**. This means the major relevant lanes have explicit coverage and future additions require a material new capability, materially stronger challenger, ecosystem change or demonstrated AIOS gap.

It does not mean all candidates should be installed.

```text
Technology Radar V1.3.7                  COMPLETE / ACTIVE
runtime adoption caused by V1.3.7        NONE
external mutation engine adoption        NONE
L                                        IMPLEMENTED / ACCEPTANCE PENDING
M                                        NOT STARTED
```

ROADMAP remains the implementation scheduler.
