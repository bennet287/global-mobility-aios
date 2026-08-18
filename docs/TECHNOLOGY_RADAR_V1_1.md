# Global Mobility AIOS — Technology Radar V1.1

**Status:** ACTIVE CANONICAL V1.1 — platform-evolution architecture / evaluation checkpoint
**Date:** 2026-08-18
**Product baseline:** Phase 13.16.7 COMPLETE / PASS at `f0688a872e7e6977b69d1f9ff0607b647fc71d14`
**Active product slice:** Phase 13.16.8 — Professional / Operator experience
**Runtime impact of this checkpoint:** none
**Historical predecessor:** [TECHNOLOGY_RADAR_V1.md](TECHNOLOGY_RADAR_V1.md) remains frozen historical evidence

Technology Radar V1.1 extends the provider-neutral architecture established in V1. It does not
reorder product delivery, install the listed technologies, create runtime provider interfaces, or
change AIOS authority/legal/evidence semantics by itself.

The radar now serves three related purposes:

1. identify technologies that can materially strengthen AIOS capabilities;
2. preserve AIOS ownership of domain meaning and replaceability of external implementations;
3. establish lawful Internal Learning & Quality and the future AIOS Coworker as explicit platform
   directions.

> **AIOS Semantic Sovereignty Principle:** Third-party infrastructure may implement, accelerate,
> observe, execute, retrieve, parse, scan, render, evaluate, or enforce an AIOS-defined
> capability, but it must never become authoritative for AIOS domain meaning, legal status,
> evidence status, certification state, human-review requirements, publication state,
> organizational authority, or business outcome semantics.

> **Internal Learning & Quality Principle:** Subject to applicable law, contractual commitments,
> declared processing purposes, required safeguards, and the relevant data-use policy, AIOS
> should maximize lawful learning from the work it performs. Evaluation, quality improvement,
> operational intelligence, retrieval/document improvement, workflow optimization, and
> appropriate internal model training are first-class product purposes.

The radar is not a dependency manifest. A listed technology is not automatically installed,
production-approved, or allowed to own AIOS state.

---

## 1. Fit tiers and adoption classifications

V1.1 introduces a **strategic fit tier** in addition to the existing adoption classification.
Fit describes architectural/product relevance. Classification describes how close a candidate is
to an evidence-driven implementation decision.

### 1.1 A+ — strongest strategic fit

| Technology | Intended AIOS role | Fit | Current classification |
|---|---|---:|---|
| **Docling** | document normalization / structured document understanding | A+ | ADOPT / EARLY PILOT |
| **Presidio** | sensitive-data detection/transformation for Privacy Gateway | A+ | ADOPT / EARLY PILOT |
| **Promptfoo** | AI regression, adversarial and safety evaluation | A+ | ADOPT / EARLY PILOT |
| **OpenTelemetry** | vendor-neutral AI/application telemetry foundation | A+ | ADOPT / EARLY PILOT |
| **urlwatch** | official-source change monitoring | A+ | ADOPT / EARLY PILOT |
| **ClamAV** | upload quarantine / malware scanning | A+ | ADOPT / EARLY PILOT |
| **OpenWorker (`andrewyng/openworker`)** | AIOS Coworker / finished-work execution reference | **A+** | **STRATEGIC REFERENCE / CONTROLLED PILOT** |
| **Temporal** | durable long-running execution | A+ Strategic | STRATEGIC PILOT |
| **OpenFGA** | fine-grained relationship authorization | A+ Strategic | STRATEGIC PILOT |

OpenWorker is an unusually strong reference for the future AIOS Coworker because its current
product model centers on completing real work, producing deliverables, using files/tools and
connectors, supporting MCP and scheduled automation, remaining model-flexible, and requiring
approval for consequential actions. The project currently documents a local Python agent server,
desktop UI, 25+ connectors, scheduled automations, deliverable production, MCP support, and
cloud/open-weight/local model choices.

**Name disambiguation:** this radar entry refers specifically to the local-first finished-work
coworker project at `andrewyng/openworker`, not other projects using the OpenWorker name.

### 1.2 A — specialist technologies

