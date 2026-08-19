# Global Mobility AIOS — Technology Radar V1.1

**Status:** ACTIVE CANONICAL V1.1 — platform-evolution architecture / evaluation checkpoint  
**Date:** 2026-08-19  
**Accepted product baseline:** Phase 13.16.10 COMPLETE / PASS at `b8393d0b6bdaf02c958bb151b4909b5b82fd0d09`  
**Active product slice:** Phase 13.17 — owner-led human acceptance, IN PROGRESS / PAUSED BY EVALUATOR  
**Runtime impact of this architecture update:** none  
**Human-like organization architecture:** [HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1.md](HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1.md)  
**Historical predecessor:** [TECHNOLOGY_RADAR_V1.md](TECHNOLOGY_RADAR_V1.md) remains frozen historical evidence

Technology Radar V1.1 identifies external/open-source technologies and architecture patterns that can materially strengthen Global Mobility AIOS without allowing third-party frameworks to define AIOS domain semantics, organizational authority, evidence truth, legal status, certification/publication state, or business outcomes.

The Radar is not a dependency manifest. Inclusion means a technology is worth evaluating for a defined AIOS capability. Runtime adoption still requires a bounded implementation slice, benchmark, architecture boundary, operational/security/data-flow review, acceptance contract, rollback plan, and exit strategy.

The 2026-08-19 update expands V1.1 from a provider-neutral capability radar into a platform-evolution model for a **human-like, high-performance AI organization**. It preserves the accepted Phase 13 product sequence and the already-started bounded Radar pilots.

---

## 1. Core architecture principle — AIOS Semantic Sovereignty

> **Third-party infrastructure may implement, accelerate, execute, retrieve, parse, monitor, observe, scan, render, evaluate, optimize, coordinate, remember, connect, or otherwise support an AIOS-defined capability, but it may never become authoritative for AIOS domain meaning, legal status, evidence state, certification state, publication state, human-review requirements, organizational authority, Mission/WorkItem semantics, ExecutiveDecision semantics, Contribution semantics, OrganizationActivity semantics, or business outcomes.**

Preferred architecture:

```text
AIOS domain / Organization OS
        ↓
AIOS-owned capability contract
        ↓
AIOS adapter / Execution Broker
        ↓
external technology / runtime
```

Provider output remains distinguishable from authoritative AIOS state.

Permanent companion principles:

> **Human in interaction. Machine-like in reliability.**

> **Natural interaction, deterministic accountability.**

> **Team outcomes over agent competition.**

> **Activity is broad; authority is narrow.**

> **Autonomy is earned and measured through quality, SLA performance, governed outcomes, and bounded authority.**

---

## 2. Updated Technology Fit Tiers

### 2.1 A+ — strongest strategic fit

| Technology | Intended AIOS capability | Current direction |
|---|---|---|
| **Docling** | document normalization / structured document intelligence | ADOPT / EARLY PILOT — Wave 2 pilot started |
| **Presidio** | sensitive-data processing / Privacy Gateway | ADOPT / EARLY PILOT |
| **Promptfoo** | AI regression, adversarial and quality evaluation | ADOPT EARLY — Wave 1 pilot complete |
| **OpenTelemetry** | vendor-neutral telemetry foundation | ADOPT EARLY — Wave 1 pilot complete |
| **urlwatch** | official-source change monitoring | ADOPT / EARLY PILOT |
| **ClamAV** | untrusted-upload quarantine / malware scanning | ADOPT — Wave 1 pilot complete |
| **Munder Difflin (`chaitanyagiri/munder-difflin`)** | AIOS Agent Organization Fabric / human-like multi-agent coordination / Live Organization reference | **STRATEGIC ARCHITECTURE REFERENCE / CONTROLLED PILOT-RESEARCH** |
| **OpenWorker (`andrewyng/openworker`)** | AIOS Coworker / finished-work execution / tools-connectors-deliverables reference | **STRATEGIC REFERENCE / CONTROLLED PILOT** |
| **Temporal** | durable timers, waits, retries, signals and resumption | STRATEGIC PILOT |
| **OpenFGA** | fine-grained relationship authorization | STRATEGIC PILOT |

