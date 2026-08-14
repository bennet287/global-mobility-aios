# Changelog

## 2026-08-14 - Phase 13.16.1D4 deferred-domain review and integrated emitter regression acceptance

- Closed 13.16.1D4 as **COMPLETE / PASS** after local acceptance of the deferred-domain governance review and integrated emitter regression: 17/17 authenticated organization-record API tests, 40/40 combined D1-D3C Contribution transaction/emitter tests, 49/49 deferred-domain regression tests, and 750 passed + 1 expected PostgreSQL-only skip with 0 failures in the complete API suite. The full API run exited 0.
- Confirmed the accepted emitter inventory remains intentionally narrow: terminal human-attributed `ExecutiveDecision`, reviewed `JurisdictionSourceCertification`, published `InitialRuleAssertion`/`VerifiedRule`, published `RegulatoryChange`/`VerifiedRule`, and published `MobilityPathwayVersion`. No additional deferred-domain runtime emitter was enabled.
- Confirmed the generic authenticated Contribution command remains ExecutiveDecision-only and cannot bypass sealed source-owned adapters by selecting source-certification, rule-publication, regulatory-change, pathway-publication, deferred-domain, assessment, external-validation component, or telemetry source types in the request body.
- Repository policy, release consistency, migration consistency, and `git diff --check` pass at Alembic head `0074_durable_contribution_activity_model` with 118 registered tables. Round 6 Austria v4 remains draft, simulation-only, unpublished/not-ready, with national/regional source certification still `pending_review` and no false legal Contribution emitted.
- 13.16.1E Observatory/read model is now **UNLOCKED / NOT STARTED**. Phase 13.16.1 remains **IN PROGRESS**; Phase 13.16.2 remains locked; genuine Phase 13.17 external-human acceptance is still required.

## 2026-08-14 - Phase 13.16.1D4 deferred-domain review and integrated emitter regression implementation

- Re-evaluated every domain source deliberately deferred in D0 after acceptance of the
  D2/D3 publication emitters. No additional runtime emitter is authorized in D4: the
  remaining candidates still lack one or more required provenance, source-transition
  audit, authenticated external/user attribution, typed evidence, independent review, or
  external-authority verification contracts. Sparse Contribution volume is intentional.
- Kept `JurisdictionImmigrationAssessment`, `ReassessmentAcceptance`,
  `ExternalValidationRun`, `CorporateComplianceEvent`, `MobilityTimelineMilestone`,
  `AgencySubmission`, and `AuthorityAppointment` deferred with explicit repository-backed
  reasons. In particular, external validation remains held behind genuine Phase 13.17
  external-human acceptance, and no current Round 6 Austria draft/pending state gains an
  emitter.
- Expanded the authenticated organization API negative-source regression so request-body
  source selection cannot invoke any sealed D2/D3 adapter, deferred domain source,
  assessment-generation record, external-validation component record, or telemetry source.
  The generic Contribution command remains terminal human-attributed ExecutiveDecision
  only; accepted real-domain emission remains source-owned and sealed.
- No runtime service/router/model/migration behavior changes are included. D4 is
  **COMPLETE / PASS** after the acceptance recorded above. 13.16.1E Observatory/read model
  is **UNLOCKED / NOT STARTED**; its source-table reconciliation remains a separate next
  slice.

## 2026-08-14 - Phase 13.16.1D3C pathway-version publication Contribution adapter acceptance

- Closed 13.16.1D3C as **COMPLETE / PASS** after local acceptance of the pathway-version
  publication Contribution adapter: 8/8 focused D3C emitter tests, 23/23 existing pathway
  catalogue/evidence-provenance/draft-simulation/reassessment regression tests, 94 passed +
  1 expected PostgreSQL-only skip in the combined D1-D3B/organization protection set, and
  750 passed + 1 expected PostgreSQL-only skip in the complete API suite.
- Confirmed authenticated pathway publication stages exactly one
  `pathway_version_published` Contribution with persisted replay idempotency, preserved
  admin/operator compatibility, fail-closed VerifiedRule/provenance drift handling,
  immutable-version supersession behavior, and atomic rollback of pathway/version/audit/
  Contribution state on emitter failure. Draft/internal-simulation and unpublished versions
  remain non-emitting, and the generic organization Contribution API remains
  ExecutiveDecision-only.
- Repository policy, release consistency, migration consistency, and `git diff --check`
  pass at Alembic head `0074_durable_contribution_activity_model` with 118 registered
  tables. The complete API suite exits 0 with zero failures.
- 13.16.1D4 deferred-domain review plus integrated emitter regression is now **UNLOCKED /
  NOT STARTED**. 13.16.1E Observatory remains not started, Phase 13.16.1 remains in
  progress, Phase 13.16.2 remains locked, and genuine Phase 13.17 external-human
  acceptance is still required.

## 2026-08-14 - Phase 13.16.1D3C pathway-version publication Contribution adapter implementation

- Added the bounded pathway-publication Contribution adapter at the existing authenticated
  `MobilityPathwayVersion` publish boundary. Only a draft version that passes the existing
  catalogue publication-evidence gate, is independently published by an authenticated
  human actor, becomes `published`, and activates its parent pathway may stage
  `pathway_version_published`; draft/internal-simulation, retired, and unpublished
  versions remain non-emitting.
- Preserved the pathway catalogue as transaction owner across supersession of any prior
  published version, the selected version's publication transition, pathway activation,
  the existing publication audit, one staged Contribution, and the Contribution audit.
  Emitter or final-commit failure rolls the whole unit back. A later immutable version
  receives a distinct deterministic Contribution instead of rewriting the earlier
  publication outcome.
- Kept the generic authenticated organization Contribution API ExecutiveDecision-only.
  The sealed D3C validator requires authenticated internal-human publication authority,
  proposer/publisher separation, active published source state, and reuses the catalogue's
  exact official-source/snapshot, verified-rule, certification, and structured-evidence
  publication blocker contract before creating the descriptor. Contribution wording
  records catalogue publication only and does not establish applicant eligibility,
  occupation eligibility, visa approval, or an authority decision for a mobility case.
- Preserved current admin/operator pathway publication compatibility and passed the
  authenticated role into the trusted adapter. Direct service calls without publisher-role
  context remain no-emitter, so no historical backfill is introduced. Added eight focused
  D3C tests for draft/no-emission, authenticated emission, operator compatibility,
  persisted replay, fail-closed rule drift, atomic rollback, revision supersession, and
  the still-closed generic source policy. D3C is **COMPLETE / PASS** after the acceptance
  recorded above; 13.16.1D4 deferred-domain review/integrated emitter regression is now
  **UNLOCKED / NOT STARTED**, and 13.16.1E Observatory remains not started.

## 2026-08-14 - Phase 13.16.1D3B regulatory-change publication Contribution adapter acceptance

- Closed 13.16.1D3B as **COMPLETE / PASS** after local acceptance of the second
  publication-class Contribution adapter: 8/8 focused regulatory-change emitter tests,
  9/9 existing regulatory-intelligence/knowledge-graph/pathway-impact regression tests,
  86 passed + 1 expected PostgreSQL-only skip in the combined D1-D3A/organization
  regression, and 742 passed + 1 expected PostgreSQL-only skip in the complete API suite.
- Confirmed authenticated publication stages exactly one
  `regulatory_change_publication_completed` Contribution with HTTP and persisted replay
  idempotency, fail-closed published-rule drift handling, authenticated publisher
  attribution, and atomic rollback of the source/rule/audit/Contribution unit on emitter
  failure. The generic organization Contribution API remains ExecutiveDecision-only and
  no historical backfill is introduced.
- Repository policy, release consistency, migration consistency, and `git diff --check`
  pass at Alembic head `0074_durable_contribution_activity_model` with 118 registered
  tables. The complete API suite exits 0 with zero failures.
- 13.16.1D3C pathway-version publication is now **UNLOCKED / NOT STARTED**.
  13.16.1E Observatory remains not started, Phase 13.16.1 remains in progress, Phase
  13.16.2 remains locked, and genuine Phase 13.17 external-human acceptance is still
  required.

## 2026-08-14 - Phase 13.16.1D3B regulatory-change publication Contribution adapter implementation

- Added the second publication-class Contribution adapter at the authenticated
  `RegulatoryChange` publish boundary. Only a previously reviewed approved change backed
  by its current hashed official-source snapshot can emit
  `regulatory_change_publication_completed` when it becomes published with an active
  resulting `VerifiedRule`; detection, classification, pending/rejected review, and
  approved-but-unpublished states remain non-emitting.
- Bound publication attribution to the authenticated HTTP publisher. The legacy request
  `reviewer` value must match that authenticated identity, and the same actor is recorded
  on the resulting VerifiedRule, graph projection, supersession when present, publication
  audit, and Contribution. Request-body actor spoofing therefore fails before mutation.
- Preserved one source-owned transaction across RegulatoryChange publication, VerifiedRule
  creation, optional prior-rule supersession/deactivation, regulatory knowledge-graph
  projection, existing source audits, the staged Contribution, and its audit. Emitter or
  final commit failure rolls back the whole unit; already-published records do not receive
  historical backfill.
- Kept the generic authenticated organization Contribution API ExecutiveDecision-only. A
  sealed D3B validator requires internal-human admin/reviewer authority, exact change/rule
  jurisdiction/source/snapshot/domain/publication provenance, prior review attribution, a
  hashed current snapshot, and authenticated publisher identity. The Contribution records
  regulatory-knowledge publication only and does not establish applicant eligibility,
  occupation eligibility, visa approval, or pathway publication.
- Added focused D3B coverage for pre-publication no-emission, authenticated atomic
  emission, HTTP and adapter replay, fail-closed rule drift, emitter rollback, publisher
  spoofing rejection, and the still-closed generic source policy. D3B is
  **COMPLETE / PASS** after the acceptance recorded above; D3C pathway publication is
  now **UNLOCKED / NOT STARTED**.

## 2026-08-14 - Phase 13.16.1D3A initial-rule publication Contribution adapter acceptance

- Closed 13.16.1D3A as **COMPLETE / PASS** after local acceptance of the first
  publication-class Contribution adapter: 8/8 focused initial-rule publication tests,
  4/4 coverage-reconciliation tests, 78 passed + 1 expected PostgreSQL-only skip in the
  combined D1/D2/organization service/API/platform regression, and 734 passed + 1
  expected PostgreSQL-only skip in the complete API suite.
- Confirmed authenticated independently reviewed `InitialRuleAssertion` publication
  stages exactly one `verified_rule_publication_completed` Contribution with HTTP and
  persisted replay idempotency, fail-closed published-source drift handling, and atomic
  rollback if Contribution staging fails. The generic organization Contribution API
  remains ExecutiveDecision-only and no historical backfill is introduced.
- Repository policy, release consistency, migration consistency, and `git diff --check`
  pass at Alembic head `0074_durable_contribution_activity_model` with 118 registered
  tables. The complete API suite exits 0 with zero failures.
- 13.16.1D3B regulatory-change publication is now **UNLOCKED / NOT STARTED**.
  13.16.1D3C pathway publication remains **LOCKED / NOT STARTED**, 13.16.1E Observatory
  remains not started, and Phase 13.16.1 remains in progress.

## 2026-08-14 - Phase 13.16.1D3A initial-rule publication Contribution adapter implementation

- Added the first publication-class Contribution adapter at the existing authenticated
  `InitialRuleAssertion` publish boundary. Only an independently reviewed assertion that
  passes the existing approved coverage/source-certification, immutable-snapshot,
  confidence, publication-attestation, and proposer/publisher-separation gates can stage
  `verified_rule_publication_completed` when it becomes an active `VerifiedRule`.
- Preserved one caller-owned transaction across the assertion `published` transition,
  VerifiedRule creation, regulatory-knowledge-graph projection, existing publication and
  coverage-reconciliation audits, one staged Contribution, and the Contribution audit.
  Contribution staging or final commit failure rolls the publication unit back rather
  than leaving a source/ledger dual-write gap.
- Kept the generic authenticated organization Contribution API ExecutiveDecision-only.
  The new sealed publication validator requires authenticated internal-human
  admin/reviewer context and exact assertion/rule jurisdiction, official-source,
  snapshot, semantic content, confidence, effective-period, publisher, and publication
  timestamp provenance. Contribution wording records knowledge publication only and does
  not establish applicant eligibility, occupation eligibility, visa approval, or pathway
  publication.
- Preserved the no-backfill boundary: already-published records and legacy direct service
  calls without trusted publisher-role context do not synthesize Contributions. Added
  focused coverage for authenticated publication emission, HTTP and persisted replay,
  fail-closed source drift, and atomic rollback on emitter failure. D3A remains
  **COMPLETE / PASS** after the acceptance recorded above. D3B regulatory-change
  publication is unlocked/not started; D3C pathway publication remains locked/not
  started.

## 2026-08-14 - Phase 13.16.1D2 source-certification Contribution adapter acceptance

- Closed 13.16.1D2 as **COMPLETE / PASS** after local acceptance of the first bounded
  real-domain Contribution emitter: 8/8 focused D2 emitter tests, 12/12 existing
  structured source-certification evidence-pack tests, 58 passed + 1 expected
  PostgreSQL-only skip in the D1/organization service/API/platform regression, and 730
  passed + 1 expected PostgreSQL-only skip in the complete API suite.
- Corrected the replay defect exposed during acceptance by normalizing reviewed
  timestamps to a database-stable UTC representation before canonical Contribution
  fingerprinting. Persist/reload replay now returns the existing Contribution without
  weakening fail-closed idempotency conflicts.
- Repository policy, release consistency, migration consistency, and `git diff --check`
  pass at Alembic head `0074_durable_contribution_activity_model` with 118 registered
  tables. Round 6 pending national/regional certifications remain non-emitting and no
  applicant-eligibility, occupation-eligibility, or pathway-publication conclusion is
  introduced.
- 13.16.1D3 publication adapters are **UNLOCKED / NOT STARTED**. 13.16.1E Observatory
  remains not started, and Phase 13.16.1 remains in progress.

## 2026-08-14 - Phase 13.16.1D2 source-certification Contribution adapter implementation

- Added the first real authoritative Contribution adapter at the existing authenticated
  `JurisdictionSourceCertification` review boundary. Only terminal approved/rejected
  reviews can stage `source_certification_review_completed`; pending/superseded state,
  raw source capture, and generated immigration assessments remain non-emitting.
- Preserved the source service as transaction owner: certification transition, the
  existing source-review `AuditLog`, one staged Contribution, and the Contribution audit
  commit or roll back together. Structured reviews retain the deterministic evidence-pack
  SHA-256, pinned immutable snapshot, independent-human attestation, and distinct
  proposer/reviewer requirements.
- Kept the generic authenticated organization Contribution API ExecutiveDecision-only. A
  separate sealed source-certification validator permits only authenticated admin/reviewer
  domain integration, uses deterministic source-version/key identity, and records safe
  organizational review semantics that explicitly do not establish applicant eligibility,
  occupation eligibility, or pathway publication.
- Added focused D2 tests for pending/no-emission, approved/rejected structured emission,
  attestation rejection, atomic rollback on emitter failure, unauthorized-role rollback,
  idempotent replay, and legacy direct-service no-emitter compatibility. D2 remains
  **IMPLEMENTED / LOCAL ACCEPTANCE PENDING** until the local regression gates pass; D3
  publication adapters and 13.16.1E Observatory remain not started.

## 2026-08-14 - Phase 13.16.1D1 transaction composability acceptance

- Closed 13.16.1D1 as **COMPLETE / PASS** after local verification of the caller-owned
  transaction contract: 8/8 focused D1 transaction tests, 50 passed + 1 expected
  PostgreSQL-only skip in the combined organization service/API/platform regression,
  and 722 passed + 1 expected PostgreSQL-only skip in the complete API suite.
- Repository policy, release consistency, migration consistency, and `git diff --check`
  pass at Alembic head `0074_durable_contribution_activity_model` with 118 registered
  tables. No migration, persistence-model, API, source-policy, emitter, or Austria
  regulated-state change was required for acceptance.
- 13.16.1D2 source-certification review emission is now **UNLOCKED / NOT STARTED**.
  Runtime Contribution emitters remain absent until the D2 adapter and its own atomic
  source/Contribution/audit acceptance pass.

## 2026-08-14 - Phase 13.16.1D1 transaction composability implementation

- Added an internal caller-owned mutation staging primitive that flushes domain changes
  and their `AuditLog` rows without committing, refreshing, or rolling back. The
  existing standalone `commit_mutations()` path retains commit/rollback ownership, so
  the authenticated organization API contract is unchanged.
- Added explicit internal `stage_contribution()` and
  `stage_contribution_correction()` integration paths while preserving the existing
  `create_contribution()` and `append_contribution_correction()` commit-on-command
  wrappers. No public `commit=False` bypass, source-policy expansion, real emitter,
  migration, persistence-model change, router change, or Observatory work was added.
- Added focused transaction-composability coverage for source/Contribution/audit
  rollback, Contribution-audit failure, caller final-commit failure, replay without
  duplicate audit, fail-closed semantic conflicts, correction rollback, and standalone
  wrapper regression. The subsequent acceptance entry records the passing local gates.

## 2026-08-14 - Phase 13.16.1D0 authoritative Contribution emitter mapping

- Completed a repository-backed, design-only mapping of real domain outcomes against
  the durable Contribution contract. Terminal `ExecutiveDecision` remains an eligible
  source but explicit-command-only; reviewed source-certification outcomes and governed
  publication transitions are the first eligible future adapter classes. Generated
  Eligibility, pathway comparison, country ranking, raw source/evidence retrieval,
  agent/workflow execution, attempts, tools/LLM calls, AuditLog, retries, messages, and
  UI interactions remain ineligible as direct Contribution authority.
- Classified `JurisdictionImmigrationAssessment`, `ReassessmentAcceptance`,
  `ExternalValidationRun`, corporate compliance, timeline milestones, and
  agency/appointment progress as deferred until their remaining audit, authenticated
  actor, evidence, or external-verification contracts are strong enough. Phase 13.17
  external-human acceptance remains unsatisfied and `external_human` is not promoted to
  durable HumanAction authority.
- Identified a transaction-composability hard gate before runtime emitters:
  `create_contribution()` commits through `commit_mutations()` while the source-domain
  services also own their commits. Direct post-commit emission would be a lossy
  best-effort dual write, while nested pre-commit use would unexpectedly transfer
  transaction ownership to the Contribution service. 13.16.1D1 must introduce a
  caller-owned staging path so the source transition, source audit, Contribution, and
  Contribution audit commit or roll back together. No new outbox is required for the
  initial same-database adapters.
- Pinned Round 6 Austria v4 to zero automatic Contributions: draft,
  `simulation_candidate`, `INTERNAL_SIMULATION_ONLY`, unpublished/not-ready, national
  and regional certification `pending_review`, absent/blocking job offer, occupation
  `AMBIGUOUS`, regional `INSUFFICIENT_INFORMATION`, qualification mapping `UNRESOLVED`,
  EUR 218, 14 evidence gaps, and human review required. No runtime code, migration, API,
  source policy, database state, or emitter changed in this design-only slice.

## 2026-08-14 - Phase 13.16.1C authenticated organization REST API

