# Global Mobility AIOS — Final Combined Project Architecture V1

**Date:** 2026-08-20  
**Status:** Canonical combined architecture direction proposed for V12  
**Active implementation branch:** `roadmap/global-mobility-aios-v12`  
**Architecture basis:** Global Mobility AIOS V1.3 + controlled Munder Difflin v0.4.4 donor adoption  
**Munder donor baseline:** `v0.4.4` frozen source snapshot  

> **Global Mobility AIOS is a governed, transparent, self-improving, high-autonomy AI-operated professional organization for global mobility.**

This document consolidates the final project direction after comparing the existing Global Mobility AIOS V1.3 architecture with Munder Difflin v0.4.4 and selecting the strongest compatible capabilities from each.

The governing decision is:

> **Global Mobility AIOS remains the product, domain model, constitutional authority, canonical truth system and governing architecture. Munder Difflin v0.4.4 is a frozen technology donor whose relevant runtime capabilities are transformed into native AIOS Organization Fabric components.**

This is not a plan to rename or lightly customize Munder Difflin. It is not a plan to maintain two competing agent architectures. AIOS owns organizational meaning and authority; Munder contributes implementation mechanics where they strengthen AIOS.

---

## 1. Project identity and operating philosophy

Global Mobility AIOS is intended to operate professional work for the movement of people, talent, families, businesses and capital across borders.

It combines:

- global-mobility intelligence;
- official-source regulatory intelligence;
- Evidence and provenance;
- document intelligence;
- case/work orchestration;
- persistent AI employees;
- AI executives and departments;
- dynamic cross-functional Mission Squads;
- agent-to-agent communication;
- organizational memory;
- Skills, tools and connectors;
- proactive triggers and schedules;
- governed external execution;
- professional/human review where required;
- organizational learning;
- Human Owner / Board oversight;
- complete material-action transparency.

The project must not collapse into a chatbot, immigration CRM, document uploader, workflow engine, generic multi-agent framework, generic AI company simulator, generic SaaS dashboard or approval queue.

Permanent operating statements:

> **AIOS does the work. Humans govern the exceptions and retained authority.**

> **The safety infrastructure exists to enable autonomy, not suppress it.**

> **Board by exception. Transparency by default.**

> **Agents are allowed to be wrong while thinking; AIOS is not allowed to be wrong silently when committing truth.**

---

## 2. Complete global-mobility lifecycle

AIOS should support the complete, branching, revisable mobility lifecycle:

```text
Human / Business Goal
        ↓
Identity / profile / circumstances / consent
        ↓
Goals + constraints + preferences
        ↓
Mobility strategy
        ↓
Country / jurisdiction discovery
        ↓
Pathway discovery
        ↓
Eligibility + alternatives
        ↓
Evidence requirements
        ↓
Evidence collection + provenance
        ↓
Official rules + regulatory intelligence
        ↓
Risk + cost + timing + dependencies
        ↓
Document preparation + validation
        ↓
Professional / regulated review where required
        ↓
Application / filing preparation
        ↓
Decision Readiness + independent verification
        ↓
Human / Board authority where required
        ↓
Submission / appointment / external action
        ↓
Authority response
        ↓
Remediation / request for information / appeal
        ↓
Relocation + post-arrival obligations
        ↓
Renewal / status change / family progression
        ↓
Long-term residence
        ↓
Permanent residence
        ↓
Citizenship
        ↓
Business / investment / wealth planning
        ↓
Future global mobility strategy
```

The lifecycle must support changed goals, employer changes, jurisdiction changes, rejected applications, expired Evidence, superseded rules, family dependencies, alternative pathways and long-lived mobility relationships.

---

## 3. Human Owner / Board — supreme authority

The Human Owner / Board is the supreme authority of Global Mobility AIOS.

No AI CEO, employee, runtime, model, Skill, connector, policy engine, Munder-derived component or external framework may grant itself authority beyond Board-defined limits.

The Board controls or reserves authority over:

- organizational constitution;
- purpose and strategic direction;
- reserved powers;
- risk tolerance;
- authority ceilings;
- autonomy policy;
- legal/professional human-review floors;
- major privacy/security principles;
- appointment/removal of senior AI executive authority;
- fundamentally new classes of autonomous external action;
- major organizational restructuring;
- exceptional legal/regulatory risk;
- exceptional financial commitments;
- organization-wide emergency intervention.

Supreme authority does not imply routine operational involvement.

> **The Board governs the organization; it does not manually operate it.**

---

## 4. Board by exception

The Board should not routinely approve internal research, ordinary case analysis, agent collaboration, drafting, extraction, WorkItem assignment, scheduling, low-risk tool usage, ordinary retries or healthy bounded operational decisions.

Board involvement should concentrate on:

- constitutionally reserved actions;
- legally required human actions;
- government submissions requiring retained authority;
- critical incidents;
- major policy changes;
- major autonomy expansions;
- major strategic decisions;
- unresolved severe contradictions;
- exceptional legal/regulatory commitments;
- exceptional financial commitments;
- executive appointment/removal;
- irreversible actions requiring Board authority.

