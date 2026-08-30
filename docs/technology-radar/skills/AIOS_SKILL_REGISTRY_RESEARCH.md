# AIOS Skill Registry — V1.3.6 Research

**Status:** R2 ARCHITECTURE FIT ASSESSED / NO RUNTIME IMPLEMENTATION
**Decision:** AIOS-native canonical registry; external skill formats are import/export projections only

## Problem

AIOS needs durable, inspectable truth about what an AI employee knows how to do without confusing that knowledge with executable permission.

```text
Skill       = versioned knowledge/procedure declaration
Capability  = technically available operation
Authority   = organization permission for a concrete action/resource
Autonomy    = permitted independence within granted authority
```

Possessing a skill never grants a capability, authority, tool credential or autonomy level.

## Proposed definition

```yaml
skill_id: austria.rwr.shortage.evaluate
version: 1.0.0
status: ACTIVE
content_sha256: <content-hash>

domain:
  jurisdiction: AT
  category: immigration

knowledge_sources:
  - source_type: governed_rule_family
    source_ref: at-rwr-skilled-worker-shortage-occupation

capability_requirements:
  - retrieve_official_sources
  - calculate_points
  - produce_internal_assessment

evidence_requirements:
  - VERIFIED_RULE
  - CURRENT_OFFICIAL_SOURCE

output_contracts:
  - internal_mobility_assessment_v1

risk_class: HIGH

authority_requirements:
  internal_assessment: REQUIRED
  client_communication: RETAINED_HUMAN_REVIEW
  government_submission: PROHIBITED_BY_SKILL

provenance:
  source_registry: aios
  reviewed_by: <durable-review-reference>
  reviewed_at: <timezone-aware-timestamp>
```

`authority_requirements` describes gates the consuming action must satisfy. It is not an embedded grant.

## Registry lifecycle

```text
DRAFT
→ REVIEWED
→ ACTIVE
→ DEPRECATED
→ REVOKED
```

Activation requires content hashing, source provenance, risk classification, output schema, evidence requirements and a reviewer with authority over the registry—not authority over every action performed using the skill.

A skill version is immutable once ACTIVE. Corrections create a new version. Revocation prevents new assignment/execution but does not rewrite historical AgentRun or ActionOutput lineage.

## Assignment model

```text
SkillDefinition
    ↓ versioned assignment
PositionSkillAssignment
    ↓ current OrganizationPosition
EmployeeRuntimeBinding
```

An assignment means the position may use the skill as knowledge when all separate context, capability, authority, autonomy, evidence and risk gates pass. Runtime availability cannot create an assignment.

Required assignment fields:

- tenant and persistent `position_key`;
- exact skill ID/version/content hash;
- assignment status and effective interval;
- assigning actor/position and authority reference;
- purpose and jurisdiction scope;
- revocation reason/reference;
- created/effective/revoked timestamps.

## External skill import

Third-party `SKILL.md`, plugin or registry content enters as an untrusted candidate:

```text
external skill content
→ content-addressed quarantine
→ license/security/source review
→ semantic classification
→ prohibited-instruction/tool analysis
→ AIOS-owned definition/version
→ authorized assignment
```

Direct bulk installation into privileged production agents is rejected.

## A2A projection

A future A2A Agent Card may expose a deliberately reduced projection:

```text
internal active skill
→ disclosure policy
→ public capability description
→ A2A AgentSkill
```

Never export internal evidence requirements, case access, authority grants, credentials, hidden policy, personal data or non-public organization structure. An inbound A2A AgentSkill is discovery metadata only and cannot create an AIOS SkillDefinition or assignment automatically.

## Acceptance questions for a later implementation

- Does replay resolve the exact historical skill version and content hash?
- Does revocation prevent new use while preserving historical lineage?
- Can two tenants assign the same definition without sharing authority or data?
- Can unreviewed external skill content reach a runtime? Expected: no.
- Can an assigned skill grant a tool or external action? Expected: no.
- Does an output identify the skill version actually used?
- Can A2A export disclose only the approved subset?

## Decision

```text
Canonical implementation: AIOS-native
External framework required: NO
Current maturity: R2
Implementation trigger: post-L capability requiring reusable governed skills
Production adoption: NONE
```
