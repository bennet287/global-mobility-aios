# Technology Radar V1.3.6 — Deep Evidence Research Method

**Date:** 2026-08-30
**Status:** ACTIVE DEEP-EVIDENCE METHOD / NO PRODUCTION ADOPTION
**Scope:** whole Technology Radar lifecycle, not only Tranche 1 or R3
**Supersedes inside V1.3.6:** earlier R0–R6 shallow maturity wording
**Repository baseline:** V1.3.6 research architecture rooted at `a9e52c28af05893a2ed6397b6bf6ba26df2f55a5`

## 1. Constitutional boundary

```text
Technology Radar = discovery + research + architecture + experiments
                 + shadow proof + integration proof + adoption governance
                 + continuous verification + retirement

Technology Radar != production authority
Technology Radar != Milestone M
Research prototype != canonical AIOS implementation
Candidate feature != product necessity
High score != adoption
Lab PASS != production PASS
```

Permanent constraints:

```text
CAN DO != MAY DO
SKILL != CAPABILITY
CAPABILITY != AUTHORITY
AUTHORITY != AUTONOMY
MEMORY != EVIDENCE
SANDBOX ISOLATION != EXECUTION AUTHORITY
AGENT FRAMEWORK STATE != ORGANIZATION TRUTH
TELEMETRY != CANONICAL ORGANIZATION ACTIVITY
UI INTENT != COMMAND AUTHORIZATION
EXTERNAL AGENT CLAIM != TRUST OR AUTHORITY
MODEL OUTPUT != HUMAN APPROVAL
RADAR EVIDENCE != PRODUCT ACCEPTANCE
```

No Radar result may silently mutate canonical Evidence, VerifiedRules, authority,
autonomy, WorkItems, OrganizationActivity, professional-review status or L
acceptance state.

## 2. Operating doctrine

The Radar is aggressive against uncertainty, feature shelfware and architectural
lock-in. It is conservative around production, authority, data and truth.

```text
DISCOVER FAST
PIN EXACTLY
MAP EVERY STRATEGIC FEATURE
TEST WHAT MAKES THE TECHNOLOGY SPECIAL
TRY TO KILL THE CANDIDATE
COMPARE AGAINST NATIVE AIOS
MEASURE FEATURE INTERACTIONS
PROVE FAILURE AND RECOVERY
SHADOW BEFORE INTEGRATION
PROVE REPLACEABILITY BEFORE ADOPTION
CONTINUOUSLY RE-VERIFY AFTER ADOPTION
RETIRE CLEANLY WHEN THE VALUE DISAPPEARS
```

A candidate survives because evidence demonstrates unique, necessary value—not
because it is popular, elegant or technically capable.

## 3. Full Radar maturity lifecycle

The canonical V1.3.6 maturity model is now R0–R8.

```text
R0  DISCOVER
 ↓
R1  UNDERSTAND
 ↓
R2  ARCHITECTURE PROVE
 ↓
R3  LAB PROVE
 ↓
R4  SHADOW PROVE
 ↓
R5  INTEGRATION PROVE
 ↓
R6  ADOPT
 ↓
R7  CONTINUOUSLY VERIFY
 ↓
R8  RETIRE / REPLACE
```

### R0 — DISCOVER

Required output: **Discovery Dossier**.

Record exact identity/version/pin, license, governance, maintainer concentration,
release cadence, security policy/advisories, deployment model, self-hosted/hosted
split, runtime, data-residency surface, minimum infrastructure, major competitors,
native AIOS alternative and initial product-need hypothesis.

R0 also produces a **Feature Potential Map**:

```text
feature
what it actually does
availability: OSS / hosted / experimental
why AIOS might need it
AIOS boundary touched
main risk
proof required
```

A candidate with no unique feature hypothesis exits at R0.

### R1 — UNDERSTAND

R1 verifies source-code and ecosystem reality rather than trusting marketing.

Inspect official docs/specification, actual source tree, release history, security
advisories, relevant issue history, dependency graph, breaking changes,
maintenance activity, edition/hosted feature boundaries and upstream benchmark
methodology.

Classify each strategic advertised feature:

```text
DOCUMENTED
IMPLEMENTED
EXPERIMENTAL
DEPRECATED
HOSTED_ONLY
OSS_AVAILABLE
UNVERIFIED_CLAIM
```

Every serious candidate is triangulated against:

```text
candidate A
candidate B
native AIOS / build-it-ourselves baseline
```

