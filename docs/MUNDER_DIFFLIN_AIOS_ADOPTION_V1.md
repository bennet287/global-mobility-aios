# Munder Difflin v0.4.4 → Global Mobility AIOS Adoption Programme V1

**Date:** 2026-08-22
**Status:** Strategic donor / controlled adoption programme
**Donor baseline:** Munder Difflin `v0.4.4`
**AIOS implementation line:** `roadmap/global-mobility-aios-v12`
**Frontend design programme:** `AIOS_FRONTEND_DESIGN_UX_PROGRAMME_V1.md`

## 1. Purpose

Munder Difflin v0.4.4 is a frozen upstream donor for the Global Mobility AIOS Organization Fabric. It is not the governing architecture, canonical truth system, domain model, authority model or final product-design system.

The objective is maximum useful feature adoption without inheriting Munder's architectural or visual ceilings.

> **External capability may be adopted aggressively. AIOS meaning and authority remain sovereign.**

## 2. Adoption doctrine

Every donor subsystem must be classified before implementation:

```text
DIRECT REUSE
PORT
ADAPT
REIMPLEMENT
REJECT
```

Each adoption record should identify:

- donor source/module;
- donor capability;
- AIOS destination;
- classification;
- retained behavior;
- AIOS-specific additions;
- rejected assumptions;
- security/authority implications;
- persistence model;
- acceptance tests;
- rollback/replacement plan.

## 3. High-value donor capabilities

| Munder capability | AIOS destination | Decision |
|---|---|---|
| Hive messaging | Organizational Communication Fabric | ADAPT heavily |
| message routing | Communication Fabric | ADAPT heavily |
| agent roster/runtime identity | Persistent Employee Runtime | map to OrganizationPosition |
| GOD orchestration | Executive Coordination | REIMPLEMENT as AI CEO hierarchy |
| Skills | Capability Registry | ADAPT |
| provider/runtime abstraction | Agent Runtime Fabric | ADAPT |
| PTY/CLI execution | CLI Agent Runtime | ADOPT as optional runtime |
| task coordination | Mission/WorkItem mechanics | ADAPT |
| circuit breaker | Organizational Immune System | ADAPT |
| triggers/schedules | Event Nervous System | ADAPT |
| heartbeat/presence | Employee Presence/Health | ADAPT |
| webhooks | Integration Plane | ADAPT |
| Slack integration | Communication Connector | ADAPT where useful |
| memory mechanics | Agent/Organizational Memory | ADAPT below trust boundary |
| shared blackboard | Mission Rooms | REIMPLEMENT/ADAPT |
| transcripts | Transparency + Flight Recorder | ADAPT |
| token/cost telemetry | AI Economics | ADAPT |
| tool waterfall | Decision/Execution Timeline | REIMPLEMENT |
| memory graph | Organization/Decision Graph | REIMPLEMENT |
| Git worktrees | Engineering Workforce | ADOPT |
| IDE/terminal | Engineering Workspace | ADAPT |
| voice/realtime | Executive Interaction | future ADAPT |
| live office scene mechanics | Living Organization Runtime | selective ADAPT |
| pixel-art presentation | Living Organization UI | REIMPLEMENT completely |
| SQLite/file state as authority | canonical state | REJECT |
| GOD implicit unlimited authority | authority model | REJECT |
| direct agent mutation of authoritative state | execution model | REJECT |

## 4. AIOS boundaries Munder may not own

Munder-derived code must not become authoritative for:

- Human Owner / Board supremacy;
- OrganizationPosition identity;
- authority or delegation;
- autonomy;
- risk classification;
- Evidence status;
- SourceSnapshot meaning;
- VerifiedRule status;
- legal/domain interpretation;
- canonical Case state;
- Mission/WorkItem meaning;
- OrganizationActivity semantics;
- Command Gateway decisions;
- Board-reserved actions;
- professional/human-review requirements;
- final business outcomes;
- AIOS information architecture, design tokens or final visual identity.

## 5. Runtime relationship

```text
Persistent AIOS Employee
        ↓
Context Broker
        ↓
AIOS Agent Runtime Port
        ↓
Munder-derived / other adapter
        ↓
Hosted model / CLI agent / local model
        ↓
Tool use / reasoning
        ↓
Typed AIOS intent
        ↓
Governance / Immune System
        ↓
Command Gateway
        ↓
Canonical AIOS state
```

## 6. Communication relationship

Munder Hive concepts provide transport/mechanics. AIOS owns semantics.

Agent communication may include REQUEST, QUERY, INFORM, PROPOSE, CHALLENGE, AGREE, DISAGREE, REFUSE, DELEGATE, REVIEW, WARN, ESCALATE, ACKNOWLEDGE and COMPLETE.

Permanent rule:

```text
conversation != authority
message != decision
provider transcript != canonical OrganizationActivity automatically
```

## 7. Skills relationship