| Technology | Intended AIOS role | Current classification |
|---|---|---|
| **pgvector** | semantic retrieval candidate | PILOT / BENCHMARK |
| **Pydantic AI** | typed production agent-runtime candidate | PILOT / BENCHMARK |
| **Langfuse** | LLM/agent observability behind OpenTelemetry | PILOT / BENCHMARK |
| **PaddleOCR** | mature OCR candidate | PILOT / BENCHMARK |
| **Unlimited-OCR** | advanced OCR/VLM candidate | PILOT / BENCHMARK |
| **DSPy** | offline AI program optimization | RESEARCH |
| **Gotenberg** | general PDF/document rendering | PILOT / BENCHMARK |
| **Typst** | premium professional report generation | PILOT / BENCHMARK |
| **EU DSS** | EU electronic-signature validation | RESEARCH |

These solve different responsibilities and must not be collapsed merely because several are
adjacent to agent/AI workloads:

```text
OpenWorker     = Coworker / finished-work execution reference
Pydantic AI    = typed AIOS agent-runtime candidate
DSPy           = offline model/program optimization
Temporal       = execution durability
OpenTelemetry  = neutral telemetry
Promptfoo      = evaluation and regression
```

OpenWorker does **not** justify removing an A+ or A specialist candidate.

### 1.3 B / conditional technologies

- Qdrant;
- Fides;
- OpenLineage;
- OPA;
- OpenFeature;
- Haystack;
- MarkItDown.

The cleanup rule is:

> **Do not remove a candidate because another unrelated technology is better overall. Remove it
> only when another candidate demonstrably owns the same capability more effectively and AIOS no
> longer benefits from maintaining both.**

Examples:

- if pgvector decisively wins the AIOS retrieval benchmark, Qdrant can leave the active radar;
- if Docling covers the required lightweight conversion workload, MarkItDown can leave;
- if Pydantic AI plus AIOS-native retrieval/orchestration satisfies the runtime need, Haystack can
  leave.

---

## 2. AIOS Coworker — product capability, not third-party semantics

OpenWorker is recorded as:

```text
Technology:     OpenWorker (andrewyng/openworker)
Fit:            A+
Classification: STRATEGIC REFERENCE / CONTROLLED PILOT
AIOS capability: AIOS Coworker / Agent Execution Plane
```

OpenWorker itself must **not** become a permanent AIOS domain abstraction. The product concept is
**AIOS Coworker**.

The intended experience is:

```text
Human asks for an outcome
          ↓
AIOS understands the case/work context
          ↓
AIOS creates / resolves governed work
          ↓
Agents use relevant tools and information
          ↓
Finished deliverables are created
          ↓
Material actions follow AIOS authority rules
          ↓
Human intervention occurs where required
          ↓
Outcome + provenance + learning signals recorded
```

Candidate outcomes include:

- prepare an employer mobility pack;
- analyse missing evidence;
- draft a professional case brief;
- review authority correspondence;
- prepare a client follow-up;
- update internal case chronology;
- build a qualification evidence memo;
- create a Board briefing;
- analyse a regulatory change;
- prepare an evidence register;
- draft an email/calendar action;
- reconcile a case against a new VerifiedRule.

The objective is:

> **Do the work, produce the artifact, preserve provenance, and learn from the outcome.**

### 2.1 Coworker architecture boundary

```text
                    GLOBAL MOBILITY AIOS
                           DOMAIN TRUTH
                                │
          ┌─────────────────────┼─────────────────────┐
          ▼                     ▼                     ▼
      Mobility              Evidence           Organization OS
       Engine                 System
                                                    │
                                           WorkItem
                                           Blocker
                                           Dependency
                                           HumanActionRequest
                                           HumanAction
                                           ExecutiveDecision
                                           Contribution
                                           Activity
                                                    │
                                                    ▼
                                          AIOS COWORKER
                                                    │
                                         Agent Execution Plane
                                                    │
                    ┌───────────────────────────────┼──────────────┐
                    ▼                               ▼              ▼
                  Files                           Tools        Connectors
                    │                               │              │
             Documents / Drive                    MCP       Email / Calendar
                                                            Slack / Teams
                                                            CRM / HRIS / ATS
                                                    │
                                                    ▼
                                           Finished Deliverable
                                                    │
                                                    ▼
                                           Governed Outcome
                                                    │
                                                    ▼
                                          Learning + Evaluation
```

