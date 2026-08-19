# Global Mobility AIOS — Active Product & Delivery Roadmap

**Roadmap generation:** V11.2 / Technology Radar V1.1 human-like organization alignment  
**Date:** 2026-08-19  
**Development branch:** `roadmap/global-mobility-aios-v11`  
**Accepted product baseline:** Phase 13.16.10 — Responsive, accessibility, polish, and integrated role acceptance — COMPLETE / PASS at `b8393d0b6bdaf02c958bb151b4909b5b82fd0d09`  
**Active product slice:** Phase 13.17 — owner-led genuine human acceptance — IN PROGRESS / PAUSED BY EVALUATOR  
**Current Technology Radar state:** Wave 1 COMPLETE; Wave 2 IN PROGRESS with Docling bounded pilot started  
**Code migration head:** `0076_organization_position_active_identity`

<!-- CURRENT_MIGRATION_HEAD: 0076_organization_position_active_identity -->

This is the canonical **active strategic and delivery roadmap** for [Global Mobility AIOS](GLOBAL_MOBILITY_AIOS_VISION_V1.md). It is intentionally optimized for current direction, gates, sequence, and architecture. Detailed historical implementation evidence remains in [CHANGELOG.md](CHANGELOG.md), Git history, and the archived pre-`f0688a8` roadmap/changelog snapshots.

---

## 1. Product definition

Global Mobility AIOS is a **governed global mobility intelligence operating system** for the movement of people, talent, families, businesses, and capital across borders.

It is not merely:

- a visa chatbot;
- a study-abroad search product;
- a CRM;
- a document uploader;
- an agent demo;
- a generic admin dashboard;
- or a collection of disconnected automations.

The product combines:

- CRM, intake, identity, consent, and long-lived case continuity;
- universal mobility profiles and goal/constraint context;
- official-source and regulatory intelligence;
- pathway discovery, versioning, comparison, and eligibility reasoning;
- evidence, provenance, document intelligence, cost, risk, and timeline planning;
- appointments, submissions, agency and authority workflow;
- post-arrival, renewal, settlement, residence, citizenship, and global-strategy progression;
- governed agents, executives, departments and position contracts;
- explicit organizational authority and human-review gates;
- durable Missions, WorkItems, Decisions, Blockers, Dependencies, Human Actions, Contributions, Conversations, Activity, and audit state;
- role-specific experiences for Owner/Board, Professionals/Operators, Mobility Users, and future partners/employers;
- an evolving human-like AI organization that collaborates naturally while remaining measurable and accountable.

### North-star mobility lifecycle

```text
Dream / Goal
   ↓
Profile + constraints
   ↓
Country / pathway discovery
   ↓
Eligibility + evidence + risk + cost + timeline comparison
   ↓
Study / Work / Family / Business / Investment / Remote-work move
   ↓
Documents / submissions / appointments / authority decisions / compliance
   ↓
Post-arrival / employment / business operation
   ↓
Renewal / status change / family progression
   ↓
Permanent or long-term residence
   ↓
Citizenship / global mobility strategy
```

The lifecycle is branching, not a forced funnel. Changed facts, failed assumptions, new goals, changing laws, alternate pathways, and different user types remain first-class.

---

## 2. Product surfaces and authority model

The canonical experience split is:

- **Global Mobility AIOS Cockpit** — Owner / Human Board control and organization-intelligence surface;
- **Board Room** — reserved Board authority-execution module inside Cockpit, not the name of the whole control surface;
- **Operations** — Professional / Operator experience;
- **My Mobility** — Mobility User experience;
- `/my-mobility` — non-sensitive orientation/access surface;
- `/portal` — secure token/device-bound personalized client workspace.

Backend authorization is authoritative. Navigation, route visibility, title, prompt wording, model capability, provider role, persona, or UI presence never grants business, legal, publication, certification, submission, or organizational authority.

### Experience direction

The product should feel like premium enterprise software with a distinct AI operating-system identity—not a generic SaaS admin dashboard and not dark sci-fi.

