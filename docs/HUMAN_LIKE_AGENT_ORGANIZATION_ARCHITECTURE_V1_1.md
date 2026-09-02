# Global Mobility AIOS — Human-Like High-Autonomy Organization Architecture V1.1

**Date:** 2026-08-19  
**Status:** CANONICAL ARCHITECTURE DIRECTION / PARALLEL IMPLEMENTATION TRACK  
**Supersedes for active direction:** [HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1.md](HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1.md)  
**Runtime impact of this document:** none by itself  
**Active product work:** Phase 13.17 owner-led human acceptance remains in progress / paused  

---

## 1. Owner decision and purpose

Global Mobility AIOS will continue to build the core product and the platform architecture **in parallel**.

The project will not stop broad architecture/platform evolution until one tiny Coworker workflow is validated first. Human acceptance, product correction, document/privacy intelligence, organization architecture, and future agent-execution capabilities may advance as parallel bounded tracks, provided each implementation slice preserves the established acceptance, authority, evidence, security, rollback, and repository discipline.

The target organization remains:

> **Human in interaction. Machine-like in reliability.**

The additional V1.1 control objective is:

> **Broad cognition. Scoped context. Narrow mutation. Deterministic authority. Reversible execution.**

The organization should feel like capable colleagues who talk, reason, help one another, prepare work, challenge each other, and deliver results. It should not feel like a collection of sterile RPC agents. At the same time, ordinary conversation, memory, model output, provider logs, or agent confidence must never silently corrupt authoritative AIOS state.

Permanent principles:

> **Natural interaction, deterministic accountability.**

> **Team outcomes over agent competition.**

> **Activity is broad; authority is narrow.**

> **Results matter more than provider competition.**

> **Agents may be creative in cognition. AIOS must be conservative in truth.**

> **Consequential actions are proposal-first unless an explicitly bounded autonomy policy permits direct execution.**

> **Autonomy is capability-specific, measurable, reversible, and never self-granted.**

---

## 2. Updated target architecture

```text
                           HUMAN OWNER / BOARD
                                    │
                                    ▼
                      GLOBAL MOBILITY AIOS COCKPIT
                                    │
                          Owner Command / Oversight
                                    │
                                    ▼
                                  AI CEO
                                    │
                                    ▼
                         ORGANIZATION OS / DOMAIN TRUTH
                                    │
             ┌──────────────────────┼──────────────────────┐
             ▼                      ▼                      ▼
         Positions              Work Graph              Authority
         Departments            Missions                Evidence
         Relationships          WorkItems               Decisions
         Conversations          Dependencies            Human Gates
             │                      │                      │
             └──────────────────────┼──────────────────────┘
                                    ▼
                         AIOS CONTEXT BROKER
                                    │
                task / tenant / purpose / sensitivity scoped
                                    │
                                    ▼
                       AGENT ORGANIZATION FABRIC
                                    │
                  ┌─────────────────┼─────────────────┐
                  ▼                 ▼                 ▼
            Communication       Coordination        Memory
                  │                 │                 │
                  └─────────────────┼─────────────────┘
                                    ▼
                           AGENT COGNITION
                   reason / search / collaborate / plan
                     remember / draft / recommend / propose
                                    │
                                    ▼
                            PROPOSED INTENT
                                    │
                                    ▼
                    AIOS CANONICALIZATION GATEWAY
                        "What does this actually mean?"
                                    │
                                    ▼
                          AIOS COMMAND GATEWAY
                                    │
                  ┌─────────────────┼─────────────────┐
                  ▼                 ▼                 ▼
             Authority          Grounding         Consistency
               Policy            Evidence         Contradiction
                  │                 │                 │
                  └─────────────────┼─────────────────┘
                                    ▼
                       CONSEQUENCE CLASSIFICATION
                                    │
                 ┌──────────────────┼──────────────────┐
                 ▼                  ▼                  ▼
             Internal          Consequential       Prohibited /
          bounded action         proposal           unsupported
                 │                  │                  │
                 ▼                  ▼                  ▼
         execute if allowed    Human Review       reject / retry /
                              Approve / Modify     peer / specialist
                                    │
                                    ▼
                            DOMAIN COMMAND
                                    │
                         atomic / versioned write
                                    │
                   ┌────────────────┴────────────────┐
                   ▼                                 ▼
                reject                              commit
                   │                                 │
          self-correct / retry                       ▼
          peer / specialist                canonical AIOS state
                   │                                 │
                   └─────────────────────────────────┼─────────────┐
                                                     ▼             ▼
                                           OrganizationActivity  Audit
                                                     │
                                                     ▼
                                            Learning & Quality
```

