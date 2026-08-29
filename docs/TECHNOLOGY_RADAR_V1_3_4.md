# Global Mobility AIOS — Technology Radar V1.3.4

**Date:** 2026-08-29
**Status:** ACTIVE CANONICAL RADAR REVISION
**Supersedes for active radar direction:** `TECHNOLOGY_RADAR_V1_3_3.md`
**Architecture references:** `GLOBAL_MOBILITY_AIOS_COMBINED_ARCHITECTURE_V1_1.md`, `ENTERPRISE_INTEGRATION_ARCHITECTURE_V1.md`
**Integration radar:** `AIOS_INTEGRATION_CAPABILITY_RADAR_V1.md`
**Accepted organization/runtime baseline:** I.1–I.4 COMPLETE / PASS / SEALED; J.1 COMPLETE / PASS / SEALED; K.1 COMPLETE / PASS / SEALED
**Next product increment:** L — Live Organization
**Forward CI direction:** self-hosted Woodpecker parity proven; historical GitHub Actions evidence remains historical evidence

Technology Radar V1.3.4 preserves the evidence-driven adoption model and formal enterprise integration/capability-gap programme, retains Tencent Hy4 Preview as a bounded frontend-development evaluation candidate, and adds the community `Anthropic-Cybersecurity-Skills` repository as a governed cybersecurity skill-corpus donor for defensive AIOS security agents and a future isolated AIOS Red Team / Adversarial Security Lab.

> **External infrastructure provides capability. AIOS owns meaning, truth and authority.**

> **No new major framework by default; no missing commodity infrastructure by neglect.**

---

## 1. Adoption lifecycle

```text
REFERENCE
  ↓
RESEARCH
  ↓
BENCHMARK
  ↓
PILOT
  ↓
TRIAL
  ↓
ADOPT
```

Additional governance states:

```text
ASSESS
DONOR CANDIDATE
WATCH
DEFER
REJECT
STRATEGIC DONOR
```

`ASSESS` means the technology is relevant enough for bounded architectural study but has no active implementation claim. `DONOR CANDIDATE` means concepts may be studied or adapted without adopting the external runtime or persistence model.

No state below `ADOPT` is a production-adoption claim.

---

## 2. Current strategic set

### Organization / runtime / context

| Technology | AIOS capability | State |
|---|---|---|
| Munder Difflin v0.4.4 | Organization Fabric / runtime / communication / Skills donor | STRATEGIC DONOR / CONTROLLED ADOPTION |
| DeepSeek Harness (developer preview) | execution-harness composition / runtime provenance / replay / sandbox donor candidate | ASSESS / DONOR CANDIDATE — NOT ADOPTED |
| Plasma Wiki 1.2.0 | Context-efficient project/organizational knowledge beneath Context Broker | PINNED DONOR PRESENT / PILOT APPROVED |
| Plasma Fractal 1.1.0 | Recursive bounded Mission decomposition / hierarchical execution | PINNED DONOR PRESENT / PILOT APPROVED — SANDBOXED ENGINEERING ONLY |
| LLMLingua-2 | Context/token compression behind `ContextCompressionPort` | SELECTED PRIMARY PILOT |
| Local/open models | economical inference | BENCHMARK THROUGH MODEL ROUTER |
| Hosted/frontier APIs | difficult/high-risk reasoning | SELECTIVE ESCALATION RESOURCE |
| Tencent Hy4 Preview | frontend implementation challenger / long-context coding assistance | RESEARCH → BOUNDED PILOT — DEVELOPER TOOLING ONLY; NOT A PRODUCTION AIOS RUNTIME |

The Plasma vendor source import is now present in the V12 repository. Vendoring remains distinct from production adoption.

### Existing platform candidates

