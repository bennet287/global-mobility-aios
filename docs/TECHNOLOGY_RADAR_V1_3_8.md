# Global Mobility AIOS — Technology Radar V1.3.8

**Date:** 2026-08-31
**Status:** ACTIVE CANONICAL RADAR REVISION — CONSOLIDATED SEAMS / DUPLICATION REDUCED
**Supersedes for active radar direction:** `TECHNOLOGY_RADAR_V1_3_7.md`
**Source audit:** `docs/technology-radar/RADAR_SCATTER_AUDIT_2026-08-31.md`
**Scheduling authority:** `docs/ROADMAP.md`
**Adoption truth index:** `docs/TECHNOLOGY_ADOPTION_LEDGER.md`
**Latest reconciliation:** 2026-09-02 — M.7.4 technical closure + AI runtime / Model Router seam restoration
**Current product milestone:** L — COMPLETE / PASS / SEALED
**M milestone:** IN PROGRESS — M.7.4 GPU FLOW field TRIAL Iteration 1 IMPLEMENTED / TECHNICAL PASS; product-value benchmark pending

> **Aggressive Radar. Conservative production authority.**

> **Research broadly. Benchmark ruthlessly. Adopt narrowly.**

> **External infrastructure provides capability. AIOS owns meaning, truth and authority.**

V1.3.7 completed the broad current-horizon inventory. V1.3.8 applies the scatter/duplication audit to the Radar itself so future sessions see the consolidated decision state directly rather than treating every inventoried tool as an active research candidate.

This revision is classification/documentation only. It causes **no package installation, no runtime adoption, no R3 merge, no authority change, and no milestone promotion**.

## 1. Constitutional boundaries

```text
CAN DO != MAY DO
MEMORY != EVIDENCE
SANDBOX ISOLATION != EXECUTION AUTHORITY
AGENT FRAMEWORK STATE != ORGANIZATION TRUTH
UI INTENT != COMMAND AUTHORIZATION
TELEMETRY != CANONICAL ORGANIZATION ACTIVITY
SKILL KNOWLEDGE != EXECUTION AUTHORITY
EVALUATOR SCORE != PROFESSIONAL CORRECTNESS
SECURITY FINDING != EXPLOITABILITY TRUTH
```

Radar presence is not dependency presence. Benchmark success is not adoption. External state must not become canonical Organization, WorkItem, Evidence, authority, policy, memory, workflow or Board truth.

## 2. Radar-state vocabulary

```text
INCUMBENT
  preferred current capability/tool for a defined seam

CHALLENGER
  one materially different comparison target with a falsifiable promotion test

IMPLEMENTED / PILOT COMPLETE / PILOT IN PROGRESS
  repository evidence already exists; do not restart from zero

SELECTED PILOT / QUEUED PILOT
  explicit bounded pilot state; not production adoption

ADOPT
  selected infrastructure/product substrate with a clear multi-surface role

TRIAL
  strong product hypothesis scheduled for bounded implementation and benchmark
  promotion requires evidence against a maintained reference analytical baseline

EXPERIMENT
  weaker/semantically uncertain hypothesis
  success graduates it to TRIAL; failure may retire it or keep it lab-only

OPTIONAL VIEW
  non-core product surface; cannot displace the default operating interface without evidence

HOLD_WITH_TRIGGER
  inactive until the named gap/trigger occurs

WATCH
  ecosystem/deployment dependent; no current work

DONOR_ONLY / REFERENCE / TARGET_CONTROL
  ideas, methods or control targets only; not runtime candidates

REJECTED
  explicitly outside AIOS authority or product direction
```

A candidate may not remain generic `RESEARCH` across two Radar revisions. It must become an incumbent, challenger, bounded pilot, HOLD_WITH_TRIGGER, WATCH, donor/reference/control, or REJECTED entry with an explicit reason.

## 3. Consolidated seam map

