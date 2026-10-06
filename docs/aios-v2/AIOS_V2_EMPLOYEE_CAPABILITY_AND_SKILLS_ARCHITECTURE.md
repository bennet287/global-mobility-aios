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

An initial Observatory read model may report a narrower structural signal from completed WorkItems linked to active, governed Contribution records. It must count distinct work and source identities, remove corrected outcomes, and remain observation-only. A Contribution linked to work does not prove the work caused the outcome, and a completion does not show which procedure succeeded. No structural signal alone creates a learned skill or a new employee capability.

For the bounded Austria specialist path, the Observatory may additionally report a validated internal execution lineage using the existing K.1 WorkItem/output/attempt/AgentRun check. A pending-review or completed internal run is still not source-outcome attribution. The Contribution source validator and execution runtime have separate owners; a linked WorkItem ID alone cannot bridge them. Keep learned-skill eligibility closed until a source transition proves exact reviewed execution causation and a stable procedure trace passes validation.

Automatic source-transition Contributions currently have no WorkItem/AgentRun association. The optional WorkItem link on a standalone Contribution is tenant checked but not causal proof. Report linked and unlinked outcome coverage honestly; do not infer that an empty recurrence means there is no history to learn from, and do not attach an internal-analysis run to a source publication it merely consumed.

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

### 8.1 REA engineering integration — full catalog

The user-selected REA integration belongs to one umbrella capability, `engineering.reverse_engineering`. Its intended scope is the complete reviewed 122-tool MCP catalog, including decompilation, native/managed/artifact/browser/Electron analysis, runtime observation, capture/replay, reconstruction, comparisons and evidence workflows. The managed two-tool fixture in the dated boundary audit is a starting verification scenario, not a reduced product scope.

Each tool has an exact AIOS identifier `engineering.reverse_engineering.rea.<upstream_tool_name>`, its complete input/output schemas, source kind/operation/session metadata, declared effects and annotation hints. The umbrella groups discovery and work matching; it is not a wildcard entitlement. Do not expand a position allowance for the umbrella into permission for all tools. Catalog entries describe reviewed source contracts, not an installed or operational provider. Preserve source/build/catalog/provider/session identities separately.

The catalog foundation is `apps/api/app/services/organization_rea_catalog.py` with a checked-in lossless snapshot in its adjacent `rea_catalog/catalog.json` and preserved `REA_LICENSE.txt`. Discovery returns all 122 exact descriptors with detached schema views. `compare_rea_tools_observation` compares one bounded complete advertised tools/list result, rejecting partial/paginated or drifted contracts; optional source declarations are compared separately and never authenticated by equality. `disabled_rea_runtime_profile` exposes the complete candidate tool set with `enabled=False` and no enable parameter or production selector registration. `scripts/import_rea_catalog.py --check <reviewed-source-checkout>` reproduces the snapshot from pinned tracked source data without executing donor code. Local snapshot/semantic hashes commit to this SDK advertisement projection; upstream source-declared runtime digests use a different direct-Zod projection and are not reproduced or attested by this import. This foundation does not validate invocation arguments, start a transport or establish a provider sandbox.

The intended execution path is `AIOS employee -> canonical WorkItem/attempt -> fresh ContextBundle/runtime intersection -> AIOS dispatcher -> admitted REA session/tool -> bounded attributable observation -> AIOS review`. AIOS owns assignment, authenticated actor binding, artifact authorization/custody, worker isolation, exact per-call authorization, resources/cost admission, transport/session lifecycle, audit and outcome review. REA supplies engineering operations; its tool responses, confidence and reconstruction checks cannot grant authority, qualify competency or promote a VerifiedRule.

The full integration must pass each acceptance layer for every applicable tool; a two-tool demonstration cannot establish full activation:

| Acceptance layer | Required proof |
| --- | --- |
| Catalog coverage | All 122 exact identities and schemas mapped without silent omissions, aliases, duplicates or unreviewed additions; reproducible snapshot and drift detection |
| Provider/session admission | Verified package/build provenance, exact observed catalog and provider identity, supported platform/dependencies, AIOS-owned isolated transport and investigation-bound session; matching catalog data alone is insufficient |
| Artifact/work authorization | Reviewed source/custodian/purpose/target hash/scope/expiry/revocation, immutable staged bytes, canonical tenant/work/position/attempt ownership, suspension/cancellation/pause/assignment enforcement |
| Per-call execution | Fresh exact allowance intersection, schema/argument/path and effect admission, bounded time/memory/process/network/filesystem/output, pre-use audit, fixed failure detail and unknown-outcome handling |
| Evidence/review | Validated bounded observation envelope and semantic evidence IDs, target/session/provider/tool/argument linkage, manifest/content commitments, explicit unknowns and independent review; hashes do not prove truth |
| Full operational coverage | Tool-by-tool supported and blocked states, positive/negative tests and separately attributed actual-provider fixtures for every applicable effect class; platform or licensing limitations remain explicit |

Tool effects are cumulative rather than mutually exclusive: an observation may also launch a provider process, mutate session state or write analysis caches. Separate parser/static work, native provider launch, passive capture, filesystem persistence, UI/network interaction, destructive/session changes and active replay in execution policy. MCP annotation hints and advertised effect flags are untrusted declarations until the admitted operation/provider environment is independently verified. A Linux replay sandbox does not establish isolation for other REA operations.

Artifact authorization reuses canonical `ExecutiveDecision` Board-reserved L4 review and the existing human Board/owner outcome command. `organization_rea_artifacts` binds one bounded typed scope to the target SHA-256/size, reviewed source/provenance/custodian/rights references, purpose/reconstruction scope, exact catalog tool IDs, expiry and current tenant/work/assignment/position version. The typed proposal witness must precede approval; canonical creation/approval snapshots and fresh state checks reject incomplete or altered lineage, expiry, cancellation, suspension and stale assignment/scope. Successor lineage blocks the predecessor conservatively; it cannot revive authority after rejection or expiry. Reviewed references are human judgments within the trusted command/database boundary, not independently established ownership or publisher provenance. Exact artifact scope can include all 122 tools and never changes position entitlement.

Internal regular-file custody uses deployment-owned source/custody roots, descriptor-relative no-follow traversal, bounded size/hash checks, exclusive restrictive staging and a committed existing AuditLog witness. Revalidation checks both canonical authorization and staged bytes; a receipt is not execution authority. No public upload/filesystem endpoint, new permission table or migration is introduced. Filesystem modes and content commitments do not provide a worker sandbox, authenticated provider admission or atomic database/filesystem delivery; staging failure cleanup is explicit and successful custody requires lifecycle cleanup. Custody revalidation closes its inspected descriptor; it does not hand transport an immutable open-file capability or prevent a later path race. A future dispatcher must preserve byte identity at provider use and freshly bind the work attempt, exact entitlement and admitted provider/session immediately before use. PostgreSQL row locks serialize guarded reads/witness completion where supported; SQLite tests do not establish concurrent writer exclusion.

Admission prerequisites in `organization_rea_admission` reuse human Board/owner ExecutiveDecision review and existing AuditLog witnesses. One reviewed contract pins the build-bundle hash/size and review references, independent deployment worker/key/policy anchors, expected package/server/protocol/platform identity, current artifact/work scope and all 122 exact tool entries. Every entry has an explicit candidate-or-blocked disposition, provider/version, review reference and cumulative source-declared hazard minimum. Candidate is a reviewed plan, not operational support or independently verified effects. Internal verification reads bounded no-follow regular build bytes without executing or installing them; byte equality does not prove an upstream publisher, source-to-build relationship or installed executable tree.

