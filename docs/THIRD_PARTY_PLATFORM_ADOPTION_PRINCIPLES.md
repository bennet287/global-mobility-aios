# Global Mobility AIOS — Third-Party Platform Adoption Principles

**Version:** V1.1
**Date:** 2026-08-18
**Status:** Current architecture principle
**Supersedes:** V1 wording only where V1.1 adds the Internal Learning & Quality and AIOS Coworker boundaries

This document defines the permanent ownership boundary between Global Mobility AIOS and external
frameworks, libraries, engines, services, standards, and infrastructure. V1.1 preserves the V1
semantic-sovereignty rules and adds explicit Internal Learning & Quality, data-use lineage, and AIOS
Coworker principles. The active radar is [TECHNOLOGY_RADAR_V1_1.md](TECHNOLOGY_RADAR_V1_1.md);
[TECHNOLOGY_RADAR_V1.md](TECHNOLOGY_RADAR_V1.md) remains historical evidence.

## 1. AIOS Semantic Sovereignty Principle

> **Third-party infrastructure may implement, accelerate, observe, execute, retrieve, parse,
> scan, render, evaluate, or enforce an AIOS-defined capability, but it must never become
> authoritative for AIOS domain meaning, legal status, evidence status, certification state,
> human-review requirements, publication state, organizational authority, or business outcome
> semantics.**

## 2. AIOS always owns

- domain/case/mobility semantics;
- legal/business conclusion state;
- jurisdiction/effective-period meaning;
- evidence and source-snapshot state;
- certification and VerifiedRule state;
- pathway/publication lifecycle;
- human-review requirements;
- positions, delegation and Board authority;
- WorkItem, Blocker, Dependency and HumanActionRequest meaning;
- ExecutiveDecision meaning;
- Contribution semantics;
- semantic OrganizationActivity;
- business audit semantics;
- final evidence/provenance interpretation.

## 3. Third parties may

Through bounded adapters, external components may:

- parse/OCR/classify;
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
- provide processing lineage.

Their output is input to an AIOS decision/state transition, not the authoritative transition.

## 4. Third parties may not implicitly

- declare immigration/legal eligibility;
- approve evidence/certification;
- publish a pathway;
- promote draft state to production;
- infer organization authority from prompts/titles;
- bypass backend authorization;
- bypass HumanActionRequest/human-review gates;
- turn retrieval similarity into legal truth;
- turn source diffs into VerifiedRules;
- turn OCR confidence into authenticity;
- turn malware-clean status into evidence approval;
- turn workflow completion into business approval;
- turn telemetry into OrganizationActivity;
- become the sole provenance record.

## 5. Adapter-first rule

Preferred:

```text
AIOS domain/service
  ↓
AIOS-owned capability contract
  ↓
AIOS adapter
  ↓
external technology
```

Avoid broad provider-specific imports throughout domain services.

### Timing

Technology Radar V1 documents conceptual ports, but **does not create empty runtime interfaces**.
A runtime contract appears only when the first real integration needs it.

## 6. Provider replacement

AIOS records must remain meaningful if the provider disappears.

Examples:

- document/evidence state must survive replacing Docling/OCR;
- WorkItems remain meaningful without Temporal;
- authorization semantics remain understandable without OpenFGA;
- Activity remains canonical if Langfuse traces expire;
- source snapshots remain authoritative if monitoring tooling changes.

External IDs are traceability mappings, not semantic primary keys.

## 7. Evidence/legal boundary

```text
external parser/retriever/model output
  ↓
candidate information
  ↓
AIOS provenance/evidence checks
  ↓
domain rules
  ↓
required review/certification
  ↓
governed AIOS transition
```

Never `model/retrieval/parsing result → legal truth`.

## 8. Authorization boundary

- **OpenFGA candidate:** relationship authorization.
- **OPA candidate:** AIOS-defined system/policy gates.
- **AIOS:** organization authority, domain/legal/business meaning and authoritative mutation.

Navigation visibility is not permission.

## 9. Durable execution boundary

A future Temporal layer may own timer durability, retries, resumption, signals and execution
history.

AIOS owns case/workflow meaning, WorkItems, blockers, dependencies, human actions, decisions,
Contributions, semantic Activity, and case/legal outcomes.

## 10. Telemetry and provenance separation

- **OpenTelemetry/Langfuse:** engineering trace.
- **OpenLineage candidate:** processing lineage.
- **OrganizationActivity:** semantic organizational history.
- **AIOS evidence/source/certification:** legal/evidence provenance.

No category may replace another.

## 11. Privacy/minimum necessary data

External AI/infrastructure should not receive sensitive values merely because they exist in a
case.

