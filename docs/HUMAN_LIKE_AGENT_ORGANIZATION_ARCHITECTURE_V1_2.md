# Global Mobility AIOS — Human-Like High-Autonomy Organization Architecture V1.2

**Date:** 2026-08-19  
**Status:** CANONICAL ARCHITECTURE DIRECTION / RUNTIME-GOVERNANCE INVARIANTS FROZEN  
**Supersedes for active direction:** [HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_1.md](HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_1.md)  
**Historical predecessor:** [HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1.md](HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1.md)  
**Runtime impact of this document:** none by itself  
**Delivery posture:** product, human acceptance, Technology Radar work, and controlled agent architecture continue in parallel through bounded slices  

---

## 1. Purpose

Global Mobility AIOS is deliberately moving toward a **human-like, high-autonomy organization** in which agents can communicate naturally, reason broadly, collaborate, remember useful organizational experience, use strong tools, prepare finished work, self-correct, and help humans complete consequential work without forcing humans to redo the AI's work manually.

The architecture does **not** attempt to prevent mistakes by making agents weak.

It instead makes mistakes **non-authoritative until they survive the correct AIOS gates**.

The core product target remains:

> **Human in interaction. Machine-like in reliability.**

The control-plane principle remains:

> **Broad cognition. Scoped context. Narrow mutation. Deterministic authority. Reversible execution.**

V1.2 freezes an additional canonical principle:

> **Agents are allowed to be wrong while thinking; AIOS is not allowed to be wrong silently when committing truth.**

Supporting permanent principles:

> **Natural interaction, deterministic accountability.**

> **Activity is broad; authority is narrow.**

> **Team outcomes over agent competition.**

> **Results matter more than provider competition.**

> **Agents may be creative in cognition. AIOS must be conservative in truth.**

> **Consequential actions are proposal-first unless an explicitly accepted bounded autonomy policy permits direct execution.**

> **Autonomy is capability-specific, measurable, reversible, and never self-granted.**

> **Parallel does not mean uncontrolled.**

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
                   LLM assistance allowed; deterministic
                      canonical classification required
                                    │
                                    ▼
                          AIOS COMMAND GATEWAY
                     ONLY production mutation path for
                       autonomous agent-originated work
                                    │
                  ┌─────────────────┼─────────────────┐
                  ▼                 ▼                 ▼
             Authority          Grounding         Consistency
               Policy            Evidence         Contradiction
                  │                 │                 │
                  └─────────────────┼─────────────────┘
                                    ▼
                     VERSION / CONCURRENCY CHECK
                                    │
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
                     atomic / versioned / idempotent
                                    │
                        rollback/compensation metadata
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
                                                     │
                                                     ▼
                                        labeled outcome / lineage
```

AIOS remains authoritative for domain meaning, case state, Evidence, VerifiedRules, certification, publication, Missions, WorkItems, Decisions, Contributions, canonical OrganizationActivity, human-review requirements, authority, and business outcomes.

External systems may provide capability, transport, memory mechanics, orchestration, execution, telemetry, visualization, tools, connectors, or finished-work functionality. They do not define canonical AIOS truth.

---

## 3. Five non-negotiable runtime implementation rules

These rules are not guidance. They are **runtime acceptance requirements** for the high-autonomy architecture.

### Rule 1 — The Canonicalization Gateway may use an LLM, but cannot be an unconstrained LLM

The Canonicalization Gateway is the semantic firewall between non-authoritative agent/provider information and canonical AIOS meaning.

An LLM may help interpret:

- free-form conversation;
- provider events;
- tool output;
- model output;
- external correspondence;
- document findings;
- memory;
- execution traces.

But final canonical classification for material states must resolve through **AIOS-owned typed schemas + deterministic validation rules**.

Examples that must never depend solely on an LLM classification:

- `ExecutiveDecision`;
- `VerifiedRule`;
- Evidence certification;
- publication state;
- eligibility transition;
- client status transition;
- application submission state;
- external communication execution;
- human-review completion;
- reserved authority action.

Preferred pattern:

```text
free-form event / message / model output
        ↓
optional LLM interpretation
        ↓
typed AIOS candidate
        ↓
schema validation
        ↓
deterministic classification rules
        ↓
required evidence / authority / state checks
        ↓