Munder Difflin and OpenWorker are **not competing organization frameworks inside AIOS**. Their strongest capabilities are complementary and may be composed behind AIOS-owned contracts when measured results justify it.

### 2.2 A — specialist technologies

| Technology | Intended AIOS role | Current classification |
|---|---|---|
| **pgvector** | governed semantic retrieval | BENCHMARK |
| **Qdrant** | dedicated semantic retrieval alternative | BENCHMARK against pgvector |
| **Pydantic AI** | typed production AI/agent runtime candidate | PILOT |
| **Langfuse** | LLM/agent engineering observability behind OpenTelemetry | PILOT behind OpenTelemetry |
| **PaddleOCR** | OCR/document extraction | BENCHMARK |
| **Unlimited-OCR** | advanced OCR/VLM extraction | BENCHMARK |
| **DSPy** | offline AI-program optimization | RESEARCH / PILOT |
| **Gotenberg** | commodity PDF/document conversion | ADOPT when output layer requires it |
| **Typst** | premium professional report generation | ADOPT for selected outputs |
| **EU DSS** | EU electronic-signature validation | PREFERRED RESEARCH |

### 2.3 B / conditional technologies

- Fides;
- OpenLineage;
- OPA;
- OpenFeature;
- Haystack;
- MarkItDown.

The cleanup rule remains:

> **Do not remove a candidate merely because another technology is attractive. Remove it only when another candidate demonstrably wins the same capability and maintaining both provides no measurable benefit.**

Examples:

- pgvector wins the AIOS retrieval benchmark → Qdrant may leave the active radar;
- Docling fully satisfies lightweight conversion → MarkItDown may leave;
- Pydantic AI + AIOS-native retrieval/orchestration satisfies production requirements → Haystack may leave.

---

## 3. Responsibility separation

```text
Munder Difflin  = human-like multi-agent organization / coordination / visual organization reference
OpenWorker      = finished-work / Coworker execution reference
AIOS Execution Broker = AIOS-owned capability selection and composition
Pydantic AI     = typed production agent-runtime candidate
DSPy            = offline model/program optimization
Temporal        = execution durability
OpenFGA         = relationship authorization
OpenTelemetry   = neutral engineering telemetry
Langfuse        = LLM/agent engineering observability behind OTel
Promptfoo       = evaluation / regression
```

No external runtime should become the semantic center of Global Mobility AIOS.

---

## 4. Munder Difflin — A+ Agent Organization reference

Munder Difflin is classified as:

```text
Fit:            A+
Classification: STRATEGIC ARCHITECTURE REFERENCE / CONTROLLED PILOT-RESEARCH
AIOS capability: Agent Organization Fabric / Live Organization
```

Current documented concepts that are particularly relevant to AIOS include:

- persistent agent identities;
- real agent processes backed by multiple providers/CLIs;
- agent-to-agent mailboxes and routed messages;
- conversation/thread behavior;
- persistent agent memory;
- shared working-memory / blackboard patterns;
- supervisor/orchestrator patterns;
- dependency-aware tasks;
- scheduled missions and heartbeat;
- human approval/intervention paths;
- agent budgets and cost accounting;
- OpenTelemetry observability;
- progressive steer → constrain → stop circuit breaking;
- skills / capability discovery;
- live fleet/organization visualization;
- direct human interaction with individual agents.

AIOS should adapt these capabilities to its stronger domain model rather than copy Munder Difflin's persistence or authority semantics.

### 4.1 Communication is organization activity

The canonical AIOS relationship is:

```text
AgentMessage ⊂ OrganizationActivity
```

Human-like conversation is legitimate organizational activity: questions, clarifications, suggestions, requests, handoffs, warnings, peer review, acknowledgements, disagreements, and routine coordination may all be recorded as organizational activity.

But:

```text
conversation ≠ authority
message ≠ ExecutiveDecision
memory ≠ Evidence
memory ≠ VerifiedRule
message ≠ certification/publication
provider event log ≠ canonical AIOS OrganizationActivity
```

Provider messages/events may be normalized into AIOS-owned `OrganizationActivity`. Provider storage itself never becomes the authoritative semantic history.