Visual direction remains:

- deep navy / graphite + warm ivory;
- selective editorial serif + operational sans;
- restrained depth/glass;
- premium iconography;
- subtle, meaningful motion;
- luxury-level spacing;
- beautiful information density;
- strong role/context clarity.

The future **Live Organization** experience may borrow Munder Difflin's principle that movement and spatial organization communicate system state, but must be translated into the established premium AIOS visual language rather than copying its pixel/SNES aesthetic.

---

## 3. Permanent governance, evidence, organization and learning invariants

These are product architecture, not optional UX copy.

1. **AIOS Semantic Sovereignty** — third parties implement capabilities; AIOS owns meaning.
2. **Evidence before regulated certainty** — retrieval, OCR, document normalization, memory, conversation, model output, source diffs, or signature validation are not legal truth.
3. **Explicit authority** — authority comes from deterministic contracts and gates, never model confidence, provider roles, titles, or prompts.
4. **Human review remains human review** — required professional, source, certification, publication, Board, or external-action gates cannot be silently automated away.
5. **Distributed review, centralized oversight** — human involvement occurs at the lowest appropriate work/authority surface; material oversight converges in Cockpit.
6. **Board Room is reserved authority** — it is not a generic human-review inbox.
7. **Navigation is not authorization** — frontend visibility never substitutes for backend enforcement.
8. **Provider replacement must remain possible** — provider IDs are mappings, not semantic primary keys.
9. **Truthful unknowns** — absent or mismatched evidence remains unknown/not-established rather than inferred clearance.
10. **Preserved databases are evidence** — never mutate the preserved database merely to produce a demo.
11. **Austria simulation safety remains frozen** — uncertain Austria v4 state must not be promoted into production certainty.
12. **Natural interaction, deterministic accountability** — agents may behave like capable colleagues while deterministic contracts still govern work, authority, evidence and outcomes.
13. **Activity is broad; authority is narrow** — conversational and collaborative messages may be OrganizationActivity without becoming Decisions or regulated truth.
14. **Team outcomes over agent competition** — Mission/business outcomes matter more than internal framework or agent leaderboards.
15. **Autonomy is earned and measured** — quality, SLA performance, correction/rework, evidence grounding and governed outcomes determine how much autonomy is justified.
16. **Finished work over chat alone** — AIOS should increasingly produce real governed artifacts/actions rather than only instructions.
17. **Internal Learning & Quality** — lawful operational experience, corrections and outcomes should improve AIOS where permitted.
18. **Training lineage** — AIOS should know what data, corrections, transformations and evaluations contributed to improved models/programs.

---

## 4. Current accepted product baseline

### Phase 13.16.8 — Professional / Operator experience — COMPLETE / PASS

The existing Operations workspace and native case workspace were refined instead of creating a parallel dashboard. The accepted professional reading order is:

```text
Decision / case context
        ↓
Blockers + uncertainty
        ↓
Governed next actions
        ↓
Supporting evidence + review state
        ↓
Technical provenance / audit detail
```

Current pathway evidence remains conservatively composed around the persisted pathway-comparison decision spine. Historical, unassigned or mismatched evidence remains inspectable but cannot silently support current conclusions.

### Phase 13.16.9 — Evidence and provenance UX — COMPLETE / PASS

A shared presentation grammar distinguishes:

- official source;
- immutable retrieved snapshot;
- certification/review state;
- VerifiedRule;
- pathway evidence;
- case evidence;
- superseded/historical state;
- unresolved gaps.

This layer is presentational and does not create/certify/publish evidence or grant authority.

### Phase 13.16.10 — Integrated responsive/accessibility acceptance — COMPLETE / PASS

Owner/Board, Professional/Operator, Mobility User and secure Portal experiences were accepted across desktop/mobile/keyboard/accessibility states after bounded responsive corrections.

Accepted evidence includes:

- design foundation **28/28 PASS**;
- request/auth regression **4/4 PASS**;
- Next.js 15.2.4 production build **41/41 PASS**;
- complete API regression **811 passed / 5 skipped / 0 failed** carried forward for the frontend-only 13.16.10 boundary;
- responsive/keyboard/Portal browser acceptance PASS;
- preserved `gmai.db` SHA256 `23FC012AF3FA89804A84A9C8DD75C0C68515B23AEF1813CC5460D6D73808CD31` unchanged.

No GitHub CI status should be inferred from these local acceptance records.

---

## 5. Active delivery sequence

| Slice | State | Intent / gate |
|---|---|---|
| **13.16.8** | **COMPLETE / PASS** | Governed Professional / Operator decision workspace |
| **13.16.9** | **COMPLETE / PASS** | Shared evidence/provenance presentation grammar |
| **13.16.10** | **COMPLETE / PASS** | Integrated responsive/accessibility role experience |
| **13.17** | **IN PROGRESS / PAUSED** | Owner-led genuine human acceptance; not independent third-party validation |
| **Final Phase 13 disposition** | **LOCKED** | Only after outstanding human findings are corrected/retested or consciously dispositioned |
| **Phase 14** | **NOT STARTED / DEMAND-GATED** | Scale a validated product; do not redesign around infrastructure prematurely |

### 5.1 Phase 13.17 — owner-led genuine human acceptance

The current evaluator is the product Owner. Therefore the evidence is genuine human-use evidence but **not independent third-party acceptance**.

The evaluation is deliberately scenario-based and avoids telling the evaluator the intended answer before comprehension/discoverability tasks.

The session is currently paused after the first Professional / Operator task. Existing findings remain unresolved evidence rather than being considered fixed because their intended semantics were later explained.

The durable checkpoint is:

- [PHASE_13_17_OWNER_LED_HUMAN_ACCEPTANCE_CHECKPOINT_2026_08_18.md](PHASE_13_17_OWNER_LED_HUMAN_ACCEPTANCE_CHECKPOINT_2026_08_18.md)

Current finding themes include:

- drill-down / traceability from summary counts;
- plain-language evidence and governance terminology;
- clearer powerful-control/emergency-stop semantics;
- better cross-organization diagnosis;
- relationship directionality;
- stronger role/context navigation;
- persistent icon + text navigation labels;
- clearer Professional next actions;
- clearer pathway/context-alignment warnings.

The human-like organization architecture must **use** this evidence, not bypass it.

Resume point: Professional Task 2 / human-review or blocked-claim case, with shorter scenarios and fewer repetitive screenshots.

---

## 6. Technology Radar V1.1 — active platform-evolution architecture

Canonical documents:

- [TECHNOLOGY_RADAR_V1_1.md](TECHNOLOGY_RADAR_V1_1.md)
- [HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1.md](HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1.md)
- [THIRD_PARTY_PLATFORM_ADOPTION_PRINCIPLES.md](THIRD_PARTY_PLATFORM_ADOPTION_PRINCIPLES.md)
- [ADR/0002-provider-neutral-platform-adapters.md](ADR/0002-provider-neutral-platform-adapters.md)

Technology Radar is a **parallel evidence-driven evolution track**. Inclusion is not installation. Runtime adoption requires a bounded slice and acceptance contract.

### 6.1 A+ strategic technologies

| Technology | AIOS role | Direction |
|---|---|---|
| Docling | document normalization / structured understanding | ADOPT / EARLY PILOT — Wave 2 started |
| Presidio | sensitive-data processing / Privacy Gateway | ADOPT / EARLY PILOT |
| Promptfoo | AI regression / safety / quality evaluation | Wave 1 bounded pilot complete |
| OpenTelemetry | vendor-neutral application/AI telemetry | Wave 1 bounded pilot complete |
| urlwatch | official-source change monitoring | ADOPT / EARLY PILOT |
| ClamAV | upload quarantine / malware scanning | Wave 1 bounded pilot complete |
| **Munder Difflin** (`chaitanyagiri/munder-difflin`) | Agent Organization Fabric / human-like coordination / Live Organization reference | **A+ strategic architecture reference / controlled pilot-research** |
| **OpenWorker** (`andrewyng/openworker`) | AIOS Coworker / finished-work / tools-connectors-deliverables reference | **A+ strategic reference / controlled pilot** |
| Temporal | durable execution | strategic pilot |
| OpenFGA | relationship authorization | strategic pilot |

