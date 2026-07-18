# Changelog

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