### 4.2 Munder storage boundary

Munder Difflin's local file/git hive is appropriate for its desktop-agent model. AIOS does not replace its authoritative database/domain model with that persistence pattern.

AIOS remains authoritative for Mission, WorkItem, Dependency, Blocker, AgentConversation, OrganizationActivity, HumanActionRequest, HumanAction, ExecutiveDecision, Contribution, evidence, certification, publication, case state, and authority.

---

## 5. OpenWorker — A+ AIOS Coworker / finished-work reference

OpenWorker is classified as:

```text
Fit:            A+
Classification: STRATEGIC REFERENCE / CONTROLLED PILOT
AIOS capability: Finished-Work Execution / AIOS Coworker
```

OpenWorker strongly informs:

- outcome-first UX;
- documents/reports/spreadsheets/web artifacts as finished deliverables;
- local files and terminal;
- MCP;
- connectors and external app actions;
- scheduled work;
- model/provider portability;
- approval before consequential writes/sends/commands;
- unattended-work approval inboxes;
- local-first execution patterns.

Candidate AIOS Coworker outcomes include:

- employer mobility packs;
- professional case briefs;
- missing-evidence analysis;
- client communications;
- qualification memos;
- evidence registers;
- Board briefings;
- regulatory-change comparisons;
- case chronologies;
- authority-correspondence analysis;
- calendar/email actions;
- premium professional reports.

OpenWorker must not own Mission, WorkItem, authority, evidence state, certification, publication, Decision, Contribution, OrganizationActivity, or business-outcome semantics.

---

## 6. AIOS Agent Organization Fabric

The long-term architecture is:

```text
AIOS DOMAIN TRUTH
                        │
     ┌──────────────────┼──────────────────┐
     ▼                  ▼                  ▼
Mobility Engine     Evidence System    Organization OS
                                            │
                                      Positions
                                      Departments
                                      Missions
                                      WorkItems
                                      Dependencies
                                      Blockers
                                      Human Actions
                                      Decisions
                                      Contributions
                                      Activity
                                            │
                                            ▼
                                  AGENT ORGANIZATION FABRIC
                                            │
                    ┌───────────────────────┼─────────────────────┐
                    ▼                       ▼                     ▼
             Orchestration            Communication            Memory
                    │                       │                     │
             CEO / executives           Messages             Session
             delegation                 Conversations         Position
             squads                     Handoffs              Department
             scheduling                 Collaboration         Organization
                    │                       │                     │
                    └───────────────────────┼─────────────────────┘
                                            ▼
                                   AIOS EXECUTION BROKER
                                            │
                     ┌──────────────────────┼─────────────────────┐
                     ▼                      ▼                     ▼
               Munder-style           OpenWorker             AIOS-native
               agent execution        finished work          typed/deterministic
                     │                      │                     │
                     └──────────────────────┼─────────────────────┘
                                            ▼
                                      Finished Work
                                            │
                                            ▼
                                  Quality / SLA / Authority
                                            │
                                            ▼
                                      Governed Outcome
                                            │
                                            ▼
                                  Learning & Quality Plane
```

---

## 7. AIOS Execution Broker

The AIOS-owned Execution Broker determines which capabilities should perform or cooperate on a Mission.

Candidate routing criteria include:

- capability fit;
- deterministic authority;
- SLA urgency;
- workload/capacity;
- jurisdiction/context;
- expected quality;
- historical success;
- human correction/rework rate;
- evidence requirements;
- required human/professional gates;
- tool/connector availability;
- model/runtime suitability;
- cost;
- privacy/data-use constraints;
- provider health;
- fallback/recovery availability.

The objective is not framework loyalty. The objective is **the best governed result**.

One Mission may therefore use Munder-inspired collaboration, AIOS-native domain services, an OpenWorker finished-work capability, a specialist model runtime, and deterministic services together.

---

## 8. Missions, Dynamic Squads and Definition of Done

AIOS should introduce **Mission** as an outcome-level organizational concept above WorkItems.

```text
Mission
  objective
  owner_position
  participants / Dynamic Squad
  priority / service class
  success definition
  SLA
  KPIs
  authority boundary
  risk
  status
  outcome
```

