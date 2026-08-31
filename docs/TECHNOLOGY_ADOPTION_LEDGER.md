# Global Mobility AIOS — Technology Adoption Ledger

**Date:** 2026-08-31  
**Status:** ACTIVE REPOSITORY-TRUTH INDEX  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Original ledger baseline head:** `74082e7296e17333027cebd7ca602d408f558f95`  
**Latest reconciliation:** V12.34 / Technology Radar V1.3.6 / Wave E2 evaluation hardening  
**Scheduling authority:** `docs/ROADMAP.md`  
**Technology evaluation authority:** `docs/TECHNOLOGY_RADAR_V1_3_6.md`  
**Delivery history:** `docs/CHANGELOG.md`

This ledger exists to prevent a recurring implementation error: **a technology appearing in the Technology Radar must not be interpreted as proof that the external technology is installed, and an external technology not being installed must not be interpreted as proof that the underlying AIOS capability is missing.**

The ledger is intentionally explicit about four separate questions:

```text
1. Does AIOS already have the product capability?
2. Is there an AIOS-owned port/boundary for an optional provider?
3. Is the named external technology actually integrated in first-party runtime code?
4. Has that integration been accepted/adopted for production?
```

Those four questions must never be collapsed into one status word.

---

## 1. Permanent interpretation rules

### 1.1 Radar presence != runtime implementation

A technology can be `RESEARCH`, `EXPLORE`, `ASSESS`, `BENCHMARK`, `PILOT`, `TRIAL-ELIGIBLE`, `DEFERRED`, or a donor candidate without a first-party runtime dependency.

Before implementing any named technology, inspect at minimum:

```text
current branch/head
first-party dependency manifests
first-party imports / adapters / configuration
first-party tests
relevant commit history
ROADMAP scheduling state
Technology Radar state
CHANGELOG implementation claims
```

Do not infer implementation from chat memory, filenames under `vendor/`, workflow examples, architecture diagrams, donor skill names, or Radar tables alone.

### 1.2 Native capability != external-provider adoption

AIOS may already satisfy a product capability natively while retaining an external technology as an optional future provider.

Examples:

```text
AIOS authorization/governance exists
!= OpenFGA is integrated

AIOS policy enforcement exists
!= OPA is integrated

AIOS observability/correlation exists
!= Langfuse is integrated

AIOS governed Cockpit/HITL interaction exists
!= CopilotKit/AG-UI is integrated

AIOS deterministic adversarial contract testing exists
!= Garak/PyRIT is integrated
```

An external provider must solve a demonstrated gap before it is pulled into runtime.

### 1.3 Adapter implementation != production adoption

A bounded adapter or pilot may exist without production adoption.

Example:

```text
SecretsPort + non-production OpenBao adapter IMPLEMENTED
!= production OpenBao deployment ADOPTED
```

Implementation, pilot proof, production promotion, operational proof and milestone acceptance are separate claims.

### 1.4 Evaluation layer != higher-order proof

V12.34 adds a deterministic adversarial-contract gate. Its evidence label must remain exact:

```text
deterministic adversarial contract proof
!= live-model attack resistance
!= professional domain correctness
!= operational Red Team proof
```

Likewise, a mutation-testing score, SAST finding, fuzz result or LLM-security scanner result is evidence for a bounded question; it is not organizational authority or canonical business truth.

### 1.5 External infrastructure never becomes constitutional authority

Permanent boundaries remain:

```text
CAN DO != MAY DO
MEMORY != EVIDENCE
SANDBOX ISOLATION != EXECUTION AUTHORITY
AGENT FRAMEWORK STATE != ORGANIZATION TRUTH
UI INTENT != COMMAND AUTHORIZATION
TELEMETRY != CANONICAL ORGANIZATION ACTIVITY
SKILL KNOWLEDGE != EXECUTION AUTHORITY
```

AIOS remains canonical for organization truth, Evidence/VerifiedRule semantics, authority, autonomy, risk, Command Gateway decisions, WorkItem/Mission meaning, persisted organizational activity and Human Owner / Board sovereignty.

---

## 2. Current adoption matrix

