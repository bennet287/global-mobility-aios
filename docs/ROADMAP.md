# Global Mobility AIOS Delivery Roadmap

This is the canonical delivery plan for
[Global Mobility AIOS](GLOBAL_MOBILITY_AIOS_VISION_V1.md). It describes what is
complete, what is operationally incomplete, what must be stabilized, and what
will be built next.

Detailed release notes belong in [CHANGELOG.md](CHANGELOG.md). Feature-level
design and evidence belong in the linked specification documents. This roadmap
does not duplicate either of them.

## 1. Product Direction

Global Mobility AIOS is being built as an **AI-operated global mobility
organization**, not as a conventional application with several disconnected AI
assistants.

The human owner is the Board. A governed CEO Agent operates the organization,
coordinates executive agents and departments, and escalates only Board-reserved
decisions, material risks, and unresolved executive exceptions. Routine work is
delegated through explicit authority limits and remains observable, attributable,
auditable, reversible where possible, and subject to emergency shutdown.

```text
Human Owner / Board
  -> CEO Agent
      -> CTO Agent: technology and engineering
      -> COO Agent: operations, sales, and business intelligence
      -> CISO Agent: security, threat intelligence, and resilience
      -> CMO Agent: marketing and product marketing
      -> CPO Agent: product, design, and product management
      -> CFO Agent: finance, accounts, M&A, and investor relations
      -> CCO Agent: communications, PR, and government relations
      -> CHRO Agent: people, culture, and recruitment
      -> CLO Agent: legal, public policy, and compliance
```

The target operating model is defined in
[AI_ORGANIZATION_GOVERNANCE_V13_0.md](AI_ORGANIZATION_GOVERNANCE_V13_0.md).

## 2. Current Release Posture

**As of:** 2026-08-14

**Development branch:** `roadmap/global-mobility-aios-v11`

<!-- CURRENT_MIGRATION_HEAD: 0074_durable_contribution_activity_model -->

**Code migration head:** `0074_durable_contribution_activity_model`

| Area | State | Current position |
|---|---|---|
| Phases 1-9 | Complete | Core platform, regulatory foundation, profiles, pathways, timelines, and document intelligence delivered |
| Phase 10 software | Complete | Self-updating intelligence, global registry workflow, dashboards, ranking, and multi-year timelines delivered |
| Phase 10 evidence operations | Ongoing | Software workflow is complete; jurisdiction evidence onboarding and independent review remain incomplete |
| Phase 11 | Complete | Corporate, entrepreneur, business, wealth, investment, family-office, and tax/treaty mobility delivered |
| Phase 12 features | Delivered | Portals, partner APIs, governed automation, and government/agency workflows delivered |
| Phase 12 release posture | Stabilized | Database alignment, client-session security, API regression coverage, and local release gates pass |
| Phase 13 | Experience implementation active | Board controls and bounded department runtimes are delivered; Round 6 correctness is PASS; Phase 13.16.0 is CLOSED / PASS; Phase 13.16.1 is IN PROGRESS with design, 13.16.1A persistence, 13.16.1B command/service, 13.16.1C authenticated organization API, and 13.16.1D0 emitter mapping/design complete; 13.16.1D1 caller-owned transaction staging is COMPLETE / PASS, 13.16.1D2 source-certification review emission is COMPLETE / PASS, the first bounded runtime emitter is accepted, 13.16.1D3A initial-rule / VerifiedRule publication is COMPLETE / PASS; 13.16.1D3B regulatory-change publication is COMPLETE / PASS; 13.16.1D3C pathway publication is COMPLETE / PASS; 13.16.1D4 deferred-domain review/integrated regression is COMPLETE / PASS, and 13.16.1E0 Observatory/read-model reconciliation design is COMPLETE; 13.16.1E1 safe snapshot/reconciliation read API is COMPLETE / PASS; 13.16.1E2 Activity staging/semantic coverage is COMPLETE / PASS; 13.16.1E3 is IN PROGRESS with E3A writer inventory/coverage-epoch design COMPLETE and E3B legacy WorkItem material-writer adapters UNLOCKED / NOT STARTED; genuine external-human acceptance remains required later before Phase 13 closure, cross-functional programmes, or Phase 14 |
| Phase 14 | Not started | Global-scale infrastructure and validated platform scaling |

### Current quality evidence

- Web production build: **passing**; the Next.js production build completes successfully with 37 routes including the Phase 13.10.2 `/validation` and `/source-certification-review` workspaces.
- Repository policy: passing.
- Migration-chain integrity: code, fresh SQLite, and isolated fresh PostgreSQL migration cycles are verified at `0074_durable_contribution_activity_model`; the preserved PostgreSQL environment remains intentionally unchanged at `0073_austria_candidate_integrity`.
- Docker production-profile validation: passing.
- API regression baseline: **760 passed, 1 PostgreSQL-only test skipped, 0 failed**
  after Phase 13.16.1E1 safe Observatory acceptance. Focused E1 tests pass **10/10** and
  the protected organization/emitter regression passes **65/65**. The accepted D2-D3C
  emitters remain covered with deterministic replay, atomic rollback, and the closed
  generic source-policy boundary. E1 is **COMPLETE / PASS**.
- E2 is **COMPLETE / PASS**. The accepted complete API baseline is **770 passed, 2 expected PostgreSQL-only tests skipped, 0 failed** with exit code 0. The two bounded isolated-PostgreSQL Activity transaction contracts pass **2/2** with zero persisted Activity streams/rows after rollback at Alembic 0074. Complete semantic history remains explicitly false because legacy organization-governance WorkItem/Decision writers remain outside the E2 adapter boundary; E3A writer reconciliation design is complete and E3B is unlocked.
- SQLite migration compatibility: **passing through current migration head `0074_durable_contribution_activity_model`** via the fresh-database upgrade/downgrade/re-upgrade regression suite.
- PostgreSQL: the preserved authoritative `gmai` Docker database remains **untouched at `0073_austria_candidate_integrity`**; a strict `BEGIN READ ONLY` preflight confirmed that boundary and no upgrade was performed. The isolated PostgreSQL service database at `0074_durable_contribution_activity_model` exposes all eight durable organization tables and passed the actual E1 Observatory summary/department/reconciliation service smoke with transaction read-only protection retained before and after the reads. Both containers were returned to their stopped state.
- Local quality gate: compilation, evidence-pack validation, repository policy,
  release consistency, migrations, Docker-profile validation, frontend production
  build, and the complete API test suite pass. The disposable/test databases are
  current; the preserved developer SQLite file still has pre-existing 0072/0073
  schema drift and was not reset during this hardening slice.

The Phase 13 governance foundation, Board Packet reporting, evidence-output, bounded
execution-control, external-action gates, bounded Operations, Technology, Product,
Security, Security Operations/SOC, Marketing/CMO, Finance/CFO, Communications/CCO,
People/CHRO, and Legal/CLO department runtimes, and the CEO coordination loop remain
implemented.
Phase 13.10.1 is release-closed. Phase 13.10.2 adds durable external-validation scenarios,
runs, evidence, external-human reviews, findings, Board risk acceptance for medium/low
findings, and a deterministic gate. Phase 13.11 adds the bounded Finance/CFO runtime with
Financial Analyst and Accounting Lead specialists. Phase 13.12 adds the bounded
Communications/CCO runtime with PR / Communications Lead and Government Relations Lead
specialists. Phase 13.13 adds the bounded People/CHRO runtime with HR Lead and Culture /
Recruitment Lead specialists. Phase 13.14 adds the bounded Legal/CLO runtime with
General Counsel and Public Policy / Compliance Lead specialists. Phase 13.15 is the
validation programme and correctness gate: its historical Austria runbook remains
useful operational evidence, and the fresh Round 6 mobility-user and professional
shadow reviews produced a [PASS correctness disposition](ROUND_6_CORRECTNESS_DISPOSITION_V13_15.md).
Phase 13.16.0 is **CLOSED / PASS**: implementation is complete and independent
internal rendered acceptance passed. Phase 13.16.1 is **IMPLEMENTATION IN PROGRESS —
DESIGN, 13.16.1A PERSISTENCE, 13.16.1B COMMAND/SERVICE, 13.16.1C AUTHENTICATED
ORGANIZATION API, AND 13.16.1D0 EMITTER MAPPING/DESIGN COMPLETE; 13.16.1D1
TRANSACTION STAGING COMPLETE / PASS; 13.16.1D2 SOURCE-CERTIFICATION EMISSION
COMPLETE / PASS; FIRST BOUNDED RUNTIME EMITTER ACCEPTED; 13.16.1D3A INITIAL-RULE / VERIFIED-RULE PUBLICATION COMPLETE / PASS; 13.16.1D3B REGULATORY-CHANGE PUBLICATION COMPLETE / PASS; 13.16.1D3C PATHWAY PUBLICATION COMPLETE / PASS; 13.16.1D4 DEFERRED-DOMAIN / INTEGRATED REGRESSION COMPLETE / PASS; 13.16.1E0 READ-MODEL RECONCILIATION DESIGN COMPLETE; 13.16.1E1 READ API COMPLETE / PASS; 13.16.1E2 ACTIVITY COVERAGE COMPLETE / PASS; 13.16.1E3 IN PROGRESS — E3A WRITER AUDIT/COVERAGE-EPOCH DESIGN COMPLETE; E3B WORKITEM ADAPTERS UNLOCKED / NOT STARTED**; its
implementation contract is recorded in
[DURABLE_CONTRIBUTION_ACTIVITY_MODEL_V13_16_1.md](DURABLE_CONTRIBUTION_ACTIVITY_MODEL_V13_16_1.md).
This closure does not satisfy genuine external-human acceptance, which remains Phase
13.17 after the shared experience layer is ready; the external-human gate remains held.

## 3. Execution Order

Work must proceed in this order. A later programme must not hide an earlier red
release gate.

1. **Phase 10B evidence operations** — continue independently reviewed
   jurisdiction onboarding without claiming global completeness; this may proceed
   operationally without weakening the active product-validation gates.
2. **Phase 13.15 / Round 6 correctness disposition** — **COMPLETE / PASS**. The
   separate mobility-user and professional shadow reviews found no Critical/High
   correctness issue and no unsupported legal certainty.
3. **Phase 13.16.0 design-system and information-architecture foundation** —
   **CLOSED / PASS**. Implementation is complete and independent internal rendered
   acceptance passed.
4. **Phase 13.16.1 durable contribution and activity model** — establish the
   outcome-oriented source of truth before building observatory dashboards.
   **IMPLEMENTATION IN PROGRESS — DESIGN, PERSISTENCE, COMMAND/SERVICE,
   AUTHENTICATED API, AND 13.16.1D0 EMITTER MAPPING COMPLETE; 13.16.1D1
   TRANSACTION STAGING COMPLETE / PASS; 13.16.1D2 SOURCE-CERTIFICATION EMISSION
   COMPLETE / PASS; FIRST BOUNDED RUNTIME EMITTER ACCEPTED; 13.16.1D3A INITIAL-RULE / VERIFIED-RULE PUBLICATION COMPLETE / PASS; 13.16.1D3B REGULATORY-CHANGE PUBLICATION COMPLETE / PASS; 13.16.1D3C PATHWAY PUBLICATION COMPLETE / PASS; 13.16.1D4 DEFERRED-DOMAIN / INTEGRATED REGRESSION COMPLETE / PASS; 13.16.1E0 READ-MODEL RECONCILIATION DESIGN COMPLETE; 13.16.1E1 READ API IS COMPLETE / PASS; 13.16.1E2 ACTIVITY COVERAGE IS COMPLETE / PASS; 13.16.1E3 IS IN PROGRESS — E3A WRITER AUDIT/COVERAGE-EPOCH DESIGN COMPLETE; E3B WORKITEM ADAPTERS UNLOCKED / NOT STARTED**.
5. **Phase 13.16.2-13.16.9 experience implementation** — build role-based shells,
   owner observatory, department workspaces, dependencies, owner inbox, mobility-user
   and operator experiences, and consolidated evidence/provenance presentation.
6. **Phase 13.16.10 responsive/accessibility and integrated acceptance** — validate
   the three experience architectures and critical rendered journeys as one system.
7. **Phase 13.17 genuine external-human acceptance** — one distinct mobility user
   and one independent professional/operator validate the revised end-to-end product;
   deterministic findings and Board disposition govern Phase 13 closure.
8. **Phase 14 scale work** — adopt new infrastructure only after Phase 13 acceptance
   and measured demand justify it.

## 4. Stabilized: Phase 12

Phase 12 is delivered and stabilized. The items below were completed before the
Phase 13 foundation was introduced.

### 12.S1 Runtime database alignment — done

- [x] Back up the local SQLite and Docker PostgreSQL databases.
- [x] Upgrade local SQLite from `0046` to `0056`.
- [x] Upgrade Docker PostgreSQL from `0054` to `0056`.
- [x] Confirm registered models and actual columns/tables are aligned.
- [x] Confirm the API container reports migration head `0067`.

### 12.S2 Secure portal-session correction — done

- [x] Replace the session-only random pseudo-device identifier with a durable,
  explicit session design.
- [x] Do not cache a portal URL containing a bearer token.
- [x] Prefer a one-time token exchange into an HttpOnly, Secure, SameSite cookie.
- [x] Define new-device enrolment, session revocation, expiry, recovery, and
  device-list management.
- [x] Preserve immediate server-side revocation and lead-scoped projections.
- [x] Add an explicit cache and storage purge on sign-out.

The existing Phase 12.8.7 implementation is a PWA/mobile-web foundation. It is
not a native iOS or Android application and must not be described as one.

### 12.S3 Error-contract and test repair — done

- [x] Align the client-portal `403` device-mismatch response, frontend parser,
  and API test around one documented response schema.
- [x] Restore the full API suite to green.
- [x] Run the complete local quality gate after database alignment.

### 12.S4 Frontend regression coverage — done

- [x] Add browser-level smoke coverage for the client portal and secure-session
  lifecycle.
- [x] Add regression coverage for authority appointments, agency submissions,
  external agency assignments, and submission checklists.
- [x] Cover primary empty, populated, validation-error, and authorization-error
  states.

### Phase 12 stabilization exit criteria

- [x] Local and Docker databases report `0058`.
- [x] API tests, frontend build/type checks, migration checks, schema checks,
  Docker checks, and repository policy all pass.
- [x] No bearer token is persisted in a service-worker cache key.
- [x] A legitimate returning client is not locked out merely by closing and
  reopening the installed portal.
- [x] Revoked and expired portal sessions fail closed online and offline.

## 5. Ongoing Operational Programme: Phase 10B Coverage

The software workflow is complete. The remaining work is evidence collection,
independent review, publication, and continuous freshness maintenance.

### Coverage rules

- Never infer an immigration-rule relationship from a territory's registry
  presence.
- Require reviewed authority and official-source evidence.
- Require independent assessment and source-certification decisions.
- Capture immutable baseline snapshots only after both reviews pass.
- Publish initial verified rules through separate proposal, review, and
  publication identities.
- Keep the global-coverage claim false until every required jurisdiction passes
  the release gates.

### Operating cycle

1. Select the next evidence gaps from the prioritized worklist.
2. Research the jurisdiction, authority, relationship, and official source.
3. Submit an atomic evidence batch.
4. Complete independent assessment and source-certification review.
5. Queue only approved baseline captures.
6. Draft, independently review, and explicitly publish snapshot-pinned rules.
7. Reconcile the readiness receipt and maintain source freshness.

The last recorded readiness in the delivery evidence is **82/243**. This is an
operational data state, not a software-completeness measure, and must be
recalculated from the active database before any external statement.

Key specifications:

- [GLOBAL_COVERAGE_EVIDENCE_OPERATIONS_V10_15.md](GLOBAL_COVERAGE_EVIDENCE_OPERATIONS_V10_15.md)
- [GLOBAL_COVERAGE_SOURCE_ONBOARDING_V10_16.md](GLOBAL_COVERAGE_SOURCE_ONBOARDING_V10_16.md)
- [INITIAL_RULE_ASSERTIONS_V10_19.md](INITIAL_RULE_ASSERTIONS_V10_19.md)
- [COVERAGE_READINESS_RECEIPTS_V10_20.md](COVERAGE_READINESS_RECEIPTS_V10_20.md)
- [Coverage tranche operations v10.22](COVERAGE_TRANCHE_OPERATIONS_V10_22.md)
  — multi-batch tranche operations with independent review gates
- Initial-rule assertion schema: migration `0032_initial_rule_assertions`

## 6. Active Gate: Phase 13 — AI Organization Governance and Autonomous Operations

**Status:** Governance foundation, Board reporting, the first bounded autonomous
organization flow, the Operations, Technology, Product, Security, Security
Operations/SOC, Marketing, Finance/CFO, Communications/CCO, and People/CHRO
department runtimes, and bounded CEO coordination are delivered. The COO delegates
general operating objectives to Sales Intelligence, Operations Coordination, and
Business Intelligence, and adds Application Readiness for mobility-case events. The
CTO delegates technology work to the Vice President of Engineering and Lead Architect
for delivery-readiness, architecture, security, data-handling, integration, and
reversibility analysis. The CPO delegates product work to the Product Manager and
Design Agent for product fit, scope, roadmap alignment, success metrics, design
quality, UX research, and accessibility analysis. The CISO delegates security work to
the Security Lead and Threat Analyst for security controls, attack surface, policy
alignment, threat intelligence, prompt-injection, jailbreak, data-exfiltration, and
compromised-agent indicator analysis, and delegates Security Operations work to the
SOC Lead and SOC Analyst for agent-behavior monitoring, audit-log triage, incident
coordination, and anomaly analysis. The CMO delegates marketing work to the Creative
Director and Marketing Manager for brand fit, creative quality, messaging, audience
alignment, channel fit, campaign plan, growth metrics, and budget-constraint analysis.
The CFO delegates finance work to the Financial Analyst and Accounting Lead for cost
structure, pricing sensitivity, revenue model, unit economics, budget constraints, and
financial-scenario analysis. The CCO delegates communications work to the PR /
Communications Lead and Government Relations Lead for messaging, media relations,
crisis readiness, policy landscape, regulatory agenda, stakeholder alignment, and
government-affairs strategy analysis. The CHRO delegates people work to the HR Lead
and Culture / Recruitment Lead for workforce planning, talent pipeline, compensation
and compliance, recruitment, culture, retention, onboarding, training, and
employee-feedback analysis. The CLO delegates legal work to the General Counsel and
Public Policy / Compliance Lead for legal exposure, contract portfolio, regulatory
interpretation, litigation and disputes, corporate governance, jurisdiction scope,
policy landscape, compliance framework, regulatory-change register, ethics and
integrity controls, training records, audit findings, and government-relations context
analysis. Evidence-complete internal L3 matters receive a durable
consultation and may be closed by the CEO Agent; external actions, L4 matters,
emergencies, self-approval conflicts, missing consultation, and dissent fail closed.
Cross-functional consultation requirements are durable and fail closed. All
planned executive department runtimes are now implemented; the remaining held gate is
external validation.

