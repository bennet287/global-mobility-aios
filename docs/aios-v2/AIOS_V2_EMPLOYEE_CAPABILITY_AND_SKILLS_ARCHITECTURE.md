# AIOS V2 Employee Capability & Skills Architecture

**Status:** ACTIVE PROGRAM DIRECTION
**Applies to:** AI employees, departments, Living Organization, Living HQ, orchestration, automation, tools, integrations, memory, evidence, and future skill discovery/execution.

## 1. Purpose

AIOS employees must not be LLMs with character skins. A visible employee represents a persistent organizational actor with a defined position, department, capability profile, tools, permissions, memory scope, objectives, work, evidence, and authority boundary.

The target model is:

`Department → Position → Employee → Skills → Tools → Permissions → Memory → Objectives → Runtime → Work → Evidence → Outcome`

This architecture connects the Living HQ presentation to the real capability and work system. The organization causes the animation; animation never causes the organization.

## 2. Department model

AIOS may contain specialist departments such as Executive/CEO, Technical, Marketing, Operations, Regulatory/Legal, Finance, People/HR, Research, and future organization-specific departments. Department membership is not merely visual grouping: it defines reporting context, capability families, tool eligibility, operating objectives, collaboration relationships, and escalation paths.

Example capability families:

| Department | Representative capabilities |
| --- | --- |
| Executive / CEO | strategy, delegation, synthesis, executive reporting, decision analysis |
| Technical | architecture, frontend, backend, testing, debugging, security, GitHub, deployment |
| Marketing | market research, positioning, SEO, campaigns, content, analytics, competitive intelligence |
| Operations | process design, automation, planning, SOPs, work coordination |
| Regulatory / Legal | jurisdiction research, compliance analysis, evidence review, regulatory reasoning |
| Finance | budgeting, forecasting, financial analysis, reporting |
| People / HR | recruiting workflows, candidate evaluation, onboarding, workforce processes |
| Research | web research, source verification, synthesis, structured investigation |

Departments and skills must remain extensible rather than hard-coded to this initial list.

## 3. Persistent AI employee contract

A persistent AI employee should be modeled as a durable organizational actor with at least:

- stable identity and presentation identity;
- department and position;
- reporting relationship;
- seniority/role metadata where meaningful;
- approved/available skills and skill versions;
- eligible tools and integrations;
- effective permissions and authority boundaries;
- scoped organizational/project memory;
- objectives and recurring responsibilities;
- execution/runtime capabilities where applicable;
- current and queued work;
- blockers and dependencies;
- evidence/work products;
- provenance and execution history;
- supported collaboration/handoff relationships;
- canonical state such as working, blocked, awaiting owner, queued, completed, or unknown.

The UI may never infer unsupported physical presence, conversation, collaboration, urgency, completion, authority, or work state from the character presentation.

## 4. Skills are first-class organizational capabilities

A skill is a reusable capability/procedure that can help an employee perform a class of work. Skills may include instructions, workflows, tool usage patterns, validation steps, domain conventions, examples, or reusable execution logic.

Skills must have durable identity. The registry should be able to record:

- skill ID and human-readable name;
- capability family/tags;
- description and intended use;
- source/provenance;
- version/content fingerprint;
- compatible roles/departments;
- tool/runtime requirements;
- permission requirements;
- inputs/outputs where defined;
- evidence expectations;
- validation/test status;
- quality/performance history;
- active/deprecated/superseded state;
- learned/generated versus imported origin.

## 5. External skill discovery

External ecosystems such as skills.sh are discovery sources, not AIOS authority. AIOS may discover reusable community skills and capability patterns from them, but external content never overrides canonical truth, the AIOS Design Constitution, Master Plan, authority contracts, security boundaries, or organizational policy.

External skill ingestion should preserve source, license information when available, version/fingerprint, dependencies, tool requirements, and review/compatibility metadata. Discovery does not itself grant an employee new authority or credentials.

Reference boundary remains:

`canonical truth → AIOS authority/policy → AIOS capability registry → external skill/reference → implementation convenience`

## 6. Automatic organizational learning — permanent direction

Repeated successful work should automatically become reusable organizational capability.

This is intentionally an **automatic learning loop**, not a manual approval workflow.

Target lifecycle:

`work executions → recurrence detection → successful-pattern extraction → generalized procedure → automatically generated skill → validation → versioned registry entry → automatic eligibility/reuse → ongoing evaluation/versioning`

AIOS should detect when substantially similar tasks/workflows recur and extract the stable procedure, including useful sequencing, tool patterns, checks, recovery behavior, evidence requirements, and domain conventions. It should generalize away task-specific secrets, identifiers, transient values, and irrelevant context.

