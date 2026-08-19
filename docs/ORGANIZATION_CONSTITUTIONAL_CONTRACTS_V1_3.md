# Global Mobility AIOS — Organization Constitutional Contracts V1.3

**Status:** V1.3-A runtime-facing contract checkpoint  
**Branch:** `roadmap/global-mobility-aios-v12`  
**Architecture:** `HUMAN_LIKE_AGENT_ORGANIZATION_ARCHITECTURE_V1_3.md`  
**Runtime behavior changed by this document alone:** none

## 1. Purpose

V1.3-A converts the owner-approved constitutional vocabulary from architecture prose into stable runtime-facing contracts before the V1.3-B Governance Kernel begins.

The goal is not to build the Command Gateway, Decision Readiness engine, Organizational Immune System, or earned-autonomy runtime yet. The goal is to ensure those systems share one deterministic vocabulary instead of inventing incompatible strings and booleans independently.

The corresponding Python contract module is:

```text
apps/api/app/core/organization_constitution.py
```

Focused contract tests are:

```text
apps/api/tests/test_organization_constitution.py
```

## 2. Human Board supremacy

Permanent invariant:

> **The Human Owner / Board is the supreme authority of Global Mobility AIOS. No agent, AI executive, model, runtime, tool, policy engine, or delegated authority may supersede it.**

Operational authority may be delegated downward, but constitutional authority remains human-owned.

The Board should govern mainly through constitution, strategy, reserved powers, autonomy ceilings, policy floors, executive authority, emergency controls, and exception handling rather than routine operational approval.

## 3. Board Transparency

Permanent invariant:

> **Operational autonomy must never create organizational opacity.**

Board transparency is an inspection right, not an approval requirement.

All organizational activity classes are Board-inspectable. Retention intensity differs by materiality:

| Activity class | Board inspectable | Durable record | Full lineage | May compact under policy |
|---|---:|---:|---:|---:|
| CONVERSATIONAL | yes | no by default | no | yes |
| COLLABORATIVE | yes | yes | no | yes |
| OPERATIONAL | yes | yes | no | yes |
| MATERIAL | yes | yes | yes | no |
| AUTHORITY | yes | yes | yes | no |

`requires_durable_record = false` for conversational activity does not mean the Board loses visibility while the activity exists. It means low-value raw conversation may be summarized/compacted after the applicable retention window rather than being retained forever as regulatory-grade history.

Material and authority-bearing activity must preserve durable lineage.

Sensitivity controls remain mandatory. Transparency does not authorize secret leakage or unlawful disclosure.

## 4. Capability, authority, autonomy, and risk remain separate

```text
Capability = what the runtime can technically do
Authority  = what AIOS permits
Autonomy   = how independently authority may be exercised
Risk       = consequence of the particular action
```

Permanent rule:

```text
CAN DO ≠ MAY DO
```

## 5. Autonomy levels A0–A5

| Level | Frozen meaning |
|---|---|
| A0 | Prohibited |
| A1 | Human executes |
| A2 | AI prepares; approval required |
| A3 | Autonomous with mandatory review |
| A4 | Autonomous with monitoring and valid recovery controls |
| A5 | Fully autonomous bounded operation |

Autonomy is capability/context-specific. This contract does not create one global autonomy level per agent.

## 6. Risk tiers R0–R5

| Tier | Frozen direction |
|---|---|
| R0 | non-material cognition such as summarization or brainstorming |
| R1 | routine internal operation with inexpensive deterministic checks |
| R2 | client-facing preparation requiring Evidence validation |
| R3 | material recommendation/eligibility requiring independent verification |
| R4 | certification/regulatory publication requiring independent verification, fresh-source validation, and appropriate authority |
| R5 | government submission or critical reserved action requiring full preparation and Human/Board gate |

Risk belongs to the action, not the employee.

## 7. HumanReviewReason

The runtime-facing review reasons are frozen as:

```text
UNCERTAINTY
CONTRADICTION
INSUFFICIENT_EVIDENCE
OUTSIDE_AUTHORITY
POLICY_REQUIRED
LEGAL_REQUIRED
BOARD_RESERVED
ANOMALY
EXCEPTION
```

This distinction is essential because a human may be involved for uncertainty, legal requirements, policy, or reserved authority even when AI confidence is high.

