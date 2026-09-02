# Global Mobility AIOS — Human-Like Agent Organization Architecture V1

**Date:** 2026-08-19  
**Status:** CANONICAL ARCHITECTURE DIRECTION / IMPLEMENTATION-GATED  
**Runtime impact of this document:** none  
**Active product work:** Phase 13.17 owner-led human acceptance remains in progress

## 1. Purpose

Global Mobility AIOS should behave less like a collection of isolated software agents and more like a capable, accountable organization whose members communicate, coordinate, remember, help one another, form teams, deliver work, learn from outcomes, and involve humans only when human knowledge, judgement, personal input, or reserved authority is genuinely required.

The target is:

> **Human in interaction. Machine-like in reliability.**

Natural organizational behaviour must not reduce professional quality, legal/evidence discipline, security, SLA performance, auditability, authority control, or outcome accountability.

The organization should feel alive without becoming casual about work.

Four permanent principles anchor the model:

> **Natural interaction, deterministic accountability.**

> **Team outcomes over agent competition.**

> **Activity is broad; authority is narrow.**

> **Autonomy is earned and measured through quality, SLA performance, governed outcomes, and bounded authority.**

---

## 2. The organization model

```text
                         HUMAN OWNER / BOARD
                                  │
                                  ▼
                    GLOBAL MOBILITY AIOS COCKPIT
                                  │
                           OWNER COMMAND MODE
                                  │
                                  ▼
                               AI CEO
                                  │
                    ORGANIZATION OS / DOMAIN TRUTH
                                  │
            ┌─────────────────────┼─────────────────────┐
            ▼                     ▼                     ▼
        Positions             Work Graph            Authority
        Departments           Missions              Evidence
        Relationships         WorkItems             Decisions
        Conversations         Dependencies          Human Gates
                                  │
                                  ▼
                    AGENT ORGANIZATION FABRIC
                                  │
                 ┌────────────────┼────────────────┐
                 ▼                ▼                ▼
           Communication      Coordination       Memory
                                  │
                                  ▼
                         EXECUTION BROKER
                                  │
           ┌──────────────────────┼───────────────────────┐
           ▼                      ▼                       ▼
    Munder-style agents      OpenWorker              AIOS-native
    organization/execution   finished-work           typed agents /
                             execution               deterministic services
           │                      │                       │
           └──────────────────────┼───────────────────────┘
                                  ▼
                         FINISHED WORK / ACTION
                                  │
                                  ▼
                          QUALITY + ACCEPTANCE
                                  │
                    SLA / KPI / evidence / review
                                  │
                                  ▼
                          GOVERNED OUTCOME
                                  │
                                  ▼
                        LEARNING & QUALITY
```

AIOS remains authoritative for domain meaning, case state, evidence, certification, publication, WorkItems, Missions, Decisions, Contributions, OrganizationActivity, authority, and business outcomes.

External runtimes provide capability. They do not define organizational truth.

---

## 3. Munder Difflin + OpenWorker: coordinated, not competing

### Munder Difflin — Agent Organization reference

Munder Difflin is the primary strategic reference for the **human-like multi-agent organization experience**:

- persistent agent identities;
- agent-to-agent communication;
- mailboxes and conversation routing;
- shared working context / blackboard patterns;
- long-term memory;
- supervisor/orchestrator patterns;
- dependency-aware task coordination;
- scheduled missions / heartbeat;
- human approval and intervention patterns;
- per-agent budgets and cost telemetry;
- OpenTelemetry visibility;
- progressive circuit breaking;
- live organization visualization;
- direct human interaction with individual agents;
- skills / capability discovery.

AIOS should use these ideas to build an **AIOS Agent Organization Fabric**, while preserving AIOS-owned persistence, domain semantics, authority, evidence and governance.

### OpenWorker — Finished-Work execution reference

OpenWorker remains an A+ strategic reference for **outcome-oriented execution**:

- finished deliverables rather than chat-only guidance;
- file and artifact production;
- tool and terminal use;
- MCP;
- connectors;
- scheduled work;
- external app actions;
- model portability;
- approval before consequential actions;
- unattended-work inbox patterns;
- local-first coworker operation.

### Combined principle

The architecture should not ask:

```text
Munder Difflin OR OpenWorker?
```

It should ask:

```text
What combination of organizational coordination and execution capability
produces the best governed result for this Mission?
```

That decision belongs to AIOS.

---

## 4. AIOS Execution Broker

A new conceptual layer, **AIOS Execution Broker**, should sit between governed organizational work and concrete runtimes/providers.

The Broker chooses or composes execution capabilities using AIOS-owned criteria such as:

- required capability;
- authority boundary;
- SLA urgency;
- expected quality;
- current workload/capacity;
- jurisdiction/context;
- evidence requirements;
- human-review requirements;
- tool/connector availability;
- model/runtime suitability;
- historical success rate;
- rework/correction rate;
- cost;
- privacy/data-use constraints;
- provider health;
- fallback options.

Example:

```text
Mission: Prepare Austria employer mobility brief
        │
        ├── Global Intelligence agent → current-source analysis
        ├── Evidence agent → source/evidence assembly
        ├── CLO → uncertainty/legal framing
        ├── OpenWorker capability → final DOCX/PDF + draft communication
        ├── Operations → case applicability / professional readiness
        └── Human review only if required by the applicable authority/risk gate
```

Providers may cooperate on one Mission. Outcome quality matters more than provider ownership.

---

## 5. Missions above WorkItems

Humans usually think in outcomes, not task records. AIOS should therefore introduce the concept of a **Mission** above WorkItems.

A Mission represents an organizational outcome such as:

- resolve Austria processing delays;
- prepare an employer relocation pack;
- investigate a regulatory-source discrepancy;
- reassess cases affected by a newly VerifiedRule;
- reduce evidence-review backlog;
- prepare weekly CEO operating brief;
- improve qualification-assessment agreement rate.

Conceptually:

```text
Mission
  mission_id
  objective
  owner_position
  participating_positions
  priority
  service_class
  success_definition
  SLA
  KPIs
  due_at
  risk_level
  authority_boundary
  status
  outcome
```

A Mission may generate multiple WorkItems, dependencies, conversations, artifacts and decisions across departments.

---

## 6. Dynamic squads

AIOS should be able to form temporary cross-department **squads** around Missions.

Example:

```text
Austria Regulatory Response Squad

Mission owner: AI CEO
Participants:
- CLO
- Global Intelligence Lead
- Evidence Operations Lead
- Operations specialist
- OpenWorker finished-work capability

Purpose:
Investigate change → validate evidence → determine affected cases → prepare response
```

The squad exists only as long as the Mission requires it. Its conversation, work, decisions, outputs and learning remain durable afterwards.

This prevents rigid departmental boundaries from slowing work while preserving normal reporting/authority structures.

---

## 7. Natural organizational communication

Agents should communicate like capable colleagues rather than isolated RPC endpoints.

Routine organizational conversation may include:

- questions;
- clarifications;
- suggestions;
- disagreement;
- requests for help;
- handoffs;
- status updates;
- warnings;
- peer review;
- shared findings;
- informal coordination;
- acknowledgement;
- completion messages.

Not every conversation requires a WorkItem, approval, formal decision or human intervention.

Example:

```text
CLO:
"Has Austria published the new salary threshold yet?"

Global Intelligence:
"Not yet. The latest official publication still reflects the current threshold."
```

This is valid organizational activity even if it creates no new task.

---

## 8. AgentMessage is OrganizationActivity

The canonical relationship should be:

```text
AgentMessage ⊂ OrganizationActivity
```

rather than treating communication as outside organizational history.

`OrganizationActivity` is broad and may contain several classes:

```text
OrganizationActivity
│
├── Conversational
│   ├── message
│   ├── question
│   ├── clarification
│   └── suggestion
│
├── Collaborative
│   ├── handoff
│   ├── delegation
│   ├── request
│   ├── response
│   └── shared finding
│
├── Operational
│   ├── work started
│   ├── work completed
│   ├── blocker discovered
│   ├── evidence reviewed
│   └── artifact produced
│
├── Material
│   ├── significant risk
│   ├── major case impact
│   ├── cross-department conflict
│   └── material recommendation
│
└── Authority-bearing
    ├── professional approval
    ├── department approval
    ├── executive decision
    ├── Owner/Board decision
    └── emergency control
```

Important boundary:

> **Conversation can create understanding; it does not automatically create authority.**

A conversational activity does not silently become a legal conclusion, VerifiedRule, certification, publication, ExecutiveDecision or Board decision.

Provider message logs may be ingested into AIOS-owned OrganizationActivity, but provider storage itself is not the authoritative AIOS activity record.

---

## 9. AgentConversation

AIOS should introduce a first-class conversation concept that groups organizational interaction.

Conceptual fields:

```text
AgentConversation
  conversation_id
  participants
  related_mission_id?
  related_work_item_id?
  related_case_id?
  related_evidence_id?
  related_regulatory_change_id?
  purpose
  status
  significance
  started_at
  last_activity_at
  summary
```

Possible significance levels:

- routine;
- notable;
- material;
- critical.

A conversation may produce WorkItems, Blockers, Decisions, Contributions or artifacts, but does not have to.

---

## 10. Human intervention and escalation

Human intervention should be **distributed and proportional**, not automatically routed to the Board.

The escalation principle is:

> **Resolve autonomously where permitted. Collaborate before escalating. Escalate to the lowest level with the necessary expertise or authority. Reserve Board attention for genuinely Board-level matters.**

```text
Issue
 │
 ├─ agent can resolve → resolve
 │
 ├─ colleague has expertise → collaborate
 │
 ├─ department authority required → department lead
 │
 ├─ professional judgement required → Professional / Operator
 │
 ├─ personal fact required → Mobility User
 │
 ├─ executive authority required → relevant Executive / CEO
 │
 └─ reserved/material organization authority → Human Owner / Board
```

Board Room must remain a reserved-authority module, not a generic review inbox.

---

## 11. Position, department and organization memory

AIOS should support several distinct organizational memory scopes:

```text
Session Memory
      ↓
Position Memory
      ↓
Department Memory
      ↓
Organization Memory
```

Examples of useful memory:

- recurring operational problems;
- preferred collaboration methods;
- past successful interventions;
- common evidence ambiguities;
- typical source-structure issues;
- professional correction patterns;
- Owner redirections;
- delegation lessons;
- department expertise;
- routing experience.

Permanent boundary:

```text
memory ≠ Evidence
memory ≠ VerifiedRule
memory ≠ certification
memory ≠ legal truth
```

Memory informs work. Evidence and governed domain state determine authoritative conclusions.

---

## 12. Agent relationships and organizational social fabric

AIOS should model useful organizational relationships rather than treating all agents as interchangeable endpoints.

Conceptually:

```text
AgentRelationship
  from_position
  to_position
  relationship_type
  structural_or_emergent
  interaction_count
  successful_collaborations
  handoff_quality
  rework_rate
  response_time
  last_interaction_at
```

Relationship types may include:

- reports_to;
- collaborates_with;
- reviewer_for;
- frequently_requests;
- subject_matter_dependency;
- escalation_path.

Structural relationships remain authoritative organization data. Emergent collaboration statistics are learned operational signals.

---

## 13. Capability Registry

AIOS should maintain an AIOS-owned **Capability Registry** describing what each position/agent/runtime can do and what it may not do.

Example:

```text
Document Officer

Capabilities
✓ OCR extraction
✓ document classification
✓ evidence completeness
✓ document comparison

Human / specialist required
○ authenticity determination
○ legal sufficiency
○ final qualification approval

Prohibited
× final visa eligibility conclusion
× official submission without required authority
```