The resulting learned skill should be created automatically and become reusable automatically after machine validation appropriate to its capability/risk class. Human approval is not the default creation gate.

### 6.1 Automatic does not mean unbounded

Automatic learning must not silently expand authority. A learned skill inherits the effective authority/permission ceiling of the employee/role and execution context in which it is used. Learning a procedure cannot grant credentials, destructive permissions, legal/financial decision authority, owner/board authority, or access to data/tools the employee otherwise lacks.

The automatic system must therefore separate:

- **capability acquisition** — may be automatic;
- **authority acquisition** — never implied by learning a skill;
- **credential/tool access** — remains governed by existing permission systems;
- **canonical decisions/outcomes** — remain subject to their existing authority contracts.

This preserves automatic organizational learning without converting skill generation into an authority bypass.

### 6.2 Recurrence detection

The learning system should use semantic similarity and workflow structure rather than exact prompt matching. Candidate recurrence signals may include:

- repeated objective/task family;
- repeated sequence of operations/tools;
- repeated input/output schema;
- repeated validation/evidence pattern;
- repeated recovery from the same failure mode;
- repeated cross-department handoff pattern;
- repeated successful result under materially similar constraints.

The system should avoid creating a new skill for every minor variation. Prefer stable, composable procedures.

### 6.3 Automatic extraction

Extraction should identify:

1. goal and applicability conditions;
2. required inputs/context;
3. ordered procedure;
4. tool/integration requirements;
5. authority/permission assumptions;
6. expected outputs/artifacts;
7. validation and acceptance checks;
8. evidence/provenance requirements;
9. failure/retry/recovery behavior;
10. known limits and non-applicable conditions.

Secrets, personal data, one-off IDs, temporary URLs/tokens, incidental conversation text, and unrelated project-specific values must not be baked into reusable skill definitions.

### 6.4 Machine validation and risk classes

Automatic reuse should be proportional to risk. Validation may include schema checks, deterministic/unit tests, sandbox execution, replay against prior successful examples, permission analysis, regression checks, and output/evidence verification.

Low-risk procedural skills can become reusable after automated validation. Higher-risk skills may still be automatically learned and registered, but execution remains constrained by the pre-existing authority and action confirmation rules of the underlying operation. The skill itself must never weaken those rules.

### 6.5 Continuous improvement

Learned skills should evolve from evidence. AIOS should track success/failure, retries, cost/latency where relevant, validation outcomes, employee/department usage, supersession, and regressions. Materially improved procedures create a new version rather than silently rewriting historical provenance.

Poor or failing skills may be automatically downgraded, quarantined from automatic selection, or superseded while preserving history.

## 7. Skill selection and assignment

Work routing should consider more than department labels. Employee selection may use:

- required capability/skill match;
- department/role suitability;
- authority and permissions;
- tool availability;
- current workload/state;
- dependency/reporting context;
- prior evidence-backed performance;
- cost/latency constraints where relevant;
- memory/context locality;
- required collaboration or escalation.

This enables work to be assigned because an employee is actually capable and authorized, not merely because its character is labeled with a role.

## 8. Tools, integrations, and runtime

Skills describe capability; tools provide action surfaces. AIOS should support department/role-specific integrations and execution environments while keeping them explicit.

Potential categories include GitHub/code tooling, browser/research, communication systems, files/artifacts, structured databases, calendars, domain APIs, terminals/sandboxes, deployment systems, and future plugins/connectors.

An employee's effective action set is the intersection of skill requirements, available tools, credentials, organizational permissions, current work scope, and authority policy.

## 9. Memory and institutional knowledge

Memory and skills are distinct:

- **memory** retains relevant context/facts/history;
- **skill** encodes a reusable way of accomplishing work;
- **evidence** records what actually happened and supports claims/outcomes.

Repeated work should preferentially become a skill when the reusable value is procedural. This prevents institutional capability from degenerating into an ever-growing pile of conversational memory.

## 10. Missions and cross-department delegation

AIOS should support organization-level missions decomposed across specialist departments. Example:

`CEO mission → Marketing research + Regulatory constraints + Finance model + Operations feasibility → evidence-backed departmental results → executive synthesis → owner/board decision when authority requires it`

Cross-department handoffs must correspond to supported work relationships. Living HQ animation may visualize a handoff only when the canonical organization supports that relationship/state.

## 11. Living HQ integration

The Living HQ should become the spatial representation of this capability graph, not decorative office wallpaper.

At useful zoom/detail levels the experience may expose:

- department zones and organizational relationships;
- recognizable employees and role identity;
- supported current work state;
- capability/skill profile on employee inspection;
- current mission/work item;
- tools/integrations relevant to current work;
- reporting relationship;
- evidence/recent work products;
- authority/permission posture where useful;
- supported handoffs/collaboration/escalations;
- blockers/awaiting-owner states;
- organizational activity/history/replay.

