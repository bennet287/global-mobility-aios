# Global Mobility AIOS — Third-Party Platform Adoption Principles

**Version:** V1.1  
**Date:** 2026-08-19  
**Status:** Current architecture principle  
**Supersedes:** V1 wording only where V1.1 adds Internal Learning & Quality, AIOS Coworker, Agent Organization Fabric, Execution Broker, human-like organization, and performance-governance boundaries

This document defines the permanent ownership boundary between Global Mobility AIOS and external frameworks, libraries, engines, services, standards, and infrastructure.

The active radar is [TECHNOLOGY_RADAR_V1_1.md](TECHNOLOGY_RADAR_V1_1.md). The canonical human-like organization direction is [HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1.md](HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1.md). [TECHNOLOGY_RADAR_V1.md](TECHNOLOGY_RADAR_V1.md) remains historical evidence.

## 1. AIOS Semantic Sovereignty Principle

> **Third-party infrastructure may implement, accelerate, execute, retrieve, parse, monitor, observe, scan, render, evaluate, optimize, coordinate, remember, connect, or otherwise support an AIOS-defined capability, but it must never become authoritative for AIOS domain meaning, legal status, evidence state, certification state, publication state, human-review requirements, organizational authority, Mission/WorkItem semantics, ExecutiveDecision semantics, Contribution semantics, OrganizationActivity semantics, or business outcomes.**

## 2. AIOS always owns

- domain/case/mobility semantics;
- legal/business conclusion state;
- jurisdiction/effective-period meaning;
- evidence and source-snapshot state;
- certification and VerifiedRule state;
- pathway/publication lifecycle;
- human-review requirements;
- positions, delegation and Board authority;
- Mission semantics;
- WorkItem, Blocker, Dependency and HumanActionRequest meaning;
- HumanAction meaning;
- AgentConversation semantics;
- ExecutiveDecision meaning;
- Contribution semantics;
- canonical OrganizationActivity semantics;
- Capability Registry semantics;
- SLA/KPI/OKR semantics;
- Definition of Done / outcome semantics;
- business audit semantics;
- final evidence/provenance interpretation.

## 3. Third parties may

Through bounded adapters / Execution Broker contracts, external components may:

- parse/OCR/classify;
- normalize documents;
- detect or transform PII;
- scan malware;
- monitor sources and detect changes;
- retrieve semantic candidates;
- persist timers/retries/execution waits;
- trace/evaluate model and tool execution;
- optimize offline experiments;
- evaluate AIOS-defined authorization relationships;
- evaluate AIOS-defined system policies;
- render/convert documents;
- validate cryptographic signatures;
- provide processing lineage;
- execute AI/model/tool steps;
- produce files and finished deliverables;
- connect to external systems through tools/MCP/connectors;
- provide agent communication transport;
- provide agent mailboxes/message routing;
- provide working-memory mechanisms;
- provide orchestration/supervisor mechanics;
- provide schedules/heartbeats;
- provide budget/cost telemetry;
- provide progressive execution/circuit-breaker mechanics;
- provide visualization/event feeds.

Their output is input to AIOS-owned organizational/domain state, not an authoritative replacement for it.

## 4. Third parties may not implicitly

- declare immigration/legal eligibility;
- approve evidence/certification;
- publish a pathway;
- promote draft state to production;
- infer organization authority from prompts, personas, titles, provider roles or model confidence;
- bypass backend authorization;
- bypass mandatory HumanActionRequest/human-review gates;
- turn retrieval similarity into legal truth;
- turn source diffs into VerifiedRules;
- turn OCR/document-normalization confidence into authenticity;
- turn malware-clean status into evidence approval;
- turn workflow completion into business approval;
- turn telemetry into OrganizationActivity;
- turn provider memory into Evidence, VerifiedRule or certification;
- turn a provider task into an AIOS Mission or WorkItem automatically;
- turn a provider message into ExecutiveDecision automatically;
- turn a provider event log into the canonical AIOS OrganizationActivity ledger automatically;
- become the sole provenance record.

## 5. Adapter-first / Execution Broker rule

