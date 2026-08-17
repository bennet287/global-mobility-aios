# Global Mobility AIOS — Third-Party Platform Adoption Principles

**Version:** V1
**Date:** 2026-08-17
**Status:** Architecture principle

This document defines the permanent ownership boundary between Global Mobility AIOS and external
frameworks, libraries, engines, services, standards, and infrastructure.

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