- Added the authenticated, tenant-scoped `/api/v1/organization` durable record API
  for Activity, Contribution, WorkItem, dependency, Blocker, HumanActionRequest,
  HumanAction, ExecutiveDecision, and heterogeneous RecordReference operations. The
  durable WorkItem and Decision collections use collision-free `/work-items/records`
  and `/decisions/records` paths because the legacy governance router retains the base
  collection contracts.
- Added bounded Pydantic command/read/page schemas, stable newest-first pagination,
  useful indexed filters, centralized safe service-error translation, non-disclosing
  tenant lookup behavior, and router registration with successful duplicate-free
  OpenAPI generation. Canonical fingerprints remain private; decisions expose only
  the safe source version required by the current Contribution validator.
- Derived `OrganizationCommandContext` exclusively from existing authenticated
  request state. The current trusted local context maps `admin` to Board/L4,
  `operator` to organization-operator/L2, and read roles conservatively; request
  bodies cannot choose actor, actor type, authenticated user, role, authority, or
  tenant. HumanAction remains restricted to authenticated internal humans, and
  Board-reserved decision and waiver checks remain enforced by the service layer.
- Added focused HTTP coverage for authentication/RBAC, identity spoofing, tenant
  isolation, idempotency, source rejection, append-only corrections/supersession,
  lifecycle conflicts, human-only action completion, pagination, OpenAPI, and the
  no-emitter/no-Observatory/no-migration boundaries. No domain emitter, workflow,
  read model, dashboard, UI, migration, persistence model, or service policy changed.
  Phase 13.16.1D real Contribution emitters and 13.16.1E Observatory/read model remain
  **NOT STARTED**; Phase 13.16.1 remains **IN PROGRESS**.

## 2026-08-14 - Phase 13.16.1B durable organization command/service layer

- Added HTTP-independent, tenant-scoped command services for ordered Activity,
  explicit authoritative Contribution, WorkItem lifecycle/dependencies, Blocker,
  HumanActionRequest/HumanAction, ExecutiveDecision, and heterogeneous record
  references, with canonical SHA-256 fingerprints and fail-closed replay conflicts.
- Added a deliberately narrow Contribution source policy: only an attributed terminal
  ExecutiveDecision is enabled. AgentRun, WorkflowRun, tool/LLM calls, AuditLog,
  retries, messages, and UI activity remain telemetry and cannot directly authorize a
  Contribution. No real domain emitter or execution integration was added.
- Added explicit lifecycle/authority matrices, exact authenticated-human enforcement
  (`external_human` is not accepted in this slice), bounded dependency-cycle checks,
  tenant-safe reference validation, PostgreSQL activity-stream row locking, and atomic
  mutation-plus-AuditLog rollback behavior.
- Added focused SQLite and isolated PostgreSQL service coverage. Phase 13.16.1 design,
  13.16.1A persistence, and 13.16.1B command/service layer are complete; REST APIs,
  real Contribution emitters, and the Observatory/read model are not started. Phase
  13.16.1 remains **IN PROGRESS**, and Phase 13.16.2 remains locked.

## 2026-08-13 - Phase 13.16.1A durable persistence foundation

- Added migration `0074_durable_contribution_activity_model` and registered portable
  SQLModel persistence for ordered Activity streams, append-only Activity,
  Contribution, HumanAction, and evidence references, plus durable dependency,
  Blocker, and HumanActionRequest lifecycle records.
- Reused and compatibility-safely extended `OrganizationalWorkItem` and
  `ExecutiveDecision`; added composite tenant fences, deterministic key/fingerprint
  constraints, controlled string-backed values, direct provenance relationships, and
  non-cascading authoritative-history foreign keys.
- Added focused persistence and fresh SQLite migration-cycle coverage. No API,
  service, workflow/agent emitter, Observatory read model, UI, semantic history
  backfill, or automatic AgentRun-to-Contribution behavior was added. Phase 13.16.1
  remains **IN PROGRESS**; its persistence foundation is complete.

## 2026-08-13 - Phase 13.16.1 durable model design complete

- Completed the repository-backed design for durable Activity, Contribution,
  WorkItem, Decision, Blocker, and HumanAction contracts, including authoritative
  source boundaries, lifecycle, attribution, evidence, idempotency, ordering,
  tenant isolation, retention, observatory aggregation, migration, backfill, API,
  and test requirements.
- Reuses `OrganizationalWorkItem` and `ExecutiveDecision`; preserves AgentRun,
  execution attempts, organizational outputs, AuditLog, automation, validation, and
  domain records in their existing authoritative roles. Agent success is Activity
  only and can never automatically become a Contribution.
- Phase 13.16.1 is **DESIGN COMPLETE / IMPLEMENTATION NOT STARTED**. This entry adds
  documentation only: no runtime code, model, migration, API, worker, or UI behavior
  changed. Phase 13.17 external-human acceptance remains required and Phase 14 stays
  locked.

## 2026-08-13 - Phase 13.16.0 closed / pass

- Closed Phase 13.16.0 with implementation **COMPLETE**, independent internal
  rendered acceptance **PASS**, and overall state **CLOSED**. Phase 13.16.1 Durable
  Contribution & Activity Model is **UNLOCKED / NOT STARTED**; Phase 13.17 genuine
  external-human acceptance remains required and Phase 14 remains locked.
- Accepted the Geist Sans and Geist Mono typography contract; shared typography,
  spacing, surface, semantic-state, layout, shell, card, form, badge, table, empty,
  loading, notice, and technical-provenance foundations; and the shared hierarchy
  **decision/context → blockers → next actions → supporting evidence → technical
  provenance** across Mobility User, Professional/Operator, and Owner/Board
  presentation foundations.
- Recorded `RV-01` through `RV-08` as **RESOLVED / PASS**: Eligibility hierarchy and
  plain-language state, Board Room acronyms, Agent Console Leads, Validation checkbox,
  Planning mobile summary/control, Agent Console mobile history/shell isolation, and
  the duplicate `/icon.svg` conflict. The canonical App Router icon returns HTTP 200.
- Recorded the final Planning country-ranking lookup defect as **RESOLVED / PASS**.
  Planning had redundantly requested ranking history and the latest-record endpoint;
  for a valid lead with zero rankings, the backend correctly returned 404 while the
  handled request still produced a repeatable console error. Planning now derives the
  optional latest ranking from `history[0]`, or `null` when history is empty, without
  changing backend latest-record semantics.
- Independent internal rendered verification passed the desktop surfaces; Eligibility,
  Planning, and Agent Console at 390px; Eligibility and Planning dark themes; Board
  acronyms; Validation control; Agent Console Leads and Recent agent runs; technical
  provenance focus, Enter/Space activation, and identifier wrapping; narrow-surface
  overflow checks; normal Agent Console console state; and the final Planning console
  re-check.
- Preserved Round 6 **PASS** and every safety boundary: Austria v4 remains draft,
  unpublished, `simulation_candidate`, `INTERNAL_SIMULATION_ONLY`, production
  recommendation false, simulation-only true, and publication-ready false. National
  and regional occupation certifications remain `pending_review`; EUR 218, 14 evidence
  gaps, the absent/blocking binding job offer, ambiguous occupation assessment,
  insufficient regional information with unknown province, unresolved qualification
  mapping, and required human review remain unchanged.
- This closure records internal rendered acceptance only. It does not claim genuine
  external-human validation or satisfy Phase 13.17.

## 2026-08-13 - Phase 13.16.0 final Planning request correction

- Classified the final Planning console 404 as a bounded client defect: the page
  redundantly requested both the latest country ranking and the descending ranking
  history when the Round 6 case legitimately had no ranking assessment.
- Planning now derives the optional latest ranking from the already-requested history,
  preserving empty-state behavior while avoiding the unnecessary expected-absence 404.
- Added a deterministic source-contract check. Rendered acceptance remains pending
  final confirmation; Phase 13.16.0 is not closed.

## 2026-08-13 - Phase 13.16.0 final bounded rendered remediation

- Remediated `13.16.0-RV-06` by giving the Planning profile, plan status, and consent
  full-width mobile rows; retaining two-column compact metrics; restoring normal name
  wrapping; and giving the internal/draft simulation checkbox a stable control column.
- Remediated `13.16.0-RV-07` by fully hiding the closed off-canvas rail, removing the
  mobile header's overlapping sticky layer, constraining Agent Console history rows to
  the viewport, and reserving mobile workspace space for the floating chat control.
- Remediated `13.16.0-RV-08` by removing the duplicate identical `public/icon.svg`;
  the supported App Router `app/icon.svg` remains the branded first-party icon.
- Extended the dependency-free foundation checks for Planning mobile structure,
  mobile shell/history isolation, and App Router icon uniqueness. Final rendered
  acceptance remains pending one independent spot check.

## 2026-08-13 - Phase 13.16.0 desktop rendered-findings remediation

- Recorded the successful clean-runtime desktop render and remediated findings
  `13.16.0-RV-01` through `13.16.0-RV-05` without changing regulated behavior.
- Moved Eligibility next actions directly after the primary blocker, moved the full
  additional-gap inventory into supporting evidence, translated raw gap states into
  plain mobility-user language, and retained raw values in Technical provenance.
  National and regional pending-certification warnings remain visible in the primary
  reading flow.
- Restored conventional Board executive acronyms, introduced stable responsive
  checkbox/avatar/content/status columns for Agent Console leads, and corrected the
  Validation simulation checkbox selector and label/helper layout.
- Added lightweight source-contract checks for ordering, plain-language state
  presentation, executive acronyms, lead-row structure, and checkbox association.
- Final rendered acceptance remains pending: the corrected desktop findings,
  mobile/narrow layout, dark theme, keyboard focus/disclosure, identifier wrapping,
  and persistent material warnings still require independent verification.

## 2026-08-13 - Phase 13.16.0 design-system and information-architecture implementation

- Implemented the Phase 13.16.0 presentation foundation with Geist Sans as the
  product font and Geist Mono restricted to technical identifiers and code-like
  provenance. No raw font binaries or component framework were added.
- Added shared typography, spacing, container, grid, shape, elevation, focus, and
  semantic state tokens across the existing light and dark themes.
- Normalized the existing workspace shell, top bar, panels, buttons, badges,
  notices, empty states, loading skeletons, form controls, and responsive table
  behavior. Added a skip link, main landmark, accessible mobile-menu state,
  Escape-to-close behavior, live status semantics, and reduced-motion support.
- Added a reusable native `details`/`summary` technical-provenance disclosure with
  copyable, wrapping Geist Mono identifiers. Material lifecycle, publication, and
  pending-certification warnings remain visible outside the disclosure.
- Reframed Eligibility around decision context, blockers, next actions, supporting
  evidence, and technical provenance. The unchanged 35% and 60% values are labelled
  as internal assessment signals and explicitly not approval probabilities.
- Reframed Planning so production catalogue and internal simulation contexts are
  visually distinct, an active simulation has a persistent accessible warning,
  blockers/actions precede evidence inventories, and excluded routes are separated
  from potential alternatives without changing their scores or exclusion logic.
- Applied the shared foundation to Mobility Profiles, Eligibility, Planning,
  Validation, Board Room, and Agent Console. Defined—but did not implement—the later
  Mobility User, Professional/Operator, and Owner/Board application architectures in
  [DESIGN_SYSTEM_INFORMATION_ARCHITECTURE_V13_16_0.md](DESIGN_SYSTEM_INFORMATION_ARCHITECTURE_V13_16_0.md).
- Added four dependency-free design-foundation contract tests. The existing four
  authenticated Eligibility request-client tests remain green, TypeScript validation
  passes, and the 37-route Next.js production build passes.
- Preserved authentication, CORS, API contracts, calculations, matching, evidence
  gaps, fees, sources, snapshots, audit behavior, certification decisions, pathway
  lifecycle, simulation authorization, and publication state. No backend, database,
  or migration change was made.
- Round 6 findings `R6-MU-01` through `R6-MU-04` and `R6-PRO-002` are addressed in
  code with rendered verification pending. `R6-PRO-001` remains open until the
  focused professional/operator rendered review occurs.
- The first manual rendered attempt exposed mixed generated output after a
  long-running Next.js development server shared `.next` with a production build:
  Planning and Profiles returned server errors, while Eligibility referenced missing
  CSS/core chunks. Clearing only `.next` and restarting the development server
  restored all three routes and their referenced assets to HTTP 200. No application
  source correction was required; rendered re-test remains required.
- Phase 13.16.0 is **IMPLEMENTED / RENDERED ACCEPTANCE PENDING** and is not closed.
  Phase 13.16.1 has not started; Phase 13.17 remains required and Phase 14 remains
  locked.

## 2026-08-13 - Phase 13.15 Round 6 correctness disposition

- Recorded **ROUND 6 CORRECTNESS DISPOSITION: PASS** for fresh synthetic case
  `AT-1D68AB41` on branch `roadmap/global-mobility-aios-v11` at baseline
  `dc22e7b2db4343bfaad702ebf53a2f9e5946e968`.
- Completed separate internal mobility-user and professional shadow reviews for the
  comparable India-to-Austria skilled-employment persona. These sessions are not
  genuine external-human acceptance and do not satisfy Phase 13.17.
- The mobility-user result is **PASS WITH MEDIUM/LOW EXPERIENCE FINDINGS**. The
  professional result is **PASS WITH MEDIUM/LOW FINDINGS**, with all 21 professional
  matrix checks passing.
- Confirmed zero Critical findings, zero High findings, and zero unsupported legal
  certainty. Candidate-family isolation, national/regional occupation
  conditionality, material blockers and costs, lifecycle/certification state,
  production/draft separation, and material traceability all pass the gate.
- Preserved the material decision state: Austria pathway v4 is `draft` and
  `simulation_candidate`, `INTERNAL_SIMULATION_ONLY`, production `false`, simulation
  `true`, and publication readiness `false`; the EUR 218 fee is retained and total
  cost remains `not_established`.
- Preserved `AMBIGUOUS` overall/national occupation results,
  `INSUFFICIENT_INFORMATION` regional status with province unset, `UNRESOLVED`
  qualification recognition, the `ABSENT` binding job offer, 14 canonical evidence
  gaps, four next actions, and the explicit non-eligibility boundary.
- Confirmed that excluded self-employment contributes no projected cost, obsolete
  optional-job-offer wording is absent, and the incorrect EUR 21,800 display is
  absent.
- Preserved the certification boundary: the distinct core pathway certification
  remains `approved`. The 2026 national and regional occupation certifications
  remained `pending_review` and were not approved or modified during Round 6.
- Carried `R6-MU-01` and `R6-MU-02` (Medium), `R6-MU-03` and `R6-MU-04` (Low), and
  `R6-PRO-001` and `R6-PRO-002` (Low) forward as formal Phase 13.16 experience and
  operational-evidence inputs.
- Added the complete pinned case, profile, comparison, pathway, rule, source,
  snapshot, hash, certification, gate, and finding record in
  [ROUND_6_CORRECTNESS_DISPOSITION_V13_15.md](ROUND_6_CORRECTNESS_DISPOSITION_V13_15.md).
- Marked Phase 13.15 Round 6 complete and Phase 13.16.0 **UNLOCKED / NOT STARTED**.
  Phase 13 remains open, Phase 13.17 genuine external-human acceptance remains
  mandatory, and Phase 14 remains locked.
- This was a documentation-only disposition. It did not modify runtime code, database
  state, the external-validation ledger, assessments, certifications, or publication
  state, and it did not start Phase 13.16 implementation.

## 2026-08-13 - Phase 13.10.2.15 eligibility preview consistency

- Corrected the eligibility candidate-contribution boundary so excluded or
  incompatible pathway families contribute no preview documents, material
  requirements, or costs. Their audit-visible candidate records remain intact.
- Removed the generic optional job-offer document wording. For the compatible
  Austria shortage-worker simulation candidate, a binding Austrian job offer is
  now exposed separately as a required, currently missing, blocking material fact;
  the employer declaration remains a distinct document requirement.
- Added a structured eligibility-preview contribution and version marker to the
  already-persisted assessment factors. No new table or column was required.
- Reconciled Planning risk prose with linked pathway evidence. When national and
  regional 2026 occupation roles are present and pending review, the comparison
  states that evidence is linked but pending independent certification instead of
  claiming it is absent. Pending status remains a publication blocker.
- Added focused regressions for excluded-family isolation, blocking job-offer
  semantics, linked/pending evidence wording, and the complete Phase 13.10.2.14
  monetary, occupation, gap-count, lifecycle, certification, and trace invariants.
- Verification passes with **11 focused eligibility/integrity tests**, **27 adjacent
  eligibility/catalogue/profile tests**, **661 API tests**, and **4 fresh-migration
  tests**, plus Python compilation, TypeScript checking, the 37-route Next.js
  production build, repository policy, release consistency, migration integrity,
  Docker-profile validation, and `git diff --check`.
- No migration was added; Alembic remains at `0073_austria_candidate_integrity`.
  The preserved developer SQLite drift was not modified. Rendered validation must
  be manually repeated before this phase closes or Round 6 begins.
- Refreshed the latest live Eligibility and Planning assessments for existing case
  `AT-7811EDF4` without deleting prior history. API-level live checks confirm no
  excluded-route documents/costs/requirements, a missing blocking job-offer fact,
  linked-and-pending occupation wording, and all 13.10.2.14 invariants. The two-page
  manual rendered retest remains deliberately unclaimed and pending.
- Recorded rendered-smoke finding `13.10.2.15-F01`: both Eligibility GET-latest and
  POST-evaluate requests returned 401 before business content loaded because the
  local production bundle had no embedded header-role flag. Eligibility business-
  content remediation was therefore not assessed and the rendered gate failed.
- Hardened the one centralized frontend request helper used by Eligibility,
  Profiles, and Planning. Explicit `NEXT_PUBLIC_AUTH_ALLOW_HEADER_ROLE=true/false`
  remains authoritative; when unset, loopback API URLs receive the same local-only
  header behavior as development. Non-loopback production stays fail-closed, and
  configured role/user values plus credentials/CORS behavior are preserved. The
  duplicate document-download auth implementation was removed.
- Rebuilt the production frontend without embedding the auth flag and verified the
  compiled bundle contains one centralized header implementation used by both
  Eligibility requests. Manual rendered retest remains required; this does not
  close the gate.
- The subsequent manual retest proved that first F01 remediation insufficient:
  both Eligibility requests still returned 401 and the final browser request still
  lacked both authentication headers. Bundle-string presence is no longer accepted
  as runtime evidence.
- Replaced inline header-object construction with one canonical fetch module that
  builds a native `Headers` instance, merges request-specific headers, applies or
  removes local header-role authentication deterministically, and enforces included
  credentials/no-store behavior immediately before native `fetch()`.
- Added a four-test runtime request regression. It imports the actual exported
  Eligibility GET/POST functions with mocked native `fetch` and verifies their final
  URLs, methods, credentials, role/user headers, explicit-false behavior,
  non-loopback production fail-closed behavior, and request-header preservation.
- The second F01 remediation also failed rendered verification after a clean Next.js
  restart, deleted `.next` output, and a fresh browser tab. GET latest and POST
  evaluate both remained 401, and DevTools still showed neither `x-gmai-role` nor
  `x-gmai-user`. This rules out stale chunks/process state and leaves F01 open.