| Technology | Intended capability | State |
|---|---|---|
| Promptfoo | AI regression/adversarial evaluation | PILOT COMPLETE / TRIAL-ELIGIBLE |
| Anthropic-Cybersecurity-Skills (community) | governed cybersecurity skill corpus for defensive agents + isolated adversarial-security lab | RESEARCH / DONOR CANDIDATE — CONTROLLED IMPORT ONLY; NO DIRECT PRODUCTION RUNTIME |
| OpenTelemetry | vendor-neutral engineering telemetry | PILOT COMPLETE / TRIAL-ELIGIBLE; PRIORITY FOR L |
| ClamAV | upload malware scanning/quarantine | PILOT COMPLETE / TRIAL-ELIGIBLE |
| Docling | document normalization/structured intelligence | PILOT IN PROGRESS |
| Presidio | privacy/sensitive-data processing | QUEUED PILOT |
| urlwatch | official-source change monitoring | QUEUED PILOT |
| pgvector | governed semantic retrieval | BENCHMARK |
| Qdrant | semantic retrieval alternative/current platform capability | BENCHMARK AGAINST PGVECTOR |
| Pydantic AI | typed runtime candidate | RESEARCH / PILOT CANDIDATE; NO NEED PROVEN FOR K.1 |
| Langfuse | LLM/agent observability behind OpenTelemetry | RESEARCH / PILOT CANDIDATE |
| Temporal | durable waits/retries/resumption | DEFERRED PILOT / GAP-TRIGGERED |
| OpenFGA | relationship authorization beneath AIOS semantics | DEFERRED PILOT |
| DSPy | offline AI-program optimization | RESEARCH |
| EU DSS | electronic-signature validation | RESEARCH |

### Anthropic-Cybersecurity-Skills donor + AIOS adversarial-security posture

Upstream reviewed for this radar revision:

- repository: `https://github.com/mukul975/Anthropic-Cybersecurity-Skills`;
- evaluation pin: `1b3f6b2286981381a5cc0566551ef3bb6bc38383` on upstream `main`;
- license: Apache-2.0;
- upstream describes itself as an independent community project and explicitly states that it is **not affiliated with Anthropic PBC**;
- the library uses structured `SKILL.md` playbooks compatible with the agentskills.io pattern and spans AI security, DevSecOps, API security, cloud/container security, IAM, incident response, threat hunting, supply-chain security, forensics, red teaming and related domains;
- upstream maps relevant skills to combinations of MITRE ATT&CK, NIST CSF 2.0, MITRE ATLAS, MITRE D3FEND, NIST AI RMF and MITRE F3;
- the corpus contains defensive as well as offensive/dual-use techniques, so direct unrestricted loading into production agents is rejected.

Current decision:

```text
Technology Radar:       RESEARCH / DONOR CANDIDATE
Priority posture:        P0/P1 CYBERSECURITY DONOR AFTER CURRENT L ACCEPTANCE
Direct production install: NO
Unreviewed npx skill install: NO
Production runtime dependency: NO
AIOS-owned skill registry: FUTURE GOVERNED PILOT
Defensive skill tranche: PRIORITIZE
Offensive / dual-use tranche: RED TEAM LAB ONLY
L dependency:           NO
M milestone start:      NO
Authority effect:       NONE
```

The adoption boundary is:

```text
UPSTREAM CYBERSECURITY SKILL CORPUS
        ↓
AIOS intake / importer
        ↓
schema + content validation
        ↓
source provenance + commit/hash pinning
        ↓
security/risk classification
        ↓
human/automated review
        ↓
AIOS Cybersecurity Skill Registry
        ↓
approved role-specific subset
        ↓
Cybersecurity Agents / Red Team Lab
        ↓
AIOS policy + Command Gateway
```

Permanent rules:

> **Skill knowledge != execution authority.**

> **CAN DO != MAY DO.**

A skill may teach an agent how a technique works without granting permission to execute that technique. No upstream skill, script, tool description, model response or framework mapping can grant AIOS authority, autonomy, credentials, target scope or external-action permission.

#### Defensive cybersecurity-agent tranche

The first governed review tranche should prefer defensive and assurance-oriented skills with direct relevance to the current architecture:

| Area | Candidate upstream skill | Intended AIOS use |
|---|---|---|
| Agent security | `securing-agentic-ai-tool-invocation` | Command Gateway / tool-boundary hardening |
| AI security | `detecting-indirect-prompt-injection` | protect web/document/email/tool-result ingestion before ContextBundle construction |
| MCP | `auditing-mcp-servers-for-tool-poisoning` | Integration Fabric / MCP security evaluation |
| Secrets | `implementing-secrets-scanning-in-ci-cd` | prevent credentials entering repository and delivery pipelines |
| GitHub / CI | `securing-github-actions-workflows` | CI supply-chain and token-permission hardening |
| Supply chain | `verifying-build-provenance-with-slsa-sigstore` | artifact/build provenance |
| Supply chain | `generating-and-analyzing-sboms` | software inventory and dependency evidence |
| Supply chain | `detecting-dependency-confusion` | Python/npm package-boundary protection |
| SAST | `implementing-semgrep-for-custom-sast-rules` | code security scanning |
| Containers | `performing-container-security-scanning-with-trivy` | image/IaC security gating |
| Containers | `hardening-docker-containers-for-production` | production runtime posture |
| API security | `testing-api-security-with-owasp-top-10` | FastAPI/API assurance |
| API security | `implementing-api-schema-validation-security` | request/response contract hardening |
| IAM | `performing-oauth-scope-minimization-review` | integration least privilege |
| Incident response | `triaging-security-incident` | bounded internal incident triage |
| Threat modelling | `performing-threat-modeling-with-owasp-threat-dragon` | architecture/security review |

These names are candidate donor skills, not approved capabilities. Each must still pass AIOS provenance, applicability, maintenance, dependency, licensing, safety and acceptance review.

#### AIOS Cybersecurity Skill Registry target

Imported skills should become AIOS-owned governed records rather than copied instructions with lost provenance. The target record should preserve at least:

```text
CybersecuritySkill
  id / skill_key / title / domain / subdomain
  source_repository / source_path
  source_commit_sha / source_content_sha256 / source_license
  framework_mappings[]
  risk_class / execution_class
  required_capabilities[] / required_tools[]
  default_mode = advisory | read_only | controlled_execution
  human_approval_required
  sandbox_required
  external_network_required
  status = candidate | reviewed | approved | deprecated | blocked
  reviewed_by / reviewed_at
```

Upstream change handling must be content-addressed:

```text
approved upstream version
        ↓
upstream content changes
        ↓
new commit/hash
        ↓
new candidate revision
        ↓
review required
        ↓
previous approved version remains unchanged until superseded
```

No silent skill mutation is allowed.

#### AIOS Red Team / Adversarial Security Lab

Offensive and dual-use skills have a legitimate AIOS destination only inside a **separate, isolated, explicitly authorized Red Team / Adversarial Security Lab**. They must not be attached to ordinary production security employees merely because they are available in the donor corpus.

Target organization:

```text
Cybersecurity Organization
│
├── Security Architecture
├── AppSec
├── DevSecOps
├── Cloud / Infrastructure Security
├── AI & Agent Security
├── Detection / Threat Hunting
├── Incident Response
│
└── AIOS Red Team / Adversarial Security Lab
    ├── Agent / LLM Red Team
    ├── Prompt-injection / RAG adversarial testing
    ├── Tool / MCP adversarial testing
    ├── API / application red team
    ├── Identity / secrets red team
    ├── Container / infrastructure red team
    ├── Supply-chain red team
    └── Purple-team validation / retest
```

Candidate donor skills for the isolated lab include:

```text
continuous-llm-red-teaming-with-promptfoo
red-teaming-llms-with-garak
orchestrating-llm-attacks-with-pyrit
testing-for-system-prompt-leakage
testing-prompt-injection-in-rag-pipelines
auditing-mcp-servers-for-tool-poisoning
performing-kubernetes-penetration-testing
conducting-cloud-penetration-testing
performing-supply-chain-attack-simulation
attacking-oauth-with-device-code-phishing
```

Their presence in the registry does not authorize execution.

Every adversarial execution must be bound to an AIOS-owned authorization object such as:

```text
AdversarialEngagement
  objective_id
  environment
  target_assets[]
  allowed_targets[]
  authorized_techniques[]
  prohibited_techniques[]
  maximum_impact_level
  network_policy
  credential_policy
  data_policy
  starts_at / expires_at
  requested_by / approved_by / approval_record_id
  status
  evidence_bundle_id
  findings[]
```

Execution rule:

```text
technical capability
      +
current AdversarialEngagement
      +
target inside approved scope
      +
technique explicitly allowed
      +
credential/network policy satisfied
      +
Command Gateway authorization
      =
MAY EXECUTE
```

Mandatory lab controls:

- default deny for offensive capabilities;
- isolated/sandboxed execution by default;
- no production credentials available to lab agents;
- explicit target and time-box scope;
- restricted network egress;
- destructive/high-impact techniques blocked or subject to an additional human authorization floor;
- synthetic/non-personal test data wherever feasible;
- durable command/tool/evidence/findings lineage;
- no agent may expand its own engagement scope;
- findings route to defensive owners;
- remediation requires independent blue-team/owner action where material;
- purple-team retest produces evidence-backed closure rather than self-attested success.

The Lab must red-team AIOS itself, including attempts to violate constitutional invariants:

```text
prompt / indirect prompt injection
poisoned official-source or document content
MCP/tool poisoning and tool shadowing
provider-response manipulation
unauthorized tool invocation
credential/identity privilege escalation
Command Gateway bypass attempts
replay / duplicate external-effect attempts
memory poisoning
telemetry-to-truth confusion
forged Evidence / provenance
fabricated human approval
agent collusion / separation-of-duty bypass
```

The objective is **continuous security assurance**, not offensive activity for its own sake:

```text
authorized adversarial test
→ durable finding
→ mapped control / ATT&CK / ATLAS evidence
→ defensive remediation
→ independent retest
→ Board-safe assurance result
```

Promptfoo remains the current trial-eligible adversarial evaluation infrastructure candidate. Garak, PyRIT and other donor-referenced tools are not adopted by this radar merely because upstream skills mention them; each technology still requires its own bounded AIOS evaluation when a measured need exists.

This donor and Lab posture does **not** interrupt Milestone L acceptance. Architecture/research may be recorded now; implementation and offensive execution remain post-L, necessity-gated work unless an immediate security incident creates a separate authorized need.

### Tencent Hy4 Preview frontend-development evaluation posture

Official release posture at this review point:

- Hy4 Preview is an Apache-2.0 open-weight Mixture-of-Experts text-generation model;
- Tencent reports 770B backbone parameters, 49B activated parameters and a 1M-token context window;
- Tencent positions the preview for long-horizon software engineering and reports gains in frontend visual taste and interaction quality;
- the published comparison is primarily vendor-reported and internally evaluated, so independent AIOS evidence is not established;
- upstream identifies preview limitations including longer-than-necessary reasoning and over-verification;
- the official FP8 serving recipes require an eight-GPU tensor-parallel deployment, so self-hosting is not assumed to be economical for the current project.

Official references:

- `https://huggingface.co/tencent/Hy4-preview`
- `https://github.com/Tencent-Hunyuan/Hy4-preview`
- `https://www.tencent.com/tencent-releases-and-open-sources-tencent-hy4-preview/`

Current decision:

```text
Technology Radar:       RESEARCH
Pilot status:           BOUNDED PILOT APPROVED
Pilot domain:           sanitized frontend-development comparison
Production runtime:     NO
Model Router entry:     NO
L dependency:           NO
M milestone start:      NO
Authority effect:       NONE
Self-hosting decision:  NO CURRENT NEED
```

The first permitted pilot is a side-by-side implementation comparison on an existing L/UX2 surface such as `/cockpit/live-organization`. It must use sanitized repository context and representative non-personal fixtures. It must not send credentials, real mobility cases, private Evidence, personal data or unrestricted repository content to an unreviewed hosted endpoint.

The comparison must evaluate:

```text
truth-boundary preservation
information hierarchy and visual quality
loading / empty / partial / blocked / stale / failure states
accessibility and reduced-motion behavior
responsive behavior
Next.js / React maintainability
tests / types / production build / browser proof
latency, cost and manual correction burden
```

Generated frontend code may not fabricate employee activity, infer online/offline status from heartbeat freshness, treat provider/model state as authority, introduce a new business-truth path, or begin the M Board Transparency milestone. Human Owner/product judgment and the existing repository acceptance gates remain authoritative.

Hy4 Preview may advance to `BENCHMARK` only after a recorded, reproducible comparison against the current primary development workflow. Vendor benchmark claims or attractive screenshots alone are insufficient.

### DeepSeek Harness donor-candidate posture

Official upstream posture at this review point:

- DeepSeek Harness is an open-source MIT-licensed agent harness in **developer preview**;
- upstream explicitly warns that compatibility-breaking changes are expected;
- the Cordis kernel provides a plugin architecture where models, tools, skills, sessions, sandboxes, storage, agent loops, scheduling and UI are composable plugins;
- the runtime is local-first by default but may store session context, tool records, paths, runtime logs, configured service addresses and API keys locally;
- upstream recommends a dedicated VM/container with restricted privileges because the harness can execute code and access local systems.

