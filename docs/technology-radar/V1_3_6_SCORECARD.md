# Technology Radar V1.3.6 — Scorecard

**Date:** 2026-08-30
**Status:** PROVISIONAL R2 DOCUMENTARY SCORES / NO ADOPTION DECISION
**Method:** `V1_3_6_RESEARCH_METHOD.md`

## 1. Weighted scoring model

| Dimension | Weight | Evidence expected |
|---|---:|---|
| AIOS architectural fit | 20 | direct fit to a demonstrated AIOS boundary/problem |
| sovereignty / replaceability | 15 | adapter viability; no external canonical truth requirement |
| security | 15 | fail-closed controls, tenant/delegation/secret posture |
| authority-model compatibility | 10 | capability and authority remain separable |
| evidence-model compatibility | 10 | no memory/telemetry/finding-to-truth shortcut |
| enterprise maturity | 8 | governance, releases, operations and support posture |
| interoperability | 7 | standard APIs/protocols and ecosystem integration |
| self-hosting / data control | 5 | deployability and data-boundary control |
| operational complexity | 4 | higher score means lower justified complexity |
| licensing | 3 | clear and compatible research/adoption posture |
| cost | 3 | predictable and proportionate ownership cost |
| **Total** | **100** | hard blockers still override score |

Scores are intentionally conservative where R3 evidence is absent. A score is not a selection or adoption claim.

## 2. Hard blockers

Any candidate is `REJECT` or `HOLD` for the proposed shape when it requires:

- provider/framework state to become canonical AIOS organization truth;
- skill/capability discovery to grant authority;
- bypass of Command Gateway for material or external actions;
- memory, telemetry or evaluator findings to become Evidence/VerifiedRule automatically;
- secrets in prompt, ContextBundle, memory, Activity or repository state;
- unbounded production/security testing;
- cross-tenant authorization ambiguity or fail-open behavior;
- an incompatible license or unresolved data-residency obligation.

## 3. Provisional R2 scores

| Candidate | Score | State | Principal conclusion |
|---|---:|---|---|
| OpenFGA | 88 | ASSESS / R2 | strongest current relationship/delegation candidate; requires canonical-data synchronization and contextual risk boundary |
| OPA | 86 | ASSESS / R2 | strongest general policy decision candidate; relationship modeling and policy/data lifecycle need care |
| Cedar | 82 | RESEARCH / R2 | clear principal/action/resource/context model; narrower ecosystem and operational fit need lab evidence |
| SpiceDB | 84 | ASSESS / R2 | strong Zanzibar-style relationship graph and consistency controls; introduces a second authorization datastore |
| MCP 2026-07-28 | 87 | ASSESS / R2 | strategically relevant tool/data protocol; requires an AIOS gateway, catalog trust and per-call authorization |
| A2A 1.0 | 82 | RESEARCH / R2 | credible agent discovery/task interoperability; Agent Card skills are untrusted capability claims |
| Inspect AI | 87 | ASSESS / R2 | best broad evaluation-lab foundation candidate; must remain outside canonical product truth |
| Promptfoo | 86 | TRIAL-ELIGIBLE / R2 | strongest current application/MCP red-team candidate; findings require AIOS reproduction and review |
| garak | 78 | RESEARCH / R2 | useful independent model/system scanner; overlaps with Promptfoo and is less AIOS-workflow-specific |

## 4. Authorization comparison

| Dimension | OpenFGA | OPA | Cedar | SpiceDB |
|---|---:|---:|---:|---:|
| AIOS architectural fit /20 | 19 | 18 | 16 | 18 |
| sovereignty /15 | 13 | 14 | 13 | 12 |
| security /15 | 13 | 13 | 13 | 13 |
| authority compatibility /10 | 10 | 9 | 9 | 10 |
| evidence compatibility /10 | 9 | 9 | 9 | 9 |
| enterprise maturity /8 | 7 | 8 | 6 | 7 |
| interoperability /7 | 6 | 6 | 5 | 6 |
| self-host/data control /5 | 5 | 5 | 5 | 5 |
| operational simplicity /4 | 2 | 2 | 3 | 1 |
| licensing /3 | 3 | 3 | 3 | 3 |
| cost /3 | 1 | 2 | 0 | 0 |
| **Total** | **88** | **86** | **82** | **84** |

R2 conclusion: do not compose two policy engines by default. An isolated authorization lab should compare OpenFGA and OPA first against the exact same five-action employee fixture. Cedar and SpiceDB remain credible challengers where embedded policy or large relationship graphs prove necessary.

## 5. Interoperability comparison

| Question | MCP | A2A |
|---|---|---|
| primary boundary | agent/runtime to tools, resources and prompts | independent agent systems and durable tasks/messages/artifacts |
| AIOS entry point | governed `McpGatewayPort` | governed `A2AGatewayPort` |
| discovery meaning | untrusted tool/resource catalog | untrusted Agent Card/capability/skill claim |
| authority decision | AIOS per invocation | AIOS before WorkItem/task creation and at each material transition |
| canonical state | AIOS WorkItem/ActionOutput/Activity | AIOS WorkItem/ActionOutput/Activity |
| main R3 risk | tool poisoning/confused deputy/credential scope | agent impersonation/skill inflation/task-state confusion |

MCP is the earlier practical assessment because AIOS has nearer-term external tool/data needs. A2A remains strategically important but should not precede a concrete remote-agent use case.

## 6. Security/evaluation comparison

| Question | Inspect AI | Promptfoo | garak |
|---|---|---|---|
| best fit | structured evaluation laboratory | application/agent/MCP adversarial testing | independent model/system scanning |
| strengths | datasets, agents, tools, scorers, sandboxes, approvals, MCP | generated attack suites, application targets, agent/MCP guides | broad probe/detector catalog and REST/model generators |
| main limitation | framework integration and lab isolation burden | findings can be heuristic and target configuration is security-sensitive | overlap, probe volume and weaker business-workflow semantics |
| proposed role | evaluation harness | primary Red Team attack generator | independent challenger/scanner |
| current decision | ASSESS | TRIAL-ELIGIBLE | RESEARCH |

R2 conclusion: use Inspect AI as the leading evaluation-lab architecture candidate, retain Promptfoo as the leading application red-team candidate, and keep garak as an independent challenger. Do not adopt all three before an R3 overlap/cost comparison.

## 7. Required R3 evidence

No score may advance a candidate without:

- exact pinned build/container and dependency inventory;
- synthetic AIOS fixture and expected decisions;
- positive and negative contract tests;
- tenant, revocation, replay and failure-mode tests;
- secrets/network isolation declaration;
- latency and operational-complexity measurements;
- retained result artifact hashes;
- owner-reviewed decision record;
- explicit cleanup and replacement path.

The first authorized R3 recommendation is an isolated OpenFGA-vs-OPA decision lab. It is a recommendation only; V1.3.6 does not create or run that lab.