A Mission may create multiple WorkItems, conversations, dependencies, artifacts and decisions across departments.

Temporary **Dynamic Squads** allow cross-department collaboration without destroying the permanent organization chart.

Every material Mission should have a **Definition of Done** appropriate to its outcome. Possible requirements include completed deliverables, current/authoritative sources, evidence/provenance completeness, explicit uncertainty, required review, valid output format, authorized external action, SLA status, and outcome/learning capture.

---

## 9. Persona + deterministic authority

Agents should possess rich organizational identities:

```text
IDENTITY
CEO — Global Mobility AIOS

REPORTS TO
Human Board

RESPONSIBILITIES
...

CURRENT AUTHORITY
...

DELEGATED CAPABILITIES
...

HUMAN / BOARD REQUIRED
...

PROHIBITED
...
```

Therefore:

```text
rich organizational persona
        +
deterministic position / delegation contract
        =
governed organizational agent
```

Persona informs reasoning, priorities, communication and delegation strategy. When persona and deterministic runtime authority disagree, **deterministic authority wins**. A model cannot obtain authority by claiming a title.

---

## 10. Distributed human review and proportional escalation

Not every uncertainty belongs in Board Room.

The canonical escalation principle is:

> **Resolve autonomously where permitted. Collaborate before escalating. Escalate to the lowest level with the necessary expertise or authority. Reserve Board attention for genuinely Board-level matters.**

```text
Issue
 │
 ├─ agent can resolve → resolve
 ├─ colleague has expertise → collaborate
 ├─ department authority required → department lead
 ├─ professional judgement required → Professional / Operator
 ├─ personal fact required → Mobility User
 ├─ executive authority required → relevant Executive / CEO
 └─ reserved/material organization authority → Human Owner / Board
```

Architecture principle:

> **Distributed human review + centralized Cockpit oversight.**

Board Room remains a reserved-authority module inside Cockpit, not a generic review queue.

---

## 11. Human Owner privileged command

Natural language should become a first-class human organizational command interface.

Conceptually:

```text
GLOBAL MOBILITY AIOS COCKPIT

OWNER COMMAND
────────────────────────────────

> Ask the CEO why Austria cases are taking longer this week,
  have Operations investigate, and prepare a recovery plan.
```

Authority comes from the authenticated Human Owner identity and deterministic AIOS governance, not the wording of the prompt.

For high-impact commands AIOS may show an interpretation preview describing affected agents/capabilities, unaffected scope, authority source and expected consequence before execution.

The preview protects against language ambiguity; it does not create or remove Owner authority.

---

## 12. SLA, KPI and OKR operating model

Human-like collaboration must remain measurable and accountable.

### SLA direction

Mission/WorkItem SLA semantics may include:

```text
service_class
acknowledge_by
start_by
respond_by
complete_by
review_by
freshness_requirement
escalation_after
maximum_blocker_age
retry_policy
```

Suggested classes: Critical, Priority, Standard, Background.

SLA risk should trigger organizational correction—assist, rebalance, reassign, change execution capability—before inappropriate Board escalation.

### KPI direction

AIOS should measure delivery, quality, collaboration, economics, safety/governance, and human-effort outcomes.

Examples:

- Mission completion / SLA attainment / cycle time / blocker age;
- first-pass quality / professional agreement / correction / rework;
- evidence-grounding and provenance completeness;
- collaboration success / unnecessary handoffs / dependency-resolution time;
- cost per successful outcome / cost of rework;
- human effort per outcome;
- human-gate compliance / blocked unauthorized actions;
- false or missed escalation rate.

Individual metrics are diagnostic. **Team/Mission outcome is the primary performance unit.**

### OKR direction

Objectives and Key Results sit above operational KPIs and help CEO/executives direct organization improvement without incentivizing narrow agent competition.

---

## 13. Progressive intervention / circuit breaker

Munder Difflin's progressive intervention concept maps strongly to AIOS.

Target ladder:

```text
NORMAL
  ↓
STEER
  ↓
ASSIST / PEER SUPPORT
  ↓
REASSIGN
  ↓
CONSTRAIN
  ↓
SUSPEND SPECIFIC AGENT / CAPABILITY
  ↓
EXECUTIVE / HUMAN ESCALATION
  ↓
EMERGENCY ORGANIZATION STOP
```

`Pause Organization` remains an emergency governance control for circumstances where continued autonomous execution itself is materially unsafe—not a generic troubleshooting fallback.

---

## 14. Capability Registry and organizational capacity

AIOS should own a Capability Registry that describes:

- what each position/agent/runtime can do;
- what requires professional/human review;
- what is prohibited;
- current availability/workload;
- recent quality;
- SLA risk;
- cost;
- provider/runtime health.

COO/CEO and the Execution Broker can use these signals to route or rebalance work before SLA failure.

Provider-specific skills register behind AIOS-owned capabilities; provider skill names do not become domain semantics.

---

## 15. Organizational memory and relationships

Memory scopes should distinguish:

```text
Session → Position → Department → Organization
```

Useful organizational experience may include successful interventions, recurring problems, collaboration preferences, source-layout knowledge, correction patterns and routing lessons.

But:

```text
memory ≠ evidence
memory ≠ VerifiedRule
memory ≠ certification
memory ≠ legal truth
```

AIOS may also maintain structural and learned collaboration relationships for routing and organizational intelligence while keeping formal reporting/authority relationships deterministic.

---

## 16. Live Organization / Cockpit direction

Munder Difflin's live office is valuable as an **information architecture concept**, not as a visual skin to copy.

Global Mobility AIOS should translate it into its premium enterprise identity:

- deep navy / graphite + warm ivory;
- editorial serif + operational sans;
- restrained motion;
- sophisticated spatial organization;
- no pixel/SNES imitation.

Potential Live Organization capabilities:

- department/position map;
- visible working/waiting/blocked/collaborating states;
- animated delegation and conversation flows;
- active Dynamic Squads;
- Mission movement;
- SLA risk and workload/capacity;
- cost/performance indicators;
- click a position to inspect work, conversations, authority, performance and permitted memory;
- natural direct conversation with CEO/executives/specialists.

The animation must communicate real organization state rather than serve as decoration.

Cockpit then compresses the large activity stream into notable/material/Owner/Board attention while keeping routine organizational activity inspectable.

---

## 17. Internal Learning & Quality Principle

> **Subject to applicable law, contractual commitments, declared processing purposes, required safeguards, and the applicable data-use policy, AIOS should maximize lawful learning from the work it performs.**

Potential signals include cases, documents, evidence, conversations, model responses, plans, tool calls, connector-derived context, retrieval results, professional corrections, Owner redirections, approvals/rejections, WorkItems, Missions, Blockers, Decisions, Contributions, Activity, SLA misses, collaboration outcomes and user feedback.

Three layers remain separate:

1. **Operational Intelligence** — understand organization/work performance.
2. **Evaluation & Quality** — measure models, agents, collaboration and workflows.
3. **Training & Optimization** — use permitted data to improve models, programs, retrieval, routing and workflows.

Training is a first-class architecture concern, but a record valid for operational analytics is not automatically valid for model training.

---

## 18. Human corrections as high-value learning assets

Where permitted:

```text
AI prediction / plan / extraction / recommendation
        ↓
professional / Owner / human decision
        ↓
difference / confirmation
        ↓
Learning Record
        ↓
Evaluation Corpus
        ↓
Training Candidate Dataset
        ↓
Permitted Training Dataset
        ↓
Model / program / routing improvement
        ↓
Shadow evaluation + deterministic regression
        ↓
Controlled promotion
```

This applies to OCR corrections, occupation mapping, evidence checklists, case summaries, agent plans, routing decisions and Board recommendations.

Learning records never rewrite authoritative legal/business records merely to create training data.

---

## 19. Training lineage

AIOS should eventually answer:

- which data/corrections contributed to a model/program;
- which jurisdictions/effective-date cutoff applied;
- what transformations created a dataset;
- which evaluation corpus remained held out;
- which benchmark justified promotion;
- which model/program produced a case result.

