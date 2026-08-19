# Global Mobility AIOS — Third-Party Platform Adoption Principles

**Version:** V1.3  
**Date:** 2026-08-19  
**Status:** Current architecture principle  
**Active organization architecture:** [HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_2.md](HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_2.md)  
**Active Radar:** [TECHNOLOGY_RADAR_V1_1.md](TECHNOLOGY_RADAR_V1_1.md)

This document defines the permanent ownership boundary between Global Mobility AIOS and external frameworks, libraries, models, agent runtimes, execution systems, services, standards and infrastructure.

---

## 1. AIOS Semantic Sovereignty

> **Third-party infrastructure may implement, accelerate, execute, retrieve, parse, monitor, observe, scan, render, evaluate, optimize, coordinate, remember, connect, visualize, draft, or propose an AIOS-defined capability, but it must never become authoritative for AIOS domain meaning, legal status, evidence state, certification state, publication state, human-review requirements, organizational authority, Mission/WorkItem semantics, ExecutiveDecision semantics, Contribution semantics, canonical OrganizationActivity semantics, or business outcomes.**

Preferred integration:

```text
AIOS domain / Organization OS
  ↓
AIOS-owned capability contract
  ↓
Context Broker / Canonicalization Gateway / Command Gateway / Execution Broker
  ↓
external technology
```

Permanent runtime principle:

> **Agents are allowed to be wrong while thinking; AIOS is not allowed to be wrong silently when committing truth.**

---

## 2. AIOS always owns

AIOS owns the canonical meaning of:

- domain/case/mobility state;
- legal/business conclusions;
- jurisdiction/effective-period semantics;
- official-source/snapshot state;
- Evidence;
- certification;
- VerifiedRule;
- pathway/publication lifecycle;
- human-review requirements;
- positions/delegation/Board authority;
- Mission;
- WorkItem;
- Blocker;
- Dependency;
- HumanActionRequest / HumanAction;
- AgentConversation semantics;
- ExecutiveDecision;
- Contribution;
- canonical OrganizationActivity;
- OrganizationActivity class/retention semantics;
- Capability Registry;
- autonomy policy;
- SLA/KPI/OKR;
- Definition of Done;
- ConsequentialActionProposal lifecycle;
- approval/modification/rejection state;
- Command Gateway semantics;
- optimistic-concurrency/precondition semantics;
- rollback/compensation semantics;
- labeled learning outcome semantics;
- business audit semantics;
- final evidence/provenance interpretation.

---

## 3. External technologies may

Through bounded AIOS contracts, external systems may:

- parse / OCR / classify / normalize documents;
- detect/redact/transform sensitive data;
- scan malware;
- monitor official sources;
- detect changes;
- retrieve semantic candidates;
- perform model/tool execution;
- produce drafts and finished artifacts;
- use files/terminal/MCP/connectors in a scoped sandbox;
- provide agent communication transport;
- provide mailboxes/message routing;
- provide working-memory mechanics;
- provide orchestration/supervisor mechanics;
- provide schedules/heartbeats;
- provide budgets/cost telemetry;
- provide circuit-breaker mechanics;
- provide visualization/event feeds;
- persist durable waits/retries/execution state;
- evaluate AIOS-defined relationships/policies;
- trace/evaluate model/tool execution;
- render/convert documents;
- validate cryptographic signatures;
- provide processing lineage;
- create candidate/proposed actions for AIOS review;
- execute approved external actions through AIOS-scoped connectors/capabilities;
- report provider-native events for AIOS normalization.

Their output is input to AIOS-owned canonicalization/domain transitions, not an automatic authoritative transition.

---

## 4. External technologies may not silently

They may not automatically:

- declare immigration/legal eligibility;
- certify Evidence;
- publish/change a VerifiedRule;
- publish a pathway;
- change client/case status;
- submit an application outside the accepted proposal/autonomy policy;
- send consequential external communication outside an accepted autonomy policy;
- create Board/executive authority from a prompt/title/persona;
- bypass backend authorization;
- bypass a required professional/source/certification/human gate;
- turn retrieval similarity into legal truth;
- turn memory into Evidence;
- turn memory into VerifiedRule;
- turn conversation into authority;
- turn an agent message directly into ExecutiveDecision without AIOS validation;
- turn a source diff into VerifiedRule;
- turn OCR/model confidence into authenticity/certification;
- turn malware-clean status into evidence approval;
- turn workflow completion into business approval;
- turn telemetry/provider event history directly into canonical OrganizationActivity;
- become the sole provenance/audit record;
- write arbitrary production-domain state around the AIOS Command Gateway;
- ignore expected-version/precondition failures;
- classify an irreversible external side effect as reversible merely because it is audited;
- self-promote agent/provider autonomy;
- flatten rejected/hallucinated/provider output into accepted training truth.

---

## 5. Non-negotiable runtime integration rules

### 5.1 Canonicalization is not LLM authority

The Canonicalization Gateway may use an LLM to interpret free-form information.

Material final classifications must validate through typed AIOS schemas and deterministic rules.

This applies to at least:

- `ExecutiveDecision`;
- `VerifiedRule`;
- Evidence certification;
- publication;
- eligibility transition;
- client-status transition;
- application submission state;
- consequential external action;
- required human-review completion.

Allowed:

```text
provider event
→ LLM-assisted interpretation
→ typed candidate
→ deterministic validation
→ canonical result
```

Disallowed:

```text
provider event
→ LLM says "this is approved"
→ canonical approved state
```

### 5.2 Command Gateway is the autonomous-agent mutation monopoly

No OpenWorker process, Munder worker, model tool, MCP connector, future agent runtime, browser automation or scheduled worker receives unrestricted production-domain write access.

The production path is:

```text
runtime
→ typed AIOS command request
→ Command Gateway
→ policy / evidence / version / review checks
→ atomic canonical mutation
```

This boundary must be enforced in executable code, not prompt wording.

### 5.3 Optimistic concurrency is required for material state

Material commands should bind to the state/version they evaluated.

```text
expected_version=14
actual_version=15
→ STALE
→ reject
→ refresh context
→ re-evaluate
```

A stale autonomous action never silently overwrites a newer accepted state.

### 5.4 Learning outcomes remain labeled

Quality/training lineage must distinguish at least:

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

The accepted/corrected outcome is distinguishable from the original proposal.

### 5.5 Rollback/compensation is first-class

Where relevant, a command/action declares:

```text
reversible
compensation_command
previous_version
side_effects
external_side_effects
rollback_deadline
rollback_preconditions
```

A4 autonomy requires meaningful rollback/compensation capability.

Audit history alone is not rollback.

---

## 6. Broad cognition / scoped context

Agents may reason broadly, but sensitive information should be provided through task/tenant/purpose/sensitivity-scoped context.

Preferred pattern:

```text
AIOS Context Broker
  ↓
provenance-aware ContextBundle
  ↓
agent/runtime
```

A ContextBundle may include only the case/documents/evidence/rules/conversations/decisions/unknowns needed for the Mission.

Target lineage:

```text
context_bundle_id
context_version
context_hash
facts + provenance/support state
Evidence / VerifiedRule / snapshot refs
unknowns / contradictions
agent capability / authority context
```

`AgentRun` should bind to the context bundle/hash and model/prompt/program/tool/connector versions.

External providers must not receive unrelated sensitive information merely because it exists in the database.

---

## 7. Canonicalization boundary

Non-authoritative inputs include:

- agent messages;
- memory;
- model outputs;
- OCR/retrieval;
- source monitoring;
- Munder Difflin events;
- OpenWorker events;
- Temporal histories;
- connector events;
- telemetry.

The AIOS Canonicalization Gateway decides whether an input becomes:

- telemetry only;
- conversational/collaborative OrganizationActivity;
- operational/material OrganizationActivity;
- candidate WorkItem/Mission/Blocker;
- Evidence candidate;
- VerifiedRule candidate;
- ExecutiveDecision candidate;
- ConsequentialActionProposal;
- unsupported/conflicted result.

Provider storage itself is never the authoritative semantic record.

Material final classification remains typed/deterministic.

---

## 8. Command boundary

Authoritative mutations use typed AIOS commands.

Before mutation, AIOS validates:

- authenticated identity;
- deterministic authority;
- capability scope;
- tenant/case scope;
- evidence sufficiency;
- contradictions;
- current version/state preconditions;
- required human/professional/source/certification gate;
- idempotency;
- transaction safety;
- rollback/compensation metadata where relevant.

An external runtime may request/propose a command. It may not bypass the command contract.

---

## 9. Consequential-action proposal boundary

The following action classes are proposal-first by default:

- send external email/communication;
- change eligibility;
- certify Evidence;
- submit application;
- change/publish VerifiedRule;
- change client status.

Agents/runtimes may prepare:

- exact payload;
- recipients/attachments;
- rationale;
- evidence/source references;
- uncertainty;
- contradictions;
- downstream impact;
- preflight results.

The appropriate human may:

- approve;
- modify;
- return for revision;
- reject.

Only after approval does AIOS execute the corresponding domain/external command, unless a separately accepted bounded autonomy policy permits direct execution for that specific action class/context.

Human modifications should preserve proposal-to-final lineage.

Review belongs at the lowest appropriate human surface, not automatically Board Room.

---

## 10. Five hard semantic constraints

```text
conversation != authority
message != ExecutiveDecision
memory != Evidence
memory != VerifiedRule
provider event log != canonical AIOS Activity automatically
```

Allowed promotion chains require AIOS-owned validation.

Examples:

```text
message
→ Decision candidate
→ authority/evidence/version/state validation
→ ExecutiveDecision
```

```text
memory
→ hypothesis
→ official-source/evidence retrieval
→ governed validation
→ Evidence / rule candidate
```

---

## 11. Evidence / legal boundary

```text
external parser / retrieval / model / memory
  ↓
candidate information
  ↓
AIOS source/evidence checks
  ↓
contradiction/effective-date/supersession checks
  ↓
required review/certification
  ↓
governed AIOS state
```

Never `model/retrieval/memory result → legal truth`.

---

## 12. Trust ladder

```text
L0 model speculation
L1 conversation / memory
L2 retrieved information
L3 captured source snapshot
L4 governed Evidence
L5 reviewed candidate
L6 VerifiedRule / certified governed fact
L7 governed case conclusion
L8 approved authority-bearing action
```

Hard constraints:

```text
L1 ↛ L6
L2 ↛ L7
L6 ↛ L8 automatically
```

Lower levels cannot skip mandatory promotion stages merely because a model is confident.

---

## 13. Confidence / grounding

Model self-confidence is not an authorization mechanism.

Material agent output should provide structured grounding such as:

- support state;
- source/evidence identifiers;
- VerifiedRule identifiers;
- assumptions;
- uncertainty;
- missing facts;
- contradictions.

AIOS may reject an unsupported high-confidence output.

---

## 14. Contradiction / self-correction boundary

Before material mutation, AIOS should check current:

- Evidence;
- VerifiedRules;
- source authority/effective date;
- supersession;
- case facts;
- pathway version;
- decisions;
- prior accepted state;
- aggregate version/preconditions.

Unsupported/conflicted results should normally follow:

```text
self-correct
→ peer/specialist review where useful
→ human review where still required
```

Peer-agent agreement is a signal, not truth.

---

## 15. Capability / autonomy boundary

Capabilities should be typed and scoped rather than exposing arbitrary database/tool power.

Suggested autonomy levels:

```text
A0 prohibited
A1 human execution required
A2 human approval required
A3 autonomous + mandatory post-review
A4 autonomous + monitoring / real rollback or compensation
A5 fully autonomous bounded internal operation
```