**Goal:** Operate Global Mobility AIOS through a governed hierarchy of executive,
manager, and specialist agents, with the human owner acting as the Board.

### 13.0 Governance contract and stabilization dependency

- [ ] Complete the Phase 12 stabilization gate.
- [x] Adopt
  [AI_ORGANIZATION_GOVERNANCE_V13_0.md](AI_ORGANIZATION_GOVERNANCE_V13_0.md)
  as the canonical organizational runtime specification.
- [x] Define Board-reserved matters, executive authority, emergency escalation,
  and global shutdown rules.
- [x] Define what agents may never do, regardless of delegated authority.

### 13.1 Organization registry and position contracts

- [x] Add versioned organization, department, position, reporting-line, and
  agent-assignment records.
- [x] Upgrade the CEO and department-head role cards into executable position
  contracts containing mission,
  authority, tools, budget, inputs, outputs, KPIs, reports-to, direct reports,
  escalation triggers, and prohibited actions.
- [x] Register the CEO, CTO, COO, CMO, CPO, CFO, CCO, CHRO, and CLO as the
  initial executive council.
- [x] Register the existing Head of Product card under the CPO organization.
- [ ] Preserve position history when roles, reporting lines, or authority change.

### 13.2 Authority, risk, and executive decisions

- [x] Add a deterministic authority matrix with L1-L4 classifications.
- [x] Add durable organizational task, delegation, decision, escalation,
  override, and executive-decision ledgers.
- [x] Require every action to identify its accountable position, authority basis,
  evidence, confidence, impact, and rollback posture. Delegated organizational
  outputs satisfy this contract, and executable external paths require a durable
  human-review or approval receipt.
- [x] Prevent an agent from approving its own restricted recommendation.
- [x] Add deadlines, reminders, delegation expiry, and escalation-on-timeout.

| Level | Default owner | Typical scope |
|---|---|---|
| L1 | Specialist agent | Research, analysis, internal summaries, reversible routine updates |
| L2 | Manager or department head | Department workflows and bounded operational recommendations |
| L3 | Executive or CEO | Cross-department decisions and material but delegated operating changes |
| L4 | Human Board | Reserved matters, major spending, contracts, legal exposure, market entry, and irreversible actions |
| Emergency | CEO to Board immediately | Client harm, security incident, regulatory breach, financial loss, or serious reputation risk |

### 13.3 CEO and executive council runtime

- [x] Implement the CEO Agent as an orchestrator with no unrestricted direct
  action path.
- [x] Implement the COO department-head runtime with bounded Operations specialists.
- [x] Implement the CTO department-head runtime with bounded Technology specialists
  (VP Engineering and Lead Architect) for delivery, architecture, security, data,
  integration, and reversibility analysis.
- [x] Implement the CPO department-head runtime with bounded Product specialists
  (Product Manager and Design Agent) for product fit, scope, roadmap alignment,
  success metrics, design quality, UX research, and accessibility analysis.
- [x] Implement the CISO department-head runtime with bounded Security specialists
  (Security Lead and Threat Analyst) for security controls, attack surface, policy
  alignment, threat intelligence, prompt-injection, jailbreak, data-exfiltration,
  and compromised-agent indicator analysis.
- [x] Implement the Security Operations/SOC runtime under the CISO with bounded
  SOC specialists (SOC Lead and SOC Analyst) for agent-behavior monitoring, audit-log
  triage, incident coordination, and anomaly analysis.
- [x] Implement the CMO department-head runtime with bounded Marketing specialists
  (Creative Director and Marketing Manager) for brand fit, creative quality,
  messaging, audience alignment, channel fit, campaign plan, growth metrics, and
  budget-constraint analysis.
- [x] Implement the Finance/CFO bounded department runtime.
- [x] Implement the Communications/CCO bounded department runtime.
- [x] Implement the CHRO department-head runtime with bounded People specialists (HR Lead and Culture / Recruitment Lead).
- [x] Implement the CLO department-head runtime with bounded Legal specialists (General Counsel and Public Policy / Compliance Lead).
- [x] Let the COO delegate to registered direct reports and receive structured,
  evidence-grounded results.
- [x] Extend the same delegation contract to the CTO and CPO runtimes.
- [ ] Complete cross-functional executive consultation when an action touches
  multiple domains. The durable requirement and fail-closed ledger are delivered;
  executive completion and dissent-submission paths remain.
- [x] Escalate L4 matters, emergency risks, CEO self-approval conflicts, and
  recorded executive dissent to the Board.
- [ ] Add deadline-based escalation for unresolved executive consultations.

### 13.4 First autonomous organization flow

Prove the model with one bounded end-to-end workflow before expanding the org.

```text
Lead or case event
  -> COO classifies operational work
  -> Sales and Application Readiness agents execute bounded analysis
  -> COO resolves L1/L2 work
  -> CEO receives only L3 or cross-functional risk
  -> Board receives only L4 or emergency escalation
  -> every delegation, result, decision, and override is recorded
```

- [x] Consume an existing governed domain event idempotently.
- [x] Create an organizational task and delegate it to the correct specialist.
- [x] Record evidence-grounded outputs and confidence through the durable,
  idempotently keyed organizational action-output ledger.
- [x] Route L1/L2/L3/L4 outcomes according to the authority matrix.
- [x] Demonstrate timeout and escalation-on-timeout safety.
- [x] Enforce bounded retries, Board-controlled cancellation, durable execution
  attempts, retry scheduling, and duplicate-delivery/replay safety.
- [x] Prove that no client message, authority submission, payment, contract, or
  production deployment bypasses its required gate. Client delivery and authority
  submission validate durable approval receipts at execution time; payment,
  contract, and production-deployment executors remain unregistered and fail closed.

### 13.5 Board Room and executive reporting

- [x] Build a Board Room scaffold with pending Board decisions,
  material risks, organizational health, autonomous actions, and overrides.
- [x] Generate recurring, on-demand, and incident-triggered Board Packets.
- [x] Show the CEO recommendation, evidence, alternatives, expected impact,
  dissenting executive views, cost, urgency, and exact approval requested.
- [x] Complete all Board controls. Approve, reject, return-for-analysis, and
  global pause are implemented; override and per-agent suspension are now
  implemented too.
- [x] Notify the owner only for L4, emergency, overdue, or explicitly subscribed
  matters. (Escalation paths now route emergency and overdue items to the Board; explicit
  subscription and notification channel remain.)

### 13.5.1 Platform hardening and runtime registration checkpoint

Before activating another executive department, preserve the autonomy already
delivered while reducing insecure defaults and central runtime coupling. Marketing
remains delivered; this checkpoint gates Finance, Communications, People, and Legal.

- [x] Default unsigned header-role authentication to disabled and fail closed at
  production startup when authentication is disabled, header-role trust is enabled,
  or production credentials/signing secrets remain missing/default/too short.
- [x] Require production identity-document storage to use TLS-protected, non-default,
  pre-provisioned MinIO/S3-compatible storage with server-side encryption; local
  document storage is prohibited in production.
- [x] Add shared query ceilings for document/lead list paths that previously
  performed unbounded reads.
- [x] Replace inline FastAPI router registration with a declarative `RouterSpec`
  registry and replace path-role authorization branches with ordered declarative
  authorization rules.
- [x] Add a declarative `DepartmentRuntimeSpec` registry and common execution adapter
  covering Technology, Product, Security, Security Operations/SOC, and Marketing,
  so another department does not require another central execution/completion branch.
- [x] Add capability-boundary regression tests proving active departments execute
  only their explicitly allowed action class and held departments remain unavailable.
- [x] Add CI migration/roadmap consistency enforcement against the unique Alembic head.
- [x] Exclude local patch-backup directories from repository policy scans and future
  source control; existing tracked backups must be removed from the Git index once.
### 13.5.2 External mobility validation framework

Phase 13.10.2 turns the pre-department-expansion customer-validation requirement into
repeatable, auditable infrastructure rather than an informal feedback exercise.

- [x] Persist versionable validation scenarios without embedding the expected legal answer.
- [x] Persist validation runs pinned to the scenario, lead, and exact pathway comparison shown to testers.
- [x] Capture durable evidence references for Truth Claims, Verified Rules, Official Sources,
  immutable Source Snapshots, pathway versions, pathway comparisons, documents, and notes.
- [x] Fail closed when the pinned comparison, primary pathway version, verified-rule set,
  jurisdiction/domain, official-source lineage, source snapshots, or lead-scoped Truth Claim
  do not form one coherent governed evidence graph.
- [x] Capture external-human mobility-user and professional/operator reviews separately from
  the internal actor who records them. AI agents cannot self-create the required review pair.
- [x] Record Critical/High/Medium/Low findings with explicit triage and remediation state.
- [x] Enforce that Critical and High findings must be resolved; only Medium/Low findings may
  receive explicit Human Board risk acceptance.
- [x] Calculate a deterministic `held` / `failed` / `passed` gate receipt and record founder
  intervention count as an autonomy metric.
- [x] Add a small operator validation workspace and an Austria first-scenario fixture/template.
- [ ] Complete the first real external run and attach the external reviewer evidence.
- [ ] Resolve/retest every Critical/High issue, triage remaining Medium/Low issues, and record
  a PASS receipt.

The framework is described in
[EXTERNAL_MOBILITY_VALIDATION_V13_10_2.md](EXTERNAL_MOBILITY_VALIDATION_V13_10_2.md).

### 13.10.2.1 PostgreSQL migration portability hardening

The Phase 13.10.2 validation dry run exercised the persistent PostgreSQL
database and exposed migration portability defects that the SQLite development
path had not detected. The schema head remains
`0068_external_validation_framework`; this slice corrects historical migration
execution without introducing a new schema revision.

- [x] Back up the persistent PostgreSQL database before migration repair.
- [x] Replace PostgreSQL-incompatible integer Boolean defaults in
  `0058_deadline_emergency_escalation` with dialect-safe `sa.false()`.
- [x] Preserve native UUID binding for `organization_positions.id` in
  `0065_security_runtime_contract`, `0066_soc_runtime_contract`, and
  `0067_marketing_runtime_contract`.
- [x] Add regression coverage preventing integer Boolean migration defaults and
  VARCHAR bindings for the UUID organization-position identifier.
- [x] Upgrade the historical PostgreSQL database transactionally from
  `0056_ai_organization_governance` through
  `0068_external_validation_framework`.
- [x] Confirm the governed data set survives unchanged: 292 jurisdictions,
  89 official sources, 521 source snapshots, 86 verified rules,
  1 mobility pathway, and 2 mobility pathway versions.
- [x] Confirm the unique Alembic head remains
  `0068_external_validation_framework`.
- [x] Run the complete release gate: **534 tests passed, 0 failed** and the
  complete local quality gate passed.
- [x] Release-close the portability hardening before resuming the Austria
  external-mobility validation run.

### 13.10.2.10 Austria intake and shadow-validation unblocking

The first strict simulated pre-validation run exposed that the Austria
skilled-employment scenario cannot be reached through the public-intake front door.
This slice fixes the immediate blocker while keeping the Austria pathway version in
its existing `draft` state and without approving any pending source certifications.

- [x] Add Austria as a first-class target-country option in the public-intake form.
- [x] Normalize Austria selection to jurisdiction `AT` on intake submission.
- [x] Capture skilled-employment case facts in public intake:
  current country, job-offer status, qualification-recognition state, and language level.
- [x] Store the structured case facts in the lead notes and intake-session answers.
- [x] Provide an Austria-specific success message and checklist while keeping the
  pathway explicitly in `draft` / internal-review state.
- [x] Add regression tests proving Austria intake normalizes to jurisdiction `AT`
  and persists the new case facts.
- [ ] Re-run both simulated testers from a fresh Austria intake without founder hints.
- [ ] Address the next set of findings in the screens now reachable after intake.

#### Phase 13.10.2.10 closure evidence

- [x] Complete verification passed with **628 API tests, 0 failed**, with only the
  existing Starlette TestClient/httpx deprecation warning.
- [x] Web production build passed with 37 routes.
- [x] No schema migration or pathway publication was introduced.
- [x] Simulated pre-validation findings are recorded in the external-validation
  ledger as internal-only; no external human reviews were created and the external
  gate remains `held`.
- [x] The Austria 2026 source certifications, pathway v3, and external-validation
  gate remain unchanged and held.

### 13.10.2.12 Intake persistence and case continuity

The first end-to-end Round 3 attempt reached the public-intake persistence boundary
and exposed a schema-validation break before router execution: optional blank email
was serialized as an empty string and rejected by `EmailStr`. This slice repairs that
boundary and carries the resulting durable Lead through the downstream workflow
without weakening production email semantics or publishing draft pathway evidence.

- [x] Normalize blank optional contact values in the frontend request and backend
  pre-validation path while retaining strict malformed-email rejection.
- [x] Commit exactly one Lead and one linked IntakeSession atomically and return the
  durable Lead ID explicitly with a human-readable case reference.
- [x] Add a frontend-generated submission key plus backend request fingerprint and
  unique database guarantee for idempotent replay and duplicate protection.
- [x] Add migration `0072_intake_submission_idempotency`.
- [x] Preserve normalized Austria target country and submitted case facts.
- [x] Add a successful case-created screen with a `Continue your case` handoff to
  `/eligibility?lead_id=<id>`.
- [x] Propagate `lead_id` to Mobility Profiles, Mobility Planning, and External
  Validation and auto-select the same Lead in each workspace.
- [x] Replace the normal External Validation raw-UUID interaction with a named Lead
  selector while retaining manual UUID entry as an advanced/debug fallback.
- [x] Preserve published-pathway-only production matching; internal draft simulation
  remains explicit, labelled, and non-publishing.
- [x] Add false-success, email-boundary, persistence, fact-retention, list-visibility,
  idempotency, and conflicting-key regression coverage.
- [x] Complete automated verification: **648 API tests**, **13 focused tests**,
  **4 fresh-migration tests**, TypeScript, Next.js production build, and diff check.
- [x] Back up live PostgreSQL and migrate it transactionally from 0071 to 0072.
- [x] Restart the API on 8002 and frontend on 3000 with the local API override; API
  health and authenticated Lead listing return successfully.
- [x] Complete the authorized one-case rendered intake-to-downstream continuity
  smoke after browser-harness recovery. The same named Austria case reached
  Eligibility and auto-selected in Profiles, Planning, and External Validation;
  normal workflow navigation required no raw Lead UUID.

#### Phase 13.10.2.12 live release evidence

- [x] Pre-migration PostgreSQL backup created and SHA-256 recorded in release handoff.
- [x] Direct Alembic and PostgreSQL checks report
  `0072_intake_submission_idempotency`.
- [x] Post-migration `/health` returns `ok`; authenticated `/api/v1/leads` is reachable.
- [x] One synthetic Austria submission creates one durable Lead and one linked
  IntakeSession and reaches the same named case in Eligibility, Profiles, Planning,
  and External Validation without a required raw UUID.
- [x] Close Phase 13.10.2.12 after the rendered smoke passes. Direct PostgreSQL
  verification confirms exactly one Lead and one linked IntakeSession for case
  reference `AT-64A2DA29`; no validation round was started.

### 13.10.2.13 Austria candidate integrity and occupation resolution

Round 4 proved that durable case continuity was working but recommendation quality
was not yet defensible: a country-only self-employment route could lead a skilled-
employment case, structured intake facts did not drive the assessment, occupation
applicability was flattened, and the rendered comparison could report zero meaningful
gaps. This slice repairs that decision boundary before Phase 13.16 begins.

- [x] Persist nationality, current country, occupation, experience, job-offer state,
  qualification-recognition state, German level, and employment province on Lead;
  backfill them from durable IntakeSession answers without parsing free-text notes.
- [x] Merge Lead, IntakeSession, and profile facts deterministically for eligibility
  and pathway comparison, preserving explicit intake facts when profile fields are blank.
- [x] Add candidate compatibility and machine recommendation states; skilled-employment
  cases retain self-employment routes as `EXCLUDED` with an audit-visible reason and a
  zero ranking score rather than silently recommending or deleting them.
- [x] Add structured Austria occupation assessment with exact, normalized-exact,
  inferred, ambiguous, no-match, and insufficient-information qualities; national and
  regional scope, province, entry, source snapshot, source certification, and
  qualification mapping remain separate, and the result never establishes eligibility.
- [x] Rebuild the skilled-worker assessment around categorized fact, evidence,
  document, regulatory, and certification gaps; a missing binding job offer is a
  material blocking fact, and a claimed A2 level is not a language certificate.
- [x] Scope the governed EUR 218 value to the government application fee only;
  estimated total cost and processing time remain `not_established` absent governed data.
- [x] Enable explicitly requested local internal simulation for authenticated
  admin/operator/reviewer roles while production remains fail-closed unless its feature
  flag is enabled; require an explicit context and audit actor, role, Lead, draft version,
  timestamp, simulation flag, and reason.
