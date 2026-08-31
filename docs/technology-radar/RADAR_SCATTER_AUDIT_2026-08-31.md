# Global Mobility AIOS — Technology Radar Scatter and Duplication Audit

**Date:** 2026-08-31  
**Radar revision audited:** `docs/TECHNOLOGY_RADAR_V1_3_7.md`  
**Status:** COMPLETE / ACTION REQUIRED  
**Purpose:** Identify overlap, reduce decision debt, and prevent parallel work on functionally identical seams.

> **V1.3.7 completed the broad inventory. This audit begins the consolidation.**

---

## 1. Executive finding

The Radar is intellectually sound but operationally scattered. Across 12 lanes there are **~50 candidates**, many of which solve overlapping problems. Without explicit consolidation, future sessions will rediscover the same seams, create duplicate pilots, and accumulate evaluation debt.

The correct posture after inventory is not to keep every candidate warm. It is to pick **one incumbent and one challenger per seam**, reject the rest with a trigger, and move on.

---

## 2. Consolidation principles

```text
1. One incumbent per seam
2. One challenger per seam
3. Everything else: REJECT or HOLD_WITH_TRIGGER
4. A challenger only survives if it materially differs from the incumbent
5. "Research" is not a permanent status
6. No new candidate enters without a specific AIOS gap it closes
```

---

## 3. Lane-by-lane consolidation

### 3.1 AI evaluation, benchmark and adversarial lane

| Current candidates | Proposed disposition | Rationale |
|--------------------|----------------------|-----------|
| **Promptfoo** | **INCUMBENT / CI ADVERSARIAL SPINE** | Already has a pilot. Closest to CI regression. |
| **Inspect AI** | **CHALLENGER / STRUCTURED EVALUATION** | Strong multi-step dataset/scorer model. Benchmark against Promptfoo. |
| **Garak** | **CHALLENGER / LIVE-MODEL VULNERABILITY SCAN** | Specialized scanner; keep isolated. |
| DeepEval | **HOLD** — trigger: need RAG/agent metrics beyond Promptfoo+Inspect | Overlaps with Inspect/Promptfoo evaluation. |
| Ragas | **HOLD** — trigger: RAG quality metrics become a measured gap | Narrower than DeepEval; overlaps with existing source verification. |
| Microsoft PyRIT | **HOLD** — trigger: need multi-turn orchestrated red-team automation | Overlaps with Promptfoo red-team + Inspect multi-step. |
| DeepTeam | **HOLD** — trigger: Promptfoo/Inspect/Garak evaluation breadth is proven insufficient | Generic red-team benchmark; no unique seam yet. |
| FuzzyAI-class LLM fuzzing | **HOLD** — trigger: deterministic suites miss parser/contract failures | Specialized fuzz; not a current gap. |
| ToolSandbox / AgentDojo | **PRIORITY RESEARCH / BEHAVIORAL BENCHMARK** | Unique: real tool-use state transitions. Keep as distinct seam. |
| Hypothesis | **BOUNDED PILOT ADOPTED** | Already implemented in Wave E3. |
| mutation testing / mutmut | **FIRST-PARTY PILOT ADOPTED / EXTERNAL DEFERRED** | Already implemented in Wave E4. |
| Atheris/equivalent | **HOLD** — trigger: parser/contract fuzzing gap demonstrated | Similar to FuzzyAI; consolidate fuzz seam later. |
| deterministic fault injection | **PRIORITY ENGINEERING APPROACH** | Distinct: first-party failure assurance. Keep. |

**Decision:** Reduce live adversarial lane to Promptfoo + Inspect + Garak + ToolSandbox. Others HOLD.

### 3.2 AI observability, tracing and experiment analysis

| Candidates | Proposed disposition | Rationale |
|------------|----------------------|-----------|
| **OpenTelemetry** | **INCUMBENT / FOUNDATION** | Already piloted; vendor-neutral. |
| **Arize Phoenix** | **CHALLENGER / SELF-HOSTED OBSERVABILITY** | Compare against Langfuse if an observability platform gap is proven. |
| Langfuse | **HOLD** — trigger: Phoenix does not fit | One challenger is enough. |
| OpenInference conventions | **HOLD** — trigger: need LLM semantic conventions beyond OTel | Niche; can be absorbed into OTel/instrumentation review. |
| OpenLLMetry | **HOLD** — trigger: OTel instrumentation coverage gap demonstrated | Donor-style instrumentation library. |
| Opik / equivalent | **HOLD** — trigger: platform-level experiment management needed | Overlaps with Phoenix/Langfuse. |

**Decision:** Observability = OpenTelemetry + Phoenix challenger. Rest HOLD.

### 3.3 Application, API and software security