- Moved all browser-visible public-auth resolution into a Next.js-compiled TypeScript
  configuration module with direct static `process.env.NEXT_PUBLIC_*` references.
  The deterministic request builder now receives resolved values and performs no
  environment discovery; explicit false, loopback-local enablement, non-loopback
  production fail-closed behavior, credentials, no-store, and request headers remain
  covered.
- Added a compiled-client regression that builds the real Eligibility browser path
  under the local test configuration and asserts that its API base, enabled flag,
  role, and user resolve to `127.0.0.1:8002`, `true`, `admin`, and
  `frontend-operator`. This complements, rather than replaces, the final-fetch tests.
  Manual rendered verification is still required and the rendered gate is not passed.
- Browser-runtime instrumentation subsequently proved F01's client configuration,
  header builder, and final fetch arguments are resolved: both role/user headers are
  present immediately before native fetch. The temporary loopback-development-only,
  redacted diagnostic remains in place until rendered Eligibility passes.
- Recorded `13.10.2.15-F03`: Chrome masked the Eligibility response behind a missing
  CORS header. Direct reproduction showed both local authenticated preflights already
  returned 200 with the expected origin, headers, methods, and credentials; the exact
  server defect was middleware ordering. Authentication wrapped CORS, so any 401/403
  produced at the auth boundary escaped without CORS response headers.
- Made CORS the outer response boundary, retained unauthenticated preflight handling,
  and replaced the wildcard request-header policy with an explicit browser header
  allowlist including content type and the two local GMAI headers. Approved origins
  remain configuration-bound, unapproved origins remain denied, actual requests still
  require valid auth, and production header-role authentication remains fail-closed.
- Added focused GET/POST preflight, authenticated route reachability, unauthorized
  actual-request, and unapproved-origin regressions. The rendered gate remains blocked
  pending an API restart and manual Eligibility retest; business content is unassessed.
- The final manual rendered gate passed. Eligibility loads; the binding Austrian job
  offer is required, missing, and blocking; the employer declaration remains a separate
  required document; and no self-employment-only business plan, capital-transfer/job-
  creation evidence, company agreements, or trade authorisations contaminate the
  skilled-employment preview. The obsolete `job offer if available` wording is absent.
- Planning now states that linked 2026 national/regional occupation evidence remains
  pending independent certification. Both evidence roles remain linked and
  `pending_review`; no certification was approved and Austria v4 remains unpublished.
- Closed Phase 13.10.2.15 with rendered status **PASS** and resolved `R5A-002`,
  `13.10.2.15-F01`, and `13.10.2.15-F03`. Removed the temporary development browser
  diagnostic, `window.__GMAI_REQUEST_DEBUG`, its diagnostic-only regression, and its
  revision marker while retaining the centralized request/auth and CORS corrections.
  Round 6 and Phase 13.16 were not started by this closure.

## 2026-08-13 - Phase 13.10.2.14 assessment consistency and conditionality hardening

- Made monetary normalization unit-explicit and currency-generic. Plain catalogue
  values remain major units, explicitly typed minor units convert exactly once, and
  the active source-pinned application-fee rule overrides stale fee aliases without
  inheriting costs from an excluded route.
- Preserved regional occupation conditionality: governed regional candidates with
  no province now return `INSUFFICIENT_INFORMATION`; an applicable province can
  remain `AMBIGUOUS`; a supplied non-applicable province or a true absence of
  governed entries returns `NO_MATCH`.
- Added conclusion-level evidence traces to Mobility Planning with full pathway,
  rule, source, snapshot, certification, evidence-pack, and official-link provenance.
  Certification review links now open the exact certification and source snapshot;
  pending certifications remain pending and no approval or publication is implied.
- Prevented required documents from excluded self-employment routes from leaking
  into skilled-employment eligibility previews.
- Pinned structured Lead/intake facts to an immutable Mobility Profile v1 before a
  comparison is generated, and made the canonical 14 categorized evidence gaps the
  single count used by the response and rendered assessment.
- Added regressions for generic governed-fee parsing, explicit major/minor money
  units, regional province states, real German occupation aliases, exact gap counts,
  trace provenance, profile versioning, and excluded-route document/cost isolation.
- Verification passes with **654 API tests**, the **6-test focused integrity suite**,
  the **4-test fresh-migration gate**, Python compilation, TypeScript checking, the
  37-route Next.js production build, repository policy, release consistency,
  migration integrity, Docker-profile validation, and `git diff --check`.
- The developer SQLite file remains deliberately untouched after the local schema
  check reported its pre-existing 0072/0073 drift.
- Live integration against existing case `AT-7811EDF4` passes: v4 remains draft,
  Profile v1 is pinned, 14 canonical gaps are retained, EUR 218 is rendered once,
  regional scope remains conditional with one governed candidate, all 16 material
  traces carry full provenance, both occupation certifications remain
  `pending_review`, and the excluded route carries no payable cost.
- Both production frontend routes return HTTP 200, but the focused rendered smoke
  remains pending because this session exposed no in-app browser surface. Round 6
  and Phase 13.16 therefore remain gated.

## 2026-08-13 - Phase 13.10.2.13 Austria candidate integrity and occupation resolution

- Added migration `0073_austria_candidate_integrity` and durable Lead columns for
  the structured Austria facts consumed downstream; existing intake sessions are
  backfilled without reconstructing facts from Lead notes.
- Made structured Lead/IntakeSession facts authoritative inputs to eligibility and
  pathway comparison, with nonblank profile facts able to refine rather than erase
  the intake state.
- Added explicit compatibility and recommendation statuses. A skilled-employment
  case now retains Austria Self-employed Key Worker as `EXCLUDED` with the goal-
  mismatch reason and cannot rank it from country match alone.
- Added a governed occupation-resolution result that preserves exact, normalized,
  inferred, ambiguous, no-match, and insufficient-information qualities separately
  across national and regional 2026 evidence, including province, entry, snapshot,
  source-certification, and qualification-mapping state. It explicitly does not
  establish pathway eligibility.
- Replaced zero/flat gap presentation for the Austria skilled-worker route with
  categorized fact, evidence, document, regulatory, and certification gaps. The
  binding job offer is a blocking fact; a claimed language level remains separate
  from documentary proof.
- Scoped the governed EUR 218 value to a source-linked government application fee;
  estimated total cost and processing time remain not established when governed
  evidence does not establish them.
- Repaired the rendered local internal-simulation mismatch without weakening
  production safeguards. Simulation requires a permitted authenticated role, an
  explicit request and audit context, and records the Lead, draft pathway versions,
  actor, role, timestamp, reason, and simulation flag.
- Advanced the existing immutable structured-evidence integration contract to
  `v13_10_2_13`; the successor Austria draft pins core plus national/regional 2026
  evidence and says those occupation sources are linked but pending independent
  certification. It remains draft, publication-unready, and excluded from ordinary
  production matching.
- Updated Mobility Planning to render exclusion reasons, safe draft/non-reliance
  labels, occupation ambiguity, categorized gaps, case-driven next actions, source-
  linked application-fee semantics, and unestablished total cost/timing.
- Added decision-integrity and legal-certainty regressions. Verification passes with
  **650 API tests**, **4 fresh-migration tests**, Python compilation, the 37-route
  Next.js production build, and `git diff --check`.
- Created a recoverable 3,691,504-byte pre-migration PostgreSQL backup (SHA-256
  `CE4207B7DD89B1E4E3B305F00C4042A39EBF53C5A26EA9F2BA6DBD149989D23C`), migrated
  the live database to `0073_austria_candidate_integrity`, and idempotently created
  immutable Austria v4 `4f02f390-1e22-4ac3-9237-8a67f6551807`.
- Live authenticated simulation confirms v4 as an internal-only candidate, two
  governed national Software Engineer candidates and an `AMBIGUOUS` result, a
  separate regional `NO_MATCH`, an absent binding job offer, 14 gaps spanning all
  five categories, source-scoped EUR 218 application fee, unestablished total cost
  and timing, explicit self-employment exclusion, and a complete durable audit.
- Live ordinary matching returns no draft versions. Core-route evidence remains
  approved; national and regional occupation-source certifications remain
  `pending_review`; v4 remains unpublished and publication-unready.
- Phase 13.16 remains paused pending a fresh case-specific Round 5. No source
  certification was approved and no pathway version was published.

## 2026-08-13 - Phase 13.10.2.12 intake persistence and case continuity

- Normalized blank optional email and phone values on both the public-intake
  frontend boundary and the backend pre-validation boundary while preserving
  strict `EmailStr` validation for malformed non-blank addresses.
- Made public intake return `201 Created` with an explicit durable `lead_id` and
  human-readable case reference after atomically committing one `Lead` and one
  linked `IntakeSession`.
- Added persisted submission keys and request fingerprints with a unique database
  guarantee so retries reuse the original Lead and changed-payload key reuse fails
  closed instead of creating duplicates.
- Added migration `0072_intake_submission_idempotency` for the intake-session
  idempotency columns and unique submission-key index.
- Added readable persistence/validation errors so failed writes cannot render a
  false case-created state or expose raw FastAPI validation JSON in the UI.
- Added post-intake case continuity through Eligibility, Mobility Profiles,
  Mobility Planning, and External Validation using `?lead_id=`, including automatic
  Lead selection and a named External Validation Lead selector. Manual UUID entry
  remains available only as an advanced operational fallback.
- Preserved the explicit internal/draft simulation boundary; production pathway
  matching remains published-pathway-only unless the internal simulation control
  is deliberately enabled. No source certification or pathway publication was
  performed.
- Added regressions for omitted/blank/whitespace/valid/malformed email, atomic
  Lead and IntakeSession persistence, Austria fact preservation, `/api/v1/leads`
  visibility, idempotent replay, key-conflict rejection, and failed-write handling.
- Verification passed with **648 API tests, 0 failed**, **13 focused tests**, the
  **4-test fresh-migration gate**, TypeScript checking, the 37-route Next.js
  production build, and `git diff --check`.
- Backed up the live PostgreSQL database before migration and upgraded it
  transactionally from `0071_structured_shortage_occupation_evidence` to
  `0072_intake_submission_idempotency`; direct PostgreSQL verification confirms
  `0072_intake_submission_idempotency` is live.
- The post-migration API and frontend are healthy on ports 8002 and 3000. After a
  full host restart recovered the browser harness, the authorized rendered smoke
  created exactly one synthetic Austria Lead and one linked IntakeSession. The
  same named case reached Eligibility and auto-selected in Profiles, Planning,
  and External Validation without requiring raw UUID entry. This was release
  verification only; no validation round was started.

## 2026-08-12 - Phase 13.10.2.10 Austria intake and shadow-validation unblocking

- Fixed the first simulated pre-validation blocker: Austria is now a first-class
  target-country option in the public-intake form.
- Added Austria jurisdiction normalization on intake submission; selecting Austria
  creates or reuses the `AT` jurisdiction record.
- Added skilled-employment case-fact capture to public intake: current country,
  job-offer status, qualification-recognition state, and German language level.
- Stored the new structured case facts in both the lead notes and intake-session
  answers so the mobility profile and lead agree on Austria and the captured facts.
- Provided an Austria-specific success message and checklist while keeping the
  Austria pathway version in `draft`; no pathway was published and no 2026 source
  certification was approved.
- Added `scripts/record_simulated_prevalidation_findings.py` to durably record
  simulated/internal pre-validation findings in the external-validation ledger as
  internal-only baselines, without creating external human reviews.
- Recorded the first simulated pre-validation findings for the Austria
  skilled-employment scenario: one critical, two high, and three medium findings
  covering intake country coverage, missing case facts, source provenance,
  pathway-version transparency, and occupation evidence visibility.
- Added regression tests in `apps/api/tests/test_public_intake.py` proving Austria
  intake normalizes to jurisdiction `AT` and persists the new case facts.
- No schema migration was introduced; Alembic remains at
  `0071_structured_shortage_occupation_evidence`.
- Complete verification passed with **628 API tests, 0 failed**, with only the
  existing Starlette TestClient/httpx deprecation warning. Web production build
  passed with 37 routes.

## 2026-08-12 - Phase 13.15 external-validation operational run initiated

- Verified the Phase 13.5.2 external-validation framework end-to-end:
  `apps/api/tests/test_external_validation.py` passes with **8 passed, 0 failed**.
- Confirmed the External Validation router is registered through the declarative
  `RouterSpec` registry and the `/validation` workspace is part of the web build.
- Created `docs/EXTERNAL_VALIDATION_RUNBOOK_V13_15.md`, the operational guide for
  executing the first real external validation run with one mobility user and one
  independent professional/operator using the `at-skilled-worker-discovery-v1`
  Austria scenario.
- Updated `docs/ROADMAP.md` to mark Phase 13.15 as in progress and reference the
  runbook, the scenario fixture, and the validation workspace.
- The deterministic gate remains `held` until real human reviews, required evidence
  references, and issue triage are recorded; Critical/High findings must be
  resolved before the gate can evaluate to `passed`.
- No schema migration was introduced; Alembic remains at
  `0071_structured_shortage_occupation_evidence`.

## 2026-08-11 - Phase 13.14 Legal/CLO bounded department runtime

- Enabled the Legal department runtime for bounded `internal.analysis` only.
- Added `General Counsel` and `Public Policy / Compliance Lead` L2 specialist
  positions under the CLO, with role cards, controlled-agent handlers, registry
  entries, output schemas, and hardened position contracts.
- Added Legal evidence fields: audit findings, compliance framework, contract
  portfolio, corporate governance, ethics and integrity controls, government
  relations context, jurisdiction scope, legal exposure, litigation and disputes,
  policy landscape, regulatory interpretation, regulatory change register, risks,
  sources, and training records.
- Blocked Legal specialists from final legal opinions, settlement commitments,
  compliance certification, privileged disclosure, authority submissions, contract
  signatures, secrets access, infrastructure mutation, spend above threshold,
  vendor commitments, pricing changes, irreversible production changes, position
  suspension, and any external action.
- Added `delegate_legal_work` and integrated Legal into the department execution
  adapter so the CLO delegates to both specialists and the CEO receives an
  evidence-backed L3 decision receipt on completion.
- Added Legal work-item routing so Legal work is assigned to the CLO and runs
  through the same bounded execution path as other hardened departments.
- Added focused regressions for Legal internal analysis, incomplete evidence
  hold, suspended specialist resume, CEO handoff, CLO contract assertions,
  prohibited-action enforcement, specialist isolation, and CLO-only assignment.
- Updated the foundation bootstrap position count to 34 and verified the
  CLO/Legal reporting line.
- Updated `test_still_unimplemented_department_runtime_is_held_without_false_completion`
  to use the delivered `Legal` department with an unsupported external action
  (`contract.sign`), since all executive departments are now implemented.
- Kept Alembic at `0071_structured_shortage_occupation_evidence`; no schema
  migration was introduced.
- Complete verification passed with **627 API tests, 0 failed**, with only the
  existing Starlette TestClient/httpx deprecation warning. Web production build
  passed with 37 routes. All executive department runtimes are now delivered.

## 2026-08-11 - Phase 13.13 People/CHRO bounded department runtime

- Enabled the People department runtime for bounded `internal.analysis` only.
- Added `HR Lead` and `Culture / Recruitment Lead` L2 specialist positions
  under the CHRO, with role cards, controlled-agent handlers, registry entries,
  output schemas, and hardened position contracts.
- Added People evidence fields: brand guidelines, compliance requirements,
  culture metrics, diversity and inclusion plan, employee feedback, employer
  value proposition, headcount forecast, onboarding plan, organizational design,
  performance data, recruitment plan, retention data, risks, sources, talent
  pipeline, training plan, and workforce plan.
- Blocked People specialists from hiring decisions, compensation changes,
  terminations, policy publication, employment offers, external candidate or
  employee contact, and any external action.
- Added `delegate_people_work` and integrated People into the department
  execution adapter so the CHRO delegates to both specialists and the CEO
  receives an evidence-backed L3 decision receipt on completion.
- Added People work-item routing so People work is assigned to the CHRO and
  runs through the same bounded execution path as other hardened departments.
- Added focused regressions for People internal analysis, incomplete evidence
  hold, suspended specialist resume, CEO handoff, CHRO contract assertions,
  prohibited-action enforcement, specialist isolation, and CHRO-only assignment.
- Updated the foundation bootstrap position count to 32 and verified the
  CHRO/People reporting line.
- Updated `test_still_unimplemented_department_runtime_is_held_without_false_completion`
  to use the still-held `Legal` department, since People is now implemented.
- Kept Alembic at `0071_structured_shortage_occupation_evidence`; no schema
  migration was introduced.
- Complete verification passed with **613 API tests, 0 failed**, with only the
  existing Starlette TestClient/httpx deprecation warning. Web production build
  passed with 37 routes. Legal remains held.

## 2026-08-11 - Phase 13.12 Communications/CCO bounded department runtime

- Enabled the Communications department runtime for bounded `internal.analysis` only.
- Added `PR / Communications Lead` and `Government Relations Lead` L2 specialist
  positions under the CCO, with role cards, controlled-agent handlers, registry
  entries, output schemas, and hardened position contracts.
- Added Communications evidence fields: brand guidelines, channel strategy,
  crisis scenarios, engagement plan, government stakeholder map, jurisdiction
  scope, legislative timeline, media plan, messaging, policy landscape,
  regulatory agenda, risks, sources, and stakeholder map.
- Blocked Communications specialists from external messaging, public statements,
  press releases, policy publication, spend commitments, contracts, and any external
  action.
- Added `delegate_communications_work` and integrated Communications into the
  department execution adapter so the CCO delegates to both specialists and the
  CEO receives an evidence-backed L3 decision receipt on completion.
- Added Communications work-item routing so Communications work is assigned to the
  CCO and runs through the same bounded execution path as other hardened departments.
- Added focused regressions for Communications internal analysis, incomplete evidence
  hold, suspended specialist resume, CEO handoff, CCO contract assertions,
  prohibited-action enforcement, specialist isolation, and CCO-only assignment.
- Updated the foundation bootstrap position count to 30 and verified the
  CCO/Communications reporting line.
- Updated `test_still_unimplemented_department_runtime_is_held_without_false_completion`
  to use the still-held `People` department, since Communications is now implemented.
- Kept Alembic at `0071_structured_shortage_occupation_evidence`; no schema
  migration was introduced.
- Complete verification passed with **605 API tests, 0 failed**, with only the
  existing Starlette TestClient/httpx deprecation warning. Web production build
  passed with 37 routes. People and Legal remain held.

## 2026-08-11 - Phase 13.11 Finance/CFO bounded department runtime

- Enabled the Finance department runtime for bounded `internal.analysis` only.
- Added `Financial Analyst` and `Accounting Lead` L2 specialist positions
  reporting to the CFO, with role cards, controlled-agent handlers, output
  schemas, and registry entries.
- Hardened the CFO position contract with required specialists, required
  evidence fields, and explicit prohibited actions.
- Added finance evidence fields: cost structure, pricing model, revenue model,
  budget constraints, scenario parameters, AP/AR aging, reconciliation,
  audit trail, chart of accounts, compliance controls, and tax/treaty implications.
- Blocked Finance specialists from funds movement, pricing changes, spend
  commitments, contract signing, tax/regulatory representations, journal
  entries, external sends, and any external action.
- Added `delegate_finance_work` and integrated Finance into the department
  execution adapter so the CFO delegates to both specialists and the CEO
  receives an evidence-backed L3 decision receipt on completion.