- [x] Create the next immutable Austria skilled-worker draft through the existing
  structured-evidence integration path. It pins core, national-2026, and regional-2026
  evidence; certification remains pending, publication readiness remains false, and no
  production recommendation or publication occurs.
- [x] Render candidate status, exclusion reasons, draft/non-reliance warnings,
  occupation ambiguity, categorized gaps, sourced application-fee semantics,
  unestablished timing, and case-driven next actions in Mobility Planning.
- [x] Add legal-certainty and decision-integrity regressions, including structured
  fact propagation, goal incompatibility, occupation ambiguity/scope, pending
  certification, nonzero case gaps, missing-job-offer treatment, fee provenance,
  missing timing, safe wording, production-only default matching, simulation audit,
  and unauthorized-role rejection.
- [x] Verification passes with **650 API tests**, **4 fresh-migration tests**, Python
  compilation, the 37-route Next.js production build, and `git diff --check`.
- [x] Back up live PostgreSQL, migrate it transactionally to
  `0073_austria_candidate_integrity`, and create immutable Austria pathway v4
  `4f02f390-1e22-4ac3-9237-8a67f6551807`. Re-running the integration returns the
  same version with `created=false`.
- [x] Complete authenticated live simulation verification against the persisted
  Austria smoke case: v4 is the non-production simulation candidate; Self-employed
  Key Worker is excluded for goal mismatch; `Software Engineer` resolves as
  `AMBIGUOUS` across two national governed entries while regional scope remains a
  distinct `NO_MATCH`; the absent job offer and 14 categorized gaps are rendered;
  fee/timing semantics remain bounded; and the full simulation context is audited.
- [x] Verify ordinary live matching returns published versions only and zero draft
  versions. No certification state or publication lifecycle was changed.
- [x] Complete the fresh case-specific Round 5 mobility-user and professional shadow
  assessment. Its decisive disposition requires Phase 13.10.2.14 before Phase 13.16;
  no certification approval or pathway publication was authorized.

### 13.10.2.14 Assessment consistency and conditionality hardening

Round 5 found that the candidate boundary was close but not professionally
defensible: a stale raw fee could render as EUR 21,800, unknown province could be
flattened to regional no-match, trace provenance required reconstruction, excluded
self-employment documents could contaminate a skilled-employment preview, and the
rendered evidence-gap/profile provenance could diverge from the canonical response.

- [x] Normalize monetary inputs by explicit unit semantics, let the governed
  source-pinned application-fee rule override stale application-fee aliases once,
  and clear payable cost components from excluded routes.
- [x] Preserve regional candidate conditionality for unknown, applicable,
  non-applicable, and truly absent province/evidence states.
- [x] Expose complete material-conclusion provenance in Mobility Planning, including
  full rule/source/snapshot/certification identifiers, official sources, deterministic
  evidence-pack hashes, and exact certification-review navigation without changing
  certification state.
- [x] Isolate eligibility documents to compatible routes so self-employment
  requirements cannot leak into a skilled-employment assessment.
- [x] Persist the structured assessment input as Mobility Profile v1, and use the
  canonical categorized gap list for the response, explanation, tradeoffs, and UI.
- [x] Complete focused, adjacent, full API, fresh-migration, TypeScript, production-
  build, repository, release, migration, Docker-profile, compilation, and whitespace
  verification. No schema migration was added; Alembic remains at 0073.
- [x] Complete live integration against existing case `AT-7811EDF4`: Profile v1,
  the canonical 14 gaps, EUR 218 fee, conditional regional candidate, full evidence
  traces, excluded-route cost isolation, draft lifecycle, and pending certification
  states are confirmed in the persistent PostgreSQL environment.
- [ ] Complete the focused rendered smoke. Both frontend routes return HTTP 200, but
  this session exposed no browser surface for visual/interactive inspection.
- [x] Execute a fresh case-specific Round 6 mobility-user shadow review followed by
  a separate professional shadow review and record the
  [PASS correctness disposition](ROUND_6_CORRECTNESS_DISPOSITION_V13_15.md).
  Phase 13.16.0 is unlocked but not started; source certification and publication
  remain outside this slice.

### 13.10.2.15 Eligibility preview consistency

The manual Phase 13.10.2.14 rendered smoke found two bounded consistency defects:
Eligibility was still rendering documents from an excluded self-employment route
and presenting a binding Austrian job offer as optional, while Planning repeated a
legacy sentence that treated linked but pending 2026 occupation evidence as absent.

**Status: COMPLETE — manual rendered gate PASS.** Findings `R5A-002`,
`13.10.2.15-F01`, and `13.10.2.15-F03` are resolved. Austria v4 remains draft and
both national/regional certifications remain `pending_review`.

- [x] Restrict eligibility-preview documents, material requirements, and costs to
  compatible pathway candidates while retaining excluded candidates for audit and
  explanation with an explicitly empty preview contribution.
- [x] Represent the binding Austrian job offer as a required, missing, blocking
  material fact, separate from the employer-declaration document requirement; remove
  the generic `if available` job-offer wording.
- [x] Reconcile legacy occupation-risk wording with the national/regional evidence
  roles currently linked to v4 and their `pending_review` certification states.
- [x] Preserve the Phase 13.10.2.14 fee, total-cost, processing-time, profile-version,
  14-gap, occupation-conditionality, exclusion, traceability, certification,
  lifecycle, publication-readiness, and production/draft-boundary invariants.
- [x] Complete focused, adjacent, full API, clean migration-cycle, TypeScript,
  production-build, compilation, repository, release, migration, Docker-profile,
  and whitespace verification. No migration was added; Alembic remains at 0073.
- [x] Record rendered gate **FAIL**, finding `13.10.2.15-F01`: GET latest and POST
  evaluate both returned 401 without `x-gmai-role`/`x-gmai-user`; Eligibility
  business content was not assessed. API runtime/auth and the other operator
  workspaces remained healthy.
- [x] Remediate the centralized client configuration boundary so an explicitly
  enabled role/user configuration or an unset configuration with a loopback API
  receives local header-role auth. Explicit false and non-loopback production remain
  fail-closed; credentials/CORS behavior is unchanged and no Eligibility-specific
  auth implementation was introduced.
- [x] Record that the first F01 remediation failed its manual retest: GET latest and
  POST evaluate remained 401 and both browser auth headers remained absent.
- [x] Replace the inline client-header expression with one native-`Headers` final
  request builder and add runtime mocked-fetch coverage through the actual exported
  Eligibility functions. Four tests prove enabled local GET/POST headers, explicit-
  false removal, non-loopback production fail-closed behavior, credentials, and
  request-specific header preservation.
- [x] Record that the second F01 remediation also failed rendered verification after
  a deleted `.next` output, clean frontend restart, and fresh tab: both calls remained
  401 and both headers remained absent. Stale client/runtime state is ruled out.
- [x] Resolve browser-visible auth settings in a Next.js-compiled TypeScript module
  using direct static `NEXT_PUBLIC_*` references and pass the resolved configuration
  into the environment-agnostic request builder. Add a compiled Eligibility-client
  regression that proves the local API base, enabled flag, role, and user are embedded
  on the same real GET/POST browser code path, while retaining the final-fetch tests.
- [x] Close F01's client-side diagnosis: loopback browser instrumentation proves the
  resolved configuration, request builder output, and final native-fetch input all
  contain `x-gmai-role: admin` and `x-gmai-user: frontend-operator`. Keep the temporary
  redacted diagnostic until the rendered Eligibility gate passes.
- [x] Record `13.10.2.15-F03`: Eligibility remains unusable in the browser because
  auth-generated responses bypassed CORS decoration. OPTIONS itself already returned
  200 with the configured local origin and requested headers; authentication was the
  outer middleware, causing its 401/403 responses to omit CORS response headers.
- [x] Make CORS the outer response boundary and explicitly allow the approved browser
  headers. Regressions prove successful local GET/POST preflight, authenticated route
  reachability, retained unauthorized-request rejection, and unapproved-origin denial.
  Production authentication and configured-origin boundaries remain fail-closed.
- [x] Pass the final manual rendered gate. Eligibility shows the missing blocking
  binding Austrian job offer and separate employer declaration without excluded
  self-employment documents or obsolete optional wording. Planning accurately states
  that linked 2026 national/regional evidence remains pending independent certification.
- [x] Resolve `R5A-002`, `13.10.2.15-F01`, and `13.10.2.15-F03`; remove the temporary
  browser diagnostic, global debug object, diagnostic revision marker, and diagnostic-
  only test while retaining the permanent centralized request/auth and CORS fixes.
- [x] Prepare the existing live case for that retest by persisting new audited
  Eligibility and Planning assessments with the corrected projections; all older
  assessments remain in history.

### 13.16 Organization Observatory & Experience Layer

**State: IN PROGRESS — 13.16.0 CLOSED / PASS; 13.16.1 DESIGN, 13.16.1A
PERSISTENCE, 13.16.1B COMMAND/SERVICE LAYER, 13.16.1C AUTHENTICATED ORGANIZATION
API, AND 13.16.1D0 EMITTER MAPPING/DESIGN COMPLETE; 13.16.1D1 CALLER-OWNED
TRANSACTION STAGING COMPLETE / PASS; 13.16.1D2 SOURCE-CERTIFICATION EMISSION
COMPLETE / PASS; FIRST BOUNDED RUNTIME CONTRIBUTION EMITTER ACCEPTED; 13.16.1D3A INITIAL-RULE / VERIFIED-RULE PUBLICATION COMPLETE / PASS; 13.16.1D3B REGULATORY-CHANGE PUBLICATION COMPLETE / PASS; 13.16.1D3C PATHWAY PUBLICATION COMPLETE / PASS; 13.16.1D4 DEFERRED-DOMAIN / INTEGRATED REGRESSION COMPLETE / PASS; 13.16.1E0
OBSERVATORY/READ-MODEL RECONCILIATION DESIGN COMPLETE; 13.16.1E1 SAFE SNAPSHOT /
RECONCILIATION READ API COMPLETE / PASS; E2 ACTIVITY COVERAGE COMPLETE / PASS; E3 IN PROGRESS — E3A WRITER AUDIT/COVERAGE-EPOCH DESIGN COMPLETE; E3B WORKITEM ADAPTERS UNLOCKED / NOT STARTED.** The
fresh Round 6 mobility-user and professional shadow reviews passed the correctness
gate, and Phase 13.16.0 implementation plus independent internal rendered acceptance
are complete. Phase 13.17 external-human acceptance is not satisfied.
The first manual rendered attempt failed because a long-running Next.js development
server was using `.next` while a production build replaced that generated output.
A bounded cache clear and development-server restart restored the affected routes and
assets; an independent rendered re-test is still required.
The subsequent clean-runtime desktop review rendered successfully and identified
`13.16.0-RV-01` through `13.16.0-RV-05`: Eligibility action ordering and plain-language
gap presentation, conventional Board executive acronyms, Agent Console lead-row
layout, and the Validation simulation checkbox. Bounded presentation remediation is
implemented. Desktop re-test of those corrections plus mobile/narrow, dark-theme,
keyboard/focus, provenance-disclosure, identifier-wrapping, and warning-visibility
acceptance remain pending.
The final bounded acceptance remediation also addresses `13.16.0-RV-06` through
`13.16.0-RV-08`: the Planning mobile summary and simulation control now have explicit
narrow-layout structure; the closed mobile rail and Agent Console run history are
isolated from one another; and the duplicate `public/icon.svg` route conflict is
removed in favor of the App Router icon. Independent re-inspection confirmed all
eight rendered findings are resolved and pass.
That spot check found one repeatable Planning console 404 from a redundant optional
country-ranking `latest` lookup. The backend correctly represented the Round 6 case's
absence of ranking assessments, but the page already fetched descending ranking
history and could derive the latest item from it. The bounded client correction removes
the duplicate lookup and retains an empty ranking state when history is empty. Final
inspection confirmed the repeated console 404 is resolved without changing backend
latest-record semantics.

Phase 13.16.0 final disposition is **CLOSED / PASS**:

- Implementation: **COMPLETE**.
- Independent internal rendered acceptance: **PASS**.
- Overall Phase 13.16.0 state: **CLOSED**.
- Next slice: Phase 13.16.1 Durable Contribution & Activity Model — **IN PROGRESS;
  DESIGN, 13.16.1A PERSISTENCE, 13.16.1B COMMAND/SERVICE, 13.16.1C AUTHENTICATED
  ORGANIZATION API, AND 13.16.1D0 EMITTER MAPPING/DESIGN COMPLETE; 13.16.1D1
  TRANSACTION STAGING COMPLETE / PASS; 13.16.1D2 SOURCE-CERTIFICATION EMISSION
  COMPLETE / PASS; FIRST BOUNDED RUNTIME EMITTER ACCEPTED; 13.16.1D3A INITIAL-RULE / VERIFIED-RULE PUBLICATION COMPLETE / PASS; 13.16.1D3B REGULATORY-CHANGE PUBLICATION COMPLETE / PASS; 13.16.1D3C PATHWAY PUBLICATION COMPLETE / PASS; 13.16.1D4 DEFERRED-DOMAIN / INTEGRATED REGRESSION COMPLETE / PASS; 13.16.1E0
  OBSERVATORY/READ-MODEL RECONCILIATION DESIGN COMPLETE; 13.16.1E1 SAFE SNAPSHOT /
  RECONCILIATION READ API COMPLETE / PASS; E2 ACTIVITY COVERAGE COMPLETE / PASS; E3 IN PROGRESS — E3A WRITER AUDIT/COVERAGE-EPOCH DESIGN COMPLETE; E3B WORKITEM ADAPTERS UNLOCKED / NOT STARTED**.
- Phase 13.17 genuine external-human acceptance: **still required**.
- Phase 14: **locked**.

The accepted foundation establishes Geist Sans for product text, Geist Mono for
technical values, shared typography, spacing, surfaces, semantic states, layouts,
cards, forms, badges, tables, empty/loading states, inline notices, technical
provenance disclosure, a consistent responsive workspace shell, and the hierarchy
**decision/context → blockers → next actions → supporting evidence → technical
provenance**. Mobility User, Professional/Operator, and Owner/Board presentation
foundations now share this grammar while preserving governance and safety warnings.

Rendered finding disposition:

- `RV-01` Eligibility hierarchy — **RESOLVED / PASS**.
- `RV-02` raw internal vocabulary in primary Eligibility presentation — **RESOLVED /
  PASS**.
- `RV-03` Board Room executive acronym casing — **RESOLVED / PASS**.
- `RV-04` Agent Console lead layout — **RESOLVED / PASS**.
- `RV-05` Validation checkbox layout — **RESOLVED / PASS**.
- `RV-06` Planning mobile summary and simulation control — **RESOLVED / PASS**.
- `RV-07` Agent Console mobile shell/history overlap — **RESOLVED / PASS**.
- `RV-08` duplicate `/icon.svg` HTTP 500 — **RESOLVED / PASS**; `/icon.svg` returns
  HTTP 200 from the canonical App Router asset.
- Final Planning country-ranking lookup defect — **RESOLVED / PASS**. Planning no
  longer redundantly requests both history and `/country-rankings/{lead_id}/latest`;
  optional latest state is derived from `history[0]`, or `null` for empty history.

Independent internal rendered acceptance matrix:

| Surface or behavior | Result |
|---|---|
| Desktop acceptance surfaces | PASS |
| Eligibility responsive at 390px | PASS |
| Planning responsive at 390px | PASS |
| Agent Console responsive at 390px | PASS |
| Planning dark theme | PASS |
| Eligibility dark theme | PASS |
| Board Room acronyms | PASS |
| Validation form control | PASS |
| Agent Console Leads | PASS |
| Agent Console Recent agent runs | PASS |
| Technical provenance visible focus | PASS |
| Technical provenance keyboard activation with Enter/Space | PASS |
| Technical provenance identifier wrapping | PASS |
| Page-level horizontal overflow in tested narrow surfaces | NONE / PASS |
| `/icon.svg` | HTTP 200 / PASS |
| Normal Agent Console console state | No errors / PASS |
| Final Planning redundant country-ranking 404 | RESOLVED / PASS |

This is internal rendered acceptance only. It is not genuine external-human
acceptance and does not satisfy Phase 13.17.

#### 13.16.1D0 authoritative emitter mapping / transaction gate

**State: DESIGN COMPLETE / RUNTIME IMPLEMENTATION NOT STARTED.** Repository-backed
inspection of the real domain outcome services confirms that real Contribution
emission must not be wired directly onto the current standalone command contract.
`create_contribution()` owns `session.commit()` through `commit_mutations()`, while the
source domain services also own their authoritative commits. Calling Contribution
after a source commit would be an unsafe best-effort dual write; calling the current
command before the source commit would make the nested service unexpectedly commit
the caller's pending transaction. 13.16.1D1 therefore must add a caller-owned staging
path so source transition + source audit + Contribution + Contribution audit commit
atomically or roll back together. A new durable outbox is not required for the first
adapters because these records share the same relational database.

Emitter classification from the design pass:

- `ExecutiveDecision` terminal approved/rejected remains an eligible source but
  **EXPLICIT COMMAND ONLY**; Decision and Contribution stay distinct.
- `JurisdictionSourceCertification` approved/rejected review is the recommended first
  real adapter after D1, with structured evidence-pack and independent-human review
  requirements preserved. Pending/superseded certification emits nothing.
- Published `InitialRuleAssertion`/`VerifiedRule`, published `RegulatoryChange`, and
  published `MobilityPathwayVersion` are eligible later publication adapters with
  narrow organizational semantics only.
- `JurisdictionImmigrationAssessment`, `ReassessmentAcceptance`,
  `ExternalValidationRun`, `CorporateComplianceEvent`, `MobilityTimelineMilestone`,
  and agency/appointment records are deferred until their remaining audit, actor,
  evidence, or external-verification contracts are strong enough.
- Eligibility, pathway comparison, country ranking, raw source retrieval/snapshots,
  external-validation component reviews/findings, AgentRun/WorkflowRun, attempts,
  tools/LLM calls, AuditLog, retries, messages, and UI interactions cannot directly
  authorize Contribution.