| Seam | Incumbent | Challenger | Deferred / held |
|---|---|---|---|
| CI adversarial evaluation | Promptfoo | Inspect AI | DeepEval, Ragas, PyRIT, DeepTeam |
| live-model vulnerability scan | Garak | none yet | FuzzyAI-class tooling |
| behavioral tool-use evaluation | first-party contracts / ToolSandbox-style methods | ToolSandbox / AgentDojo methods | none |
| property/invariant testing | Hypothesis | none | none |
| mutation strength | first-party Wave E4 gate | mutmut on Linux/CI trigger | none |
| parser/contract fuzzing | first-party deterministic/property tests | none yet | Atheris/FuzzyAI until a measured fuzz gap |
| failure assurance | deterministic first-party fault injection | none | chaos platform adoption |
| engineering observability | OpenTelemetry | Arize Phoenix | Langfuse, OpenInference, OpenLLMetry, Opik |
| SAST | Semgrep | CodeQL | Bandit |
| DAST/API security | OWASP ZAP | Schemathesis | Nuclei |
| dependency/container scanning | Trivy | OSV-Scanner | Syft, Grype, Scorecard |
| repository secret scanning | Gitleaks | TruffleHog | none |
| artifact provenance/signing | existing repository controls | none | Sigstore/cosign, in-toto until signing/attestation trigger |
| dedicated IaC assurance | Checkov | KICS | Kubernetes-only tools WATCH |
| isolated execution | Microsandbox | E2B | Daytona HOLD, Nightona WATCH |
| relationship authorization | OpenFGA | SpiceDB | none |
| contextual policy evaluation | OPA/Rego | Cedar | Kyverno WATCH |
| semantic retrieval | Qdrant | pgvector | none |
| context compression | LLMLingua-2 selected pilot | none | none |
| continuity memory | AIOS memory boundary | Mem0 | OpenViking donor only |
| durable workflow | AIOS WorkItem/runtime baseline | Temporal on trigger | LangGraph/Agno donor only |
| document normalization | Docling | none | none |
| malware scanning | ClamAV | none | none |
| privacy/PII | existing AIOS privacy boundary | Presidio queued pilot | none |
| source-change monitoring | existing source-monitor baseline | urlwatch queued pilot | none |
| document trust/signatures | current document/evidence boundary | EU DSS on trigger | none |
| human-agent interaction | current AIOS Cockpit | CopilotKit / AG-UI post-L M | Storybook HOLD |
| model execution | deterministic template baseline + DeepSeek / Gemini / Moonshot provider adapters | Ollama optional dependency/config present; provider adapter not implemented | storage-streamed / memory-elastic large-local inference HOLD_WITH_TRIGGER; `kimi-k3-in-c` REFERENCE only |
| capability-qualified model routing | architecture-defined Model Router; adaptive runtime routing not implemented | no runtime challenger selected; benchmark before implementation | no second "Intelligence Router"; implementation remains roadmap/N-owned |
| design tooling | Penpot preferred environment | none | none |

## 4. AI evaluation, benchmark and adversarial lane

| Candidate | V1.3.8 state | Trigger / boundary |
|---|---|---|
| Promptfoo | **INCUMBENT / CI ADVERSARIAL SPINE / PILOT COMPLETE** | expand only when it strengthens continuous regression |
| Inspect AI | **CHALLENGER / STRUCTURED EVALUATION** | benchmark only against a concrete Promptfoo/current-harness gap |
| Garak | **CHALLENGER / LIVE-MODEL VULNERABILITY SCAN** | isolated authorized target only |
| ToolSandbox / AgentDojo-style methods | **CHALLENGER / BEHAVIORAL TOOL-USE EVALUATION** | unique state-transition seam; no organization truth |
| Hypothesis | **IMPLEMENTED / TEST-ONLY PROPERTY PILOT** | Wave E3; no production runtime role |
| first-party mutation-strength gate | **IMPLEMENTED / INCUMBENT MUTATION PROOF** | Wave E4; bounded selected mutants |
| mutmut | **HOLD_WITH_TRIGGER** | Linux/CI mutation campaign materially exceeds current first-party gate |
| deterministic fault injection | **INCUMBENT ENGINEERING APPROACH** | first-party provider/storage/network failure assurance |
| DeepEval | **HOLD_WITH_TRIGGER** | RAG/agent metrics gap remains after Promptfoo + Inspect |
| Ragas | **HOLD_WITH_TRIGGER** | retrieval-quality metric gap becomes measured and cannot be covered by current evidence/source evaluation |
| Microsoft PyRIT | **HOLD_WITH_TRIGGER** | need multi-turn red-team orchestration beyond Promptfoo/Inspect/Garak |
| DeepTeam | **HOLD_WITH_TRIGGER** | current adversarial trio demonstrably misses material attack classes |
| FuzzyAI-class tooling | **HOLD_WITH_TRIGGER** | deterministic/property/mutation tests miss a reproducible fuzzing class |
| Atheris/equivalent | **HOLD_WITH_TRIGGER** | parser/contract fuzzing gap is demonstrated |