The visual hierarchy should support the progression:

`Organization → Department → Team/Employee → Work → Interaction/Handoff → Evidence/Details`

Characters should remain original AIOS miniature professionals with distinct role, department, seniority/personality cues and semantically supported state—not generic avatars.

## 12. Spatial-office reference adoption

AI-agent-office references may inform the concept of multiple departments as distinct physical zones, employee grouping, inter-department relationships, drill-down, work-state visibility, and organization-at-a-glance comprehension.

Do not copy generic neon tiles, floating statistic-card farms, meaningless network lines, decorative dashboards, or visualizations that imply unsupported relationships. AIOS should use authored architecture, spatial memory, department identity, restrained atmosphere, and canonical state.

## 13. Persistent-agent reference adoption

Persistent-agent systems may inform long-running employees, reusable capabilities, research, file/artifact work, integrations, terminals/runtimes, recurring objectives, and communication adapters. AIOS adapts these concepts into a multi-employee organization with stronger authority, evidence, provenance, and truth semantics rather than copying a single personal-assistant model.

## 14. Employee detail experience

An employee inspection/detail surface should eventually be capable of presenting:

- identity/character;
- department, position, seniority, reporting line;
- capability/skill inventory and versions;
- skill origin (native/imported/learned);
- tools/integrations and availability;
- effective permission/authority boundaries;
- current mission/work and state;
- queued responsibilities;
- blockers/dependencies;
- recent evidence/work products;
- scoped memory/context summary where appropriate;
- learned-skill history/performance where useful.

This surface must not become a decorative RPG stat sheet; information must help understand capability, work, authority, or evidence.

## 15. Observability and provenance

Automatic organizational learning requires strong observability. AIOS should be able to answer:

- Why was this employee selected?
- Which skills were used, and which versions?
- Which tools/actions ran?
- What authority/permissions applied?
- Which evidence supports the result?
- Was a skill imported, authored, or automatically learned?
- Which prior executions produced a learned skill?
- Why was a learned skill updated/superseded/quarantined?

Historical replay should preserve the versions that actually participated rather than presenting current skill definitions as if they existed in the past.

## 16. Security and failure boundaries

Automatic skill creation/reuse must fail safely. At minimum:

- no automatic privilege escalation;
- no secret/credential embedding in learned procedures;
- no external skill may override higher AIOS instructions/authority;
- untrusted skill content is data/instructions within its bounded execution context, not system authority;
- destructive/external side effects remain behind their existing permission/confirmation boundaries;
- provenance/version history is retained;
- failed validation cannot be presented as proven capability;
- unsupported activity cannot be visualized as fact in Living HQ;
- learned procedures must be revocable/quarantinable/supersedable.

## 17. Product acceptance principles

This architecture is successful when:

1. employees have meaningful, inspectable capabilities rather than labels alone;
2. departments correspond to real specialization and work routing;
3. repeated successful work automatically increases reusable organizational capability;
4. automatic learning does not increase authority by itself;
5. skills, memory, tools, evidence, and authority remain distinct concepts;
6. external ecosystems can enrich capability discovery without becoming AIOS authority;
7. Living HQ reflects real organizational work/capability relationships;
8. cross-department missions can be decomposed, executed, evidenced, synthesized, and escalated truthfully;
9. historical provenance can explain how a result and learned capability were produced;
10. the system becomes more capable through use without becoming less trustworthy.

## 18. Implementation sequencing

This document establishes the target architecture; it does not authorize an uncontrolled implementation jump during current Visual Redesign Convergence.

Recommended sequence:

1. preserve this architecture in canonical program documentation;
2. define capability/skill domain contracts and provenance schema;
3. define employee capability profiles and role eligibility;
4. define tool/permission intersection semantics;
5. implement registry/read models;
6. implement automatic recurrence detection and skill extraction behind bounded runtime contracts;
7. implement validation/versioning/quality telemetry;
8. connect work routing and employee selection;
9. expose employee capability inspection surfaces;
10. integrate semantically with Living HQ;
11. add external skill discovery/import pipeline;
12. prove automatic learning with deterministic repeated-task fixtures and authority-negative tests;
13. expand to cross-department mission orchestration.

Do not let this future architecture derail the currently active Operator visual-convergence slice. It should shape the design system and Living HQ now so those surfaces do not need another conceptual redesign later.

## 19. Session continuity

This file is mandatory context for sessions that modify AI employees, departments, Living Organization/Living HQ, skills, tools/integrations, agent memory, work routing, automation, or cross-department orchestration.

New sessions must preserve the automatic-learning direction: repeated successful procedures are automatically detected, extracted, validated, versioned, and made reusable, while authority and permission ceilings remain independently enforced.