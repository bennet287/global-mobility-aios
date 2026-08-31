# Global Mobility AIOS — Technology Radar V1.3.7

**Date:** 2026-08-31  
**Status:** ACTIVE CANONICAL RADAR REVISION — CONSOLIDATED AGGRESSIVE FRONTIER  
**Supersedes for active radar direction:** `TECHNOLOGY_RADAR_V1_3_6.md`  
**Inherited baseline:** all V1.3.6 classifications remain active unless explicitly overridden here  
**Scheduling authority:** `docs/ROADMAP.md`  
**Adoption truth index:** `docs/TECHNOLOGY_ADOPTION_LEDGER.md`  
**Current product milestone:** L — Live Organization — IMPLEMENTED / ACCEPTANCE PENDING  
**M milestone:** NOT STARTED

> **Aggressive Radar. Conservative production authority.**

> **Research broadly. Benchmark ruthlessly. Adopt narrowly.**

> **External infrastructure provides capability. AIOS owns meaning, truth and authority.**

V1.3.7 completes the current broad Technology Radar pass before further product-milestone work. “Complete” means the major technology capability lanes relevant to the present AIOS architecture now have explicit incumbents, challengers or research targets. It does **not** mean the Radar is permanently closed: new material technologies may still enter through evidence-based scouting.

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

Radar presence is not dependency presence. Benchmark success is not adoption. External state must not become canonical organization, WorkItem, Evidence, authority, policy, memory or Board truth.

## 2. AI evaluation, benchmark and adversarial lane

| Candidate | Radar state | Primary question |
|---|---|---|
| Promptfoo | **PILOT COMPLETE / TRIAL-ELIGIBLE — EXPANSION CANDIDATE** | can the existing pilot become the CI adversarial regression spine? |
| Inspect AI | **PRIORITY RESEARCH / BENCHMARK CANDIDATE** | does rigorous sandboxed multi-step evaluation add evidence quality beyond current harnesses? |
| DeepEval | **RESEARCH / BENCHMARK CANDIDATE** | do agent/task/RAG metrics close a measured evaluation gap? |
| Ragas | **RESEARCH / RETRIEVAL-METRIC BENCHMARK** | can retrieval quality be measured without confusing metrics with Evidence truth? |
| Garak | **RESEARCH / BOUNDED LIVE-MODEL PILOT CANDIDATE** | broad vulnerability scanning in an isolated authorized target |
| Microsoft PyRIT | **RESEARCH / RED-TEAM-LAB CANDIDATE** | multi-turn orchestrated adversarial evaluation under `AdversarialEngagement` |
| DeepTeam | **RESEARCH / RED-TEAM BENCHMARK CANDIDATE** | compare vulnerability/attack breadth and CI ergonomics against Promptfoo/Garak/PyRIT |
| FuzzyAI-class LLM fuzzing | **RESEARCH / SPECIALIZED FUZZ BENCHMARK** | whether automated adversarial fuzzing finds failures deterministic suites miss |
| ToolSandbox / AgentDojo-style evaluation | **PRIORITY RESEARCH / BEHAVIORAL BENCHMARK METHODS** | evaluate real tool-use state transitions and behavioral evidence, not only verbal answers |
| Hypothesis | **BENCHMARK / HIGH-PRIORITY ENGINEERING CANDIDATE** | property/invariant proof on governance/evaluation seams |
| mutmut/equivalent | **RESEARCH / BOUNDED PILOT CANDIDATE** | measure whether tests kill meaningful logic mutations |
| Atheris/equivalent | **RESEARCH / BOUNDED FUZZ PILOT CANDIDATE** | malformed parser/contract/input resilience |
| deterministic fault injection | **PRIORITY ENGINEERING APPROACH** | first-party provider/storage/network failure assurance before chaos-platform adoption |

Evaluation ladder remains:

```text
unit → deterministic adversarial → property → mutation → fuzz → fault injection
→ real provider → fresh source → provider disagreement → poisoned context
→ authorization/replay/isolation attacks → concurrency → professional review
→ isolated Red Team/purple-team → continuous regression
```

## 3. AI observability, tracing and experiment analysis

| Candidate | Radar state | Boundary |
|---|---|---|
| OpenTelemetry | **PILOT COMPLETE / TRIAL-ELIGIBLE — FOUNDATION** | vendor-neutral engineering telemetry only |
| OpenInference conventions | **RESEARCH / INTEROPERABILITY BENCHMARK** | evaluate LLM/agent semantic conventions without creating business truth |
| OpenLLMetry | **RESEARCH / INSTRUMENTATION DONOR CANDIDATE** | compare instrumentation coverage with current OTel seams |
| Langfuse | **RESEARCH / PILOT CANDIDATE** | only for measured prompt/run/eval/cost analysis gap |
| Arize Phoenix | **PRIORITY RESEARCH / LANGFUSE CHALLENGER** | compare self-hosted tracing/evals, OpenInference fit, privacy and exportability |
| Opik / equivalent OSS eval-observability platform | **RESEARCH / BENCHMARK CANDIDATE** | benchmark only if platform-level experiment management is needed |

