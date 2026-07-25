# Changelog

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
