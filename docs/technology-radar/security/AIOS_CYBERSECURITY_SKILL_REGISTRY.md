# AIOS Cybersecurity Skill Registry — V1.3.6 Research

**Status:** R2 ARCHITECTURE FIT ASSESSED / NO EXECUTABLE REGISTRY
**Relationship:** specialized governed subset of the future AIOS Skill Registry

## Purpose

Security skills need stronger controls than ordinary business-domain skills because many contain dual-use procedures, code execution, scanning, credential or network interaction.

```text
security knowledge != permission to test
test capability != authorized target scope
sandbox isolation != authorization
finding != verified security truth
```

## Initial taxonomy

```text
SECURITY.PROMPT_INJECTION
SECURITY.SOURCE_POISONING
SECURITY.RAG_POISONING
SECURITY.MCP_TOOL_POISONING
SECURITY.TOOL_SHADOWING
SECURITY.SECRET_EXPOSURE
SECURITY.PRIVILEGE_ESCALATION
SECURITY.AUTHORITY_BYPASS
SECURITY.MEMORY_POISONING
SECURITY.OUTPUT_EXFILTRATION
SECURITY.SUPPLY_CHAIN
SECURITY.REPLAY_ABUSE
SECURITY.IDENTITY_IMPERSONATION
SECURITY.TENANT_ISOLATION
SECURITY.EXCESSIVE_AGENCY
```

## Proposed definition extension

```yaml
skill_id: security.mcp.tool-poisoning.assess
version: 1.0.0
dual_use: true
risk_class: CRITICAL

attack_surface:
  - MCP_DISCOVERY
  - MCP_TOOL_CALL

execution_class: ISOLATED_LAB_ONLY
allowed_target_classes:
  - SYNTHETIC_FIXTURE
  - DISPOSABLE_TEST_SERVICE

prohibited_targets:
  - PRODUCTION
  - REAL_CLIENT_DATA
  - GOVERNMENT_ENDPOINT

sandbox_requirements:
  network_policy: DENY_BY_DEFAULT
  ephemeral_filesystem: true
  production_credentials: false

evidence_contract:
  - exact_target_hash
  - exact_attack_fixture_hash
  - command_and_tool_lineage
  - observed_result
  - reproduction_steps
  - control_mapping

human_authorization:
  engagement_required: true
  production_override: not_supported
```

The definition declares constraints; an authorized engagement supplies the exact target, time, operator and permitted action envelope.

## Import pipeline

```text
external security skill corpus
→ content-addressed quarantine
→ source/license/malware review
→ dual-use and execution classification
→ secret/network/tool instruction analysis
→ AIOS-owned rewritten definition
→ independent reviewer approval
→ disabled-by-default registry entry
```

Upstream instructions never execute during review. References to package installers, shells, network scanners or offensive tools remain inert text until a separately authorized isolated experiment.

## Separation of duties

- Security Governance approves engagement scope.
- Red Team executes only within that scope.
- Defensive owner validates impact and accepts remediation.
- Material remediation follows normal owner/Command Gateway authority.
- Retest should be independent of the original remediation author where feasible.
- No security agent may expand its own target, network, credentials, duration or attack class.

## Registry acceptance questions

- Can a dual-use skill be assigned to a production mobility employee? Expected: no.
- Can an engagement authorize an unspecified target? Expected: no.
- Can skill content request a secret or wider network scope? Expected: rejected/quarantined.
- Can a scanner result become an accepted finding automatically? Expected: no.
- Are exact skill, fixture, target and tool versions present in finding lineage?
- Does revocation prevent new engagements while preserving history?

## Decision

Define this as an AIOS-native restricted registry class. Do not install external security-skill collections or security tools into production agents through V1.3.6.