- Added Finance work-item routing so Finance work is assigned to the CFO and
  runs through the same bounded execution path as other hardened departments.
- Added focused regressions for Finance internal analysis, incomplete evidence
  hold, suspended specialist resume, CEO handoff, CFO contract-mismatch repair,
  prohibited-action enforcement, specialist isolation, and CFO-only assignment.
- Updated the foundation bootstrap position count to 28 and verified the
  CFO/Finance reporting line.
- Kept Alembic at `0071_structured_shortage_occupation_evidence`; no schema
  migration was introduced.
- Complete verification passed with **597 API tests, 0 failed**, with only the
  existing Starlette TestClient/httpx deprecation warning. Web production build
  passed with 37 routes. Communications, People, and Legal remain held.

## 2026-08-11 - Independent source-review workflow UX and audit closure

- Added a dedicated `/source-certification-review` workspace for genuine independent
  human review of structured source certifications, with a bounded pending queue and
  exact immutable projection selection.
- Added read-only review-queue and review-workspace APIs. They expose certification,
  jurisdiction, authority, source, projection, deterministic review-pack identity,
  authenticated reviewer/proposer conflict state, submission requirements, and durable
  audit history without mutating certification state.
- Multi-projection sources remain fail-closed until an exact `source_snapshot_id` is
  selected. The review workspace never silently chooses among years or snapshots.
- The reviewer UI shows immutable source text and every structured entry side-by-side,
  supports downloading the exact JSON pack, and requires explicit 64-character pack-hash
  confirmation, substantive notes, and independent-human attestation before submission.
- Durable review receipts are rendered from the existing audit log after a decision;
  certification decisions remain distinct from pathway publication and external product
  validation.
- Added focused regressions for queue determinism, read-only state, case-insensitive
  proposer/reviewer blocking, snapshot pinning, audit-history reconstruction, and
  authenticated review-workspace API behavior.
- Added the reviewer workspace to navigation and responsive styling. No database
  migration is introduced; Alembic remains at `0071_structured_shortage_occupation_evidence`.
- This patch does not approve/reject the live Austria 2026 certifications, publish
  pathway v3, or release the external-human validation gate.

- Complete verification passed with **589 API tests** plus the complete local
  quality gate; only the existing Starlette TestClient/httpx deprecation warning
  remained.
- This slice required no database migration or live regulatory write;
  PostgreSQL remained at `0071_structured_shortage_occupation_evidence`.
- Added the `/source-certification-review` reviewer workspace with queue,
  immutable evidence-pack inspection, source/projection comparison, deterministic
  hash confirmation, download, role-aware submission controls, independent-human
  attestation, and audit-history presentation.
- Read-only live workspace validation reported exactly two pending structured
  Austria certifications.
- National certification `599f7ce7-b85e-4d02-b3ca-ea17b75aba84` remained
  `pending_review`, with **64 entries**, pack state `ready`, zero review-history
  records, and SHA-256
  `b8073504eef684a1d02c5e99efb16c9bf1225c89c807196ce103b0bb9b9cffe7`.
- Regional certification `f4cf5f04-0519-4cad-b5c2-88ec1183ded5` remained
  `pending_review`, with **66 entries**, pack state `ready`, zero review-history
  records, and SHA-256
  `46f4b74a379aaea9a3bd90f1da14166a1ea408842020cf2b700059ff8687920d`.
- Austria pathway version 3 remained draft and publication readiness remained
  false. Both national and regional certification blockers were returned and an
  independent reviewer remained required.
- Pre/post smoke database checks matched exactly. No certification review,
  approval, pathway publication, or external-validation release occurred.


## 2026-08-11 - Independent source-review readiness

- Added deterministic reviewer-facing evidence packs for source certifications backed by
  structured shortage-occupation evidence. Each pack pins certification/source/authority
  identity, the immutable source snapshot, exact projection identity, and every structured
  occupation row while also exposing the source text for human comparison.
- Added stable evidence-pack SHA-256 generation and fail-closed snapshot selection when a
  source has more than one structured projection.
- Structured source reviews now require the exact pack SHA-256 plus an explicit
  independent-human attestation. Proposer/reviewer identity separation is enforced
  case-insensitively, and pack generation itself never changes certification state.
- Review evidence is recorded in the existing durable audit log with the pack version/hash,
  pinned snapshot, projection identity, reviewer decision, and attestation. No schema
  migration is required; Alembic remains at `0071_structured_shortage_occupation_evidence`.
- Historical/non-structured certifications keep their existing review behavior.
- Pathway publication readiness now aggregates deterministic evidence blockers so Austria
  v3 can expose both pending national and regional certification blockers simultaneously.
- Added focused regressions for pack determinism, source-text/entry projection content,
  attestation/hash enforcement, case-insensitive reviewer separation, multi-projection
  snapshot pinning, audit evidence, API enforcement, legacy compatibility, and aggregate
  pathway blockers.
- This code slice does not approve or reject either live Austria 2026 source, publish the
  pathway, or release the external-human validation gate. Live reviewer-pack generation is
  a read-only post-verification step.

- Post-patch validation completed with **583 passed** and the complete local quality gate
  green; only the existing Starlette TestClient/httpx deprecation warning remained.
- Read-only live review-pack generation pinned the national certification
  `599f7ce7-b85e-4d02-b3ca-ea17b75aba84` to **64** entries with pack SHA-256
  `b8073504eef684a1d02c5e99efb16c9bf1225c89c807196ce103b0bb9b9cffe7`, and the
  regional certification `f4cf5f04-0519-4cad-b5c2-88ec1183ded5` to **66** entries with
  pack SHA-256 `46f4b74a379aaea9a3bd90f1da14166a1ea408842020cf2b700059ff8687920d`.
- Both live certifications remained `pending_review`; Austria pathway v3 remained draft,
  unapproved, and unpublished, and publication readiness remained held with both required
  structured-evidence blockers visible. No independent-human attestation was submitted.


## 2026-08-11 - Austria structured-evidence pathway integration

- Reserved `national_occupation_list` and `regional_occupation_list` pathway evidence
  roles for canonical structured shortage-occupation projections. Structured roles
  must be required for publication and must pin the exact materialized year, scope,
  entry count, entry-set hash, extraction version, and source-snapshot content hash.
- Added an idempotent pathway integration workflow that clones the current immutable
  pathway version, preserves core route/rules/content, and adds national plus regional
  structured occupation evidence without mutating the source version. Stale-source
  branching fails closed.
- The Austria `at-rwr-skilled-worker-shortage-occupation` pathway now requires both
  structured occupation-list roles before publication, so historical core-only drafts
  cannot bypass the new evidence gate.
- Added read-only pathway publication readiness reporting, including source
  certification status by evidence role, so pending structured evidence can be
  attached to a draft while publication remains deterministically held.
- Added regressions for projection identity mismatch, optional-evidence bypass,
  idempotent integration, stale-source rejection, pending certification blockers, and
  synthetic publication only after both supplemental certifications are approved.
- No database migration is introduced; Alembic remains at
  `0071_structured_shortage_occupation_evidence`.
- The code patch did not create Austria pathway version 3 automatically. The live
  integration was intentionally deferred until focused/full validation passed and a
  fresh PostgreSQL backup was verified. The Austria-wide and regional 2026 source
  certifications remained `pending_review` throughout.

- Focused verification passed with **14 tests** and the complete API suite passed
  with **577 tests**; the complete local quality gate passed. The only warning was
  the existing Starlette TestClient/httpx deprecation warning.
- Persistent PostgreSQL remained at
  `0071_structured_shortage_occupation_evidence`; this slice required no migration.
- The canonical pre-write backup was
  `gmai-postgres-before-at-pathway-v3-20260811-022050.dump`
  (3,673,174 bytes; SHA-256
  `590342DB52783D804034D3F5C36F97B9910897F482E7E6FCB794682DDA494383`).
- The live integration created Austria skilled-worker pathway version 3
  `35412414-2cfd-489b-8731-c375d41d6f52` from version 2
  `cb17657f-be9f-4ea9-b7ce-795cf0e1b1d5`. Version 3 remains draft,
  unapproved, and unpublished.
- Version 3 binds `core_route`, `national_occupation_list`, and
  `regional_occupation_list` as required publication evidence, preserving the
  exact immutable 2026 national and regional source snapshots.
- Publication readiness remains `false` and an independent reviewer remains
  required. The core route is approved while both 2026 occupation-list
  certifications remain `pending_review`.
- A second controlled integration returned `created = false` and reused the same
  version-3 ID. Direct PostgreSQL verification confirmed exactly three pathway
  versions exist, proving that no version 4 was created.
- No 2026 source certification was approved, no pathway was published, and the
  external-human validation gate remains held.



## 2026-08-10 - Structured shortage-occupation evidence

- Added migration `0071_structured_shortage_occupation_evidence` and normalized
  `shortage_occupation_entries` for deterministic year/scope/category/province
  projections of immutable shortage-occupation source snapshots.
- Added the bounded `austria_migration_shortage_v1` parser for the official
  migration.gv.at Austria-wide and regional shortage-occupation pages. The parser
  requires exact source/snapshot provenance, one declared year, contiguous numbered
  groups, an operator-pinned expected group count, and recognized Austrian province
  names for regional rows.
- Preserves exact source category labels and source-listed occupation aliases while
  normalizing only presentation differences; no fuzzy, semantic, translated, or LLM
  occupation classification is introduced.
- Materialization is immutable and idempotent. Reprocessing the same snapshot reuses
  deterministic entry hashes; conflicting derived content for an immutable snapshot
  fails closed instead of being silently rewritten.
- Added exact lookup states for national and province-specific list applicability,
  including explicit `ambiguous` and `province_required` outcomes.
- Lookup reports source-certification governance readiness separately from list
  applicability and warns that a structured source-list match is not case eligibility
  or a prediction of authority outcome.
- Added regulatory-intelligence endpoints for controlled materialization and read-only
  lookup, plus focused regressions for parser boundaries, province handling,
  idempotency, audit receipts, ambiguity, and certification state.
- Hardened the fresh-database Alembic regression on slower Windows hosts by raising
  the upgrade/downgrade/re-upgrade subprocess budget from 60 to 180 seconds. This
  changes test-harness timing only and does not alter migration or production behavior.
- Before the live migration, persistent PostgreSQL remained at
  `0070_pathway_version_evidence_provenance`; the controlled pre-`0071` backup and
  migration were performed only after focused/full verification passed. The
  Austria-wide and regional 2026 source certifications and the external-human
  validation gate remained held throughout.



- Persistent PostgreSQL was backed up before `0071` to
  `gmai-postgres-before-0071-20260810-135554.dump` (3,637,418 bytes;
  SHA-256 `7355C9A9C18A61E2FD261AF9333FDEC4B0FDDBAAF660F3CA0996458758C95FB6`).
- Validation passed with **39 focused tests** and **571 complete API tests**;
  the complete local quality gate passed. The single warning is the existing
  Starlette TestClient/httpx deprecation warning.
- Austria 2026 materialization produced **64 national groups** with entry-set
  SHA-256
  `43f1b9fad49777a89da280395124a6d3e4608219b835d144765f47e148d00301`
  and **66 regional groups** with entry-set SHA-256
  `5fd467b7bb3d1681dcf90f604d648af83483dfec443e4ae1d6bc5faf8e7bc238`.
- Idempotency was verified by a second materialization: zero new rows were
  created, all 64 national and 66 regional rows were recognized as existing,
  and both entry-set hashes remained identical.
- Deterministic lookups confirmed list applicability while retaining
  `governance_ready = false`; both exact 2026 supplemental certifications
  remain `pending_review`.
- Austria skilled-worker pathway versions 1 and 2 remain draft, unapproved,
  and unpublished. Materialization created or published no pathway version.

## 2026-08-10 - Pathway multi-source evidence provenance

- Added migration `0070_pathway_version_evidence_provenance` and normalized
  `mobility_pathway_version_evidence` records for role-aware multi-source pathway
  provenance.
- Backfills the existing singular pathway source/snapshot pair as `core_route` while
  retaining the legacy columns for compatibility.
- Pathway drafts can declare multiple immutable source/snapshot pairs. Publication
  now requires every referenced human-published rule's exact provenance to be
  represented in the pathway evidence set.
- Required non-core evidence must have an approved source certification before a
  pathway can be published; pending source evidence may remain attached to drafts.
- Rule-bearing non-core evidence cannot be marked optional to bypass certification,
  and a core source with certification history cannot publish while no approved
  certification exists.
- Multi-year scenarios now pin all declared pathway evidence snapshots. Pathway risk
  analysis and regulatory-impact source matching inspect all declared evidence rather
  than only the historical core source.
- Added focused regressions for multi-source publication gating, rule-provenance
  containment, legacy core fallback, risk inspection, and regulatory-impact matching.
- Persistent PostgreSQL was backed up immediately before migration to
  `0070_pathway_version_evidence_provenance`; backup:
  `gmai-postgres-before-0070-20260810-124945.dump`, 3,631,344 bytes,
  SHA-256 `7EC3E2E5E350A59EC21D4345662AC1B6E36B9F172C422BFA454675025FEB7E5C`.
- PostgreSQL migration validation reported `missing_core_backfills = 0` and four
  historical `core_route` evidence rows. The Austria skilled-worker pathway versions
  remained draft/unpublished with exact matching core source/snapshot provenance.
- Post-migration validation passed with **14 focused tests** and **560 complete API
  tests**; repository policy, release consistency, database migrations, Docker
  production profile, and local schema checks also passed. The single warning is the
  existing Starlette TestClient/httpx deprecation warning.
- The existing Austria general skilled-worker supplemental certification remains
  approved. The Austria-wide and regional 2026 source certifications and the
  external-human validation gate remain held; this change grants no regulatory
  approval and creates no national/regional pathway evidence automatically.


## 2026-08-10 - Supplemental source-certification multiplicity hardening

Validation:
- SQLite upgrade/downgrade/re-upgrade migration smoke test passed.
- PostgreSQL migrated successfully to
  `0069_source_certification_multiplicity`; the new primary and supplemental
  partial unique indexes were verified directly in PostgreSQL.
- Live Austria regression created the regional 2026 supplemental
  certification as independent version 1 while preserving the existing
  approved skilled-worker certification and pending Austria-wide 2026
  certification.
- Added database-backed review-isolation coverage, including same-source
  version supersession and legacy cross-source supersession-pointer cleanup.
- Focused suite: 18 passed.
- Complete API suite: 552 passed, 1 non-blocking deprecation warning.
- The external-human validation gate and the two 2026 source-certification
  review gates remain held.

- Fixed supplemental source-certification lineage so multiple official sources
  in the same jurisdiction and domain can be independently pending, versioned,
  approved, and superseded.
- Primary immigration certification remains jurisdiction-scoped and unchanged.
- Supplemental certification lineage is now scoped by jurisdiction,
  certification scope, and official-source identity.
- Approval of one supplemental source no longer supersedes approved
  certifications for other sources in the same domain.
- Added bounded cleanup for legacy cross-source supersession pointers created
  before this hardening while preserving certification identity and history.
- Added focused regression coverage.
- Added Alembic migration
  `0069_source_certification_multiplicity` because the historical database
  constraint still enforced jurisdiction/scope-wide supplemental versioning.
- Database uniqueness now preserves jurisdiction-scoped primary certification
  while allowing source-scoped supplemental certification version lineages.
- SQLModel metadata mirrors the migrated database invariant.
- The external-human validation gate remains held.


## 2026-08-10 - Existing-source baseline linkage hardening

- Live PostgreSQL verification reconciled the Austria skilled-employment batch
  to its existing approved authority, official source, and source monitor while
  preserving the certification ID, batch payload hash, retrieval run, immutable
  snapshot ID, and snapshot content hash. A repeated reconciliation changed zero
  rows, confirming idempotency.

- Fixed certification-only coverage batches so already-onboarded sources persist
  their existing regulatory-authority, official-source, and monitor linkage.
- Added backward-compatible baseline resolution for certification-only batch items
  created before the linkage fix.
- Existing immutable source snapshots are reused when present; the fix does not
  create a coverage claim or publish a verified rule.
- Added regression coverage reproducing the Austria external-validation linkage gap.
- Added an audited, idempotent batch-linkage reconciliation operation that fills only missing derived authority/source/monitor foreign keys and rejects conflicting stored provenance.


## 2026-08-09 — Controlled official-source authority remediation

- Added an audited API to reassign an existing official source to the jurisdiction's
  independently approved primary immigration authority without replacing the source,
  monitor, retrieval history, or immutable snapshots.
- Reassignment fails closed across jurisdictions and for sources with pending or approved
  certifications, and it is idempotent once the approved authority is already attached.
- This hardening closes the duplicate-authority remediation gap discovered while preparing
  Austria skilled-employment external validation evidence; no schema migration is required.


## 2026-08-09 - Phase 13.10.2.1 PostgreSQL migration portability hardening

- Corrected PostgreSQL-incompatible Boolean defaults in
  `0058_deadline_emergency_escalation` by replacing integer defaults with
  dialect-safe `sa.false()`.
- Corrected Security, SOC, and Marketing migration bindings for
  `organization_positions.id` so native PostgreSQL UUID columns are bound as
  UUID rather than VARCHAR.
- Added regression coverage preventing integer Boolean migration defaults and
  string bindings for the UUID organization-position identifier.
- Verified the corrections against a backed-up persistent PostgreSQL database
  and upgraded it transactionally from `0056_ai_organization_governance` to
  the unchanged unique head `0068_external_validation_framework`.
- Confirmed governed data survived intact: 292 jurisdictions, 89 official
  sources, 521 source snapshots, 86 verified rules, 1 mobility pathway, and
  2 mobility pathway versions.
- Focused migration regression coverage passed with **4 tests passed**.
- Complete Phase 13.10.2.1 verification passed with **534 tests passed,
  0 failed** and the complete local quality gate green.
- The external-human validation gate remains held; this hardening does not
  substitute for the required mobility-user and independent-professional run.

## 2026-08-08 — Phase 13.10.2 external mobility validation framework

- Added migration `0068_external_validation_framework` with durable validation scenarios,
  runs, external-human reviews, findings, and evidence references.
- Added a deterministic `held` / `failed` / `passed` validation gate requiring one real
  mobility user and one distinct independent professional/operator.
- Added acceptance thresholds for user understanding/usefulness, professional operational
  usefulness, jurisdiction/pathway correctness, 100% material-rule traceability, zero
  unsupported legal-certainty statements, and zero missing critical document requirements.
- Added Critical/High/Medium/Low finding triage. Critical and High findings must be resolved;
  only Medium/Low findings can receive explicit Human Board risk acceptance.
- Added durable evidence pinning to Truth Claims, Verified Rules, Official Sources, immutable
  Source Snapshots, pathway versions, pathway comparisons, documents, and operator notes.
- Added founder-intervention count to each run as an autonomy metric without allowing that
  metric to override correctness/evidence requirements.
- Added an Austria skilled-employment discovery scenario and external-review templates that
  deliberately do not encode an expected pathway or legal threshold.
- Added `/api/v1/external-validation` endpoints, declarative auth rules, router registration,
  regression tests, and a small operator validation workspace.
- Finance, Communications, People, and Legal remain held. The code framework does not satisfy
  the external-validation gate; a real user + professional/operator PASS receipt is still
  required before another executive department is activated.