```text
evaluation score != professional correctness
live-model adversarial proof != operational Red Team authority
```

### 4.1 AI runtime / Model Router

The canonical architecture already defines a capability-qualified **Model Router**. This Radar seam restores that architecture to the active technology-evaluation view without claiming that adaptive routing is implemented.

| Capability | Current repository truth | Deferred direction |
|---|---|---|
| deterministic execution | current no-provider baseline; governed templates remain available when no LLM provider is configured | preserve as the low-risk/repeatable execution path |
| hosted/frontier provider adapters | DeepSeek, Gemini and Moonshot are implemented in `LLMProviderFactory` | capability eligibility and adaptive selection remain future work |
| small-local execution | `ollama>=0.4` is an optional dependency; `ollama_base_url` and `default_local_model` settings exist | **adapter not implemented** in `LLMProviderFactory`; no accepted local-model benchmark baseline yet |
| capability-qualified Model Router | architecture-defined in `GLOBAL_MOBILITY_AIOS_COMBINED_ARCHITECTURE_V1_1.md` | adaptive runtime routing remains roadmap/N-owned and must be benchmark-qualified |
| storage-streamed / memory-elastic large-local inference | no runtime, package, weights or scheduling adoption | **HOLD_WITH_TRIGGER** |
| `kimi-k3-in-c` class implementation | no repository runtime role | **REFERENCE only** for the held capability; do not install/adopt |

The held deep-local capability may become a TRIAL only when a real AIOS workload is simultaneously:

- prohibited from cloud execution;
- beyond an **accepted and benchmarked small-local baseline**;
- tolerant of offline-scale latency;
- economically justified after storage, energy, hardware and operational cost;
- license/provenance compatible;
- benchmarkable against existing governed providers without bypassing Evidence, Truth, risk, authority or audit controls.

Permanent boundary:

```text
MODEL ROUTER != AUTHORITY
LOCAL MODEL != TRUTH SOURCE
PROVIDER IDENTITY != PERMISSION
REFERENCE IMPLEMENTATION != RUNTIME ADOPTION
```

No separate "Intelligence Router" abstraction is introduced; that would duplicate the canonical Model Router seam.

## 5. Observability, tracing and experiment analysis

| Candidate | V1.3.8 state | Trigger / boundary |
|---|---|---|
| OpenTelemetry | **INCUMBENT / FOUNDATION / PILOT COMPLETE** | vendor-neutral engineering telemetry |
| Arize Phoenix | **CHALLENGER / SELF-HOSTED OBSERVABILITY** | only if a platform-level tracing/eval gap is demonstrated |
| Langfuse | **HOLD_WITH_TRIGGER** | Phoenix proves unsuitable for the measured platform gap |
| OpenInference conventions | **HOLD_WITH_TRIGGER** | semantic-convention gap remains beyond current OTel instrumentation |
| OpenLLMetry | **HOLD_WITH_TRIGGER** | OTel instrumentation coverage is proven insufficient |
| Opik / equivalent | **HOLD_WITH_TRIGGER** | experiment-management workflow becomes a real product/engineering need |