Preferred:

```text
AIOS domain / Organization OS
  ↓
AIOS-owned capability contract
  ↓
AIOS Execution Broker / adapter
  ↓
external technology
```

Avoid broad provider-specific imports throughout domain services.

### Timing

The Technology Radar documents conceptual boundaries but **does not create empty runtime interfaces merely because a candidate exists**. A runtime contract appears when a bounded implementation needs it and its acceptance contract is known.

## 6. Provider replacement

AIOS records must remain meaningful if a provider disappears.

Examples:

- document/evidence state survives replacing Docling/OCR;
- Missions and WorkItems remain meaningful without Munder Difflin/OpenWorker/Temporal;
- AgentConversation remains meaningful if a message provider changes;
- authorization semantics remain understandable without OpenFGA;
- OrganizationActivity remains canonical if provider logs/Langfuse traces expire;
- source snapshots remain authoritative if monitoring tooling changes;
- finished deliverables remain attached to AIOS outcomes even if OpenWorker is replaced.

External IDs are traceability mappings, not semantic primary keys.

## 7. Evidence/legal boundary

```text
external parser / retriever / model / memory / agent output
  ↓
candidate information / working context
  ↓
AIOS provenance + evidence checks
  ↓
domain rules
  ↓
required review / certification
  ↓
governed AIOS transition
```

Never `model/retrieval/parsing/memory/conversation result → legal truth`.

## 8. Authorization boundary

- **OpenFGA candidate:** relationship authorization evaluation.
- **OPA candidate:** narrow AIOS-defined system/policy gates.
- **AIOS:** organization authority, domain/legal/business meaning and authoritative mutation.

Navigation visibility, provider role, system prompt, persona and model confidence are not permission.

## 9. Durable execution boundary

A future Temporal layer may own timer durability, retries, resumption, signals and execution history.

AIOS owns Mission/workflow meaning, WorkItems, blockers, dependencies, human actions, decisions, Contributions, OrganizationActivity and case/legal/business outcomes.

## 10. Telemetry, Activity and provenance separation

- **OpenTelemetry/Langfuse:** engineering trace.
- **OpenLineage candidate:** processing lineage.
- **AIOS OrganizationActivity:** semantic organizational history, including normalized conversational/collaborative/operational activity.
- **AIOS evidence/source/certification:** legal/evidence provenance.

No category may replace another.

Important refinement:

```text
AgentMessage ⊂ OrganizationActivity
```

is valid **when the message is normalized into the AIOS-owned activity model**.

But:

```text
provider message log ≠ canonical OrganizationActivity automatically
telemetry trace ≠ OrganizationActivity
conversation ≠ authority
```

## 11. Privacy/minimum necessary data

External AI/infrastructure should not receive sensitive values merely because they exist in a case.

A future Privacy Gateway should apply purpose, recipient/tool identity, minimum necessary fields, redaction/pseudonymization, retention, re-identification permission, and human-review rules.

Automated PII detection is a safety aid, not proof of complete de-identification.

## 12. Untrusted document boundary

```text
upload
  ↓
type/size validation
  ↓
hash
  ↓
quarantine
  ↓
malware scan
  ↓
safe-to-process state
  ↓
document normalization / parser / OCR
```

A clean scan does not establish authenticity or evidence validity. Document normalization does not establish legal sufficiency.

## 13. Retrieval boundary

Semantic retrieval may identify candidate evidence. AIOS must still verify jurisdiction, source authority, effective date, certification state, supersession and tenancy.

Vector similarity is not legal truth.

## 14. Agent-framework / organization-framework boundary

Agent frameworks may provide typed model calls, tools, provider adapters, structured outputs, message transport, working memory, supervisor/orchestrator mechanics, schedules and circuit breakers.

They may not grant authority through prompts/personas, replace deterministic business logic without justification, publish evidence, approve certification, establish final legal outcomes, or substitute provider task/message/memory semantics for AIOS Missions, WorkItems, Decisions, OrganizationActivity or evidence state.

## 15. Munder Difflin boundary