| Technology / capability | AIOS capability status | External technology status | Scheduling truth | Do not duplicate |
|---|---|---|---|---|
| Wave E2 AI-domain adversarial contract gate | deterministic authority/provenance/fake-consensus/prompt-boundary mutation coverage exists | **FIRST-PARTY IMPLEMENTED / FULL LOCAL-CI PROOF PENDING** | supporting L evaluation hardening | do not create a second mock/evaluator stack |
| OpenTelemetry | vendor-neutral operational telemetry/correlation foundation exists | **PILOT COMPLETE / TRIAL-ELIGIBLE** | already supports L operational diagnosis | do not rebuild telemetry foundation |
| Langfuse | LLM/agent observability need is substantially covered by AIOS + OpenTelemetry | **RESEARCH / PILOT CANDIDATE; no first-party Langfuse dependency observed at latest inspection** | demand-gated on a measured LLM-specific observability gap | do not install merely because Radar lists it |
| OpenFGA | AIOS owns capability/authority/autonomy/risk and Command Gateway semantics | **DEFERRED PILOT; no first-party OpenFGA dependency observed** | only if relationship authorization complexity creates a demonstrated gap | do not treat authorization as missing |
| OPA / Open Policy Agent | AIOS already has native policy/governance enforcement seams | **no first-party OPA adapter/dependency observed at latest inspection** | only behind a future AIOS-owned policy-evaluation boundary if a measured need appears | do not create a second policy truth system |
| CopilotKit / AG-UI | governed Cockpit, persisted projection and human/Board interaction capability already exist natively | **EXPLORE / POST-L FRONTEND INTERACTION CANDIDATE; no package installed** | after L seal, aligned with M only if it improves the accepted Cockpit | do not start M or add package pre-L |
| Promptfoo | adversarial/evaluation infrastructure capability exists | **PILOT COMPLETE / TRIAL-ELIGIBLE — EXPANSION CANDIDATE** | may support stronger continuous adversarial regression | do not restart Promptfoo pilot from zero |
| Garak | no first-party Garak integration claimed | **RESEARCH / BOUNDED LIVE-MODEL PILOT CANDIDATE** | future authorized security/evaluation need | do not treat donor mention as installation or attack authority |
| Microsoft PyRIT | no first-party PyRIT integration claimed | **RESEARCH / RED-TEAM-LAB CANDIDATE** | future isolated authorized lab | do not run against arbitrary/production targets |
| DeepEval | no first-party DeepEval integration claimed | **RESEARCH / BENCHMARK CANDIDATE** | only for a concrete metric/test gap | do not add a second evaluation framework without comparison |
| Ragas-style evaluation | retrieval evaluation methods may complement AIOS Evidence/retrieval tests | **RESEARCH / BENCHMARK CANDIDATE** | retrieval/RAG quality question required | retrieved score never becomes Evidence truth |
| Hypothesis | property-based testing can strengthen invariant-heavy Python seams | **BENCHMARK / HIGH-PRIORITY ENGINEERING CANDIDATE** | candidate next evaluation hardening tranche | inspect existing property tests/dependency state first |
| mutation testing | test-strength measurement is a recognized gap | **RESEARCH / BOUNDED PILOT CANDIDATE** | benchmark on high-value governance/evaluation modules | mutation score != product acceptance |
| Atheris / guided fuzzing | parser/contract fuzzing may strengthen malformed-input assurance | **RESEARCH / BOUNDED PILOT CANDIDATE** | bounded parser/contract targets only | no uncontrolled fuzzing against external systems |
| Semgrep | SAST/custom security-rule need recognized | **PRIORITY RESEARCH / PILOT CANDIDATE** | defensive CI/security evaluation | inspect any existing scanner config first |
| GitHub CodeQL | semantic code-security analysis candidate | **PRIORITY RESEARCH / BENCHMARK CANDIDATE** | compare against existing/other SAST coverage | avoid redundant mandatory gates without evidence |
| Trivy | container/IaC/dependency scanning candidate | **PRIORITY RESEARCH / PILOT CANDIDATE** | production/security foundation | inspect existing container scanning first |
| Syft + Grype | SBOM + vulnerability correlation candidates | **RESEARCH / PILOT/BENCHMARK CANDIDATES** | supply-chain evidence need | inventory/vulnerability result != exploitability truth |
| SLSA + Sigstore | build provenance/signing candidates | **RESEARCH / TARGET CONTROL / PILOT CANDIDATE** | release artifact path must justify integration | signing infrastructure does not create AIOS authority |
| Gitleaks-class secret scanning | repository/delivery secret detection candidate | **PRIORITY RESEARCH / PILOT CANDIDATE** | complements runtime secret handling | does not replace SecretsPort/OpenBao |
| OWASP API assurance | FastAPI/API adversarial methodology/tooling | **PRIORITY RESEARCH / CONTINUOUS TEST TARGET** | authorized local/test environments | no unsanctioned target testing |
| Anthropic-Cybersecurity-Skills community corpus | cybersecurity donor architecture and intake/governance design established | **RESEARCH / DONOR CANDIDATE; controlled import only** | P0/P1 donor after current L acceptance unless a separate authorized incident need exists | do not directly install/load unrestricted skills |
| AIOS Red Team / Adversarial Security Lab | architecture, authorization model, target organization and mandatory controls are documented | **PROGRAMME STARTED AT ARCHITECTURE/RADAR LEVEL; runtime lab not claimed implemented** | offensive execution remains post-L and necessity/authorization gated | continue existing programme; do not redesign from scratch |
| Backup / isolated restore | bounded recoverability proof exists | **IMPLEMENTED SUPPORTING FOUNDATION** | production release blocker only when deployment target requires it | do not recreate the already implemented proof as a new Radar wave |
| SecretsPort | AIOS-owned secret-reference boundary exists | **IMPLEMENTED BOUNDED PILOT** | supporting parallel; production backend promotion demand-gated | extend existing port rather than create another secret system |
| OpenBao | optional KV-v2 provider behind SecretsPort | **NON-PRODUCTION BOUNDED ADAPTER IMPLEMENTED; PRODUCTION ADOPTION NOT CLAIMED** | promote only with real deployment/rotation/recovery need and proof | do not claim production adoption |
| ClamAV | malware scan/quarantine adapter capability exists | **PILOT COMPLETE / TRIAL-ELIGIBLE** | pull forward only where upload-security dependency requires it | do not recreate pilot |
| Docling | document normalization candidate | **PILOT IN PROGRESS** | continue only against the active document-intelligence need | inspect existing work before adding another parser stack |
| Presidio | privacy/sensitive-data processing candidate | **QUEUED PILOT** | necessity-gated | not implemented merely because queued |
| urlwatch | official-source change-monitoring candidate | **QUEUED PILOT** | necessity-gated | inspect existing source-monitoring code first |
| LLMLingua-2 | Context Broker owns context truth and purpose-scoped assembly | **SELECTED PRIMARY COMPRESSION PILOT** | advance only on measured token/context/runtime need | R3–R5 protected context remains zero-semantic-compression by default |
| pgvector | governed semantic retrieval candidate | **BENCHMARK** | compare only when retrieval need justifies change | do not replace Qdrant by fashion/default |
| Qdrant | current platform semantic-retrieval capability | **CURRENT PLATFORM CAPABILITY / BENCHMARK BASELINE** | retain unless evidence favors another provider | no parallel truth store without boundary |
| Microsandbox | future isolated execution seam identified | **EXPLORE / SANDBOX PROVIDER CANDIDATE; NOT ADOPTED** | post-L engineering/security need | sandbox capability does not grant authority |
| Mem0 | continuity/memory need has AIOS Context Broker boundary | **EXPLORE / MEMORY PROVIDER CANDIDATE; NOT ADOPTED** | post-L/post-M measured need | memory cannot become Evidence/VerifiedRule |
| OpenViking | overlapping context DB concepts may be studied | **RESEARCH / DONOR; NOT ADOPTED** | research only; license/overlap require caution | do not create second context truth system |
| Agno / AgentOS | AIOS already owns control plane and organization runtime semantics | **ASSESS / DONOR CANDIDATE; NOT ADOPTED** | study mechanics only when a concrete gap exists | AgentOS control plane cannot replace AIOS Cockpit/Board |
| LangGraph | bounded execution-graph concepts may be useful | **RESEARCH / EXECUTION-GRAPH DONOR; NOT ADOPTED** | only behind AIOS runtime boundary on demonstrated need | graph/checkpoint state cannot become WorkItem truth |
| Temporal | durable waits/retries/resumption candidate | **DEFERRED / GAP-TRIGGERED** | only when current runtime demonstrates durable-workflow deficiency | do not introduce second workflow authority pre-need |

