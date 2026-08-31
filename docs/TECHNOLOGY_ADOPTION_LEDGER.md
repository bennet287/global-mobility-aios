# Global Mobility AIOS — Technology Adoption Ledger

**Date:** 2026-08-31  
**Status:** ACTIVE REPOSITORY-TRUTH INDEX  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Baseline head inspected before this ledger:** `74082e7296e17333027cebd7ca602d408f558f95`  
**Scheduling authority:** `docs/ROADMAP.md`  
**Technology evaluation authority:** `docs/TECHNOLOGY_RADAR_V1_3_5.md`  
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

A technology can be `RESEARCH`, `EXPLORE`, `ASSESS`, `PILOT`, `TRIAL-ELIGIBLE`, `DEFERRED`, or a donor candidate without a first-party runtime dependency.

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

Do not infer implementation from chat memory, filenames under `vendor/`, workflow examples, architecture diagrams, or Radar tables alone.

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

### 1.4 External infrastructure never becomes constitutional authority

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
| OpenTelemetry | vendor-neutral operational telemetry/correlation foundation exists | **PILOT COMPLETE / TRIAL-ELIGIBLE** | already supports L operational diagnosis | do not rebuild telemetry foundation |
| Langfuse | LLM/agent observability need is substantially covered by AIOS + OpenTelemetry | **RESEARCH / PILOT CANDIDATE; no first-party Langfuse dependency observed** | demand-gated on a measured LLM-specific observability gap | do not install merely because Radar lists it |
| OpenFGA | AIOS owns capability/authority/autonomy/risk and Command Gateway semantics | **DEFERRED PILOT; no first-party OpenFGA dependency observed** | only if relationship authorization complexity creates a demonstrated gap | do not treat authorization as missing |
| OPA / Open Policy Agent | AIOS already has native policy/governance enforcement seams | **no first-party OPA adapter/dependency observed at inspected baseline** | only behind a future AIOS-owned policy-evaluation boundary if a measured need appears | do not create a second policy truth system |
| CopilotKit / AG-UI | governed Cockpit, persisted projection and human/Board interaction capability already exist natively | **EXPLORE / POST-L FRONTEND INTERACTION CANDIDATE; no package installed** | after L seal, aligned with M only if it improves the accepted Cockpit | do not start M or add package pre-L |
| Promptfoo | adversarial/evaluation infrastructure capability exists | **PILOT COMPLETE / TRIAL-ELIGIBLE** | may support bounded evaluation when needed | do not restart Promptfoo pilot from zero |
| Anthropic-Cybersecurity-Skills community corpus | cybersecurity donor architecture and intake/governance design established | **RESEARCH / DONOR CANDIDATE; controlled import only** | P0/P1 donor after current L acceptance unless a separate authorized incident need exists | do not directly install/load unrestricted skills |
| AIOS Red Team / Adversarial Security Lab | architecture, authorization model, target organization and mandatory controls are documented | **PROGRAMME STARTED AT ARCHITECTURE/RADAR LEVEL; runtime lab not claimed implemented** | offensive execution remains post-L and necessity/authorization gated | continue from V1.3.4/V1.3.5; do not redesign from scratch |
| Backup / isolated restore | bounded recoverability proof exists | **IMPLEMENTED SUPPORTING FOUNDATION** | production release blocker only when deployment target requires it | do not recreate the already implemented proof as a new Radar wave |
| SecretsPort | AIOS-owned secret-reference boundary exists | **IMPLEMENTED BOUNDED PILOT** | supporting parallel; production backend promotion demand-gated | extend existing port rather than create another secret system |
| OpenBao | optional KV-v2 provider behind SecretsPort | **NON-PRODUCTION BOUNDED ADAPTER IMPLEMENTED; PRODUCTION ADOPTION NOT CLAIMED** | promote only with real deployment/rotation/recovery need and proof | do not claim production adoption |
| ClamAV | malware scan/quarantine adapter capability exists | **PILOT COMPLETE / TRIAL-ELIGIBLE** | pull forward only where upload-security dependency requires it | do not recreate pilot |
| Docling | document normalization candidate | **PILOT IN PROGRESS** | continue only against the active document-intelligence need | inspect existing work before adding another parser stack |
| Presidio | privacy/sensitive-data processing candidate | **QUEUED PILOT** | necessity-gated | not implemented merely because queued |
| urlwatch | official-source change-monitoring candidate | **QUEUED PILOT** | necessity-gated | inspect existing source-monitoring code first |
| LLMLingua-2 | Context Broker owns context truth and purpose-scoped assembly | **SELECTED PRIMARY COMPRESSION PILOT** | advance only on measured token/context/runtime need | compressed context never becomes Evidence |
| pgvector | governed semantic retrieval candidate | **BENCHMARK** | compare only when retrieval need justifies change | do not replace Qdrant by fashion/default |
| Qdrant | current platform semantic-retrieval capability | **CURRENT PLATFORM CAPABILITY / BENCHMARK BASELINE** | retain unless evidence favors another provider | no parallel truth store without boundary |
| Microsandbox | future isolated execution seam identified | **EXPLORE / SANDBOX PROVIDER CANDIDATE; NOT ADOPTED** | post-L engineering/security need | sandbox capability does not grant authority |
| Mem0 | continuity/memory need has AIOS Context Broker boundary | **EXPLORE / MEMORY PROVIDER CANDIDATE; NOT ADOPTED** | post-L/post-M measured need | memory cannot become Evidence/VerifiedRule |
| OpenViking | overlapping context DB concepts may be studied | **RESEARCH / DONOR; NOT ADOPTED** | research only; license/overlap require caution | do not create second context truth system |
| Agno / AgentOS | AIOS already owns control plane and organization runtime semantics | **ASSESS / DONOR CANDIDATE; NOT ADOPTED** | study mechanics only when a concrete gap exists | AgentOS control plane cannot replace AIOS Cockpit/Board |
| LangGraph | bounded execution-graph concepts may be useful | **RESEARCH / EXECUTION-GRAPH DONOR; NOT ADOPTED** | only behind AIOS runtime boundary on demonstrated need | graph/checkpoint state cannot become WorkItem truth |
| Temporal | durable waits/retries/resumption candidate | **DEFERRED / GAP-TRIGGERED** | only when current runtime demonstrates durable-workflow deficiency | do not introduce second workflow authority pre-need |

