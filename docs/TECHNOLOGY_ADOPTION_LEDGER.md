# Global Mobility AIOS — Technology Adoption Ledger

**Date:** 2026-08-31
**Status:** ACTIVE REPOSITORY-TRUTH INDEX
**Branch:** `roadmap/global-mobility-aios-v12`
**Original ledger baseline head:** `74082e7296e17333027cebd7ca602d408f558f95`
**Latest reconciliation:** V12.54 / V12.53 fail-fast local acceptance recorded; technology truth unchanged
**Scheduling authority:** `docs/ROADMAP.md`
**Technology evaluation authority:** `docs/TECHNOLOGY_RADAR_V1_3_8.md`
**Delivery history:** `docs/CHANGELOG.md`

This ledger prevents Radar entries from being mistaken for installed technology and prevents native AIOS capability from being mistaken for missing capability merely because an external product is absent.

## 1. Permanent rules

```text
Radar presence != runtime implementation
native capability != external-provider adoption
adapter implementation != production adoption
evaluation score != professional correctness
security finding != exploitability/authority truth
```

Before implementing a named technology inspect dependencies, imports, configuration, tests, commit history, ROADMAP, Radar, CHANGELOG and this ledger.

Permanent architecture boundaries:

```text
CAN DO != MAY DO
MEMORY != EVIDENCE
SANDBOX ISOLATION != EXECUTION AUTHORITY
AGENT FRAMEWORK STATE != ORGANIZATION TRUTH
UI INTENT != COMMAND AUTHORIZATION
TELEMETRY != CANONICAL ORGANIZATION ACTIVITY
SKILL KNOWLEDGE != EXECUTION AUTHORITY
```

## 2. Implemented / existing foundations — do not duplicate

| Capability | Repository truth |
|---|---|
| OpenTelemetry | vendor-neutral telemetry foundation exists; pilot complete / trial-eligible |
| Promptfoo | pilot complete / trial-eligible; expansion candidate, not a missing pilot |
| backup + isolated restore | bounded recoverability proof implemented |
| ClamAV | malware scan/quarantine pilot complete / trial-eligible |
| SecretsPort | AIOS-owned secret-reference boundary implemented |
| OpenBao | optional non-production bounded adapter implemented; production adoption not claimed |
| Wave E2 adversarial contract | first-party deterministic input-mutation gate implemented; local proof observed at historical exact head `285a7f08...`; higher-order security proof not claimed |
| Wave E3 property/invariant testing | Hypothesis-based bounded property suite implemented; local proof observed at historical exact head `285a7f08...`; Hypothesis is test-only |
| Wave E4 mutation strength | first-party bounded semantic implementation-mutation gate implemented; local exact-head proof observed at `5d8e940e...`: 8/8 selected mutants killed, 0 survived; full backend 1328 passed / 22 skipped |
| Docling | pilot in progress |
| Qdrant | current semantic-retrieval platform capability / comparison baseline |
| Austria Live Organization runtime quality | AIOS Board-safe transparency projection already exposes provider/model outcome, tokens, estimated provider cost, grounding/provenance and fallback state; Track B web presentation now consumes this native projection rather than adding donor telemetry truth |
| Austria Live Organization durable activity lineage | canonical OrganizationActivity + Board-transparency causation/trace projection already exists; Track B renders that lineage in the Cockpit instead of adding Munder/provider transcript/event truth; local + Chromium browser proof observed at exact head `958b796...` |
| Organization collaboration / coordination visualization | AIOS already exposes hierarchy focus through OrganizationPosition reporting lines, WorkItem dependency edges, cross-department friction, governed human follow-up and durable activity context; do not add a donor collaboration state/graph unless a concrete unmet UX need is proven |
| Austria blind professional-review handoff | existing professional-review compiler retained; reviewer-facing handoff excludes benchmark labels/rationale and blind reviewer returns compile afterward into canonical CONFIRMED/CORRECTED/DISPUTED/NEEDS_MORE_FACTS semantics; stable exact-head local proof observed at `d969c7d...`: 19 focused tests, blind packet/template assertions, fail-closed untouched return, 1332 passed / 22 skipped backend regression, repository gates and stable start/end SHA; genuine professional review still pending |

## 3. V1.3.8 consolidated seam decisions — do not revive held duplicates