Target experience:

```text
AI organization researches
        ↓
Evidence verified
        ↓
Application / action prepared
        ↓
Independent verification where required
        ↓
Policy / readiness / risk checks
        ↓
READY
        ↓
Human Board
[Approve] [Modify] [Return] [Submit]
```

---

## 5. AI CEO and executive hierarchy

Munder's centralized GOD/orchestrator concept is not imported as an all-powerful agent. Its useful coordination mechanics are transformed into a scalable executive hierarchy:

```text
Human Owner / Board
        ↓
      AI CEO
        ↓
   L3 Executives
        ↓
 Department Heads
        ↓
Senior Specialists
        ↓
   Specialists
```

The AI CEO focuses on strategy execution, executive coordination, resource allocation, organization-wide performance, budgets, major cross-department conflicts, major escalations, organizational health and Board communication.

Department Heads coordinate professional domains. Specialists perform domain work. This avoids a universal-agent bottleneck.

---

## 6. Persistent AI employees

AIOS employees are persistent organizational identities rather than temporary model sessions.

A mature employee profile may include:

```text
AI Employee
│
├── identity
├── modern character/avatar
├── OrganizationPosition
├── department
├── manager
├── responsibilities
├── expertise
│
├── Missions
├── WorkItems
├── assigned cases
│
├── working memory
├── agent memory
├── organizational memory access
│
├── relationships
├── collaboration history
├── previous decisions
│
├── Skills
├── tools
├── connectors
├── data permissions
│
├── runtime profile
├── provider/model
│
├── authority profile
├── autonomy profile
├── risk limits
├── budget
│
├── performance history
├── quality history
├── verification history
├── incident history
└── learning history
```

Permanent identity rule:

```text
Employee Identity ≠ Provider Identity
Employee Identity ≠ Model Identity
Employee Identity ≠ Runtime Session
```

Changing the underlying provider/model must not create a new employee.

---

## 7. Stable departments + Dynamic Mission Squads

AIOS uses both a durable hierarchy and temporary cross-functional teams.

Permanent departments provide reporting lines, expertise ownership, capacity, budgets, management and capability development.

Dynamic Mission Squads form around specific outcomes. Example:

```text
MISSION AT-4821
Austria RWR+ Application

Austria Immigration Specialist        Lead
Evidence Specialist
Regulatory Intelligence Analyst
Document Intelligence Specialist
Client Communication Specialist
Submission Readiness Specialist
```

When the Mission closes, the squad may dissolve while its Mission record, relationships, performance and learning remain durable.

---

## 8. Mission / Work architecture

The organization should represent work explicitly:

```text
Strategic Goal
      ↓
Mission
      ↓
Case / organizational objective
      ↓
WorkItems
      ↓
Dependencies / blockers
      ↓
Assignment / delegation
      ↓
AgentRuns + collaboration
      ↓
Decision
      ↓
MaterialAction
      ↓
Outcome
      ↓
Learning
```

A conversation does not need to become a WorkItem. A WorkItem does not automatically become a material action.

---

## 9. AIOS Organization Fabric

The Organization Fabric is the primary home for Munder-derived capabilities. It includes:

- persistent employee runtime binding;
- organizational communication;
- message routing;
- Mission/work coordination;
- Dynamic Mission Squads;
- presence and heartbeats;
- Mission Rooms;
- shared collaboration state;
- employee relationships;
- Skills and Capability Registry integration;
- memory mechanics;
- scheduling;
- triggers/events;
- runtime telemetry.

AIOS owns semantics, persistence, authority and governance. Munder supplies reusable implementation patterns where compatible.

---

## 10. Organizational Communication Fabric

Munder's Hive messaging concepts should be adapted into an AIOS-native communication system.

Supported communication acts can include:

```text
REQUEST
QUERY
INFORM
PROPOSE
CHALLENGE
AGREE
DISAGREE
REFUSE
DELEGATE
REVIEW
WARN
ESCALATE
ACKNOWLEDGE
COMPLETE
```

A message may reference:

```text
conversation_id
parent_message_id
sender
sender_position
recipient
department
Mission
Case
WorkItem
Evidence refs
VerifiedRule refs
Decision refs
sensitivity
materiality
risk
trace identity
timestamp
```

Permanent rules:

```text
conversation != authority
message != decision
provider transcript != canonical OrganizationActivity automatically
```

---

## 11. Agent relationships

Persistent employees should build meaningful professional relationship history. AIOS may learn:

- frequent collaborators;
- effective pairings;
- verifier relationships;
- disagreement patterns;
- handoff quality;
- complementary expertise;
- collaboration latency;
- rework caused by team combinations;
- incident correlations.

Relationship intelligence should improve Dynamic Squad formation without becoming social simulation for its own sake.

---

## 12. Mission Rooms / organizational blackboard

Each Mission may maintain purpose-scoped collaborative state:

```text
Mission Room
│
├── objective
├── current plan
├── participants
├── working facts
├── hypotheses
├── known unknowns
├── Evidence references
├── applicable Rules
├── contradictions
├── open questions
├── decisions
├── blockers
├── dependencies
├── requested actions
└── timeline
```

