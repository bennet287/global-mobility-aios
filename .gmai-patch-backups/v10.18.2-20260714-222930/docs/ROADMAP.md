# Global Mobility AIOS Delivery Roadmap

The canonical product scope is defined in
[`GLOBAL_MOBILITY_AIOS_VISION_V1.md`](GLOBAL_MOBILITY_AIOS_VISION_V1.md). This
roadmap turns that complete vision into incremental delivery phases. A later phase
does not remove any capability from the canonical blueprint.

## Delivery Status — v10.18.1 (2026-07-14)

Current database migration head: `0031_global_coverage_source_onboarding` (unchanged in v10.18.1).

- v10.18.1 corrects the Austria starter-tranche monitor to a canonical HTTPS endpoint after the upstream short URL redirected to HTTP. The retrieval security policy remains fail-closed; existing deployments use an audited same-host source-remediation script before retrying baseline capture.
- v10.18 adds controlled, idempotent baseline capture for independently approved evidence-batch sources. It pre-creates durable retrieval runs, queues the exact monitored source through Celery, records immutable snapshots, and never publishes a verified rule or coverage claim.
- v10.17 adds the first current official-evidence tranche for Austria, Germany, Canada, Australia, and New Zealand, plus offline validation and a PowerShell submission workflow. The linked assessment/certification records still require independent decisions before baseline capture is eligible.
- v10.16 extends coverage evidence batches with atomic authority, official-source, and monitor onboarding plus automatically linked pending primary-source certification proposals.
- v10.15.1 fixed PostgreSQL-safe compilation of the `0030` coverage-batch index names and added an offline PostgreSQL migration regression gate.

- Phase 7 regulatory-intelligence foundation is complete.
- Phase 8 universal profile, pathway catalogue, comparisons, and single-pathway timelines are complete.
- Phase 9 document intelligence is complete: extraction, profile/application validation,
  expiry reminders, missing-document and inconsistency detection, human-reviewed integrity
  indicators, and signed expiring document access with production storage controls.
- Phase 10A self-updating intelligence, controlled classification, relational knowledge
  graph, and pathway-impact linking are complete.
- Phase 10C dashboard filtering is complete across freshness, coverage, authority,
  confidence, materiality, and review state.
- Phase 10D is complete: explicit reassessment acceptance preserves pinned assessments,
  while immutable country-ranking assessments compare only human-published pathways,
  explain costs, trade-offs, long-term residence dependencies, and uncertainty, and preserve
  the Phase 10B global-coverage claim boundary.
- Phase 10E is complete: immutable, human-confirmed multi-year and multi-country scenarios
  model reviewed study, graduate-rights, work, settlement, permanent-residence, and
  citizenship-review transitions. Reviewed rule changes create a new scenario version and
  never rewrite the original plan.
- Phase 10B now has a prioritized evidence worklist and atomic, idempotent evidence batches
  for up to 50 jurisdictions. The same package can onboard authorities, official sources, and
  monitors, then create pending certification proposals while preserving the separate-reviewer
  requirement. Approved batch items can now queue controlled baseline retrieval and immutable
  source snapshots, while pending or rejected evidence remains ineligible. The first five-
  jurisdiction tranche still changes no coverage-gate total until all review, freshness, and
  verified-rule gates pass.
- The remaining Phase 10 delivery work is factual Phase 10B evidence collection and human
  approval across every required jurisdiction.
- Global coverage claims remain blocked until the authority, source, freshness,
  verified-rule, and jurisdiction-assessment gates are complete.

### Recommended execution order

1. Complete independent review of the v10.17 Austria, Germany, Canada, Australia, and New Zealand evidence tranche.
2. Use the v10.18 controlled baseline action to capture immutable snapshots only for approved batch items; inspect and remediate retrieval failures without bypassing source controls.
3. Review detected changes and publish at least one verified rule per approved jurisdiction through the existing classification, review, and publication gates.
4. Use the v10.15 worklist and v10.16 atomic onboarding path to prepare additional regional tranches without bulk-inferring jurisdiction relationships.
5. Maintain fresh monitors and continue expanding the human-published pathway catalogue without claiming complete global coverage until every Phase 10B release gate passes.