## 8. Consequence and recovery classes

The frozen recovery vocabulary is:

```text
REVERSIBLE
COMPENSATABLE
IRREVERSIBLE
APPEND_ONLY_CORRECTION
```

Recovery belongs to consequential business commands, not arbitrary database rows.

Examples:

- WorkItem reassignment may be `REVERSIBLE`.
- An incorrect external message may be `COMPENSATABLE` through a correction.
- A government submission may be `IRREVERSIBLE` and therefore needs stronger pre-execution controls.
- Evidence certification may later require `APPEND_ONLY_CORRECTION` so historical truth is preserved.

## 9. Reserved authority classes

The constitutional contract identifies Board-owned authority domains:

```text
CONSTITUTION
STRATEGIC_DIRECTION
AUTONOMY_CEILING
MAJOR_POLICY
EXECUTIVE_APPOINTMENT
EMERGENCY_CONTROL
BOARD_RESERVED_EXTERNAL_ACTION
```

These classes describe authority categories. Detailed jurisdiction/workflow policy in later phases will map specific actions to the appropriate class.

## 10. Initial Materiality Registry

The first frozen action vocabulary is intentionally small and aligned to the V1.3 roadmap examples:

| Action type | Material | Default risk | Board reserved |
|---|---:|---:|---:|
| `official_source.search` | no | R0 | no |
| `document.summary` | no | R0 | no |
| `internal.note` | no | R0 | no |
| `work_item.assignment` | yes | R1 | no |
| `evidence.candidate` | yes | R2 | no |
| `eligibility.transition` | yes | R3 | no |
| `evidence.certification` | yes | R4 | no by this base contract |
| `verified_rule.publication` | yes | R4 | no by this base contract |
| `external_communication.consequential` | yes | R3 | no by this base contract |
| `government.submission` | yes | R5 | yes |

The registry is deliberately immutable at runtime in this phase.

Later policy layers may further restrict an action, but they may not silently downgrade the constitutional minimum risk or remove an explicit Board-reserved gate without a governed constitutional/policy change.

## 11. Scores route; gates authorize

Permanent authorization invariant:

> **Scores route decisions; deterministic gates authorize decisions.**

Decision Readiness is not implemented in V1.3-A. This contract simply ensures later runtime code cannot treat a readiness scalar as constitutional permission.

## 12. Relationship to existing runtime

Existing runtime authorization remains in place, including route/role policy and existing organization-governance request schemas.

For example, current organization work creation still uses fields such as:

```text
risk_level
requires_board_approval
```

V1.3-A does **not** rewrite those existing APIs yet. Doing so here could create unnecessary compatibility risk.

V1.3-B will introduce the Minimal Governance Kernel and provide the controlled integration point where existing loose runtime fields can begin mapping into the typed constitutional vocabulary.

## 13. What V1.3-A intentionally does not implement

This slice does not implement:

- MaterialAction persistence;
- Command Gateway execution;
- capability-authority persistence;
- Decision Readiness calculation;
- independent verification;
- dynamic autonomy promotion/demotion;
- Organizational Immune System signals;
- agent memory/context runtime;
- Transparency indexing;
- Board search/explorer UI;
- database migrations;
- external runtime integration.

Those remain later roadmap phases.

## 14. Acceptance contract

V1.3-A is ready to be marked PASS only when:

1. the typed contract module imports successfully;
2. focused contract tests pass;
3. A0–A5 and R0–R5 are complete and stable;
4. HumanReviewReason and consequence classes match the canonical architecture;
5. every declared MaterialActionType has a registry rule;
6. government submission is R5 and Board-reserved;
7. all activity classes preserve Board inspectability;
8. MATERIAL/AUTHORITY activity requires durable full lineage;
9. registries cannot be mutated accidentally at runtime;
10. `ROADMAP.md` and `CHANGELOG.md` truthfully record the delivery state;
11. no runtime/database/CI claims are made without evidence.

## 15. Next phase

After V1.3-A acceptance, proceed to:

> **V1.3-B — Minimal Governance Kernel**

The first kernel should remain small: actor identity, capability authority, expected version, idempotency, MaterialAction envelope, basic deterministic policy evaluation, Command Gateway foundation, and OrganizationActivity trace identity.