- Phase 13.10.2 software release verification completed successfully at migration head
  `0068_external_validation_framework`: **532 API tests passed, 0 failed**, the
  `/validation` production build passed, and the complete local quality gate passed.
  The external-human validation gate itself remains held until a real mobility user and
  an independent professional/operator produce a qualifying PASS run.

## 2026-08-08 — Phase 13.10.1 platform hardening and runtime registration

- Preserved the delivered Phase 13.10 Marketing/CMO runtime at migration head
  `0067_marketing_runtime_contract`; this hardening slice introduces no schema
  migration.
- Wired the existing startup-safety module into application startup and fail closed
  in production when authentication is disabled, unsigned header-role trust is
  enabled, or JWT/admin credentials remain missing, default, or too short.
- Defaulted MinIO server-side encryption to enabled and made production identity-
  document storage require encrypted, TLS-protected, non-default, pre-provisioned
  MinIO/S3-compatible storage; local document storage now refuses production use.
- Added shared query limits and bounded previously unbounded document/lead reads.
- Replaced inline FastAPI router registration with an ordered `RouterSpec` registry
  while preserving all 62 registrations, including compatibility registrations.
- Replaced the hand-written route-role authorization cascade with an ordered,
  declarative authorization-rule registry while preserving existing role behavior.
- Added a `DepartmentRuntimeSpec` registry and common execution/completion adapter
  for Technology, Product, Security, Security Operations/SOC, and Marketing. The
  delivered Marketing runtime remains active for bounded `internal.analysis`;
  Finance, Communications, People, and Legal remain explicitly held.
- Removed repeated executive-contract repair branches in organization governance and
  route contract recovery through runtime metadata instead.
- Added capability-boundary, startup fail-closed, pagination, router-registry, and
  authorization-policy regression tests.
- Added a migration/ROADMAP consistency check to CI and the local quality gate, using
  the unique Alembic graph head rather than filename ordering.
- Added `.gmai-patch-backups/` to ignore/scanner exclusions so local replacement
  backups no longer slow repository policy checks or belong in future source control.
- Added an external-validation gate before activating Finance, Communications,
  People, or Legal: one real mobility user and one professional/operator must first
  exercise the end-to-end Truth Engine/pathway workflow and resulting defects must
  be triaged.
- Release verification completed successfully at migration head
  `0067_marketing_runtime_contract`: **524 API tests passed, 0 failed**, and the
  complete local quality gate passed.

## 2026-08-08 — Phase 13.10 bounded Marketing/CMO runtime contract

- Expanded the registered organization from 22 to 24 positions by adding the
  Chief Marketing Officer Agent, Creative Director Agent, and Marketing Manager
  Agent under CEO and CMO accountability.
- Added full position contracts for the CMO, Creative Director, and Marketing
  Manager through migration `0067_marketing_runtime_contract`, including required
  evidence fields, required specialist outputs, prohibited direct actions, and a
  unique work/delegate constraint on Marketing delegation records.
- Added `agents/role_cards/CMO.md`, `agents/role_cards/Creative_Director.md`, and
  `agents/role_cards/Marketing_Manager.md` with bounded L3/L2 analysis contracts
  for brand fit, creative quality, messaging, audience alignment, channel fit,
  campaign plan, growth metrics, and budget constraints.
- Implemented a fail-closed Marketing department-head runtime that delegates only
  `internal.analysis` work to the Creative Director and Marketing Manager,
  validates required evidence fields, validates required specialist outputs,
  records dissent and material risks, and fails closed on pricing changes,
  policy publication, external messaging, spend, contracts, external action,
  campaign launch, or non-Marketing work requests.
- Enforced that Marketing specialists cannot be invoked for non-Marketing work,
  that Marketing work is assigned only to the CMO, and that incomplete evidence
  or missing outputs are recorded as gaps rather than silently approved.
- Connected the controlled-agent registry and role-card loader to the Marketing
  specialist contracts so runtime prompts, rejection behavior, and output schemas
  are consistent with the persisted position contract.
- Added Marketing runtime regression coverage including evidence-field validation,
  output-field validation, non-Marketing rejection, CMO-only assignment,
  required-delegate completeness, suspended-specialist resume, hardened contract
  enforcement, and evidence-aware fail-closed controlled-agent outputs.
- Updated `docs/ROADMAP.md` to mark the Marketing department runtime as delivered
  and identify Finance, Communications, People, and Legal as the remaining held
  departments.
- Full API suite passes with the expanded test suite at migration head `0067` and
  the local quality gate passes.

## 2026-08-07 — Phase 13.8 bounded Security/CISO runtime contract

- Expanded the registered organization from 19 to 22 positions by adding the
  Chief Information Security Officer Agent, Security Lead Agent, and Threat Analyst
  Agent under CISO accountability.
- Added full position contracts for the CISO, Security Lead, and Threat Analyst
  through migration `0065_security_runtime_contract`, including required evidence
  fields, required specialist outputs, prohibited direct actions, and a unique
  work/delegate constraint on Security delegation records.
- Added `agents/role_cards/CISO.md`, `agents/role_cards/Security_Lead.md`, and
  `agents/role_cards/Threat_Analyst.md` with bounded L2 analysis contracts,
  required inputs/outputs, and rejection rules for position suspension, contract
  changes, policy publication, secret access, deployment, infrastructure mutation,
  spend, and external action authority.
- Implemented a fail-closed Security department-head runtime that delegates only
  `internal.analysis` work to Security Lead and Threat Analyst, validates required
  evidence fields, validates required specialist outputs, records dissent and
  material risks, detects prompt-injection, jailbreak, data-exfiltration, and
  compromised-agent signals, and fails closed on external action, deployment,
  infrastructure mutation, secret access, spend, contract, or non-Security work
  requests.
- Enforced that Security specialists cannot be invoked for non-Security work,
  that CISO work is assigned only to the CISO, and that incomplete evidence or
  missing outputs are recorded as gaps rather than silently approved.
- Connected the controlled-agent registry and role-card loader to the Security
  specialist contracts so runtime prompts, rejection behavior, and output schemas
  are consistent with the persisted position contract.
- Added Security runtime regression coverage including evidence-field validation,
  output-field validation, non-Security rejection, CISO-only assignment,
  required-delegate completeness, suspended-specialist handling, hardened contract
  enforcement, and prompt-injection / compromised-agent detection in deterministic
  handlers.
- Updated `docs/ROADMAP.md` to mark the Security department runtime as delivered
  and identify Marketing/Finance/Communications/People/Legal as the remaining held
  departments.
- Full API suite passes with the expanded test suite at migration head `0065` and
  the local quality gate passes.

## 2026-08-07 — Phase 13.9 bounded Security Operations/SOC runtime contract

- Added the Security Operations (SOC) department under the CISO with two bounded
  L2 specialists: SOC Lead and SOC Analyst.
- Hardened the SOC Lead and SOC Analyst position contracts through migration
  `0066_soc_runtime_contract`, including required evidence fields, required
  specialist outputs, prohibited direct actions, and a unique work/delegate
  constraint on Security Operations delegation records.
- Added `agents/role_cards/SOC_Lead.md` and `agents/role_cards/SOC_Analyst.md`
  with bounded L2 analysis contracts for agent-behavior monitoring, audit-log
  triage, incident coordination, and anomaly detection.
- Updated `agents/role_cards/CISO.md` to name the SOC Lead and SOC Analyst as
  direct reports alongside Security Lead and Threat Analyst.
- Implemented a fail-closed Security Operations department-head runtime that
  delegates only `internal.analysis` work to SOC Lead and SOC Analyst, validates
  required evidence fields, validates required specialist outputs, records dissent
  and material risks, and fails closed on position suspension, policy publication,
  secret access, deployment, infrastructure mutation, spend, contract, or
  external-action requests.
- Enforced that SOC specialists cannot be invoked for non-Security-Operations
  work, that Security Operations work is assigned only to the CISO, and that
  incomplete evidence or missing outputs are recorded as gaps rather than
  silently approved.
- Connected the controlled-agent registry and role-card loader to the SOC
  specialist contracts so runtime prompts, rejection behavior, and output
  schemas are consistent with the persisted position contract.
- Added SOC runtime regression coverage including evidence-field validation,
  output-field validation, non-SOC rejection, CISO-only assignment,
  required-delegate completeness, suspended-specialist resume, prohibited-action
  enforcement, and prompt-injection / compromised-agent / data-exfiltration
  detection.
- Updated `docs/ROADMAP.md` to mark the Security Operations/SOC runtime as
  delivered and identify Marketing/Finance/Communications/People/Legal as the
  remaining held departments.
- Full API suite passes with 500+ tests at migration head `0066` and the local
  quality gate passes.

## 2026-08-03 — Phase 13.6 bounded Product/CPO runtime contract

- Expanded the registered organization from 15 to 17 positions by adding Product
  Manager and Design Agent under CPO accountability.
- Added full position contracts for the CPO, Product Manager, and Design Agent
  through migration `0064_product_runtime_contract`, including required
  evidence fields, required specialist outputs, prohibited direct actions, and a
  unique work/delegate constraint on Product delegation records.
- Added `agents/role_cards/Product_Manager.md` and
  `agents/role_cards/Design_Agent.md` with bounded L2 analysis contracts,
  required inputs/outputs, and rejection rules for external action, client
  delivery, deployment, infrastructure mutation, spend, and contract authority.
- Rewrote `agents/role_cards/CPO.md` to report to the CEO, own Product
  accountability, delegate to Product Manager and Design Agent, and escalate
  product strategy, roadmap, market entry, design-system, and irreversible
  decisions.
- Implemented a fail-closed Product department-head runtime that delegates only
  `internal.analysis` work to Product Manager and Design Agent, validates required
  evidence fields, validates required specialist outputs, records dissent and
  material risks, and fails closed on external action, deployment, infrastructure,
  secret-access, spend, contract, or non-Product work requests.
- Enforced that Product specialists cannot be invoked for non-Product work, that
  CPO work is assigned only to the CPO, and that incomplete evidence or missing
  outputs are recorded as gaps rather than silently approved.
- Connected the controlled-agent registry and role-card loader to the Product
  specialist contracts so runtime prompts, rejection behavior, and output schemas
  are consistent with the persisted position contract.
- Added Product runtime regression coverage including evidence-field validation,
  output-field validation, non-Product rejection, CPO-only assignment,
  required-delegate completeness, and hardened contract enforcement.
- Updated `docs/ROADMAP.md` to mark the Product department runtime as delivered
  and identify Marketing/Finance/Communications/People/Legal as the remaining
  held departments.
- Full API suite passes with 473 tests at migration head `0064` and the local
  quality gate passes.

## 2026-08-03 — Phase 13.3 bounded Technology/CTO runtime contract

- Hardened the CTO, VP Engineering, and Lead Architect position contracts through
  migration `0063_cto_runtime_contract` with explicit capabilities, required
  evidence fields, required specialist outputs, prohibited direct actions, and a
  unique work/delegate constraint on delegation records.
- Added `agents/role_cards/VP_Engineering.md` and
  `agents/role_cards/Lead_Architect.md` with bounded L2 analysis contracts,
  required inputs/outputs, and rejection rules for external action, deployment,
  infrastructure mutation, secret access, spend, and contract authority.
- Updated `agents/role_cards/CTO.md` to report to the CEO, own Technology
  accountability, delegate to VP Engineering and Lead Architect, and escalate
  production, security, financial, contractual, and irreversible decisions.
- Implemented a fail-closed Technology department-head runtime that delegates only
  `internal.analysis` work to VP Engineering and Lead Architect, validates
  required evidence fields, validates required specialist outputs, records
  dissent and material risks, and fails closed on deployment, infrastructure,
  secret-access, spend, contract, or external-action requests.
- Enforced that Technology specialists cannot be invoked for non-Technology work,
  that CTO work is assigned only to the CTO, and that incomplete evidence or
  missing outputs are recorded as gaps rather than silently approved.
- Connected the controlled-agent registry and role-card loader to the Technology
  specialist contracts so runtime prompts, rejection behavior, and output
  schemas are consistent with the persisted position contract.
- Added Technology runtime regression coverage including evidence-field
  validation, output-field validation, non-Technology rejection, CTO-only
  assignment, required-delegate completeness, and hardened contract enforcement.
- Updated `docs/ROADMAP.md` to mark the Technology department runtime as
  delivered and identify the Product department runtime as the next active gate.
- Full API suite passes with 463 tests at migration head `0063` and the local
  quality gate passes.

## 2026-08-03 — Phase 13.3 bounded CEO and executive-consultation ledger

- Added migration `0061_exec_council_consultations` and a durable consultation
  ledger recording the decision, work item, executive domain, evidence,
  recommendation, confidence, dissent, status, and completion time.
- Added migration `0062_ceo_coordination_fencing` with durable claim tokens and
  claimed-at timestamps; every CEO hold, Board promotion, release, and final
  decision now uses a token-qualified compare-and-set transition.
- Implemented a fail-closed CEO coordinator that may approve only
  evidence-complete `internal.analysis` work at L3 after a distinct COO
  consultation; its receipt explicitly authorizes no external action.
- Added immediate event-driven CEO coordination after organizational execution,
  an atomic coordination lease with stale-claim recovery, a recovery scanner in
  Celery Beat, an admin trigger that retains the `ceo-agent` runtime identity,
  and a Board-visible consultation endpoint.
- Prevented CEO self-approval, blocked CEO handling of L4 and emergency matters,
  kept registered external actions behind their separate human gates, and made
  the Board-decision endpoint reject pending CEO matters unless the explicit
  Board-override lane is used.
- Corrected emergency promotion so work is removed from the executable queue,
  upgraded to L4, assigned to the Board, represented by a `pending_board`
  decision, forward-healed after a partial replay, and reported through one
  replay-safe incident packet.
- Held registered departments whose specialist runtime is not yet operational,
  preventing empty delegation sets from being reported as completed work.
- Made stored executive dissent renderable in the Board Packet when supplied;
  cross-functional executive completion and dissent-submission paths remain a
  later Phase 13 gate.
- Limited automatic risk closure to non-emergency governance-boundary records;
  operational and emergency risks retain their own resolution lifecycle.
- Removed the misleading legacy `ai_ceo` alias to Application Readiness and
  persisted the CEO's orchestrator-only, no-direct-action position contract
  through migration or explicit Human Board bootstrap, never the CEO runtime.
- Added CEO, consultation, owner-boundary, self-approval, L4, scanner, and
  emergency-idempotency regression coverage. The full API suite passes with
  447 tests at migration head `0062`.

## 2026-08-03 — Phase 13.6 bounded Operations department runtime

- Expanded the registered organization from 13 to 15 positions by adding
  Operations Coordination and Business Intelligence under COO accountability.
- Added full role and output contracts for Sales Intelligence, Operations
  Coordination, Business Intelligence, and Application Readiness, correcting the
  legacy role-card mappings used by controlled-agent prompts.
- Added deterministic, review-gated Operations Coordination and Business
  Intelligence handlers that expose evidence gaps, confidence, safe next actions,
  and blocked external actions.
- Added an idempotent COO delegation plan: general Operations objectives route to
  three core specialists, while mobility-case events also route to Application
  Readiness.
- Proved routine L1 Operations work completes without CEO or Board interruption,
  while the existing L3/L4 classification and escalation paths remain unchanged.
- Expanded hierarchy, role-card, agent-registry, suspension, output-ledger, and
  direct-objective regression coverage. The full API suite passes with 435 tests.

## 2026-08-03 — Phase 13.4 fail-closed external-action gates

- Added a central external-action policy registry for client sends, authority
  submissions, payments, contracts, and production deployments, exposed through
  the governed organization API for Board inspection.
- Revalidated external automation delivery approval at dispatch time, including
  the complete review receipt and different-reviewer invariant, so direct state
  mutation cannot bypass the human gate.
- Closed an authority-submission tracking gap: an agency submission can now be
  recorded only for an approved or already-submitted application.
- Kept payment initiation, contract signature, and production deployment
  non-executable until dedicated reviewed adapters are explicitly registered.
- Expanded deterministic authority classification and regression coverage for
  gate completeness, unknown actions, unavailable executors, application state,
  and dispatch-state tampering. The full API suite passes with 428 tests and the
  complete local quality gate passes at migration head `0060`.

## 2026-08-03 — Phase 13.4 bounded execution controls

- Added migration `0060_org_execution_controls` with durable execution-attempt
  records and work-item controls for attempt budgets, claim tokens, retry timing,
  failure details, and cancellation provenance.
- Added an atomic claim boundary so duplicate API or Celery delivery cannot run
  an already-running, completed, cancelled, not-yet-due, or exhausted work item.
- Added database-scheduled exponential retry backoff capped at five minutes and
  a configurable, non-resettable one-to-five attempt ceiling.
- Preserved completed delegation outputs across partial recovery so retrying a
  failed organizational task does not replay work that already succeeded.
- Added Human Board-only cancellation and retry endpoints plus an execution
  attempt ledger endpoint for CEO and Board inspection.
- Added cooperative running-work cancellation and immediate queued-work
  cancellation with delegation and audit-state preservation.
- Expanded regression coverage for cancellation authorization, replay blocking,
  mid-run failure recovery, retry exhaustion, attempt history, and due-retry
  scanner selection. The full API suite passes with 425 tests.

## 2026-08-02 — Phase 13.4 evidence-grounded organizational outputs

- Added migration `0059_org_action_outputs` and a durable organizational
  action-output ledger keyed idempotently to each delegation.
- Every delegated result now records its accountable position, authority basis,
  evidence references, normalized confidence and its basis, expected impact,
  rollback posture, bounded output, and execution status.
- Added a governed aggregate envelope to each completed work item and linked its
  exact output IDs and aggregate confidence into the pending executive decision.
- Added `GET /api/v1/organization/work-items/{id}/outputs` for traceable CEO and
  Board inspection of the evidence behind organizational work.
- Preserved the human gate: action outputs remain internal, identify blocked
  external actions, and do not authorize client-facing or irreversible effects.
- Added regression coverage for routine output persistence, evidence and impact
  fields, confidence aggregation, replay protection, missing-ledger handling, and
  L4 decision evidence linkage.

## 2026-08-02 — Phase 13.5 governed Board Packet generation

- Added the admin-only `POST /api/v1/organization/board-packets` endpoint and a
  recent-packet ledger for on-demand Board reporting.
- Added CEO-prepared packet content covering the recommendation, exact approval
  requested, source-record evidence, alternatives, expected impact, dissent,
  resource impact, urgency, pending Board decisions, and emergency risks.
- Added daily and weekly Celery Beat generation with deterministic packet keys,
  making recurring task retries replay-safe instead of publishing duplicates.
- Connected emergency escalation to an idempotent incident Board Packet keyed to
  the affected organizational work item.
- Corrected organization task database-engine lookup so isolated runtimes and
  tests always use the active configured engine.
- Added regression coverage for Board-only creation, packet content and listing,
  emergency generation, recurring task execution, schedule registration, and
  recurring-packet replay safety.

## 2026-08-02 — Phase 13.2 deadline, reminder, and emergency escalation controls

- Added migration `0058_deadline_emergency_escalation` to track `due_at`,
  `reminded_at`, `escalated_at`, and `is_emergency` on organizational work and
  decisions, plus `is_emergency` on risk escalations.