The Execution Broker may use capability, authority, workload, historical quality, SLA risk and cost when routing work.

Provider-specific skills may register behind this AIOS-owned contract.

---

## 14. Service Level Agreements

SLAs should become a first-class organizational operating mechanism.

A Mission or WorkItem may define:

```text
SLAContract
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

Suggested service classes:

- Critical;
- Priority;
- Standard;
- Background.

SLA risk should trigger **organizational correction before Board escalation**:

```text
SLA risk
  ↓
notify owner / team
  ↓
request assistance
  ↓
rebalance capacity
  ↓
reassign work
  ↓
change execution capability
  ↓
escalate to appropriate authority only when necessary
```

The goal is reliable service, not punishment.

---

## 15. KPIs and organizational performance

AIOS should measure performance without creating a simplistic agent leaderboard.

### Delivery KPIs

- Mission completion rate;
- SLA attainment;
- average cycle time;
- blocker age;
- handoff latency;
- response latency;
- overdue work rate.

### Quality KPIs

- first-pass quality;
- professional agreement rate;
- human correction rate;
- material correction rate;
- rework rate;
- evidence-grounding rate;
- source/provenance completeness;
- review rejection rate.

### Collaboration KPIs

- successful collaboration rate;
- unnecessary handoff rate;
- repeated-question rate;
- dependency resolution time;
- peer-review usefulness;
- duplicate-work rate;
- escalation appropriateness.

### Economic KPIs

- cost per successful outcome;
- model/runtime cost by capability;
- cost of rework;
- human effort per outcome;
- value/throughput per department or Mission.

### Safety/governance KPIs

- unauthorized-action attempts blocked;
- human-gate compliance;
- evidence/review gate compliance;
- circuit-breaker activations;
- material incidents;
- false escalation / missed escalation rates.

Individual metrics support diagnosis and routing. **Team/Mission outcome is the primary performance unit.**

---

## 16. Objectives and Key Results

Above operational KPIs, AIOS should support organization goals/OKRs.

Example:

```text
Objective:
Reduce avoidable Austria case delays.

Key Results:
- ≥95% evidence reviews within SLA
- reduce median blocker age by 30%
- <5% material professional correction rate
- reduce unnecessary cross-department handoffs by 20%
```

The CEO and executives should use OKRs to direct organizational improvement rather than optimizing isolated agent metrics.

---

## 17. Definition of Done and finished work

Each important Mission should define what **finished** means.

A Definition of Done may require:

- requested artifact produced;
- authoritative sources attached where required;
- uncertainty explicitly stated;
- evidence/provenance complete;
- required professional/human review complete;
- output format valid;
- client/internal communication prepared;
- external action executed only with proper authority;
- SLA satisfied or exception documented;
- outcome recorded;
- learning signals captured where permitted.

This is where OpenWorker's finished-work philosophy aligns strongly with AIOS.

---

## 18. Peer review before human review

Human review should not be the first response to every uncertainty.

Where safe and appropriate, AIOS can use peer/agent review first:

```text
Agent work
  ↓
peer/specialist review
  ↓
confidence / disagreement assessment
  ↓