No observability platform may become canonical OrganizationActivity.

## 4. Application, API and software security

| Candidate | Radar state | Intended use |
|---|---|---|
| Semgrep | **PRIORITY RESEARCH / PILOT CANDIDATE** | SAST + AIOS-specific security rules |
| GitHub CodeQL | **PRIORITY RESEARCH / BENCHMARK CANDIDATE** | semantic analysis challenger/complement |
| Bandit | **RESEARCH / LIGHTWEIGHT PYTHON BASELINE CANDIDATE** | cheap Python security lint baseline |
| OWASP ZAP | **PRIORITY RESEARCH / DAST PILOT CANDIDATE** | authorized test-environment web/API dynamic testing |
| Schemathesis | **PRIORITY RESEARCH / API PROPERTY-TEST CANDIDATE** | OpenAPI-driven negative/property testing |
| Nuclei | **RESEARCH / AUTHORIZED SCANNER CANDIDATE** | template-driven service exposure checks in controlled targets |
| OWASP API Security methodology | **PRIORITY RESEARCH / CONTINUOUS TEST TARGET** | API assurance taxonomy and regression coverage |

## 5. Dependency, container, secret and supply-chain security

| Candidate | Radar state | Intended use |
|---|---|---|
| Trivy | **PRIORITY RESEARCH / PILOT CANDIDATE** | dependency/container/IaC scanning |
| OSV-Scanner | **PRIORITY RESEARCH / DEPENDENCY CHALLENGER** | vulnerability intelligence against manifests/lockfiles/SBOM |
| Syft | **RESEARCH / PILOT CANDIDATE** | SBOM generation |
| Grype | **RESEARCH / BENCHMARK CANDIDATE** | SBOM/package vulnerability matching |
| Gitleaks | **PRIORITY RESEARCH / PILOT CANDIDATE** | repository secret scanning |
| TruffleHog | **RESEARCH / SECRET-SCANNER CHALLENGER** | verified-secret discovery comparison |
| OpenSSF Scorecard | **PRIORITY RESEARCH / DEPENDENCY-GOVERNANCE CANDIDATE** | upstream project risk signals |
| SLSA | **RESEARCH / TARGET CONTROL** | provenance maturity model |
| Sigstore/cosign | **RESEARCH / PILOT CANDIDATE** | artifact signing and verification |
| in-toto | **RESEARCH / PROVENANCE CHAIN CANDIDATE** | supply-chain step attestations |
| GUAC | **WATCH / SUPPLY-CHAIN GRAPH CANDIDATE** | only if SBOM/provenance volume creates graph-analysis need |

SecretsPort/OpenBao remains the runtime-secret boundary; scanners complement it rather than replace it.

## 6. Infrastructure, container and IaC assurance

| Candidate | Radar state | Trigger |
|---|---|---|
| Checkov | **RESEARCH / IAC BENCHMARK CANDIDATE** | when deployment IaC becomes material |
| KICS | **RESEARCH / IAC CHALLENGER** | compare with Checkov/Trivy IaC coverage |
| Kubescape | **WATCH / KUBERNETES SECURITY CANDIDATE** | only if Kubernetes becomes a real deployment target |
| kube-bench | **WATCH / CIS KUBERNETES CANDIDATE** | Kubernetes deployment only |

Do not add Kubernetes tooling merely because it is mature commodity infrastructure; deployment reality controls scheduling.

## 7. Sandbox and isolated execution

| Candidate | Radar state | Boundary |
|---|---|---|
| Microsandbox | **EXPLORE / PRIMARY SANDBOX PROVIDER CANDIDATE** | post-L bounded engineering/security execution |
| E2B | **RESEARCH / MANAGED SANDBOX CHALLENGER** | benchmark isolation, lifecycle, network controls, cost and exit path |
| Daytona-class sandbox | **RESEARCH / MANAGED WORKSPACE CHALLENGER** | evaluate only against a concrete developer/agent execution need; verify current licensing/hosting model at pilot time |
| Nightona | **WATCH / SELF-HOSTED DAYTONA-DERIVED CANDIDATE** | licensing/community maturity must be rechecked before any pilot |

`SANDBOX ISOLATION != EXECUTION AUTHORITY` remains permanent.

## 8. Authorization and policy engines

| Candidate | Radar state | Boundary |
|---|---|---|
| OpenFGA | **DEFERRED PILOT / RELATIONSHIP-AUTH CHALLENGER** | only if native relationship authorization becomes measurably insufficient |
| OPA/Rego | **RESEARCH / POLICY-ENGINE CANDIDATE** | optional engine behind future AIOS-owned policy-evaluation port only |
| Cedar | **RESEARCH / POLICY-LANGUAGE CHALLENGER** | benchmark expressive safety/verification only if policy complexity warrants external engine |
| Kyverno | **WATCH / KUBERNETES POLICY CANDIDATE** | deployment-specific; never AIOS organizational authority |