| Candidates | Proposed disposition | Rationale |
|------------|----------------------|-----------|
| **Semgrep** | **INCUMBENT / SAST** | Fast, AIOS-specific rules possible. |
| **GitHub CodeQL** | **CHALLENGER / SEMANTIC SAST** | Deeper semantic analysis; compare against Semgrep. |
| Bandit | **HOLD** — trigger: need cheap Python baseline before Semgrep | Lightweight but overlaps with Semgrep Python rules. |
| **OWASP ZAP** | **INCUMBENT / AUTHORIZED DAST** | Distinct seam from SAST. |
| **Schemathesis** | **CHALLENGER / API PROPERTY TESTING** | OpenAPI-driven; distinct from ZAP. |
| Nuclei | **HOLD** — trigger: need template-driven exposure scanning | Overlaps with ZAP for AIOS scope. |
| OWASP API Security methodology | **REFERENCE TAXONOMY** | Not a tool; keep as coverage checklist. |

**Decision:** SAST = Semgrep + CodeQL. DAST/API = ZAP + Schemathesis. Rest HOLD.

### 3.4 Dependency, container, secret and supply-chain security

| Candidates | Proposed disposition | Rationale |
|------------|----------------------|-----------|
| **Trivy** | **INCUMBENT / DEPENDENCY + CONTAINER + IaC** | Broad coverage; already used elsewhere. |
| **OSV-Scanner** | **CHALLENGER / DEPENDENCY INTELLIGENCE** | Google-backed vulnerability data; compare against Trivy dependency scanning. |
| Syft | **HOLD** — trigger: Trivy SBOM generation insufficient | SBOM generation is a feature, not a separate seam yet. |
| Grype | **HOLD** — trigger: Trivy vulnerability matching insufficient | Anchore scanner; overlaps with Trivy. |
| **Gitleaks** | **INCUMBENT / REPOSITORY SECRET SCANNING** | Fast, widely used. |
| TruffleHog | **CHALLENGER / VERIFIED-SECRET DISCOVERY** | Can verify secrets; compare if Gitleaks misses real leaks. |
| OpenSSF Scorecard | **HOLD** — trigger: upstream risk signals become a gate | Governance signal; not operational security. |
| SLSA | **TARGET CONTROL** | Maturity model; not a tool. Keep as aspiration. |
| Sigstore/cosign | **HOLD** — trigger: artifact signing becomes required | Not a current gap. |
| in-toto | **HOLD** — trigger: provenance chain attestation needed | Niche supply-chain provenance. |
| GUAC | **WATCH** — trigger: SBOM/provenance volume justifies graph analysis | Far future. |

**Decision:** Dependency/container = Trivy + OSV-Scanner. Secrets = Gitleaks + TruffleHog. Rest HOLD/WATCH.

### 3.5 Infrastructure, container and IaC assurance

| Candidates | Proposed disposition | Rationale |
|------------|----------------------|-----------|
| **Checkov** | **INCUMBENT / IaC BENCHMARK** | Broad IaC policy coverage. |
| **KICS** | **CHALLENGER / IaC BENCHMARK** | Compare coverage and noise against Checkov. |
| Kubescape | **WATCH** — trigger: Kubernetes becomes real deployment target | Irrelevant without K8s. |
| kube-bench | **WATCH** — trigger: Kubernetes becomes real deployment target | Irrelevant without K8s. |

**Decision:** IaC = Checkov + KICS. K8s tooling WATCH.

### 3.6 Sandbox and isolated execution

| Candidates | Proposed disposition | Rationale |
|------------|----------------------|-----------|
| **Microsandbox** | **INCUMBENT / PRIMARY SANDBOX** | Lightweight, self-hostable. |
| **E2B** | **CHALLENGER / MANAGED SANDBOX** | Compare lifecycle/network/cost. |
| Daytona-class sandbox | **HOLD** — trigger: need managed workspace sandbox specifically | Overlaps with E2B for agent execution. |
| Nightona | **WATCH** — trigger: Daytona licensing/hosting fails | Too immature. |

**Decision:** Sandbox = Microsandbox + E2B. Rest HOLD/WATCH.

### 3.7 Authorization and policy engines

| Candidates | Proposed disposition | Rationale |
|------------|----------------------|-----------|
| **OpenFGA** | **INCUMBENT / RELATIONSHIP-AUTH CHALLENGER** | Already deep R3 work. |
| **OPA/Rego** | **CHALLENGER / POLICY ENGINE** | Context-heavy policies; compare against OpenFGA. |
| **Cedar** | **CHALLENGER / POLICY LANGUAGE** | Strong verification story; compare expressiveness. |
| SpiceDB | **CHALLENGER / RELATIONSHIP-ENGINE ALTERNATIVE** | Already in R3 authority as OpenFGA challenger. |
| Kyverno | **WATCH** — trigger: Kubernetes policy needed | Deployment-specific. |

**Decision:** Auth = OpenFGA + OPA + Cedar + SpiceDB. This is the one lane where three challengers are justified because each represents a different approach (relationship, context-policy, verified-language). Kyverno WATCH.

### 3.8 Context, retrieval, memory and durable workflow