Mission Room content is working context, not canonical truth by default.

```text
Mission Room ≠ Evidence
Mission Room ≠ VerifiedRule
Mission Room ≠ final CaseFact
```

---

## 13. Transparency Layer — permanent and cross-cutting

Transparency remains a first-class architectural layer.

> **Operational autonomy must never create organizational opacity.**

> **Board visibility ≠ Board interruption.**

The Transparency Layer spans:

- AgentRuns;
- conversations/messages;
- delegation chains;
- Missions/WorkItems;
- decisions/recommendations;
- Evidence/SourceSnapshots/VerifiedRules;
- policy evaluations;
- tool actions;
- external actions;
- governance decisions;
- Command Gateway effects;
- contradictions;
- escalations;
- incidents/circuit breakers;
- autonomy changes;
- recovery;
- learning outcomes.

Board drill-down target:

```text
Organization
→ Department
→ Mission
→ Case
→ WorkItem
→ Squad
→ Agent
→ Conversation
→ Decision
→ Tool Action
→ Evidence / Rule
→ Canonical Effect
→ Outcome
```

Transparency should use progressive disclosure rather than a raw event firehose.

---

## 14. Decision Lineage

Every material decision should be reconstructable:

```text
FINAL OUTCOME
     ▲
Canonical transition
     ▲
Command Gateway authorization
     ▲
Policy / authority evaluation
     ▲
Independent verification
     ▲
Agent recommendation
     ▲
Evidence
     ▲
VerifiedRules
     ▲
SourceSnapshots
     ▲
Official-source research / tool actions
```

Structured decision rationale should include conclusion, key reasons, Evidence references, rule references, alternatives considered, uncertainty, contradictions, verification, policy decision and resulting action.

Hidden chain-of-thought is not the governance artifact.

---

## 15. Context Broker

The Context Broker remains a core V1.3 component.

> **More relevant truth, not more tokens.**

Agents should receive purpose-scoped ContextBundles rather than unrestricted organizational data.

```text
ContextBundle
│
├── agent identity
├── OrganizationPosition
├── authority
├── autonomy
├── Mission
├── WorkItem
├── case
│
├── relevant facts
├── relevant Evidence
├── relevant VerifiedRules
├── relevant SourceSnapshots
├── known unknowns
├── contradictions
│
├── previous relevant decisions
├── collaboration summaries
├── relevant organizational memory
│
├── allowed tools
├── allowed connectors
├── sensitivity profile
├── risk tier
├── policy version
└── context version/hash
```

Additional context should be lazy-loaded through purpose-scoped requests.

Material AgentRun lineage should bind the effective ContextBundle so AIOS can later reconstruct what information the employee actually had when acting.

---

## 16. Memory architecture

AIOS supports strong memory while preventing memory from becoming authority automatically.

```text
Working Memory
      ↓
Agent Memory
      ↓
Organizational Memory

----------------------------

Canonical AIOS Truth
```

Permanent principle:

> **Memory provides continuity. Evidence provides authority.**

Munder memory, semantic recall and blackboard ideas should strengthen continuity beneath the AIOS trust boundary.

---

## 17. Agent Runtime Fabric

Munder's provider abstraction and CLI-agent support should evolve into a native AIOS Agent Runtime Fabric:

```text
Persistent Employee
        ↓
AIOS Agent Runtime Port
        ↓
Runtime Adapter
        │
        ├── Hosted/API Model
        ├── CLI Agent
        ├── Local Model
        ├── Specialized Runtime
        └── future provider
```

External runtimes provide capability. AIOS owns employee identity, Mission, authority, context, Evidence, domain semantics, policy, action meaning and canonical state.

---

## 18. Intelligent runtime routing

Eligible runtime selection should eventually consider:

- required capability;
- risk;
- historical reliability;
- provider/model strengths;
- privacy/sensitivity constraints;
- latency;
- cost;
- context requirements;
- availability;
- verification independence.

Typical direction:

```text
R0 summarization
→ economical fast model

R2 client-facing draft
→ balanced quality model

R3 material recommendation
→ high-quality reasoning runtime

Independent verification
→ sufficiently independent runtime/model family

R4/R5
→ strongest eligible bounded configuration
   + required verification/authority
```

---

## 19. Skills & Capability Registry

Munder Skills should become implementation input for the AIOS Capability Registry.

```text
Skill
  ↓
Technical Capability
  ↓
Capability Registry
  ↓
Authority
  ↓
Autonomy
  ↓
Risk
```

Permanent rule:

> **CAN DO ≠ MAY DO**

Installing a Skill gives capability; it does not silently grant authority.

---

## 20. Capability, Authority, Autonomy and Risk

These remain four separate concepts:

```text
Capability = what the runtime can technically do
Authority  = what AIOS permits the actor to do
Autonomy   = how independently that permitted capability may operate
Risk       = consequence of the particular action
```

This separation is foundational.

---

## 21. Earned Autonomy — A0 to A5