---

## 3. Focused reconciliation of the technologies most likely to be duplicated

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

Technology Radar V1.3.5 explicitly positions CopilotKit/AG-UI as a governed Cockpit interaction candidate and defers the first plausible pilot until after L is sealed / M begins. The current first-party web package contract does not include CopilotKit/AG-UI.

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

Commit `6ea70cd4a549bfbbe3951a81d38955e79343403d` added the governed cybersecurity-skill and Red Team Radar architecture. V1.3.5 preserves that posture.

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
```

Not yet claimed:

```text
production Cybersecurity Skill Registry runtime
unrestricted donor-skill import
operational offensive Red Team agents
production-target penetration authority
Microsandbox-backed lab execution
Garak/PyRIT adoption merely because donor skills mention them
```

Continuation rule:

> **Do not create another Red Team architecture. Continue from the existing V1.3.4/V1.3.5 model when ROADMAP scheduling permits implementation.**

Until L is sealed, offensive execution remains deferred unless a separate, explicit, authorized security incident creates an immediate need.

---

## 4. Current milestone protection

At creation of this ledger:

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

This ledger does not seal L, start M, authorize external action, grant Red Team execution authority, promote any external technology, or alter production runtime.

---

## 5. Mandatory pre-implementation anti-duplication check

Every future session that proposes a Radar technology must answer this checklist before code changes:

```text
[ ] What exact product problem is being solved now?
[ ] Does first-party AIOS already solve the capability natively?
[ ] Is there already an AIOS-owned port/adapter for this capability?
[ ] Is the named technology actually present in first-party dependencies/imports/config?
[ ] Is there an existing pilot/test/receipt/commit for it?
[ ] Does ROADMAP permit implementation now?
[ ] Would adoption create a second truth/authority/control-plane system?
[ ] What is the bounded acceptance test?
[ ] What is explicitly NOT being claimed?
[ ] Have ROADMAP / CHANGELOG / this ledger been reconciled if truth changes?
```

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
- a previously believed-missing capability is discovered to already exist.

When this ledger disagrees with newer implementation evidence, **newer repository evidence wins**, and the ledger must be reconciled in the same tranche rather than left stale.

---

## 8. Current next-action rule

This ledger is not a new implementation roadmap.

The master scheduling rule remains:

```text
ROADMAP product need
→ demonstrated architectural gap
→ native build vs existing implementation vs external provider comparison
→ bounded implementation
→ proof
→ documentation reconciliation
```

For the current branch state, L acceptance remains primary. Red Team offensive runtime, CopilotKit/AG-UI M work, Langfuse, OpenFGA and OPA must not be pulled forward merely to consume the Technology Radar.
