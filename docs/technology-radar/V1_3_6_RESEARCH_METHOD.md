# Technology Radar V1.3.6 — Research Method

**Date:** 2026-08-30
**Status:** ACTIVE RESEARCH METHOD / NO PRODUCTION ADOPTION
**Scope:** V1.3.6 Tranche 1 — skills, authorization, MCP/A2A interoperability, and adversarial evaluation
**Repository baseline:** `a9e52c28af05893a2ed6397b6bf6ba26df2f55a5`

## 1. Constitutional boundary

```text
Technology Radar = research + architecture + controlled experiments
Technology Radar != production adoption
Technology Radar != Milestone M
Research prototype != canonical AIOS implementation
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
```

No research result may mutate canonical Evidence, VerifiedRules, authority, autonomy, WorkItems, OrganizationActivity, professional-review status, or L acceptance state.

## 2. Evidence hierarchy

Candidate research uses sources in this order:

1. versioned specification or official project documentation;
2. exact upstream source/release pin and license;
3. upstream security policy, advisories and issue history;
4. reproducible isolated experiment;
5. AIOS-owned test fixtures and results;
6. secondary commentary only as discovery input.

Every record must include a review date and exact upstream pin when a source repository exists. A moving `main` branch, product landing page, popularity count or vendor benchmark is not durable adoption evidence.

## 3. Research maturity

```text
R0 DISCOVERED
R1 RESEARCHED
R2 ARCHITECTURE FIT ASSESSED
R3 ISOLATED LAB VERIFIED
R4 PILOT APPROVED
R5 INTEGRATION CANDIDATE
R6 ADOPTED
```

V1.3.6 Tranche 1 targets R2. A candidate may reach R3 only through an isolated, non-production experiment with deterministic fixtures, explicit network/credential scope, reproducible commands and retained results. No Tranche 1 candidate reaches R4–R6 through documentation alone.

## 4. Six-stage assessment

### A — Identity

Record project/vendor or foundation, license, reviewed pin/version, governance, release cadence, supported deployment modes, language/runtime surface, self-hosted posture, cloud dependency and archival status.

### B — Functional fit

Evaluate a concrete AIOS problem rather than generic product quality. Each candidate must answer one or more of:

- can it express or support what an AI employee knows without granting permission?
- can it check whether a specific principal may perform a specific action on a specific resource in the supplied context?
- can it expose tools or remote agents without bypassing Command Gateway?
- can it generate reproducible security/evaluation evidence without becoming canonical truth?

### C — Architectural sovereignty

Determine whether the candidate can sit behind an AIOS-owned port and remain replaceable. Penalize any requirement that external framework/session/graph/memory/policy state become canonical organization, Evidence, WorkItem, Activity, authority or autonomy truth.

### D — Security

Review authentication, authorization, delegation, confused-deputy risk, credential handling, tenant isolation, network exposure, prompt/tool injection, supply-chain risk, auditability, data residency, secret handling, sandbox assumptions and fail-open behavior.

### E — Operations

Evaluate deployment complexity, dependencies, latency, consistency, availability, failure behavior, observability, backup/recovery, upgrade path, self-hosting, cost and vendor lock-in.

### F — Decision

Assign one decision state:

```text
ADOPT
ASSESS
EXPLORE
RESEARCH
HOLD
REJECT
```

The numerical score informs the decision but never overrides a hard constitutional blocker.

## 5. AIOS reference benchmark

All candidates use the same bounded organization fixture:

```text
Human Owner
└─ Austria Mobility Team
   ├─ Regulatory Agent
   ├─ Pathway Agent
   ├─ Document Agent
   └─ Client Communication Agent
```

The Regulatory Agent may retrieve an approved official source, analyze a governed rule and produce an internal finding. It may not send a legal conclusion to a client or submit an application.

Required scenarios:

| Scenario | Required result |
|---|---|
| capability without authority | internal analysis allowed; client send and submission denied |
| malicious MCP tool advertisement | discovery succeeds; unauthorized invocation denied before provider call |
| external A2A skill advertisement | capability claim becomes untrusted discovery data only |
| memory poisoning | governed current VerifiedRule wins over remembered threshold |
| source prompt injection | source content remains untrusted data, never instruction |
| duplicate external command | one canonical execution or fail-closed reconciliation |
| stale/revoked grant | authorization fails closed at command time |
| evaluator finding | finding remains provisional until reproduced and accepted by AIOS |

## 6. Experiment contract

An R3 experiment must declare:

```text
candidate + exact version/pin
owner
question being tested
non-production target
fixture identities and data classification
network and credential scope
expected allow/deny matrix
commands and environment
result hashes/artifacts
failure and cleanup behavior
observed limitations
decision and expiry/review date
```

Experiments use synthetic or non-personal data. They may not use real mobility cases, production credentials, unrestricted repository content, government submission endpoints or live client communication.

## 7. Decision record requirements

Each decision record must state:

- what need exists now;
- why native AIOS capability is insufficient or sufficient;
- build vs integrate vs donor comparison;
- canonical state ownership;
- authority and failure boundary;
- data/secret flow;
- operational and licensing implications;
- replacement/exit path;
- score and hard blockers;
- next trigger and decision expiry.

An untriggered candidate stays research-only even when its score is high.

## 8. Tranche 1 source pins

Reviewed on 2026-08-30:

| Candidate | Exact upstream pin | License observed from GitHub metadata |
|---|---|---|
| OpenFGA | `openfga/openfga@a7dfe8491dc7f9cd5905f4e9ae6c8e1d718c4bd9` | Apache-2.0 |
| OPA | `open-policy-agent/opa@8e733384254aa0211f0464852f2881f83d700bf1` | Apache-2.0 |
| Cedar | `cedar-policy/cedar@468eaef41a4fd27c17a02cef48b58bce7f2034fc` | Apache-2.0 |
| SpiceDB | `authzed/spicedb@1ba6b9714f0a1af73d20033c63977d963f2a9a84` | Apache-2.0 |
| MCP | `modelcontextprotocol/modelcontextprotocol@ca4ab3027f7c844cd3039c956438d72e8253f7f5` | GitHub metadata `NOASSERTION`; license review required before adoption |
| A2A | `a2aproject/A2A@f63dbb48271940ca5bd421f87e27e4d6ec002795` | Apache-2.0 |
| Inspect AI | `UKGovernmentBEIS/inspect_ai@56c9cae65844c87479b10e212a93b91e1a17c351` | MIT |
| Promptfoo | `promptfoo/promptfoo@90fa399b941364363f57288fbf305b6d6aaff7ed` | MIT |
| garak | `NVIDIA/garak@8ed1543b985a5722adb659584182faf6f7907d4e` | Apache-2.0 |

Primary documentation references are recorded in the candidate research files. These pins make the review reproducible; they do not approve dependencies or production use.