The question is not "is this technology good?" but "what unique value does it
remove, enable or simplify for AIOS?"

### R2 — ARCHITECTURE PROVE

R2 creates an AIOS mapping, not a generic architecture diagram.

Required:

1. Ownership Map — what AIOS owns, what the candidate owns, what is derived.
2. Anti-Fit Matrix — where the candidate fights AIOS architecture.
3. State Map — canonical, projected, cached, rebuildable and external state.
4. Failure Map — stale/wrong/unavailable behavior.
5. Exit Map — how AIOS replaces or removes it.
6. Feature Hypotheses — claims R3 must prove.
7. Native-Build Comparison — what custom code/infrastructure it would replace.

Example:

```text
H1 feature X removes custom code Y
H2 feature X remains derived from canonical AIOS state
H3 feature X preserves replay/history
H4 feature X fails closed under revocation/outage
H5 feature X gives measurable value over native AIOS
```

R2 scores architecture potential only. They are never empirical proof.

### R3 — LAB PROVE

R3 tests the technology's **native strategic features**, not merely mocks and
adapters.

Use the T0–T8 evidence tiers in section 4. R3 includes, where relevant:

- real component execution;
- native feature semantics;
- feature interaction;
- stateful lifecycle;
- adversarial/security;
- chaos;
- property/metamorphic testing;
- concurrency;
- performance;
- differential comparison;
- historical replay;
- fingerprinted evidence.

A technically successful candidate may still be rejected when it offers no
meaningful advantage over native AIOS.

### R4 — SHADOW PROVE

The candidate receives realistic work but cannot control canonical outcomes.

```text
realistic/staging command
       ├─ canonical AIOS path → authoritative result
       └─ candidate shadow    → comparison only
```

Measure agreement, false allows, false denies, latency, availability, drift,
explainability, operational burden and update/restart behavior.

For authority/security-critical candidates:

```text
FALSE ALLOW = 0
```

R4 should survive at least one meaningful restart/update/failure or
policy/version change for component types where that applies.

### R5 — INTEGRATION PROVE

R5 proves product integration without surrendering AIOS sovereignty.

Required:

- AIOS-owned port/adapter;
- bounded feature activation;
- migration/rebuild path;
- rollback;
- observability;
- config/secrets isolation;
- SBOM/dependency inventory;
- security review;
- upgrade proof;
- replacement test.

Mandatory question:

> Can Provider A be replaced by Provider B or a native evaluator without changing
> AIOS business semantics?

If replacement requires rewriting core truth/authority semantics, R5 fails.

### R6 — ADOPT

ADOPT is scoped, never blanket.

```text
Candidate X

ADOPTED FOR:
  bounded capability

NOT ADOPTED FOR:
  canonical truth
  authority ownership
  evidence ownership
  human approval
```

R6 requires R3 evidence, R4 shadow where applicable, R5
integration/rollback/replaceability proof, security/license review, operational
owner, recovery where stateful, runbook/SLO, upgrade strategy and exit strategy.

### R7 — CONTINUOUSLY VERIFY

Adopted technologies remain on the Radar.

Triggers include new releases, security advisories, license/governance changes,
regressions, incidents, major new competitors and native AIOS capability making
the dependency redundant.

Maintain:

```text
review cadence
release watch
security watch
compatibility corpus
upgrade rehearsal
cost/latency trend
replacement candidates
```

No blind upgrades.

### R8 — RETIRE / REPLACE

Retirement triggers include abandonment, degraded security posture, license
incompatibility, excessive cost, a better proven candidate, native replacement or
feature irrelevance.

Retirement proof includes state export/rebuild, adapter/dependency removal,
config/secret cleanup, documentation cleanup and historical evidence preservation.

A mature Radar proves technology can leave as cleanly as it arrived.

## 4. Evidence depth — T0 through T8

R0–R8 answers **where a candidate is in the adoption lifecycle**.

T0–T8 answers **how deep its evidence is**.

```text
T0  CONTRACT / MOCK / SERIALIZATION
T1  REAL COMPONENT BASIC CORRECTNESS
T2  NATIVE FEATURE DEPTH
T3  STATEFUL LIFECYCLE
T4  ADVERSARIAL / SECURITY
T5  CHAOS / FAILURE / RECOVERY
T6  CONCURRENCY / SCALE / PROPERTY
T7  CROSS-COMPONENT INTEGRATION
T8  HISTORICAL REPLAY / RESTORE / RETIREMENT
```