| Candidates | Proposed disposition | Rationale |
|------------|----------------------|-----------|
| **Qdrant** | **INCUMBENT / SEMANTIC RETRIEVAL** | Existing platform. |
| **pgvector** | **CHALLENGER / RETRIEVAL** | Simpler, already have Postgres. |
| **LLMLingua-2** | **SELECTED COMPRESSION PILOT** | Already chosen. |
| Mem0 | **EXPLORE / L1 CONTINUITY** | Distinct: agent memory. |
| OpenViking | **DONOR ONLY** | Not a current runtime candidate. |
| LangGraph | **DONOR ONLY** | Already non-production skeleton. |
| Agno/AgentOS | **DONOR ONLY** | No demonstrated gap. |
| **Temporal** | **DEFERRED / DURABLE WORKFLOW CANDIDATE** | Distinct seam; trigger when durable multi-day workflows need engine. |
| Pydantic AI | **HOLD** — trigger: need agent-programming abstraction beyond current stack | Overlaps with existing controlled-agent stack. |
| DSPy | **HOLD** — trigger: prompt/program optimization becomes a measured gap | Optimization framework; not a current need. |

**Decision:** Keep existing Qdrant/pgvector/LLMLingua-2/Mem0/Temporal. Demote Pydantic AI and DSPy to HOLD.

### 3.9 Document, privacy and source intelligence

| Candidates | Proposed disposition | Rationale |
|------------|----------------------|-----------|
| **ClamAV** | **PILOT COMPLETE / TRIAL-ELIGIBLE** | Malware scanning; do not restart. |
| **Docling** | **PILOT IN PROGRESS** | Continue existing work only. |
| **Presidio** | **QUEUED PILOT** | PII processing; distinct seam. |
| **urlwatch** | **QUEUED PILOT** | Source change monitoring; distinct seam. |
| EU DSS | **RESEARCH** | Digital signature trust; distinct but distant. |

**Decision:** Keep as-is; these are genuinely distinct seams.

### 3.10 Frontend, human interaction and agent UI

| Candidates | Proposed disposition | Rationale |
|------------|----------------------|-----------|
| **CopilotKit / AG-UI** | **EXPLORE / POST-L M PILOT** | Already correctly deferred to M. |
| Storybook | **HOLD** — trigger: M component/design-system work justifies it | UI workbench; not needed now. |
| Penpot | **PREFERRED DESIGN ENVIRONMENT** | Not a runtime dependency. |

**Decision:** Keep as-is.

### 3.11 Cybersecurity skill and Red Team programme

| Candidates | Proposed disposition | Rationale |
|------------|----------------------|-----------|
| community cybersecurity skill corpus | **RESEARCH / DONOR** | Reference material. |
| defensive tranche | **POST-L WHERE USEFUL** | Not a Radar tool candidate. |
| Cybersecurity Skill Registry | **FUTURE GOVERNED PILOT** | Not current. |
| operational offensive Red Team agents | **NOT IMPLEMENTED** | Correct. |
| arbitrary production-target attack authority | **REJECTED** | Correct. |

**Decision:** No change; boundaries are correct.

---

## 4. Consolidated seam map

```text
ADVERSARIAL EVALUATION       Promptfoo (incumbent) + Inspect AI + Garak + ToolSandbox
OBSERVABILITY                OpenTelemetry (incumbent) + Arize Phoenix
SAST                         Semgrep (incumbent) + CodeQL
DAST/API SECURITY            OWASP ZAP (incumbent) + Schemathesis
DEPENDENCY/CONTAINER         Trivy (incumbent) + OSV-Scanner
SECRET SCANNING              Gitleaks (incumbent) + TruffleHog
IaC ASSURANCE                Checkov (incumbent) + KICS
SANDBOX                      Microsandbox (incumbent) + E2B
AUTHORIZATION                OpenFGA (incumbent) + OPA + Cedar + SpiceDB
RETRIEVAL/COMPRESSION        Qdrant + pgvector + LLMLingua-2
AGENT MEMORY                 Mem0
DURABLE WORKFLOW             Temporal (deferred)
DOCUMENT/PRIVACY/SOURCE      Docling + Presidio + urlwatch
FRONTEND                     CopilotKit/AG-UI (post-L M)
```

Everything else is **HOLD_WITH_TRIGGER** or **REJECTED**.

---

## 5. Recommended Radar V1.3.8 action

1. Update `docs/TECHNOLOGY_RADAR_V1_3_7.md` or publish `docs/TECHNOLOGY_RADAR_V1_3_8.md` with the consolidated seam map.
2. Change every non-incumbent/non-challenger status from "RESEARCH / BENCHMARK CANDIDATE" to either:
   - `HOLD_WITH_TRIGGER`
   - `REJECT`
   - `MERGED INTO <incumbent/challenger>`
3. Add a rule: no candidate may remain in `RESEARCH` for more than one Radar revision without a trigger or rejection.
4. Update `docs/TECHNOLOGY_ADOPTION_LEDGER.md` with the rejections so future sessions do not revive them.

---

## 6. Anti-duplication guardrails

Before adding any new Radar candidate, require:

```text
1. Name the exact AIOS seam it addresses.
2. Name the current incumbent for that seam.
3. Explain why the incumbent cannot close the gap.
4. If it is a challenger, define the falsifiable benchmark that would promote it.
5. If no unique seam exists, reject.
```

This prevents "tool collection" from masquerading as architecture.