---

## 3. Focused reconciliation of technologies most likely to be duplicated

### 3.1 Langfuse

**Repository-truth classification:** external Langfuse integration is **not currently proven**.

The capability question is different: AIOS already has an OpenTelemetry-based telemetry/correlation foundation and L requires operational correlation sufficient to diagnose provider/runtime behavior. Therefore Langfuse is not an outstanding mandatory foundation task.

Permitted future reason to pilot Langfuse:

```text
measured LLM-specific observability gap
→ compare native OTel + current tooling against Langfuse capability
→ define AIOS-owned telemetry boundary
→ bounded pilot
→ prove replacement/exit path and truth separation
```

Not permitted:

```text
"Langfuse is on the Radar"
→ install Langfuse
```

### 3.2 OpenFGA

**Repository-truth classification:** external OpenFGA integration is **not currently proven**.

AIOS authorization is not absent. Existing constitutional semantics distinguish capability, authority, autonomy and risk, with material execution constrained by AIOS governance/Command Gateway behavior.

OpenFGA should only be considered if relationship authorization itself becomes a measured complexity/problem, for example large cross-tenant/case/organization delegation graphs that are difficult to represent and evaluate safely with the current first-party model.

Any future shape must remain:

```text
AIOS authorization semantics
→ AIOS-owned relationship authorization port
→ optional OpenFGA decision engine
→ typed bounded result
→ AIOS policy/Command Gateway remains authoritative
```