canonical candidate / Activity / command
```

The Gateway may help answer:

> “What might this mean?”

It may not decide by itself:

> “This is now legally/governance-authoritative truth.”

### Rule 2 — The Command Gateway is the only production mutation path for autonomous agents

No autonomous runtime receives arbitrary production-database write capability.

This includes:

- OpenWorker;
- Munder Difflin workers;
- LLM tool calls;
- Pydantic-AI-style agents;
- MCP servers/connectors;
- future browser automation;
- scheduled agent missions;
- provider-native scripts;
- local coworker processes.

Allowed architecture:

```text
agent/runtime
  ↓
AIOS typed intent / command request
  ↓
Command Gateway
  ↓
identity
  ↓
authority
  ↓
capability scope
  ↓
tenant / case / Mission scope
  ↓
evidence / truth requirements
  ↓
contradiction checks
  ↓
expected-version / precondition checks
  ↓
human/professional/source/certification gate
  ↓
idempotency / transaction validation
  ↓
canonical mutation
```

Disallowed architecture:

```text
agent → arbitrary ORM session → production write
```

or:

```text
MCP tool → unrestricted database mutation
```

or:

```text
OpenWorker shell → production SQL mutation
```

The rule must be executable in code, not merely stated in system prompts.

### Rule 3 — Material writes require optimistic concurrency / expected-version checks

Autonomous agents will work concurrently. Hallucination is not the only source of risk; stale state is equally dangerous.

Example:

```text
Case version = V14

Agent A reads V14
Agent B reads V14

Agent A proposes mutation
→ accepted
→ Case becomes V15

Agent B later attempts mutation
based on V14
```

Required behavior:

```text
expected_version = 14
actual_version   = 15

→ STALE PROPOSAL
→ mutation rejected
→ refresh ContextBundle
→ rebase / re-evaluate
```

The second agent may not silently overwrite V15.

Material AIOS commands should therefore support concepts such as:

```text
expected_version
expected_state
precondition_hash
idempotency_key
command_id
```

Where the domain object is immutable/versioned, the command should bind to the exact source version it evaluated.

Where multiple domain aggregates are involved, the command must define the relevant concurrency/precondition contract explicitly.

### Rule 4 — Learning captures failures, but training truth preserves outcome labels

Rejected proposals, hallucinations, contradictions, human modifications, peer disagreements, stale proposals, and execution failures are **valuable learning data**.

They must not be flattened into undifferentiated training truth.

Canonical learning outcome labels should include at least:

```text
PROPOSED
ACCEPTED
MODIFIED
REJECTED
CONTRADICTED
STALE
SUPERSEDED
HUMAN_CORRECTED
EXECUTION_FAILED
PARTIAL
ROLLED_BACK
```

Example:

```text
bad proposal
        +
reason for rejection / contradiction
        +
human or governed correction
        +
final accepted outcome
        =
high-value supervised learning example
```

The Learning & Quality Plane should preserve the relationship among:

```text
input context
model/agent proposal
validation findings
human modification
final accepted state
execution result
rollback/compensation if any
```

A future training dataset must be able to distinguish:

- what an agent suggested;
- whether it was accepted;
- what was changed;
- why it failed;
- what eventually became canonical.

### Rule 5 — Rollback / compensation is first-class, not just audit history

Audit tells us what happened.

Rollback/compensation tells AIOS what it can safely do about it.

For A3/A4 transitions, and for lower-autonomy consequential proposals where appropriate, commands should declare:

```text
reversible: true | false
compensation_command
previous_version
side_effects
external_side_effects
rollback_deadline
rollback_preconditions
```

Example:

```text
reassign internal WorkItem
→ reversible = true
→ compensation = restore previous assignment
```

versus:

```text
submit government application
→ reversible = false
→ external side effect exists
→ stricter autonomy / human approval required
```

or:

```text
send email
→ external side effect exists
→ cannot truly unsend after delivery
→ proposal-first / stricter autonomy
```

A4 means **autonomous with monitoring/rollback only where rollback is real**.

A command must not be treated as A4 merely because an audit log exists.

---

## 4. Context Broker — provenance-aware ContextBundle

The Context Broker should give agents **more relevant truth, not merely more tokens**.

The agent should receive a task/tenant/purpose/sensitivity-scoped `ContextBundle`, not unrestricted database visibility.

Conceptual contract:

```text
ContextBundle

