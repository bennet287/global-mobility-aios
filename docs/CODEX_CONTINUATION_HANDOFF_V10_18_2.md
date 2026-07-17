# Codex Continuation Handoff v10.18.2

## Outcome

v10.18.2 fixes the Austria canonical-source remediation helper after a real
PostgreSQL/SQLAlchemy run committed the URL update but failed while printing
expired ORM attributes outside the session.

## Fix

- scalar IDs and status values are copied while the SQLAlchemy session is open;
- output after the session uses only a detached-safe result dictionary;
- rerunning after the prior post-commit failure is idempotent and reports
  `already_corrected=true`;
- an idempotent confirmation does not create a duplicate audit event;
- a source with an immutable snapshot may be confirmed when the URL already
  matches, but the URL can never be changed after snapshot creation.

## Unchanged boundaries

- HTTPS only;
- same hostname only;
- monitor allowlist required;
- credentials and non-standard ports rejected;
- no assessment, certification, snapshot, rule, or coverage-claim mutation;
- migration head remains `0031_global_coverage_source_onboarding`.

## Operator continuation

1. Apply the v10.18.2 hotfix.
2. Rerun `scripts/Repair-CoverageSourceCanonicalUrl.ps1` for Austria.
3. If the previous run committed successfully, expect `changed=false` and
   `already_corrected=true`.
4. Retry `scripts/Capture-ApprovedCoverageBaselines.ps1`.
5. Continue independent review for Germany, Canada, Australia, and New Zealand.
