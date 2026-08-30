# AIOS Red Team / Adversarial Security Lab Blueprint

**Status:** V1.3.6 TRANCHE 1 ARCHITECTURE / NOT IMPLEMENTED
**Purpose:** authorized, isolated and reproducible security assurance for AIOS boundaries

## Governance topology

```text
Human Owner / Security Governance
              ↓
      Engagement Contract
              ↓
        Isolated Red Team Lab
     ┌────────┼─────────┐
     │        │         │
 Inspect AI  Promptfoo  garak challenger
     │        │         │
     └────────┴─────────┘
              ↓
        raw observations
              ↓
 reproduction + defensive triage
              ↓
      reviewed SecurityFinding
              ↓
       defensive remediation
              ↓
        independent retest
```

## Engagement contract

Every execution binds:

- owner and approving authority;
- exact target identity/version/hash;
- permitted target class and tenant;
- attack families and prohibited techniques;
- start/end time and execution budget;
- credential references and privilege floor;
- network allowlist/deny-by-default policy;
- synthetic data/fixture hashes;
- sandbox image/tool/version hashes;
- stop conditions and kill switch;
- evidence retention/redaction policy;
- defensive owner and escalation route.

The lab cannot create or widen its own engagement.

## Target classes

```text
SYNTHETIC_FIXTURE          allowed at R3
DISPOSABLE_TEST_SERVICE    allowed at R3 with explicit scope
STAGING                    future separate approval
PRODUCTION                 prohibited by this blueprint
THIRD_PARTY                prohibited without explicit owner/legal authority
```

## Finding lifecycle

```text
OBSERVED
→ REPRODUCED
→ VALIDATED | FALSE_POSITIVE | DISPUTED
→ ACCEPTED
→ REMEDIATION_IN_PROGRESS
→ RETESTED
→ CLOSED | REOPENED
```

Tool output creates `OBSERVED` only. `VALIDATED` requires an AIOS-owned reproduction with exact target/config/evidence. `ACCEPTED` requires the defensive owner or delegated security authority. A model or scanner cannot approve its own result.

## Finding contract

```text
finding_id / version / status
engagement + target + fixture references
attack class and mapped AIOS invariant/control
exact tool/skill/config versions
reproduction steps and artifact hashes
observed vs expected behavior
impact/severity/confidence with rationale
data/secret exposure classification
defensive owner and disposition
remediation and retest references
created/reviewed/closed timestamps
```

Findings are security-assurance records. They are not immigration Evidence/VerifiedRules and do not replace canonical OrganizationActivity.

## Initial AIOS security matrix

| Attack | Expected boundary |
|---|---|
| prompt/source injection | instruction/data separation; governed source remains data |
| memory poisoning | current Evidence/VerifiedRule overrides memory |
| MCP tool poisoning/shadowing | reviewed catalog + exact per-call authorization |
| external A2A skill inflation | discovery claim never grants skill/authority |
| privilege/authority escalation | Authority Engine + Command Gateway deny |
| agent impersonation | authenticated identity/trust registration required |
| cross-tenant access | tenant mismatch denied and surfaced |
| secret request/exfiltration | SecretsPort boundary; no prompt/context exposure |
| replay/duplicate effect | idempotency or ambiguous-effect reconciliation |
| fabricated approval | exact authenticated approval receipt required |
| provider hallucinated authority | provider/model authority remains false |
| excessive agency/external action | retained authority and explicit human gate |

## Lab data and observability

Use synthetic data. Logs and traces may contain adversarial content and must be access-controlled, redacted and retention-limited. Engineering telemetry observes lab execution; it does not establish finding truth or canonical business Activity.

## Tool strategy

```text
Inspect AI  leading structured evaluation-lab candidate
Promptfoo   leading application/MCP red-team candidate
garak       independent model/system scanner challenger
```

The first R3 lab should use the minimum tool set that proves the engagement/finding contracts. Tool diversity is not itself assurance.

## Adoption gate

Implementation requires post-L scheduling or an authorized immediate security need, isolated infrastructure, threat model, engagement/finding schemas, access and secrets design, cleanup/recovery runbook, safe-content handling, deterministic fixtures, owner-approved test scope and an acceptance record.