context_bundle_id
mission_id
case_id?
tenant_id
requested_by
agent_position
purpose
generated_at
context_version

facts[]
  fact_id
  value
  support_state
  provenance
  source_record_id?
  effective_at?

evidence[]
verified_rules[]
source_snapshots[]
case_state[]
pathway_state[]
relevant_decisions[]
recent_conversations[]
unknowns[]
contradictions[]

agent_capabilities
agent_authority_context
allowed_tools
allowed_external_actions
sensitivity_profile
retention/data_use_context

context_hash
```

### Provenance-aware facts

A fact should be distinguishable from a memory hint or model interpretation.

Example:

```text
Fact
value: "passport expires 2028-04-10"
support_state: GOVERNED_CASE_FACT
provenance: profile_record_...
```

versus:

```text
Working hypothesis
value: "salary threshold may have changed"
support_state: MEMORY_HINT
provenance: organization_memory_...
```

### AgentRun reproducibility

An `AgentRun` should eventually preserve enough execution lineage to reconstruct what the agent knew and which implementation acted.

Conceptually:

```text
AgentRun

context_bundle_id
context_hash
mission_id
work_item_id?
agent_position
model
model_version
prompt_program_version
role_card_version
tool_versions
connector_versions
execution_policy_version
autonomy_policy_version
started_at
completed_at
result_state
```

This supports:

- debugging;
- incident analysis;
- quality evaluation;
- regression reproduction;
- human correction analysis;
- training lineage;
- model/provider comparison.

---

## 5. Machine-readable trust ladder

AIOS should maintain a machine-readable epistemic hierarchy.

```text
L0  model speculation
L1  conversation / memory / working hypothesis
L2  retrieved information
L3  captured source snapshot
L4  governed Evidence
L5  reviewed candidate
L6  VerifiedRule / certified governed fact
L7  governed case conclusion
L8  approved authority-bearing action
```

The key benefit is not merely documentation.

AIOS can programmatically know what class of truth a value represents.

### Forbidden jumps

```text
L1 ↛ L6
L2 ↛ L7
L6 ↛ L8 automatically
```

Additional principle:

```text
higher-level consequence
requires appropriately supported lower-level truth
```

A model's probability/confidence score does not create a trust-level promotion.

---

## 6. Evidence sufficiency, not self-confidence, drives material work

Material agent results should expose structured support metadata.

Conceptual output:

```text
AgentMaterialResult

claim
support_state
supporting_evidence_ids[]
supporting_source_ids[]
verified_rule_ids[]
assumptions[]
uncertainties[]
missing_facts[]
contradictions[]
recommended_action
requested_consequence_class
```

Example:

```text
claim:
"case can progress to professional readiness review"

support_state:
SUPPORTED_WITH_OPEN_REVIEW

verified_rule_ids:
[...]

evidence_ids:
[...]

missing_facts:
[]

open_reviews:
["insurance professional review"]
```

An unsupported result with `confidence=0.99` may still be rejected.

---

## 7. Contradiction detection happens before unnecessary human review

Humans should review difficult/consequential matters, not act as the first hallucination detector for errors AIOS can identify itself.

Before a material proposal reaches a human, AIOS should compare it with relevant current state:

- governed Evidence;
- VerifiedRules;
- official source authority;
- source effective dates;
- supersession;
- case facts;
- pathway/profile version;
- current eligibility/conclusion;
- ExecutiveDecisions;
- previous accepted proposal/state;
- expected aggregate versions;
- human corrections relevant to the same capability.

Preferred recovery sequence:

```text
agent proposal
     ↓
deterministic validation / contradiction check
     ↓
conflict?
     ↓
return to originating agent
     ↓
self-correct with stronger context
     ↓
peer review where useful
     ↓
specialist review
     ↓