professional or human review only when required
```

Examples:

- regulatory extraction → Global Intelligence peer check;
- evidence classification → Evidence specialist cross-check;
- case-summary drafting → Operations peer review;
- legal ambiguity → CLO or qualified professional;
- personal fact uncertainty → Mobility User;
- reserved authority → Owner/Board.

Peer review does not replace mandatory human gates.

---

## 19. Progressive intervention / circuit breaker

AIOS should adopt a progressive intervention model rather than jumping from normal execution to organization-wide pause.

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

Possible constraints include:

- reduced tools;
- lower budget;
- no external actions;
- additional peer review;
- human approval before continuation;
- model/runtime change;
- narrower mission scope.

`Pause Organization` should remain an emergency governance control for situations where continued autonomous execution itself is materially unsafe.

---

## 20. Capacity and workload management

Every operational position should expose enough state for the organization to manage capacity:

- queue depth;
- current Missions;
- current WorkItems;
- utilization;
- blocked/waiting work;
- SLA risk;
- available capabilities;
- recent quality;
- execution cost;
- dependency load.

COO/CEO routing should use this information to rebalance work before service degradation becomes an escalation.

---

## 21. Organizational rituals

AIOS should support recurring organizational behaviours, not merely cron jobs.

Examples:

- CEO morning operating brief;
- daily SLA-risk review;
- regulatory-change briefing;
- evidence backlog review;
- weekly quality review;
- monthly learning retrospective;
- department planning sessions;
- mission post-mortems after material failure.

These rituals may create Missions or WorkItems only when something actionable emerges.

---

## 22. Learning from organizational behaviour

The Learning & Quality Plane should evaluate not only model correctness but also **organizational effectiveness**.

Potential learning signals:

- repeated unnecessary handoffs;
- collaboration paths that resolve issues quickly;
- departments repeatedly asked the same question;
- poor routing decisions;
- SLA misses;
- successful capacity rebalancing;
- human corrections;
- Owner redirection;
- professional overrides;
- peer-review disagreements;
- failed external actions;
- provider/runtime performance.

A failure should support root-cause classification such as:

```text
source problem
routing problem
capacity problem
capability gap
model weakness
prompt/program weakness
authority ambiguity
poor collaboration
provider failure
insufficient evidence
```

This turns operational history into organization-improvement data where legally and contractually permitted.

---

## 23. Live Organization in Cockpit

Munder Difflin's visual-office principle should be adapted into a premium **Live Organization** experience inside the Global Mobility AIOS Cockpit.

AIOS should not copy Munder's pixel/SNES visual style. The concept should be translated into the established AIOS identity: deep navy/graphite, warm ivory, premium typography, restrained motion, sophisticated information density and subtle depth.

Potential Live Organization capabilities:

- department/position map;
- agents visibly working/waiting/blocked/collaborating;
- subtle animated delegations;
- conversation flows;
- active squads;
- Mission movement;
- SLA-risk indicators;
- workload/capacity;
- agent/runtime cost;
- current tool/capability use;
- click any position to inspect work, conversation, authority, performance and memory scope;
- direct natural-language conversation with CEO/executives/specialists.

The goal is a **window into a living organization**, not decorative animation.

---

## 24. Cockpit compression

The underlying organization may generate large volumes of activity. Cockpit should compress that intelligently.

Example:

```text
Organization today

143 conversations
39 delegations
12 completed Missions
18 agents working
7 collaborating
4 waiting
2 blocked

3 notable issues
1 material risk
0 Board decisions required
```

Routine activity remains inspectable in Live Organization / Activity. Only significant or authority-bearing matters should cross the Owner/Board attention boundary.

---

## 25. Human Owner command

The Human Owner should normally interact through the CEO, while retaining the ability to inspect or address any permitted organizational position directly.

Example:

```text
OWNER COMMAND