- Added `POST /api/v1/organization/work-items/{id}/deadline` and
  `/decisions/{id}/deadline` for the Board to set accountability deadlines.
- Added `POST /api/v1/organization/work-items/{id}/escalate` to move a work item
  to its parent position (e.g., COO → CEO) with an audit trail and refreshed
  risk escalation.
- Added `POST /api/v1/organization/work-items/{id}/emergency` to mark a work
  item as emergency and escalate it all the way to the human Board immediately.
- Added `scan_organization_deadlines_task` Celery task that escalates overdue
  work and marks overdue decisions as reminded.
- Added regression tests for work deadlines, decision deadlines, manual escalation,
  emergency escalation to the Board, and overdue scanner escalation.

## 2026-08-02 — Phase 13.1 Board override and per-agent suspension controls

- Added migration `0057_position_suspension_tracking` to record when a position is
  suspended, by whom, and why.
- Added `POST /api/v1/organization/decisions/{id}/board-override` so the human
  Board can override L3 CEO decisions or re-decide L4 Board-reserved matters.
- Added `POST /api/v1/organization/positions/{id}/suspend` and `/resume` so the
  Board can pause individual agents while keeping the rest of the organization
  active.
- Enforced suspension during work routing (new delegations skip suspended
  positions) and during execution (existing delegations to a suspended position
  are held with a clear audit note).
- Protected the human Board position from being suspended by the organization.
- Added regression tests for Board override authorization, L3 override, L4
  override-through-Board-decision, position suspend/resume, and suspension impact
  on new and in-flight work.
- Updated `docs/ROADMAP.md` to migration head `0057`, 411 passing API tests, and
  mark Board override and per-agent suspension as delivered.

## 2026-08-02 — Phase 13 AI Organization governance foundation

- Added versioned organization positions plus durable work, delegation,
  executive-decision, risk-escalation, Board Packet, and global-control ledgers
  through migration `0056_ai_organization_governance`.
- Registered the human Board, CEO, eight executive department heads, Head of
  Product, and two bounded operating specialists as an executable hierarchy.
- Added CEO and department-head role cards with explicit reports-to, authority,
  accountability, and escalation contracts.
- Added deterministic L1-L4 authority classification, Board-reserved actions,
  CEO/Board escalation, human-only L4 decisions, audit records, and a global
  pause/resume control.
- Connected governed automation events to idempotent organizational work and
  added a Celery loop that executes queued specialist delegations.
- Added `/api/v1/organization` governance endpoints and a `/board-room` UI for
  the organization map, decision inbox, risks, work pulse, and shutdown control.
- Added Phase 13 regression tests and updated the structured roadmap to show the
  delivered foundation and remaining expansion work accurately.
- Standardized the client-portal device-mismatch response as a root-level public
  error contract while keeping the web client tolerant of the former nested
  FastAPI detail shape.

## 2026-08-02 — Roadmap restructuring and Phase 13 AI Organization direction

- Reorganized `docs/ROADMAP.md` into current release posture, execution order,
  active stabilization, ongoing evidence operations, future programmes, completed
  delivery map, and delivery-governance sections.
- Removed duplicated release-note detail from the roadmap; historical delivery
  remains available through this changelog, versioned feature documents, Git
  history, and Alembic migrations.
- Recorded the open Phase 12 stabilization gate: runtime database alignment,
  client-portal session security, device-mismatch error-contract repair, and
  frontend regression coverage.
- Defined Phase 13 as AI Organization Governance and Autonomous Operations, with
  the human owner as the Board and a governed CEO Agent coordinating executive,
  manager, and specialist agents.
- Added `docs/AI_ORGANIZATION_GOVERNANCE_V13_0.md` covering the organization tree,
  position contracts, L1-L4 authority, emergency escalation, required ledgers,
  CEO responsibilities, Board Packets, Board controls, and the first bounded
  autonomous workflow.
- Moved the former global-scale platform programme to Phase 14 so it follows the
  new organizational governance programme.
- Updated the canonical product blueprint and Head of Product role card to match
  the approved direction without claiming that the Phase 13 runtime already
  exists.

## 2026-07-25 — Business and Wealth Mobility advisory v11.4.1

- Enhanced `POST /api/v1/business-mobility-advisory/advise` to be situation-aware and commercially specific.
- Replaced generic fallback rationales with intent-specific actions, critical factors, and per-strategy fit scoring.
- Success meter now responds to disclosed capital, net worth, revenue, founder experience, business age, timeline, family relocation, source-of-funds confirmation, and published pathway/program availability.
- Risk-flagged situations (prior refusals, source-of-funds, sanctions/PEP exposure) now return the strongest lawful alternative plus remediation/specialist guidance, rather than falling back to a generic block.
- Prohibited-conduct signals remain capped and escalated; the response offers lawful remediation or an alternative route.
- Updated the LLM prompt to be commercially oriented while preserving the boundary against illegal acts.
- Added regression tests for situation-specific actions, lawful alternatives for risky situations, and success-meter sensitivity to capital/timeline.
- Updated `docs/BUSINESS_WEALTH_ADVISORY_V11_4.md`.

## 2026-07-25 — Automation connector hardening v12.4.1

- Added encrypted credential storage for automation connector configs via `app/services/automation_connector_encryption.py`, using Fernet keyed from `AUTOMATION_ENCRYPTION_KEY` (falling back to `JWT_SECRET` when not set).
- Connector credentials are encrypted before persistence and masked (`***`) on every API read path; plaintext credentials are no longer returned or audit-logged.
- Added `health_check` to the `AutomationProviderAdapter` contract. Implemented for `console` (always healthy) and `smtp` (connects, STARTTLS, and logs in). Added `POST /api/v1/automation/connectors/{config_id}/health-check` with a `503` response on failure and audit logging of both success and failure.
- Added delivery reconciliation: `reconcile_automation_deliveries` marks long-dispatched `console` deliveries as `reconciled`, records `reconciled_at`, and audits the action. Added `reconcile_automation_deliveries_task` wired into the Celery beat schedule to run daily.
- Added `reconciled` and `reconciled_at` columns to `automation_deliveries` via migration `0053_automation_delivery_reconciliation`.
- Added regression tests verifying credential encryption at rest, API-level credential masking, connector health-check success/failure paths, and delivery reconciliation via both the service routine and the Celery task.

## 2026-07-24 — Authority appointment reminders v12.8.5

- Added `appointment.reminder` to `AUTOMATION_EVENT_TYPES`.
- Added `scan_appointment_reminders` service routine in `app/services/authority_appointments.py` that finds scheduled appointments occurring within the next 24 hours and emits one `appointment.reminder` automation event per appointment when the linked application's lead is associated with an active corporate mobility case.
- Added `app/tasks/authority_appointment_tasks.py` with `appointment_reminder_task` and wired it into the Celery beat schedule to run every hour.
- Reminder events are idempotent per appointment per UTC day, include authority name, appointment type, scheduled time, location, and reference number, and flow through the same account-scoped rule matching, human review, retry, and delivery controls as other automation events.
- Added regression tests covering upcoming-appointment event creation, idempotency, outside-window skipping, non-scheduled status skipping, and omission without a corporate case.
- No database migration is required; the task reuses the `AuthorityAppointment` table from v12.5 and the `AutomationEvent` table from v12.3.

## 2026-07-24 — External agency SLA tracking and client portal visibility v12.8.6

- Added `sla_due_hours` to `ExternalAgency` and `sla_due_at`, `sla_status`, and `sla_breached_at` to `ExternalAgencyAssignment` via migration `0052_external_agency_assignment_sla`.
- New assignments inherit their agency's `sla_due_hours` and start with `sla_status = on_track`.
- Added `evaluate_assignment_sla` and `scan_assignment_sla_evaluations` routines that compute SLA status (`on_track`, `due_soon`, `breached`, `completed`) based on the assignment's current state and due timestamp.
- Added `app/tasks/external_agency_sla_tasks.py` with `evaluate_external_agency_assignment_sla_task` and wired it into the Celery beat schedule to run hourly.
- Completing an assignment after its due date records `sla_status = breached`; completing before the due date or cancelling records `sla_status = completed`.
- Extended the client portal dashboard's external agency assignment projection to expose `sla_due_at`, `sla_status`, and `sla_breached_at`.
- Added regression tests for SLA defaults, breach/completed states, the SLA evaluation scan, and portal exposure.

## 2026-07-24 — Client portal agency workflow visibility v12.8.4

- Extended the client portal dashboard (`GET /api/v1/public/client-portal/dashboard`) to expose authority appointments, agency submissions, external agency assignments, and authority checklist items for the granted lead.
- Portal-safe projections omit internal notes, actor identities, audit fields, and contact details. Only status, authority/agency names, reference numbers, scheduled/submitted/handoff/completed timestamps, and checklist item labels/categories/status are returned.
- The dashboard now supports leads with multiple applications by aggregating agency workflow data across all of the lead's applications.
- Added regression test verifying that appointments, submissions, assignments, and checklist items appear in the dashboard and that internal fields remain hidden.
- No database migration is required; the slice reuses the existing client portal, appointment, submission, assignment, and checklist tables.

## 2026-07-24 — Scheduled authority checklist reminders v12.8.3

- Added `scan_checklist_reminders` service routine that finds every application with at least one pending authority checklist item and emits one `authority_checklist.reminder` automation event per pending item when the application's lead is linked to an active corporate case.
- Added `app/tasks/authority_checklist_tasks.py` with `scan_checklist_reminders_task` and wired it into the Celery beat schedule to run once per day.
- Reminder events remain idempotent per checklist item per UTC day, so repeated daily scans never duplicate events.
- Added regression tests for the scan routine: pending items create events, completed items are skipped, and items without a corporate case are omitted.
- No database migration is required; the task reuses the `ApplicationAuthorityChecklistItem` table from v12.8 and the `AutomationEvent` table from v12.3.

## 2026-07-24 — Authority checklist reminders and blocking gates v12.8.2

- Added `authority_checklist.reminder` to `AUTOMATION_EVENT_TYPES` so pending checklist items can trigger governed reminder deliveries.
- Added a blocking gate in agency submission creation: `POST /api/v1/agency-submissions` now returns `409` when any required checklist item for the target authority is still `pending`.
- Required items marked `completed` or `not_applicable` satisfy the gate; optional pending items do not block submission.
- Added `POST /api/v1/applications/{application_id}/authority-checklist/reminders` to emit one `authority_checklist.reminder` automation event per pending checklist item when the application's lead is linked to an active corporate mobility case.
- Reminder events are idempotent per item per UTC day, include the item key/label, authority name, required flag, and case context, and flow through the same rule-matching, review, and delivery controls as other automation events.
- Added regression tests for the blocking gate and reminder event creation/omission.
- No database migration is required; the slice reuses the `ApplicationAuthorityChecklistItem` table from v12.8 and the `AutomationEvent` table from v12.3.

## 2026-07-24 — External agency automation bridge v12.8.1

- Extended `AUTOMATION_EVENT_TYPES` to include `external_agency_assignment.status_changed`.
- Extended `APPLICATION_EVENT_TYPES` in `app/services/automation_bridge.py` to bridge external agency assignment status changes into the governed automation outbox.
- `app/services/external_agencies.py` now emits an `external_agency_assignment.status_changed` automation event after an assignment status transition when the application's lead is linked to an active corporate mobility case.
- Event payloads include the `application_id`, `lead_id`, `lead_name`, `case_reference`, and new `status`, scoped by the linked corporate account and case.
- Added a regression test verifying that an external agency assignment status change creates the corresponding automation event when a corporate link exists.
- No database migration is required; the bridge reuses the existing `AutomationEvent` and `CorporateMobilityCase` tables from v12.3 and the `ExternalAgencyAssignment` table from v12.7.

## 2026-07-24 — Authority submission checklist v12.8

- Added `AuthorityChecklistTemplate` and `ApplicationAuthorityChecklistItem` tables with migration `0051_authority_submission_checklist`.
- Added authority checklist template CRUD and template-apply endpoints under `/api/v1/authority-checklist-templates`.
- Added application checklist item CRUD, status, and delete endpoints under `/api/v1/application-authority-checklist-items` and `/api/v1/applications/{application_id}/authority-checklist`.
- Enforced business rules: template categories are `document`, `fee`, `form`, or `step`; applying a template is idempotent; item statuses are `pending`, `completed`, or `not_applicable`.
- Every template creation, item creation, status change, and deletion records an `AuditLog` event with before/after state.
- Advanced the migration head to `0051_authority_submission_checklist`.

## 2026-07-24 — External agency assignment tracking v12.7

- Added `ExternalAgency` registry and `ExternalAgencyAssignment` tables with migration `0050_external_agency_assignment`.
- Added external agency CRUD and status endpoints under `/api/v1/external-agencies`.
- Added assignment CRUD and lifecycle endpoints under `/api/v1/external-agency-assignments` and `/api/v1/applications/{application_id}/external-agency-assignments`.
- Enforced business rules: only active agencies can receive assignments; only one active assignment per application; forward-only status transitions `assigned → in_progress → handed_off → completed/cancelled`; terminal states are immutable.
- Recorded `handoff_at` and `completed_at` timestamps automatically when assignments reach those statuses.
- Every creation and status change records an `AuditLog` event with before/after state.
- Advanced the migration head to `0050_external_agency_assignment`.

## 2026-07-24 — Application status automation bridge v12.6.1

- Extended `AUTOMATION_EVENT_TYPES` to include `appointment.status_changed` and `submission.status_changed`.
- Added `app/services/automation_bridge.py` to bridge individual application-level status changes into the governed corporate automation outbox when the application's lead is linked to an active corporate mobility case.
- Authority appointment status changes now emit `appointment.status_changed` automation events.
- Agency submission status changes now emit `submission.status_changed` automation events.
- When no active corporate case is linked to the application's lead, the status change still completes but no automation event is created.
- Added regression tests verifying event creation when a corporate link exists and omission when it does not.

## 2026-07-24 — Agency submission tracking v12.6

- Added `AgencySubmission` model linked to `applications` with indexed `application_id`, `submission_channel`, `submitted_at`, `status`, and audit actor/timestamp columns.
- Added Alembic migration `0049_agency_submission_tracking` to create the table and indexes.
- Added submission CRUD and status-lifecycle endpoints under `/api/v1/agency-submissions`:
  - `POST /api/v1/agency-submissions`
  - `GET /api/v1/agency-submissions`
  - `GET /api/v1/agency-submissions/{submission_id}`
  - `POST /api/v1/agency-submissions/{submission_id}/status`
- Enforced business rules: valid submission channels (`online`, `in_person`, `courier`, `agency`); initial status `submitted`; forward-only transitions `submitted → acknowledged → under_review → decision_received/returned`; terminal states are immutable.
- Every creation and status change records an `AuditLog` event with before/after state.
- Advanced the migration head to `0049_agency_submission_tracking`.

## 2026-07-24 — Authority appointment tracking v12.5

- Added `AuthorityAppointment` model linked to `applications` with indexed `application_id`, `appointment_type`, `scheduled_at`, `status`, and audit actor/timestamp columns.
- Added Alembic migration `0048_authority_appointment_tracking` to create the table and indexes.
- Added appointment CRUD and status-lifecycle endpoints under `/api/v1/authority-appointments`:
  - `POST /api/v1/authority-appointments`
  - `GET /api/v1/authority-appointments`
  - `GET /api/v1/authority-appointments/{appointment_id}`
  - `POST /api/v1/authority-appointments/{appointment_id}/status`
- Enforced business rules: valid appointment types (`biometric`, `interview`, `document_submission`, `other`); initial status `scheduled`; transitions only from `scheduled` to `completed`, `cancelled`, or `no_show`; terminal states are immutable.
- Every creation and status change records an `AuditLog` event with before/after state.
- Advanced the migration head to `0048_authority_appointment_tracking`.

## 2026-07-24 — Credential-backed automation connectors v12.4

- Added `AutomationConnectorConfig` and linked deliveries to an active account/channel connector config, with `next_attempt_at` for scheduled retry.
- Added abstract `AutomationProviderAdapter` interface plus `console` (local/test) and `smtp` (STARTTLS email) adapters.
- Added connector config CRUD endpoints and audit:
  - `POST /api/v1/automation/connectors`
  - `GET /api/v1/automation/connectors`
  - `POST /api/v1/automation/connectors/{config_id}/status`
- Added per-delivery dispatch endpoint `POST /api/v1/automation/deliveries/{delivery_id}/dispatch` with 3-attempt exponential backoff (60s, 300s, 900s) and audit.
- Added `dispatch_automation_deliveries_task` Celery task and a 60-second beat schedule to process due `ready` and `retry` deliveries.
- Fixed the v12.4 migration (`0047_automation_connector_config`) to use SQLite-compatible `batch_alter_table` for foreign-key and index changes.
- Advanced the migration head to `0047_automation_connector_config`. Provider health checks, delivery reconciliation, and encrypted credential storage remain future hardening.

## 2026-07-23 — Governed automation foundation v12.3

- Added account-scoped automation rules, an idempotent corporate case-event ledger, and a durable email, messaging, calendar, and CRM delivery outbox.
- Wired case creation and status changes, compliance creation and resolution, and relocation-task transitions into the event ledger in the same transaction as each source mutation.
- Added tenant-isolated rule matching, minimized payloads, independent external-delivery review, pause/reactivation controls, dispatch-receipt recording, and complete audit events.
- Added the Automation Hub for rule configuration, review decisions, event visibility, and outbox readiness.
- Advanced the migration head to `0046_governed_automation_outbox`. Live credential-backed provider adapters, retry/dead-letter workers, and reconciliation remain the next automation slice.

## 2026-07-23 — Versioned public and partner APIs v12.2

- Added unauthenticated, data-free public discovery endpoints under `/api/public/v1` and account-scoped partner resources under `/api/partner/v1`.
- Added expiring and revocable partner API credentials with explicit read scopes, one-time raw-key delivery, SHA-256 digest persistence, and active-account enforcement.
- Added stable minimized projections for corporate-account metadata, paginated mobility cases, and paginated compliance events without exposing internal records or caller-selectable tenant identifiers.
- Added contract-version, no-store, pagination, authentication, scope, revocation, expiry, suspended-account, audit, and cross-tenant regression coverage.
- Advanced the migration head to `0045_partner_api_credentials` and marked the Phase 12 public/partner API contract item complete.

## 2026-07-23 — Employer and partner portal tenancy v12.1

- Added a dedicated employer and authorized-partner workspace with corporate case, relocation-task, and compliance visibility.
- Added expiring, revocable grants whose authorization scope is derived from exactly one stored corporate-account relationship and recorded employer or partner audience.
- Persisted only SHA-256 token digests and kept external tenant access separate from internal RBAC and individual client access.
- Minimized the external projection by excluding contact data, internal notes, lead identifiers, evidence, reviews, truth claims, audit records, and operator actions.
- Added a two-tenant leakage regression test plus authentication, expiry, revocation, and audit coverage.
- Advanced the migration head to `0044_ecosystem_portal_tenancy` and marked the employer/partner tenant-isolation roadmap item complete.

## 2026-07-23 — Client portal foundation v12.0