A future OpenWorker-derived integration is therefore a reference, adapter, or bounded execution
implementation behind AIOS-owned contracts. It does not own WorkItem meaning, Board authority,
legal/evidence conclusions, Activity, or the definition of a successful business outcome.

---

## 3. Internal Learning & Quality Plane

Internal Learning & Quality is a first-class platform capability.

Subject to applicable law, contractual commitments, declared processing purposes, and the
applicable data-use policy, AIOS should be capable of learning from:

```text
Cases
Documents
Evidence
Agent activity
Model outputs
Retrieval results
Professional corrections
Human approvals / rejections
Tool outcomes
Connector-derived context
WorkItems
Blockers
Decisions
Contributions
Activity
User feedback
Workflow outcomes
        │
        ▼
AIOS LEARNING & QUALITY PLANE
        │
        ├── product analytics
        ├── AI evaluations
        ├── regression datasets
        ├── human-correction datasets
        ├── agent-quality analysis
        ├── workflow optimization
        ├── document/OCR improvement
        ├── retrieval improvement
        ├── regulatory-intelligence quality
        ├── organizational intelligence
        ├── prompt/program optimization
        └── permitted internal model training/fine-tuning
```

The intended outcome is:

> **Every permitted interaction should have the potential to make AIOS better.**

### 3.1 Human corrections as learning signals

Professional corrections, overrides, confirmations, review outcomes, and evidence/OCR
corrections should be capable of becoming explicit learning events.

```text
AI prediction
     ↓
professional decision
     ↓
difference
     ↓
Learning Record
```

The same pattern applies to OCR extraction corrections, evidence checklist edits, retrieval
acceptance/rejection, agent rework, and workflow overrides.

A future controlled pipeline is:

```text
Operational interaction
        ↓
Outcome
        ↓
Human correction / confirmation
        ↓
Learning Record
        ↓
Evaluation Corpus
        ↓
Training Candidate Corpus
        ↓
Permitted Training Corpus
        ↓
Model / prompt / program improvement
        ↓
Shadow evaluation
        ↓
Promptfoo + deterministic regression
        ↓
Controlled promotion
```

### 3.2 Keep three learning uses distinct

**Level 1 — operational intelligence**

- workflow bottlenecks;
- agent performance;
- professional workload;
- case friction;
- evidence gaps;
- source quality;
- user behaviour;
- department performance.

**Level 2 — evaluation and quality improvement**

- professional agreement/correction rates;
- material correction rate;
- hallucination and retrieval quality;
- OCR correction rate;
- agent outcome quality;
- tool failure rates;
- legal-certainty regressions.

**Level 3 — internal training and optimization**

- fine-tuning and specialized models;
- prompt/program optimization;
- ranking/retrieval improvement;
- document classifiers;
- workflow prediction;
- agent planning improvements.

Separating these uses is necessary for model/data lineage, evaluation integrity, and compliance.

---

## 4. Training and learning lineage

AIOS should eventually be able to answer:

- Which information contributed to this model or program version?
- Which model produced this result?
- Which training/evaluation corpus was used?
- Which professional corrections were included?
- What was the jurisdiction/effective-date cutoff?
- Which evaluation corpus was held out?
- Which model/program version replaced which one?
- Why was it promoted?

Conceptually:

```text
TrainingDataset
    dataset_id
    purpose
    creation_date
    provenance
    source_categories
    jurisdictions
    permitted_usages
    model_targets
    transformation_history

ModelVersion
    base_model
    training_dataset_ids
    training_configuration
    evaluation_dataset_ids
    benchmark_results
    promotion_decision
```

Training lineage is both an engineering quality control and potential regulatory/compliance
evidence. It must not be confused with legal/evidence provenance or OrganizationActivity.

---

## 5. Cockpit Quality Intelligence direction

Learning and quality should eventually surface in the **Global Mobility AIOS Cockpit** rather
than remain only an ML-engineering facility.

Potential future measures include:

```text
AIOS Quality Intelligence
────────────────────────────────────
Professional agreement rate
Human correction rate
Material correction rate

Evidence extraction accuracy
OCR correction rate
Retrieval citation acceptance

Qualification-mapping disagreement
Occupation-assessment agreement
Regulatory extraction agreement

Average human intervention per case
Agent completion success
Agent rework rate

Most corrected AI capability
Most common evidence ambiguity
Largest workflow bottleneck
Weakest jurisdiction coverage

Model performance by capability
Model performance by jurisdiction
Model cost / successful outcome

Human effort saved
Human effort still required
```

The Cockpit should eventually help the Board ask where AIOS is weak, where humans repeatedly
correct agents, which models/workflows perform best, and what should improve next. Durable
WorkItems, Decisions, Blockers, Contributions and curated Activity remain organizational records;
quality telemetry does not replace them.

---

## 6. EU compliance direction for learning

The product objective is **compliance-aware lawful learning**, not indiscriminate reuse of data
and not automatic abandonment of useful learning.

The engineering direction is:

```text
AIOS learning objective
        ↓
explicit processing purpose
        ↓
appropriate lawful basis / compatibility assessment
        ↓
applicable treatment of relevant data categories
        ↓
transparent policy and notices
        ↓
minimum-necessary processing + retention/security controls
        ↓
traceable evaluation / training use
```

GDPR principles require lawfulness, fairness, transparency, purpose limitation, data
minimisation, and other safeguards. New or secondary processing cannot be treated as an undefined
future use. Where personal data is involved, the applicable lawful basis and purpose/compatibility
analysis must be established before the corresponding production processing regime is enabled.

Global mobility cases may contain special-category personal data. Such data requires an
applicable Article 9 condition and any other required safeguards before a learning/evaluation or
training use is permitted.

The EDPB's Opinion 28/2024 addresses personal data in AI model development/deployment, including
anonymisation and legitimate-interest analysis. It does not create a blanket permission or blanket
prohibition; production use requires case-specific compliance analysis.

### 6.1 Data usage policy metadata direction

A future AIOS data-governance layer should be capable of representing:

```text
AIOSDataUsagePolicy

service_operation                  allowed / conditional / excluded
quality_assurance                  allowed / conditional / excluded
internal_analytics                 allowed / conditional / excluded
agent_evaluation                   allowed / conditional / excluded
safety_evaluation                  allowed / conditional / excluded
workflow_improvement               allowed / conditional / excluded
retrieval_improvement              allowed / conditional / excluded
document_intelligence_improvement  allowed / conditional / excluded
prompt_program_improvement         allowed / conditional / excluded
internal_model_training            allowed / conditional / excluded
human_quality_review               allowed / conditional / excluded

processing_purpose                 [...]
lawful_basis                       [...]
tenant                             ...
provenance                         ...
sensitivity_class                  ...
retention_class                    ...
training_lineage                   ...
```

This metadata exists to make permitted learning traceable and enforceable, not to imply that every
record is trainable.

### 6.2 EU AI Act / GPAI boundary

Using or fine-tuning a third-party model does not by itself establish that AIOS is a provider of a
general-purpose AI model. Current European Commission guidance focuses on whether modifications
are significant enough for the modifier to become the provider of the resulting GPAI model.

If AIOS later develops or places its own GPAI model on the Union market, additional provider
obligations may apply. Current Commission guidance states that GPAI provider obligations entered
into application on 2 August 2025 and Commission enforcement powers apply from 2 August 2026.
The current public-summary template also requires disclosure of whether training included data
collected through user interactions with the provider's services/products.

This is another reason to build training-data lineage early.

**This section is an engineering/compliance architecture direction, not legal advice or a final
lawful-basis determination for any production processing purpose.** Legal/privacy review remains a
required gate before a concrete learning/training processing regime is enabled.

---

## 7. Updated platform-evolution waves

### Wave 0 — architecture and governance — COMPLETE

Established in V1 and extended by V1.1:

- Technology Radar and candidate-evaluation contract;
- third-party adoption principles;
- provider-neutral adapter rule;
- semantic sovereignty;
- Internal Learning & Quality Principle;
- training-lineage direction;
- OpenWorker / AIOS Coworker architecture;
- EU processing-purpose architecture.

**No runtime dependency is required by this checkpoint.**

### Wave 1 — low-blast-radius quality foundation

- Promptfoo;
- OpenTelemetry;
- ClamAV.