Autonomy remains capability-specific, not a single score for an employee.

| Level | Meaning |
|---|---|
| A0 | Prohibited |
| A1 | Human executes |
| A2 | AI prepares; approval required |
| A3 | Autonomous with mandatory review |
| A4 | Autonomous with monitoring and valid recovery controls |
| A5 | Fully autonomous bounded operation |

Example:

```text
Austria Immigration Specialist

Official-source research       A5
Document extraction            A5
Evidence assessment            A4
Eligibility assessment         A4
Client explanation             A3
Evidence certification         A2
Government submission          Human / Board reserved
```

The organization must never collapse this into a single blanket rating such as `Austria Specialist = A4`.

---

## 22. Autonomy maturity progression

Separate from A0-A5 execution level, a capability may progress through:

```text
SHADOW
   ↓
RECOMMEND
   ↓
SUPERVISED
   ↓
AUTONOMOUS
   ↓
HIGH-TRUST AUTONOMOUS
```

These dimensions are related but not identical. A new runtime configuration may remain in SHADOW while the production capability operates at A4.

---

## 23. AutonomyEvidenceProfile

Autonomy promotion/demotion should use evidence such as:

- execution count;
- Evidence-grounding rate;
- verifier agreement;
- human acceptance/modification/rejection;
- contradiction rate;
- policy compliance;
- material error rate;
- critical incidents;
- false/missed escalations;
- SLA attainment;
- latency;
- recovery effectiveness;
- tool reliability;
- outcome quality.

Agents cannot self-promote.

---

## 24. Decision Readiness

Decision Readiness is a routing/quality signal, not authority.

Potential inputs include Evidence completeness, source authority, source freshness, rule freshness, required-fact completeness, cross-source consistency, contradiction state, deterministic validation, capability reliability, verification status and limited confidence metadata.

Permanent rule:

> **Scores route; gates authorize.**

```text
Readiness 99%
BUT mandatory Evidence missing
→ BLOCK
```

```text
Readiness 100%
BUT Board-reserved action
→ BOARD GATE
```

---

## 25. Risk-tiered verification — R0 to R5

Governance effort should scale with consequence.

| Risk | Typical work | Verification |
|---|---|---|
| R0 | brainstorming / summarization | single agent |
| R1 | routine internal operation | cheap deterministic checks |
| R2 | client-facing preparation | Evidence validation |
| R3 | eligibility / material recommendation | blind independent verification |
| R4 | certification / regulatory publication | independent verification + fresh-source validation + proper authority |
| R5 | government submission / critical reserved action | full AI preparation + required Human/Board authority |

---

## 26. Professional Peer Review Network

Independent verification should evolve beyond calling an arbitrary second model.

Verifier selection should consider capability, jurisdiction, professional specialization, independence, model/provider independence, historical verifier quality, conflicts and capacity.

```text
Primary Specialist
      ↓
blind recommendation

Independent Specialist
      ↓
independent conclusion

Evidence Specialist
      ↓
Evidence integrity

Regulatory Specialist
      ↓
Rule freshness

Decision Readiness
      ↓
Governance
```

---

## 27. AI-to-AI escalation

Uncertainty should normally be resolved within the organization:

```text
Specialist
    ↓
Peer Specialist
    ↓
Senior Specialist
    ↓
Department Head
    ↓
Executive
    ↓
AI CEO
    ↓
Human / Board
```

AIOS distinguishes uncertainty escalation from authority escalation. A fully prepared action may still require Human/Board authority even when uncertainty is low.

---

## 28. Event Nervous System

AIOS should operate proactively rather than waiting for user prompts.

```text
Internal / External Event
        ↓
Event Nervous System
        ↓
Trigger evaluation
        ↓
Policy
        ↓
Mission / WorkItem
        ↓
Employee / Squad
```

Triggers may include government-source changes, Rule review dates, passport/permit expiry, stale Evidence, document upload, authority email, employer response, appointment change, deadline, payment, SLA breach, incident detection and completed dependencies.

Munder trigger/schedule/webhook patterns can accelerate this layer.

---

## 29. Presence and heartbeats

Employee operational states may include:

```text
AVAILABLE
THINKING
RESEARCHING
COLLABORATING
USING_TOOL
WAITING
BLOCKED
VERIFYING
ESCALATED
RECOVERING
OFFLINE
SUSPENDED
```

Heartbeat/health may expose runtime status, last heartbeat, current Mission/WorkItem, queue depth, context pressure, latency, error/retry rate, budget consumption, circuit-breaker state and provider status.

Presence must derive from real runtime state, not fake animation.

---

## 30. Materiality Registry

Not every action belongs behind the same heavy control path.

Useful materiality classes may include:

```text
COGNITIVE
CONVERSATIONAL
COLLABORATIVE
OPERATIONAL
MATERIAL
AUTHORITY
EXTERNAL_CONSEQUENCE
```

This allows governance effort to match actual consequence.

---

## 31. Typed MaterialAction

Material actions should use a typed governance envelope containing concepts such as:

```text
action_type
actor
actor_position
subject
aggregate
expected_version
proposed_change
Evidence refs
Rule refs
rationale
authority context
autonomy context
risk tier
consequence class
Decision Readiness snapshot
policy version
idempotency key
trace identity
timestamp
```

Flexible cognition stays flexible; authoritative mutation does not.

---

## 32. Canonicalization Gateway

Raw provider/model/tool output must not become authoritative AIOS semantics directly.

```text
Model / Agent / Tool
        ↓
Provider-specific result
        ↓
AIOS typed candidate
        ↓
Schema validation
        ↓
Deterministic domain validation
        ↓
Evidence / policy / authority checks
        ↓
Canonical AIOS representation
```

---

## 33. Command Gateway

The Command Gateway is the primary material mutation boundary. It is not a universal human-approval gateway.

```text
Agent
  ↓
MaterialAction
  ↓
Identity / authority
  ↓
Autonomy
  ↓
Risk
  ↓
Evidence
  ↓
Policy
  ↓
Contradictions
  ↓
Expected version
  ↓
Idempotency
  ↓
Command Gateway
  ↓
AUTO EXECUTE or ESCALATE
```

---

## 34. Concurrency and idempotency

High-autonomy organizations create parallel work. AIOS therefore requires expected aggregate versions, idempotency keys, safe retry/backoff, conflict detection, bounded partitions and re-evaluation after stale state.

One authority model must not become one global execution mutex.

---

## 35. Organizational Immune System

The Organizational Immune System remains a cross-cutting quality/safety layer:

```text
Organizational Immune System
│
├── Evidence Integrity Monitor
├── Contradiction Detector
├── Anomaly Detector
├── Decision Readiness Engine
├── Capability Performance Monitor
├── Dynamic Autonomy Manager
├── Circuit Breakers
├── Runtime Health Monitor
├── Rate Protection
├── Budget Protection
├── Blast-Radius Controller
├── Incident Detector
├── Root-Cause Classifier
├── Escalation Router
├── Shadow Evaluation Engine
└── Learning Feedback
```

Munder's circuit-breaker and runtime telemetry ideas should strengthen this layer.

> **Almost invisible during healthy operation; highly capable when abnormal behavior appears.**

---

## 36. Circuit breaking and blast-radius control

A useful combined state model:

```text
HEALTHY
   ↓
STEER
   ↓
CONSTRAIN
   ↓
SUSPEND
   ↓
STOP
```

Interventions may react to repetitive loops, lack of progress, abnormal errors/retries, abnormal tool use, budget/latency spikes, provider instability, policy failures or unusual collaboration patterns.

Blast radius should be constrained to the smallest useful scope: tool, capability, employee, provider/runtime, Mission, case, department, connector or entire organization.

---

## 37. Recovery semantics

Consequential actions need honest recovery classes:

```text
REVERSIBLE
COMPENSATABLE
IRREVERSIBLE
APPEND_ONLY_CORRECTION
```

Incident lifecycle:

```text
Detect
 ↓
Contain
 ↓
Diagnose
 ↓
Recover / compensate
 ↓
Verify
 ↓
Restore authority
 ↓
Learn
```

Government submission is not falsely described as rollback-capable; stronger controls apply before execution.

---

## 38. Tool / Connector Plane

Potential capability classes include browser, official-source retrieval, email, calendar, files, documents, storage, terminal, code tools, GitHub, CRM, employer/HR platforms, government portals, APIs, MCP, Slack/Teams, finance systems and OCR/document processing.

Permanent rule:

```text
Tool availability ≠ authority to use tool consequentially
```

Material tool actions should preserve actor, purpose, scope, result and lineage while never exposing secrets merely for transparency.

---

## 39. Sandbox boundary

Powerful employees require bounded execution environments covering filesystem, network, credentials, shell, production DB, connectors, external actions, runtime, spend and tool installation.

Powerful tools are compatible with high autonomy when authority and consequence boundaries remain explicit.

---

## 40. Organizational Flight Recorder

Decision Lineage explains why a decision exists. The Organizational Flight Recorder reconstructs how the organization operated around it.

For a material outcome it should be possible to reconstruct:

```text
Mission
Delegation
WorkItems
Agent identities
AgentRuns
ContextBundles
Conversations
Provider/models
Skills
Tools
Evidence
VerifiedRules
Policy decisions
Verification
Command Gateway
Canonical effects
Cost
Latency
Retries
Incidents
Recovery
Outcome
```

This becomes foundational for Board Transparency, incident investigation, debugging, compliance, learning, replay and autonomy evaluation.

---

## 41. Replay / counterfactual evaluation

Historical work should eventually be replayable without real-world consequence using a new model, prompt/program, ContextBundle strategy, team, Skill, workflow, verifier or newer Rules.

Compare quality, grounding, readiness, cost, latency, tool reliability, human modification and risk before changing production behavior.

---

## 42. Shadow Employees

Shadow evaluation should support complete shadow employee configurations:

```text
Production employee
        │
        ├──── real authorized result
        │
        └──── Shadow employee
                    │
                 no authority
                    │
             independent result
                    │
                 comparison
```