No external policy store becomes constitutional truth.

## 9. Context, retrieval, memory and durable workflow

Existing classifications remain authoritative:

- Qdrant — current semantic-retrieval platform / benchmark baseline;
- pgvector — benchmark challenger;
- LLMLingua-2 — selected primary compression pilot;
- Mem0 — explore L1 continuity provider only;
- OpenViking — research/context-database donor only;
- LangGraph — research execution-graph donor only;
- Agno/AgentOS — assess/donor candidate only;
- Temporal — deferred/gap-triggered durable-workflow candidate;
- Pydantic AI — research/pilot candidate;
- DSPy — research optimization/programming candidate.

No memory, graph or workflow engine becomes Evidence or organization truth.

## 10. Document, privacy and source intelligence

| Candidate | Radar state | Current truth |
|---|---|---|
| ClamAV | **PILOT COMPLETE / TRIAL-ELIGIBLE** | existing malware scan/quarantine pilot; do not restart |
| Docling | **PILOT IN PROGRESS** | continue existing document-normalization work only |
| Presidio | **QUEUED PILOT** | privacy/PII processing candidate |
| urlwatch | **QUEUED PILOT** | official-source change-monitoring candidate |
| EU DSS | **RESEARCH** | digital-signature/document-trust candidate |

## 11. Frontend, human interaction and agent UI

| Candidate | Radar state | Boundary |
|---|---|---|
| CopilotKit / AG-UI | **EXPLORE / POST-L M PILOT CANDIDATE** | interaction protocol/library only; AIOS APIs authorize commands |
| Storybook | **RESEARCH / COMPONENT-WORKBENCH CANDIDATE** | adopt only if M design-system/component proof benefits |
| Penpot | **PREFERRED DESIGN ENVIRONMENT / NOT ACCEPTANCE DEPENDENCY** | design tooling does not become product truth |

The Cockpit remains the top-level product surface; Board Room remains a module inside it.

## 12. Cybersecurity skill and Red Team programme

The V1.3.4+ governed cybersecurity donor and Red Team architecture remains active.

- community cybersecurity skill corpus — **RESEARCH / DONOR CANDIDATE**;
- defensive tranche — prioritize after current L acceptance where useful;
- Cybersecurity Skill Registry — future governed pilot;
- operational offensive Red Team agents — **NOT IMPLEMENTED**;
- arbitrary production-target attack authority — **REJECTED**;
- Promptfoo/Garak/PyRIT/DeepTeam/FuzzyAI-class tools — evaluators only under bounded target authorization.

`SKILL KNOWLEDGE != EXECUTION AUTHORITY`.

## 13. Current incumbents that must not be rediscovered as missing

```text
OpenTelemetry foundation                  exists
Promptfoo pilot                           exists
backup + isolated restore proof           exists
ClamAV pilot                              exists
SecretsPort                               exists
non-production OpenBao adapter            exists
Wave E2 adversarial contract gate         exists
Docling pilot                             in progress
Qdrant platform capability                exists
```

Future sessions must inspect dependencies/imports/config/tests/commits before implementing any Radar item.

## 14. Promotion and rejection rubric

A candidate advances only when it has:

1. a demonstrated product/security/operability gap;
2. comparison against current native capability and incumbent candidates;
3. a clear AIOS-owned boundary;
4. acceptable license, privacy, data residency, operational and exit posture;
5. a bounded benchmark with falsifiable success criteria;
6. no second truth/control plane unless explicitly architected and subordinate;
7. proof proportional to the claim;
8. ROADMAP, CHANGELOG and adoption-ledger reconciliation.

Reject/defer a candidate when overlap, lock-in, authority ambiguity, operational burden or marginal benefit exceeds measured value.

## 15. Radar-completion rule

With V1.3.7, the current broad Radar inventory is considered **COMPLETE FOR THIS PRODUCT HORIZON**.

This means:

```text
major relevant capability lanes have explicit coverage
known incumbents and challengers are visible
security/evaluation depth is first-class
anti-duplication boundaries are explicit
future additions require a material new capability or materially better challenger
```

It does **not** authorize implementation of the backlog. ROADMAP scheduling remains authoritative.

## 16. Scheduling truth after Radar completion

```text
Technology Radar V1.3.7                    COMPLETE / ACTIVE CANONICAL RADAR
runtime adoption caused by V1.3.7          NONE
Wave E2 deterministic adversarial gate     IMPLEMENTED / LOCAL-CI PROOF PENDING
professional Austria review                PENDING
final exact-current-head technical proof   PENDING
L overall                                  IMPLEMENTED / ACCEPTANCE PENDING
M                                          NOT STARTED
```

The next product work may proceed only after repository reconciliation for this Radar revision. The Radar itself should now return to continuous scouting mode rather than expanding indefinitely before L acceptance.