### Wave 2 — document + privacy intelligence

```text
Document
   ↓
ClamAV
   ↓
Docling
   ↓
OCR providers
   ↓
AIOSDocumentArtifact
   ↓
Presidio / Privacy Gateway
   ↓
Evidence
   ↓
Learning signals
```

Candidates: Docling, PaddleOCR, Unlimited-OCR, Presidio.

### Wave 3 — regulatory intelligence monitoring

```text
official source
        ↓
urlwatch / monitoring adapter
        ↓
change detection
        ↓
RegulatoryChange candidate
        ↓
AI analysis
        ↓
human/source review
        ↓
VerifiedRule
```

Never `website changed → law automatically changed`.

### Wave 4 — AI runtime + retrieval + quality

- Pydantic AI;
- pgvector vs Qdrant;
- DSPy;
- Langfuse;
- OpenTelemetry;
- Promptfoo;
- initial AIOS Learning & Evaluation Plane.

### Wave 5 — AIOS Coworker + organization execution

- OpenWorker reference / controlled pilot;
- Temporal;
- OpenFGA.

Target capability:

```text
AIOS Coworker
        +
durable execution
        +
tools/connectors
        +
organizational authority
        +
finished deliverables
        +
learning from outcomes
```

AIOS remains the organization. OpenWorker is a reference/potential adapter, not the semantic
organization model.

### Wave 6 — professional output

- Gotenberg;
- Typst;
- EU DSS.

Target outputs include Mobility Assessments, Employer Packs, Evidence Registers, Case
Chronologies, Risk Registers, Board Briefs, Qualification Memos, professional reports, and
source-provenance appendices.

---

## 8. Product-roadmap relationship

Technology Radar V1.1 does **not** interrupt Phase 13.16.8.

```text
13.16.8  Professional / Operator experience
        ↓
13.16.9  Evidence + provenance UX
        ↓
13.16.10 Responsive/accessibility/integrated acceptance
        ↓
13.17    Genuine external-human acceptance
        ↓
measured Platform Evolution pilots
        ↓
AIOS Coworker / Learning Plane / Document Intelligence /
Agent Runtime / Retrieval / Durable Execution / Professional Output
```

13.16.8 should leave an intentional future UX seam for AIOS Coworker because the Professional
workspace is a likely first bounded product surface, but it must not absorb the Coworker runtime
or speculative dependencies into the current slice.

Phase 14 remains a scale programme for a validated product. Technology Radar winners such as
Temporal, OpenTelemetry, the selected retrieval architecture, and OpenFGA may eventually enter
through Phase 14 when measured needs justify them. AIOS Coworker is a product capability and may
begin as a bounded Platform Evolution pilot after Phase 13 acceptance rather than being reduced
to Phase 14 infrastructure.

---

## 9. Permanent architecture principles

1. **AIOS Semantic Sovereignty** — third parties implement capabilities; AIOS owns meaning.
2. **Internal Learning & Quality** — permitted operational information should improve service,
   evaluation, organizational intelligence and AI capability where appropriate.
3. **Finished Work over Chat Alone** — agents should increasingly produce governed outcomes and
   artifacts, not only instructions.
4. **Human Corrections Are Learning Assets** — corrections, overrides, approvals and rejections
   are valuable quality signals when their reuse is permitted.
5. **Training Lineage** — AIOS should be able to establish which datasets, transformations,
   evaluations and decisions contributed to promoted model/program versions.
6. **Evidence Remains Evidence** — OCR is not truth; retrieval is not truth; model output is not
   legal truth; source change is not a VerifiedRule; signature validity is not legal acceptance.
7. **Organization Semantics Remain AIOS-owned** — Temporal history is not Activity; an OpenWorker
   task is not a WorkItem; a Langfuse trace is not AuditLog; a Promptfoo result is not production
   authority.
8. **Duplicate-framework restraint** — retain useful candidates during evaluation, then prefer one
   winner for the same core capability unless measured requirements justify plurality.
9. **EU Compliance Enables the Lawful Learning Loop** — define purposes, applicable legal bases,
   data-use controls, safeguards, lineage and transparency so that lawful internal learning remains
   possible without making every operational record trainable by default.

---