### Remaining-work ledger

- **Phase 9:** complete.
- **Phase 10B:** software workflow complete; jurisdiction evidence onboarding and independent
  review remain operationally incomplete.
- **Phase 10C:** complete.
- **Phase 10D:** complete.
- **Phase 10E:** complete.
- **Phases 11–13:** not started; all listed capability groups remain future work.

## Current Baseline: MVP Phases 1-5

- Local/Docker FastAPI and Next.js platform
- CRM, public intake, client return, lead detail, and operator workbench
- Official-source Truth Engine and human review queues
- Documents, MinIO-ready storage, browser OCR, and verification actions
- Eligibility assessment and coaching
- Opportunity catalogue and deterministic matching
- Controlled agents and asynchronous batch execution
- Draft communications and trigger-based automatic communication records
- Audit, RBAC, demo/release checks, and Alembic foundation

## Phase 6: Foundation Alignment

- Make this roadmap and the product blueprint canonical
- Repair controlled-agent contract tests
- Complete migrations for every current SQLModel table
- Align public routes, browser sessions, local header authentication, and CORS
- Refresh architecture and operational documentation
- Keep frontend build, API tests, schema checks, and repository policy green

## Phase 7: Regulatory Intelligence Foundation

- [x] Add jurisdiction, immigration authority, and source schedule models
- [x] Support country, territory, and autonomous-jurisdiction identifiers
- [x] Ingest official-source content into immutable snapshots with hashes and timestamps
- [x] Compare snapshots and produce structured regulatory change sets
- [x] Queue every material change for human validation
- [x] Publish approved verified rules with evidence links and effective dates
- [x] Execute scheduled retrieval through controlled background workers
- [x] Add safe generic HTML, text, JSON, XML, and PDF parser routing
- [x] Add a Next.js regulatory operations workspace for health, review, publication, rules, and evidence
- [x] Add rule supersession and explicit retirement controls with audit history
- [x] Expose source-monitor freshness, due-state, errors, and retrieval failures
- [x] Add transactional jurisdiction, authority, source, and monitor onboarding with domain allowlists
- [x] Add coverage and freshness rollups by jurisdiction, authority, and regulatory domain
- [x] Add configurable authority-specific gazette and structured API parser profiles
- [x] Detect new, changed, and retired programs from structured authority catalogues

## Phase 8: Universal Mobility Profile and Pathways

- [x] Expand the profile across education, work, skills, languages, family,
  finances, goals, constraints, consent, and evidence
  - [x] Add immutable versions, supersession, completeness, and readiness stages
  - [x] Validate lead-owned document evidence and record purpose-limited consent
  - [x] Restrict eligibility and opportunity processing after consent withdrawal
  - [x] Persist profile-version provenance on eligibility conclusions
  - [x] Add the operator profile workspace and version history
- [x] Build a versioned pathway catalogue for study, work, visa, scholarship,
  settlement, family, and digital-nomad routes
  - [x] Add immutable draft, published, superseded, and retired versions
  - [x] Require official sources, immutable snapshots, verified rules, and human review for publication
  - [x] Add deterministic profile matching with consent enforcement and missing-evidence results
  - [x] Add the pathway governance workspace and version ledger
- [x] Connect eligibility conclusions to verified rules and source references
  - [x] Persist pathway, version, source, snapshot, and verified-rule provenance in assessment factors
- [x] Add cost, risk, alternative-pathway, and missing-evidence explanations
  - [x] Persist comparisons against exact profile and pathway versions
  - [x] Separate payable fees, recurring costs, and minimum-funds thresholds
  - [x] Explain declared, evidence-derived, and regulatory-freshness risks
  - [x] Rank alternatives with tradeoffs, benefits, gaps, and source provenance
  - [x] Add the Mobility Planning workspace and immutable comparison history