AIOS remains authoritative for domain meaning, case state, evidence, VerifiedRules, certification, publication, Missions, WorkItems, Decisions, Contributions, canonical OrganizationActivity, human-review requirements, authority and business outcomes.

External systems provide capability, transport, execution, memory mechanics, visualization, telemetry, or finished-work tooling. They do not define AIOS truth.

---

## 3. Parallel project strategy

The project proceeds through parallel tracks rather than a stop-and-wait model.

### Track A — Product / Human Experience

- Phase 13.17 owner-led human acceptance;
- bounded correction of genuine usability/comprehension findings;
- Professional / Operator workflow refinement;
- Mobility User and Cockpit refinement;
- role separation and traceability.

### Track B — Technology Radar / Platform Evolution

- Wave 2 document/privacy intelligence;
- Wave 3 regulatory monitoring;
- Wave 4 AI runtime/retrieval/quality;
- Wave 6 professional output where justified.

### Track C — Human-Like Organization / Agent Control Plane

- Context Broker;
- Canonicalization Gateway;
- Command Gateway;
- capability-scoped autonomy;
- Consequential Action Proposals;
- Mission / Conversation / Activity semantics;
- Munder Difflin organization patterns;
- OpenWorker finished-work patterns;
- Live Organization;
- Learning & Quality.

These tracks may advance in parallel. A track may not weaken another track's accepted invariants.

---

## 4. Munder Difflin + OpenWorker — cooperate under AIOS

Global Mobility AIOS does not need an artificial framework winner when complementary capabilities produce better results.

### Munder Difflin — A+ Agent Organization reference

Primary reference areas:

- persistent organizational identities;
- agent-to-agent communication;
- mailboxes and conversation routing;
- shared working context;
- position/department memory patterns;
- supervisor/orchestrator patterns;
- dependency-aware coordination;
- scheduled missions / heartbeat;
- human intervention patterns;
- budgets and cost telemetry;
- progressive circuit breaking;
- skills/capability discovery;
- live organization visualization;
- direct conversation with individual agents.

### OpenWorker — A+ Finished-Work / Coworker reference

Primary reference areas:

- real deliverables rather than chat-only answers;
- files and artifact production;
- tools / terminal execution;
- MCP;
- connectors;
- scheduled work;
- external application actions;
- model portability;
- approval-gated consequential actions;
- unattended approval inbox patterns;
- local-first coworker patterns.

### Combined architecture rule

```text
Munder Difflin strengths
        +
OpenWorker strengths
        +
AIOS-native services / agents / deterministic logic
        ↓
AIOS Execution Broker
        ↓
best governed capability composition for the Mission
```

The Execution Broker optimizes for result quality, SLA, evidence requirements, workload, capability, cost, safety, human-review requirements, privacy/data-use constraints, provider health and fallback availability.

Framework neatness is not the goal. **Governed results are.**

---

## 5. Broad cognition does not mean unrestricted data access

Agents should receive enough relevant context to reduce guessing and hallucination, but not unlimited unrelated client data.

The canonical rule is:

```text
broad reasoning capability
        +
scoped authorized context
        =
useful cognition without unnecessary exposure
```

### AIOS Context Broker

The Context Broker prepares a task-relevant `ContextBundle`.

Conceptually:

```text
ContextBundle
  mission
  case
  profile
  relevant_documents
  relevant_evidence
  relevant_source_snapshots
  verified_rules
  active_pathway_context
  current_work_items
  blockers
  recent_conversations
  applicable_decisions
  known_unknowns
  contradictions
  authority_scope
  data_usage_constraints
```

Before exposing context, AIOS evaluates:

- tenant;
- authenticated actor / position;
- Mission purpose;
- case relationship;
- sensitivity classification;
- minimum-necessary data;
- jurisdiction;
- data-use policy;
- tool/provider recipient;
- retention/export restrictions.

Agents should not query the authoritative database arbitrarily when an AIOS-owned context contract can provide the needed information.

