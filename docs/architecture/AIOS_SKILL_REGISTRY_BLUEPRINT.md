# AIOS Skill Registry Blueprint

**Status:** V1.3.6 TRANCHE 1 ARCHITECTURE / NOT IMPLEMENTED

## Canonical boundary

```text
Human Owner / delegated registry steward
                 ↓
         Skill Registry Service
        ┌────────┼─────────┐
        │        │         │
 definitions  versions  assignments
        │        │         │
        └────────┴─────────┘
                 ↓
       Context/runtime preparation
                 ↓
          capability check
                 ↓
           authority check
                 ↓
           Command Gateway
```

The registry owns skill identity, version, content hash, provenance, requirements, risk declaration and position assignment. It does not own authority, autonomy, Evidence, runtime credentials or Command Gateway outcomes.

## Proposed ports

```text
SkillRegistryPort
  get_active_definition(skill_id, version?)
  list_position_assignments(tenant_id, position_key, at_time)
  validate_assignment(position, skill, purpose, jurisdiction)
  resolve_execution_manifest(work_item, position, context_bundle)

ExternalSkillImportPort
  inspect_candidate(source_ref, source_pin, content_hash)
  compile_review_packet(candidate)

SkillProjectionPort
  project_a2a_agent_skills(position, disclosure_policy)
```

`resolve_execution_manifest` returns a derived, non-authorizing manifest containing exact skill versions, requirements and allowed output schemas. Command Gateway remains responsible for permission.

## Required persistence properties

- UUID identity with stable semantic `skill_id` and immutable semantic version;
- tenant-safe assignment and global/tenant definition ownership declared explicitly;
- unique `(skill_id, version)` and content hash;
- no in-place mutation of ACTIVE content;
- durable lifecycle and reviewer lineage;
- time-bounded assignments and revocation;
- exact skill-version lineage on AgentRun/ActionOutput where used;
- idempotent import and assignment commands;
- no credential or personal case material in definitions.

## Failure semantics

Fail closed when a skill is missing, inactive, hash-mismatched, unreviewed, out of scope, revoked, stale or assigned to a different position/tenant. A missing skill may block execution but may never relax evidence or authority gates.

## Non-goals

- generic marketplace installation;
- using skill text as a system prompt without review;
- granting tools or external action through skill metadata;
- replacing ContextBundle or Evidence;
- publishing internal skill/authority details through A2A by default.

## Implementation gate

Implementation requires a post-L product need, domain schema review, migration proposal, Command Gateway integration design, tenant/replay/revocation tests and an explicit acceptance record. This blueprint alone authorizes none of them.