Munder Difflin (`chaitanyagiri/munder-difflin`) is an A+ strategic architecture reference / controlled pilot-research candidate for the AIOS Agent Organization Fabric.

Its useful reference concepts include:

- persistent identities;
- mailboxes and routed messages;
- long-term/working memory;
- supervisor/orchestrator coordination;
- task/dependency coordination;
- scheduled missions / heartbeat;
- human intervention patterns;
- budgets/cost telemetry;
- OpenTelemetry spans;
- progressive circuit breakers;
- skills/capability discovery;
- live organization visualization.

Munder Difflin may not define AIOS Mission, WorkItem, Blocker, Dependency, HumanActionRequest, ExecutiveDecision, Contribution, evidence, certification, publication, authority, canonical OrganizationActivity or business-outcome semantics.

Its local file/git hive is a provider implementation detail/reference pattern, not the AIOS authoritative persistence model.

## 16. OpenWorker / AIOS Coworker boundary

OpenWorker (`andrewyng/openworker`) is an A+ strategic reference / controlled-pilot candidate for governed finished-work execution.

```text
AIOS Mission / governed work
        ↓
AIOS Execution Broker
        ↓
AIOS-owned execution/tool/connector contract
        ↓
OpenWorker-derived or other bounded implementation
        ↓
finished deliverable / external action
        ↓
AIOS quality + authority gates
        ↓
governed outcome
```

A third-party coworker/runtime may not redefine Mission, WorkItem, Blocker, Dependency, HumanActionRequest, ExecutiveDecision, Contribution, OrganizationActivity, authority, evidence truth, certification, publication or legal/business outcomes.

## 17. Munder + OpenWorker cooperation principle

AIOS should not optimize for framework competition when complementary capabilities produce a better governed result.

A single Mission may legitimately involve:

- Munder-inspired multi-agent communication/coordination;
- AIOS-native domain/evidence services;
- OpenWorker-style finished-work/tool/connector execution;
- deterministic services;
- specialist models;
- required professional/human gates.

The AIOS Execution Broker owns the composition decision.

> **Results matter more than framework ownership, while semantic sovereignty remains non-negotiable.**

## 18. Human-like interaction boundary

Agents should be allowed to behave like capable colleagues: ask questions, clarify, suggest, disagree, request assistance, hand off work, warn, acknowledge, review, and coordinate without creating a formal WorkItem or human escalation for every interaction.

This human-like behavior must remain bounded by:

- deterministic authority;
- evidence/legal truth rules;
- SLA/Definition of Done;
- quality gates;
- privacy/data-use constraints;
- required human/professional review.

> **Natural interaction, deterministic accountability.**

## 19. Activity is broad; authority is narrow

OrganizationActivity may include conversational, collaborative, operational, material and authority-bearing activity.

A message can be genuine OrganizationActivity without becoming a decision.

A conversation can create understanding without creating authority.

Only the appropriate governed transition can create a Decision, approval, certification, publication, external action or legal/business conclusion.

## 20. Distributed human review / escalation boundary

The canonical escalation principle is:

> **Resolve autonomously where permitted. Collaborate before escalating. Escalate to the lowest level with the necessary expertise or authority. Reserve Board attention for genuinely Board-level matters.**

```text
agent can resolve → agent
colleague expertise → collaborate
operational authority → department lead
professional judgement → Professional / Operator
personal fact → Mobility User
executive authority → executive / CEO
reserved material authority → Human Owner / Board
```

Board Room remains reserved authority, not a generic review inbox.

## 21. Persona + deterministic authority

Rich organizational persona may inform reasoning, priorities, communication style and delegation strategy.

Actual authority comes from deterministic AIOS runtime position/delegation contracts.

```text
persona / identity
      +
position contract / delegated authority
      =
governed organizational agent
```

When they disagree, deterministic authority wins.

## 22. Human Owner privileged command

Natural-language commands from authenticated humans are an interface to existing AIOS authority, not a new source of authority.

The Human Owner / Board may exercise the highest organizational privileges available through normal AIOS governance.

