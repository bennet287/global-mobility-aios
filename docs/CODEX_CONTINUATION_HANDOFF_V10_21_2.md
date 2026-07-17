# Codex Continuation Handoff — v10.21.2

## Delivered

- Added `supplemental_<domain>` official-source certifications without a schema migration.
- Supplemental certification requires an approved primary certification, the same approved
  authority, and an approved immigration relationship.
- Primary certifications are never superseded by supplemental approvals.
- Fresh-monitor coverage can come from an approved primary or supplemental source while the
  primary authority/source gates remain primary-only.
- Supplemental batch items reuse the jurisdiction's approved assessment and support baseline
  capture plus assertion provenance pinned to the supplemental snapshot.
- Added Canada IRCC visitor-visa supplemental pack and PowerShell submission helper.
- Updated Coverage UI labels and approved supplemental-source visibility.
- Updated `docs/ROADMAP.md` and `docs/CHANGELOG.md`.

## Migration

No new migration. Expected head remains:

`0032_initial_rule_assertions`

## Next operation

Submit the Canada supplemental pack, independently approve its `supplemental_visa`
certification, capture its baseline, then use the tranche assistant on the returned batch ID.

## Safety

No automatic approvals, assertions, rule publication, regulatory changes, pathway mutations,
or coverage claims were added.