---

## 6. Natural conversation remains OrganizationActivity

The canonical relationship remains:

```text
AgentMessage ⊂ OrganizationActivity
```

Agents may naturally:

- ask questions;
- clarify;
- suggest;
- disagree;
- acknowledge;
- request help;
- hand work over;
- warn colleagues;
- peer review;
- discuss hypotheses;
- report progress;
- coordinate informally;
- close a conversation.

Not every conversation needs a WorkItem, formal decision, approval or human intervention.

The safety distinction is:

```text
conversation = organizational activity
conversation != authority
```

Conversation may **contain or create an intent** that later becomes a governed action.

---

## 7. Five hard canonicalization invariants

These relationships are permanent:

```text
conversation != authority
message != ExecutiveDecision
memory != Evidence
memory != VerifiedRule
provider event log != canonical AIOS Activity automatically
```

But the system must allow useful promotion paths.

### 7.1 Conversation → authority-bearing intent

```text
Conversation
   ↓
understanding / agreement / instruction
   ↓
Intent Candidate
   ↓
AIOS Canonicalization
   ↓
Command / Proposal
   ↓
validation + applicable approval
   ↓
canonical action / Decision
```

### 7.2 Message → ExecutiveDecision candidate

A CEO/executive message may contain a decision intent, but AIOS must validate identity, position, current authority, scope, required evidence, state preconditions and any human gate before creating the canonical `ExecutiveDecision`.

### 7.3 Memory → evidence discovery

```text
Memory
   ↓
search hint / hypothesis
   ↓
retrieve governed source/evidence
   ↓
validate
   ↓
Evidence if requirements are met
```

Memory helps locate truth. It does not manufacture truth.

### 7.4 Memory → VerifiedRule investigation

```text
Memory: "Austria threshold may have changed"
   ↓
Regulatory Intelligence Mission
   ↓
official source retrieval
   ↓
immutable snapshot
   ↓
rule candidate
   ↓
required source/certification review
   ↓
VerifiedRule
```

### 7.5 Provider event → canonical Activity

```text
Munder / OpenWorker / Temporal / model / tool event
   ↓
RawExecutionEvent
   ↓
AIOS Event Normalizer
   ↓
classify
   ├── telemetry only
   ├── conversational Activity
   ├── operational Activity
   ├── material Activity
   └── authority-bearing intent
   ↓
AIOS-owned canonical state where appropriate
```

Provider storage is not the canonical record merely because an event occurred.

---

## 8. AIOS Canonicalization Gateway

The Canonicalization Gateway converts non-authoritative agent/provider information into explicitly classified AIOS meaning.

Inputs may include:

- agent messages;
- agent memory;
- provider event logs;
- model outputs;
- tool results;
- OCR;
- retrieval;
- source monitoring;
- OpenWorker events;
- Munder Difflin events;
- external connector events.

Outputs may include:

- telemetry-only event;
- OrganizationActivity;
- AgentConversation event;
- WorkItem proposal;
- Blocker proposal;
- Mission proposal;
- Evidence candidate;
- VerifiedRule candidate;
- ExecutiveDecision candidate;
- ConsequentialActionProposal;
- unsupported/conflicted result requiring retry.

It answers:

> **What does this information actually mean inside AIOS?**

It does not itself grant authority or bypass domain services.

---

## 9. AIOS Command Gateway

Authoritative writes should occur through typed AIOS commands rather than raw model/database mutation.

Example command families:

```text
CreateMission
CreateWorkItem
AssignWorkItem
ReassignWorkItem
CreateBlocker
ResolveBlocker
RecordConversationActivity
CreateEvidenceCandidate
ProposeVerifiedRule
ProposeEligibilityChange
ProposeEvidenceCertification
ProposeClientStatusChange
PrepareExternalCommunication
ProposeApplicationSubmission
ApproveConsequentialAction
RejectConsequentialAction
ModifyConsequentialAction
ExecuteApprovedAction
```

Before an authoritative mutation, the Command Gateway checks:

- actor identity;
- position / authenticated human role;
- deterministic authority;
- capability scope;
- tenant / case scope;
- preconditions;
- evidence sufficiency;
- contradictions;
- current version / supersession;
- required human/professional/source/certification gate;
- idempotency / duplicate protection;
- transaction safety.