Autonomy belongs to capability + context.

An agent/provider may not self-promote its autonomy or authority.

A future `AutonomyEvidenceProfile` may support governed promotion recommendations using acceptance, modification, rejection, contradiction, grounding, SLA, incident and rollback metrics.

---

## 16. Execution sandbox

Powerful runtimes should use bounded controls for:

- filesystem;
- network;
- secrets;
- shell;
- connectors;
- execution time;
- token/model cost;
- production mutation;
- external actions.

No local-first/coworker convenience justifies unrestricted secrets/network/filesystem access.

Production domain mutation remains Command-Gateway-only.

---

## 17. Atomic/versioned mutation and concurrency

Rejected/bad/stale proposals must not corrupt the prior accepted state.

Prefer:

```text
proposal
→ validate / approve
→ expected-version check
→ atomic commit
```

Material assessments/rules/plans/drafts should use version/supersession rather than destructive overwrite where appropriate.

Irreversible external actions must preserve the exact approved proposal and execution result.

Stale proposal is a normal state, not an error to bypass.

---

## 18. OrganizationActivity tiering

The semantic relationship remains:

```text
AgentMessage ⊂ OrganizationActivity
```

Runtime activity classes:

```text
CONVERSATIONAL
COLLABORATIVE
OPERATIONAL
MATERIAL
AUTHORITY
```

Provider/native event volume must not drown material history.

Suggested policy direction:

- conversational — high volume, inspectable, policy-governed summarization/compression after retention window;
- collaborative — structured handoff/peer-review history;
- operational — durable execution history;
- material — long-term durable / strongly indexed;
- authority — highest durability and tamper-evident/immutable target linked to AuditLog and exact approved payload.

Compression does not mean permitted humans lose the ability to inspect relevant conversation history.

---

## 19. Munder Difflin boundary

Munder Difflin is an A+ reference / controlled-research candidate for:

- organization/agent identities;
- communication/mailboxes;
- memory mechanics;
- orchestration;
- dependencies;
- scheduling;
- budgets/cost;
- circuit breakers;
- skills;
- live organization visualization.

It may not own AIOS Mission/WorkItem/Decision/Activity/Evidence/VerifiedRule/authority semantics.

Its provider-native messages/events may feed AIOS normalization but are not canonical by existence alone.

Its workers may not receive arbitrary production-domain DB mutation capability.

---

## 20. OpenWorker boundary

OpenWorker is an A+ reference / controlled-research candidate for:

- finished work;
- artifacts/files;
- terminal/tools;
- MCP;
- connectors;
- scheduled work;
- approval inbox patterns;
- external actions;
- model portability;
- local-first Coworker execution.

External action functionality remains subject to AIOS proposal/approval and Command Gateway rules.

OpenWorker tasks/sessions do not replace AIOS Missions/WorkItems.

OpenWorker processes may not write canonical production-domain state around the Command Gateway.

---

## 21. Execution Broker / complementary frameworks

AIOS may compose Munder/OpenWorker/AIOS-native capabilities when that produces better governed results.

The Execution Broker may consider:

- capability;
- quality;
- SLA;
- workload;
- evidence requirements;
- human-review requirements;
- cost;
- privacy/data-use;
- provider health;
- fallback.

Duplicate-framework restraint does **not** mean forcing one winner when technologies own genuinely complementary responsibilities.

It still means not retaining duplicate production solutions for the same capability without measured justification.

---

## 22. Durable execution / telemetry separation

- **Temporal** may eventually own durable timer/retry/signal mechanics.
- **OpenTelemetry/Langfuse** own engineering telemetry/observability roles.
- **OrganizationActivity** remains AIOS semantic organizational history.
- **AuditLog** remains business/security audit state.
- **Evidence/source/certification** remains separate legal/evidence provenance.

No one substitutes for another.

Temporal/provider execution histories cannot override AIOS version/precondition semantics.

---