Round 6 Austria v4 remains a zero-emitter safety pin: draft,
`simulation_candidate`, `INTERNAL_SIMULATION_ONLY`, unpublished/not-ready, national
and regional certification `pending_review`, job offer absent/blocking, occupation
`AMBIGUOUS`, regional result `INSUFFICIENT_INFORMATION`, qualification mapping
`UNRESOLVED`, EUR 218, 14 gaps, and human review required. No current Round 6 record
may emit “eligibility established”, “occupation confirmed”, “source certified”, or
“pathway published”.

Required implementation order:

1. 13.16.1D1 transaction composability correction — **COMPLETE / PASS**; no source-policy expansion.
2. 13.16.1D2 source-certification review adapter — **COMPLETE / PASS**.
3. 13.16.1D3A initial-rule / VerifiedRule publication adapter — **COMPLETE / PASS**.
4. 13.16.1D3B regulatory-change publication adapter — **COMPLETE / PASS**.
5. 13.16.1D3C pathway-version publication adapter — **COMPLETE / PASS**.
6. 13.16.1D4 deferred-domain review plus integrated emitter regression — **COMPLETE / PASS**.
7. 13.16.1E0 Observatory/read-model source reconciliation design — **COMPLETE**; 13.16.1E1 safe snapshot + Contribution reconciliation read API — **COMPLETE / PASS**; 13.16.1E2 Activity staging/semantic coverage — **COMPLETE / PASS**; 13.16.1E3 legacy-writer reconciliation / Activity-coverage closure — **IN PROGRESS; E3A DESIGN COMPLETE, E3B UNLOCKED / NOT STARTED**.

#### 13.16.1D1 caller-owned transaction staging

**State: COMPLETE / PASS.** The bounded D1 patch adds an
internal `stage_mutations()` primitive plus explicit `stage_contribution()` and
`stage_contribution_correction()` integration paths. These paths flush the domain row
and its audit record but never commit, refresh, or roll back the caller's session.
The existing standalone Contribution commands retain commit-on-command behavior and
safe replay semantics. No `commit=False` public bypass, source-policy expansion,
real emitter, migration, persistence-model change, router change, or Observatory work
is included.

D1 acceptance proved caller-owned rollback across source + source audit + Contribution
+ Contribution audit, audit-failure propagation without an inner commit, final-commit
rollback, idempotent replay without duplicate audit, fail-closed semantic conflict,
correction rollback, and unchanged standalone API behavior. Local verification passed
8/8 focused D1 transaction tests, 50 passed + 1 expected PostgreSQL-only skip in the
focused service/API/platform regression, and 722 passed + 1 expected PostgreSQL-only
skip in the complete API suite. Repository policy, release consistency, migration
consistency, and `git diff --check` pass at Alembic head
`0074_durable_contribution_activity_model` with 118 registered tables. D2 is therefore
unlocked but not started.

#### 13.16.1D2 source-certification review Contribution adapter

**State: COMPLETE / PASS.** The first real domain emitter is
restricted to the existing authenticated source-certification review boundary. The
review route supplies trusted reviewer/admin identity to a source-specific organization
adapter; business payloads cannot choose Contribution actor, role, authority, or tenant.
The generic organization Contribution POST remains ExecutiveDecision-only.

For terminal `approved`/`rejected` `JurisdictionSourceCertification` reviews, D2 stages
exactly one `source_certification_review_completed` Contribution before the source
service's single outer commit. Structured review still requires the deterministic
evidence-pack hash, pinned immutable source snapshot, independent-human attestation, and
separate proposer/reviewer. Pending and superseded certification do not emit. The
Contribution wording is organizational only and explicitly does not establish applicant
eligibility, occupation eligibility, or pathway publication.

The transition, existing source-review audit, Contribution, and Contribution audit share
one transaction. Emitter or authority failure rolls back the certification review and
all related audit/Contribution rows. Deterministic source version and Contribution key
protect replay; legacy direct service calls without trusted HTTP reviewer-role context
retain their prior no-emitter behavior. No migration, persistence model, Observatory,
publication adapter, eligibility/pathway emitter, or Round 6 state change is included.

D2 acceptance is complete. Local verification passes **8/8** focused emitter tests,
**12/12** existing structured source-certification evidence-pack tests, **58 passed + 1
expected PostgreSQL-only skip** in the D1/organization service/API/platform regression,
and **730 passed + 1 expected PostgreSQL-only skip** in the complete API suite. Repository
policy, release consistency, migration consistency, and `git diff --check` pass at
Alembic head `0074_durable_contribution_activity_model` with 118 registered tables. The
replay defect found during acceptance was corrected by normalizing reviewed timestamps
to a DB-stable UTC representation before canonical fingerprinting; replay now remains
idempotent across SQLite persistence/reload. D3A is COMPLETE / PASS; D3B is COMPLETE / PASS; D3C is COMPLETE / PASS; D4 is COMPLETE / PASS.

#### 13.16.1D3A initial-rule / VerifiedRule publication Contribution adapter

**State: COMPLETE / PASS.** D3A connects only the existing
authenticated initial-rule publication endpoint to the durable Contribution ledger.
The generic `/api/v1/organization/contributions` command remains
ExecutiveDecision-only; a separate sealed publication validator is used by the domain
integration path.

Only an `InitialRuleAssertion` that has already passed independent review and the
existing approved coverage/source-certification, immutable-snapshot, confidence,
attestation, and proposer/publisher-separation gates can emit. After the publication
workflow stages the new active `VerifiedRule`, marks the assertion `published`, projects
the rule into the regulatory knowledge graph, and records its existing publication and
coverage-reconciliation audits, D3A stages one
`verified_rule_publication_completed` Contribution before the single outer commit.
Source transition, graph projection, source audits, Contribution, and Contribution audit
therefore commit or roll back as one unit.

The Contribution source is the published `InitialRuleAssertion`, bound to its assertion
SHA-256 and material `VerifiedRule` publication state. The adapter verifies exact
jurisdiction, official-source, immutable-snapshot, rule-key/domain, statement,
confidence, effective-period, publisher, and publication-time provenance. Its wording
records governed regulatory-knowledge publication only and explicitly does not establish
applicant eligibility, occupation eligibility, visa approval, or pathway publication.
Already-published legacy records are not backfilled. Direct service calls without trusted
publisher-role context preserve their prior no-emitter behavior.

Focused coverage is included for authenticated publication emission and HTTP replay,
persisted adapter replay, fail-closed published-source drift, and atomic rollback on
Contribution staging failure. Local acceptance passed 8/8 focused initial-rule tests,
4/4 coverage-reconciliation tests, 78 passed + 1 expected PostgreSQL-only skip in the
combined D1/D2/organization service/API/platform regression, and 734 passed + 1 expected
PostgreSQL-only skip in the complete API suite. Repository policy, release consistency,
migration consistency, and `git diff --check` pass at Alembic head
`0074_durable_contribution_activity_model` with 118 registered tables. D3B
regulatory-change publication is COMPLETE / PASS; D3C pathway publication is
COMPLETE / PASS and D4 is COMPLETE / PASS.

#### 13.16.1D3B regulatory-change publication Contribution adapter

**State: COMPLETE / PASS.** D3B connects only the existing
authenticated regulatory-change publication endpoint to the durable Contribution ledger.
The generic `/api/v1/organization/contributions` command remains ExecutiveDecision-only;
a separate sealed regulatory-change publication validator is used by the domain
integration path.

Only a previously reviewed `approved` `RegulatoryChange` backed by its current hashed
`SourceSnapshot` may emit. The HTTP request `reviewer` identity must match the
authenticated publisher, and that authenticated actor is used for resulting
`VerifiedRule.approved_by`, graph projection, supersession attribution where present,
publication audit, and Contribution attribution. Detection, classification, pending or
rejected review, and approved-but-unpublished state remain non-emitting.

The source workflow owns one transaction across the change `published` transition,
resulting `VerifiedRule`, optional prior-rule supersession/deactivation, regulatory
knowledge-graph projection, existing publication/supersession audits, one staged
`regulatory_change_publication_completed` Contribution, and its audit. Emitter or final
commit failure rolls the entire unit back. Already-published records return through the
existing idempotent branch without historical Contribution backfill.

The sealed validator requires internal-human admin/reviewer authority, prior review
attribution, a hashed current source snapshot, and exact change/rule jurisdiction,
official-source, snapshot, domain, publisher, and publication-time lineage. Contribution
semantics record governed regulatory-knowledge publication only and explicitly do not
establish applicant eligibility, occupation eligibility, visa approval, or pathway
publication. Focused D3B tests cover pre-publication no-emission, authenticated atomic
emission, HTTP and adapter replay, fail-closed rule drift, emitter rollback, publisher
spoofing rejection, and confirmation that the generic source policy remains closed. Local
acceptance passes **8/8** focused D3B emitter tests, **9/9** existing regulatory-
intelligence/knowledge-graph/pathway-impact regression tests, **86 passed + 1 expected
PostgreSQL-only skip** in the combined D1-D3A/organization regression, and **742 passed
+ 1 expected PostgreSQL-only skip** in the complete API suite. Repository policy,
release consistency, migration consistency, and `git diff --check` pass at Alembic head
`0074_durable_contribution_activity_model` with 118 registered tables. D3C pathway
publication is now COMPLETE / PASS and D4 is COMPLETE / PASS.

#### 13.16.1D3C pathway-version publication Contribution adapter

**State: COMPLETE / PASS.** D3C connects only the existing
authenticated `MobilityPathwayVersion` publication endpoint to the durable Contribution
ledger. The generic `/api/v1/organization/contributions` command remains
ExecutiveDecision-only; a separate sealed pathway-publication validator is used by the
domain integration path.

Only a draft pathway version that passes the existing publication evidence gate can
emit. The gate continues to enforce governed official-source/snapshot links, active
human-published `VerifiedRule` provenance, required source certification, and the
structured national/regional occupation evidence required by the Austria RWR shortage
pathway. The publisher must remain distinct from the version creator. Existing
admin/operator publication authorization is preserved and the authenticated role is now
passed into the trusted organization adapter. Draft/internal-simulation, retired, and
unpublished versions remain non-emitting.

The pathway catalogue owns one transaction across supersession of any currently
published predecessor, the selected version's `published` transition, parent pathway
activation, the existing `mobility_pathway_version_published` audit, one staged
`pathway_version_published` Contribution, and the Contribution audit. Emitter or final
commit failure rolls the entire publication unit back. Direct service callers that omit
trusted publisher-role context preserve their previous no-emitter behavior, so D3C does
not backfill historical pathway publications.

The sealed validator reuses the catalogue's exact publication-evidence blocker contract
after the transition is staged, then binds the immutable pathway/version content,
evidence links, verified-rule state, publication actor, and DB-stable publication
timestamp into a deterministic source version. The Contribution states only that a
governed catalogue version was published; it does not establish applicant eligibility,
occupation eligibility, visa approval, or an authority decision for a mobility case. A
later immutable pathway version receives its own deterministic Contribution while the
previous publication record remains immutable and the previous pathway version becomes
`superseded`.

Focused D3C coverage passes **8/8** for draft/no-emission, authenticated publication,
operator-role compatibility, persisted replay idempotency, fail-closed verified-rule
drift, atomic rollback on emitter failure, new-version supersession with a distinct
Contribution, and the still-closed generic source policy. Existing pathway governance
regression passes **23/23**, the combined D1-D3B/organization protection set passes
**94 passed + 1 expected PostgreSQL-only skip**, and the complete API suite passes
**750 passed + 1 expected PostgreSQL-only skip, 0 failed** with exit code 0. Repository
policy, release consistency, migration consistency, and `git diff --check` pass at
Alembic head `0074_durable_contribution_activity_model` with 118 registered tables.
13.16.1D4 is therefore **COMPLETE / PASS**. 13.16.1E0 Observatory/read-model
source reconciliation design is **COMPLETE** and 13.16.1E1 safe snapshot + Contribution
reconciliation read API is **COMPLETE / PASS**; E2 Activity coverage is **COMPLETE / PASS**; E3 is **IN PROGRESS**: E3A writer inventory/coverage-epoch design is **COMPLETE** and E3B legacy WorkItem material-writer adapters are **UNLOCKED / NOT STARTED**. Phase 13.16.1 remains **IN PROGRESS**.

#### 13.16.1D4 deferred-domain review and integrated emitter regression

**State: COMPLETE / PASS.** D4 re-evaluates every source that
was deliberately deferred in D0 after the accepted D2/D3 publication adapters. The
review does **not** authorize another emitter merely to increase Contribution volume.
No runtime service, router, persistence model, migration, source-owned transaction, or
public API behavior changes in this slice.

The deferred-source decision remains conservative:

- `JurisdictionImmigrationAssessment` stays deferred. Approved/rejected review has
  proposer/reviewer separation, but review still commits without a source-transition
  `AuditLog`, and proposal provenance can omit `official_source_id` /
  `source_snapshot_id`; it is therefore not yet a uniformly evidence-bound authority.
- `ReassessmentAcceptance` stays deferred. It records explicit user attestation and a
  deterministic acceptance key, but the durable record attributes the write to the
  internal `recorded_by` actor rather than an authenticated end-user identity contract.
- `ExternalValidationRun` stays deferred until genuine Phase 13.17 external-human
  acceptance and an accepted durable external-human attribution contract exist. The AI
  organization must not self-attest that gate.
- `CorporateComplianceEvent` stays deferred. `evidence_required` and
  `human_review_required` flags exist, but completion does not bind typed governed
  evidence or a distinct reviewer/approver record.
- `MobilityTimelineMilestone` stays deferred. Generic completion validates dependency
  state and optionally a human approval note, but does not enforce stage-specific
  evidence from `required_evidence_json`; generic milestone completion is too broad to
  become Contribution authority.
- `AgencySubmission` and `AuthorityAppointment` stay deferred. Their forward status
  machines and audits are useful Activity/work evidence, but terminal states remain
  operator-recorded and do not require an immutable external-authority receipt, decision
  artifact, or attendance proof.

D4 also hardens the existing generic organization API regression so request-selected
source authority remains closed not only to telemetry, but also to every sealed adapter
source (`JurisdictionSourceCertification`, initial-rule publication, regulatory-change
publication, pathway-version publication) and every deferred/ineligible domain source.
The only generic source contract remains terminal human-attributed `ExecutiveDecision`;
all four accepted real-domain emitters remain source-owned sealed integrations.

The accepted emitter inventory therefore remains exactly: explicit terminal
`ExecutiveDecision`, reviewed `JurisdictionSourceCertification`, published
`InitialRuleAssertion`/`VerifiedRule`, published `RegulatoryChange`, and published
`MobilityPathwayVersion`. Round 6 Austria v4 remains a zero-emitter safety pin while it
is draft, simulation-only, unpublished/not-ready, and its national/regional source
certifications remain `pending_review`.

Local acceptance is complete: the expanded organization-record source-policy suite passes
17/17; the combined D1-D3C emitter/transaction suites pass 40/40; deferred-domain
regression passes 49/49; the complete API suite passes 750 with 1 expected
PostgreSQL-only skip and 0 failures (exit code 0); repository policy, release
consistency, migration consistency, and `git diff --check` pass at Alembic head
`0074_durable_contribution_activity_model` with 118 registered tables. D4 is therefore
closed; 13.16.1E0 Observatory/read-model reconciliation design is complete, D4 unlocked E1, and E1 is now COMPLETE / PASS.

#### 13.16.1E0 Observatory/read-model source reconciliation design

**State: DESIGN COMPLETE.** Repository reconciliation confirmed
that the first Observatory read slice can safely summarize current authoritative state
and verified Contributions, but it cannot yet claim complete transition-history metrics.
No runtime code, schema, migration, database state, or UI changes are part of E0.

E0 fixes the source contract for E1:

- active Contributions are only immutable `outcome` rows not targeted by a same-tenant
  `supersession` or `retraction`; correction rows remain history and never inflate active
  outcome counts;
- current WorkItem, Blocker, ExecutiveDecision, HumanActionRequest, HumanAction, and
  dependency snapshots can be aggregated directly from their tenant-scoped durable rows;
- accepted sealed Contribution sources must reconcile to exact source IDs, terminal
  review/publication state, deterministic source versions, and governed attribution;
- automatic D2/D3 source-to-ledger completeness is bounded by an explicit
  `first_observed_contribution` coverage watermark because no historical backfill or
  durable deployment watermark exists; pre-coverage terminal source rows are reported
  separately, not called missing;
- `ExecutiveDecision` remains explicit-command-only, so a terminal decision without a
  Contribution is not a completeness defect;
- every response must include one `as_of`, UTC timezone, tenant/filter scope, source
  counts, coverage start/basis, and partial/unavailable warnings.

The repository also exposes a material Activity-coverage gap that E must handle rather
than hide. WorkItem, Blocker, HumanActionRequest, and ExecutiveDecision transitions
currently persist their authoritative state plus `AuditLog`, but do not automatically
append curated `OrganizationActivity`. The Activity append command itself owns a commit.
Therefore E1 must not derive cycle time, resolved-blocker period throughput, last
material-transition ageing, or a complete organization timeline from `updated_at`,
AuditLog volume, AgentRun/WorkflowRun, retries, tools, or messages. E1 is limited to safe
snapshot/reconciliation metrics. A later bounded E Activity slice must add caller-owned
Activity staging plus source-owned semantic transition adapters before those historical
metrics are enabled.

Planned E1 read-only endpoints are:

- `/api/v1/organization/observatory/summary`;
- `/api/v1/organization/observatory/contribution-reconciliation`;
- `/api/v1/organization/observatory/departments`.

They inherit authenticated tenant/role context from 13.16.1C, perform no mutations or
AuditLog writes, use bounded deterministic detail pagination, and do not implement the
Owner Control Center UI. E1 acceptance must reconcile SQLite and PostgreSQL fixtures,
preserve Alembic head `0074_durable_contribution_activity_model` and 118 registered
tables, prove tenant isolation and correction-chain semantics, identify source drift and
post-coverage missing emissions without repair, and keep the current Round 6 Austria
draft/pending state from appearing as published/certified/eligible Contribution.

