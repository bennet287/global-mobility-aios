# Global Mobility AIOS — Technology Radar V1.3.6

**Date:** 2026-08-31
**Status:** ACTIVE CANONICAL RADAR REVISION
**Supersedes for active radar direction:** `TECHNOLOGY_RADAR_V1_3_5.md`
**Inherited baseline:** all V1.3.5 classifications remain unchanged unless explicitly overridden below
**Scheduling authority:** `docs/ROADMAP.md`
**Adoption truth index:** `docs/TECHNOLOGY_ADOPTION_LEDGER.md`
**Current product milestone:** L — Live Organization — IMPLEMENTED / ACCEPTANCE PENDING
**M milestone:** NOT STARTED

V1.3.6 makes the Radar deliberately more aggressive as a discovery, benchmarking, evaluation and security instrument while preserving necessity-gated production adoption.

> **Aggressive Radar. Conservative production authority.**

> **External infrastructure provides capability. AIOS owns meaning, truth and authority.**

A technology can be aggressively researched, benchmarked, attacked, compared or rejected without becoming a production dependency. No Radar entry grants organizational truth, Evidence status, authority, autonomy, credentials, network scope or permission to execute material actions.

## 1. Unchanged constitutional rules

```text
CAN DO != MAY DO
MEMORY != EVIDENCE
SANDBOX ISOLATION != EXECUTION AUTHORITY
AGENT FRAMEWORK STATE != ORGANIZATION TRUTH
UI INTENT != COMMAND AUTHORIZATION
TELEMETRY != CANONICAL ORGANIZATION ACTIVITY
SKILL KNOWLEDGE != EXECUTION AUTHORITY
```

The V1.3.5 external-agent classifications remain active: Microsandbox, Mem0, OpenViking, Agno/AgentOS, LangGraph and CopilotKit/AG-UI retain their existing states and boundaries. The V1.3.4/V1.3.5 Cybersecurity Skill Registry and isolated Red Team / Adversarial Security Lab architecture also remains active and must not be redesigned from zero.

## 2. Evaluation and adversarial engineering lane

The prior three-case Austria benchmark and deterministic tests are useful bounded signals but are not sufficient as a mature AI-quality claim. V1.3.6 therefore makes evaluation-depth itself a first-class Radar lane.

Target evidence ladder:

```text
unit contracts
→ deterministic adversarial mutation
→ property / invariant testing
→ mutation testing
→ fuzzing
→ deterministic fault injection
→ real-provider evaluation
→ fresh-source evaluation
→ cross-provider disagreement analysis
→ poisoned/contradictory context evaluation
→ authorization/replay/tenant-isolation attacks
→ concurrency/race proof
→ independent professional domain review
→ isolated Red Team / purple-team retest
→ continuous regression
```

Each layer has its own proof label. A lower layer must never be reported as proof of a higher layer.

### Current evaluation/security candidates

| Technology / approach | Intended AIOS capability | V1.3.6 state | Immediate rule |
|---|---|---|---|
| Promptfoo | AI regression / adversarial evaluation | **PILOT COMPLETE / TRIAL-ELIGIBLE — EXPANSION CANDIDATE** | extend existing pilot; do not restart |
| Garak | LLM vulnerability / adversarial probing | **RESEARCH / BOUNDED LIVE-MODEL PILOT CANDIDATE** | isolated targets only; no production-target authority |
| Microsoft PyRIT | orchestrated AI red-team evaluation | **RESEARCH / RED-TEAM-LAB CANDIDATE** | only under future authorized `AdversarialEngagement` |
| DeepEval | LLM/evaluation test framework | **RESEARCH / BENCHMARK CANDIDATE** | benchmark only against concrete metric gaps |
| Ragas-style evaluation | retrieval/RAG evaluation methods | **RESEARCH / BENCHMARK CANDIDATE** | Evidence truth remains AIOS-owned |
| Hypothesis | Python property-based testing | **BENCHMARK / HIGH-PRIORITY ENGINEERING CANDIDATE** | use first on invariant-heavy governance/evaluation seams |
| mutmut or equivalent | mutation testing / test-strength measurement | **RESEARCH / BOUNDED PILOT CANDIDATE** | measure whether tests kill meaningful logic mutations |
| Atheris / guided Python fuzzing | parser/contract fuzzing | **RESEARCH / BOUNDED PILOT CANDIDATE** | target bounded parsers/contracts, not uncontrolled systems |
| deterministic fault injection | provider/storage/network failure assurance | **PRIORITY ENGINEERING APPROACH** | prefer first-party deterministic seams before adding a chaos platform |

The bounded Wave E2 implementation is recorded in `TECHNOLOGY_RADAR_WAVE_E2_EVALUATION_HARDENING_2026-08-31.md`.

## 3. Security engineering and software-supply-chain lane

The Radar should actively evaluate commodity security tooling rather than waiting for an incident.