## 23. Document / OCR boundary

Docling/document parsers/OCR produce machine-readable normalization/extraction signals.

They do not establish:

- authenticity;
- legal sufficiency;
- certification;
- eligibility;
- publication;
- authority.

PaddleOCR/Unlimited-OCR should be benchmarked only when measured Docling/current-stack gaps justify another OCR technology.

---

## 24. Privacy / minimum necessary

A future Presidio/Privacy Gateway may assist with sensitive-data detection/transformation.

Automated PII detection is not proof of complete de-identification.

Tool/provider context should follow recipient identity, purpose, minimum necessary fields, sensitivity, tenancy, retention and re-identification policy.

ContextBundle provenance and context hashes should support later reconstruction without creating unrestricted data copies.

---

## 25. Internal Learning & Quality

Keep three uses distinct:

1. operational intelligence;
2. evaluation/quality;
3. training/optimization.

Permitted corrections, proposal modifications/rejections, approvals, OCR/document corrections, routing outcomes, SLA misses, contradiction recovery, stale proposals, execution failures and provider outcomes may become quality/learning signals.

A record valid for service operation or analytics is not automatically valid for training.

Training/evaluation lineage must preserve the difference among original proposal, validation result, human correction, accepted canonical outcome, execution result and rollback/compensation.

Real-client-data training/reuse requires the applicable processing purpose, legal/compliance treatment, special-category safeguards where relevant, retention/deletion, tenant/data-use policy and lineage.

---

## 26. Provider replacement / exit

AIOS records must remain meaningful if a provider disappears.

Before production adoption define:

- external-ID mapping;
- export/rebuild path;
- rollback;
- replacement interface;
- minimum authoritative AIOS data required to reconstruct capability.

If provider removal requires rewriting core domain semantics, the integration is too coupled.

---

## 27. Security / license / operations review

Before adoption re-check:

- canonical repository/project;
- license/open-core terms;
- transitive dependencies;
- security advisories;
- network/filesystem/secrets access;
- data residency;
- tenancy;
- deletion/backups;
- telemetry export;
- update cadence;
- deployment/supportability;
- SBOM/container provenance where applicable;
- mutation-path architecture;
- concurrency/precondition behavior;
- rollback/compensation support;
- idempotency for consequential effects.

---

## 28. Adoption lifecycle

Strategic fit and adoption state remain separate.

```text
REFERENCE
→ RESEARCH
→ BENCHMARK
→ PILOT
→ TRIAL
→ ADOPT
```

Passing a pilot does not automatically mean `ADOPT`.

---

## 29. Change-management rule

A Radar technology enters or expands runtime only through a bounded slice documenting:

- problem;
- AIOS-owned capability boundary;
- alternatives;
- security/license/data flow;
- authority impact;
- proposal/approval impact where relevant;
- canonicalization behavior;
- mutation path;
- concurrency/preconditions;
- failure modes;
- rollback/compensation;
- learning labels/lineage;
- benchmark/acceptance;
- exit strategy;
- ROADMAP/CHANGELOG updates.

Repository popularity alone is not an adoption criterion.

---

## 30. Current architecture decision

The active organization architecture is V1.2.

Platform architecture may proceed in parallel with Phase 13.17 human acceptance.

This parallelism does not permit:

- bypassing unresolved human findings;
- claiming docs as runtime acceptance;
- weakening evidence/authority/security boundaries;
- letting agents silently execute proposal-first consequential actions;
- LLM-only canonicalization of material state;
- autonomous production mutation outside Command Gateway;
- stale writes overriding newer accepted state;
- treating audit history as rollback;
- flattening rejected/modified/contradicted outputs into training truth.

The objective is a **high-autonomy, low-corruption organization**: agents can think, collaborate and prepare work broadly, while AIOS remains conservative at the point where information becomes canonical truth or real-world consequence.

> **Agents are allowed to be wrong while thinking; AIOS is not allowed to be wrong silently when committing truth.**