### T0
Schemas, adapters, serialization, fixture generation and normalization. Necessary,
but never proof that an external component or defense actually worked.

### T1
Real binary/container/service against basic positive/negative scenarios.

### T2
Features that justify the candidate: relationship graphs, policy bundles,
schema/entity models, MCP/A2A lifecycle, agent evaluation features, sandbox
isolation features, etc.

### T3
Create/update/revoke/expire/reassign/upgrade/rollback state over time.

### T4
Actual adversarial payloads with effects measured from real state.

### T5
Outages, timeouts, malformed responses, stale state, corrupted policy, restart
and recovery.

### T6
Concurrency, scale, property/metamorphic testing, generated state spaces and
differential testing.

### T7
Realistic cross-component AIOS flows.

### T8
Historical reconstruction, restore/rebuild, upgrade/rollback and clean removal.

A candidate cannot claim deep R3 verification merely because many T0 tests pass.

## 5. Feature Potential and Exploitation

Every active candidate owns:

### Feature Potential Map — R0/R1

Strategically relevant capabilities plus edition/version availability.

### Feature Exploitation Matrix — R2/R3+

```text
feature
AIOS use case
hypothesis
test tier
fixture
expected value
failure criterion
measured result
unique value over native/competitor
```

Before promotion beyond R3, the majority of strategically relevant features must
be exercised or explicitly excluded with rationale.

The target is not 100% vendor-feature coverage. It is deep coverage of features
that could materially improve AIOS.

## 6. Feature interaction testing

Important failures occur between features.

Examples:

```text
OpenFGA:
delegation + group membership + conditional relation + revocation

OPA:
bundle update + canonical data version + deny precedence + rollback

MCP:
tool discovery + authorization + reconnect + malicious metadata

Inspect:
agent + tool + approval + sandbox + scorer

Skill Registry:
version + assignment + revocation + execution lineage
```

A feature that passes alone but violates AIOS boundaries in combination fails.

## 7. Grand Integration Trial

The base fixture remains:

```text
Human Owner
└─ Austria Mobility Team
   ├─ Regulatory Agent
   ├─ Pathway Agent
   ├─ Document Agent
   └─ Client Communication Agent
```

The final cross-radar proof is the **Technology Radar Grand Integration Trial**.

Target composition:

```text
Human Owner
    ↓
AI Employee Team
    ├─ Skill Registry
    ├─ Memory/context
    ├─ Evidence/VerifiedRule
    ├─ Authority Engine
    ├─ Command Gateway
    ├─ MCP
    ├─ A2A
    ├─ Sandbox/execution
    ├─ Durable runtime
    ├─ Secrets
    ├─ Observability
    └─ Red Team / Evaluation Lab
```

Inject simultaneously using synthetic data:

- poisoned memory;
- malicious official-source instruction;
- malicious MCP metadata/result;
- malicious/inflated A2A Agent Card;
- fake human approval;
- model/provider authority hallucination;
- delegation revocation;
- duplicate command/replay;
- provider/tool timeout;
- telemetry outage;
- secret-canary request;
- durable-runtime/database interruption where safe.

Required invariants:

```text
Human Owner / Board sovereignty preserved
Authority preserved
Tenant boundary preserved
Evidence/VerifiedRule truth preserved
No unauthorized external action
No unauthorized canonical mutation
No secret exfiltration
Replay/reconciliation truthful
Failure evidence preserved
Decision lineage reconstructable
```

## 8. Security measurement rule

Security effects must be measured from real before/after state, not assigned.

Bad:

```python
effects = ZERO_EFFECTS
```

Required:

```text
before-state fingerprint
        ↓
execute actual attack
        ↓
after-state fingerprint
        ↓
derive canonical effect diff
```

Observe, where applicable: ActionOutput, AuthorityGrant, VerifiedRule, Evidence,
OrganizationActivity, external mock calls, cross-tenant reads and canary secrets.

## 9. Property and metamorphic proof

Permanent properties include:

```text
Removing authority can never turn DENY into ALLOW.
Revoking delegation can never increase permissions.
Higher risk can never grant more authority.
Cross-tenant movement cannot preserve privileged access accidentally.
Removing human approval cannot enable a retained action.
Unknown action cannot authorize.
Provider/model claims cannot increase authority.
A2A advertisement cannot increase local authority.
MCP descriptions cannot increase local authority.
Memory cannot override governed Evidence/VerifiedRule.
Telemetry cannot override canonical truth.
```