Official references:

- `https://www.deepseek.com/harness/en/`
- `https://github.com/deepseek-ai/deepseek-harness`
- `https://www.deepseek.com/harness/en/data-processing/`
- `https://www.deepseek.com/harness/en/privacy/`

AIOS interest is architectural, not authority-bearing. Highest-value concepts to study later are:

```text
Cordis/plugin lifecycle
append-only execution trajectory concepts
session replay / resume / fork
runtime inspection
sandbox abstraction
tool/service dependency composition
subagent scheduling mechanics
provider/runtime composition
```

The append-only trajectory concept is especially relevant to execution provenance and diagnosis, but AIOS must preserve a stricter separation:

```text
runtime trajectory / technical execution evidence
!=
canonical OrganizationActivity
```

AIOS may persist enough typed execution evidence to reconstruct, inspect and replay a run. It does **not** establish unrestricted hidden chain-of-thought retention as a product requirement.

If Harness is ever evaluated as an adapter, the boundary must remain:

```text
GLOBAL MOBILITY AIOS
  OrganizationPosition
  Objective / Mission / WorkItem
  ContextBundle
  Evidence / VerifiedRule
  Capability / Authority / Autonomy / Risk
  Governance
  OrganizationalActionOutput
  OrganizationActivity
  Outcome
        ↓
  provider-neutral RuntimePort
        ↓
  optional DeepSeek Harness adapter
        ↓
  model / tool / sandbox / session plugins
```

Permanent rejection rules:

```text
Harness runtime capability != AIOS organizational authority
plugin installed != capability authorized
capability available != action authorized
provider/model identity != autonomy
Harness session/storage != canonical AIOS business truth
Harness trajectory != canonical OrganizationActivity
Harness storage != long-lived AIOS secrets authority
```

A future adapter must use AIOS-owned credential/secrets boundaries and scoped runtime injection rather than treating Harness-local credential storage as the organization credential authority.

Current scheduling decision:

```text
Technology Radar:       ASSESS
Donor status:           DONOR CANDIDATE
Strategic donor:        NOT YET
Runtime adapter:        POSSIBLE FUTURE
Production adoption:    NO
L dependency:           NO
Immediate benchmark:    NO
Authority:              NONE
Scheduling:             DEFERRED / GAP-TRIGGERED
```

A bounded evaluation becomes justified only when the native AIOS runtime exposes a measured gap that these concepts might solve. The first plausible evaluation context is the future AIOS Engineering workforce, where coding-agent shell/file/sandbox mechanics fit the upstream product domain more naturally than regulated mobility execution.

DeepSeek Harness discovery does not change L/M/N priority and does not create an independent implementation programme.

### New enterprise-integration capability candidates

| Capability | Candidates / class | State |
|---|---|---|
| Secrets management | OpenBao-class | RESEARCH NOW → bounded PILOT |
| Identity / SSO | Keycloak / Authentik-class | RESEARCH NOW |
| PostgreSQL backup / PITR | pgBackRest / WAL-G-class | RESEARCH NOW |
| Encrypted backup / restore | Restic-class | RESEARCH NOW |
| Observability backend | Langfuse and/or conventional OTel-compatible backend | RESEARCH / PILOT CANDIDATE |
| Communications | provider-neutral email/portal/SMS adapters | CONTRACT DESIGN NOW; PROVIDER DEFERRED |
| Open-source e-signing | Documenso / DocuSeal-class | RESEARCH / WATCH |
| ERP/accounting | ERPNext / Odoo / accounting integration | WATCH / DEFER |
| Payments | provider-neutral payment port | DEFER PROVIDER SELECTION |
| Feature flags | Unleash-class | WATCH |

---

## 3. Capability-first adoption rule

```text
Capability gap?
  ├── no → do not add technology
  └── yes
       ↓
Global Mobility differentiator?
  ├── yes → build/extend AIOS-native domain capability
  └── no
       ↓
Mature infrastructure available?
  ├── yes → integrate behind AIOS-owned port
  └── no → smallest bounded implementation or defer
```

This prevents two opposite failures:

- building every commodity capability internally;
- turning AIOS into a collection of externally-owned frameworks.

---

## 4. Current L interaction

The next product milestone remains L — Live Organization.

Technology work may support L but may not replace it.

Priority integration contribution to L:

```text
real persisted Austria organization cycle
        ↓
canonical AIOS Activity / execution truth
        +
OpenTelemetry correlation
        ↓
latency / retries / runtime/tool telemetry
        ↓
Cockpit / transparency read model
```

Permanent distinction:

```text
engineering telemetry != canonical AIOS Activity
```

L should prove organization behavior using persisted AIOS truth; observability provides correlated operational evidence.

DeepSeek Harness is not an L dependency and is not scheduled by this section.

Hy4 Preview is also not an L dependency. Its bounded developer-tooling pilot may compare implementation quality on an existing L/UX2 surface only when it does not delay L acceptance; it cannot initiate M or establish product/runtime model eligibility.

---

## 5. Secrets decision

Production AIOS should not rely indefinitely on flat `.env` files for growing provider credentials.

Target:

```text
AIOS config
→ secret reference
→ SecretsPort
→ secret backend
→ runtime injection
```

Permanent rules:

```text
secret != prompt
secret != ContextBundle
secret != memory
secret != OrganizationActivity
secret != repository content
```

OpenBao-class infrastructure enters RESEARCH NOW. First pilot must be bounded to non-production credentials and must test retrieval, scope, rotation/revocation and recovery.

---

## 6. Identity / SSO decision

Keycloak and Authentik-class systems enter RESEARCH NOW.

Permanent rule:

> **Identity Provider != Authority Provider.**

An IdP may authenticate a human/service identity. AIOS remains authoritative for tenant, role, `OrganizationPosition`, reserved powers, capability authority, autonomy and material-action permission.

No production identity migration is authorized by this radar.

---

## 7. Backup / DR decision

Backup infrastructure is now a production-foundation priority.

Canonical classification:

```text
CANONICAL → restore-tested backup required
DERIVED   → may be rebuilt
CACHE     → may be discarded
EXTERNAL  → reconciliation required
```

Research now:

- PostgreSQL PITR/scheduled backup via pgBackRest/WAL-G-class tooling;
- encrypted off-host backup via Restic-class tooling;
- MinIO/S3 versioning/replication strategy;
- isolated restore proof;
- RPO/RTO definition.

A backup file existing is not acceptance. Restore must be demonstrated.

---

## 8. Communications decision

A provider-neutral `CommunicationPort` / Communications Gateway is architecturally approved for design.

```text
CommunicationIntent
→ risk/materiality/authority/review
→ Command Gateway where material
→ CommunicationPort
→ provider
→ delivery result
→ reconciliation / lineage
```

No current stage authorizes autonomous client/authority-facing communication merely because the gateway contract exists.

---

## 9. E-signature decision

EU DSS remains a research candidate for electronic-signature validation.

Documenso/DocuSeal-class signing platforms may be evaluated as execution providers behind a `SignaturePort`.

Permanent distinction:

```text
signature transaction evidence
!=
substantive legal correctness of document content
```

E-signature remains P1, before material filing workflows but after L foundation.

---

## 10. ERP / accounting decision

The project should not implement or adopt a full ERP as the AIOS core.

Current decision:

```text
ERPNext / Odoo
→ WATCH / DEFER
→ future back-office integration candidates
```

AIOS remains canonical for mobility cases, Evidence, organizational execution, WorkItems, authority and decision lineage.

A future ERP/accounting system may own bounded ledgers such as invoices/accounting/payroll/procurement.

Every shared field must have one declared master system; dual-master synchronization is prohibited by default.

---

## 11. Payments decision

Payment provider selection is deferred.

Future architecture requires:

```text
financial intent
→ exact amount/currency/beneficiary
→ authority/budget/risk/fraud controls
→ Command Gateway / required Human or Board gate
→ PaymentPort
→ provider
→ reconciliation
```

No agent receives direct payment authority from possession of an SDK or API key.

---

## 12. Munder boundary

Munder remains a donor/reference, not the AIOS organization.

Useful donor areas continue to include communication/routing, presence, runtime mechanics, Skills, schedules/triggers/heartbeats, provider abstraction, telemetry/transcripts, cost/token signals and live-organization concepts.