| Seam | Incumbent / current baseline | Challenger | Held / watch truth |
|---|---|---|---|
| CI adversarial evaluation | Promptfoo pilot | Inspect AI | DeepEval, Ragas, PyRIT, DeepTeam HOLD_WITH_TRIGGER |
| live-model vulnerability scan | bounded current harness | Garak | FuzzyAI HOLD_WITH_TRIGGER |
| behavioral tool-use evaluation | first-party contracts | ToolSandbox / AgentDojo methods | distinct seam; no organization truth |
| property testing | Hypothesis implemented | none | no duplicate pilot needed |
| mutation strength | first-party Wave E4 gate | mutmut on Linux/CI trigger | external engine not adopted |
| parser/contract fuzzing | deterministic/property baseline | none yet | Atheris/FuzzyAI HOLD_WITH_TRIGGER |
| observability | OpenTelemetry foundation | Arize Phoenix | Langfuse, OpenInference, OpenLLMetry, Opik HOLD_WITH_TRIGGER |
| SAST | Semgrep | CodeQL | Bandit HOLD_WITH_TRIGGER |
| DAST/API | OWASP ZAP | Schemathesis | Nuclei HOLD_WITH_TRIGGER |
| dependency/container | Trivy | OSV-Scanner | Syft, Grype, Scorecard HOLD_WITH_TRIGGER |
| secret scanning | Gitleaks | TruffleHog | no third scanner currently justified |
| IaC assurance | Checkov | KICS | Kubescape/kube-bench WATCH for real Kubernetes only |
| sandbox | Microsandbox | E2B | Daytona HOLD_WITH_TRIGGER; Nightona WATCH |
| relationship authorization | OpenFGA | SpiceDB | R3 research only; no constitutional authority |
| contextual policy evaluation | OPA/Rego | Cedar | Kyverno WATCH for Kubernetes only |
| retrieval | Qdrant | pgvector | no duplicate vector store pilot |
| continuity memory | AIOS memory boundary | Mem0 | OpenViking DONOR_ONLY |
| durable workflow | AIOS WorkItem/runtime baseline | Temporal on trigger | LangGraph/Agno DONOR_ONLY |
| document/privacy/source | existing AIOS boundaries + Docling/ClamAV | Presidio/urlwatch bounded pilots | EU DSS HOLD_WITH_TRIGGER |
| human-agent interaction | current AIOS Cockpit | CopilotKit / AG-UI post-L M | Storybook HOLD_WITH_TRIGGER |

The active status source for exact per-candidate triggers is `docs/TECHNOLOGY_RADAR_V1_3_8.md`.

## 4. External candidates most likely to be confused with missing capability

| Candidate | Current truth |
|---|---|
| Langfuse | HOLD_WITH_TRIGGER; OpenTelemetry is incumbent and Phoenix is the selected platform challenger |
| OpenFGA | relationship-authorization R3 incumbent/challenger baseline only; native AIOS authorization remains authoritative |
| SpiceDB | relationship-authorization challenger to OpenFGA; research branch evidence does not grant authority |
| OPA/Rego | contextual-policy R3 incumbent benchmark behind an AIOS-owned boundary only |
| Cedar | contextual-policy challenger to OPA; typed/verification research does not grant policy authority |
| CopilotKit / AG-UI | post-L M interaction challenger; not installed/adopted on canonical V12 |
| Munder Difflin | strategic donor programme only; no canonical V12 runtime package; donor state cannot become organization truth |
| Garak | bounded live-model adversarial challenger; operational Red Team authority not claimed |
| Microsoft PyRIT | HOLD_WITH_TRIGGER for multi-turn Red Team orchestration |
| DeepEval / Ragas | HOLD_WITH_TRIGGER; do not add while Promptfoo + Inspect/current evidence evaluation covers the seam |
| Hypothesis | bounded test-only property pilot implemented |
| mutmut | HOLD_WITH_TRIGGER for Linux/CI; first-party mutation gate is current baseline |
| Semgrep / CodeQL | selected SAST incumbent/challenger pair |
| Trivy / OSV-Scanner | selected dependency/container incumbent/challenger pair |
| Gitleaks / TruffleHog | selected secret-scanning incumbent/challenger pair |
| Microsandbox / E2B | selected future sandbox incumbent/challenger pair; no execution authority |
| Mem0 | continuity-memory challenger only; MEMORY != EVIDENCE |
| Temporal | trigger-bound durable-workflow challenger |
| LLMLingua-2 | selected bounded compression pilot; protected R3–R5 context remains zero-semantic-compression by default |
| Presidio | queued privacy pilot |
| urlwatch | queued source-monitoring pilot |
| EU DSS | HOLD_WITH_TRIGGER for material document-signature/trust requirement |