High-impact commands may receive an interpretation preview to reduce ambiguity. The preview does not create or remove authority.

## 23. Mission / WorkItem boundary

Mission represents the outcome-level organizational objective. WorkItems represent durable units of work needed to achieve it.

Provider tasks may help execute WorkItems/Missions but do not become authoritative Mission/WorkItem records automatically.

A conversation may create a WorkItem only when actual durable work is warranted.

## 24. Capability Registry / Execution Broker boundary

Provider skills, tools and connectors register behind AIOS-owned capability semantics.

The Execution Broker may consider capability, authority, SLA risk, workload, historical quality, rework, cost, privacy/data-use constraints and provider health.

Provider skill names do not become AIOS organizational semantics.

## 25. SLA / KPI / OKR boundary

SLAs, KPIs and OKRs measure/steer organizational performance; they do not grant authority or change evidence truth.

KPIs should support diagnosis and improvement rather than create a simplistic competitive agent leaderboard.

> **Team/Mission outcome is the primary performance unit.**

## 26. Progressive intervention boundary

AIOS should prefer progressive intervention:

```text
NORMAL
→ STEER
→ ASSIST / PEER SUPPORT
→ REASSIGN
→ CONSTRAIN
→ SUSPEND SPECIFIC AGENT / CAPABILITY
→ EXECUTIVE / HUMAN ESCALATION
→ EMERGENCY ORGANIZATION STOP
```

Global pause must remain an emergency governance action, not a normal troubleshooting fallback.

## 27. Evaluation boundary

AI evaluation tools may run regression/red-team/prompt-injection tests. They do not become production authority.

Evaluation configuration capable of code/tool execution must be treated as trusted engineering material and isolated appropriately.

## 28. Rendering/signature boundary

Rendering success does not prove factual correctness, approval or certification.

Cryptographic signature validity does not independently establish legal acceptance of document contents.

## 29. License/security review

Before adoption re-check:

- canonical project/repository;
- current license/open-core boundaries;
- transitive dependencies;
- security advisories;
- data sent to the component;
- network/filesystem/secrets access;
- update cadence;
- SBOM/container provenance where relevant.

## 30. Data residency

Document where data is processed/persisted, deletion behavior, backup behavior, telemetry export, tenancy, encryption and operator access.

Sensitive mobility data must not leave the controlled environment merely because an SDK makes it easy.

## 31. Exit strategy

Before adoption define:

- data export;
- provider-ID mapping;
- rebuild strategy for derived data;
- rollback;
- replacement boundary;
- minimum authoritative AIOS data required to reconstruct the capability.

If removal requires rewriting core semantics, the integration is too coupled.

## 32. Duplicate-framework restraint

- maintain one AIOS-owned semantic organization model;
- maintain one AIOS-owned Execution Broker contract;
- prefer one primary production agent runtime per actual overlapping capability after evaluation, unless measured needs justify plurality;
- complementary Munder/OpenWorker roles may coexist if they measurably improve outcomes rather than duplicate the same responsibility;
- one primary retrieval architecture unless real workloads prove a split;
- OpenTelemetry remains the neutral trace contract;
- DSPy stays offline if Pydantic AI becomes the production runtime;
- Haystack remains benchmark-only unless measured requirements justify it.

## 33. Change-management rule

A Radar technology enters runtime only through a bounded slice documenting:

- problem;
- AIOS-owned boundary;
- alternatives;
- security/license/data flow;
- authority impact;
- evidence impact;
- failure modes;
- SLA/quality expectations where relevant;
- benchmark;
- acceptance;
- rollback;
- exit strategy;
- ROADMAP/CHANGELOG updates.

Repository popularity or visual appeal alone is not an adoption criterion.

## 34. Internal Learning & Quality Principle

> **Subject to applicable law, contractual commitments, declared processing purposes, required safeguards, and the applicable data-use policy, AIOS should maximize lawful learning from the work it performs. Evaluation, quality improvement, operational intelligence, retrieval/document improvement, workflow optimization, organizational improvement, and appropriate internal model training are first-class product purposes.**

This does **not** mean every record is automatically trainable.