No observability platform becomes canonical `OrganizationActivity`.

## 6. Application and API security

### SAST

| Candidate | V1.3.8 state |
|---|---|
| Semgrep | **INCUMBENT / SAST** |
| GitHub CodeQL | **CHALLENGER / SEMANTIC SAST** |
| Bandit | **HOLD_WITH_TRIGGER — cheap Python baseline needed before/without Semgrep** |

### DAST / API testing

| Candidate | V1.3.8 state |
|---|---|
| OWASP ZAP | **INCUMBENT / AUTHORIZED DAST** |
| Schemathesis | **CHALLENGER / OPENAPI PROPERTY + NEGATIVE TESTING** |
| Nuclei | **HOLD_WITH_TRIGGER — template-driven exposure scanning becomes a distinct need** |
| OWASP API Security methodology | **REFERENCE TAXONOMY** |

## 7. Dependency, container, secret and supply-chain security

| Candidate | V1.3.8 state | Trigger / boundary |
|---|---|---|
| Trivy | **INCUMBENT / DEPENDENCY + CONTAINER + AUXILIARY IaC** | broad baseline |
| OSV-Scanner | **CHALLENGER / DEPENDENCY INTELLIGENCE** | compare vulnerability intelligence/noise against Trivy |
| Syft | **HOLD_WITH_TRIGGER** | Trivy SBOM generation insufficient |
| Grype | **HOLD_WITH_TRIGGER** | Trivy vulnerability matching insufficient |
| Gitleaks | **INCUMBENT / REPOSITORY SECRET SCANNING** | repository history/worktree scope only |
| TruffleHog | **CHALLENGER / VERIFIED-SECRET DISCOVERY** | compare only if Gitleaks misses material verified secrets |
| OpenSSF Scorecard | **HOLD_WITH_TRIGGER** | upstream project-risk signals become an explicit dependency gate |
| SLSA | **TARGET_CONTROL** | provenance maturity target, not a runtime tool |
| Sigstore/cosign | **HOLD_WITH_TRIGGER** | artifact signing/verifying becomes a release requirement |
| in-toto | **HOLD_WITH_TRIGGER** | supply-chain step attestation becomes required |
| GUAC | **WATCH** | SBOM/provenance volume justifies graph analysis |

SecretsPort/OpenBao remains the runtime secret-reference boundary. Scanners complement it; they do not replace it.

## 8. Infrastructure and IaC assurance

| Candidate | V1.3.8 state |
|---|---|
| Checkov | **INCUMBENT / DEDICATED IaC BENCHMARK** |
| KICS | **CHALLENGER / IaC BENCHMARK** |
| Kubescape | **WATCH — Kubernetes deployment trigger only** |
| kube-bench | **WATCH — Kubernetes/CIS trigger only** |

Do not add Kubernetes tooling without a real Kubernetes deployment target.

## 9. Sandbox and isolated execution

| Candidate | V1.3.8 state |
|---|---|
| Microsandbox | **INCUMBENT / PRIMARY FUTURE SANDBOX** |
| E2B | **CHALLENGER / MANAGED SANDBOX** |
| Daytona-class sandbox | **HOLD_WITH_TRIGGER — managed workspace sandbox becomes a distinct need** |
| Nightona | **WATCH — Daytona/self-hosted maturity or licensing trigger** |

`SANDBOX ISOLATION != EXECUTION AUTHORITY`.

## 10. Authorization and policy engines

The previous lane looked like four simultaneous challengers. V1.3.8 splits it into two real seams.

### Relationship authorization

| Candidate | V1.3.8 state |
|---|---|
| OpenFGA | **INCUMBENT R3 RELATIONSHIP-AUTH BENCHMARK** |
| SpiceDB | **CHALLENGER / RELATIONSHIP-AUTH ALTERNATIVE** |

### Contextual policy evaluation / policy language