### 6.2 A specialist candidates

- pgvector — governed semantic retrieval benchmark;
- Qdrant — dedicated retrieval alternative benchmarked against pgvector;
- Pydantic AI — typed production AI/agent runtime candidate;
- Langfuse — LLM/agent engineering observability behind OpenTelemetry;
- PaddleOCR — OCR/document extraction benchmark;
- Unlimited-OCR — advanced OCR/VLM benchmark;
- DSPy — offline AI-program optimization;
- Gotenberg — commodity PDF/document conversion;
- Typst — premium professional report generation;
- EU DSS — EU electronic-signature validation research.

### 6.3 Conditional / fallback candidates

Fides, OpenLineage, OPA, OpenFeature, Haystack and MarkItDown remain conditional/fallback candidates.

---

## 7. Human-like Agent Organization architecture

The canonical architecture direction is defined in [HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1.md](HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1.md).

### 7.1 Target organization stack

```text
Human Owner / Board
        ↓
Global Mobility AIOS Cockpit / Owner Command
        ↓
AI CEO
        ↓
Organization OS / Domain Truth
        ↓
Missions + WorkItems + Authority + Evidence
        ↓
Agent Organization Fabric
        ├── communication
        ├── conversations
        ├── coordination
        ├── memory
        ├── Dynamic Squads
        └── organizational relationships
        ↓
AIOS Execution Broker
        ├── Munder-inspired organization/execution capabilities
        ├── OpenWorker finished-work capabilities
        ├── AIOS-native typed agents
        └── deterministic services
        ↓
Finished Work
        ↓
Definition of Done + SLA + quality + evidence + authority gates
        ↓
Governed Outcome
        ↓
Learning & Quality
```

### 7.2 Munder Difflin and OpenWorker cooperate

The architecture does not force a false choice between Munder Difflin and OpenWorker.

- **Munder Difflin** principally informs the human-like multi-agent organization: identity, conversations, mailboxes, memory, orchestration, dependencies, schedules, budgets, circuit breakers, skills and Live Organization.
- **OpenWorker** principally informs finished-work execution: files, artifacts, terminal/tools, MCP, connectors, schedules, model portability, consequential-action approvals and outcome-oriented UX.
- **AIOS Execution Broker** owns capability composition and chooses what best satisfies the Mission based on measured quality, SLA, authority, workload, evidence needs, cost, privacy/data-use and provider health.

> **Results matter more than framework ownership; semantic sovereignty remains non-negotiable.**

### 7.3 AgentMessage / OrganizationActivity

Canonical relationship:

```text
AgentMessage ⊂ OrganizationActivity
```

Routine human-like conversation is legitimate organizational activity. However:

```text
conversation ≠ authority
message ≠ ExecutiveDecision
memory ≠ Evidence
memory ≠ VerifiedRule
provider event log ≠ canonical AIOS Activity automatically
```

Provider messages/events are normalized into AIOS-owned semantic Activity where appropriate.

### 7.4 Missions and Dynamic Squads

**Mission** is the outcome-level organizational concept above WorkItems.

A Mission may create:

- WorkItems;
- conversations;
- dependencies;
- artifacts;
- decisions;
- temporary Dynamic Squads.

Dynamic Squads allow cross-department work without destroying the permanent organization chart or authority structure.

### 7.5 Capability Registry

AIOS owns the capability semantics for positions, agents, runtimes, tools and connectors.

Routing can consider:

- capability;
- deterministic authority;
- SLA risk;
- workload/capacity;
- historical quality;
- correction/rework;
- cost;
- provider/runtime health;
- privacy/data-use;
- evidence/human-review needs.

### 7.6 Organizational memory

Memory scopes:

```text
Session → Position → Department → Organization
```

Memory may contain collaboration lessons, recurring problems, successful interventions, routing experience and correction patterns.

Memory never becomes evidence/legal truth merely because an agent remembers it.

---

## 8. SLA, KPI, OKR and Definition of Done

Human-like interaction must not reduce performance discipline.

### 8.1 SLA direction

Potential SLA contract fields:

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

Suggested classes: Critical / Priority / Standard / Background.

SLA risk should first trigger organizational correction—assist, rebalance, reassign or change execution capability—before escalation beyond the level genuinely required.

### 8.2 KPI direction

Measure at least:

- Mission completion / SLA attainment / cycle time;
- blocker age / handoff latency / response latency;
- first-pass quality / professional agreement / correction / rework;
- evidence-grounding / provenance completeness;
- collaboration success / unnecessary handoffs / duplicate work;
- dependency-resolution time / escalation appropriateness;
- cost per successful outcome / cost of rework;
- human effort per outcome;
- human-gate / authority / evidence-gate compliance.

**Team/Mission outcome is the primary performance unit.** Individual metrics are diagnostic, not an incentive to compete at the expense of the organization.

### 8.3 OKR direction

Objectives and Key Results sit above operational KPIs and allow CEO/executives to direct improvement.

Example:

```text
Objective: Reduce avoidable Austria case delays

KR1 ≥95% evidence review within SLA
KR2 reduce median blocker age by 30%
KR3 <5% material professional correction rate
KR4 reduce unnecessary cross-department handoffs by 20%
```

### 8.4 Definition of Done

Material Missions should define what “finished” actually requires, including deliverables, evidence/provenance, uncertainty, required review, valid output, authorized external actions, SLA disposition and outcome/learning capture.

---

## 9. Progressive intervention and human escalation

The organization should not jump from uncertainty to Board intervention or global pause.

Target intervention ladder:

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

`Pause Organization` remains an emergency governance control for cases where continued autonomous execution itself is materially unsafe.

Escalation rule:

> **Resolve autonomously where permitted. Collaborate before escalating. Escalate to the lowest level with the necessary expertise or authority. Reserve Board attention for genuinely Board-level matters.**

---

## 10. Live Organization / Cockpit direction

The future Cockpit should become a window into a living organization while retaining premium enterprise information design.

Potential capabilities:

- department/position map;
- visible working/waiting/blocked/collaborating states;
- meaningful animated delegations/conversation flows;
- active Dynamic Squads;
- Mission movement;
- SLA risk;
- workload/capacity;
- agent/runtime cost and quality;
- click a position to inspect work, conversations, authority, performance and permitted memory;
- natural conversation with CEO/executives/specialists;
- organization-wide compression into routine/notable/material/Owner/Board attention.

The visualization must reflect AIOS-owned normalized state. Decorative animation cannot become semantic truth.

---

## 11. Internal Learning & Quality

The long-term flywheel is:

```text
Work
  ↓
Outcomes
  ↓
Corrections / collaboration / SLA / routing signals
  ↓
Operational Intelligence
  ↓
Evaluation & Quality
  ↓
Permitted Training / Optimization
  ↓
Better models / routing / organization
  ↓
Better Work
```

Three layers remain distinct:

1. Operational Intelligence;
2. Evaluation & Quality;
3. Training & Optimization.

Human corrections, Owner redirections, peer-review disagreements, failed routing, SLA misses and provider/runtime outcomes may become learning signals where legally and contractually permitted.

`AIOSDataUsagePolicy`, `LearningRecord`, `TrainingDataset`, `ModelVersion` and training/evaluation lineage remain future architecture concepts. A record valid for analytics is not automatically trainable.