### 3.3 OPA / Open Policy Agent

**Repository-truth classification:** no first-party OPA adapter/dependency was observed at the inspected baseline.

This does not mean AIOS lacks policy enforcement. Native policy/governance seams already exist. OPA is therefore a potential commodity decision engine, not a missing constitutional layer.

A future OPA pilot is justified only if a concrete policy-expression/evaluation need is demonstrated and must remain subordinate to AIOS semantics:

```text
AIOS policy meaning
→ PolicyEvaluationPort
→ optional OPA/Rego evaluation
→ typed decision evidence
→ AIOS authority boundary
```

Rejected:

```text
OPA policy store
→ independent source of organizational authority
```

### 3.4 CopilotKit / AG-UI

**Repository-truth classification:** **evaluated/classified, not integrated**.

Technology Radar V1.3.6 preserves CopilotKit/AG-UI as a governed Cockpit interaction candidate and defers the first plausible pilot until after L is sealed / M begins. The current first-party web package contract does not include CopilotKit/AG-UI.

AIOS already owns the important semantics:

```text
persisted state / ActionOutput / Evidence
→ governed frontend projection
→ human/Board interaction
→ AIOS API/governance for commands
```

A later frontend library/protocol may improve interaction ergonomics, but it must not manufacture truth or authorize commands.

### 3.5 Red Team / adversarial security

**Repository-truth classification:** **started, but not as an operational offensive runtime**.

Commit `6ea70cd4a549bfbbe3951a81d38955e79343403d` added the governed cybersecurity-skill and Red Team Radar architecture. V1.3.6 preserves and expands its research frontier.

Already established:

```text
community cybersecurity-skill donor classification
AIOS intake/importer target
schema/content/provenance/risk review requirements
Cybersecurity Skill Registry target record
separation of defensive vs offensive/dual-use skills
AIOS Red Team / Adversarial Security Lab target organization
AdversarialEngagement authorization object design
mandatory lab controls
AIOS-self-red-team target classes
Promptfoo as trial-eligible adversarial evaluation infrastructure
Wave E2 deterministic adversarial-contract gate
```

Not yet claimed:

```text
production Cybersecurity Skill Registry runtime
unrestricted donor-skill import
operational offensive Red Team agents
production-target penetration authority
Microsandbox-backed lab execution
Garak/PyRIT integration or adoption
live-model prompt-injection resistance
```

Continuation rule:

> **Do not create another Red Team architecture. Continue from the existing V1.3.4→V1.3.6 model when ROADMAP scheduling permits implementation.**

Until L is sealed, offensive execution remains deferred unless a separate, explicit, authorized security incident creates an immediate need.

### 3.6 Wave E2 evaluation hardening

**Repository-truth classification:** first-party deterministic adversarial contract tooling is implemented in:

```text
scripts/check_ai_domain_adversarial_contract.py
apps/api/tests/test_ai_domain_adversarial_contract.py
```