Agents can be intelligent and proactive because the domain layer remains conservative.

---

## 10. Consequential Action Proposal — first-class human collaboration

For high-impact operations, the agent's job is primarily to **prepare, explain and propose**.

The appropriate human reviews the proposal, may modify it, and approves or rejects execution.

This is not the same as asking the Board about everything. Review stays at the **lowest appropriate human surface**.

Conceptually:

```text
ConsequentialActionProposal
  proposal_id
  action_type
  requested_by_agent_or_position
  related_mission_id
  related_case_id
  proposed_payload
  rationale
  evidence_refs
  source_refs
  verified_rule_refs
  assumptions
  uncertainties
  contradictions
  impact_summary
  side_effects
  reversible
  required_reviewer_role
  status
  created_at
  expires_at?
```

Lifecycle:

```text
DRAFT
  ↓
PROPOSED
  ↓
HUMAN REVIEW
  ├── APPROVE
  ├── MODIFY
  ├── RETURN FOR REVISION
  └── REJECT
  ↓
APPROVED
  ↓
EXECUTE
  ↓
VERIFY RESULT
  ↓
COMPLETED / FAILED / PARTIAL
```

A modification produces a traceable human-owned revision rather than silently altering the agent proposal.

---

## 11. Consequential actions approved for proposal-first architecture

The following actions are explicitly designed as **agent-helpful, human-approved** operations.

### 11.1 Send email / external communication

Agent may autonomously:

- determine that communication is useful;
- draft the message;
- select proposed recipients from authorized context;
- prepare attachments;
- explain purpose;
- cite supporting case/evidence context;
- create the proposal.

Human review surface shows:

```text
To
CC
Subject
Body
Attachments
Why this is being sent
Related Mission / Case
Potential side effects
```

Human may:

- edit text;
- add/remove recipient;
- add/remove attachment;
- approve/send;
- return to agent;
- reject.

The agent does not silently send the external message unless a separately approved bounded autonomy policy later permits that exact communication class.

### 11.2 Change eligibility

Agent may:

- re-evaluate relevant case facts;
- compare them with current VerifiedRules/pathway context;
- identify differences from the current assessment;
- explain evidence and uncertainty;
- propose a new eligibility state/version.

Human/professional sees:

```text
Current eligibility
Proposed eligibility
What changed
Supporting evidence
VerifiedRules used
Missing facts
Contradictions
Impact on case
```

Approval creates/version-promotes the governed assessment according to existing domain rules. Rejection leaves the prior valid state untouched.

### 11.3 Certify evidence

Agent may:

- extract/classify evidence;
- compare evidence against requirement criteria;
- identify provenance/integrity gaps;
- prepare a certification recommendation;
- explain uncertainty;
- assemble supporting evidence.

The qualified human reviewer may approve, modify/annotate, request more evidence, or reject certification.

Machine confidence alone cannot certify evidence.

### 11.4 Submit application

Agent/OpenWorker may:

- assemble the submission pack;
- pre-fill permitted fields;
- check completeness;
- prepare attachments;
- run deterministic validation;
- identify unresolved gaps;
- prepare a submission preview.

The authorized human reviews the exact payload and approves/changes/rejects submission.

The external submit side effect occurs only after approval.

### 11.5 Change VerifiedRule

Regulatory agents may:

- monitor sources;
- detect change;
- retrieve/capture immutable official-source snapshots;
- extract a candidate rule;
- compare against current rule/version;
- identify effective dates/supersession;
- create a proposed VerifiedRule change.

The required source/certification/human reviewer may approve, modify interpretation, return for more evidence, or reject.

No model, memory, source diff or provider event can silently publish/change a VerifiedRule.

### 11.6 Change client status

Agent may:

- infer that a status transition may be appropriate;
- explain triggering evidence/workflow state;
- show current and proposed status;
- describe downstream effects;
- create a proposal.

Professional/authorized human may approve, modify or reject.

No proposal should destroy the previous valid state before approval.

---

## 12. Proposal Inbox / Human Review UX

High-impact agent work should feel helpful, not bureaucratic.

A Professional, department lead, executive or Owner should see a compact queue such as:

```text
PROPOSAL
────────────────────────────────────────
Agent: Operations Case Agent
Case: AT-204
Action: Send client follow-up
Reason: Financial proof and admission letter missing

Prepared:
✓ email draft
✓ recipient
✓ missing-document list
✓ case link

[Approve & Send]
[Modify]
[Return to Agent]
[Reject]
```

Or:

```text
PROPOSED ELIGIBILITY UPDATE
────────────────────────────────────────
Current: Needs Documents
Proposed: Ready for Professional Review

Why:
✓ Passport verified
✓ Financial proof received
✓ Admission letter received
○ Insurance still needs review

[Approve]
[Modify]
[Return]
[Reject]
```

The user should not need to understand internal authority jargon to perform ordinary review.

---

## 13. Truth / evidence ladder

AIOS should formalize different trust levels.

```text
L0  Model speculation / ungrounded thought
L1  Agent conversation / memory / working hypothesis
L2  Retrieved external information
L3  Captured source snapshot
L4  Governed Evidence
L5  Reviewed rule / evidence candidate
L6  VerifiedRule / certified governed fact
L7  Governed case conclusion
L8  Authority-bearing decision / approved external action
```

Hard rules:

```text
L1 cannot jump directly to L6
L2 cannot jump directly to L7
L6 does not automatically create L8
```

The required transition path depends on domain and action type.

---

## 14. Evidence sufficiency, not model self-confidence

Model confidence is useful as metadata but is not a permission mechanism.

Material outputs should provide structured grounding such as:

```text
AgentResult
  claim
  support_state
  supporting_evidence_ids
  supporting_source_ids
  verified_rule_ids
  assumptions
  uncertainties
  contradictions
  missing_facts
  recommended_action
  requested_action_type
```

Possible `support_state` values:

- unsupported;
- weakly_supported;
- supported;
- strongly_supported;
- conflicted;
- superseded;
- unknown.

A material conclusion with no required supporting evidence can be rejected even if the model says it is highly confident.

---

## 15. Contradiction detection

Before accepting material proposals, AIOS should compare them against:

- current VerifiedRules;
- governed Evidence;
- source authority;
- source/effective dates;
- supersession;
- current pathway version;
- current case facts;
- existing ExecutiveDecisions;
- prior approved state.

Example:

```text
Agent proposes: salary threshold = X
        ↓
Conflict Detector
        ↓
current VerifiedRule = Y
        ↓
CONFLICTED
        ↓
no mutation
        ↓
return to agent with exact conflict references
```

The agent should usually receive a chance to self-correct before a human is asked to intervene.

---

## 16. Self-correction and peer/specialist validation

Default recovery ladder for mistakes/uncertainty:

```text
unsupported / conflicted result
        ↓
SELF-CORRECT with better context/evidence
        ↓
PEER REVIEW where useful
        ↓
SPECIALIST / DEPARTMENT REVIEW
        ↓
HUMAN REVIEW only where still required
```

Peer agreement is not truth. Two agents may share the same model, prompt or evidence error.

For high-risk work, prefer different verification mechanisms:

- deterministic validation;
- independent source retrieval;
- contradiction checking;
- specialist reasoning;
- source/certification review;
- human judgement where required.

---

## 17. Capability Registry and scoped autonomy

Agents should receive typed capabilities rather than raw unrestricted database/tool access.

Capability classes:

```text
READ
ANALYSE
DRAFT
PROPOSE
EXECUTE_INTERNAL
EXECUTE_EXTERNAL
CERTIFY / PUBLISH / RESERVED
```

Example:

```text
Evidence Agent

READ
✓ documents
✓ evidence
✓ official-source snapshots

ANALYSE
✓ OCR/extraction
✓ classify
✓ compare
✓ detect gaps

PROPOSE
✓ evidence relationship
✓ certification recommendation

NOT DIRECT
× evidence certification
× final legal conclusion
× authority submission
```

### Capability-specific autonomy levels

```text
A0  prohibited
A1  human execution required
A2  human approval required
A3  autonomous with mandatory post-review
A4  autonomous with monitoring / rollback
A5  fully autonomous bounded internal operation
```

Autonomy attaches to **capability + context**, not simply to an agent identity.

Example:

```text
Global Intelligence Agent
source search              A5
snapshot capture           A5
candidate extraction       A4
VerifiedRule proposal      A3/A4
VerifiedRule publication   A2 or A1 depending contract
```