human only when unresolved or consequential gate requires it
```

### Peer review limitation

Two agents can share the same blind spot.

High-value peer validation should prefer diversity of verification mechanisms:

```text
agent reasoning
+
independent evidence retrieval
+
deterministic invariants
+
source/effective-date validation
+
peer/specialist reasoning
+
human where required
```

Agreement is a useful signal.

Agreement is not truth.

---

## 8. Proposal-first consequential actions remain a product strength

Agents are not recommendation engines that stop after giving advice.

They should perform as much useful work as possible before human intervention.

The following action classes remain proposal-first by default:

1. send email / external communication;
2. change eligibility;
3. certify Evidence;
4. submit application;
5. change/publish VerifiedRule;
6. change client status.

An agent may:

- research;
- retrieve;
- reason;
- assemble Evidence;
- fill forms;
- draft communication;
- prepare attachments;
- perform checks;
- identify risks;
- calculate impact;
- create the exact intended payload;
- create a finished proposal;
- revise after human feedback.

Human interaction becomes:

```text
APPROVE
MODIFY
RETURN FOR REVISION
REJECT
```

The human should not redo the agent's work manually unless they choose to.

### Proposal lifecycle

```text
DRAFT
  ↓
PROPOSED
  ↓
AIOS VALIDATION
  ↓
HUMAN REVIEW
  ├── APPROVE
  ├── MODIFY
  ├── RETURN FOR REVISION
  └── REJECT
  ↓
APPROVED
  ↓
FINAL VERSION / CONCURRENCY CHECK
  ↓
EXECUTE
  ↓
VERIFY RESULT
  ↓
COMPLETED / FAILED / PARTIAL / COMPENSATED
```

### Modification lineage

If a human modifies the proposal, AIOS should preserve:

```text
agent_proposal_version
human_modified_version
changed_fields
reviewer
review_reason?
approval_time
final_execution_payload_hash
```

That becomes valuable quality/training information.

---

## 9. Command Gateway executable contract

A material command should eventually have a common envelope.

Conceptually:

```text
AIOSCommandEnvelope

command_id
command_type
requested_by_actor
requested_by_agent_run?
mission_id?
case_id?
tenant_id

expected_version
expected_state?
precondition_hash?
idempotency_key

capability_id
autonomy_level

supporting_evidence_ids[]
verified_rule_ids[]
source_snapshot_ids[]

consequence_class
requires_human_review
review_id?

reversible
compensation_command?
rollback_deadline?

payload
payload_hash

created_at
```

The command handler validates before commit.

The LLM never "executes authority" by text alone.

---

## 10. Optimistic concurrency and stale proposals

Concurrent autonomous work is expected.

Stale proposals are normal and must be safe.

State transition pattern:

```text
read V14
  ↓
reason / prepare proposal
  ↓
submit expected_version=14
  ↓
actual version?

14
→ continue validation

15
→ STALE
→ no write
→ issue refreshed ContextBundle
→ re-evaluate / rebase
```

### Why this matters

Without this rule, two perfectly non-hallucinating agents can still corrupt state through lost updates.

Therefore concurrency safety is part of the **autonomous organization model**, not merely database engineering.

---

## 11. Capability-specific autonomy

Autonomy remains attached to capability + context.

```text
A0  prohibited
A1  human execution required
A2  human approval required
A3  autonomous + mandatory post-review
A4  autonomous + monitoring / real rollback or compensation
A5  fully autonomous bounded internal operation
```

Examples:

```text
Global Intelligence

search official source           A5
capture immutable snapshot       A5
compare source versions          A5
extract rule candidate           A4
prepare VerifiedRule proposal    A3/A4
publish/change VerifiedRule      A2/A1
```

```text
OpenWorker-style Coworker

create internal report           A5
draft email                      A5
prepare external action          A4
send external email              A2 by default
submit authority application     A2/A1
```

### Autonomy Evidence Profile

AIOS should eventually calculate an evidence profile per capability.

Example:

```text
Capability: regulatory_candidate_extraction

Executions                4,812
Acceptance                 98.7%
Modified                    1.1%
Rejected                    0.2%
Contradicted                0.1%
Material errors                0
Grounding completeness     99.4%
SLA attainment             99.1%
Rollback/incident rate      0.0%

