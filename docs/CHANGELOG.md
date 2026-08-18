# Global Mobility AIOS — Active Changelog

This is the current changelog from the post-`f0688a8` baseline onward. The complete historical changelog through the sealed
Phase 13.16.7 baseline is preserved byte-for-byte at
[archive/CHANGELOG_THROUGH_F0688A8_2026-08-17.md](archive/CHANGELOG_THROUGH_F0688A8_2026-08-17.md).

## 2026-08-18 - Technology Radar V1.1 / Platform Evolution architecture checkpoint

- Promoted `docs/TECHNOLOGY_RADAR_V1_1.md` as the active canonical platform-evolution radar while preserving frozen
  `docs/TECHNOLOGY_RADAR_V1.md` as historical evidence.
- Added strategic fit tiers and recorded OpenWorker (`andrewyng/openworker`) as **A+ / STRATEGIC REFERENCE / CONTROLLED
  PILOT** for the future AIOS Coworker / finished-work execution plane; existing specialist candidates remain independently
  evaluated.
- Established the AIOS-owned **AIOS Coworker** capability boundary: third-party coworker/runtime implementations may
  execute files/tools/connectors and produce deliverables behind AIOS-owned contracts, but may not define WorkItem,
  authority, evidence/legal truth, Activity, Contribution, certification, publication, or business outcome semantics.
- Added the **Internal Learning & Quality Principle** and separated operational intelligence, evaluation/quality, and
  permitted training/optimization. Professional corrections, approvals/rejections, OCR fixes, and workflow outcomes are
  future traceable learning signals rather than implicit mutations of authoritative records.
- Added training/evaluation lineage direction plus a future `AIOSDataUsagePolicy` boundary so service, analytics,
  evaluation, improvement, human-review, and internal-model-training uses can be allowed/conditional/excluded with purpose,
  lawful-basis/compatibility, sensitivity, retention, provenance, and lineage metadata.
- Recorded the EU compliance direction as compliance-aware lawful learning: GDPR processing-purpose/legal-basis,
  special-category, minimisation, transparency, retention/security, and other applicable safeguards must be resolved for
  each production regime; future EU AI Act/GPAI provider obligations remain separately assessed if AIOS later becomes a
  model provider.
- Updated Platform Evolution waves: Wave 1 quality/safety (Promptfoo/OpenTelemetry/ClamAV), Wave 2 document/privacy
  intelligence, Wave 3 regulatory monitoring, Wave 4 AI runtime/retrieval/quality, Wave 5 AIOS Coworker + durable
  organization execution, Wave 6 professional output.
- Updated `docs/THIRD_PARTY_PLATFORM_ADOPTION_PRINCIPLES.md` to V1.1 while preserving AIOS Semantic Sovereignty,
  adapter-first integration, provider replacement, and evidence/authority boundaries.
- Reorganized the active `docs/ROADMAP.md` and `docs/CHANGELOG.md` into current-state documents while preserving their exact
  pre-checkpoint contents under `docs/archive/`. This keeps ongoing sessions focused without deleting historical Phase-13
  evidence.
- Corrected roadmap status so 13.16.8 Professional / Operator experience is consistently **UNLOCKED / NEXT** after accepted
  13.16.7; product sequencing itself is unchanged.
- Documentation/architecture checkpoint only: **no runtime dependency, package, model/table change, migration, container,
  feature flag, provider interface, preserved-database mutation, authorization expansion, publication/certification
  change, human-review weakening, production training regime, or Austria legal-safety change**. Phase 13.16.8 remains the
  active product slice.

### Verification in the documentation-preparation environment

- repository policy: **PASS**;
- release consistency: **PASS** at `0076_organization_position_active_identity`;
- UTF-8 / markdown-fence / relative-reference / trailing-whitespace integrity: **PASS**;
- database-migration checker: **not executed successfully in this environment** because the isolated runtime does not
  include `sqlmodel`; this is recorded as an environment limitation, not a PASS or product failure.
- no frontend build, complete API regression, browser/runtime acceptance, database mutation, or migration execution is
  claimed for this docs-only architecture checkpoint.