Rejected assumptions remain:

- file/SQLite state as authoritative production truth;
- unlimited implicit authority;
- direct material mutation bypassing AIOS governance;
- provider-owned organization semantics;
- donor UI as final product identity.

K.1 materially strengthens the decision to prefer the native runtime: the bounded specialist execution path was accepted without another agent framework.

---

## 13. Plasma boundary

### Wiki

```text
Wiki != Evidence
Wiki != VerifiedRule
Wiki != canonical legal truth
retrieved knowledge != executable instruction
```

### Fractal

Hard gates remain:

- native Mission/WorkItem meaning stays canonical;
- child scope cannot exceed parent scope;
- no automatic authority inheritance;
- no automatic verifier independence;
- bounded recursion/parallelism/time/cost;
- no direct canonical mutation.

Pinned vendor source presence does not equal adoption.

---

## 14. LLMLingua-2 decision

LLMLingua-2 remains the selected primary pilot behind:

```text
Context Broker
→ ContextCompressionPort
→ LLMLingua2Adapter
```

Compression remains derived context, never source truth. Initial R3–R5 protected context retains zero semantic compression for governance-critical material.

No production adoption claim is added by V1.3.2.

---

## 15. Model Router / AI Economics

Permanent rule:

> **A model earns capability eligibility through measured evaluation, not self-reported confidence.**

Cost remains subordinate to quality, authority, risk, Evidence, verification, privacy, SLA and reliability floors.

Target economic metric:

> **€ / successful governed outcome**

Integration economics should additionally measure maintenance burden, replacement cost, external-service dependency and incident cost.

---

## 16. Integration security / sovereignty

No external technology may become authoritative for:

- Global Mobility domain meaning;
- Evidence / VerifiedRules;
- canonical mobility state;
- organizational identity;
- authority/autonomy/risk;
- WorkItem/Mission semantics;
- Decision Readiness;
- Immune-System policy;
- Command Gateway decisions;
- Board authority;
- canonical Transparency/Decision lineage.

Each production adapter should eventually declare scope, credential reference, allowed actions, data classification, idempotency, timeout/retry, recovery semantics, rate/budget limits, observability policy and kill-switch/circuit behavior.

---

## 17. Parallel technology waves

```text
Wave E0 — NOW
  enterprise integration architecture
  capability/integration inventory
  ownership matrix

Wave E1 — alongside L
  OpenTelemetry correlation
  secrets-manager bounded pilot
  backup + isolated restore proof

Wave E2
  IdentityPort benchmark
  Communications Gateway contract

Wave E3
  e-signature validation/signing pilot
  governed communications trial

Wave E4 — demand gated
  accounting / ERP adapter benchmark
  payment adapter design
```

No wave automatically authorizes the next. This section is descriptive capability grouping only; `ROADMAP.md` is the scheduling authority.

DeepSeek Harness does not enter any active wave merely by being listed as an ASSESS / DONOR CANDIDATE technology.

Hy4 Preview does not enter an active product-technology wave. Its bounded frontend-development pilot is an optional developer-tool evaluation, not a product dependency or implementation programme.

Anthropic-Cybersecurity-Skills likewise does not enter an active L implementation wave. It is a governed donor candidate for a post-L cybersecurity assurance programme. The AIOS Red Team / Adversarial Security Lab is an AIOS-native future capability, not an upstream runtime adoption, and must remain isolated, scope-authorized and Command-Gateway governed.

---

## 18. No-new-framework default

> **Do not add another major agent framework unless a measured architectural gap cannot be addressed cleanly by AIOS + the current donor/adapter set.**

At the same time, the Technology Radar must proactively identify necessary infrastructure gaps instead of waiting for them to be discovered ad hoc.

DeepSeek Harness is specifically governed by this rule: assessment is allowed; adoption requires a measured gap and bounded comparison against the native AIOS runtime.

A cybersecurity skill corpus is not an authority framework. Direct bulk installation of third-party skills into privileged production agents is rejected; governed, content-addressed import of reviewed skills behind AIOS-owned capability and authorization boundaries is the permitted direction.

---

## 19. Permanent sovereignty rule

> **Adopt commodity capability aggressively when evidence supports it. Build differentiating mobility intelligence natively. Never surrender the constitution.**