Future concepts may include `TrainingDataset`, `ModelVersion`, `LearningRecord`, and `AIOSDataUsagePolicy` with explicit provenance, purpose, allowed/conditional/excluded uses, sensitivity, retention and training lineage.

---

## 20. EU compliance and lawful learning

EU compliance should enable sustainable lawful improvement rather than either indiscriminate reuse or reflexive discarding of useful operational intelligence.

Architecture direction:

```text
learning objective
      ↓
defined processing purpose
      ↓
appropriate lawful basis / compatibility analysis
      ↓
treatment of relevant data categories
      ↓
transparent policy / notices
      ↓
minimum-necessary processing + safeguards + retention
      ↓
traceable analytics / evaluation / training use
```

Where GDPR applies, concrete production learning/evaluation/training involving personal data requires the applicable purpose, legal basis or compatibility analysis, transparency, minimisation, retention/security controls and other required safeguards. Special-category data requires an applicable Article 9 condition and additional safeguards.

The architecture must not assume a single generic Terms clause automatically authorizes every future use.

If AIOS later becomes a provider of a general-purpose AI model under the EU AI Act, applicable GPAI-provider obligations and training-content lineage requirements must be assessed separately.

This Radar is engineering/compliance architecture direction, not a final legal determination for a specific production processing regime.

---

## 21. Updated Platform Evolution waves

These waves describe platform evolution, not automatic installation order.

### Wave 0 — Architecture & governance — COMPLETE

Established/frozen direction includes:

- Radar / candidate-evaluation contract;
- AIOS Semantic Sovereignty;
- provider-neutral adapter rule;
- Internal Learning & Quality;
- training lineage;
- AIOS Coworker / OpenWorker boundary;
- Agent Organization Fabric / Munder Difflin boundary;
- Execution Broker;
- natural interaction + deterministic accountability;
- Activity broad / Authority narrow;
- distributed review / centralized oversight;
- Human Owner Command;
- SLA/KPI/OKR direction.

### Wave 1 — Quality foundation — COMPLETE

- Promptfoo bounded pilot;
- OpenTelemetry bounded pilot;
- ClamAV bounded pilot.

The accepted runtime evidence for these pilots remains in the active CHANGELOG. This architecture update does not represent those tests as rerun.

### Wave 2 — Document & Privacy Intelligence — IN PROGRESS

```text
ClamAV → Docling → OCR providers → AIOSDocumentArtifact → Presidio / Privacy Gateway → Evidence
```

- Docling bounded pilot: **STARTED**;
- Presidio: next queued candidate;
- PaddleOCR / Unlimited-OCR: benchmark candidates.

### Wave 3 — Regulatory Monitoring

`official source → urlwatch/change detector → candidate change → AI analysis → human/source review → VerifiedRule`

Never `website changed → law automatically changed`.

### Wave 4 — AI Runtime, Retrieval & Quality

- Pydantic AI;
- pgvector vs Qdrant;
- DSPy;
- Langfuse behind OTel;
- Promptfoo;
- initial Learning/Evaluation runtime.

### Wave 5A — Organization Semantics Foundation

Define and accept AIOS-owned contracts for:

- Mission;
- AgentConversation;
- conversational/collaborative OrganizationActivity;
- Capability Registry;
- organizational memory scopes;
- AgentRelationship;
- SLA contract;
- KPI / OKR semantics;
- Definition of Done;
- Dynamic Squad;
- Execution Broker contract.

### Wave 5B — Agent Organization Fabric

Munder Difflin is the principal reference/pilot for:

- identity;
- communication;
- conversations;
- memory;
- coordination;
- supervisor patterns;
- scheduling;
- budgets;
- circuit breakers;
- Live Organization event feed.

### Wave 5C — Execution Broker + AIOS Coworker

OpenWorker is the principal reference/pilot for:

- finished deliverables;
- files;
- tools;
- MCP;
- connectors;
- scheduled execution;
- external actions;
- approval handling;
- result return into AIOS Missions.

Munder/OpenWorker/AIOS-native capabilities may cooperate through the Broker.

### Wave 5D — Live Organization / Cockpit

Premium AIOS-native visualization for:

- positions;
- work;
- conversations;
- delegations;
- squads;
- SLA risk;
- workload/capacity;
- performance/cost;
- progressive intervention.

### Wave 5E — Organizational Learning & Optimization

Use permitted outcomes to improve:

- routing;
- collaboration;
- capability/runtime selection;
- SLA performance;
- team composition;
- prompts/programs;
- capacity decisions.

### Wave 6 — Professional Output

- Gotenberg;
- Typst;
- EU DSS;
- premium Mobility Assessments, Employer Packs, Evidence Registers, Case Chronologies, Risk Registers, Board Briefs, Qualification Memos and provenance appendices.

### Continuous — Learning & Quality Plane

Evaluation, correction learning, organization analytics, training lineage, Cockpit Quality Intelligence and permitted model/program improvement are continuous capabilities rather than a one-time wave.

---

## 22. Relationship to the current product roadmap

Technology Radar V1.1 must **not** interrupt Phase 13.17 owner-led human acceptance or erase its findings.

```text
13.16.8  Professional / Operator experience                   COMPLETE
        ↓
13.16.9  Evidence + provenance UX                             COMPLETE
        ↓
13.16.10 Responsive/accessibility/integrated acceptance       COMPLETE
        ↓
13.17    Owner-led human acceptance                           IN PROGRESS / PAUSED
        ↓
Final Phase 13 disposition
        ↓
measured Platform Evolution pilots / Phase 14 when gated
```

Current Phase 13.17 evidence is genuine human-use evidence but **not independent third-party validation** because the current evaluator is the product Owner. Existing O-/P- findings remain unresolved until corrected and retested.

Further Radar pilots may proceed only when they do not displace the active product acceptance sequence or compromise its evidence.

---

## 23. Permanent Technology Radar principles

1. **AIOS Semantic Sovereignty** — third parties implement capabilities; AIOS defines their meaning.
2. **Human-Like Organization** — agents communicate and collaborate naturally rather than behaving as isolated endpoints.
3. **Natural Interaction, Deterministic Accountability** — human-like behavior sits on deterministic authority, evidence and performance contracts.
4. **Activity Is Broad; Authority Is Narrow** — communication may be OrganizationActivity without becoming a Decision or legal/evidence truth.
5. **Persona + Authority** — persona informs behavior; deterministic runtime contracts define power.
6. **Human Privileged Command** — authenticated humans may exercise their existing authority through natural language.
7. **Distributed Review, Centralized Oversight** — review occurs where work belongs; material oversight converges in Cockpit.
8. **Team Outcomes over Agent Competition** — optimize Mission/business outcomes, not framework or agent leaderboards.
9. **Finished Work over Chat Alone** — agents increasingly produce real deliverables/actions.
10. **SLA/KPI/OKR Discipline** — human-like organization remains measurable and accountable.
11. **Progressive Intervention** — steer/assist/reassign/constrain/suspend before inappropriate global pause/escalation.
12. **Internal Learning & Quality** — lawful operational experience should continuously improve AIOS.
13. **Human Corrections Are Learning Assets** — corrections and redirections are high-value evaluation/training signals where permitted.
14. **Training Lineage** — AIOS should know what data/evaluations contributed to improved models/programs.
15. **Evidence Remains Evidence** — OCR, retrieval, memory, conversation and model output cannot silently become legal/evidence truth.
16. **Organization Semantics Stay AIOS-owned** — Munder messages, OpenWorker tasks, Temporal histories and telemetry traces do not replace AIOS semantic records.
17. **Outcome-Based Provider Composition** — complementary providers may cooperate when measured result quality justifies it.
18. **Duplicate-Framework Restraint** — benchmark genuine duplicates and eventually prefer a primary winner unless measured needs justify plurality.
19. **EU Compliance Enables the Learning Loop** — purpose, legal basis/compatibility, safeguards, transparency and lineage make lawful learning sustainable.

---

## 24. Standard candidate-evaluation contract

Every candidate must still be evaluated on:

### Domain correctness
- preserves AIOS semantics;
- does not force framework state into domain records;
- provider output remains distinguishable from authoritative AIOS state.

