# Global Mobility AIOS — Third-Party Platform Adoption Principles

**Version:** V1.2  
**Date:** 2026-08-19  
**Status:** Current architecture principle  
**Active organization architecture:** [HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_1.md](HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_1.md)  
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
Context Broker / Canonicalization / Command Gateway / Execution Broker
  ↓
external technology
```

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
- Capability Registry;
- autonomy policy;
- SLA/KPI/OKR;
- Definition of Done;
- ConsequentialActionProposal lifecycle;
- approval/modification/rejection state;
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
- create candidate/proposed actions for AIOS review.

Their output is input to AIOS-owned canonicalization/domain transitions, not an automatic authoritative transition.

---

## 4. External technologies may not silently

They may not automatically:

- declare immigration/legal eligibility;
- certify Evidence;
- publish/change a VerifiedRule;
- publish a pathway;
- change client/case status;
- submit an application;
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
- write arbitrary production-domain state around the AIOS Command Gateway.

---

## 5. Broad cognition / scoped context

Agents may reason broadly, but sensitive information should be provided through task/tenant/purpose/sensitivity-scoped context.

The preferred pattern is:

```text
AIOS Context Broker
  ↓
ContextBundle
  ↓
agent/runtime
```

A ContextBundle may include only the case/documents/evidence/rules/conversations/decisions/unknowns needed for the Mission.

External providers must not receive unrelated sensitive information merely because it exists in the database.

---

## 6. Canonicalization boundary

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

---

## 7. Command boundary

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
- transaction safety.

An external runtime may request/propose a command. It may not bypass the command contract.

---

## 8. Consequential-action proposal boundary

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

Review belongs at the lowest appropriate human surface, not automatically Board Room.

---

## 9. Five hard semantic constraints

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
→ authority/evidence/state validation
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

## 10. Evidence / legal boundary

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

## 11. Trust ladder

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

Lower levels cannot skip mandatory promotion stages merely because a model is confident.

---

## 12. Confidence / grounding

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

## 13. Contradiction / self-correction boundary

Before material mutation, AIOS should check current:

- Evidence;
- VerifiedRules;
- source authority/effective date;
- supersession;
- case facts;
- pathway version;
- decisions;
- prior accepted state.

Unsupported/conflicted results should normally follow:

```text
self-correct
→ peer/specialist review where useful
→ human review where still required
```

Peer-agent agreement is a signal, not truth.

---

## 14. Capability / autonomy boundary

Capabilities should be typed and scoped rather than exposing arbitrary database/tool power.

Suggested autonomy levels:

```text
A0 prohibited
A1 human execution required
A2 human approval required
A3 autonomous + mandatory post-review
A4 autonomous + monitoring/rollback
A5 fully autonomous bounded internal operation
```

Autonomy belongs to capability + context.

An agent/provider may not self-promote its autonomy or authority.

---

## 15. Execution sandbox

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

---

## 16. Atomic/versioned mutation

Rejected/bad proposals must not corrupt the prior accepted state.

Prefer:

```text
proposal
→ validate / approve
→ atomic commit
```

and version/supersession rather than destructive overwrite for material assessments/rules/plans/drafts.

Irreversible external actions must preserve the exact approved proposal and execution result.

---

## 17. Munder Difflin boundary

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

---

## 18. OpenWorker boundary

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

---

## 19. Execution Broker / complementary frameworks

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

## 20. Durable execution / telemetry separation

- **Temporal** may eventually own durable timer/retry/signal mechanics.
- **OpenTelemetry/Langfuse** own engineering telemetry/observability roles.
- **OrganizationActivity** remains AIOS semantic organizational history.
- **AuditLog** remains business/security audit state.
- **Evidence/source/certification** remains separate legal/evidence provenance.

No one substitutes for another.

---

## 21. Document / OCR boundary

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

## 22. Privacy / minimum necessary

A future Presidio/Privacy Gateway may assist with sensitive-data detection/transformation.

Automated PII detection is not proof of complete de-identification.

Tool/provider context should follow recipient identity, purpose, minimum necessary fields, sensitivity, tenancy, retention and re-identification policy.

---

## 23. Internal Learning & Quality

Keep three uses distinct:

1. operational intelligence;
2. evaluation/quality;
3. training/optimization.

Permitted corrections, proposal modifications/rejections, approvals, OCR/document corrections, routing outcomes, SLA misses and provider outcomes may become quality/learning signals.

A record valid for service operation or analytics is not automatically valid for training.

Real-client-data training/reuse requires the applicable processing purpose, legal/compliance treatment, special-category safeguards where relevant, retention/deletion, tenant/data-use policy and lineage.

---

## 24. Provider replacement / exit

AIOS records must remain meaningful if a provider disappears.

Before production adoption define:

- external-ID mapping;
- export/rebuild path;
- rollback;
- replacement interface;
- minimum authoritative AIOS data required to reconstruct capability.

If provider removal requires rewriting core domain semantics, the integration is too coupled.

---

## 25. Security / license / operations review

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
- SBOM/container provenance where applicable.

---

## 26. Adoption lifecycle

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

## 27. Change-management rule

A Radar technology enters or expands runtime only through a bounded slice documenting:

- problem;
- AIOS-owned capability boundary;
- alternatives;
- security/license/data flow;
- authority impact;
- proposal/approval impact where relevant;
- failure modes;
- benchmark/acceptance;
- rollback;
- exit strategy;
- ROADMAP/CHANGELOG updates.

Repository popularity alone is not an adoption criterion.

---

## 28. Current architecture decision

The active organization architecture is V1.1.

Platform architecture may proceed in parallel with Phase 13.17 human acceptance.

This parallelism does not permit:

- bypassing unresolved human findings;
- claiming docs as runtime acceptance;
- weakening evidence/authority/security boundaries;
- letting agents silently execute proposal-first consequential actions.

The objective is a **high-autonomy, low-corruption organization**: agents can think, collaborate and prepare work broadly, while AIOS remains conservative at the point where information becomes canonical truth or real-world consequence.