## 5. R3 research-branch recoverability truth

Verified separate research branches:

```text
radar/r3-authority  acd917670630abdfebe20f3f687a310f67d22b3f
radar/r3-security   d908a8c7ccde463ae0dec097211562e7ef8e86ca
radar/r3-interop    aad377e401b10a95b11440442831290c5c60a9f2
```

The interop branch was previously local-only and is now preserved on origin. This changes recoverability only:

```text
remote branch preservation != V12 merge
remote branch preservation != production adoption
remote branch preservation != L acceptance
```

## 6. Cybersecurity / Red Team truth

The governed cybersecurity donor and AIOS Red Team / Adversarial Security Lab programme has already started at architecture/Radar level. Do not redesign it from zero.

```text
Cybersecurity Skill Registry runtime       NOT YET CLAIMED
operational offensive Red Team agents      NOT YET CLAIMED
arbitrary production-target authority      REJECTED
Promptfoo                                  existing bounded evaluation pilot
Garak/PyRIT/DeepTeam/FuzzyAI               research candidates only
Microsandbox-backed lab                     future candidate only
```

`SKILL KNOWLEDGE != EXECUTION AUTHORITY`.

## 7. Mandatory anti-duplication checklist

```text
[ ] What exact product problem is being solved now?
[ ] Does first-party AIOS already solve the capability natively?
[ ] Is there already an AIOS-owned port/adapter?
[ ] Is the named technology actually present in dependencies/imports/config?
[ ] Is there an existing pilot/test/receipt/commit?
[ ] Does ROADMAP permit implementation now?
[ ] Would adoption create a second truth/authority/control plane?
[ ] What is the bounded acceptance test?
[ ] What is explicitly NOT being claimed?
[ ] Have ROADMAP / CHANGELOG / this ledger been reconciled?
```

## 8. Radar-completion interpretation

Technology Radar V1.3.8 is the **active consolidated current-horizon Radar**. V1.3.7 remains the historical broad inventory; V1.3.8 applies the scatter audit so duplicate candidates are trigger-bound rather than permanently active research.

It does not mean all candidates should be installed.

```text
Technology Radar V1.3.8                  ACTIVE / CONSOLIDATED
scatter-audit application                 COMPLETE
runtime adoption caused by V1.3.8        NONE
Munder runtime adoption                  NONE ON CANONICAL V12
external mutation engine adoption        NONE
L                                        IMPLEMENTED / ACCEPTANCE PENDING
M                                        NOT STARTED
```

ROADMAP remains the implementation scheduler.

CI administration note: GitHub policy jobs that run `check_diff_hygiene.py` now require full authenticated checkout history so transition baseline `8624d7f...` is present. This is CI proof plumbing only and changes no technology adoption/runtime classification.

Restored full-history CI then exposed 22 post-baseline trailing-space violations across five documentation files. V12.51 removes only that whitespace; technology/adoption truth is unchanged.

Local-artifact administration note: V12.52 classifies only `.local/gmai-dev-cache/`, `.local/gmai-dev-temp/` and existing `.local/professional-review/` as narrow ignored local roots. Recovery/history buckets are to be archived outside the worktree rather than hidden. This changes no technology adoption/runtime truth.

V12.53 extends the preservation list after the next local run exposed `.local/archives/`, `.local/discovery/`, and `.local/13.16.6-owner-inbox-discovery.txt`. Canonical V12 has no references to those paths; they are local recovery/history material, not runtime/adoption state.

Those three items were subsequently archived outside the worktree, and V12.53 fail-fast local acceptance passed at exact head `b2cc754...`. This closes local administration/hygiene only and changes no technology adoption/runtime classification.

Administration note: V12.47 PROJECT_STATE/recovery exact-head proof passed at `80deef2...`. The later V12.48 attempt at `b079428...` failed its clean-worktree gate because additional untracked `.local/` state became visible after removing a broad operator-local exclude. No technology/adoption classification changes from either administration event. This did not change any technology adoption state. The operator-local `.git/info/exclude` broad `/.local/` entry is local hygiene only and is not an AIOS adoption/runtime fact.