13.16.1E1 is now **COMPLETE / PASS**. 13.16.1E2 Activity staging/semantic coverage is **COMPLETE / PASS**; 13.16.1E3 is **IN PROGRESS**: E3A writer inventory/coverage-epoch design is **COMPLETE** and E3B legacy WorkItem material-writer adapters are **UNLOCKED / NOT STARTED**. Phase 13.16.2 remains locked.

#### 13.16.1E1 safe snapshot + Contribution reconciliation read API

**State: COMPLETE / PASS.** The first Observatory runtime stays
inside the existing authenticated organization boundary and is read-only. It adds
`/api/v1/organization/observatory/summary`, `/contribution-reconciliation`, and
`/departments` without a mutation route, materialized metric table, cache, migration, or
Owner Control Center UI.

The implementation reads current tenant-scoped WorkItems, Blockers, ExecutiveDecisions,
HumanActionRequests, HumanActions, dependencies, and Contributions directly from their
authoritative rows. Active Contribution counts follow immutable correction semantics:
supersession/retraction targets no longer count active, while correction history remains
visible separately. Department summaries use only directly attributable current rows and
do not invent ownership from audit/runtime context.

The Contribution reconciliation API validates explicit terminal `ExecutiveDecision`
references and the four sealed automatic source families accepted in D2/D3. Automatic
completeness uses `first_observed_contribution` as the explicit no-backfill watermark;
precoverage rows are separated, post-coverage missing exact source/version Contributions
are visible gaps, and source/version/state drift is reported without repair. Terminal
ExecutiveDecision rows remain `explicit_command_only` and are not automatically expected
to have Contributions.

Every E1 response exposes a UTC `as_of`, trusted tenant scope, source-row counts,
coverage basis/start, and partial/unavailable warnings. Reconciliation pagination is
bounded at 50 default / 200 maximum and deterministically ordered. GET requests do not
append AuditLog, Activity, Contribution, or source state.

Historical WorkItem cycle time, completed-throughput periods, blockers-resolved-in-period,
last-material-transition ageing, and a complete semantic organization timeline remain
unavailable. E2 must first add caller-owned Activity staging and source-owned semantic
transition adapters. Round 6 Austria v4 remains draft/simulation-only/unpublished with
pending national/regional certification and remains outside published/certified/
eligibility Contribution metrics.

E1 acceptance is complete. Focused Observatory coverage passes **10/10**, the protected
organization/emitter regression passes **65/65**, and the complete API suite passes
**760 passed + 1 expected PostgreSQL-only skip, 0 failed** with exit code 0. Repository
policy, release consistency, migration consistency, and `git diff --check` pass with code
head `0074_durable_contribution_activity_model` and 118 registered tables.

PostgreSQL acceptance preserves two distinct boundaries. The authoritative integration
database `gmai` was inspected only inside `BEGIN READ ONLY` and remains intentionally at
`0073_austria_candidate_integrity`; the 0074 Observatory ledgers are absent there and no
migration was performed. The isolated PostgreSQL service database at 0074 exposes all
eight durable organization tables and successfully executed the current E1
`observatory_summary`, `observatory_departments`, and
`observatory_contribution_reconciliation` functions under transaction-level read-only
protection. The smoke retained `transaction_read_only=on` before and after the reads,
returned internally consistent tenant/source-count/coverage projections, and exited 0.
Its organization/source rows were empty, so sealed automatic coverage correctly remained
`not_established` while ExecutiveDecision remained `explicit_command_only`; this is not
claimed as production-data completeness. Both PostgreSQL containers were returned to
their prior stopped state.

The focused acceptance also fixed blocker department attribution to prefer the linked
WorkItem's department before the blocker record's fallback department, and narrowed the
OpenAPI architecture guard to permit exactly the three E1 GET-only routes without opening
arbitrary Observatory/dashboard/metrics surfaces. E1 is **COMPLETE / PASS**. E2 Activity
staging/semantic coverage is **COMPLETE / PASS**; E3 is **IN PROGRESS**: E3A writer inventory/coverage-epoch design is **COMPLETE** and E3B legacy WorkItem material-writer adapters are **UNLOCKED / NOT STARTED**; Phase 13.16.2 remains locked.

#### 13.16.1E2 caller-owned Activity staging and semantic transition coverage

**State: COMPLETE / PASS.** E2 adds the missing
caller-owned Activity transaction primitive and connects it only to the modern 13.16.1
organization command-service paths. It does not add a migration, table, router, API
mutation, dashboard, materialized metric, source-authority expansion, or historical
backfill.

`stage_activity(...)` now stages an immutable `OrganizationActivity`, its ordered
`OrganizationActivityStream` sequence update, and the Activity `AuditLog` inside the
caller's transaction. It never commits or rolls back. The standalone
`append_activity(...)` path retains its existing authenticated mutation-role check and
commit ownership. Internal staged Activity inherits the authorization already enforced by
the source command; this is required so sealed D2/D3 reviewer-authorized publication
transactions can append their Contribution Activity without widening any public command.

The bounded semantic adapters cover:

- WorkItem create, status transitions, and assignment changes;
- dependency creation and active -> satisfied/waived/superseded transitions;
- Blocker open, mitigation/resolution/waiver, and explicit predecessor supersession;
- ExecutiveDecision creation and approved/rejected outcome recording;
- HumanActionRequest creation, assignment, acknowledgement/start/decline/cancel/expire,
  plus completed state when an immutable HumanAction is appended;
- immutable HumanAction append;
- Contribution outcome, supersession, and retraction records for both standalone
  commands and caller-owned sealed source emitters.

Each modern source command now stages its authoritative row mutation/audit first, then
stages semantic Activity and the Activity audit, and commits once. Any Activity/audit
failure rolls back the source mutation as part of the same unit. Idempotent source replay
returns before creating duplicate Activity. Activity remains descriptive history only: it
does not create a Contribution, and AgentRun/WorkflowRun/tool/retry/message/AuditLog
volume remains non-authoritative.

Stream semantics are source-lineage bounded. WorkItem and its dependency events share the
WorkItem stream; HumanActionRequest and its immutable HumanAction share the request stream;
Contribution corrections share the original outcome lineage stream. Domain ownership is
used for Activity attribution where it is explicit (for example a linked WorkItem
department), while authenticated actor identity remains the command context.

E2 intentionally keeps Observatory `activity_history_established = false`. Repository
inspection found legacy writers in `app/services/organization_governance.py` and
`app/routers/organization_governance.py` that still create or mutate
`OrganizationalWorkItem` and `ExecutiveDecision` outside the modern 13.16.1 semantic
adapter boundary. Those paths are not silently reinterpreted, backfilled, or inferred
from `updated_at`/AuditLog. Therefore historical WorkItem cycle time, period throughput,
resolved-blocker throughput, last-material-transition ageing, and a complete organization
timeline remain unavailable after this slice. A later bounded E reconciliation/writer
coverage step must close or explicitly retire those writer gaps before history can be
called complete.

E2 acceptance is complete. The complete API suite passes **770 passed + 2 expected
PostgreSQL-only skips, 0 failed** with exit code 0. Repository policy, release consistency,
migration consistency, and `git diff --check` remain green at Alembic head
`0074_durable_contribution_activity_model` with 118 registered tables. The two bounded
Activity transaction contracts then execute against the isolated PostgreSQL 0074 service
database and pass **2/2** (35 non-PostgreSQL tests deselected). Post-test read-only
verification confirms `organization_activity_streams = 0` and `organization_activities = 0`,
proving rollback/no-residue behavior; the preserved authoritative `gmai` database remains
stopped, unmigrated, and untouched.

E2 is **COMPLETE / PASS**, but Phase 13.16.2 remains locked because complete semantic
history coverage remains explicitly false. E3A writer inventory/coverage-epoch design is
**COMPLETE** and the detailed reconciliation contract is recorded in
[ORGANIZATION_ACTIVITY_WRITER_RECONCILIATION_V13_16_1E3.md](ORGANIZATION_ACTIVITY_WRITER_RECONCILIATION_V13_16_1E3.md).
E3B legacy WorkItem material-writer adapters are **UNLOCKED / NOT STARTED**; E3C Decision
adapters and E3D explicit coverage activation remain locked in sequence.

#### 13.16.1E3A legacy-writer inventory and Activity coverage-epoch design

**State: COMPLETE (DESIGN); E3 OVERALL IN PROGRESS.** A fresh audit of exact committed
baseline `8bfbd40a1b4e460757b99d943a139cfd2ef83316` found that the remaining WorkItem/Decision
writer gaps are bounded to the legacy organization-governance router/service plus task
reminder bookkeeping. The full writer-by-writer disposition is recorded in
[ORGANIZATION_ACTIVITY_WRITER_RECONCILIATION_V13_16_1E3.md](ORGANIZATION_ACTIVITY_WRITER_RECONCILIATION_V13_16_1E3.md).

Material creation, requeue, assignment/escalation, emergency/hold/final Work disposition,
cancellation/retry control, deadline/readiness changes, Decision hold/Board promotion and
terminal outcomes must gain semantic Activity in their existing transaction boundaries.
Execution claim leases, per-attempt retry bookkeeping, delegation/action-output progress,
CEO coordination leases, reminder timestamps, and evidence-only Decision refresh are
explicitly excluded telemetry/intermediate state.

E3A also records that adapting every writer does not retroactively make pre-E3 history
complete. E1 has no durable Activity coverage start and E2/E3 forbid reconstructing old
Activity from mutable rows/AuditLog. E3D must therefore establish an explicit immutable
coverage-epoch Activity and expose its timestamp before `activity_history_established` can
be true from that point forward. No historical backfill is authorized.

Implementation order is E3B WorkItem material writers, E3C Decision/coupled writers, then
E3D coverage epoch/Observatory activation. Phase 13.16.2 remains locked.

#### Canonical validation sequence from Round 6 onward

This sequence supersedes older roadmap examples that referred to Round 3/4,
Phase 13.10.2.12, Austria pathway v3, migration 0072, or a proposed Phase 13.11 UX
track. Those references remain historical evidence; they are not the current plan.

```text
Phase 13.10.2.15 rendered gate                 PASS / CLOSED
                    ↓
Round 6 mobility-user shadow review             PASS / COMPLETE
                    ↓
Round 6 independent professional shadow review  PASS / COMPLETE
                    ↓
Round 6 correctness disposition                 PASS / CLOSED
                    ↓
13.16.0 Design System & Information Architecture Foundation
                                                     CLOSED / PASS
                    ↓
13.16.1 Durable Contribution & Activity Model
  DESIGN + PERSISTENCE + SERVICE + API + D0 EMITTER MAPPING COMPLETE
  D1 TRANSACTION STAGING + D2/D3 EMITTERS + D4 REGRESSION COMPLETE / PASS
  E0 READ-MODEL RECONCILIATION DESIGN COMPLETE
  E1 SAFE SNAPSHOT / RECONCILIATION READ API COMPLETE / PASS
  E2 ACTIVITY STAGING / SEMANTIC COVERAGE NEXT
                    ↓
13.16.2-13.16.9 role-based experience and observatory delivery
                    ↓
13.16.10 integrated responsive/accessibility acceptance
                    ↓
13.17 genuine external-human acceptance and Phase 13 disposition
                    ↓
Phase 14 only when Phase 13 acceptance and measured scale demand justify it
```

Round 6 was a clean correctness gate, not genuine external-human acceptance. The
same comparable Austria skilled-employment persona was used in a fresh synthetic case
for a mobility-user session and a separate professional shadow session. The
[deterministic disposition](ROUND_6_CORRECTNESS_DISPOSITION_V13_15.md) records zero
Critical/High correctness findings and zero unsupported legal certainty, with safe
candidate-family and occupation conditionality, credible material gaps and costs,
accurate lifecycle/certification state, an intact production/draft boundary, and
traceable material conclusions.

The Medium/Low experience findings are prioritized inputs to the experience track.
This PASS does not authorize certification approval or Austria v4 publication: v4
remains draft, unpublished, and not publication-ready; the national and regional
occupation certifications remain `pending_review`, while the distinct core pathway
certification remains approved.

#### 13.16.0 Design System & Information Architecture Foundation

**State: CLOSED / PASS — IMPLEMENTATION COMPLETE / RENDERED ACCEPTANCE PASS.** This
foundation must be completed before Organization Observatory dashboard development.
It addresses the typography, sizing, spacing, density, card, and information-hierarchy
drift accumulated while backend and governance capabilities expanded. This is a
presentation and interaction-system refactor: it must preserve every material safety,
governance, lifecycle, certification, evidence, and non-reliance warning.

Round 6 supplies these formal acceptance inputs:

- [x] Clarify that the 35% overall score and 60% confidence are internal assessment
  signals, not approval probabilities (`R6-MU-01`, Medium); rendered verification
  passed.
- [x] Create a plain-language hierarchy for draft, simulation, certification, and
  publication state without weakening any warning (`R6-MU-02`, Medium); rendered
  verification passed.
- [x] Separate internal simulation behavior from production availability around the
  draft toggle and published-only messaging (`R6-MU-03`, Low); rendered verification
  passed.
- [x] Prioritize the binding job-offer blocker and next actions before the long
  document inventory (`R6-MU-04`, Low); rendered verification passed.
- [x] Include a focused professional rendered check during experience acceptance
  (`R6-PRO-001`, Low operational-evidence finding); rendered verification passed.
- [x] Separate excluded self-employment from plausible alternative routes and retain
  it under explicitly excluded assessed routes (`R6-PRO-002`, Low); rendered
  verification passed.

- [x] Adopt Geist Sans as the primary product typeface. Restrict Geist Mono to
  technical identifiers, hashes, audit IDs, source IDs, and code-like values.
- [x] Define shared typography tokens for page titles, section titles, card titles,
  body copy, secondary copy, labels, statuses, and technical metadata. Remove
  excessive uppercase styling and labels rendered at microscopic sizes.
- [x] Establish project-wide layout and component foundations for spacing, responsive
  container widths, cards, form controls, badges, tables, empty states, loading states,
  and error states.
- [x] Apply one primary information hierarchy across decision workspaces:
  **decision/context → blockers → next actions → supporting evidence → technical
  provenance**.
- [x] Keep raw UUIDs, hashes, source identifiers, and audit metadata out of dominant
  primary-screen positions when they are not the user's immediate task. Preserve
  access to them in appropriately labelled expandable technical details.
- [ ] Refactor Mobility Profiles, Eligibility, Planning, Validation, Board Room,
  Agent Console, department views, and the remaining operator pages onto the shared
  tokens, components, density rules, and hierarchy. The shared foundation and six
  critical routes are implemented; full later-role experience work remains deferred.
- [x] Define distinct but visually related information architectures for the
  **Mobility User**, **Professional/Operator**, and **Owner/Board** experiences, with
  role-appropriate navigation, disclosure depth, terminology, and decision emphasis.
- [x] Preserve material governance and safety content in every experience. Improve
  its prioritization, grouping, progressive disclosure, and readability without
  hiding warnings or weakening certification, draft/production, evidence, or human-
  review boundaries.
- [ ] Meet responsive acceptance criteria across small mobile, tablet, standard
  desktop, and wide desktop layouts: no clipped actions or critical content, no
  horizontal page overflow, usable tables or responsive alternatives, stable reading
  order, and task controls reachable without precision interaction. Responsive code
  is implemented; the Phase 13.16.0 desktop and 390px acceptance surfaces pass, while
  broader cross-role integrated acceptance remains scheduled for Phase 13.16.10.
- [ ] Meet accessibility acceptance criteria: semantic landmarks and heading order,
  full keyboard operation, visible focus, labelled controls, non-color-only states,
  sufficient text and UI contrast, scalable text, reduced-motion support, accessible
  validation/error announcements, and screen-reader names for disclosure controls.
  The code foundation and bounded keyboard/focus/provenance checks pass; broader
  assistive and cross-role review remains scheduled for Phase 13.16.10.
- [ ] Add representative rendered/regression coverage for shared foundations and the
  three experience architectures, then complete mobility-user, professional/operator,
  and owner/board review before unlocking Organization Observatory dashboards.
  Deterministic foundation checks and the Phase 13.16.0 internal rendered review pass;
  broader experience-architecture coverage remains scheduled for later slices.

The implementation is documented in
[DESIGN_SYSTEM_INFORMATION_ARCHITECTURE_V13_16_0.md](DESIGN_SYSTEM_INFORMATION_ARCHITECTURE_V13_16_0.md).
Automated checks and independent internal rendered inspection pass. Phase 13.16.0 is
closed; Phase 13.16.1 design, persistence foundation, internal command/service layer,
authenticated organization API, and 13.16.1D0 emitter mapping/design are complete.
13.16.1D1 caller-owned transaction staging is COMPLETE / PASS; 13.16.1D2
source-certification review emission is COMPLETE / PASS. The first bounded runtime emitter
is accepted, 13.16.1D3A initial-rule / VerifiedRule publication is COMPLETE / PASS; 13.16.1D3B regulatory-change publication is COMPLETE / PASS; 13.16.1D3C pathway publication is COMPLETE / PASS; 13.16.1D4 is COMPLETE / PASS, and
13.16.1E0 read-model reconciliation design is COMPLETE; 13.16.1E1 read API implementation is COMPLETE / PASS; 13.16.1E2 Activity coverage is COMPLETE / PASS; 13.16.1E3 is IN PROGRESS with E3A writer inventory/coverage-epoch design COMPLETE and E3B legacy WorkItem material-writer adapters UNLOCKED / NOT STARTED.

#### 13.16 delivery sequence

The attached concept correctly prioritizes outcomes over agent activity noise. The
implementation order below improves it by establishing design/IA and authoritative
contribution data before any dashboard attempts to summarize the organization.