It reuses the existing blind Austria AI-domain evaluator and exercises authority/provenance/corroboration/prompt-boundary failure classes. It does not add an external dependency.

The correct continuation is to deepen the evidence ladder rather than recreate this gate under a new framework name:

```text
Wave E2 deterministic gate
→ focused local/CI proof
→ broader benchmark/edge-case corpus
→ property/invariant benchmark where useful
→ mutation/fuzz/fault-injection proof where useful
→ live-provider adversarial variants
→ isolated Red Team when authorized
```

---

## 4. Current milestone protection

Current truth at V12.34:

```text
K.1  COMPLETE / PASS / SEALED
L    IMPLEMENTED / ACCEPTANCE PENDING
M    NOT STARTED
```

Remaining L acceptance truth remains:

```text
independent professional Austria review    PENDING
final exact-current-head technical proof   PENDING
```

This ledger does not seal L, start M, authorize external action, grant Red Team execution authority, promote any external technology, or alter production authority.

---

## 5. Mandatory pre-implementation anti-duplication check

Every future session that proposes a Radar technology must answer this checklist before code changes:

```text
[ ] What exact product/risk problem is being solved now?
[ ] Does first-party AIOS already solve the capability natively?
[ ] Is there already an AIOS-owned port/adapter/test gate for this capability?
[ ] Is the named technology actually present in first-party dependencies/imports/config?
[ ] Is there an existing pilot/test/receipt/commit for it?
[ ] Does ROADMAP permit implementation now?
[ ] Would adoption create a second truth/authority/control-plane/evaluation system?
[ ] What is the falsifiable bounded acceptance test?
[ ] What is explicitly NOT being claimed?
[ ] Have ROADMAP / CHANGELOG / this ledger been reconciled if truth changes?
```

For V1.3.6 candidates specifically, search first for existing Promptfoo, property-based tests, mutation/fuzz tooling, SAST/scanner configs, SBOM/provenance tooling and Red Team code before adding a package.

If those questions cannot be answered from repository evidence, **inspect further before implementing**.

---

## 6. Documentation and commit discipline

For every meaningful implementation tranche, future sessions must leave a durable handoff trail.

Minimum documentation expectation:

```text
implementation + focused tests
→ bounded receipt/spec when the capability needs one
→ ROADMAP reconciliation when scheduling/milestone truth changes
→ CHANGELOG entry for delivered behavior
→ TECHNOLOGY_ADOPTION_LEDGER reconciliation when adoption status changes
→ detailed commit message explaining scope, proof and non-claims
→ remote-head verification
```

Commit messages should state enough context that another session can reconstruct intent without chat history. At minimum include:

```text
what changed
why it was necessary now
important architecture/truth boundaries
what tests/proof actually ran
what remains unproven/deferred
whether milestone/adoption status changed
```

Do not use a detailed commit message to replace canonical documentation when repository truth changed; use both.

---

## 7. Update protocol

Update this ledger whenever any of the following occurs:

- a Radar candidate gains a first-party dependency or runtime adapter;
- an existing native capability makes an external candidate unnecessary;
- a pilot becomes trial-eligible or adopted;
- a production promotion is accepted;
- a candidate is rejected/deferred for architectural overlap;
- Red Team/Cybersecurity Skill Registry implementation begins;
- CopilotKit/AG-UI moves from post-L candidate to bounded M pilot;
- OpenFGA/OPA/Langfuse gains a demonstrated gap and real adapter;
- Promptfoo/Garak/PyRIT/property/mutation/fuzz/security tooling gains a real first-party integration;
- a previously believed-missing capability is discovered to already exist.

When this ledger disagrees with newer implementation evidence, **newer repository evidence wins**, and the ledger must be reconciled in the same tranche rather than left stale.

---

## 8. Current next-action rule

This ledger is not a new implementation roadmap.

The master scheduling rule remains:

```text
ROADMAP product/risk need
→ demonstrated architectural/evidence gap
→ native build vs existing implementation vs external provider comparison
→ bounded implementation
→ proof
→ documentation reconciliation
```

For the current branch state, L acceptance remains primary. The aggressive V1.3.6 Radar expands the research frontier but does not automatically pull Red Team offensive runtime, CopilotKit/AG-UI M work, Langfuse, OpenFGA, OPA, Garak, PyRIT or any security scanner into production.
