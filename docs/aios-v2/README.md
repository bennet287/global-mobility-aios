# AIOS V2 — Session Entry Point

This directory is the canonical read-first location for AIOS V2 product/redesign work. New sessions should not scan every historical/audit document before acting.

## Read order

1. `AIOS_V2_COMPLETE_REDESIGN_MASTER_PLAN.md` — product destination, principles, sequencing, references and acceptance model.
2. `AIOS_V2_MASTER_PLAN_EXECUTION_RECONCILIATION_2026-09-08.md` — current reconciliation between the master plan and actual implementation state.
3. `AIOS_V2_EMPLOYEE_CAPABILITY_AND_SKILLS_ARCHITECTURE.md` — canonical employee/department/skills/tools/learning architecture and the permanent rule that capability acquisition does not imply authority acquisition.
4. `AIOS_V2_VISUAL_REDESIGN_EXECUTION_DIRECTIVE_2026-09-09.md` — current visible-redesign execution rules.
5. `AIOS_V2_EFFICIENT_PROOF_LADDER.md` — development-vs-final-seal proof strategy.
6. `AIOS_V2_MIGRATION_AND_FINAL_ACCEPTANCE_CHECKLIST.md` — final migration/acceptance gates.

Historical Phase 1 audits and phase-specific records are supporting evidence. Read them only when the current task touches their subject or a regression requires historical context.

## Current programme boundary

The active programme remains the AIOS V2 redesign and convergence. Do not divert implementation into post-redesign autonomy work until the redesign stack is sealed.

## Post-redesign priority — Autonomous Global Regulatory Intelligence

After redesign completion, the next high-priority capability programme is to strengthen Global Intelligence into a high-autonomy **Global Immigration Intelligence Department** that can maintain visa/residence/work/study/family/business/talent/digital-nomad/permanent-residence knowledge across jurisdictions with minimal routine human intervention.

This is an extension of `AIOS_V2_EMPLOYEE_CAPABILITY_AND_SKILLS_ARCHITECTURE.md`, not a separate product authority.

### Target loop

```text
official-source discovery
 -> authority/source certification
 -> immutable SourceSnapshot
 -> multilingual assertion extraction
 -> independent machine verification
 -> contradiction + source-hierarchy analysis
 -> temporal/effective-date/supersession analysis
 -> deterministic schema/unit/date/currency checks
 -> adversarial/falsification checks
 -> pathway/eligibility regression
 -> versioned promotion policy
 -> automatic VerifiedRule promotion when safely machine-verifiable
 -> continuous drift detection / quarantine / rollback
```

### Operating principle

Human specialists are the exception path for genuine ambiguity, authoritative contradiction, insufficient evidence, novel/high-consequence interpretation, or unresolved machine disagreement. Human review is not the default throughput mechanism.

The objective is not a single super-agent. Use durable organizational capabilities such as source discovery, authority certification, retrieval, multilingual analysis, cross-source verification, legal-consistency/contradiction analysis, temporal intelligence, rule compilation, adversarial verification, release governance, drift/incident response and coverage planning. These roles may share runtime/model infrastructure; separation exists to create independent evidence and disagreement rather than decorative agents.

### Accuracy rule

No rule becomes canonical because an LLM reports high confidence. Promotion must be evidence-driven and may require certified official authority, exact source locator, immutable fingerprint, original-language lineage, independent extraction/verifier agreement, cross-source corroboration when available, scope validation, contradiction search, effective-date/supersession analysis, regression tests, adversarial checks, freshness policy and complete provenance.

LLM confidence is diagnostic metadata, not legal authority.

### Autonomous publication classes