> Ask the CEO why Austria cases are taking longer this week,
> have Operations investigate, and prepare a recovery plan.
```

AIOS interprets the request into governed Missions/work while preserving authenticated Owner authority.

High-impact commands may show an interpretation preview, especially for suspend/pause/external-action commands.

---

## 26. Provider/storage boundary

Munder Difflin's local-file/git hive is appropriate for its own desktop-agent architecture. AIOS should not replace its authoritative database/domain model with that storage pattern.

Likewise, OpenWorker's internal task/session model should not replace AIOS organizational semantics.

AIOS remains authoritative for:

- Missions;
- WorkItems;
- Dependencies;
- Blockers;
- AgentConversation;
- OrganizationActivity;
- HumanActionRequest;
- HumanAction;
- ExecutiveDecision;
- Contribution;
- evidence/certification/publication;
- authority;
- case/domain outcomes.

External IDs/events are mappings and inputs to AIOS state.

---

## 27. Proposed platform-evolution implementation sequence

This architecture is approved as a direction, not an instruction to install everything immediately.

### Wave 5A — Organization semantics foundation

Define/validate AIOS-owned contracts for:

- Mission;
- AgentConversation;
- conversational OrganizationActivity;
- Capability Registry;
- organizational memory scopes;
- AgentRelationship;
- SLA contract;
- KPI/OKR semantics;
- Definition of Done;
- Dynamic Squad.

### Wave 5B — Agent Organization Fabric pilot

Use Munder Difflin as the principal architecture/reference pilot for:

- agent identity;
- communication;
- conversation routing;
- memory;
- coordination;
- supervisor patterns;
- scheduling;
- budgets;
- circuit breaker;
- Live Organization event feed.

Pilot behind AIOS-owned adapters/contracts.

### Wave 5C — Execution Broker + OpenWorker pilot

Pilot OpenWorker concepts/capability for:

- finished deliverables;
- files;
- tools;
- MCP;
- connectors;
- scheduled execution;
- external actions;
- approval handling;
- result return into AIOS Missions.

### Wave 5D — Live Organization / Cockpit

Build a premium AIOS-native visualization of:

- positions;
- work;
- conversations;
- delegations;
- squads;
- SLA risk;
- workload;
- performance;
- interventions.

### Wave 5E — Organizational learning and optimization

Use permitted historical outcomes to improve:

- routing;
- collaboration;
- capability selection;
- SLA performance;
- runtime/model selection;
- team composition;
- prompts/programs;
- capacity decisions.

Each wave remains separately gated by architecture review, benchmark, security/data-flow review, acceptance, rollback, and exit strategy.

---

## 28. Relationship to Phase 13.17

This architecture must **not** interrupt or rewrite the current human-acceptance evidence.

Phase 13.17 remains owner-led human acceptance, not independent third-party validation. Existing findings remain genuine unresolved product evidence until corrected and retested.

The future architecture should use those findings. Examples:

- better persistent navigation supports role clarity;
- plain-language terminology supports human-like collaboration;
- progressive intervention reduces misuse of global pause controls;
- direct traceability supports inspectable organizational work;
- Live Organization can reduce manual department hunting;
- distributed review reinforces the correct Owner/Professional/Mobility User boundaries.

---

## 29. Success criteria for the future organization

The architecture succeeds when Global Mobility AIOS can demonstrate all of the following:

1. agents collaborate naturally without human micromanagement;
2. humans enter at the lowest appropriate expertise/authority boundary;
3. Board attention remains reserved and material;
4. Missions finish as real governed outcomes, not only chat responses;
5. SLA performance is measurable and actively managed;
6. team quality is more important than internal agent competition;
7. evidence/legal truth remains protected from memory/chat/model shortcuts;
8. capability/runtime routing improves based on measured outcomes;
9. the Cockpit makes the organization understandable in real time;
10. failures produce learning rather than repeated organizational mistakes;
11. provider replacement does not destroy AIOS semantics;
12. human corrections and outcomes can improve AIOS where their use is permitted.

---

## 30. Target end state

```text
Work / Mission
      ↓
Natural organizational conversation
      ↓
Collaboration + delegation
      ↓
AIOS Execution Broker
      ↓
Best available governed capabilities
(Munder-inspired organization + OpenWorker execution + AIOS-native services)
      ↓
Finished work
      ↓
Definition of Done
      ↓
SLA + quality + evidence + authority gates
      ↓
Real outcome
      ↓
KPI / organizational intelligence
      ↓
Corrections + learning
      ↓
Better routing / agents / models / organization
      ↓
Better work
```

The long-term product should feel like **a real organization made of AI colleagues, human professionals, mobility users and an accountable Human Owner/Board — natural in interaction, rigorous in execution, observable in operation, and continuously improving.**