Shadow Employees can safely test new models/providers, programs, Skills, routing policies, team structures and proposed autonomy increases.

---

## 43. Organizational learning

AIOS should improve from outcomes rather than merely accumulate conversations:

```text
Outcome
  ↓
Evaluation
  ↓
LearningRecord
  ↓
Pattern detection
  ↓
Improvement proposal
  ↓
Replay / shadow validation
  ↓
Governed adoption
```

Possible improvements include runtime selection, prompts/programs, ContextBundle composition, team composition, Skills, workflow, routing, retrieval, verification strategy, autonomy and capacity.

---

## 44. LearningRecords, curation and retention

AIOS should distinguish raw telemetry, conversation history, material records, LearningRecords and CuratedLearningExamples.

High-volume conversational traces may be summarized or compressed according to policy. Material decisions and authority events require stronger durability. Curated learning examples require provenance, sensitivity and data-usage controls.

---

## 45. AI Economics

Munder token/cost telemetry should evolve into organizational economics measured by organization, department, Mission, case, employee, capability, provider, model and Skill/tool.

Routing should optimize:

```text
Quality × Risk × Latency × Cost
```

not cost alone.

Budgets may exist at organization, department, Mission, employee, capability, tool and provider levels. Budget controls must never force unsafe quality degradation for high-risk work.

---

## 46. Performance and scalability doctrine

Permanent principles:

1. **Pay for risk** — verification cost scales with consequence, uncertainty and novelty.
2. **Recompute only what changed** — Evidence/readiness/policy state should be incremental and version-aware.
3. **Load only what is needed** — ContextBundles are purpose-scoped, lazy and composable.
4. **Block only when necessary** — support PRE_COMMIT, POST_COMMIT and BACKGROUND verification where appropriate.
5. **Centralize governance, distribute execution** — one authority model does not require one global mutex.
6. **Cache only exact governed state** — verifier reuse must bind exact facts/Evidence/Rules/policy/program/model versions.
7. **Instrument from day one** — measure latency, cost, retries, freshness, verification cost, incidents, Board workload, autonomy and transparency lag.

Conceptual rule:

> **Governance Cost ∝ Risk × Uncertainty × Novelty**

---

## 47. Evidence and Trust Model

Global Mobility operates in domains where plausible output can still be dangerously wrong.

```text
L0  model speculation
L1  conversation / memory / hypothesis
L2  retrieved information
L3  captured SourceSnapshot
L4  governed Evidence
L5  reviewed candidate
L6  VerifiedRule / certified governed fact
L7  governed case conclusion
L8  approved authority-bearing action
```

Forbidden shortcuts:

```text
L1 ↛ L6
L2 ↛ L7
L6 ↛ L8 automatically
```

Permanent distinctions:

```text
memory != Evidence
memory != VerifiedRule
conversation != authority
provider output != canonical truth
```

---

## 48. Official-source and regulatory intelligence

AIOS should preserve OfficialSources, SourceSnapshots, retrieval timestamps, source hashes, jurisdiction, effective dates, candidate rules, review state, VerifiedRules and supersession/version history.

A changed webpage is not automatically a certified legal rule.

---

## 49. Document intelligence

Target capabilities include ingestion, OCR, parsing, classification, extraction, consistency checks, metadata/provenance, sensitivity classification, Evidence linking, expiry detection, missing-document detection, contradiction detection and professional output generation.

Third-party tools remain adapters below AIOS semantics.

---

## 50. Privacy and sensitivity

Board Transparency must coexist with lawful sensitivity controls for identity data, medical Evidence, privileged communications, personnel data, financial information, immigration history and credentials.

```text
Board Transparency + Sensitivity Controls
```

Sensitivity controls protect data; they do not create hidden agent authority.

---

## 51. Living Organization

Munder's pixel-office concept survives only as a runtime/interaction donor. The visual experience is completely transformed.

> **Living Organization is a premium modern 2D/2.5D animated representation of the actual AI organization, populated by persistent modern cartoon AI employees whose visible behavior derives from real organizational state.**

It should be modern, premium, expressive, professional, inspectable and truthful.

It must not become retro pixel art, fake NPC busywork, photorealistic fake humans, dark sci-fi or cheap gamification.

---

## 52. Modern cartoon AI employees

Every persistent employee may receive a distinctive modern stylized character identity reflecting department, specialization, seniority and operational state.

Example:

```text
MARA
Austria Immigration Specialist

● Researching

Mission
AT-4821

Working with
Elena — Evidence Specialist
Noah — Regulatory Intelligence

Current Activity
Validating employment Evidence

Research              A5
Eligibility           A4
Client Communication  A3
```

Professional identity remains primary; visual progression should not become arbitrary game XP.

---

## 53. Semantic animation

Visible movement must represent real activity:

```text
Employee approaches another employee
→ real AgentConversation

Several employees cluster
→ real collaboration

Employee enters Mission Room
→ active Mission participation

Cross-department movement
→ real handoff/delegation

Employee enters review space
→ independent verification

Warning state
→ Immune System intervention

AI CEO appears
→ actual executive involvement

Employee approaches Board Room
→ real authority escalation

Mission Room closes
→ Mission completed/closed
```

No fabricated activity should be created merely to make the interface look alive.

---

## 54. Living Organization as transparency navigation

The Living Organization is also a navigation layer into organizational truth:

```text
Organization
→ Department
→ Mission
→ Squad
→ Employee
→ Conversation
→ Decision
→ Tool
→ Evidence
→ Rule
→ Outcome
```

It complements the Organization/Decision Graph: the Living Organization provides situational awareness; the graph provides lineage/causal investigation.

---

## 55. Global Mobility AIOS Cockpit

The Cockpit is the top-level Human Owner / Board surface.

It should answer:

> **Is my organization healthy, effective, grounded, transparent and operating inside the authority I granted it?**

Target modules:

```text
Cockpit
│
├── Overview
├── Organization
│   └── Living Organization
├── Missions
├── Departments
├── Workforce
├── Intelligence
├── Decisions
├── Performance
├── Quality
├── Risk
├── Autonomy
├── Transparency
├── Immune System
├── Incidents
├── AI Economics
├── Organizational Learning
├── Search / Intelligence
└── Board Room
```

Board Room remains a module inside Cockpit, not the name of the entire Owner experience.

---

## 56. Operations, My Mobility and external-role surfaces

**Operations** is the professional/operator environment for cases, Evidence, documents, applications, review, exceptions, blockers, submission readiness, authority workflow and remediation.

**My Mobility** is the journey-centric end-user experience for goals, pathways, progress, Evidence needs, documents, deadlines, appointments, costs, risk, messages, application status, next actions and future mobility.

Employer, partner, HR, adviser and authority-facing surfaces should reuse the same canonical state, identity, Evidence and permission model rather than inventing parallel truths.

---

## 57. Executive conversation and voice

Munder realtime/voice ideas may become a future Cockpit interaction mode:

- "Give me today's organizational brief."
- "Why is Austria Operations elevated?"
- "Show unresolved R4 decisions."
- "Which employees are autonomy-promotion candidates?"
- "Why was case AT-4821 escalated?"

Voice/chat is an interface over governed AIOS information, never a governance bypass.

---

## 58. Engineering workforce

Munder's coding-focused capabilities are particularly useful for AIOS Engineering employees. CLI agents, PTY execution, Git worktrees, terminal, IDE concepts, diff/history and tool telemetry can support isolated parallel engineering Missions.

These belong in a specialized Engineering Workspace rather than ordinary mobility-user surfaces.

---

## 59. Munder Difflin v0.4.4 donor mapping

| Munder capability | AIOS decision |
|---|---|
| Hive messaging | ADAPT heavily |
| Message routing | ADAPT heavily |
| Agent roster/runtime identity | map to existing OrganizationPosition |
| GOD orchestration | REIMPLEMENT as AI CEO hierarchy |
| Skills system | ADAPT into Capability Registry |
| Provider/runtime abstraction | ADAPT into Agent Runtime Fabric |
| PTY/CLI execution | ADOPT as optional runtime |
| Task coordination | map into Mission/WorkItem |
| Circuit breaker | ADAPT into Immune System |
| Triggers/schedules | ADAPT into Event Nervous System |
| Webhook/integration broker | ADAPT |
| Slack integration | ADAPT where useful |
| Memory mechanics | ADAPT below AIOS trust boundary |
| Shared blackboard | transform into Mission Rooms |
| Transcripts | ADAPT into Transparency/Flight Recorder |
| Token/cost telemetry | ADAPT into AI Economics |
| Tool waterfall | transform into Decision/Execution Timeline |
| Memory graph | transform into Organization/Decision Graph |
| Worktrees | ADOPT for engineering employees |
| IDE | specialized Engineering Workspace |
| Voice/realtime | future executive interaction |
| Pixel office | REIMPLEMENT completely |
| Live-scene/event mechanics | potentially ADAPT |
| SQLite/file state as authority | REJECT |
| GOD implicit authority | REJECT |
| direct agent mutation of authoritative state | REJECT |

Each donor subsystem should be classified as DIRECT REUSE, PORT, ADAPT, REIMPLEMENT or REJECT before implementation.

---

## 60. Data and semantic sovereignty

External platforms may parse, retrieve, execute, render, observe, scan, evaluate or store technical artifacts. They must not become authoritative for AIOS domain meaning.

AIOS owns:

- Evidence status;
- VerifiedRule status;
- legal/domain meaning;
- publication state;
- human-review requirements;
- organizational authority;
- semantic Activity;
- material business outcomes.

> **External infrastructure provides capability. AIOS owns meaning and authority.**

---

## 61. Target domain entities

Existing durable organization concepts include `OrganizationPosition`, `OrganizationalWorkItem`, `OrganizationBlocker`, `OrganizationWorkItemDependency`, `OrganizationHumanActionRequest`, `OrganizationContribution` and `OrganizationActivity`.