| Slice | Outcome | Exit condition |
|---|---|---|
| **13.16.0** | Design System & Information Architecture Foundation | Shared tokens, components, hierarchy, accessibility rules, and three experience architectures accepted |
| **13.16.1** | Durable Contribution & Activity Model | Common contribution, work item, activity, decision, blocker, and human-action contracts are durable, attributable, auditable, and linked to evidence |
| **13.16.2** | Role-based application shells and navigation | Mobility User, Professional/Operator, and Owner/Board see distinct but related navigation and disclosure depth |
| **13.16.3** | Unified Owner Control Center | Company health, meaningful work, contributions, blockers, decisions, validation state, and human attention derive from authoritative records rather than invented summaries |
| **13.16.4** | Department workspaces | Each department exposes objectives, current work, contributions, blockers, decisions, evidence, authority, and runtime health consistently |
| **13.16.5** | Cross-department dependencies and blocker view | Outcome dependencies, accountable owners, gating state, and critical paths are first-class and auditable |
| **13.16.6** | Owner decision and escalation inbox | Only genuine Board/owner decisions, approvals, exceptions, and external-human actions reach the attention queue |
| **13.16.7** | Mobility User experience | Case-centric journey exposes progress, blockers, documents, next actions, and safe decision context without operator or backend noise |
| **13.16.8** | Professional/Operator experience | Case operations, comparison, evidence, validation, timelines, and authority work are efficient while retaining appropriate provenance |
| **13.16.9** | Evidence and provenance UX consolidation | Evidence, certification, lifecycle, source, and audit detail use progressive disclosure without weakening material warnings or traceability |
| **13.16.10** | Responsive, accessibility, polish, and integrated acceptance | Critical journeys pass rendered mobile/desktop, keyboard, screen-reader, contrast, loading/error/empty-state, and cross-role acceptance checks |

##### 13.16.1 authoritative model requirements

**Status: IMPLEMENTATION IN PROGRESS — DESIGN, 13.16.1A PERSISTENCE, 13.16.1B
COMMAND/SERVICE LAYER, 13.16.1C AUTHENTICATED ORGANIZATION API, AND 13.16.1D0
EMITTER MAPPING/DESIGN COMPLETE; 13.16.1D1 TRANSACTION STAGING COMPLETE / PASS;
13.16.1D2 SOURCE-CERTIFICATION EMISSION COMPLETE / PASS; FIRST BOUNDED RUNTIME
CONTRIBUTION EMITTER ACCEPTED; 13.16.1D3A INITIAL-RULE / VERIFIED-RULE PUBLICATION COMPLETE / PASS; 13.16.1D3B REGULATORY-CHANGE PUBLICATION COMPLETE / PASS; 13.16.1D3C PATHWAY PUBLICATION COMPLETE / PASS; 13.16.1D4 DEFERRED-DOMAIN / INTEGRATED REGRESSION COMPLETE / PASS;
13.16.1E0 READ-MODEL RECONCILIATION DESIGN COMPLETE; 13.16.1E1 READ API COMPLETE / PASS; 13.16.1E2 ACTIVITY COVERAGE COMPLETE / PASS; 13.16.1E3 IN PROGRESS — E3A WRITER AUDIT/COVERAGE-EPOCH DESIGN COMPLETE; E3B WORKITEM ADAPTERS UNLOCKED / NOT STARTED.** The current-state
inventory, six canonical contracts, exact proposed database model, migration plan,
API/service direction, observatory aggregation boundary, backfill policy, and test
matrix are defined in
[DURABLE_CONTRIBUTION_ACTIVITY_MODEL_V13_16_1.md](DURABLE_CONTRIBUTION_ACTIVITY_MODEL_V13_16_1.md).
Migration `0074_durable_contribution_activity_model`, registered SQLModel entities,
portable controlled-value checks, tenant-fenced relationships, and focused persistence
tests establish the durable schema. The bounded HTTP-independent command services now
enforce source authority, lifecycle, idempotency, tenant, actor, reference, and atomic
AuditLog invariants on SQLite and PostgreSQL. The authenticated REST surface derives
identity, tenant, role, position, and authority from trusted request state, delegates
mutations to those services, and applies non-disclosing tenant lookups, safe errors,
bounded pagination, and typed responses. The unchecked items below now remain read-model/aggregation and experience exit criteria;
the accepted D emitter set exists, but API/emitter completion does not claim that the
Observatory read model or UI exists.

Remaining implementation order: proceed with **13.16.1E3B legacy WorkItem material-writer adapters** now that E3A writer inventory/coverage-epoch design is COMPLETE. Then close Decision/coupled writers in E3C and establish the explicit Activity coverage epoch in E3D before enabling transition-period throughput/cycle-time metrics. E1 safe snapshot + Contribution reconciliation remains COMPLETE / PASS, and enabled Contribution adapters must continue to reconcile to their authoritative source tables before Observatory/read-model acceptance.
Phase 13.16.2 remains locked until that sequence and the 13.16.1 exit criteria pass.

- [x] Define separate durable records or explicitly versioned event contracts for
  **activity**, **contribution**, **decision**, **blocker**, **work item**, and
  **human action**; do not treat them as interchangeable counters.
- [x] Make every meaningful contribution attributable to a department/position,
  related objective or phase, affected entity, authority level, evidence, status,
  impact, timestamps, and human-action requirement.
- [ ] Prefer outcome metrics over tool-call or agent-message volume. The observatory
  may expose execution telemetry as technical detail, but must not present activity
  volume as organizational contribution.
- [x] Link contribution and dependency records to existing provenance, audit,
  validation, agent-output, decision, case, pathway, evidence, and lifecycle records
  instead of copying or silently reinterpreting their truth.
- [x] Define idempotency, ordering, correction/supersession, retention, authorization,
  tenant isolation, and audit semantics before dashboard aggregation is accepted.

##### 13.16.2 navigation and experience-shell baseline

- [ ] Owner/Board navigation groups the product into **Overview**, **Organization**
  (Departments, Contributions, Activity, Decisions, Owner Inbox), **Mobility
  Operations** (Cases, Profiles, Planning, Timelines, Documents), **Intelligence**
  (Pathways, Regulatory Intelligence, Sources & Evidence, Occupation Evidence),
  **Validation**, **Governance**, and **Settings**.
- [ ] Mobility User navigation remains case-centric: case overview, profile,
  pathways/eligibility, documents, progress, and next action. It must not expose
  phase numbers, backend health, raw UUIDs, publication controls, or certification
  administration as primary navigation.
- [ ] Professional/Operator navigation prioritizes cases, pathway comparison,
  eligibility, documents, evidence, timelines, authority workflow, and validation,
  with provenance and governance visible at the depth needed for professional work.
- [ ] Existing routes remain reachable during migration through the correct shell;
  route consolidation must be incremental and preserve authorization boundaries.

##### 13.16 experience constraints

- [ ] Do not add more departments merely to populate the observatory. Make existing
  departments visible, measurable, governable, and useful first.
- [ ] Keep existing deep routes available during incremental migration, but stop
  presenting all routes as equal top-level navigation choices.
- [ ] Owner views must distinguish company health, active work, contributions,
  decisions, risks/blockers, external validation, and human attention.
- [ ] Department and global timelines must represent governed business events and
  outcomes, with raw agent/tool execution available only as supporting telemetry.
- [ ] Observatory summaries must be reproducible from authoritative records and must
  never infer completion, impact, readiness, or publication state from UI activity.


### 13.6 Departmental expansion

After the first organization flow and Board Room pass their release gates, and after the hardening checkpoint above:

- [x] Expand Operations: Sales Intelligence, Operations Coordination, Business
  Intelligence, and case-specific Application Readiness under COO accountability.
- [x] Expand Technology: VP Engineering, Lead Architect, and hardened CTO
  delegation contracts under Technology accountability. (Engineering managers,
  technical leads, and engineering members remain future scale work.)
- [x] Expand Product: CPO, Product Manager, and Design Agent with bounded
  delegation, required evidence/output contracts, and hardened role cards under
  Product accountability.
- [x] Expand Security: CISO, Security Lead, and Threat Analyst with bounded
  delegation, threat-intelligence/prompt-injection/compromised-agent analysis,
  required evidence/output contracts, and hardened role cards under Security
  accountability.
- [x] Expand Security Operations (SOC): SOC Lead and SOC Analyst under CISO
  accountability, with bounded delegation, agent-behavior and audit-log analysis,
  required evidence/output contracts, and hardened role cards.
- [x] Add Marketing: CMO, Creative Director, and Marketing Manager under CMO
  accountability, with bounded delegation, brand/creative/channel analysis, and
  required evidence/output contracts.
- [ ] **External-validation gate:** do not activate time-bounded cross-functional
  programmes or advance to Phase 14 until at least one real mobility user and one
  professional/operator have tested an end-to-end Truth Engine/pathway workflow
  and the resulting defects are triaged.
- [ ] Add Finance: CFO, Accounts Lead, and Investor Relations Lead under CFO
  accountability, with bounded delegation, spend/investment/contract analysis,
  and required evidence/output contracts.
- [x] Add Communications/CCO: CCO, PR / Communications Lead, and Government Relations
  Lead under CCO accountability, with bounded delegation, messaging/media/crisis
  and policy/regulatory/stakeholder analysis, required evidence/output contracts,
  and fail-closed prohibited-action enforcement.
- [x] Add People/CHRO: CHRO, HR Lead, and Culture/Recruitment Lead under CHRO
  accountability, with bounded delegation, workforce/talent/compensation/compliance
  and culture/recruitment/retention analysis, required evidence/output contracts,
  and fail-closed prohibited-action enforcement.
- [x] Add Legal: CLO, General Counsel, and Public Policy/Compliance Lead under
  CLO accountability, with bounded delegation, risk/authority/policy analysis,
  and required evidence/output contracts.
- [ ] Add time-bounded cross-functional programmes with one accountable executive
  sponsor and explicit participating positions.

### Phase 13 non-negotiable controls

- No position receives authority merely because its prompt claims authority.
- No agent may change its own position contract, reporting line, authority, or
  budget.
- No autonomous spending, contract signature, legal filing, authority submission,
  production deployment, or client-facing send outside an explicit gate.
- Regulated conclusions remain source-controlled and review-gated.
- Cross-tenant access remains prohibited.
- Every meaningful action is attributable and audited.
- The Board can suspend one agent, one department, or the complete organization.

### Phase 13 release criteria

- [x] One complete hierarchy from Board to specialist is executable.
- [x] Authority classification is deterministic and covered by tests.
- [x] Restricted actions fail closed.
- [x] Delegation and escalation are idempotent and traceable.
- [x] The CEO produces an evidence-backed Board Packet.
- [x] The Board can approve, reject, override, and stop execution. Approve,
  reject, return-for-analysis, global pause, override, and per-agent suspension
  are implemented.
- [x] An emergency scenario reaches the Board without delay.
- [x] Routine L1/L2 work completes without unnecessary Board interruption.
- [x] Evidence-complete internal L3 Operations work resolves through a distinct
  CEO decision receipt without authorizing an external action or interrupting the
  Board.
- [x] Evidence-complete internal L3 Marketing work resolves through a distinct
  CEO decision receipt that consults the CMO, without authorizing an external
  action or interrupting the Board.
- [x] Evidence-complete internal L3 Finance work resolves through a distinct
  CEO decision receipt that consults the CFO, without authorizing funds movement,
  pricing changes, spend commitments, contracts, or interrupting the Board.
- [x] Round 6 confirms the current Austria decision pipeline has no Critical/High
  correctness finding and no unsupported legal certainty; Phase 13.16.0 is unlocked
  but not started.
- [ ] Phase 13.16 delivers the shared design/IA foundation, authoritative contribution
  model, role-based experiences, Organization Observatory, and integrated responsive/
  accessibility acceptance without weakening governance or evidence boundaries.
- [ ] Phase 13.17 passes genuine external-human mobility-user and independent
  professional/operator acceptance and records the deterministic Phase 13 disposition.

## 7. Phase 14: Global Scale Platform

**Status:** Not started; implement only after validated operational demand.

- [ ] Expand reviewed evidence coverage across all required jurisdictions.
- [ ] Add OpenSearch or Elasticsearch only when PostgreSQL search is measured as
  insufficient.
- [ ] Add Neo4j only when validated graph traversal requires a dedicated graph
  database.
- [ ] Add durable event streaming and Temporal-class workflows when throughput and
  recovery requirements justify them.
- [ ] Add OpenTelemetry, Prometheus, Grafana, Loki, tracing, SLOs, backups, and
  disaster-recovery exercises.
- [ ] Add Kubernetes and cloud/on-premise deployment profiles when operationally
  justified.

## 8. Completed Delivery Map

| Phase | Outcome | Evidence |
|---|---|---|
| 1-5 | Local-first platform, CRM, intake, Truth Engine, documents, eligibility, controlled agents, audit, and RBAC | [GLOBAL_MOBILITY_AIOS_VISION_V1.md](GLOBAL_MOBILITY_AIOS_VISION_V1.md) |
| 6 | Foundation and repository alignment | [ARCHITECTURE.md](ARCHITECTURE.md) |
| 7 | Regulatory intelligence, monitored official sources, immutable snapshots, reviewed changes, and verified rules | [TRUTH_ENGINE_SPEC.md](TRUTH_ENGINE_SPEC.md) |
| 8 | Universal profile, governed pathways, deterministic comparison, and operational timelines | [GLOBAL_MOBILITY_AIOS_VISION_V1.md](GLOBAL_MOBILITY_AIOS_VISION_V1.md) |
| 9 | Server-side document extraction, validation, integrity findings, reminders, and controlled access | [DOCUMENT_INTELLIGENCE_FOUNDATION_V9_0.md](DOCUMENT_INTELLIGENCE_FOUNDATION_V9_0.md) |
| 10A | Self-updating regulatory intelligence, controlled classification, graph projection, and pathway impacts | [CONTROLLED_REGULATORY_CLASSIFICATION_V10_4.md](CONTROLLED_REGULATORY_CLASSIFICATION_V10_4.md) |
| 10B software | Registry, evidence batches, source onboarding, baseline capture, rule assertions, readiness receipts, and tranche operations | [COVERAGE_TRANCHE_OPERATIONS_V10_22.md](COVERAGE_TRANCHE_OPERATIONS_V10_22.md) |
| 10C-10E | Global dashboards, reviewed ranking, and immutable multi-year mobility scenarios | [MULTI_YEAR_MOBILITY_SCENARIOS_V10_14.md](MULTI_YEAR_MOBILITY_SCENARIOS_V10_14.md) |
| 11 | Corporate, business, wealth, investment, family-office, and tax/treaty mobility | [BUSINESS_WEALTH_ADVISORY_V11_4.md](BUSINESS_WEALTH_ADVISORY_V11_4.md) |
| 12 | Client/ecosystem portals, partner APIs, governed automation, appointments, submissions, assignments, checklists, and reminders | [GOVERNED_AUTOMATION_FOUNDATION_V12_3.md](GOVERNED_AUTOMATION_FOUNDATION_V12_3.md) |
| 13.0-13.14 software | AI organization governance, Board Room, bounded Operations/Technology/Product/Security/SOC/Marketing/Finance/Communications/People/Legal runtimes, platform hardening, and durable external-mobility validation infrastructure | [AI_ORGANIZATION_GOVERNANCE_V13_0.md](AI_ORGANIZATION_GOVERNANCE_V13_0.md), [EXTERNAL_MOBILITY_VALIDATION_V13_10_2.md](EXTERNAL_MOBILITY_VALIDATION_V13_10_2.md) |

## 9. Delivery Governance

Every software slice must include:

- an accountable product owner and runtime owner;
- acceptance criteria tied to the canonical vision;
- migration and rollback paths when data changes;
- least-privilege authorization and tenant boundaries;
- audit events for sensitive actions and transitions;
- provenance and Truth Engine integration for regulated claims;
- backend tests and frontend build/type validation;
- browser-level validation for critical user journeys;
- security, privacy, consent, retention, and operational notes;
- roadmap, feature-document, and changelog updates;
- an explicit statement of what remains incomplete.

### Status rules

- **Delivered** means the code exists and focused verification passes.
- **Complete** means the phase exit criteria and full quality gate pass.
- **Operationally ongoing** means the software is complete but live evidence,
e  review, monitoring, or data expansion continues.
- **Blocked** identifies the exact external or technical dependency; it is not a
  substitute for unfinished work.
- A UI without its authoritative backend, permissions, audit, and tests is not a
  completed capability.
- A role card without runtime registration, authority enforcement, and an output
  contract is not an operational agent.

### 13.10.2.2 Controlled official-source authority remediation

- [x] Add a bounded, audited official-source authority-reassignment API for correcting
  duplicate authority ownership discovered during external mobility validation.
- [x] Require the target authority to be the jurisdiction's independently approved
  `primary_immigration` authority and fail closed on cross-jurisdiction moves.
- [x] Refuse reassignment when the source already has a pending or approved source
  certification, preserving certification provenance.
- [x] Preserve the official-source identity and therefore existing monitor, retrieval,
  and immutable snapshot lineage; only the source-to-authority relationship changes.
- [x] Make retries idempotent when the source is already attached to the approved
  primary authority.
- [ ] Complete the live Austria remediation, submit `supplemental_visa` certification
  for the Skilled Workers in Shortage Occupations source, and obtain independent review.

### 13.10.2.3 Existing-source baseline linkage hardening

- [x] Persist authority, official-source, and existing-monitor linkage when a
  coverage batch certifies an already-onboarded source without repeating source
  onboarding.
- [x] Resolve legacy certification-only batch items read-only from their immutable
  source certification so baseline status can reuse existing evidence.
- [x] Preserve existing source, monitor, retrieval, and immutable-snapshot identity;
  no replacement evidence is created by linkage resolution.
- [x] Add regression coverage for the certification-only legacy batch condition
  discovered during Austria skilled-employment validation.
- [x] Add an audited, idempotent reconciliation operation for legacy
  certification-only batch items; conflicting non-null linkage fails closed.
- [x] Reconcile the existing live Austria batch-item linkage and confirm it resolves
  to the already captured immutable baseline before initial-rule assertions.