AIOS issues short-lived nonce/session challenges bound to fresh artifact custody and a current running canonical execution attempt/start audit, using a token digest rather than putting the token in new observations. Signed worker statements include separately reported identity and a commitment to the complete advertised catalog. Consumption rechecks canonical state, deployment trust, build/custody bytes, identity, freshness and signature under a conditional database writer guard, preserving WorkItem state/timestamps and recording one-use consumption in the existing audit owner. A valid signature authenticates the statement under the independently pinned reviewed key. It does not prove actual key custody, provider routing/behavior, worker isolation or owned live transport. Outputs keep provider readiness and execution authority false, with those missing proofs explicit.

Signed package inspection commits the complete reviewed Git source tree and the build-recipe/dependency-lock inputs without importing or executing donor code. The importer reproduces the checked-in source-material manifest from pinned regular Git blobs. An internal deployment-pinned builder key authenticates a bounded statement linking those commitments to the currently approved archive and its complete package-file manifest. Inspected archive bytes and the complete installed package-directory snapshot must agree, including source-shipped assets; unsafe paths, duplicate entries, links, special files, unexpected files and resource-bound violations fail closed. The accepted archive profile is a single gzip stream with plain USTAR records; PAX/GNU extensions and other unsupported formats remain blocked, and inspection performs no extraction or lifecycle execution. The signature covers canonical JSON of the original bounded parsed statement, preserving signed timestamp representations rather than normalizing them before authentication. The original signed object, signature and verification summary fit within the existing bounded AuditLog; oversized combined evidence is rejected before persistence. Existing work/attempt, artifact custody, review and audit owners govern this evidence. Successful evidence is a snapshot observation, not a reusable authority grant.

The builder signature authenticates the claim under a trusted deployment key; it does not independently reproduce compilation or authenticate an upstream publisher. REA emits unbundled JavaScript, so the package directory excludes the external Node executable and dependency tree. Those runtime bytes, actual consumed build inputs and immutable binding at later use remain unproven. Inspected descriptors close before return; future launch must preserve fresh byte identity and all authority/resource checks at use.

A separate bounded CI workflow provides actual build-repeatability evidence. Two distinct hosted jobs check the complete pinned source material before and after compilation, install locked dependencies with lifecycle scripts disabled and compile directly using pinned Node/npm/TypeScript. They share no restored npm/Turbo/build cache and never import generated REA JavaScript or start its CLI/MCP/providers. A third job inspects the actual downloaded outputs and compares their complete path/size/hash/content sets, bound to the same exact candidate, workflow run and source. The original build artifacts and comparison report own this observation; a script result or manifest alone does not authenticate a workflow. Hosted build jobs do not establish investigation-worker isolation.

Observed repeatability is limited to that selected recipe and platform. Repeatability alone does not reproduce or authenticate the published npm package, independently bind the generated output to a Board-reviewed package archive, verify external runtime closure, or automatically change the signed package inspector’s claims. No ExecutiveDecision, entitlement, runtime profile, competency or verified rule is promoted by CI artifacts.

The comparison job can assemble a deterministic single-gzip, plain USTAR package from the complete matching compiled output set and all exact source assets selected by the reviewed package declaration, including package metadata, license and readme. Source commitments are checked before and after assembly. No npm packaging hook, donor generator, generated JavaScript, CLI or provider is executed. The preserved package and diagnostic correlation report are build artifacts; CI does not manufacture a Board approval or builder signature.

The existing signed package inspector accepts optional deployment compilation trust only as a physical locator and redundant pin set. The current human Board-approved provider scope must itself carry the exact correlation report digest, candidate, repository, run, attempt, workflow and helper pins; deployment trust must match those governed values before report bytes are considered. The inspector then checks the whole report and complete package/output manifest against the approved archive, revalidates physical report bytes and current work/attempt/custody/review before audit and commit, and records a bounded hash/context summary using the existing AuditLog. Complete correlation may set `compiled_package_dist_matches` and `governed_compilation_evidence_approved`; report labels, copied hashes and Board acceptance of those pins still do not authenticate the owning CI execution. The report is historical compilation evidence, while canonical work and authorization remain freshly checked. All existing source-to-build, publisher, runtime-closure, isolation, provider, live-transport and execution-authority flags remain false. The optional path introduces no public endpoint or permission owner and preserves the default inspector boundary. Existing approved provider contracts that predate the optional compilation-evidence field retain their original bytes, fingerprints and audit lineage; only that field's absence is treated as no evidence. Their proposal retries, worker challenges and default package inspections remain valid, while positive correlation still requires explicit governed evidence.