| Candidate | V1.3.8 state |
|---|---|
| OPA/Rego | **INCUMBENT R3 CONTEXTUAL POLICY BENCHMARK** |
| Cedar | **CHALLENGER / TYPED POLICY-LANGUAGE ALTERNATIVE** |
| Kyverno | **WATCH — Kubernetes policy trigger only** |

No external relationship or policy engine becomes constitutional truth or grants authority by itself.

## 11. Context, retrieval, memory and durable workflow

| Candidate | V1.3.8 state | Boundary |
|---|---|---|
| Qdrant | **INCUMBENT / SEMANTIC RETRIEVAL** | current platform capability |
| pgvector | **CHALLENGER / RETRIEVAL** | simpler Postgres-native alternative |
| LLMLingua-2 | **SELECTED BOUNDED COMPRESSION PILOT** | protected R3–R5 context remains zero-semantic-compression by default |
| Mem0 | **CHALLENGER / L1 CONTINUITY MEMORY** | MEMORY != EVIDENCE |
| OpenViking | **DONOR_ONLY / CONTEXT RESEARCH** | no canonical memory role |
| LangGraph | **DONOR_ONLY / EXECUTION-GRAPH RESEARCH** | cannot become WorkItem truth |
| Agno / AgentOS | **DONOR_ONLY / AGENT-RUNTIME RESEARCH** | cannot replace AIOS control plane |
| Temporal | **HOLD_WITH_TRIGGER / DURABLE-WORKFLOW CHALLENGER** | trigger: native WorkItem/runtime cannot meet measured multi-day/recovery requirements |
| Pydantic AI | **HOLD_WITH_TRIGGER** | agent-programming abstraction gap beyond current controlled-agent stack |
| DSPy | **HOLD_WITH_TRIGGER** | measured prompt/program optimization need |

## 12. Document, privacy and source intelligence

These candidates occupy distinct seams and remain intentionally separate.

| Candidate | V1.3.8 state |
|---|---|
| ClamAV | **PILOT COMPLETE / TRIAL-ELIGIBLE** |
| Docling | **PILOT IN PROGRESS** |
| Presidio | **QUEUED PILOT** |
| urlwatch | **QUEUED PILOT** |
| EU DSS | **HOLD_WITH_TRIGGER — digital-signature/document-trust requirement becomes material** |

## 13. Frontend, human interaction and design tooling

| Candidate | V1.3.8 state | Boundary |
|---|---|---|
| CopilotKit / AG-UI | **CHALLENGER / POST-L M PILOT CANDIDATE** | interaction layer only; AIOS APIs/governance authorize commands |
| **WebGPU** | **ADOPT / M LIVING ORGANIZATION RENDERING SUBSTRATE** | multi-surface rendering/compute infrastructure; scene state is projection, never authority |
| **Three.js WebGPU/compute layer** | **ADOPT / M SCENE + INTERACTION SUBSTRATE; M.4.0 COMPLETE / PASS** | `three@0.185.1`; exact-head browser mount, actual backend, picking and Structured fallback proven at `e6640755...` |
| **GPU flow/fluid simulation** | **TRIAL / M.7.4 ITERATION 1 TECHNICAL PASS / BENCHMARK PENDING** | default-off derived field is implemented and technically proven; promotion still requires product-value evidence against the maintained Structured FLOW baseline |
| **Reaction-diffusion fields** | **EXPERIMENT / M.9 ENVIRONMENTAL-MEMORY RESEARCH** | high interpretation risk; must establish explainable mapping and graduate to TRIAL |
| **Cognitive Ecology / Organica** | **POST-M OPTIONAL RESEARCH** | not an M deliverable; may return only if implemented views expose a concrete unmet task |
| Storybook | **HOLD_WITH_TRIGGER** | M component/design-system proof demonstrates a workbench need |
| Penpot | **PREFERRED DESIGN ENVIRONMENT / NOT ACCEPTANCE DEPENDENCY** | design tooling only |