Current autonomy             A3
Recommended                  A4
```

This produces an `AutonomyChangeRecommendation`.

The agent cannot approve its own promotion.

Meaningful autonomy expansion remains a governed human/executive/policy decision.

---

## 12. Rollback-aware autonomy

A4 is only appropriate where monitoring + rollback/compensation is meaningful.

A capability assessment should consider:

```text
reversibility
external_side_effects
compensation_quality
rollback_window
state_reconstruction
financial impact
legal/authority consequence
notification consequence
```

Examples:

### Easy rollback

```text
internal WorkItem reassignment
→ reversible
→ prior owner known
→ no external effect
```

### Compensatable but not perfectly reversible

```text
internal generated report publication
→ unpublish/replace may be possible
→ prior consumers may already have seen it
```

### Irreversible / externally consequential

```text
government application submission
client email delivery
external payment
legal/authority filing
```

These require stricter autonomy and stronger proposal/approval controls.

---

## 13. OrganizationActivity tiering and retention

The semantic relationship remains:

```text
AgentMessage ⊂ OrganizationActivity
```

Natural agent conversation is legitimate organizational history.

But runtime storage/indexing/retention should recognize that not all Activity has the same significance or volume.

Canonical activity classes:

```text
OrganizationActivity

activity_class:
  CONVERSATIONAL
  COLLABORATIVE
  OPERATIONAL
  MATERIAL
  AUTHORITY
```

### CONVERSATIONAL

Examples:

- question;
- clarification;
- acknowledgement;
- informal coordination;
- ordinary status discussion.

Characteristics:

- potentially very high volume;
- human-inspectable while active/recent;
- may be compressed/summarized after a retention period subject to audit/legal/data-use requirements;
- exact messages may remain available where policy requires.

### COLLABORATIVE

Examples:

- handoff;
- peer review;
- request for specialist help;
- delegated analysis;
- shared finding.

Characteristics:

- more structured;
- linked to Mission/WorkItem/Case where relevant;
- useful for collaboration analytics.

### OPERATIONAL

Examples:

- work started/completed;
- artifact produced;
- blocker discovered/resolved;
- tool execution outcome;
- SLA event.

Characteristics:

- durable operational history;
- indexed for work reconstruction and KPI analysis.

### MATERIAL

Examples:

- material risk;
- significant case impact;
- consequential recommendation;
- important cross-department conflict;
- major contradiction.

Characteristics:

- long-term durable;
- strongly indexed;
- visible in Cockpit compression where appropriate.

### AUTHORITY

Examples:

- professional approval;
- evidence certification;
- ExecutiveDecision;
- Owner/Board decision;
- external consequential action approval;
- emergency intervention.

Characteristics:

- permanently durable subject to governing retention requirements;
- immutable/tamper-evident design target;
- linked to AuditLog and exact approved payload/version.

### Conversation visibility

Compression must not mean conversation becomes invisible.

Humans should still be able to inspect the relevant conversation history when permitted, including reconstructed summaries and retained exact records according to policy.

---

## 14. Learning & Quality outcome model

The Learning & Quality Plane must distinguish **what was proposed** from **what became accepted truth**.

Conceptual learning record:

```text
LearningRecord

source_agent_run
context_bundle_id
context_hash
capability
proposal_id?
command_id?

proposal_state
validation_state
human_review_state
execution_state

labels[]
  PROPOSED
  ACCEPTED
  MODIFIED
  REJECTED
  CONTRADICTED
  STALE
  SUPERSEDED
  HUMAN_CORRECTED
  EXECUTION_FAILED
  PARTIAL
  ROLLED_BACK

failure_reasons[]
human_changes[]
final_canonical_record_ids[]

processing_purpose
data_use_policy
retention_class
training_eligibility
```

### Training truth rule

Never:

```text
everything agents said
→ training truth
```

Prefer:

```text
agent proposal
+
validation result
+
human modification / rejection
+
corrected canonical outcome
→ labeled learning example
```

This is how failures become an advantage rather than contamination.

---

## 15. Agent sandbox

Powerful agents become safer through bounded capability, not by removing useful tools.

A future worker may legitimately have:

```text
Terminal ✓
Files ✓
MCP ✓
Browser ✓
Email ✓
Calendar ✓
GitHub ✓
Documents ✓
```

while production controls remain:

```text
Production DB mutation
→ Command Gateway only

External consequence
→ autonomy / proposal policy

Secrets
→ capability-scoped

Network
→ allowlisted / policy-scoped

Filesystem
→ workspace-scoped

Runtime
→ bounded