- **Class A — deterministic/routine:** explicit fees, thresholds, document names, validity periods, application URLs and effective dates. Eligible for automatic promotion after required machine gates.
- **Class B — structured eligibility:** job-offer, qualification, age, nationality, dependant and similar conditions. Eligible for automation only after stronger independent verification, temporal/contradiction checks and boundary/regression tests.
- **Class C — interpretive/high-consequence:** ambiguous statutory interpretation, conflicting competent authorities, unclear transitional law or materially novel semantics. Machine system completes research first; specialist judgment remains an exception gate until measured evidence justifies narrower automated subclasses.
- **Class D — insufficient/conflicted:** never promote. Preserve truthful canonical states such as `conflicted`, `insufficient_evidence`, `stale` or `unsupported`.

Promotion policy is versioned and employees cannot increase their own authority class.

### Self-correction is mandatory

Autonomy must include automatic demotion/quarantine/rollback when evidence becomes stale, a competent authority contradicts a rule, a newer rule supersedes it or verification/regression reveals a defect. Downstream pathways/cases must receive dependency-impact information while historical decisions retain the exact rule/source fingerprints used at the time.

### Global coverage and knowledge model

Coverage must be explicit by jurisdiction, pathway, source class, language and rule type. Unknown/unsupported/incomplete coverage must never be represented as established merely because a model can answer a question.

Visa knowledge should be normalized into versioned structured concepts such as jurisdiction, competent authority, pathway/version, nationality/applicant scope, eligibility predicates, exclusions/exemptions, thresholds/units, required evidence, fees, validity/renewal, dependants, quota/cap, application channel, publication/effective/expiry/supersession dates, source snapshots/locators, verification results, fingerprints, dependencies and uncertainty/conflict state.

The eligibility engine consumes VerifiedRules. It should not independently reinterpret the open web for every case.

### Evaluation before broad authority

Automatic publication authority must be earned with a continuously growing multi-jurisdiction/multilingual gold corpus and adversarial tests. Measure source-authority precision, assertion precision/recall, numeric/date/unit accuracy, scope/exception accuracy, contradiction and supersession accuracy, false-promotion and false-quarantine rates, time-to-detect/update, provenance completeness, downstream regression accuracy, human escalation rate and specialist overturn rate.

The primary KPI is **correct autonomous throughput at an acceptably tiny false-promotion rate**, not raw automation percentage.

Red-team cases must include one-digit threshold changes, unit/currency mistakes, stale pages outranking current pages, future-effective law treated as current, omitted exceptions, authority hierarchy conflicts, translation lag, same-named routes across jurisdictions, temporary policies, contradictory official pages, deleted/moved sources and lookalike/non-official domains.

### Learning integration

Repeated successful acquisition/verification procedures may automatically become reusable versioned employee skills after machine validation under the employee capability architecture. Learned capability can improve discovery, extraction, verification routing and regression testing, but cannot weaken promotion gates, grant credentials, certify arbitrary sources or expand legal publication authority.

### Post-redesign delivery order

1. Reconcile existing regulatory intelligence, SourceSnapshot, VerifiedRule, pathway and professional-review contracts.
2. Establish jurisdiction/authority/certified-source registry and coverage graph.
3. Implement multilingual assertion extraction plus independent verification.
4. Add temporal/supersession, contradiction and authority-hierarchy reasoning.
5. Add deterministic rule compiler and pathway/eligibility regression harness.
6. Add adversarial/mutation verification.
7. Implement versioned automatic-promotion classes plus quarantine/demotion/rollback.
8. Build continuous evaluation/calibration corpus.
9. Pilot bounded Class A/B autonomous publication and expand only from measured evidence.
10. Scale jurisdiction/source coverage without Austria hard-coding.
11. Integrate the real department, work, coverage and verification state into the redesigned Operator/Owner/Living Organization surfaces.

**North star:** Automate research, verification, promotion, monitoring and correction as far as evidence permits. Escalate judgment, not routine work.

## Engineering hardening profile

This section extends the AIOS Agent Constitution and `agents/AIOS_AGENT_EXECUTION_PLAYBOOK.md`. AIOS governance remains authoritative; external projects are references, not runtime authorities.