L is sealed and M is in progress. WebGPU/Three.js are adopted infrastructure. M.7.1–M.7.4 implementation slices are sealed; the M.7.4 GPU FLOW field remains a TRIAL / NOT PROMOTED / BENCHMARK PENDING. Reaction-diffusion remains an EXPERIMENT and Cognitive Ecology/Organica remains Post-M optional research.

## 14. Cybersecurity skill and Red Team programme

| Capability | V1.3.8 state |
|---|---|
| community cybersecurity skill corpus | **DONOR_ONLY / RESEARCH** |
| defensive tranche | **POST-L WHERE USEFUL** |
| Cybersecurity Skill Registry | **FUTURE GOVERNED PILOT** |
| operational offensive Red Team agents | **NOT IMPLEMENTED** |
| arbitrary production-target attack authority | **REJECTED** |

`SKILL KNOWLEDGE != EXECUTION AUTHORITY`.

## 15. Existing foundations that must not be rediscovered as missing

```text
OpenTelemetry foundation                  exists
Promptfoo pilot                           exists
backup + isolated restore proof           exists
ClamAV pilot                              exists
SecretsPort                               exists
non-production OpenBao adapter            exists
Wave E2 adversarial contract gate         implemented
Wave E3 Hypothesis property suite         implemented
Wave E4 mutation-strength gate            implemented
Docling pilot                             in progress
Qdrant platform capability                exists
Track B runtime-economics projection      exists
Track B durable activity lineage          exists
collaboration/coordination foundation      exists across current AIOS surfaces
blind Austria professional-review handoff implemented / proof still pending
```

## 16. Candidate-entry and persistence rules

Before adding any new Radar candidate:

```text
1. Name the exact AIOS seam.
2. Name the incumbent for that seam.
3. Explain the measured gap the incumbent cannot close.
4. If the candidate is a challenger, define a falsifiable benchmark.
5. Check repository dependencies/imports/config/tests/commits for existing work.
6. Check ROADMAP and the adoption ledger.
7. Reject the candidate if no unique seam or material challenger value exists.
```

Persistence rule:

> **No candidate may remain generic RESEARCH across two Radar revisions.**

By the next revision it must have a trigger-bound status, a bounded pilot, incumbent/challenger designation, donor/reference/control classification, WATCH state, or rejection.

## 17. R3 interpretation

The R3 authority/security branches are research/benchmark lanes, not justification for indefinite expansion.

Verified R3 branch preservation truth:

```text
radar/r3-authority   acd917670630abdfebe20f3f687a310f67d22b3f
radar/r3-security    d908a8c7ccde463ae0dec097211562e7ef8e86ca
radar/r3-interop     aad377e401b10a95b11440442831290c5c60a9f2
```

At the start of V1.3.8 consolidation, interop was not present on origin. It was subsequently pushed from the local worktree and is now recoverable remotely. That preservation does not merge the R3 lane into V12 and does not promote any Radar candidate.

Authority R3 must converge on its closure evidence/runbook rather than continuously adding policy engines. Security R3 should execute its defined external-tool shootout or record explicit tool/environment blockers. Interop recoverability risk is closed by the remote branch push; integration/adoption remains explicitly unscheduled.

R3 evidence does not seal L and must not displace the independent professional Austria review.

## 18. Scheduling truth

```text
Technology Radar V1.3.8                  ACTIVE CANONICAL / CONSOLIDATED
Radar-caused runtime adoption             NONE
scatter-audit recommendation              APPLIED
generic duplicate research statuses       REMOVED / TRIGGER-BOUND
R3 branch merge into V12                  NONE
professional Austria review               COMPLETE under sealed L record
final L exact-evidence-head proof          COMPLETE
L                                          COMPLETE / PASS / SEALED
M                                          IN PROGRESS — M.7.4 ITERATION 1 TECHNICAL PASS; GPU FLOW TRIAL BENCHMARK PENDING
N                                          NOT STARTED
```

ROADMAP remains the implementation scheduler. The active M state is M.7.4 technical closure with GPU FLOW product-value benchmark evidence still pending; Radar work must not displace the roadmap or convert held/reference technologies into implementation work.