- [x] Build the multi-stage mobility timeline engine
  - [x] Generate deterministic profile-to-settlement stages from an immutable pathway comparison
  - [x] Enforce sequential dependencies, profile consent, and exact profile/pathway-version provenance
  - [x] Require audited human approval notes for eligibility, route, application, submission, and decision gates
  - [x] Keep application approval, authority decisions, and regulatory claims in their existing controlled systems
  - [x] Add the Mobility Timelines operator workspace with evidence, blockers, ownership, and due dates

## Phase 9: Document Intelligence

- [x] Server-side OCR/extraction jobs and structured document schemas
  - [x] Add Celery extraction jobs tied to immutable upload hashes and exact schema versions
  - [x] Extract text server-side from text files, PDF text layers, and Tesseract-supported images
  - [x] Publish baseline schemas for passports, CVs, degrees, transcripts, employment letters, and bank statements
  - [x] Require human approval or rejection without automatically verifying authenticity or mutating profile facts
  - [x] Add restricted document-intelligence APIs and an operator review workspace
- [x] Validation against profile and application facts
  - [x] Compare only human-approved extractions with exact immutable profile versions
  - [x] Snapshot lead identity and application facts inside every assessment
  - [x] Separate matches, mismatches, missing values, and semantically non-comparable facts
  - [x] Require human assessment review without overwriting documents, profiles, or applications
  - [x] Add consistency findings and immutable assessment history to the Document Intelligence workspace
- [x] Expiry monitoring and reminders
  - [x] Add deterministic 90, 30, 7-day, and expired urgency bands
  - [x] Create immutable, deduplicated reminder tasks from recorded document expiry metadata
  - [x] Supersede stale tasks when urgency increases or an expiry date changes
  - [x] Schedule controlled scans and expose lead-scoped manual scanning
  - [x] Require human review notes without sending uncontrolled external messages
  - [x] Add expiry metrics, task review, and audit history to Document Intelligence
- [x] Missing-document and inconsistency detection
  - [x] Resolve exact human-published pathway versions, eligibility assessments, or application-domain requirement snapshots
  - [x] Create immutable, content-addressed coverage assessments without creating or modifying source records
  - [x] Distinguish satisfied, missing, optional, expired, rejected, unverified, mismatch, and duplicate-conflict outcomes
  - [x] Reuse approved document-consistency findings as broader cross-document risk signals
  - [x] Add deduplicated scheduled and lead-scoped scans with mandatory human review and audit history
  - [x] Add requirement metrics, findings, provenance, and review actions to Document Intelligence
- [x] Human-reviewed fraud-risk indicators
  - [x] Create immutable, content-addressed integrity assessments with exact source provenance
  - [x] Detect exact-file reuse, approved identity/material mismatches, duplicate conflicts, rejected evidence, and hash-integrity failures
  - [x] Detect approved identifier reuse across leads while storing only hashes and masked values
  - [x] Require controlled human triage without declaring fraud or taking adverse action
  - [x] Add scheduled and lead-scoped scans, audit history, metrics, and review controls
- [x] Signed, expiring document access and production object-storage controls
  - [x] Issue short-lived, audited access grants instead of durable or direct object URLs
  - [x] Enforce authenticated role, lead ownership, document scope, and purpose on every grant
  - [x] Support local storage and MinIO without exposing storage credentials or unrestricted object keys
  - [x] Record grant creation, access, expiry, revocation, denial, and actor provenance
  - [x] Add explicit revocation and fail-closed handling for expired, altered, missing, or unauthorized objects
  - [x] Add production bucket privacy, TLS, encryption, retention/lifecycle, backup, and recovery guidance
  - [x] Add restricted operator controls and regression coverage without changing document verification state

## Phase 10: Global Self-Updating Mobility Intelligence — Highest Priority

### 10A. Self-Updating Visa Intelligence Engine