```text
OpenWorker capability
create internal DOCX       A5
draft client email         A5
send client email          A2
submit authority form      A2/A1
```

An agent cannot increase its own autonomy.

Performance may create an `AutonomyChangeRecommendation`, but meaningful authority expansion remains governed.

---

## 18. AIOS Execution Sandbox

Powerful agent runtimes should execute inside bounded environments.

Controls may include:

```text
filesystem       workspace-scoped
network          allowlisted / purpose-scoped
secrets          capability-specific
production DB    no arbitrary direct mutation
shell            bounded / sandboxed
connectors       scoped credentials
execution time   bounded
model/token cost bounded
external actions proposal/approval gated
logging          mandatory
rollback         defined where possible
```

The Execution Broker selects an execution profile appropriate to the Mission.

---

## 19. Atomic, versioned and reversible state

An agent mistake should not corrupt the previous accepted state.

```text
current authoritative state
        ↓
proposal
        ↓
validation / approval
        ├── fail → previous state unchanged
        └── pass → atomic commit
```

Prefer versions/supersession over destructive overwrites for material states such as:

- eligibility assessments;
- pathway comparisons;
- rule candidates;
- evidence interpretations;
- Mission plans;
- client communication drafts;
- professional reports.

For irreversible external actions, store the exact approved proposal, execution request and external result.

---

## 20. Mission, WorkItem and Dynamic Squad

`Mission` remains the outcome-level concept above WorkItems.

A Mission may contain:

- objective;
- Definition of Done;
- Mission owner;
- service class / SLA;
- KPI targets;
- participating positions;
- WorkItems;
- conversations;
- dependencies;
- blockers;
- artifacts;
- Consequential Action Proposals;
- decisions;
- outcome.

Dynamic Squads allow temporary cross-department collaboration around a Mission without destroying the permanent organization chart or authority structure.

---

## 21. SLA / KPI / OKR / Definition of Done

Human-like interaction must never reduce execution discipline.

### SLA

Potential fields:

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

Suggested classes:

- Critical;
- Priority;
- Standard;
- Background.

### KPIs

Delivery:

- Mission completion rate;
- SLA attainment;
- cycle time;
- blocker age;
- handoff latency;
- response latency.

Quality:

- first-pass quality;
- professional agreement;
- human correction rate;
- material correction rate;
- rework;
- evidence grounding;
- provenance completeness.

Collaboration:

- successful collaboration;
- unnecessary handoffs;
- repeated questions;
- dependency-resolution time;
- duplicate work;
- peer-review usefulness;
- escalation appropriateness.

Economics:

- cost per successful outcome;
- runtime/model cost;
- rework cost;
- human effort per outcome.

Safety/governance:

- blocked unauthorized mutation attempts;
- proposal approval/modification/rejection rate;
- evidence-gate compliance;
- human-review compliance;
- circuit-breaker activation;
- material incident rate.

**Mission/team outcome remains the primary performance unit.**

### OKRs

Strategic objectives guide improvement above operational KPIs.

### Definition of Done

A material Mission is not complete merely because the model says "done". Definition of Done may require:

- deliverable produced;
- evidence/provenance attached;
- uncertainty disclosed;
- review complete;
- consequential proposals dispositioned;
- authorized external actions completed;
- SLA status known;
- final result verified;
- outcome recorded.

---

## 22. Progressive intervention / circuit breaker

The intervention ladder remains:

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

Possible constraints:

- reduced tools;
- lower spend/token budget;
- proposal-only mode;
- additional peer review;
- no external actions;
- narrower context;
- different model/runtime;
- narrower Mission scope.

`Pause Organization` remains an emergency system-level control, not routine troubleshooting.

---

## 23. Distributed human approval — not Board approval everywhere

Consequential proposals should be reviewed by the lowest appropriate human role.

```text
Mobility User
→ confirm personal facts / user-owned choices

Professional / Operator
→ eligibility, evidence, case state, communications, application readiness

Qualified source/certification reviewer
→ evidence/rule certification where required

Department lead / Executive
→ organizational operational decisions within delegated scope

Human Owner / Board
→ reserved organizational authority / material strategic controls
```

The Owner may inspect and intervene across the organization, but ordinary professional work should not be routed to Board Room by default.

---

## 24. Live Organization / Cockpit