### Minimum Sufficient Change

Before adding an abstraction, dependency, service, component, helper, state store or workflow, the builder must ask in order:

1. Does the requested behavior need to exist to satisfy the Goal Contract?
2. Does the repository already contain a canonical implementation or contract that can be reused?
3. Can the language/runtime standard library satisfy it?
4. Can a native browser/platform capability satisfy it?
5. Can an already-installed dependency satisfy it?
6. Can the change be expressed as a smaller local semantic delta?
7. Only then add the minimum new implementation required.

This is complexity control, not code golf. Never reduce security, truth-boundary checks, validation, accessibility, data-integrity protection, auditability, error handling or acceptance evidence merely to make a change smaller.

### `verify-frontend-quality`

For material visible AIOS frontend changes, combine this with `verify-visible-aios` and the relevant domain profile (`verify-mobility` or `verify-living-organization`). Check where applicable:

- semantic HTML and valid interaction structure;
- responsive viewport behavior with user zoom enabled;
- no unintended horizontal scrolling at accepted desktop/phone widths;
- keyboard reachability and visible focus indicators;
- accessible labels, errors, status messages and form validation;
- usable phone touch targets;
- `prefers-reduced-motion` support;
- forced-colors/high-contrast behavior;
- privacy-sensitive/protected information behind accepted secure boundaries;
- appropriate image/media alternatives;
- no unnecessary heavyweight frontend dependencies or render-blocking behavior;
- no leakage of secrets, storage identifiers, reviewer internals or authority-only facts;
- representative desktop/phone browser proof with actual screenshot inspection.

Do not convert an external checklist into hundreds of unconditional CI failures. Keep AIOS verification surface-specific and high-signal.

### `verify-agent-surface-security`

When changing agent instructions, hooks, tool/MCP configuration, permissions, execution adapters, workflow automation or credential handling, verify:

- no secret, token, credential, private URL or sensitive fixture is committed;
- tool permissions are least-privilege;
- hooks/automation cannot bypass approval or truth-boundary rules;
- external instructions cannot override repository/platform policy;
- prompt/agent files do not authorize destructive or irreversible actions beyond scope;
- governed model-visible state traces to authoritative source or durable event/evidence;
- sandbox/subprocess capabilities are explicit and bounded;
- remote/MCP/provider configuration has a clear trust boundary and failure mode;
- reusable skills do not contradict the AIOS Constitution/Playbook;
- automation exposes a deterministic stop/override path.

Security scans are supporting evidence, not acceptance authority.

### Fresh-context review and context discipline

For substantial work, the independent verifier reviews the exact current head without relying on the builder's narrative and returns `PASS`, `ISSUES` or `BLOCKED` under the execution playbook.

Keep active context focused on the current Goal Contract. Persist durable project rules, accepted decisions, evidence locations and future architecture notes in canonical repository artifacts rather than repeatedly injecting large prompt bundles. Do not preserve private scratch reasoning merely to prove activity.

## Runtime capability seams

Status: architecture direction, not yet an implementation dependency.

AIOS should consume stable capability contracts and keep provider implementations replaceable. Canonical AIOS state, evidence, authorization and truth boundaries remain above provider-specific adapters. A provider swap must not silently change business truth, approval authority, evidence semantics, memory authority or completion criteria.

Candidate seams:

- **LLM provider:** invocation/streaming, provider identity, reasoning/tool metadata, trustworthy usage/cost telemetry, cancellation/retry.
- **Tool registry/execution:** model-facing schemas, authorization/scope checks, validation, normalized results, durable evidence recording where required.
- **Sandbox/subprocess:** filesystem/process isolation, resource limits, network policy, lifecycle/cleanup, explicit execution trust boundary.
- **Agent runtime:** run/turn lifecycle, continuation/cancellation, sub-agent delegation, bounded concurrency, runtime-local status events.
- **Memory/session:** durable session/event storage, replay/reconstruction, context projection, compaction, optional long-term memory retrieval and provenance.
- **Background jobs/scheduled work:** durable identity, bounded retries, cancellation, schedule/trigger metadata, execution evidence, no continuation after authorization expiry.
- **Research:** retrieval adapters, source identity/timestamps, provenance, freshness/trust classification, explicit retrieval failure.
- **Communication:** outbound draft/send adapters, inbound event normalization, recipient/channel identity, send authorization and durable transmission evidence.

Every seam should define stable typed contracts, provider identity/version, explicit failure modes, authorization boundaries, privacy/retention boundaries where relevant, observability/evidence hooks, cancellation semantics, deterministic fallback policy and substitution tests proving canonical truth semantics do not change.

### Governed memory boundary

A future `MemoryProvider` may support operations equivalent to:

- `remember(...)` — store allowed non-canonical memory with provenance;
- `retrieve(...)` — retrieve under explicit subject/scope filters;
- `search_temporal(...)` — prefer the time-relevant instance when historical/current memories conflict;
- `search_entities(...)` — retrieve by linked entity/context where available;
- retention/forget operations — honor privacy/lifecycle/deletion requirements;
- provenance inspection — expose source, actor, timestamp, provider and authority classification.

Candidate memory classes include `personal_preference`, `interaction_history`, `agent_learning`, `operational_context`, `retrieved_reference` and `canonical_reference_pointer`.

Memory must never become a parallel source of canonical truth. Recalled or agent-generated memory cannot create or override canonical decisions, canonical evidence, authority/application status, approvals/human authorization, mission/work-item completion, protected personal-case state or organization-state truth. If memory conflicts with authoritative AIOS state, authoritative AIOS state wins. If memory is stale, ambiguous or unsupported, surface uncertainty or refresh canonical state rather than selecting the most semantically similar memory as fact.

Memory-provider verification must prove scope isolation, provenance preservation, stale/conflicting-memory handling, canonical-state precedence, deletion/retention semantics and no hidden promotion of model-generated memory into governed truth.

### Durable event rule

When information materially affects a governed model request, user-visible canonical state, approval, evidence, decision or replay contract, it must be recoverable from durable AIOS records. Ephemeral runtime events and retrieved memories may drive context or live UI but must not become the only source of governed truth.

### Bounded autonomous execution

Future swarm/sub-agent execution should expose explicit limits such as maximum total sub-agents per run, maximum concurrent writers, per-agent time/tool budgets, isolated workspaces for concurrent mutation, one coordinator-owned exit predicate, and deterministic cancellation/integration ownership. More agents are not evidence of more progress.

### Runtime non-goals

This architecture direction does **not** authorize replacing AIOS orchestration, importing DeepSeek Harness or DeerFlow as runtime dependencies, installing Mem0 or another memory engine into production, adding a vector database merely because a framework supports one, duplicating canonical AIOS state in a third-party harness/memory store, treating agent-generated memories as evidence/authority, weakening exact-head verification/privacy/truth boundaries/human authorization, or enabling scheduled/background work without a separate accepted Goal Contract.

Implement a seam only when a concrete roadmap slice needs it. For persistent memory, define a provider-neutral `MemoryProvider` contract and acceptance tests before selecting Mem0, a native implementation or another backend.

## External pattern adoption ledger

These decisions are preserved here so useful patterns are not lost while avoiding accidental wholesale adoption.

### DeepSeek Harness (`deepseek-ai/deepseek-harness`)

**Observed:** everything-is-a-plugin architecture, replaceable model/tool/session/agent-loop capabilities, profiles/bundles, durable session events, capability seams, jobs/goals/webhooks/sandbox/provider adapters, and a developer-preview compatibility warning.