EU compliance remains an enabler of lawful learning through explicit purpose, lawful basis/compatibility analysis, appropriate treatment of data categories, transparency, minimisation, safeguards, retention and lineage. A generic Terms clause is not universal authorization for all future learning uses.

---

## 12. Platform Evolution waves

Technology Radar waves describe implementation order/gates, not automatic installation.

### Wave 0 — Architecture & Governance — COMPLETE

- Radar/candidate-evaluation contract;
- AIOS Semantic Sovereignty;
- provider-neutral adapters;
- Internal Learning & Quality;
- training lineage;
- AIOS Coworker boundary;
- Agent Organization Fabric boundary;
- Execution Broker direction;
- natural interaction + deterministic accountability;
- distributed review / centralized oversight;
- Human Owner Command;
- SLA/KPI/OKR direction.

### Wave 1 — Quality Foundation — COMPLETE

Bounded pilots:

- Promptfoo;
- OpenTelemetry;
- ClamAV.

The detailed acceptance remains in CHANGELOG. This architecture checkpoint does not claim those tests were rerun.

### Wave 2 — Document & Privacy Intelligence — IN PROGRESS

```text
ClamAV → Docling → OCR providers → AIOSDocumentArtifact → Presidio / Privacy Gateway → Evidence
```

Current state:

- **Docling bounded pilot STARTED**;
- latest accepted runtime regression: **873 passed / 5 skipped / 0 failed**;
- Next.js build **41/41 PASS**;
- design foundation **28/28 PASS**;
- preserved `gmai.db` unchanged;
- **Presidio remains the next queued Wave 2 pilot**.

### Wave 3 — Regulatory Monitoring

`official source → urlwatch/change detector → candidate change → AI analysis → human/source review → VerifiedRule`

Never `website changed → law automatically changed`.

### Wave 4 — AI Runtime, Retrieval & Quality

- Pydantic AI;
- pgvector vs Qdrant;
- DSPy;
- Langfuse behind OpenTelemetry;
- Promptfoo;
- initial Learning/Evaluation runtime.

### Wave 5A — Organization Semantics Foundation

Define/accept AIOS-owned contracts for:

- Mission;
- AgentConversation;
- conversational/collaborative OrganizationActivity;
- Capability Registry;
- organizational memory scopes;
- AgentRelationship;
- SLA contract;
- KPI/OKR semantics;
- Definition of Done;
- Dynamic Squad;
- Execution Broker.

### Wave 5B — Agent Organization Fabric

Munder Difflin principal reference/pilot for:

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

OpenWorker principal reference/pilot for:

- finished deliverables;
- files;
- tools;
- MCP;
- connectors;
- scheduled execution;
- external actions;
- approval handling;
- Mission result return.

Munder/OpenWorker/AIOS-native capabilities may cooperate through the Broker.

### Wave 5D — Live Organization / Cockpit

Premium AIOS-native organization visualization for positions, work, conversations, delegations, squads, SLA risk, workload, cost, performance and intervention.

### Wave 5E — Organizational Learning & Optimization

Use permitted outcomes to improve routing, collaboration, capability/runtime selection, SLA performance, team composition, prompts/programs and capacity decisions.

### Wave 6 — Professional Output

Gotenberg, Typst, EU DSS and premium professional outputs such as Mobility Assessments, Employer Packs, Evidence Registers, Case Chronologies, Risk Registers, Board Briefs, Qualification Memos and provenance appendices.

### Continuous — Learning & Quality Plane

Evaluation, correction learning, organizational analytics, training lineage, Cockpit Quality Intelligence and permitted model/program improvement continue across waves.

---

## 13. Phase 14 relationship

Phase 14 remains a **scale-validated-product** programme, not permission to redesign the product around infrastructure.

Measured needs may eventually justify dedicated retrieval/search, graphs, streaming, Temporal, OpenFGA or other Radar winners.

The Agent Organization Fabric / AIOS Coworker / Execution Broker are product capabilities and may begin as bounded Platform Evolution pilots only when:

- Phase 13 evidence allows it;
- a concrete product need exists;
- AIOS-owned contracts are defined;
- implementation is bounded;
- acceptance/rollback/exit criteria are explicit.

---

## 14. Acceptance and repository discipline

Every implementation slice must follow the established deterministic workflow:

1. verify exact branch/SHA and clean baseline;
2. read canonical docs relevant to the slice;
3. perform bounded discovery;
4. freeze exact file/change boundary;
5. implement incrementally inside that boundary;
6. run focused and broad acceptance appropriate to the change;
7. perform runtime/browser review for user-facing work;
8. update this roadmap for every project patch;
9. update `CHANGELOG.md` for meaningful delivery/checkpoint closure;
10. stage exact intended files only;
11. run staged diff/whitespace checks;
12. commit truthfully and push the exact branch;
13. fetch and verify local SHA == remote SHA;
14. verify clean working tree;
15. create an immutable `.local/archives/...zip` baseline and SHA256 when working from the canonical local repository.

Never invent PASS evidence. Missing tools/dependencies are environment limitations, not successful checks.

No Phase 13.17 finding is considered fixed until the relevant correction is implemented and retested with human-use evidence.

---

## 15. Canonical documents for ongoing work

At minimum:

- [GLOBAL_MOBILITY_AIOS_VISION_V1.md](GLOBAL_MOBILITY_AIOS_VISION_V1.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [REPOSITORY_POLICY.md](REPOSITORY_POLICY.md)
- [DESIGN_SYSTEM_INFORMATION_ARCHITECTURE_V13_16_0.md](DESIGN_SYSTEM_INFORMATION_ARCHITECTURE_V13_16_0.md)
- [AI_ORGANIZATION_GOVERNANCE_V13_0.md](AI_ORGANIZATION_GOVERNANCE_V13_0.md)
- [HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1.md](HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1.md)
- [TECHNOLOGY_RADAR_V1_1.md](TECHNOLOGY_RADAR_V1_1.md)
- [THIRD_PARTY_PLATFORM_ADOPTION_PRINCIPLES.md](THIRD_PARTY_PLATFORM_ADOPTION_PRINCIPLES.md)
- [ADR/0002-provider-neutral-platform-adapters.md](ADR/0002-provider-neutral-platform-adapters.md)
- [PHASE_13_17_OWNER_LED_HUMAN_ACCEPTANCE_CHECKPOINT_2026_08_18.md](PHASE_13_17_OWNER_LED_HUMAN_ACCEPTANCE_CHECKPOINT_2026_08_18.md)
- operator UX/review specifications relevant to the active slice;
- this `ROADMAP.md` and current `CHANGELOG.md`.

---

## 16. Current decision

**Phase 13.17 owner-led genuine human acceptance remains IN PROGRESS / PAUSED BY EVALUATOR.** It is not independent third-party validation, and the existing human findings remain unresolved until correction/retest/disposition.

**Technology Radar Wave 1 is COMPLETE.**

**Technology Radar Wave 2 is IN PROGRESS:** Docling bounded pilot has started; Presidio remains next queued.

The **Human-Like Agent Organization Architecture V1 is now canonical architecture direction**, including:

- Munder Difflin + OpenWorker as complementary A+ references;
- AIOS Execution Broker;
- Mission / Dynamic Squad;
- AgentConversation and conversational OrganizationActivity;
- organizational memory / relationships;
- Capability Registry;
- SLA / KPI / OKR / Definition of Done;
- progressive intervention;
- Live Organization;
- organizational learning.

This architecture checkpoint **does not start Munder Difflin, OpenWorker, Temporal, OpenFGA, Pydantic AI, Qdrant, or any new Wave 5 runtime integration**. Implementation remains bounded and evidence-gated.

Phase 13.16 product acceptance remains sealed. Phase 14 remains demand-gated.

Long-term flywheel:

> **Work → Outcomes → Corrections → Intelligence → Evaluation → Training → Better AIOS → Better Work.**