### 13.10.2.4 Supplemental source-certification multiplicity hardening

#### Validation evidence

- [x] Isolated SQLite migration smoke test passed through
  `0068_external_validation_framework -> 0069_source_certification_multiplicity`,
  downgrade to `0068`, and re-upgrade to `0069`.
- [x] PostgreSQL production-shape database migrated successfully to
  `0069_source_certification_multiplicity`.
- [x] PostgreSQL now enforces separate partial unique indexes for
  jurisdiction-scoped `primary_immigration` certification and
  source-scoped supplemental certification lineages.
- [x] Historical `uq_jsc_scope_version` database constraint was removed.
- [x] Pre-migration PostgreSQL backup created at
  `gmai-postgres-before-0069-20260810-040926.dump`
  with SHA-256
  `26BEA6AD1D83BB5E4B453141FD921797F05000A6B20E5D8C47086C475996E535`.
- [x] Live Austria verification proved three supplemental visa source
  lineages can coexist: the existing skilled-worker source remains approved,
  the Austria-wide 2026 source remains pending review, and the regional 2026
  source was independently created as version 1 with no supersession pointer.
- [x] Regional 2026 certification
  `f4cf5f04-0519-4cad-b5c2-88ec1183ded5` is linked to coverage batch
  `0bd5b76d-49f5-4dbd-ba54-feeb4591676c` and monitor
  `09295bbc-8b68-45e8-9387-4184b7172d8a`.
- [x] Behavioral regression proves approving one supplemental source does
  not mutate independently approved or pending sources, while a later
  version of the same source supersedes only its own lineage.
- [x] Focused certification/linkage suite: **18 passed**.
- [x] Complete API suite: **552 passed**, with one non-blocking
  Starlette/httpx deprecation warning.
- [ ] Austria-wide and regional 2026 certifications remain pending genuine
  independent human review; this hardening does not satisfy that review gate.

- [x] Add Alembic migration
  `0069_source_certification_multiplicity` to replace the historical
  jurisdiction/scope/version uniqueness constraint with explicit primary and
  supplemental lineage invariants.
- [x] Preserve database-enforced jurisdiction-scoped version uniqueness for
  `primary_immigration`.
- [x] Enforce source-scoped version uniqueness for supplemental certifications
  so independently governed sources in the same jurisdiction/domain may
  coexist.
- [x] Mirror both partial unique indexes in SQLModel metadata so fresh test
  databases and Alembic-managed databases express the same invariant.
- [x] Add regression coverage proving two supplemental sources can both start
  at version 1 while duplicate versions within one source remain blocked.

- [x] Preserve jurisdiction-scoped versioning and supersession for
  `primary_immigration` certification.
- [x] Scope `supplemental_<domain>` pending-review guards, version lineage, and
  supersession to the exact official source so multiple independently reviewed
  sources may coexist within one jurisdiction/domain.
- [x] Prevent approval of one supplemental visa source from superseding approved
  supplemental visa certifications belonging to other official sources.
- [x] Clear legacy cross-source `supersedes_certification_id` pointers at review
  time without replacing certification, source, monitor, retrieval, or snapshot
  identity.
- [x] Add regression coverage for primary-vs-supplemental lineage semantics.
- [ ] Re-verify the live Austria 2026 Austria-wide certification, submit the
  regional 2026 certification concurrently, and confirm the previously approved
  skilled-worker source certification remains approved.
- [ ] Obtain genuine independent review of both 2026 shortage-list source
  certifications before proposing regulatory assertions.

### 13.10.2.5 Pathway multi-source evidence provenance

- [x] Add normalized `mobility_pathway_version_evidence` records so one immutable
  pathway version can declare multiple official source/snapshot pairs with explicit
  evidence roles.
- [x] Preserve the historical `official_source_id` / `source_snapshot_id` fields as
  the backward-compatible `core_route` pair rather than performing a disruptive
  pathway API rewrite.
- [x] Add Alembic migration `0070_pathway_version_evidence_provenance` and backfill
  every historical version that already has a source/snapshot pair into a
  `core_route` evidence row without database-specific UUID generation.
- [x] Add input/read schemas for evidence links and persist normalized links on new
  pathway drafts.
- [x] Fail closed on duplicate or mismatched core evidence, cross-country evidence,
  cross-jurisdiction evidence, and source/snapshot mismatch.
- [x] Require every human-published Verified Rule referenced by a published pathway
  version to have its exact source/snapshot pair declared by that version.
- [x] Require non-core evidence marked `required_for_publication` to have an approved
  certification for that exact official source before pathway publication. Drafts
  may still carry pending evidence so governance review is not bypassed.
- [x] Prevent certification bypass by requiring any non-core evidence used by a
  referenced Verified Rule to be publication-required and certified, and hold a
  `core_route` source when it has entered certification but has no approved state.
- [x] Extend multi-year mobility scenarios to pin every pathway evidence snapshot,
  not only the legacy core snapshot.
- [x] Extend pathway risk analysis across every declared evidence source/snapshot and
  surface stale, missing, inactive, or certification-regressed evidence by role.
- [x] Extend regulatory-impact source matching and impact receipts across every
  declared pathway evidence source/snapshot.
- [x] Add focused regression coverage for required supplemental certification,
  undeclared rule provenance, legacy core fallback, multi-source risk inspection,
  and regulatory-impact source matching.
- [x] Applied `0070` to the persistent PostgreSQL database after a verified
  custom-format backup:
  `C:\\Users\\Bennet Allryn\\Downloads\\gmai-postgres-before-0070-20260810-124945.dump`
  (3,631,344 bytes; SHA-256
  `7EC3E2E5E350A59EC21D4345662AC1B6E36B9F172C422BFA454675025FEB7E5C`).
- [x] Verified the PostgreSQL `0069` -> `0070` migration transactionally:
  `missing_core_backfills = 0`, four historical `core_route` evidence rows were
  created, and the database revision is
  `0070_pathway_version_evidence_provenance`.
- [x] Complete post-migration validation passed: focused Phase 13.10.2.5 suite
  **14 passed, 1 warning**; complete API suite **560 passed, 1 warning**;
  repository policy, release consistency, database migration, Docker production
  profile, and local database-schema checks all passed.
- [x] Re-verified live Austria integrity after migration: skilled-worker pathway
  versions 1 and 2 remain `draft`, unpublished and unapproved; both retain matching
  `core_route` source/snapshot evidence and no national/regional evidence links were
  introduced by migration.
- [x] Confirmed the existing general skilled-worker supplemental source certification
  remains `approved`, while the Austria-wide and regional 2026 shortage-list source
  certifications remain `pending_review`. The historical Austria-wide cross-source
  supersedes pointer remains untouched for controlled cleanup during genuine review.
- [ ] Create a future Austria pathway version only after the two 2026 evidence links
  are deliberately attached and the publication gate can evaluate their real
  certification state after genuine independent review.

### 13.10.2.6 Structured 2026 shortage-occupation evidence

- [x] Add normalized `shortage_occupation_entries` derived from immutable official
  source snapshots rather than encoding hundreds of occupation labels as
  `VerifiedRule` statements.
- [x] Add Alembic migration `0071_structured_shortage_occupation_evidence` with
  source/jurisdiction/snapshot foreign keys, deterministic source ordinals, exact
  extraction hashes, and snapshot/year/scope uniqueness.
- [x] Add a bounded `austria_migration_shortage_v1` parser for the official
  migration.gv.at Austria-wide and regional shortage-occupation pages. Extraction
  requires one declared year, contiguous numbered groups, an operator-pinned expected
  group count, and exact official source URL/scope provenance.
- [x] Preserve source category titles and exact source-listed occupation aliases;
  normalize only Unicode, dash, spacing, slash, and comma presentation differences.
  No translation, fuzzy classification, embedding similarity, or LLM inference is
  allowed in deterministic lookup.
- [x] Model regional applicability with official Austrian federal-province codes
  (`AT-1` through `AT-9`) and fail closed when a regional source group has no
  recognized province list.
- [x] Make materialization immutable and idempotent: a repeated extraction from the
  same snapshot/year/scope reuses the same entry hashes, while any conflicting
  derived projection for an immutable snapshot is rejected rather than overwritten.
- [x] Add exact occupation lookup states for `matched`, `not_found`,
  `province_required`, `not_applicable_in_province`, and `ambiguous`; multiple exact
  source matches fail closed as ambiguous.
- [x] Keep source-list applicability separate from governance readiness. Lookup may
  report that a label is present in an immutable list while still returning
  `governance_ready = false` when that source has no approved certification; it never
  asserts case eligibility, qualification equivalence, job-offer sufficiency, or an
  authority outcome.
- [x] Add regulatory-intelligence API routes for controlled snapshot materialization
  and read-only exact lookup, plus regression coverage for national/regional parsing,
  province applicability, year/ordinal fail-closed behavior, ambiguity, idempotency,
  audit receipts, and pending-vs-approved certification state.
- [x] Harden the fresh-database Alembic regression for slower Windows hosts by
  increasing the subprocess wall-clock budget for the upgrade/downgrade/re-upgrade
  chain from 60 to 180 seconds. This is test-harness resilience only; it does not
  change migration logic, runtime database timeouts, or production behavior.
- [x] Apply the incremental patch to the `fbe4796` base, run focused and complete API
  verification, and record the resulting test counts.
- [x] Back up persistent PostgreSQL immediately before the `0070` -> `0071` migration,
  apply `0071`, and verify the new table/index/constraint shape without modifying
  existing pathway versions or source certifications.
- [x] Materialize the live Austria 2026 Austria-wide snapshot
  `a1032556-81f1-49bf-acd6-fa8f43e45341` and regional snapshot
  `7a3503f3-dc9d-4ded-bf31-7a80738b7434`; record entry counts and deterministic
  entry-set hashes from those exact immutable snapshots.
- [x] Confirm the Austria-wide and regional 2026 source certifications remain
  `pending_review` after structuring. Structured extraction is not source approval.
- [x] Do not create or publish a new Austria skilled-worker pathway version in this
  slice; the external-human validation gate and genuine independent-review gates
  remain held.


- [x] Applied `0071_structured_shortage_occupation_evidence` to persistent
  PostgreSQL after verified custom-format backup
  `C:\Users\Bennet Allryn\Downloads\gmai-postgres-before-0071-20260810-135554.dump`
  (3,637,418 bytes; SHA-256
  `7355C9A9C18A61E2FD261AF9333FDEC4B0FDDBAAF660F3CA0996458758C95FB6`).
- [x] Post-patch validation passed with **39 focused tests** and **571 complete
  API tests**, with one existing Starlette TestClient/httpx deprecation warning;
  the complete local quality gate passed.
- [x] Materialized immutable Austria 2026 shortage evidence into **64 national**
  and **66 regional** structured occupation groups.
- [x] National entry-set SHA-256:
  `43f1b9fad49777a89da280395124a6d3e4608219b835d144765f47e148d00301`.
- [x] Regional entry-set SHA-256:
  `5fd467b7bb3d1681dcf90f604d648af83483dfec443e4ae1d6bc5faf8e7bc238`.
- [x] Idempotency re-run confirmed zero duplicate writes:
  national `created_count = 0`, `existing_count = 64`; regional
  `created_count = 0`, `existing_count = 66`; both entry-set hashes remained
  unchanged.
- [x] Deterministic lookup smokes returned `matched` and
  `list_applicability = true` while correctly retaining
  `governance_ready = false`.
- [x] Both Austria-wide and regional 2026 source certifications remain
  `pending_review`; structured materialization grants no source approval.
- [x] Re-verified the Austria skilled-worker pathway after materialization:
  versions 1 and 2 remain `draft`, unapproved, and unpublished. No pathway
  version was created or published by this slice.

### 13.10.2.7 Austria pathway integration of structured 2026 evidence

- [x] Reserve `national_occupation_list` and `regional_occupation_list` pathway
  evidence roles for canonical structured shortage-occupation projections. These
  roles must be `required_for_publication` and cannot be used as optional evidence
  to bypass source-certification governance.
- [x] Require each structured occupation evidence link to pin the exact materialized
  projection identity: year, scope, entry count, entry-set SHA-256, extraction
  version, and immutable source-snapshot content hash. Draft creation fails closed
  when any pinned value differs from the persisted projection.
- [x] Add a controlled structured-occupation integration workflow that clones the
  current immutable pathway version into a new draft, preserves its core route and
  Verified Rules, and adds canonical national/regional occupation-list evidence.
- [x] Require the Austria `at-rwr-skilled-worker-shortage-occupation` pathway to carry
  both structured occupation-list evidence roles before any version can publish. This
  keeps historical core-only drafts v1/v2 fail-closed instead of leaving an older
  publication path around the new evidence gate.
- [x] Make the integration idempotent by persisting a deterministic integration
  signature in pathway-version metadata. Repeating the same integration returns the
  existing draft instead of creating another version. A stale source-version branch
  is rejected rather than silently forking pathway history.
- [x] Add a read-only pathway publication-readiness endpoint that reports the
  deterministic evidence blocker plus certification status by evidence role without
  mutating or approving the pathway. Independent human review remains a separate
  publication requirement even when evidence readiness becomes green.
- [x] Add focused regressions for canonical projection binding, operator-pinned hash
  mismatch, required-for-publication enforcement, idempotency, stale-source rejection,
  pending certification hold state, and synthetic post-certification publication.
- [x] Keep Alembic head at `0071_structured_shortage_occupation_evidence`; this slice
  changes pathway integration/governance behavior and requires no database migration.
- [x] Apply the incremental patch to the clean `8eb84af` base and run focused plus
  complete API/local quality verification before any live pathway write.
- [x] Back up persistent PostgreSQL immediately before the live Austria pathway-draft
  integration even though this slice has no schema migration.
- [x] Create or idempotently reuse Austria skilled-worker pathway version 3 from
  source version `cb17657f-be9f-4ea9-b7ce-795cf0e1b1d5`, binding the existing
  `core_route` plus the immutable 2026 national and regional occupation projections.
- [x] Verify live version 3 remains `draft`, unapproved and unpublished, and that
  publication readiness is held while both 2026 supplemental source certifications
  remain `pending_review`.
- [x] Do not approve either 2026 source, publish the pathway, or release the external
  validation gate in this slice. Genuine independent review remains required.

#### Phase 13.10.2.7 closure evidence

- [x] Focused verification passed with **14 tests**. Complete API verification
  passed with **577 tests**, with only the existing Starlette TestClient/httpx
  deprecation warning; the complete local quality gate passed.
- [x] No schema migration was introduced. Persistent PostgreSQL remained at
  `0071_structured_shortage_occupation_evidence`.
- [x] The canonical PostgreSQL backup immediately before the first successful
  live pathway-v3 write is
  `C:\Users\Bennet Allryn\Downloads\gmai-postgres-before-at-pathway-v3-20260811-022050.dump`
  (3,673,174 bytes; SHA-256
  `590342DB52783D804034D3F5C36F97B9910897F482E7E6FCB794682DDA494383`).
- [x] Created Austria skilled-worker pathway version 3
  `35412414-2cfd-489b-8731-c375d41d6f52` from version 2
  `cb17657f-be9f-4ea9-b7ce-795cf0e1b1d5`. Version 3 remains `draft`,
  with no `approved_by` value and no `published_at` value.
- [x] Version 3 carries exactly three required publication evidence roles:
  `core_route`, `national_occupation_list`, and `regional_occupation_list`.
  The structured roles pin the existing immutable 2026 national snapshot
  `a1032556-81f1-49bf-acd6-fa8f43e45341` and regional snapshot
  `7a3503f3-dc9d-4ded-bf31-7a80738b7434`.
- [x] Publication-readiness evaluation remains fail-closed:
  `ready = false` and `requires_independent_reviewer = true`.
  `core_route` is approved, while both `national_occupation_list` and
  `regional_occupation_list` remain `pending_review`.
- [x] Idempotency re-run returned `created = false` for the same version
  `35412414-2cfd-489b-8731-c375d41d6f52`. A direct database check confirmed
  exactly three pathway versions exist; no version 4 was created.
- [x] Neither 2026 supplemental source was approved, no pathway version was
  published, and the genuine independent-review/external-validation gates
  remain held.

### 13.10.2.8 Independent review readiness and certification evidence packs

- [x] Add a deterministic reviewer-facing evidence pack for source certifications that
  have structured shortage-occupation projections. The pack binds the certification,
  jurisdiction, authority, official source, immutable source snapshot, declared
  year/scope, extraction version, entry count, entry-set SHA-256, and every structured
  occupation row without inferring case eligibility.
- [x] Include the immutable source text alongside the structured rows so a reviewer can
  perform a source-to-projection comparison. The deterministic pack SHA-256 is computed
  from canonical evidence identity/content rather than from mutable review status.
- [x] Fail closed when a source has multiple structured projections unless the reviewer
  pins the exact `source_snapshot_id`; a certification review must not silently choose
  among multiple years or snapshots.
- [x] Require an explicit independent-human attestation plus the exact deterministic
  evidence-pack SHA-256 before any certification backed by structured occupation data can
  be approved or rejected. Reviewer/proposer identity separation is case-insensitive.
- [x] Preserve the existing review path for certifications with no structured projection,
  avoiding an unrelated migration or forced retrofit of historical source reviews.
- [x] Record structured review evidence in the durable audit log, including reviewer,
  decision, pack version/hash, pinned source snapshot, structured projection identity,
  and human attestation. The source certification remains the only explicit approval
  action; generating a review pack grants no approval.
- [x] Aggregate pathway publication-readiness blockers instead of exposing only the first
  source-certification failure. Austria v3 can therefore report both national and
  regional pending-review blockers at the same time while remaining fail-closed.
- [x] Keep Alembic head at `0071_structured_shortage_occupation_evidence`; this slice
  changes review/readiness behavior and requires no database migration.
- [x] Apply the incremental patch to clean base `b61ddd7`, run focused tests, then run the
  complete API/local quality gate before restarting the host API.