- [x] Continuously schedule controlled retrieval from allowlisted government, authority, and gazette sources
- [x] Detect immutable source changes through content hashes and snapshot comparison
- [x] Extract generic HTML, text, JSON, XML, PDF, gazette, and structured programme catalogues
- [x] Classify new programmes, removals, rule changes, salary thresholds, age limits,
  occupation lists, quotas, processing times, and policy changes
- [x] Route every material change through human validation before verified-rule publication
- [x] Refresh relational intelligence and dashboards from reviewed changes and verified rules
- [x] Add controlled model-assisted classification proposals with confidence, evidence, and deterministic fallback
- [x] Add a provenance-preserving regulatory knowledge graph updated only from human-published rules
- [x] Link graph updates to affected pathway versions without silently changing client assessments

Target pipeline:

```text
Government website / official API / gazette
  -> controlled crawler
  -> immutable snapshot and extraction
  -> structured classification proposal
  -> deterministic comparison
  -> human validation when material
  -> verified rule and knowledge-graph update
  -> global dashboard refresh
```

Delivered classification governance: every detected change receives a persisted
deterministic proposal tied to exact snapshots and diff evidence. Operators can
request configured model assistance; invalid, unavailable, or disabled model
execution falls back deterministically with a visible reason. A human must
accept one proposal before the separate regulatory-change review and verified-
rule publication gates can proceed. See
`docs/CONTROLLED_REGULATORY_CLASSIFICATION_V10_4.md`.

Delivered graph governance: human-published verified rules now transactionally
project typed jurisdiction, domain, authority, source, snapshot, change, and
rule nodes with per-edge rule/change/snapshot provenance. Supersession and
retirement preserve history, while controlled synchronization ignores
unpublished rules. See `docs/REGULATORY_KNOWLEDGE_GRAPH_V10_5.md`.

Delivered pathway-impact governance: rule publication, supersession, and
retirement now create idempotent, review-gated links to exact currently
published pathway versions using jurisdiction, domain, source, and direct-rule
evidence. Existing pathway criteria, comparisons, timelines, and client
conclusions remain immutable; resolving an impact requires an explicitly
published newer pathway version. See
`docs/PATHWAY_REGULATORY_IMPACT_LINKS_V10_6.md`.

### 10B. Global Country and Immigration-Jurisdiction Coverage

- [x] Support country, territory, and autonomous-immigration-jurisdiction types
- [x] Support parent jurisdictions, authorities, official sources, domains, and independent schedules
- [x] Seed and version a canonical registry covering every UN member/observer state and ISO 3166-1 entry
- [x] Register autonomous jurisdictions and territories without inferring their immigration-rule relationship
- [x] Add evidence-backed proposal, separate-reviewer approval, rejection, and supersession for immigration-rule relationships
- [x] Add a prioritized region/gap worklist for the remaining jurisdiction evidence programme
- [x] Add atomic, idempotent evidence batches that create pending proposals only
- [x] Add atomic batch onboarding for authorities, official sources, and source monitors
- [x] Automatically link onboarded sources to pending primary-source certification proposals
- [x] Preserve independent review and immutable batch provenance at scale
- [ ] Complete reviewed independent, inherited, shared, or not-applicable assessments for every required jurisdiction
- [x] Add separate-reviewer certification for each jurisdiction's primary immigration authority and official source
- [ ] Establish at least one reviewed primary immigration authority and official source per jurisdiction
- [x] Track country-level source, authority, freshness, verified-rule, and immigration-rule-assessment gaps
- [x] Prevent “global coverage” claims unless registry and source-coverage release gates pass

Delivered registry foundation: immutable dataset-hashed releases from the fixed
UN M49 source with ISO 3166-1 scope reconciliation, 249 active entries, a
reproducible import command, coverage-gap API, release gate, and operator ledger.
Territories remain `unassessed` for independent immigration rules until reviewed;
their presence in the registry is not treated as verified immigration coverage.