Cost/token budget
→ bounded
```

This is controlled autonomy.

---

## 16. Munder Difflin + OpenWorker remain complementary

Munder Difflin remains the principal A+ reference for the **Agent Organization Fabric**:

- identities;
- conversations/mailboxes;
- coordination;
- shared/long-term memory mechanics;
- supervisor/orchestrator patterns;
- dependencies;
- schedules/heartbeat;
- budgets/cost;
- circuit breakers;
- skills/capability discovery;
- Live Organization concepts.

OpenWorker remains the principal A+ reference for **Coworker / finished-work execution**:

- files/artifacts;
- terminal/tools;
- MCP;
- connectors;
- scheduled work;
- external actions;
- approval inbox;
- model portability;
- local-first outcome-oriented execution.

Neither gets direct canonical mutation authority by virtue of being powerful.

Both operate behind AIOS-owned context, canonicalization, command, autonomy, proposal, and sandbox contracts.

The AIOS Execution Broker may combine them when that produces the best governed Mission result.

---

## 17. SLA / KPI / OKR / Definition of Done remain first-class

Human-like behavior must not reduce operational discipline.

### SLA

- acknowledge;
- start;
- respond;
- complete;
- review;
- freshness;
- blocker age;
- escalation;
- retry/recovery.

### Delivery / quality KPIs

- Mission completion rate;
- SLA attainment;
- first-pass quality;
- professional agreement;
- human correction;
- material correction;
- evidence grounding;
- provenance completeness;
- rework;
- blocker age.

### Collaboration KPIs

- successful collaboration;
- unnecessary handoffs;
- repeated questions;
- dependency resolution;
- peer-review usefulness;
- duplicate work;
- escalation appropriateness.

### Proposal / autonomy KPIs

- proposal acceptance;
- human modification rate;
- rejection rate;
- contradiction rate;
- stale-proposal rate;
- rollback rate;
- external execution success;
- unauthorized mutation attempt blocks;
- command precondition failure rate.

### Economic KPIs

- cost per successful outcome;
- model/runtime cost;
- cost of rework;
- human effort per outcome.

### OKR

Strategic improvement remains above operational metrics.

### Definition of Done

A Mission is complete only when its explicit quality, evidence, review, SLA, proposal/execution, outcome, and rollback/exception requirements are satisfied.

---

## 18. Parallel delivery remains the strategy

The project does **not** adopt a stop-and-wait strategy.

### Track A — Product / Human Experience

- Phase 13.17 owner-led acceptance;
- bounded UX/comprehension corrections;
- Operations/Cockpit/My Mobility refinement;
- role clarity;
- human explainability/traceability.

### Track B — Technology Radar / Platform Evolution

- document/privacy intelligence;
- regulatory monitoring;
- AI runtime/retrieval/quality;
- professional output technologies.

### Track C — Human-Like Organization / Runtime Control Plane

- deterministic Canonicalization contracts;
- Command Gateway mutation monopoly;
- ContextBundle provenance;
- optimistic concurrency;
- proposal-first consequential actions;
- rollback/compensation;
- activity tiering;
- capability autonomy;
- Munder/OpenWorker integration boundaries;
- Live Organization;
- organizational learning.

Parallel means:

- architecture does not wait for Phase 13.17 closure;
- Phase 13.17 findings remain unresolved until corrected/retested/dispositioned;
- a docs checkpoint is not runtime acceptance;
- each runtime slice has its own acceptance boundary;
- no track may weaken another track's accepted evidence/authority/security invariants.

---

## 19. Updated Wave 5 sequence

### Wave 5A — Runtime Control Plane / Immune System

Non-negotiable first-class capabilities:

- deterministic Canonicalization Gateway contracts;
- Command Gateway as sole autonomous-agent production mutation path;
- Context Broker + provenance-aware ContextBundle;
- expected-version / optimistic concurrency;
- idempotency / preconditions;
- ConsequentialActionProposal lifecycle;
- evidence sufficiency;
- contradiction detection;
- capability autonomy;
- execution sandbox;
- rollback/compensation metadata;
- labeled LearningRecord outcome model.

### Wave 5B — Organization Semantics

- Mission;
- AgentConversation;
- tiered OrganizationActivity;
- Dynamic Squad;
- Capability Registry;
- organizational memory scopes;
- AgentRelationship;
- SLA;
- KPI/OKR;
- Definition of Done.

5A and 5B may progress in coordinated parallel slices, but deep external-agent mutation capability depends on the relevant 5A controls existing.

### Wave 5C — Munder Difflin Agent Organization Fabric

Controlled research/pilot behind AIOS-owned contracts for:

- identity;
- communication;
- memory;
- coordination;
- scheduling;
- budgets;
- circuit breakers;
- skills;
- Live Organization event integration.

### Wave 5D — Execution Broker + OpenWorker / AIOS Coworker

Controlled research/pilot for:

- files;
- tools;
- MCP;
- connectors;
- scheduled execution;
- finished work;
- proposal-gated consequential actions;
- result return into AIOS Missions.

### Wave 5E — Live Organization / Cockpit

Premium AIOS-native organization visualization using canonical AIOS state, including:

- positions;
- conversations;
- delegations;
- Missions;
- squads;
- SLA risk;
- workload;
- proposals;
- cost;
- quality;
- interventions.

### Wave 5F — Organizational Learning & Optimization

Use permitted labeled outcomes to improve:

- routing;
- collaboration;
- capability selection;
- runtime/model selection;
- SLA performance;
- proposal quality;
- contradiction recovery;
- autonomy recommendations;
- capacity/team composition.

---

## 20. Runtime acceptance expectations

The following should become executable tests/contracts as implementation begins.

### Canonicalization tests

- unstructured message cannot directly become `ExecutiveDecision`;
- memory cannot directly become Evidence/VerifiedRule;
- provider event does not automatically become canonical Activity;
- final material classification uses typed AIOS schema + deterministic validators.

### Mutation-path tests

- agent-originated production writes outside Command Gateway fail;
- arbitrary provider/MCP database write path is unavailable;
- required human gate cannot be bypassed;
- idempotency prevents duplicate consequential execution.

### Concurrency tests

- stale expected version rejects;
- accepted V15 is not overwritten by proposal based on V14;
- re-evaluation receives refreshed context.

### Rollback tests

- reversible actions expose compensation;
- A4 requires valid rollback/compensation semantics;
- irreversible external side effects cannot masquerade as reversible.

### Learning tests

- rejected/modified/contradicted outcomes preserve labels;
- canonical accepted outcome is distinguishable from proposal text;
- context/model/program/tool versions remain reconstructable.

### Activity tests

- conversational messages are legitimate Activity;
- activity class is explicit;
- authority Activity retains immutable/high-durability treatment;
- provider logs remain non-authoritative until normalized.

---

## 21. Success criteria

The architecture succeeds when Global Mobility AIOS can demonstrate that:

1. agents are powerful enough to perform serious work without constant human micromanagement;
2. agents receive sufficient grounded context without unrestricted sensitive-data access;
3. agents can be wrong during reasoning without silently corrupting canonical state;
4. all autonomous production mutations pass the Command Gateway;
5. material canonicalization is typed/deterministic rather than another LLM-only decision;
6. stale autonomous work cannot overwrite newer accepted state;
7. consequential proposals preserve exact human modification/approval lineage;
8. rollback/compensation capability is known before autonomy is granted;
9. rejected/hallucinated outputs become labeled learning assets rather than training truth;
10. Activity remains human-like and inspectable without drowning material/authority history;
11. Munder/OpenWorker capabilities can be powerful without owning AIOS truth;
12. SLA/KPI/OKR performance remains measurable;
13. autonomy expands only from evidence and governed approval;
14. humans review consequential/hard cases rather than serving as first-line hallucination filters;
15. parallel delivery remains controlled through slice-specific acceptance.

---

## 22. Final architecture principle

The architecture can deliberately make AIOS agents powerful because the system no longer depends on perfect agent reasoning for safety.

The intended model is:

```text
powerful cognition
+
excellent scoped context
+
natural collaboration
+
self-correction
+
peer/specialist review
+
typed proposals
+
deterministic canonicalization
+
Command Gateway-only mutation
+
evidence grounding
+
contradiction detection
+
optimistic concurrency
+
atomic/versioned writes
+
rollback/compensation
+
labeled learning from every outcome
=
HIGH-AUTONOMY, LOW-CORRUPTION AIOS
```

The defining sentence is:

> **Agents are allowed to be wrong while thinking; AIOS is not allowed to be wrong silently when committing truth.**