Use generated state spaces and shrinkable counterexamples where practical.

## 10. Differential testing

When multiple candidates solve the same semantics, compile the same AIOS-owned
scenario into each implementation.

```text
Native AIOS oracle
OpenFGA
OPA
Cedar
```

A disagreement becomes a first-class Radar event with a retained minimal
counterexample. Never choose the most permissive result to resolve disagreement.

## 11. Score, confidence and coverage

A single number is insufficient.

Track:

```text
Architecture Score
Security Score
Operational Score
Empirical Score

Confidence = LOW | MEDIUM | HIGH

Evidence coverage:
  feature
  security
  failure
  lifecycle
  integration
```

Score = how promising.
Confidence = how strong the evidence is.
Coverage = what remains untested.

## 12. Hard blockers

Numbers never override:

- external state becoming canonical AIOS truth;
- skill/capability discovery granting authority;
- Command Gateway bypass;
- memory/telemetry/scanner findings becoming Evidence automatically;
- secrets entering prompts/memory/Activity/repository state;
- unbounded production testing;
- cross-tenant ambiguity;
- fail-open privileged execution;
- unrecoverable lock-in;
- incompatible license/data-residency obligations.

## 13. Native-build and kill experiments

Every serious candidate must answer:

> Do we actually need this dependency?

Compare candidate technology vs native AIOS vs existing accepted subsystem.

Measure code/complexity removed, reliability/features gained, new operational and
security burden, cost and migration/exit burden.

A technically excellent technology may still be rejected because AIOS already
solves the problem better.

## 14. Experiment contract

Every experiment declares:

```text
candidate + exact version/pin
maturity stage
test tier(s)
owner
hypothesis
feature(s) exercised
non-production target
fixture/data classification
network/credential scope
commands/environment
expected invariants
result hashes/artifacts
failure/cleanup behavior
limitations
score/confidence/coverage delta
decision + expiry
```

## 15. Current evidence truth

The current V1.3.6 work must be described by evidence depth, not test count.

```text
Common contracts/mocks                  T0 PASS
OpenFGA real 120-case corpus            T1 PASS
OPA real 120-case corpus                T1 PASS
Authority adapter chaos                 T5 partial PASS
Authority native feature depth          T2 PENDING
Authority stateful lifecycle            T3 PENDING
Authority deep adversarial              T4 PENDING
Authority concurrency/property depth    T6 PENDING
Cedar real CLI                          T1 IN PROGRESS / rerun pending
Security 18-category native baseline    T0 CONTRACT SMOKE only
External security tools                 T1-T4 PENDING
Cross-lane integration                  T7 PENDING
Historical replay/retirement proof      T8 PENDING
```

The security baseline's 18 category mappings prove owned category coverage and
zero-effect contract shape. They do not prove 18 real attacks were resisted.

## 16. Existing source pins

Existing V1.3.6 source pins remain in force until explicitly refreshed:

| Candidate | Exact upstream pin | License observed from GitHub metadata |
|---|---|---|
| OpenFGA | `openfga/openfga@a7dfe8491dc7f9cd5905f4e9ae6c8e1d718c4bd9` | Apache-2.0 |
| OPA | `open-policy-agent/opa@8e733384254aa0211f0464852f2881f83d700bf1` | Apache-2.0 |
| Cedar | `cedar-policy/cedar@468eaef41a4fd27c17a02cef48b58bce7f2034fc` | Apache-2.0 |
| SpiceDB | `authzed/spicedb@1ba6b9714f0a1af73d20033c63977d963f2a9a84` | Apache-2.0 |
| MCP | `modelcontextprotocol/modelcontextprotocol@ca4ab3027f7c844cd3039c956438d72e8253f7f5` | metadata NOASSERTION; license review before adoption |
| A2A | `a2aproject/A2A@f63dbb48271940ca5bd421f87e27e4d6ec002795` | Apache-2.0 |
| Inspect AI | `UKGovernmentBEIS/inspect_ai@56c9cae65844c87479b10e212a93b91e1a17c351` | MIT |
| Promptfoo | `promptfoo/promptfoo@90fa399b941364363f57288fbf305b6d6aaff7ed` | MIT |
| garak | `NVIDIA/garak@8ed1543b985a5722adb659584182faf6f7907d4e` | Apache-2.0 |

Pins make research reproducible. They do not approve dependencies.