Initial named coverage includes Austria, Germany, Canada, UAE, Singapore, Japan,
New Zealand, South Korea, Brazil, South Africa, Qatar, Oman, Saudi Arabia, and
all remaining registry jurisdictions—not only this example list.

Delivered v10.15 coverage operations: a prioritized release-derived worklist and
immutable SHA-256-keyed evidence batches for up to 50 jurisdictions. Batches are
atomic, create only pending assessment/certification proposals, and never bypass
the separate-reviewer or global-coverage release gates. See
`docs/GLOBAL_COVERAGE_EVIDENCE_OPERATIONS_V10_15.md`.

Delivered v10.16 source onboarding: the same atomic evidence package can create or update
a registry-bound regulatory authority, HTTPS official source, allowlisted source monitor,
and pending primary-source certification. Any invalid row rolls back the entire package;
source ownership conflicts and unsafe URLs still fail closed. Certification remains subject
to an independent reviewer and does not establish coverage by itself. See
`docs/GLOBAL_COVERAGE_SOURCE_ONBOARDING_V10_16.md`.

Delivered v10.17 official evidence starter: a validated, content-addressed pack prepares
Austria, Germany, Canada, Australia, and New Zealand for review using current official
authority and immigration portal evidence. Submission creates five pending immigration-rule
assessments and five pending primary-source certifications; it creates no approvals, source
snapshots, verified rules, or coverage claim. Combined rows link each assessment to the exact
newly onboarded official source. See
`docs/GLOBAL_COVERAGE_OFFICIAL_EVIDENCE_STARTER_V10_17.md`.

Delivered v10.18 controlled baseline capture: independently approved batch items can create
durable queued retrieval runs and dispatch the exact allowlisted monitors through the existing
controlled Celery worker. Existing snapshots and queued/running work are not duplicated; failed
runs remain visible for deliberate retry. The workflow captures evidence only and cannot publish
a verified rule or satisfy the global-coverage gate by itself. See
`docs/CONTROLLED_COVERAGE_BASELINE_CAPTURE_V10_18.md`.

### 10C. Live Global Intelligence Dashboard

- [x] New Visa Programmes dashboard with introductions, removals, provenance, and visible review state
- [x] Immigration Changes dashboard with countries and changes updated today
- [x] Processing-Time dashboard with windowed change history and visible review state
- [x] Skilled-Occupation dashboard with shortage/eligible-list changes
- [x] Salary and Investment Threshold dashboard
- [x] Global country activity heatmap across onboarded jurisdictions
- [x] Evidence-based Opportunity Radar calculated only from human-published events
- [x] Freshness, coverage, authority, confidence, materiality, and review-state filters
  - [x] Apply one evidence scope consistently to counts, change feeds, heatmaps, and Opportunity Radar
  - [x] Expose verified-rule or classification-proposal confidence provenance without inventing confidence
  - [x] Preserve pending-review visibility while keeping the Opportunity Radar human-published-only
- [x] Explicitly label activity signals as evidence summaries—not predictions or visa recommendations

Delivered foundation: `GET /api/v1/global-intelligence/dashboard` and the
`/global-intelligence` operator workspace. The dashboard deliberately displays
an onboarded-coverage warning until the Phase 10B global registry release gate passes.

### 10D. Global User Intelligence Engine

- [x] Maintain one immutable universal profile across education, experience,
  skills, languages, family, finances, goals, constraints, consent, and evidence
- [x] Rank published pathways with risks, costs, evidence gaps, alternatives, and provenance
- [x] Generate dependency-controlled operational case timelines
- [x] Rank best-fit countries across the complete reviewed global catalogue
  - [x] Persist immutable, content-addressed country-ranking assessments against an exact profile and published pathway-version set
  - [x] Require explicit user acceptance and human review before generating a new country-ranking assessment
  - [x] Preserve the Phase 10B release gate by labelling incomplete scope as reviewed-published-catalogue-only