- Started Phase 12 with a dedicated responsive client portal showing a deliberately client-safe case status, next action, milestones, and document metadata.
- Added revocable, expiring, lead-scoped access grants whose raw bearer tokens are never persisted; only SHA-256 token digests are stored.
- Added operator issuance, grant listing, and revocation endpoints plus a token-scoped public dashboard, with audit events for creation, access, expiry, and revocation.
- Disabled the legacy public email-or-phone case lookup and secured the legacy return route with the same portal token boundary.
- Integrated initial portal issuance with public intake, added link creation to the lead workspace, hid internal agent controls on client routes, and added focused security and migration coverage.
- Advanced the migration head to `0043_client_portal_foundation`; native/mobile access and the remaining Phase 12 ecosystem scope are still pending.

## 2026-07-23 — Austria program publication v11.12

- Enforced independent reviewer separation for mobility-pathway publication and added regression coverage across all affected pathway consumers.
- Independently published Austria Self-employed Key Worker pathway version `b62fb1e2-29d8-45cf-9510-1e269f0ea8d2`.
- Created investor-entrepreneur program `dbd59207-a870-4388-a5bb-131521d25a85` from the published pathway, eligible official source, exact immutable snapshot, and four active verified rules.
- Independently published program version `11790441-bd7e-4b3b-b1c5-6aa42909fb05`; Austria now reports `published` onboarding readiness with zero blockers.
- Marked Phase 11 complete while leaving broader jurisdiction and treaty evidence onboarding as ongoing operational expansion.

## 2026-07-23 — Initial-rule assertion publication v10.22.28

- Published exactly the 17 independently approved assertions after the user's separate authorization; Senegal remained pending and detected-change reviews were not modified.
- Created 17 active, source-pinned verified rules under publisher `bennet-coverage-publisher`.
- Confirmed that all 17 jurisdictions independently became coverage-ready, moving readiness from 65/243 to 82/243.
- Preserved the global-coverage block because 161 required jurisdictions remain incomplete.
- Added a durable publication receipt with every jurisdiction and verified-rule identifier.

## 2026-07-23 — Initial-rule assertion approval v10.22.27

- Recorded the user's explicit approval of the recommended 17 assertions under independent reviewer `bennet-initial-rule-reviewer`.
- Left Senegal pending without a review decision because its live official endpoint remains unavailable.
- Preserved the separate publication gate at that checkpoint. The later v10.22.28 publication created the 17 verified rules and moved readiness to 82/243.

## 2026-07-23 — Initial-rule assertion review packet v10.22.26

- Prepared 18 human-edited initial-rule assertions pinned to the approved coverage items, official sources, and immutable baseline snapshots from v10.22.20 through v10.22.24.
- Replaced unusable assistant wording, including navigation-heavy Tanzania and insufficient Chile drafts, with narrow substantive statements from the stored evidence.
- Submitted every assertion as `pending_review` under a distinct proposer identity with confidence 0.90; no approval, publication, verified rule, or readiness claim was created.
- Added a decision-ready human review packet recommending approval of 17 assertions and a hold on Senegal until its live official endpoint recovers or is replaced.

## 2026-07-23 — Coverage independent review v10.22.25

- Completed independent review of 20 pending immigration-authority assessments and 20 pending primary-source certifications from evidence batches v10.22.20 through v10.22.24.
- Approved all 20 narrow authority relationships and 18 source certifications using a reviewer identity different from every proposer.
- Rejected Peru and Qatar source certifications because their pinned extracts were not assertion-grade; narrower official sources and fresh independent certification remain required.
- Recorded Senegal's current official-endpoint failure as a monitoring caveat while preserving its valid immutable July 18 snapshot and narrow entry-visa scope.
- Cleared both pending-review queues and moved 18 items to baseline-ready without proposing or publishing a rule. Coverage readiness remains 65/243.

## 2026-07-23 — Tax-residency and treaty intelligence v11.11

- Added source-pinned bilateral treaty evidence proposals restricted to active tax-domain official sources and exact content-addressed snapshots.
- Added independent treaty publication decisions, effective-period enforcement, jurisdiction-pair matching, audit history, and exclusion of unpublished evidence from client work.
- Added immutable client tax-residency issue maps across dated facts, client-owned evidence, treaty grounding, specialist coordination, domestic residence, entity/permanent-establishment, employment/payroll, and filing sequence.
- Added prohibited-conduct escalation, independent specialist review, read-only enforcement, migration `0042_tax_residency_treaty`, and focused transaction tests.
- Added the `/tax-residency` Tax & Treaty workspace with a compact assessment surface, issue matrix, workstreams, treaty proposal desk, and evidence publication queue.

## 2026-07-23 — HNWI and family-office mobility v11.10

- Added immutable principal-linked family-office readiness assessments across identity/family, wealth evidence, ownership/control, governance/specialists, and mobility-route workstreams.
- Added client-owned document enforcement, source-of-wealth and source-of-funds states, entity and UBO inventories, PEP/sanctions posture, adviser coverage, succession continuity, and banking-readiness controls.
- Added independently published pathway and investment-program grounding without presenting capital, wealth, or residence outcomes as guaranteed.
- Added readiness caps and operational blockers for concealment, evasion, sanctions circumvention, false documents, sham structures, and ownership misrepresentation.
- Added independent assessment review, actor attribution, audit events, read-only enforcement, migration `0041_family_office_mobility`, focused tests, and the `/family-office` operator workspace.

## 2026-07-23 — Independent investment-rule review v11.9

- Added immutable rule proposals pinned to a draft pathway, eligible official source, and exact content-addressed snapshot.
- Added independent approve/reject decisions with actor attribution, audit history, duplicate-rule protection, and read-only role enforcement.
- Approval creates active verified rules and a replacement pathway draft while superseding the unverified draft; it never publishes a pathway or investment program.
- Added the Investment Programs review surface for inspecting proposed statements and provenance, recording a reason, and making the separate human decision.
- Added migration `0040_investment_rule_review`, focused transaction tests, and an Austria rule proposal based on the v11.8 evidence pack. Independent review subsequently approved four source-pinned rules and created a replacement pathway draft without publishing it.

## 2026-07-23 — Austria investment onboarding tranche v11.8

- Onboarded the Austrian Federal Government migration page for Self-employed Key Workers as an investment-domain official source and active controlled monitor.
- Captured an HTTPS 200 baseline with immutable SHA-256 `905a6e47c821be64863efc9037e99b611e31d0d797a6b6799d1fc8b2e5f8ba38`.
- Added a fail-closed evidence pack and review-pending Austria pathway draft without publishing an eligibility or approval claim. Independent rule review subsequently activated four pinned rules and created a replacement draft; pathway publication remains separate.
- Added evidence-pack regression tests and exposed the active verified-rule gate in jurisdiction onboarding readiness.

## 2026-07-23 — Investment program onboarding readiness v11.7

- Added jurisdiction-level readiness across eligible official sources, immutable snapshots, published pathways, program drafts, and independent publication.
- Added explicit blocker and next-action reporting to the Investment Programs workspace.
- Prevented visa-domain and other unrelated sources from grounding investment-mobility programs.
- Kept jurisdiction program onboarding incomplete until actual source-grounded records pass independent review; no sample program is presented as verified production data.

## 2026-07-23 — Investment mobility suitability v11.6

- Added client-specific comparison across independently published investment-program versions.
- Added transparent capital-coverage, controlled-evidence, family-fit, and risk-alignment components with explicit blockers and next actions.
- Added fail-closed currency handling, client-owned document validation, source-of-funds and capital-preservation constraints, and prohibited-conduct caps.
- Added immutable pending-review assessments, independent review, audit records, role enforcement, and exact program/pathway/source/snapshot provenance.
- Added migration `0039_investment_suitability`, focused tests, and the `/investment-suitability` workspace.

## 2026-07-23 — Governed investment program catalogue v11.5

- Added residence-by-investment, citizenship-by-investment, and investor-entrepreneur catalogue records with immutable versions and explicit thresholds, options, holding/presence context, family scope, due diligence, fees, benefits, and risks.
- Required every program version to reference an active matching-country pathway, its published version, an active official source, and a content-addressed source snapshot.
- Added independent publication, previous-version supersession, actor attribution, audit records, role enforcement, and rejection of guaranteed authority-outcome claims.
- Connected independently published programs to Business & Wealth advisory strategy grounding and added the `/investment-mobility` operator workspace.
- Added Alembic migration `0038_investment_programs` and focused tests covering transaction boundaries, source consistency, publication separation, version history, role restrictions, and advisory integration.

## 2026-07-23 — Business and Wealth advisory v11.4

- Added a narrative Business & Wealth Mobility assessment that ranks three commercially distinct strategy options across startup, expansion, founder, investment, family-office, tax-residency, and asset/family intentions.
- Added a lightweight `POST /api/v1/business-mobility-advisory/advise` endpoint that returns a single recommended solution with a 0–100 success meter, alternative options, critical factors, and concrete next actions; it uses the configured LLM when available and falls back to deterministic scoring when no LLM is configured or when risk flags are present.
- Added transparent feasibility scoring across information completeness, controlled evidence, commercial fit, and published-pathway grounding; the score is explicitly not an approval probability or professional opinion.
- Added pathway grounding, evidence ownership checks, risk disclosures, hard blockers, lawful remediation, specialist escalation, immutable assessment records, audit events, and independent human review.
- Added Alembic migration `0037_business_advisory`, focused transaction and boundary tests, a named navigation destination, and a responsive Business & Wealth Advisor workspace.
- Deliberately blocked operational guidance for concealment, false documents, sham arrangements, sanctions avoidance, tax evasion, or material misrepresentation while preserving commercially useful lawful alternatives.

## 2026-07-23 — Entrepreneur and startup dossiers v11.3

- Added entrepreneur/startup case type support and one review-gated venture dossier per case.
- Added founder, destination, stage, sector, incorporation, role, and business-model consistency controls.
- Added venture evidence items with paired amount/currency declarations and optional founder-owned controlled-document links.
- Added explicit evidence-completeness submission and append-only decisions with independent-reviewer enforcement.
- Added Alembic migration `0036_entrepreneur_ventures`, focused tests, and a founder dossier surface in Corporate Mobility.
- Deliberately excluded eligibility, investment qualification, funding verification, program recommendation, and filing automation.

## 2026-07-23 — Relocation task orchestration v11.2

- Added case-scoped relocation tasks with categories, accountable owner roles, due dates, and explicit same-case dependencies.
- Added controlled task transitions, dependency completion gates, required blocking/cancellation notes, and immutable terminal records.
- Added human-review-required completion submission and append-only decisions with enforced reviewer separation.
- Added Alembic migration `0035_relocation_tasks`, focused lifecycle tests, and a relocation task board in the Corporate Mobility case control plane.
- Preserved source, evidence, consent, role, application, and authority-decision controls; tasks coordinate human work and do not perform regulated actions.

## 2026-07-23 — Corporate mobility relationships v11.1

- Added account-scoped sponsor entities and audited case-sponsor assignments with cross-account and active-status controls.
- Added audited dependant links backed by existing lead profiles, including duplicate prevention and terminal removal history.
- Added human-review-required compliance events with accountable completion or reasoned waiver and immutable terminal states.
- Added Alembic migration `0034_corp_relationships`, focused API tests, and a Corporate Mobility case control plane for sponsors, dependants, and deadlines.
- Preserved Truth Engine, consent, evidence, review, role, application, and authority-decision boundaries; no regulated decision or filing is automated.

## 2026-07-23 — Corporate mobility foundation v11.0

- Added governed corporate accounts and account-scoped corporate mobility cases with optional employee-lead links.
- Added explicit case state transitions, immutable closed records, mandatory human-review flags, authenticated audit history, date-order validation, and read-only mutation protection.
- Added Alembic migration `0033_corporate_mobility_foundation` and focused API coverage.
- Added the Corporate Mobility operator workspace for employer onboarding, employee linking, relocation routes, compliance dates, and controlled status changes.
- Preserved the existing Truth Engine, source provenance, review, application, and authority-decision boundaries; no eligibility or sponsorship conclusion is generated by this feature.

## 2026-07-19 — Workspace navigation and System Pulse v10.23.4

- Replaced the tilted dashboard status cards and connector lines with one aligned System Pulse panel.
- Added persistent destination names to the desktop workspace rail and aligned every label with its page title.
- Preserved compact icon navigation at narrower widths with accessible hover and keyboard-focus labels.
- Warmed light-mode surfaces from neutral white to a layered ivory palette while retaining the deep-indigo identity and semantic status colors.
- Verified the production Next.js build, TypeScript checks, and static generation for all 21 frontend routes.

## 2026-07-19 — Timeless workspace rail and theme v10.23.3

- Removed the expanding Mobility, Operations, and Engagement sidebar cards.
- Added a compact fixed workspace rail with custom icons, direct navigation, active markers, accessible labels, tooltips, theme control, and backend status.
- Replaced the reference-adjacent olive palette with an original neutral-stone and deep-indigo system for both light and dark themes.
- Refined shared surfaces, typography, buttons, empty states, focus treatment, and motion while reserving green for semantic success.
- Verified the production build and HTTP 200 responses for the home, Pathways, and Global Intelligence routes without Docker runtime errors.

## 2026-07-19 — Next.js cache-isolation hotfix v10.23.2

- Fixed the Docker development runtime error caused by a host production build replacing chunks in the shared `.next` directory.
- Configured an environment-selectable Next.js output directory and assigned Docker development to `.next-docker`.
- Mounted the Docker development cache in an isolated volume and excluded its fallback directory from version control.
- Recreated the web container and verified HTTP 200 responses for the home and Global Intelligence routes before and after a host production build.

## 2026-07-19 — Focused workspace UX v10.23.1

- Reorganized the operations home into Cases, Verification, Intake, and Governance views so only one task context is displayed at a time.
- Split Global Intelligence coverage into Readiness, Evidence, Rules, and Registry workspaces with wired local navigation.
- Converted evidence-batch history into a horizontal review rail and bounded long operational lists inside their workspace.
- Collapsed global evidence filters and grouped sidebar tools into Mobility, Operations, and Engagement sections.
- Removed duplicated active sidebar states and preserved all workflow, review, truth, and publication controls.
- Verified the production Next.js build, TypeScript checks, and static generation for all 21 routes.

## 2026-07-19 — Editorial operator UI v10.23

- Reworked the shared web design system around the supplied nature-led editorial references.
- Added a dark olive navigation rail, calmer off-white content canvas, lime system accents, flatter panels, thinner dividers, and more deliberate typography and spacing.
- Rebuilt the operations dashboard hero as a connected workflow overview with live pipeline, Truth Engine, controlled-agent, backend, and safety-gate context.
- Simplified shared metrics, tables, action queues, status badges, buttons, forms, and responsive navigation without changing their underlying behavior.
- Verified the production Next.js build, TypeScript checks, and static generation for all 21 frontend routes.

## 2026-07-18 — Phase 10B evidence tranche v10.22.24

- Added current official-source evidence for Hungary, Malta, Liechtenstein, Bosnia and Herzegovina, and Albania.
- Verified all five endpoints through the controlled API-container retriever with HTTPS 200 and suitable content-quality scores.
- Excluded Lithuania after a fail-closed HTTP 403 response rather than weakening retrieval controls.
- Submitted an atomic evidence batch containing five pending immigration assessments and five pending primary-source certifications.
- Left all 40 pending decisions across the current 20 jurisdictions for independent reviewers; readiness remains 65/243.

## 2026-07-18 — Phase 10B independent-review handoff v10.22.23

- Consolidated the v10.22.20-v10.22.22 batches into one 15-jurisdiction review queue with immutable JSON and CSV operations receipts.
- Confirmed 15 pending immigration assessments and 15 pending primary-source certifications without creating any review decision.
- Prepared 13 constrained candidate assertion drafts as non-persistent suggestions.
- Identified insufficient current snapshot content for Peru and Qatar and recorded narrower official remediation candidates that pass controlled retrieval and content-quality scoring.
- Preserved all human-review, baseline, assertion, publication, and global-coverage gates; readiness remains 65/243.

## 2026-07-18 — Phase 10B evidence tranche v10.22.22

- Added current official-source evidence for Namibia, Sierra Leone, Somalia, Senegal, and Tanzania.
- Verified all five endpoints through the controlled API-container retriever with HTTPS 200 and usable generic-parser output.
- Kept Senegal's proposal narrowly scoped to the official entry-visa function and flagged broader authority scope for separate evidence and reviewer judgment.
- Submitted an atomic evidence batch containing five pending immigration assessments and five pending primary-source certifications.
- Preserved the independent-review, baseline, assertion, publication, and global-coverage gates; readiness remains 65/243.

## 2026-07-18 — Phase 10B evidence tranche v10.22.21

- Added current official-source evidence for Eswatini, Lesotho, Liberia, Zambia, and Uganda.
- Verified all five endpoints through the controlled API-container retriever with HTTPS 200 and usable generic-parser output.
- Excluded Algeria, The Gambia, and Nigeria after fail-closed transport or HTTP results rather than weakening retrieval controls.
- Submitted an atomic evidence batch containing five pending immigration assessments and five pending primary-source certifications.
- Preserved the independent-review, baseline, assertion, publication, and global-coverage gates; readiness remains 65/243.

## 2026-07-18 — Phase 10B evidence tranche v10.22.20

- Added current official-source evidence for the Republic of Korea, Malaysia, Chile, Peru, and Qatar.
- Verified all five endpoints through the controlled API-container retriever with HTTPS 200 and usable generic-parser output.
- Excluded Thailand, Vietnam, and Mexico after fail-closed probe results rather than weakening transport or content-quality controls.
- Submitted an atomic evidence batch containing five pending immigration assessments and five pending primary-source certifications.
- Preserved the independent-review, baseline, assertion, publication, and global-coverage gates; readiness remains 65/243.

## 2026-07-18 — Authority-decision transactional integrity v1.9.1

- Made application status, mapped lead status and audit note, optional follow-up, and authority-decision audit creation atomic.
- Roll back the complete transition if follow-up construction, audit creation, or the database commit fails.
- Added regression coverage for successful metadata persistence and simulated audit-failure rollback.
- Kept the authority-decision routes and database schema unchanged.

## 2026-07-15 — Supplemental official sources v10.21.2

- Added review-gated `supplemental_<domain>` source certifications without changing the database schema.
- Required an approved primary immigration certification, the same approved primary authority, and an approved immigration relationship before supplemental onboarding.
- Prevented supplemental approvals from superseding existing primary certifications.
- Allowed the freshness gate to use an approved primary or supplemental source while keeping primary authority/source gates primary-only.
- Allowed supplemental batch items to reuse an approved jurisdiction assessment and support baseline plus initial-assertion provenance from the exact supplemental snapshot.
- Added the Canada IRCC visitor-visa supplemental pack and `Submit-SupplementalCoverageSource.ps1` with `-WhatIf` safeguards.
- Updated the Coverage workspace to label pending supplemental certifications correctly and display approved supplemental certifications separately.
- Added focused regression tests and updated `docs/ROADMAP.md`; migration head remains `0032_initial_rule_assertions`.

## 2026-07-15 — Tranche draft handoff UX hotfix v10.21.1

- Fixed the Coverage tranche assistant copy action so it visibly confirms the selected jurisdiction draft.
- Added automatic smooth scrolling to the existing initial-rule assertion form and focus on the title field after copying.
- Added an in-form confirmation notice that the draft remains unsubmitted and requires human editing and independent review.
- Added an explicit `type="button"` guard so the copy action cannot accidentally behave as a form submission control.
- Preserved all v10.21 safety boundaries; no assessments, assertions, publications, snapshots, regulatory changes, or coverage claims are created by copying a draft.
- Updated `docs/ROADMAP.md`; database migration head remains `0032_initial_rule_assertions`.