The combined target domain may expand toward:

```text
AgentCapability
AgentAuthority
AutonomyEvidenceProfile
AgentRuntimeProfile
Mission
MissionSquad
MissionRoom
ContextBundle
AgentRun
AgentConversation
AgentMessage
ConversationSummary
AgentRelationship
MaterialAction
DecisionReadinessSnapshot
ConsequentialActionProposal
IndependentVerification
HumanReview
BoardDecision
DecisionLineage
ToolActionRecord
PolicyDecision
Incident
CircuitBreakerEvent
RecoveryAction
LearningRecord
CuratedLearningExample
ShadowEvaluation
ReplayEvaluation
```

These are target concepts; their appearance here does not claim every entity is already implemented.

---

## 62. Performance and success metrics

AIOS should increase autonomous completion, quality, Evidence grounding, decision traceability, Board transparency, capability reliability and recovery effectiveness while reducing critical errors, Board operational workload, false/missed escalations, cost per successful outcome, latency, rework and opaque activity.

Metrics should include:

- autonomous completion rate;
- Board decisions per material actions;
- human interventions;
- Evidence grounding;
- human modification/rejection;
- verifier disagreement;
- contradiction rate;
- source freshness;
- capability reliability;
- workflow completion time;
- p50/p95 latency;
- cost per workflow;
- retries/stale-state conflicts;
- incident frequency;
- recovery success;
- lineage completeness;
- transparency lag;
- employee utilization;
- queue depth;
- autonomy distribution;
- tool reliability.

---

## 63. Delivery dependency rule

The implementation dependency remains:

```text
Governance / Constitutional Contracts
          ↓
Transparency Foundation
          ↓
Context + Organization Semantics
          ↓
Munder-derived Organization Fabric
          ↓
Powerful execution
          ↓
Living Organization
          ↓
Organizational Learning
```

> **Governance before unrestricted execution. Transparency before increased autonomy.**

---

## 64. Permanent architectural invariants

1. Human Owner / Board is supreme authority.
2. Board governs by exception.
3. Transparency is a right, not an approval requirement.
4. Operational autonomy must never create organizational opacity.
5. Memory is not canonical truth.
6. Evidence provides authority.
7. Capability ≠ Authority ≠ Autonomy ≠ Risk.
8. Autonomy is capability-specific.
9. Agents cannot self-promote autonomy.
10. Scores route; gates authorize.
11. Risk determines verification cost.
12. Independent verification should be genuinely independent.
13. Conversation does not create authority.
14. Provider output does not become canonical truth automatically.
15. Context should be purpose-scoped and lazy.
16. Material actions cross typed governance boundaries.
17. Command Gateway is the material mutation boundary.
18. Governance enables autonomy rather than creating universal approval queues.
19. Concurrency is versioned and idempotent.
20. Consequential actions require honest recovery semantics.
21. External frameworks provide capability; AIOS owns meaning.
22. Live organization visuals reflect real organizational activity.
23. The organization learns from outcomes through governed LearningRecords.
24. Global Mobility remains the product specialization.
25. Munder Difflin is a donor subsystem, not the governing architecture.

---

## 65. Final north-star statement

> **Global Mobility AIOS is a governed, transparent, self-improving, high-autonomy AI-operated professional organization for global mobility. Persistent AI employees operate under an AI CEO, executive hierarchy and Human Owner / Board constitution; belong to durable departments; form dynamic cross-functional Mission Squads; communicate through an organizational messaging fabric; receive purpose-scoped truth through a Context Broker; use provider-independent AI runtimes, Skills, tools and connectors; maintain working, personal and institutional memory; and proactively respond to events across the complete mobility lifecycle.**
>
> **Their power is bounded through explicit separation of Capability, Authority, Autonomy and Risk; capability-specific Earned Autonomy from A0 to A5; risk-tiered verification from R0 to R5; Decision Readiness; a Materiality Registry; Canonicalization and Command Gateways; and an Organizational Immune System capable of detecting, containing, recovering from and learning from abnormal behavior.**
>
> **Every material organizational outcome remains reconstructable through Decision Lineage, Conversation and Tool Lineage, a cross-cutting Transparency Layer and an Organizational Flight Recorder. The Human Owner / Board retains supreme authority and can inspect or intervene throughout the organization without being forced to approve healthy routine work.**
>
> **Munder Difflin v0.4.4 serves as a frozen upstream technology donor for the AIOS Organization Fabric—particularly communication, runtime/provider abstraction, Skills, coordination, circuit breaking, triggers, presence, telemetry, memory mechanics, integrations and live-organization mechanics—while AIOS retains exclusive ownership of organizational meaning, Evidence, authority, canonical state, governance and Global Mobility domain truth.**
>
> **The organization is made visible through the Global Mobility AIOS Cockpit and its Living Organization: a premium modern 2D/2.5D environment with persistent modern cartoon AI employees, Mission spaces and semantic animation driven by genuine runtime state rather than fabricated activity.**

Short form:

> **AIOS is not an application containing agents. It is a governed AI organization that happens to expose itself through software.**