```text
Munder-style Skill
      ↓
AIOS Technical Capability
      ↓
Capability Registry
      ↓
Authority
      ↓
Earned Autonomy
      ↓
Risk controls
      ↓
Execution
```

Installing a Skill never grants consequential authority automatically.

## 8. Circuit-breaker relationship

Munder's circuit-breaker concepts should be integrated into the broader Organizational Immune System.

Target intervention progression:

```text
HEALTHY
   ↓
STEER
   ↓
CONSTRAIN
   ↓
SUSPEND
   ↓
STOP
```

Signals may include loops, no-progress behavior, errors, excessive retries, abnormal tool use, budget anomalies, provider failures, latency anomalies and repeated governance failures.

## 9. Memory relationship

Munder memory capabilities may strengthen working, agent and organizational memory, but never bypass the AIOS trust ladder.

> **Memory provides continuity. Evidence provides authority.**

## 10. Event relationship

Munder triggers, scheduling, heartbeats and webhooks should feed the AIOS Event Nervous System rather than create a parallel workflow truth model.

```text
Event
 ↓
Trigger
 ↓
Policy
 ↓
Mission / WorkItem
 ↓
Employee / Squad
```

## 11. Telemetry relationship

Munder runtime telemetry, transcripts, token/cost signals and tool activity should feed:

- Transparency Layer;
- Organizational Flight Recorder;
- AI Economics;
- Immune System;
- AutonomyEvidenceProfile;
- replay/shadow evaluation;
- organizational learning.

Provider-native logs remain technical evidence, not automatically canonical OrganizationActivity.

## 12. Living Organization + frontend relationship

Munder's 2D office is a conceptual/runtime donor, not the target visual system.

AIOS target:

> **Premium modern 2D/2.5D Living Organization with modern cartoon AI employees and semantic animation derived from real runtime state.**

Retain or study:

- scene/event synchronization;
- presence state and heartbeat mechanics;
- character positioning;
- collaboration grouping;
- live message/tool signals;
- runtime-driven animation;
- transcript and execution-timeline concepts.

Replace completely:

- pixel-art visual language;
- retro office presentation;
- random wandering;
- game-like decorative busywork;
- GOD-character metaphors.

Frontend ownership is now explicit:

```text
Munder donor mechanics
        ↓ selective adaptation
canonical AIOS organization/read-model state
        ↓
AIOS interaction semantics
        ↓
Penpot + AIOS Design System
        ↓
repository-owned React components / Storybook workbench
        ↓
Next.js Cockpit / Board Room / Operations / My Mobility
```

Munder may influence mechanics; it does not define the AIOS product identity. Meaningful animation must be derived from real persisted/runtime state and may never manufacture apparent organizational activity.

## 13. Engineering-workforce relationship

Munder's PTY/CLI/worktree/IDE capabilities are particularly useful for internal AIOS Engineering employees. They should be scoped to Engineering Missions, tool permissions and isolated workspaces rather than exposed as unrestricted organization-wide execution.

## 14. Proposed implementation slices

```text
M0   frozen donor provenance
M1   runtime/provider abstraction
M2   communication/router
M3   persistent employee runtime binding
M4   Mission/WorkItem coordination
M5   Dynamic Squads
M6   presence + heartbeat
M7   Skills / Capability Registry
M8   relationships
M9   circuit breaker integration
M10  transcripts + telemetry
M11  tool/action lineage
M12  AI Economics inputs
M13  triggers/scheduling
M14  webhooks/integration broker
M15  memory mechanics
M16  Organization/Decision Graph
M17  Living Organization runtime
M18  modern character system via AIOS Design System
M19  executive voice/realtime
M20  engineering worktrees/IDE
M21  optional desktop runtime
```

These slices are subordinate to the main V1.3 programme. Governance and transparency dependencies must be satisfied before powerful external execution is enabled. M17/M18 are additionally subordinate to real L read-model state and the frontend UX programme.

## 15. Acceptance requirements

Every adoption slice should demonstrate, as applicable:

- domain-semantic sovereignty;
- Board authority preservation;
- tenant isolation;
- sensitivity handling;
- typed AIOS contracts;
- no direct canonical mutation bypass;
- capability/authority separation;
- risk/autonomy enforcement;
- traceability;
- deterministic failure behavior;
- idempotency/concurrency safety;
- resource bounds;
- rollback/replacement path;
- focused tests;
- full regression where required;
- repository-policy compliance;
- truthful acceptance evidence.

Frontend-facing donor slices must additionally demonstrate:

- no fake live organization state;
- canonical read-model fidelity;
- accessibility/responsive behavior where applicable;
- AIOS design-token/component ownership;
- no donor visual identity leakage into the final product by accident.

## 16. Final adoption rule

> **Use Munder Difflin aggressively where it accelerates AIOS runtime capability, but never let donor implementation replace AIOS constitutional authority, Evidence, governance, canonical truth, Global Mobility domain semantics or final product-design authority.**