A future Privacy Gateway should apply purpose, recipient/tool identity, minimum necessary fields,
redaction/pseudonymization, retention, re-identification permission, and human-review rules.

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
parser/OCR
```

A clean scan does not establish authenticity or evidence validity.

## 13. Retrieval boundary

Semantic retrieval may identify candidate evidence. AIOS must still verify jurisdiction, source
authority, effective date, certification state, supersession and tenancy.

Vector similarity is not legal truth.

## 14. Agent-framework boundary

Agent frameworks may provide typed model calls, tools, provider adapters and structured outputs.

They may not grant authority through prompts, replace deterministic business logic without
justification, publish evidence, approve certification, or establish final legal outcomes.

## 15. Evaluation boundary

AI evaluation tools may run regression/red-team/prompt-injection tests. They do not become
production authority.

Evaluation configuration capable of code/tool execution must be treated as trusted engineering
material and isolated appropriately.

## 16. Rendering/signature boundary

Rendering success does not prove factual correctness, approval or certification.

Cryptographic signature validity does not independently establish legal acceptance of the document
contents.

## 17. License/security review

Before adoption re-check:

- canonical project/repository;
- current license/open-core boundaries;
- transitive dependencies;
- security advisories;
- data sent to the component;
- network/filesystem/secrets access;
- update cadence;
- SBOM/container provenance where relevant.

## 18. Data residency

Document where data is processed/persisted, deletion behavior, backup behavior, telemetry export,
tenancy, encryption and operator access.

Sensitive mobility data must not leave the controlled environment merely because an SDK makes it
easy.

## 19. Exit strategy

Before adoption define:

- data export;
- provider-ID mapping;
- rebuild strategy for derived data;
- rollback;
- replacement boundary;
- minimum authoritative AIOS data required to reconstruct the capability.

If removal requires rewriting core semantics, the integration is too coupled.

## 20. Duplicate-framework restraint

- one primary production agent runtime after evaluation;
- one primary retrieval architecture unless real workloads prove a split;
- no multiple orchestration frameworks by default;
- OpenTelemetry remains the neutral trace contract;
- DSPy stays offline if Pydantic AI becomes production runtime;
- Haystack is benchmarked, not automatically adopted.

## 21. Change-management rule

A Radar technology enters runtime only through a bounded slice documenting problem, boundary,
alternatives, security/license, data flow, authority impact, failure modes, benchmark, acceptance,
rollback, exit and ROADMAP/CHANGELOG updates.

Repository popularity is not an adoption criterion.

## 22. Internal Learning & Quality Principle

> **Subject to applicable law, contractual commitments, declared processing purposes, required
> safeguards, and the applicable data-use policy, AIOS should maximize lawful learning from the
> work it performs. Evaluation, quality improvement, operational intelligence, retrieval/document
> improvement, workflow optimization, and appropriate internal model training are first-class
> product purposes.**

This principle does **not** mean every record is automatically trainable. It means AIOS should be
architected so that permitted operational outcomes, corrections, approvals/rejections, retrieval
results, document corrections, agent outcomes and workflow signals can become traceable quality
or learning assets when their use is allowed.

## 23. Separate operational intelligence, evaluation and training

AIOS must preserve three distinct uses:

1. **operational intelligence** — understand work, bottlenecks, workloads, source quality and
   outcomes;
2. **evaluation/quality** — measure correctness, correction rates, retrieval/OCR quality, agent
   success, tool failures and regressions;
3. **training/optimization** — build permitted corpora for fine-tuning, specialized models,
   prompt/program optimization, retrieval/ranking improvements and planning improvements.

A record being valid for analytics does not automatically make it valid for model training.

## 24. Human corrections are governed learning assets

Professional corrections, review outcomes, approvals, rejections, evidence edits and OCR fixes
are high-value supervised quality signals.

Where permitted, AIOS should preserve the relationship between:

```text
prediction / extraction / recommendation
        ↓
professional or human decision
        ↓
difference / confirmation
        ↓
Learning Record
```

The learning record must retain provenance and must not rewrite the authoritative business/legal
record merely to create training data.

## 25. Learning and training lineage

AIOS should be able to establish which source categories, datasets, transformations, human
corrections, evaluation corpora and promotion decisions contributed to a model/program version.

Training/evaluation lineage is separate from:

- AIOS evidence/legal provenance;
- OrganizationActivity;
- business AuditLog;
- engineering telemetry.

No one lineage layer may silently substitute for another.

## 26. Data-use policy boundary

A future AIOS data-governance layer should express allowed/conditional/excluded uses for service
operation, quality assurance, analytics, agent/safety evaluation, workflow/retrieval/document
improvement, prompt/program improvement, human quality review and internal model training.

It should also preserve the relevant processing purpose, lawful-basis/compatibility analysis,
tenant, provenance, sensitivity classification, retention class and training lineage.

The data-use layer exists to make permitted learning enforceable and auditable, not to block
learning by default and not to imply universal reuse permission.

## 27. EU compliance boundary for learning

Where GDPR applies, learning/evaluation/training involving personal data requires the applicable
processing purpose, legal basis or compatible-purpose analysis, transparency, minimisation,
retention/security controls and other required safeguards. Special-category personal data requires
an applicable Article 9 condition and any additional required safeguards.

The EDPB's AI-model guidance requires case-specific assessment; it does not create a blanket
permission or blanket prohibition on AI model development using personal data.

If AIOS later becomes a provider of a general-purpose AI model under the EU AI Act, GPAI provider
obligations may become relevant. Using or fine-tuning a third-party model does not automatically
settle that classification; the applicable Commission guidance and the significance of the
modification must be assessed at that time.

This is an architecture requirement, not a final legal determination. Concrete production
processing regimes require legal/privacy review before enablement.

## 28. AIOS Coworker boundary

**AIOS Coworker** is the AIOS-owned product capability for governed finished-work execution.
OpenWorker (`andrewyng/openworker`) is an A+ strategic reference / controlled-pilot candidate,
not the domain abstraction.

```text
AIOS domain truth + Organization OS
        ↓
AIOS Coworker capability
        ↓
AIOS-owned execution/tool/connector contracts
        ↓
OpenWorker-derived or other bounded implementation
        ↓
finished deliverable
        ↓
governed outcome
        ↓
permitted learning/evaluation signals
```

A third-party coworker/runtime may not redefine WorkItem, Blocker, Dependency,
HumanActionRequest, ExecutiveDecision, Contribution, Activity, authority, evidence truth,
certification, publication, or legal/business outcome semantics.

## 29. Finished work over chat alone

The platform should increasingly use agents to produce useful governed outcomes and artifacts,
not merely conversational instructions. Finished work remains subject to the same authority,
review, evidence and publication gates as any other AIOS operation.