CI correlation-report attestation uses a reviewed fixed action after inert package assembly. Only the comparison job receives OIDC/attestation write permissions, with signing restricted to same-repository pull requests or explicit dispatch; source compiler jobs retain read permissions. The exact report and raw Sigstore bundle are preserved separately from the package artifact. Fresh diagnostic verification invokes a fixed digest-verified GitHub CLI against those actual bytes and trusted roots, then checks cryptographically verified certificate identity and witnessed timestamps. Repository identifiers, source/ref, workflow revision, trigger, hosted runner and exact run/attempt are checked from certificate fields. Workflow-controlled provenance predicates do not authorize identity. Explicit candidate checkout, execution/source commit and workflow commit remain separate; authenticated workflow bytes must equal reviewed YAML, with candidate helper pins checked independently. A separate read-only job repeats cryptographic verification against downloaded bytes.

This proves which CI execution attested the report bytes; it does not independently prove both compiler jobs caused the stated outputs. Diagnostic verification is not an AIOS admission receipt and copied verifier JSON cannot confer trust. The internal signed package inspector can now consume raw report and bundle bytes through its trusted runtime verifier when the current Board-approved compilation scope separately pins the bundle hash and exact attesting source/workflow commits, ref and trigger. Deployment locators and redundant pins must match that review. The fixed digest-verified CLI freshly verifies the private sealed bytes with default authenticated roots; neither copied verification JSON nor a caller-supplied proof is an authentication input. Existing work/attempt/custody/review and expiry checks remain authoritative, with immutable raw inputs revalidated before and after audit. Historical absent and explicit-null attestation fields preserve their original contract shape. Successful consumption records only bounded certificate identity, witness timestamps and byte commitments in the existing audit and sets the narrow `attesting_execution_identity_verified=True`. `owning_github_execution_authenticated`, candidate-to-CI-source relation and independent compiler causality remain false; report-signing identity does not prove source consumption or both compiler executions. This adds no public route, migration, permission owner or provider execution.

The next boundary must establish independent compiler causality and candidate/source relation, publisher/source provenance and dependency/Node runtime closure, bind immutable bytes at use and admit an AIOS-owned isolated live transport/session before the full-catalog dispatcher can enforce fresh exact allowance, arguments, effects and resources. Closed inspection descriptors and signed metadata cannot solve a later provider-use path race. No public filesystem/private-key/observation-upload endpoint, new permission table, migration, provider launch, production selector or paid call follows from these prerequisites.

Use existing `OrganizationPosition` allowance, context/runtime, WorkItem/execution-attempt, action-output and audit owners. Catalog matching is diagnostic and cannot bypass reviewed artifact authorization, the missing authenticated dispatcher or provider/session admission owners. CLI support is a separately admitted transport using the same AIOS authority path; the 75 CLI commands do not become new autonomous capabilities or a shell fallback around denied MCP tools.

## 9. Memory and institutional knowledge

Memory and skills are distinct:

- **memory** retains relevant context/facts/history;
- **skill** encodes a reusable way of accomplishing work;
- **evidence** records what actually happened and supports claims/outcomes.

Repeated work should preferentially become a skill when the reusable value is procedural. This prevents institutional capability from degenerating into an ever-growing pile of conversational memory.

The first bounded recall query belongs to the existing context broker. Given a fresh, tenant-scoped WorkItem binding, it returns references to active Contribution outcomes and completed WorkItems for the same source, objective, phase, and department. It returns no raw work output, inferred procedure, or verified fact. Its historical-observation citations remain outside the bundle's governed evidence, rules, tools, and context hash; consumers must keep this distinction when rendering or using retrieved history. Wider similarity retrieval and provider use require their own scope and trust proof.

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