## 2026-07-15 — Safe coverage tranche assistant v10.21

- Added a feature-flagged, disabled-by-default tranche preparation service and API.
- Added deterministic immutable-snapshot quality scoring and rejection of navigation-heavy or low-information pages.
- Added exact candidate evidence-line extraction and constrained assertion suggestions that are never persisted automatically.
- Added explicit jurisdiction selection and selective baseline queueing; eligible sources outside the selected codes are skipped.
- Added a Coverage workspace assistant with dry-run preparation and a copy-to-existing-assertion-form action.
- Added `Prepare-CoverageTranche.ps1` with `-WhatIf`, default dry-run behavior, explicit apply mode, and optional JSON receipt export.
- Preserved all existing assessment, certification, reviewer, publisher, immutable-snapshot, regulatory-change, pathway, and coverage-claim boundaries.
- Added focused regression tests, operator documentation, environment flags, and an updated `docs/ROADMAP.md`.
- Database migration head remains `0032_initial_rule_assertions`.


## 2026-07-14 — Coverage readiness receipts v10.20

- Added before/after jurisdiction coverage receipts to independently reviewed initial-rule publication.
- Added idempotent read-only reconciliation for already-published assertions without duplicate rules, graph projections, or readiness audits.
- Added audit event `jurisdiction_coverage_readiness_reconciled` with exact evidence-gate posture.
- Added a read-only per-jurisdiction coverage-receipt API and PowerShell helper.
- Reconciled active verified-rule and coverage-ready dashboard counts from the same registry evidence calculation while keeping detected-change counts unchanged.
- Added published-assertion coverage status and remaining-gate visibility in the Coverage workspace.
- Removed preloaded `official.example` evidence JSON and disabled batch submission until a real evidence row is present.
- Added regression coverage for readiness transitions, audit provenance, dashboard counts, read-only receipts, and idempotent publication.
- Updated `docs/ROADMAP.md`; database migration head remains `0032_initial_rule_assertions`.

## 2026-07-14 — Controlled initial verified-rule assertions v10.19

- Added migration `0032_initial_rule_assertions`.
- Added immutable SHA-256-keyed initial rule assertions tied to an approved coverage-batch item and exact baseline snapshot.
- Required approved immigration-rule and primary-source reviews before assertion creation.
- Required a different authenticated reviewer and a separate explicit publication action.
- Published verified rules with `initial_rule_assertion_id` provenance and no fabricated regulatory-change record.
- Extended the regulatory knowledge graph to represent reviewed initial assertions alongside reviewed source changes.
- Kept pathway-impact generation change-event-only and Opportunity Radar change-event-only.
- Added Coverage workspace drafting, review, publication, and immutable assertion history controls.
- Added regression coverage for idempotency, reviewer separation, explicit publication, no-change provenance, graph integrity, migration parity, and API behavior.
- Updated `docs/ROADMAP.md` in the same patch.

## 2026-07-14 — Canonical-source remediation output hotfix v10.18.2

- Fixed `Repair-CoverageSourceCanonicalUrl.ps1` so it never reads expired SQLAlchemy ORM attributes after the database session closes.
- Made the remediation idempotent: a rerun after the earlier post-commit output failure reports `already_corrected=true` without duplicating the audit event.
- Allowed a no-op confirmation after a snapshot exists while still refusing any post-snapshot URL mutation.
- Preserved HTTPS-only, same-host, allowlist, credential, standard-port, immutable-snapshot, review, and coverage-claim boundaries.
- Updated `docs/ROADMAP.md`; database migration head remains `0031_global_coverage_source_onboarding`.

## 2026-07-14 — Austria canonical HTTPS source hotfix v10.18.1

- Corrected the Austria starter-tranche monitor URL from the HTTPS endpoint that redirects to HTTP to the directly reachable canonical HTTPS page.
- Preserved the fail-closed redirect and scheme policy; HTTP retrieval was not enabled.
- Added an audited same-host remediation script for already-onboarded sources, with snapshot, allowlist, credential, and standard-port guards.
- Updated `docs/ROADMAP.md`; database migration head remains `0031_global_coverage_source_onboarding`.

## 2026-07-14 — Controlled coverage baseline capture v10.18

- Added review-gated baseline capture for approved jurisdiction coverage evidence batches.
- Required both an approved immigration-rule assessment and approved primary authority/source certification before a monitor can be queued.
- Added durable pre-created `SourceRetrievalRun(status="queued")` records and exact run-ID handoff to Celery workers.
- Added idempotent protection for existing snapshots and queued/running retrievals, plus deliberate retry visibility for failed runs.
- Reused the existing HTTPS, allowlist, SSRF, redirect, timeout, response-size, parser, immutable snapshot, and regulatory-change controls.
- Added Coverage workspace baseline counts, a **Capture approved baselines** action, API status/queue endpoints, and a PowerShell helper.
- Preserved the rule-publication and global-coverage gates; baseline capture creates evidence only.
- Added regression coverage for independent-review gating, durable queueing, duplicate prevention, exact run reuse, API behavior, and baseline snapshot creation.
- Updated `docs/ROADMAP.md`; database migration head remains `0031_global_coverage_source_onboarding`.

## 2026-07-14 — Official global coverage evidence starter v10.17

- Added a current official-evidence tranche for Austria, Germany, Canada, Australia, and New Zealand.
- Added an offline pack validator that enforces HTTPS provenance, source-domain allowlists, exact jurisdiction/reference alignment, pending-review state, and no-global-coverage safety flags.
- Added a PowerShell submission helper that posts the pack to the existing review-gated evidence-batch API and supports `-WhatIf`.
- Changed combined source-onboarding/assessment rows so the pending immigration assessment is linked to the exact newly onboarded official source.
- Kept every relationship and primary-source certification pending for a different reviewer; the pack creates no approvals, snapshots, verified rules, or global-coverage claim.
- Added regression coverage for pack validation, atomic five-jurisdiction submission, source provenance linkage, idempotency, and unsafe-pack rejection.
- Updated `docs/ROADMAP.md` in the same patch; database migration head remains `0031_global_coverage_source_onboarding`.

## 2026-07-14 — Global coverage source onboarding v10.16

- Added migration `0031_global_coverage_source_onboarding`.
- Extended the existing atomic coverage evidence batch with authority, official-source, and source-monitor onboarding for up to 50 registry jurisdictions.
- Bound jurisdiction identity to the active registry release instead of accepting caller-supplied country names or types.
- Reused the existing HTTPS, standard-port, credential, domain-allowlist, source-ownership, and parser-profile controls.
- Automatically created a pending primary-source certification proposal for each onboarded source.
- Preserved separate-reviewer approval and the global-coverage release gate; onboarding alone never certifies coverage.
- Added immutable authority/source/monitor provenance to each batch item and source-onboarding counts to batch history.
- Added regression coverage for idempotency, complete rollback, source conflicts, reviewer separation, PostgreSQL migration compilation, and frontend production build.
- Updated `docs/ROADMAP.md` in the same patch.

## 2026-07-14 — PostgreSQL migration identifier hotfix v10.15.1

- Fixed migration `0030_global_coverage_evidence_batches` so convention-generated index names are deterministically truncated within PostgreSQL's 63-character identifier limit.
- Added an offline PostgreSQL migration-compilation regression test to prevent SQLite-only migration validation from missing identifier-length failures.
- Kept the migration revision and database head unchanged; failed PostgreSQL attempts remain safely at `0029` because migration DDL is transactional.
- Updated `docs/ROADMAP.md` and included it in the hotfix patch.

## 2026-07-14 — Global coverage evidence operations v10.15

- Added migration `0030_global_coverage_evidence_batches` with immutable batch and item provenance.
- Added a prioritized Phase 10B worklist filterable by gap and region without interpreting registry inclusion as immigration coverage.
- Added atomic, idempotent evidence-batch submission for up to 50 jurisdictions.
- Batch submission can create pending immigration-rule assessments and primary authority/source certifications from existing reviewed evidence relationships.
- Preserved separate-reviewer requirements; batch submitters cannot approve their own proposals.
- Added derived batch progress across pending, approved, rejected, superseded, and missing linked review records.
- Added audit event `jurisdiction_coverage_evidence_batch_submitted` and operator controls in the Global Intelligence Coverage workspace.
- Kept the global-coverage release gate blocked until every required jurisdiction passes authority, source, freshness, verified-rule, and immigration-rule assessment checks.
- Added regression coverage for atomic rollback, idempotency, reviewer gating, worklist prioritization, API routing, and migration metadata parity.

## 2026-07-14 — Immutable multi-year mobility scenarios v10.14

- Added migration `0029_multi_year_mobility_scenarios` with immutable scenario and stage ledgers.
- Added human-confirmed transitions across study, graduate rights, work permits, skilled migration, settlement, permanent residence, and citizenship review.
- Added dated multi-country planning from exact published pathway versions, verified rules, and source snapshots.
- Added strict explicit-acceptance, current-consent, human-review, and reviewed-evidence gates.
- Added reviewed regulatory-impact recalculation that creates a new scenario version while preserving the original scenario and dates unchanged.
- Added non-guarantee and rule-reverification boundaries to every stage and retained the Phase 10B global-coverage gate.
- Added the Timelines scenario builder, immutable version history, evidence badges, and recalculation controls.
- Added regression coverage for idempotency, multi-country dates, evidence gates, audit events, and source-record immutability.

## 2026-07-14 — Reviewed global country ranking v10.13

- Added migration `0028_country_ranking_assessments` and immutable, content-addressed ranking history tied to exact profile and published pathway versions.
- Added explicit user attestation and operator notes for every generated cross-country assessment.
- Ranked countries deterministically from profile fit, confidence, and reviewed pathway risk without treating the score as a recommendation or eligibility prediction.
- Added country-level costs, route alternatives, evidence gaps, coverage posture, trade-offs, and uncertainty explanations.
- Added reviewed permanent-residence and citizenship dependency parsing from pathway metadata; missing fields remain explicit and are never inferred.
- Preserved the Phase 10B release gate by labelling incomplete results as `reviewed_published_catalogue_only` and blocking complete-global-ranking claims.
- Added Planning workspace country-ranking controls, immutable history metrics, and responsive country cards.
- Added regression coverage for cross-country ranking, long-term dependency provenance, acceptance gating, idempotency, audit events, and global-coverage boundaries.

## 2026-07-14 — Explicit reassessment acceptance controls v10.12

- Added migration `0027_reassessment_acceptances` and an immutable acceptance ledger tied to the exact baseline comparison.
- Blocked ordinary reassessment when a newer profile or reviewed regulatory replacement would change pinned inputs.
- Added separate record-and-execute actions so recording acceptance never changes assessments or timelines by itself.
- Recomputed only against the accepted profile and exact pinned/replacement pathway versions, preserving all historical comparison and timeline rows.
- Added user attestation, operator notes, idempotent acceptance keys, consumption provenance, and dedicated audit events.
- Added the Mobility Planning acceptance queue, accepted-version controls, and immutable acceptance history.
- Added regression coverage for profile-version gating, regulatory-version gating, idempotency, and source-record immutability.

## 2026-07-14 — Global intelligence evidence filters v10.11

- Added API filters for source freshness, jurisdiction coverage, regulatory authority, evidence confidence, materiality, and review state.
- Added source-monitor freshness, registry coverage posture, authority provenance, and verified-rule/classification-proposal confidence to every dashboard change record.
- Applied the selected evidence scope consistently to metrics, change feeds, country heatmap totals, and the human-published-only Opportunity Radar.
- Added filter option counts, matched-versus-available evidence totals, clear-filter controls, and responsive operator UI.
- Added regression coverage for combined filters, stale/fresh monitoring, coverage posture, authority scoping, confidence provenance, and invalid filter rejection.
- Kept the database migration head at `0026_document_access_grants`; this increment is query and presentation logic only.

## 2026-07-14 — Signed document access v9.5 / product continuation v10.10

- Added migration `0026_document_access_grants` and a short-lived, use-limited access ledger.
- Added HMAC-signed tokens bound to actor, role, lead, document, purpose, and expiry, with raw tokens returned only once and stored only as SHA-256 hashes.
- Added local/MinIO content access with immutable hash and size validation, revocation, expiry reconciliation, and fail-closed denial for missing or altered objects.
- Removed raw storage keys from operator-facing document API payloads and disabled direct object URLs.
- Added strict production posture checks for MinIO TLS, non-default credentials, private pre-provisioned buckets, signing secrets, retention, backup, and recovery records.
- Added Document Intelligence secure-download controls, active-grant metrics, access ledger, and audit provenance without changing document verification state.
- Added regression coverage for one-use consumption, delegated role scope, expiry, revocation, tamper denial, public policy detection, and audit events.

## v6.4 - Next.js Operator Workspace Completion

- Added In-House Consultant Agent (`agents/role_cards/inhouse_consultant.md`, `app/services/inhouse_consultant.py`, `app/routers/agent_chat.py`) with LLM-powered routing and deterministic fallback.
- Added floating chat widget (`apps/web/components/AgentChatWidget.tsx`) integrated into the root layout.
- Added Next.js Agent Console (`apps/web/app/agents/console/page.tsx`) for single and batch controlled-agent runs.
- Added Next.js Agent Review Queue (`apps/web/app/agents/review/page.tsx`) with filters, bulk actions, and run detail view.
- Added `GET /api/v1/agent-output-reviews/runs/{run_id}` endpoint and audit history schema.
- Enriched `GET /api/v1/leads/{id}/detail` with documents and applications; redesigned Next.js lead detail page with tabs, profiles, source references, and actions.
- Added Next.js Client Communication Drafts workspace (`apps/web/app/communications/*`) backed by existing `/api/v1/client-communications` endpoints.
- Updated sidebar navigation with active states for Agents and Communications.

## v6.3 - GitHub Release Prep

- Added `scripts/check_github_release_ready.py`.
- Added release-readiness checks for required tags, clean Git state, release notes, and the v6.2 archive manifest.
- Added `docs/RELEASE_NOTES_MVP_V6_2.md`.
- Added `docs/GITHUB_RELEASE_PREP_V6_3.md`.
- Included the GitHub release readiness checker in local compile coverage.

## v6.2 - MVP Release Archive Export

- Added `scripts/export_mvp_release_archive.py`.
- Added ignored release archive zip output under `release_exports/`.
- Added archive manifest metadata with bundle status, safety rules, tags, and included files.
- Added tests for archive path handling, manifest content, and zip contents.
- Added `docs/MVP_RELEASE_ARCHIVE_V6_2.md`.
- Included the archive exporter in local compile coverage.

## v6.1 - MVP Release Bundle Export

- Added `scripts/export_mvp_release_bundle.py`.
- Added ignored `release_exports/` output storage.
- Added bundle tests for Markdown content, JSON structure, and ignored export paths.
- Added `docs/MVP_RELEASE_BUNDLE_EXPORT_V6_1.md`.
- Included the bundle exporter in local compile coverage.

## v6.0 - MVP Release Hardening

- Added `scripts/check_mvp_release.py`.
- Added release-hardening tests for git cleanliness, required demo tags, demo release status, and quality status.
- Added `docs/MVP_RELEASE_HARDENING_V6_0.md`.
- Included the MVP release checker in local compile coverage.

## v5.9 - Demo Release Status Sync

- Updated `scripts/check_demo_release.py` to validate the v5.8 release state.
- Added release coverage for v5.6 duplicate-output guard, v5.7 demo UX polish, and v5.8 export cleanup.
- Added export-cleanup checks for ignored local demo exports and local production env files.
- Added `docs/DEMO_RELEASE_STATUS_V5_9.md`.

## v5.5 - Demo Release Checkpoint

- Added `scripts/check_demo_release.py`.
- Added release tests for demo readiness, release artifacts, and safety state.
- Added `docs/DEMO_RELEASE_V5_5.md`.
- Added this changelog.
- Included the release checker in local compile coverage.

## v5.4 - Demo Readiness Banner

- Added readiness banner to `/admin/demo`.
- Added readiness banner to `/admin/v2`.
- Extended demo navigation JSON with readiness metadata.

## v5.3 - Demo Navigation Polish

- Added `/admin/demo`.
- Added `/api/v1/admin-demo/navigation`.
- Added a local demo command center with primary workflow links.

## v5.2 - Demo Snapshot Export

- Added JSON and Markdown demo snapshot export.
- Captured lead, agent, client draft, audit, URL, and safety state.

## v5.1 - Demo Release Runbook

- Added local demo runbook helper.
- Documented the safe agent-to-client-draft walkthrough.

## 2026-07-14 — Pathway regulatory impact links v10.6

- Added migration `0022_pathway_regulatory_impacts` and immutable impact ledger.
- Linked human-published graph/rule publication, supersession, and retirement
  events to exact affected published pathway versions.
- Added a review lifecycle that cannot mutate pathway versions, comparisons,
  timelines, or client conclusions.
- Added pathway impact APIs, operator workspace controls, audit events, and
  regression coverage for pinned-record immutability and idempotent graph sync.

## 2026-07-14 — Document expiry monitoring v9.2 / product continuation v10.7

- Added migration `0023_document_expiry_reminders` and the immutable reminder ledger.
- Added deterministic 90, 30, 7-day, and expired urgency scans with unique keys.
- Added stale-date and increasing-urgency supersession while preserving task history.
- Added six-hour Celery Beat scanning, lead-scoped manual scans, and restricted APIs.
- Added human acknowledgement, resolution, and dismissal with mandatory notes and audit events.
- Added the Document Intelligence expiry queue and explicit zero-external-message controls.
- Added regression coverage for deduplication, renewal, lifecycle review, and audit provenance.

## 2026-07-14 — Document requirement detection v9.3 / product continuation v10.8

- Added migration `0024_document_requirement_assessments` and an immutable, content-addressed requirement coverage ledger.
- Added exact requirement resolution from human-published pathway versions, persisted eligibility assessments, or application-domain baselines with visible provenance.
- Added deterministic satisfied, missing, optional, expired, rejected, unverified, fact-inconsistency, and duplicate-conflict findings.
- Added twelve-hour Celery Beat scanning, lead-scoped manual scans, idempotent regeneration, human approval/rejection, and audit history.
- Added the Document Intelligence requirement queue, gap metrics, source snapshots, and explicit non-mutation controls.
- Added regression coverage proving no documents are created and no profile, application, eligibility, pathway, or timeline record is rewritten.
## 2026-07-14 — Document fraud-risk indicators v9.4 / product continuation v10.9

- Added migration `0025_document_fraud_risk_assessments` and immutable integrity-assessment ledger.
- Added deterministic exact-file reuse, conflicting type, approved mismatch, duplicate-conflict, rejected-evidence, hash-integrity, and approved identifier-reuse indicators.
- Masked repeated identifiers and retained only SHA-256 comparison hashes in indicator evidence.
- Added twelve-hour Celery Beat scanning, lead-scoped manual scans, restricted APIs, and mandatory human review notes.
- Added Document Intelligence risk metrics and queue with explicit zero automated fraud determinations or adverse actions.
- Added regression tests for idempotency, source linkage, privacy masking, human review, and non-mutation.