### Organizational fit
- supports AIOS Missions/WorkItems rather than replacing them;
- can participate in AgentConversation/Activity without taking authority;
- fits Capability Registry / Execution Broker contracts;
- supports collaboration without bypassing hierarchy/authority.

### Safety/governance
- cannot bypass authorization, evidence, certification, publication or mandatory human gates;
- supports least privilege;
- failures cannot silently become successful business transitions.

### Performance/quality
- accuracy / task-success where applicable;
- SLA behavior;
- first-pass quality / rework;
- latency / throughput;
- collaboration overhead;
- cost per successful outcome;
- determinism / failure behavior.

### Technical/operational quality
- observability;
- CPU/GPU/memory;
- self-hosting/deployment;
- backup/restore;
- disaster recovery;
- data residency;
- tenancy;
- security updates;
- reproducibility.

### Learning/data-use fit
- processing purpose / allowed use categories;
- minimum-necessary data flow;
- special-category handling where relevant;
- evaluation/training lineage;
- deletion/retention;
- separation of telemetry, learning records, Activity and legal/evidence provenance.

### Exit cost
- removable without rewriting domain services;
- provider IDs mapped, not semantic primary keys;
- export/rebuild path exists;
- alternatives benchmarkable behind the same AIOS meaning.

Exit cost remains a first-class selection criterion.

---

## 25. External references reverified for V1.1

Time-sensitive project/compliance facts must be reverified immediately before implementation or production decisions.

- Munder Difflin (`chaitanyagiri/munder-difflin`): https://github.com/chaitanyagiri/munder-difflin
- OpenWorker (`andrewyng/openworker`): https://github.com/andrewyng/openworker
- European Commission — GDPR principles: https://commission.europa.eu/law/law-topic/data-protection/information-business-and-organisations/principles-gdpr_en
- European Commission — legal grounds / special categories: https://commission.europa.eu/law/law-topic/data-protection/information-business-and-organisations/legal-grounds-processing-data_en
- EDPB Opinion 28/2024 — AI models and personal data: https://www.edpb.europa.eu/documents/opinion-of-the-board-art-64/opinion-282024-on-certain-data-protection-aspects-related-to_en
- European Commission — GPAI provider guidelines: https://digital-strategy.ec.europa.eu/en/policies/guidelines-gpai-providers
- European Commission — GPAI training-content summary template: https://digital-strategy.ec.europa.eu/en/faqs/template-general-purpose-ai-model-providers-summarise-their-training-content

License, maturity, security, data-flow and regulatory metadata must be reverified against canonical sources before runtime adoption.

---

## 26. Target end state

```text
GLOBAL MOBILITY AIOS
                             │
                       DOMAIN TRUTH
                             │
       ┌─────────────────────┼─────────────────────┐
       ▼                     ▼                     ▼
 Mobility Intelligence   Evidence Intelligence   Organization OS
                                                    │
                                              AI Organization
                                                    │
                                   ┌────────────────┼─────────────────┐
                                   ▼                ▼                 ▼
                              Orchestration      Memory         Communication
                                   │                │                 │
                                   └────────────────┼─────────────────┘
                                                    ▼
                                           AIOS Execution Broker
                                                    │
                                  ┌─────────────────┼─────────────────┐
                                  ▼                 ▼                 ▼
                             Munder-style       OpenWorker        AIOS-native
                             coordination       finished work     capabilities
                                  │                 │                 │
                                  └─────────────────┼─────────────────┘
                                                    ▼
                                               Finished Work
                                                    │
                                               Real Outcomes
                                                    │
                                                    ▼
                                         Learning & Quality Plane
                                      ┌─────────────┼─────────────┐
                                      ▼             ▼             ▼
                                  Evaluation     Analytics      Training
                                      │             │             │
                                      └─────────────┼─────────────┘
                                                    ▼
                                             Better AIOS
                                                    │
                                                    ▼
                                          Cockpit Intelligence
                                                    │
                                                    ▼
                                         HUMAN OWNER / BOARD
                                           Privileged Command
```

Long-term flywheel:

> **Work → Outcomes → Corrections → Intelligence → Evaluation → Training → Better AIOS → Better Work.**