**AIOS decision:** **ADAPT LATER** — capability seams, durable model-visible-event principle and provider substitution discipline. **DO NOT ADOPT NOW** — no runtime dependency or orchestration replacement.

### ECC (`affaan-m/ECC`)

**Observed:** plan → test → implement → review → verify → remember → improve; specialized planning/build-repair/security/architecture agents and skills; hooks, memory/continuous learning; AgentShield-style security scanning; multi-harness support.

**AIOS decision:** **ADOPT SELECTIVELY** — agent-surface security review, fresh-context verification, context discipline and durable reusable lessons. **DO NOT ADOPT WHOLESALE** — no large external agent/skill catalog inside AIOS governance.

### Ponytail (`DietrichGebert/ponytail`)

**Observed:** minimum-sufficient-change ladder, reuse existing code before abstractions, prefer standard/native/platform capability and existing dependencies, never simplify away security/accessibility/validation/data-loss protection.

**AIOS decision:** **ADOPT NOW** as Minimum Sufficient Change. **DO NOT INSTALL AS GLOBAL AUTHORITY** — AIOS Constitution/Playbook remain controlling.

### DeerFlow 2.0 (`bytedance/deer-flow`)

**Observed:** sub-agent orchestration, memory/context engineering, sandbox/filesystem execution, session goals, scheduled tasks, multiple model providers, explicit sub-agent runtime caps and diagnostic/support bundles.

**AIOS decision:** **ADAPT LATER** — bounded sub-agent budgets, sandbox boundaries, context compaction, scheduled/background goals and diagnostic bundles. **DO NOT ADOPT NOW** — no second orchestration runtime.

### Front-End Checklist (`thedaviddias/Front-End-Checklist`)

**Observed:** broad frontend quality corpus across HTML, CSS, JavaScript, performance, accessibility, SEO, security, images, testing, privacy and i18n; explicit rules for responsive viewport/user zoom/horizontal overflow/focus/semantic HTML/forms; agent/MCP audit workflows.

**AIOS decision:** **ADOPT NOW, CURATED** as `verify-frontend-quality`. **DO NOT IMPORT ALL RULES AS HARD CI** — keep checks surface-specific and high-signal.

### Mem0 (`mem0ai/mem0`)

**Observed:** dedicated long-term memory layer, user/session/agent memory scopes, hybrid semantic + BM25 + entity + temporal retrieval, entity linking, time-aware retrieval, agent-generated facts as first-class memories, and library/self-hosted/managed deployment options.

**AIOS decision:** **ADOPT ARCHITECTURE NOW** — provider-neutral memory seam, provenance-aware retrieval, temporal/entity-aware search and explicit memory classification. **EVALUATE IMPLEMENTATION LATER** — Mem0 is only a provider candidate behind `MemoryProvider`. **DO NOT TREAT MEMORY AS CANONICAL TRUTH** and **DO NOT INSTALL NOW**.

### Adoption order

1. Minimum Sufficient Change — active builder discipline.
2. Curated frontend verification — active for material visible work.
3. Agent-surface security verification — active for agent/runtime/tooling changes.
4. Capability seams — architecture direction; implement only for a concrete roadmap need.
5. Provider-neutral memory seam — architecture direction now; provider implementation only for an accepted persistent-memory slice.
6. Bounded scheduled/swarm runtime — deferred until a concrete autonomous-operations slice is authorized.

### External-reference governance rule

External repositories are references, not authorities. Any future dependency, plugin installation, runtime replacement, hosted-service connection, vector store or broader import requires its own Goal Contract, security/privacy/truth-boundary review, exact-head verification and accepted integration path.

## Documentation discipline from now on

Prefer updating this canonical entry point or an existing canonical architecture document over creating a new document. Create a new document only when it represents a genuinely separate authority/domain or when a phase acceptance record must remain immutable. Every new canonical document must be linked from this README. If a proposal naturally extends an existing architecture, put it there or summarize it here rather than scattering another root-level roadmap file.