- [x] Restart the host API and materialize read-only reviewer packs for the live Austria
  2026 national and regional certifications. Record each exact pack SHA-256 and confirm
  the packs pin the already materialized 64/66-entry projections.
- [x] Confirm both live 2026 certifications remain `pending_review`, Austria pathway v3
  remains draft/unapproved/unpublished, and publication readiness reports both structured
  certification blockers after pack generation.
- [x] Do not submit the independent-human attestation, approve/reject either certification,
  publish v3, or release the external-validation gate unless a genuine separate human
  reviewer personally performs the review.

#### Phase 13.10.2.8 closure evidence

- [x] Focused and complete verification passed. The complete API suite reached
  **583 passed**, with only the existing Starlette TestClient/httpx deprecation
  warning, and the complete local quality gate passed.
- [x] No database migration or live regulatory write was required. Persistent
  PostgreSQL remained at `0071_structured_shortage_occupation_evidence`.
- [x] Generated a deterministic independent-review evidence pack for Austria's
  2026 national shortage-occupation source certification
  `599f7ce7-b85e-4d02-b3ca-ea17b75aba84`, covering all **64** structured
  national entries.
- [x] National independent-review pack SHA-256
  `b8073504eef684a1d02c5e99efb16c9bf1225c89c807196ce103b0bb9b9cffe7`.
- [x] Generated a deterministic independent-review evidence pack for Austria's
  2026 regional shortage-occupation source certification
  `f4cf5f04-0519-4cad-b5c2-88ec1183ded5`, covering all **66** structured
  regional entries.
- [x] Regional independent-review pack SHA-256
  `46f4b74a379aaea9a3bd90f1da14166a1ea408842020cf2b700059ff8687920d`.
- [x] Review-pack generation remained read-only. Both exact certifications
  remained `pending_review`; no independent-human attestation was submitted.
- [x] Austria skilled-worker pathway version 3
  `35412414-2cfd-489b-8731-c375d41d6f52` remained `draft`, unapproved and
  unpublished.
- [x] Publication readiness remained fail-closed with
  `ready = false` and `requires_independent_reviewer = true`. Readiness now
  aggregates both outstanding required-evidence blockers:
  `national_occupation_list` and `regional_occupation_list`.
- [x] The generated review packs are preparation artifacts only. Certification
  approval remains reserved for a genuine separate human reviewer who personally
  reviews the exact evidence pack.


### 13.10.2.9 Independent review workflow UX and audit closure

- [x] Add a dedicated `/source-certification-review` operator workspace for structured
  source certifications instead of forcing independent reviewers through generic
  registry controls.
- [x] Add a deterministic read-only structured certification review queue that exposes
  pending certification identity, jurisdiction/authority/source provenance, available
  immutable projections, exact pack readiness, authenticated reviewer identity conflict,
  and whether submission is currently allowed.
- [x] Add a bounded review-workspace API that returns the exact deterministic evidence
  pack plus explicit submission requirements and durable review history from the existing
  audit log. The workspace performs no certification mutation.
- [x] Preserve fail-closed multi-projection behavior in the UX: when more than one
  structured projection exists, no review pack or submission is available until the
  reviewer pins an exact `source_snapshot_id`.
- [x] Require the reviewer UI to confirm the exact 64-character deterministic pack
  SHA-256, enter substantive review notes, and explicitly attest genuine independent
  human review before the existing certification-review endpoint can be submitted.
- [x] Display immutable source text and structured entries side-by-side, expose the
  source ordinal/aliases/province mapping/entry hash, and allow downloading the exact
  JSON review pack for offline inspection without changing review state.
- [x] Surface durable review audit receipts in the same workspace after a decision,
  including actor, decision, notes, attestation state, exact pack hash, snapshot, and
  structured projection identity.
- [x] Keep certification approval and pathway publication separate. A successful source
  review does not publish Austria pathway v3 or release the external-validation gate.
- [x] Keep Alembic at `0071_structured_shortage_occupation_evidence`; reuse the existing
  certification and audit-log tables rather than introducing a migration for presentation
  or derived review state.
- [ ] Apply the incremental patch to clean base `934b073` and run focused API tests plus
  the complete API/local quality gate including the Next.js production build.
- [ ] Restart the host API and perform a read-only live smoke of the Austria 2026 review
  queue/workspaces. Confirm the national pack hash remains
  `b8073504eef684a1d02c5e99efb16c9bf1225c89c807196ce103b0bb9b9cffe7` and the regional
  pack hash remains `46f4b74a379aaea9a3bd90f1da14166a1ea408842020cf2b700059ff8687920d`.
- [ ] Confirm the live smoke leaves both certifications `pending_review`, pathway v3
  `draft`, and the publication/external-validation gates held.
- [ ] Do not use the new submission UI to approve or reject either live Austria source
  unless a genuine separate human reviewer personally completes the exact pack review.

#### Phase 13.10.2.9 closure evidence

- [x] Complete verification passed with **589 API tests** and the complete local
  quality gate. The only warning remained the existing Starlette
  TestClient/httpx deprecation warning.
- [x] No schema migration or live regulatory write was introduced. Persistent
  PostgreSQL remained at `0071_structured_shortage_occupation_evidence`.
- [x] Added the dedicated `/source-certification-review` workspace with
  structured-review queue, deterministic evidence-pack inspection, exact
  source/projection comparison, pack download, reviewer identity controls,
  explicit pack-hash confirmation, human attestation controls, and review
  history/audit presentation.
- [x] Read-only Austria reviewer-workspace smoke passed with exactly two pending
  structured source certifications in the queue.
- [x] National certification
  `599f7ce7-b85e-4d02-b3ca-ea17b75aba84` remained `pending_review`; its
  workspace reported pack state `ready`, **64 entries**, zero review-history
  entries, and deterministic pack SHA-256
  `b8073504eef684a1d02c5e99efb16c9bf1225c89c807196ce103b0bb9b9cffe7`.
- [x] Regional certification
  `f4cf5f04-0519-4cad-b5c2-88ec1183ded5` remained `pending_review`; its
  workspace reported pack state `ready`, **66 entries**, zero review-history
  entries, and deterministic pack SHA-256
  `46f4b74a379aaea9a3bd90f1da14166a1ea408842020cf2b700059ff8687920d`.
- [x] Austria skilled-worker pathway version 3
  `35412414-2cfd-489b-8731-c375d41d6f52` remained `draft`, with
  `publication_ready = false` and `requires_independent_reviewer = true`.
- [x] Publication readiness continued to expose both outstanding required
  evidence blockers: `national_occupation_list` and
  `regional_occupation_list`, while `core_route` remained approved.
- [x] Pre-smoke and post-smoke database hold-state checks were identical:
  national 2026 structured entries remained **64**, regional remained **66**,
  both certifications remained `pending_review`, and pathway version 3
  remained draft.
- [x] The smoke performed no certification review, source approval, pathway
  publication, or external-validation release. A live decision remains reserved
  for a genuine separate human reviewer who personally reviews the exact pack.


### 13.11 Finance/CFO bounded department runtime

- [x] Enable the Finance department runtime for bounded `internal.analysis` only.
- [x] Add `Financial Analyst` and `Accounting Lead` L2 specialist positions
  reporting to the CFO, with role cards, controlled-agent handlers, output
  schemas, and registry entries.
- [x] Harden the CFO position contract with required specialists, required
  evidence fields, and explicit prohibited actions.
- [x] Require financial evidence for cost structure, pricing model, revenue
  model, budget constraints, scenario parameters, AP/AR aging, reconciliation,
  audit trail, chart of accounts, compliance controls, and tax/treaty implications.
- [x] Block Finance specialists from funds movement, pricing changes, spend
  commitments, contract signing, tax/regulatory representations, journal
  entries, external sends, and any external action.
- [x] Add `delegate_finance_work` and `DEPARTMENT_EXECUTION_ADAPTERS` integration
  so the CFO delegates to both specialists and the CEO receives an evidence-backed
  L3 decision receipt when the review is complete.
- [x] Add router and governance integration so Finance work items are assigned
  to the CFO and routed through the same bounded execution path as other
  hardened departments.
- [x] Add focused regressions for Finance internal analysis, incomplete evidence
  hold, suspended specialist resume, CEO handoff, CFO contract-mismatch repair,
  prohibited-action enforcement, specialist isolation, and CFO-only assignment.
- [x] Update the foundation bootstrap position count to 28 and verify the
  CFO/Finance reporting line.
- [x] Keep Alembic at `0071_structured_shortage_occupation_evidence`; this slice
  introduces no schema migration.

#### Phase 13.11 closure evidence

- [x] Complete verification passed with **597 API tests, 0 failed**, with only
  the existing Starlette TestClient/httpx deprecation warning.
- [x] Web production build passed with 37 routes.
- [x] No schema migration or live financial write was introduced.
- [x] Communications, People, and Legal remain held runtimes.
- [x] The Austria 2026 source certifications, pathway v3, and external-validation
  gate remain unchanged and held.


### 13.12 Communications/CCO bounded department runtime

- [x] Enable the Communications department runtime for bounded `internal.analysis` only.
- [x] Add `PR / Communications Lead` and `Government Relations Lead` L2 specialist
  positions under the CCO, with role cards, controlled-agent handlers, registry
  entries, output schemas, and hardened position contracts.
- [x] Add `COMMUNICATIONS_DELEGATION_SPECS`, required evidence fields, specialist
  output fields, prohibited actions, preflight checks, and the `delegate_communications_work`
  execution adapter in `organization_governance.py`.
- [x] Wire `delegate_communications_work` into the `/work-items` create endpoint.
- [x] Add Communications regression tests mirroring Finance/Marketing coverage:
  required-delegate execution, incomplete evidence hold, suspended specialist
  hold/resume, prohibited-action enforcement, non-department rejection, CCO-only
  assignment, and L3 CEO handoff.
- [x] Update platform-hardening tests for the Communications runtime and prohibited
  actions.
- [x] Update controlled-agent and role-card-loader canonical agent sets.

#### Phase 13.12 closure evidence

- [x] Complete verification passed with **605 API tests, 0 failed**, with only
  the existing Starlette TestClient/httpx deprecation warning.
- [x] Web production build passed with 37 routes.
- [x] No schema migration or live external communication was introduced.
- [x] People and Legal remain held runtimes.
- [x] The Austria 2026 source certifications, pathway v3, and external-validation
  gate remain unchanged and held.


### 13.13 People/CHRO bounded department runtime

- [x] Enable the People department runtime for bounded `internal.analysis` only.
- [x] Add `HR Lead` and `Culture / Recruitment Lead` L2 specialist positions
  under the CHRO, with role cards, controlled-agent handlers, registry entries,
  output schemas, and hardened position contracts.
- [x] Add `PEOPLE_DELEGATION_SPECS`, required evidence fields, specialist output
  fields, prohibited actions, preflight checks, and the `delegate_people_work`
  execution adapter in `organization_governance.py`.
- [x] Wire `delegate_people_work` into the `/work-items` create endpoint.
- [x] Add People regression tests mirroring Communications coverage: required-delegate
  execution, incomplete evidence hold, suspended specialist hold/resume,
  prohibited-action enforcement, non-department rejection, CHRO-only assignment,
  and L3 CEO handoff.
- [x] Update platform-hardening tests for the People runtime and prohibited actions.
- [x] Update controlled-agent and role-card-loader canonical agent sets.

#### Phase 13.13 closure evidence

- [x] Complete verification passed with **613 API tests, 0 failed**, with only
  the existing Starlette TestClient/httpx deprecation warning.
- [x] Web production build passed with 37 routes.
- [x] No schema migration or live employment action was introduced.
- [x] Legal remains the only held runtime.
- [x] The Austria 2026 source certifications, pathway v3, and external-validation
  gate remain unchanged and held.


### 13.14 Legal/CLO bounded department runtime

- [x] Enable the Legal department runtime for bounded `internal.analysis` only.
- [x] Add `General Counsel` and `Public Policy / Compliance Lead` L2 specialist
  positions under the CLO, with role cards, controlled-agent handlers, registry
  entries, output schemas, and hardened position contracts.
- [x] Add `LEGAL_DELEGATION_SPECS`, required evidence fields, specialist output
  fields, prohibited actions, preflight checks, and the `delegate_legal_work`
  execution adapter in `organization_governance.py`.
- [x] Wire `delegate_legal_work` into the `/work-items` create endpoint.
- [x] Add Legal regression tests mirroring People coverage: required-delegate
  execution, incomplete evidence hold, suspended specialist hold/resume,
  prohibited-action enforcement, non-department rejection, CLO-only assignment,
  and L3 CEO handoff.
- [x] Update platform-hardening tests for the Legal runtime and prohibited actions.
- [x] Update controlled-agent and role-card-loader canonical agent sets.

#### Phase 13.14 closure evidence

- [x] Complete verification passed with **627 API tests, 0 failed**, with only
  the existing Starlette TestClient/httpx deprecation warning.
- [x] Web production build passed with 37 routes.
- [x] No schema migration or live legal action was introduced.
- [x] All executive department runtimes (Operations, Technology, Product,
  Security/CISO, Security Operations/SOC, Marketing/CMO, Finance/CFO,
  Communications/CCO, People/CHRO, and Legal/CLO) are now delivered.
- [x] The Austria 2026 source certifications, pathway v3, and external-validation
  gate remain unchanged and held.


### 13.15 Validation programme and Round 6 correctness gate

The original Phase 13.15 plan described the first external-human operational run.
Subsequent shadow rounds exposed and corrected the Austria decision pipeline through
Phase 13.10.2.15.

**Status: COMPLETE — ROUND 6 CORRECTNESS DISPOSITION: PASS.** The fresh Round 6
shadow reviews found zero Critical/High correctness findings and zero unsupported
legal certainty. Phase 13.16.0 is unlocked but not started. Genuine external-human
acceptance is Phase 13.17 and must not be claimed from these shadow sessions.

- [x] Deliver and regression-test the versioned validation scenario/run/review/finding
  framework, deterministic gate, and operator workspace.
- [x] Preserve all earlier shadow-round findings, remediation history, comparisons,
  and audit evidence without rewriting prior assessments.
- [x] Close Phase 13.10.2.15 after the rendered Eligibility and Planning gate passes.
- [x] Create one fresh synthetic Austria skilled-employment case for the Round 6
  mobility-user shadow session; do not reuse the engineering-history-heavy Round 5 case.
- [x] Use the comparable persona: India to Austria, skilled employment, Software
  Engineer, four years' experience, no Austrian job offer, qualification recognition
  unknown, German A2, and province unknown.
- [x] Conduct a separate fresh professional shadow review against the resulting case
  and assess legal certainty, traceability, lifecycle, and decision integrity.
- [x] Categorize findings as correctness, experience/presentation, or operational
  evidence so UX debt does not obscure correctness and vice versa.
- [x] Confirm zero Critical/High correctness findings and zero unsupported legal
  certainty before unlocking Phase 13.16.0. Confirm candidate family, occupation
  conditionality, material gaps, costs, lifecycle/certification state, production/draft
  boundary, and material traceability are safe.
- [ ] If a future correctness gate fails, open only the bounded correction needed
  and run another fresh numbered validation round. Do not begin gated experience
  work on a failed correctness result. This conditional branch was not triggered
  by Round 6.
- [x] Record the
  [Round 6 PASS disposition](ROUND_6_CORRECTNESS_DISPOSITION_V13_15.md) and unlock
  Phase 13.16.0 without starting it. Medium/Low experience findings are formal
  Phase 13.16 inputs rather than an automatic correctness veto.

#### Phase 13.15 retained operational assets

- Historical runbook: [EXTERNAL_VALIDATION_RUNBOOK_V13_15.md](EXTERNAL_VALIDATION_RUNBOOK_V13_15.md)
- Round 6 disposition: [ROUND_6_CORRECTNESS_DISPOSITION_V13_15.md](ROUND_6_CORRECTNESS_DISPOSITION_V13_15.md)
- Scenario fixture: `apps/api/validation/scenarios/austria_skilled_worker_v1.json`
- Validation workspace: `/validation`
- Gate evaluation endpoint: `POST /api/v1/external-validation/runs/{run_id}/evaluate`

### 13.17 Genuine external-human acceptance and Phase 13 disposition

After Phase 13.16.10 passes integrated acceptance, validate the revised product with
people who are genuinely independent of implementation and shadow-review history.

- [ ] Recruit one distinct mobility user and one independent professional/operator.
- [ ] Run both through the end-to-end role-appropriate experience while recording
  founder interventions, task completion, comprehension, accessibility barriers, and
  confidence in material decision and evidence boundaries.
- [ ] Pin reviews to the exact case, profile, assessment, pathway comparison, evidence,
  UI release, and scenario shown to each participant.
- [ ] Record all findings with severity and category in the validation ledger.
- [ ] Resolve and retest every Critical/High correctness, safety, governance, security,
  accessibility, or task-completion finding. Board acceptance may apply only where the
  existing policy explicitly permits it.
- [ ] Confirm no experience layer obscures draft/production state, pending
  certification, material blockers, non-reliance warnings, or evidence provenance.
- [ ] Evaluate the deterministic external gate and record the Phase 13 disposition.
- [ ] Do not unlock Phase 14 or time-bounded cross-functional programmes until the
  Phase 13 external-human gate passes.


## 10. Historical Evidence

- Release-level history: [CHANGELOG.md](CHANGELOG.md)
- Canonical product scope: [GLOBAL_MOBILITY_AIOS_VISION_V1.md](GLOBAL_MOBILITY_AIOS_VISION_V1.md)
- Architecture: [ARCHITECTURE.md](ARCHITECTURE.md)
- Security baseline: [SECURITY_AND_COMPLIANCE.md](SECURITY_AND_COMPLIANCE.md)
- Agent organization target:
  [AI_ORGANIZATION_GOVERNANCE_V13_0.md](AI_ORGANIZATION_GOVERNANCE_V13_0.md)
- Feature-specific evidence: versioned documents under `docs/`
- Exact implementation history: Git commits and Alembic migrations