| Technology / approach | Capability | V1.3.6 state | Boundary |
|---|---|---|---|
| Semgrep | SAST / custom security rules | **PRIORITY RESEARCH / PILOT CANDIDATE** | findings are evidence for review, not authority |
| GitHub CodeQL | semantic code security analysis | **PRIORITY RESEARCH / BENCHMARK CANDIDATE** | compare coverage/cost with Semgrep; avoid redundant mandatory gates without evidence |
| Trivy | container/IaC/dependency scanning | **PRIORITY RESEARCH / PILOT CANDIDATE** | security gate only after bounded proof |
| Syft | SBOM generation | **RESEARCH / PILOT CANDIDATE** | SBOM is software inventory evidence |
| Grype | SBOM/package vulnerability matching | **RESEARCH / BENCHMARK CANDIDATE** | vulnerability feed result != exploitability/authority truth |
| SLSA | build provenance model | **RESEARCH / TARGET CONTROL** | integrate only when release artifact path warrants it |
| Sigstore/cosign | artifact signing/provenance | **RESEARCH / PILOT CANDIDATE** | signing key/identity lifecycle must be governed |
| Gitleaks or equivalent | repository secret scanning | **PRIORITY RESEARCH / PILOT CANDIDATE** | complements SecretsPort; does not replace runtime secret management |
| OWASP API Security testing | API attack/assurance methodology | **PRIORITY RESEARCH / CONTINUOUS TEST TARGET** | authorized local/test environments only |

These candidates align with the already-reviewed defensive cybersecurity donor tranche. Their presence here does not mean the upstream skill corpus or any tool is installed.

## 4. Observability / AI-quality analysis lane

OpenTelemetry remains the vendor-neutral foundation and is already pilot-complete/trial-eligible.

Langfuse remains a specialized candidate rather than a missing baseline:

```text
AIOS + OpenTelemetry operational correlation
→ measure LLM-specific analysis gap
→ if material, bounded Langfuse comparison behind telemetry boundary
→ typed/exportable telemetry
→ AIOS truth remains canonical
```

**Langfuse state remains RESEARCH / PILOT CANDIDATE.** Do not install it merely because V1.3.6 is aggressive.

Potential benchmark questions include prompt/run trace usability, evaluation linkage, provider/model cost attribution, dataset experiment comparison, retention/privacy boundaries and exit/export cost.

## 5. Sandbox and Red Team acceleration

Microsandbox remains the highest-priority future isolated execution candidate for engineering/security workloads. Garak and PyRIT are now explicit Radar candidates for the future lab, but neither is adopted.

Permitted future shape:

```text
approved AdversarialEngagement
→ Command Gateway / policy
→ SandboxPort
→ optional Microsandbox adapter
→ approved Garak/PyRIT/other bounded evaluator
→ isolated target
→ durable execution receipt / finding
→ defensive remediation
→ independent retest
```

Rejected shape:

```text
red-team tool installed
→ permission to attack arbitrary target
```

The current deterministic Wave E2 gate is a defensive precursor only and has `red_team_runtime_claim=false`.

## 6. Retrieval, context and memory challengers

Existing V1.3.5 states remain:

- LLMLingua-2 — selected compression pilot;
- pgvector — benchmark;
- Qdrant — current platform capability / comparison baseline;
- Mem0 — explore as L1 continuity provider only;
- OpenViking — research/context-database donor only;
- LangGraph — research execution-graph donor;
- Agno/AgentOS — assess/donor candidate;
- Temporal — gap-triggered/deferred;
- Pydantic AI — research/pilot candidate.

An aggressive Radar means these technologies may be re-benchmarked as the product changes. It does not mean running several overlapping memory, workflow or agent control planes simultaneously.

## 7. Privacy / document / source-intelligence lane

Existing classifications remain active and should not be forgotten:

- Docling — PILOT IN PROGRESS;
- Presidio — QUEUED PILOT;
- urlwatch — QUEUED PILOT;
- ClamAV — PILOT COMPLETE / TRIAL-ELIGIBLE.

A future evaluation should first inspect existing first-party document normalization, source monitoring, privacy and upload-security seams so the project does not duplicate native capability under a new package name.

## 8. Frontend interaction lane

CopilotKit / AG-UI remains **EXPLORE / POST-L FRONTEND INTERACTION CANDIDATE**. It is one of the strongest M-aligned candidates but does not start M before L acceptance.

The evaluation should challenge the existing Cockpit on:

- generative UI usefulness rather than novelty;
- human-in-loop clarity;
- shared agent/UI state without second truth;
- accessibility and responsive behavior;
- latency and failure states;
- command authorization through AIOS APIs;
- maintenance cost and exit path.

## 9. Promotion rules

A Radar candidate can move toward runtime only when:

1. the product/risk problem is explicit;
2. native capability and existing pilots were inspected first;
3. the candidate has a bounded owner port/boundary;
4. privacy, licensing, recovery and authority effects are understood;
5. a falsifiable benchmark/pilot exists;
6. replacement/exit cost is acceptable;
7. the candidate demonstrably outperforms or fills a gap rather than merely increasing architecture surface;
8. repository truth is reconciled in the adoption ledger, ROADMAP and CHANGELOG.

## 10. Current scheduling truth

```text
L runtime acceptance evidence              COMPLETE / ACCEPTED
Wave E2 deterministic adversarial gate     IMPLEMENTED / LOCAL-CI PROOF PENDING
professional Austria review                PENDING
final exact-current-head technical proof   PENDING
L overall                                  IMPLEMENTED / ACCEPTANCE PENDING
M                                          NOT STARTED

Promptfoo expansion                        ALLOWED AS SUPPORTING EVALUATION WHEN JUSTIFIED
Hypothesis / mutation-test benchmark       HIGH-PRIORITY NEXT EVALUATION CANDIDATES
Garak / PyRIT live adversarial pilot        DEFER TO AUTHORIZED ISOLATED LAB / POST-L NEED
Microsandbox execution pilot               DEFER UNTIL POST-L NEED
CopilotKit / AG-UI                         DEFER UNTIL L SEALED / M
```

V1.3.6 expands the **research and benchmark frontier**, not the current product milestone.