The Cockpit should eventually expose the organization as a living system rather than a static dashboard.

Premium AIOS-native Live Organization may show:

- departments / positions;
- current Missions;
- agents working / waiting / blocked / collaborating;
- natural conversation flows;
- delegations;
- Dynamic Squads;
- SLA risk;
- workload / capacity;
- proposal queues;
- approval/modification outcomes;
- cost / runtime/model utilization;
- quality and rework;
- progressive interventions;
- click-through to conversations, work, performance, authority and permitted memory.

The visual state must come from AIOS-owned normalized state, not provider animation alone.

---

## 25. Owner Command

The Owner should be able to talk naturally to the CEO and other permitted positions.

Example:

```text
OWNER COMMAND

> Ask the CEO why Austria cases are delayed,
> have Operations prepare a recovery plan,
> and draft the client communications needed.
```

AIOS may create Missions, conversations, WorkItems and draft/proposal actions automatically.

If the requested outcome includes consequential external/domain changes, AIOS prepares the proposal(s) and presents the exact consequences for human approval/modification before execution, unless an explicitly pre-approved bounded policy already covers that action.

---

## 26. Learning & Quality — controlled but not blocked

The project keeps Internal Learning & Quality as a first-class strategic capability while separating three uses:

1. **Operational Intelligence**;
2. **Evaluation & Quality**;
3. **Training & Optimization**.

AIOS may build operational/evaluation capability in parallel with the product.

Real client data used for training/optimization must eventually be governed through explicit data-use policy, processing purpose, applicable legal basis/compatibility analysis, sensitivity handling, retention/deletion rules, tenant policy, lineage and legal/privacy review.

The architecture should not throw away useful permitted signals, but it also should not assume that data being usable for service operation automatically makes it usable for training.

Potential learning signals:

- corrections;
- proposal modifications;
- proposal rejections;
- approval outcomes;
- SLA misses;
- routing outcomes;
- peer-review disagreements;
- provider/runtime performance;
- successful collaboration patterns;
- human effort;
- evidence gaps;
- contradiction recoveries;
- external-action failures.

---

## 27. Technology adoption lifecycle clarification

Strategic fit and adoption state are separate dimensions.

Recommended lifecycle:

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

Examples of clearer current states:

| Technology | Fit | Adoption state |
|---|---:|---|
| Promptfoo | A+ | PILOT COMPLETE / TRIAL-ELIGIBLE |
| OpenTelemetry | A+ | PILOT COMPLETE / TRIAL-ELIGIBLE |
| ClamAV | A+ | PILOT COMPLETE / TRIAL-ELIGIBLE |
| Docling | A+ | PILOT IN PROGRESS |
| Presidio | A+ | QUEUED PILOT |
| urlwatch | A+ | QUEUED PILOT |
| Munder Difflin | A+ | REFERENCE / CONTROLLED RESEARCH |
| OpenWorker | A+ | REFERENCE / CONTROLLED RESEARCH |
| Temporal | A+ Strategic | DEFERRED PILOT |
| OpenFGA | A+ Strategic | DEFERRED PILOT |
| pgvector | A | BENCHMARK |
| Qdrant | A | BENCHMARK |

This replaces ambiguous labels such as `ADOPT / EARLY PILOT`.

---

## 28. Docling / OCR simplification rule

Do not adopt an extra OCR framework merely because it is listed on the Radar.

Sequence:

```text
realistic document corpus
        ↓
measure Docling + current fallback stack
        ↓
identify actual gaps
        ↓
benchmark PaddleOCR / Unlimited-OCR only for those gaps
        ↓
adopt additional OCR only if it produces measurable value
```

Potential measured gaps:

- low-quality scans;
- language coverage;
- table structure;
- handwriting;
- layout fidelity;
- throughput/latency;
- extraction accuracy.

Technology enters runtime because a capability gap exists, not because an architecture diagram has an empty slot.

---

## 29. Updated platform-evolution implementation sequence

Architecture and product work continue in parallel. The following waves are **implementation tracks**, not a rule that later tracks must wait for complete Phase 13 closure.

### Wave 5A — Control Plane Foundation

Define/implement AIOS-owned contracts for:

- Context Broker / ContextBundle;
- Canonicalization Gateway;
- Command Gateway;
- ConsequentialActionProposal;
- proposal review/modification lifecycle;
- evidence sufficiency state;
- contradiction detection;
- capability-specific autonomy;
- execution sandbox;
- atomic/versioned mutation.

### Wave 5B — Organization Semantics Foundation

Define/implement:

- Mission;
- AgentConversation;
- conversational/collaborative OrganizationActivity;
- Dynamic Squad;
- Capability Registry;
- memory scopes;
- AgentRelationship;
- SLA;
- KPI/OKR;
- Definition of Done.

5A and 5B may progress as coordinated parallel slices when dependencies permit.

### Wave 5C — Munder Difflin Agent Organization Fabric

Controlled research/pilot behind AIOS-owned contracts for:

- identity;
- communication;
- conversation routing;
- memory mechanics;
- supervisor patterns;
- scheduling;
- budgets;
- circuit breakers;
- skills;
- event feed / Live Organization integration.

### Wave 5D — Execution Broker + OpenWorker / Coworker

Controlled research/pilot for:

- finished deliverables;
- files;
- tools;
- MCP;
- connectors;
- scheduled execution;
- proposal-gated external actions;
- approval inbox integration;
- result return into AIOS Missions.

### Wave 5E — Live Organization / Cockpit

Premium organization visualization and direct human interaction.

### Wave 5F — Organizational Learning & Optimization

Use permitted outcomes to improve:

- routing;
- capability selection;
- collaboration;
- SLA performance;
- runtime/model selection;
- team composition;
- prompts/programs;
- capacity decisions;
- proposal quality;
- contradiction recovery.

Every implementation slice still requires bounded scope, tests, security/data-flow review, acceptance, rollback and exit strategy.

---

## 30. Relationship to Phase 13.17

Phase 13.17 remains genuine owner-led human acceptance evidence and should continue when the Owner chooses to resume.

The platform/architecture track does **not wait for Phase 13.17 to finish**.

At the same time:

- architecture changes must not rewrite existing human findings;
- unresolved usability findings remain unresolved until implemented/retested/dispositioned;
- new architecture should learn from those findings;
- no docs-only architecture decision may be presented as a product usability PASS.

This is parallel progress, not evidence bypass.

---

## 31. Success criteria

The architecture succeeds when AIOS can demonstrate that:

1. agents talk/collaborate naturally without constant human micromanagement;
2. agents receive sufficient but scoped context;
3. ordinary conversation can become Activity without becoming authority;
4. memory can guide work without becoming evidence/truth;
5. provider events can be normalized without providers owning AIOS semantics;
6. consequential actions are prepared intelligently and reviewed/modified efficiently;
7. one hallucination cannot silently modify regulated/business-critical state;
8. unsupported/conflicted claims trigger self-correction before unnecessary escalation;
9. high-value work can use independent verification mechanisms;
10. prior accepted state survives rejected/bad proposals;
11. external actions are exact, previewable and auditable;
12. Munder Difflin and OpenWorker can cooperate through AIOS rather than compete for semantic ownership;
13. SLA/KPI/OKR keep the organization high-performing;
14. human review occurs at the lowest appropriate level;
15. Board Room remains reserved;
16. Live Organization makes the organization understandable in real time;
17. permitted outcomes/corrections improve future performance;
18. provider replacement remains possible;
19. product and architecture can progress in parallel without weakening governance.

---

## 32. Target end state

```text
Work / Mission
      ↓
AIOS Context Broker
      ↓
Natural organizational conversation + cognition
      ↓
Collaboration / delegation / memory
      ↓
AIOS Execution Broker
      ↓
Best available capabilities
(Munder-inspired organization + OpenWorker execution + AIOS-native services)
      ↓
Draft / artifact / recommendation / proposed action
      ↓
Canonicalization + grounding + contradiction checks
      ↓
Internal bounded action
          OR
Consequential Action Proposal
      ↓
appropriate human review / modify / approve
      ↓
atomic governed execution
      ↓
real outcome
      ↓
OrganizationActivity + audit
      ↓
SLA / KPI / quality / learning
      ↓
better routing / agents / models / organization
      ↓
better work
```

The long-term organization should feel like **a real high-performing company made of AI colleagues and humans**: natural enough to collaborate like people, disciplined enough to operate regulated work safely, and powerful enough to prepare most of the work before a human ever needs to touch it.