- [x] Explain country-level tradeoffs, long-term goals, PR/citizenship dependencies, and uncertainty
  - [x] Derive ranking scores deterministically from profile fit, confidence, and reviewed pathway risk
  - [x] Surface costs, processing ranges, evidence gaps, coverage posture, and route alternatives by country
  - [x] Read permanent-residence and citizenship dependencies only from human-published pathway metadata and never infer missing rules
  - [x] Add uncertainty scoring and explicit non-recommendation/non-guarantee labels
- [x] Reassess only when the user explicitly accepts a new profile or reviewed regulatory version

### 10E. Multi-Year Global Mobility Timeline

- [x] Generate operational profile-to-settlement milestones for one selected pathway
- [x] Model versioned transitions across study, graduate rights, work permits,
  skilled migration, settlement, permanent residence, and citizenship eligibility
- [x] Support dated multi-country scenarios such as Austria study (2026), graduate
  permit (2028), RWR Card (2029), RWR Plus (2031), permanent residence (2034),
  and citizenship-eligibility review (2035)
- [x] Recalculate downstream stages when verified rules change while preserving the original scenario
- [x] Never present future eligibility dates as guarantees; require reviewed rules and human confirmation


Delivered country-ranking governance: explicit user acceptance creates an immutable
assessment tied to the exact profile version, published pathway versions, and registry
release posture. Countries are grouped and ranked only from human-published pathway
evidence. Permanent-residence and citizenship dependencies are surfaced only when they
exist in reviewed pathway metadata; missing data becomes visible uncertainty, never an
inference. Until Phase 10B passes, every response is labelled
`reviewed_published_catalogue_only` and cannot claim complete global ranking coverage. See
`docs/REVIEWED_GLOBAL_COUNTRY_RANKING_V10_13.md`.

Delivered multi-year scenario governance: explicit user acceptance and human review create
an immutable scenario version from exact published pathway versions, verified rules, source
snapshots, operator-confirmed durations, and dated dependencies. Reviewed pathway-impact
replacements can create a new scenario version; the prior scenario and all of its dates and
evidence remain unchanged. Every stage states that future eligibility is not guaranteed and
must be re-verified before action. See `docs/MULTI_YEAR_MOBILITY_SCENARIOS_V10_14.md`.

Historical and predictive analytics remain gated until sufficient verified history exists.

## Phase 11: Business and Wealth Mobility — Not Started

- [ ] Corporate accounts, employees, dependants, sponsors, relocations, and compliance
- [ ] Entrepreneur and startup mobility
- [ ] Residency/citizenship by investment
- [ ] HNWI and family-office mobility
- [ ] Tax residency and treaty intelligence with specialist-review controls

## Phase 12: Channels, Ecosystem, and Automation — Not Started

- [ ] Dedicated client portal and mobile application
- [ ] Employer and partner portal with tenant isolation
- [ ] Versioned public/partner APIs
- [ ] Email, messaging, calendar, CRM, and case-event automation
- [ ] Government and mobility-agency workflows

## Phase 13: Global Scale Platform — Not Started

- [ ] Progressive coverage of all recognized countries and independent jurisdictions
- [ ] OpenSearch/Elasticsearch when validated search requirements exceed PostgreSQL
- [ ] Neo4j when validated graph traversal requires a dedicated graph store
- [ ] Durable event streaming and Temporal-class workflows when scale requires them
- [ ] OpenTelemetry, Prometheus, Grafana, Loki, tracing, SLOs, backups, and DR exercises
- [ ] Kubernetes and AWS/Azure/GCP/on-premise deployment profiles when operationally justified

## Delivery Rules

Every phase must include:

- Source provenance and Truth Engine integration for regulated claims
- Controlled agent permissions and human-review defaults
- Audit events for sensitive actions and state transitions
- Database migration and rollback paths
- Backend tests and frontend type/build validation
- Security, privacy, consent, retention, and operational notes
- Documentation updates and coverage-ledger status changes