## 10. Standard candidate-evaluation contract

Every candidate must still be evaluated on:

### Domain correctness
- preserves AIOS semantics;
- does not force framework state into domain records;
- provider output remains distinguishable from authoritative AIOS state.

### Safety/governance
- cannot bypass authorization, evidence, certification, publication, or human-review gates;
- supports least privilege;
- failures cannot silently become successful business transitions.

### Technical quality
- accuracy/recall where applicable;
- latency/throughput;
- determinism;
- failure behavior;
- observability;
- CPU/GPU/memory;
- upgrade/reproducibility.

### Operational fit
- self-hosting/deployment;
- backup/restore;
- disaster recovery;
- data residency;
- tenancy;
- security updates;
- monitoring and supportability.

### Learning/data-use fit
- processing purpose and allowed use categories;
- minimum-necessary data flow;
- special-category handling where relevant;
- evaluation/training lineage;
- deletion/retention behavior;
- separation of telemetry, learning records, organizational Activity and legal/evidence provenance.

### Exit cost
- can be removed without rewriting domain services;
- external IDs are mapped, not semantic primary keys;
- data export/rebuild path exists;
- alternative providers can be benchmarked behind the same AIOS meaning.

Exit cost remains a first-class selection criterion.

---

## 11. External references reverified for V1.1

These references support time-sensitive factual/compliance statements in this checkpoint and must
be reverified again before production adoption or a concrete legal processing decision:

- OpenWorker (`andrewyng/openworker`): https://github.com/andrewyng/openworker
- European Commission — GDPR principles: https://commission.europa.eu/law/law-topic/data-protection/information-business-and-organisations/principles-gdpr_en
- European Commission — legal grounds / special categories: https://commission.europa.eu/law/law-topic/data-protection/information-business-and-organisations/legal-grounds-processing-data_en
- EDPB Opinion 28/2024 — AI models and personal data: https://www.edpb.europa.eu/documents/opinion-of-the-board-art-64/opinion-282024-on-certain-data-protection-aspects-related-to_en
- European Commission — GPAI provider guidelines: https://digital-strategy.ec.europa.eu/en/policies/guidelines-gpai-providers
- European Commission — GPAI training-content summary template: https://digital-strategy.ec.europa.eu/en/faqs/template-general-purpose-ai-model-providers-summarise-their-training-content

License, maturity, security, data-flow, and regulatory metadata must be reverified against canonical
sources immediately before any implementation or production decision.

---

## 12. Strategic end state

```text
                         GLOBAL MOBILITY AIOS
                                 │
                         GOVERNED DOMAIN TRUTH
                                 │
     ┌───────────────────────────┼──────────────────────────┐
     │                           │                          │
     ▼                           ▼                          ▼
Mobility Intelligence     Evidence Intelligence       Organization OS
     │                           │                          │
Official Sources               Documents                  WorkItems
Verified Rules                 Evidence                   Blockers
Pathways                       Provenance                 Decisions
Assessments                    Certification              Human Actions
                                                           Activity
                                                           Contributions
     │                           │                          │
     └───────────────────────────┼──────────────────────────┘
                                 ▼
                           AI INTELLIGENCE
                                 │
                    Typed models / agents / tools
                                 │
                        Semantic retrieval
                                 │
                           AIOS COWORKER
                                 │
             ┌───────────────────┼─────────────────────┐
             ▼                   ▼                     ▼
          Files              Connectors             Tools/MCP
             │                   │                     │
             └───────────────────┼─────────────────────┘
                                 ▼
                       FINISHED PROFESSIONAL WORK
                                 │
                                 ▼
                         REAL-WORLD OUTCOMES
                                 │
                                 ▼
                     AIOS LEARNING & QUALITY PLANE
                                 │
          ┌──────────────────────┼─────────────────────────┐
          ▼                      ▼                         ▼
     Evaluation             Analytics                  Training
          │                      │                         │
          └──────────────────────┼─────────────────────────┘
                                 ▼
                         BETTER GLOBAL AIOS
                                 │
                                 ▼
                       Cockpit Intelligence
```

Long-term flywheel:

> **More work → more outcomes → more corrections → more intelligence → better permitted training
> and optimization → better AIOS → higher-quality work.**
