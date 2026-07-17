# Codex Continuation Handoff v10.17

## Completed increment

Phase 10B now includes the first current official-evidence starter tranche for:

- Austria (`AT`)
- Germany (`DE`)
- Canada (`CA`)
- Australia (`AU`)
- New Zealand (`NZ`)

The pack onboards authority/source/monitor records and creates ten pending review
records: five immigration-rule assessments and five primary-source
certifications. It never approves evidence.

## Important implementation change

`create_coverage_evidence_batch` now onboards a source before creating an
immigration assessment when both operations are present in the same row. The
assessment is automatically linked to that exact source. A mismatched supplied
source ID fails the complete batch.

## New files

- `apps/api/app/services/coverage_evidence_packs.py`
- `apps/api/tests/test_coverage_evidence_packs.py`
- `knowledge/global_coverage/tranches/v10_17_official_evidence_starter.json`
- `scripts/validate_global_coverage_evidence_pack.py`
- `scripts/Submit-GlobalCoverageEvidencePack.ps1`
- `docs/GLOBAL_COVERAGE_OFFICIAL_EVIDENCE_STARTER_V10_17.md`
- `docs/CODEX_CONTINUATION_HANDOFF_V10_17.md`

## Modified files

- `apps/api/app/services/coverage_evidence_batches.py`
- `apps/api/tests/test_local_quality_gate.py`
- `knowledge/official_sources/sources.yaml`
- `scripts/check_local_quality.py`
- `docs/CHANGELOG.md`
- `docs/ROADMAP.md`

## Release gates

- Focused coverage tests: 9 passed.
- Complete API suite reported 214 passed with 1 existing SQLModel deprecation warning. In this build container, the pytest process remained alive after printing its completed summary; the focused suites and all static quality gates exited cleanly.
- Local quality gate with migrated temporary SQLite database: passed.
- Next.js production build: passed all 21 routes.
- Migration head remains `0031_global_coverage_source_onboarding`.
- No database migration is included in v10.17.

## Operator next steps

1. Apply the v10.17 incremental patch and rebuild the API image.
2. Validate the pack with `python scripts/validate_global_coverage_evidence_pack.py`.
3. Preview submission with `scripts/Submit-GlobalCoverageEvidencePack.ps1 -WhatIf`.
4. Submit using a named proposer account.
5. Use a different reviewer account in the Coverage workspace to review each proposal.
6. Run the newly active monitors, review captured evidence, and publish at least one verified rule per jurisdiction.

## Remaining Phase 10B work

The five-jurisdiction tranche is not global coverage. The remaining required
jurisdictions still need official evidence, independent assessment/certification
review, fresh monitors, and human-published verified rules.