## 35. Separate operational intelligence, evaluation and training

AIOS preserves three distinct uses:

1. **Operational intelligence** — work, bottlenecks, capacity, conversations, collaboration, source quality and outcomes.
2. **Evaluation/quality** — correctness, correction rates, retrieval/OCR quality, agent success, collaboration quality, SLA performance, tool/provider failure and regressions.
3. **Training/optimization** — permitted corpora for fine-tuning, specialized models, prompt/program optimization, routing/retrieval/ranking and planning improvements.

A record being valid for analytics does not automatically make it valid for model training.

## 36. Human corrections are governed learning assets

Professional corrections, Owner redirections, review outcomes, approvals/rejections, evidence edits and OCR fixes are high-value supervised signals where reuse is permitted.

```text
prediction / extraction / plan / recommendation
        ↓
professional / Owner / human decision
        ↓
difference / confirmation
        ↓
Learning Record
```

Learning records retain provenance and never rewrite the authoritative business/legal record merely to create training data.

## 37. Organizational learning assets

Where permitted, AIOS may also learn from:

- successful/failed collaboration paths;
- unnecessary handoffs;
- repeated questions;
- SLA misses;
- capacity rebalancing;
- routing outcomes;
- peer-review disagreements;
- provider/runtime success and cost;
- escalation appropriateness;
- Mission outcomes.

Operational learning does not create legal/evidence truth.

## 38. Learning and training lineage

AIOS should be able to establish which source categories, datasets, transformations, human corrections, organizational outcomes, evaluation corpora and promotion decisions contributed to a model/program version.

Training/evaluation lineage is separate from:

- AIOS evidence/legal provenance;
- OrganizationActivity;
- business AuditLog;
- engineering telemetry.

No one lineage layer may silently substitute for another.

## 39. Data-use policy boundary

A future AIOS data-governance layer should express allowed/conditional/excluded uses for service operation, quality assurance, analytics, agent/safety evaluation, workflow/retrieval/document improvement, organizational improvement, prompt/program improvement, human quality review and internal model training.

It should preserve relevant processing purpose, lawful-basis/compatibility analysis, tenant, provenance, sensitivity classification, retention class and training lineage.

The data-use layer exists to make permitted learning enforceable/auditable, not to block learning by default and not to imply universal reuse permission.

## 40. EU compliance boundary for learning

Where GDPR applies, learning/evaluation/training involving personal data requires the applicable processing purpose, legal basis or compatible-purpose analysis, transparency, minimisation, retention/security controls and other required safeguards. Special-category personal data requires an applicable Article 9 condition and additional safeguards.

The EDPB's AI-model guidance requires case-specific assessment; it does not create a blanket permission or blanket prohibition on AI model development using personal data.

A generic Terms clause is not treated as automatic authorization for every future learning use.

If AIOS later becomes a provider of a general-purpose AI model under the EU AI Act, GPAI provider obligations may become relevant. Using or fine-tuning a third-party model does not automatically settle that classification.

Concrete production processing regimes require legal/privacy review before enablement.

## 41. Finished work over chat alone

The platform should increasingly use agents to produce useful governed outcomes and artifacts, not merely conversational instructions.

Finished work remains subject to the same authority, review, evidence, SLA, Definition of Done and publication gates as any other AIOS operation.

## 42. Live Organization boundary

External visualization/event systems may inform the future Live Organization experience, but the Cockpit visualization must reflect AIOS-owned normalized state.

A provider avatar/status animation is not itself authority, WorkItem truth, SLA truth, evidence truth or OrganizationActivity until mapped to the relevant AIOS semantics.

The AIOS visual direction remains premium enterprise—deep navy/graphite, warm ivory, restrained motion and sophisticated information density—not a direct copy of a third-party visual style.

## 43. Outcome principle

> **Results matter more than provider competition.**

AIOS may combine complementary technologies when that measurably improves quality, SLA performance, reliability, cost or human effort without compromising semantic sovereignty, privacy, evidence boundaries or authority.

The organization optimizes for **governed Mission outcomes**, not framework loyalty.
