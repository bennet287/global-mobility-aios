# Global Mobility AIOS MVP Release v6.2

## Release Summary

This release packages the local-first Global Mobility AIOS demo into a shareable MVP checkpoint.

The system demonstrates a human-controlled immigration/admissions operations workflow with lead intake, document tracking, official-source truth checks, controlled internal agent outputs, client communication draft review, audit logs, and a local release archive.

## Release Tags

```text
demo-release-v5.6
demo-release-v5.7
demo-release-v5.8
demo-release-v5.9
mvp-release-v6.0
mvp-release-v6.1
mvp-release-v6.2
```

## Included Release Artifacts

The local archive is generated at:

```text
release_exports/mvp-release-archive-v6.2.zip
```

It contains:

```text
release/mvp-release-bundle-v6.1.md
release/mvp-release-bundle-v6.1.json
metadata/manifest.json
project/docs/CHANGELOG.md
project/docs/DEMO_RELEASE_RUNBOOK_V5_1.md
project/docs/DEMO_SNAPSHOT_EXPORT_V5_2.md
project/docs/DEMO_READINESS_BANNER_V5_4.md
project/docs/DEMO_RELEASE_STATUS_V5_9.md
project/docs/AGENT_DUPLICATE_OUTPUT_GUARD_V5_6.md
project/docs/DEMO_UX_POLISH_V5_7.md
project/docs/DEMO_EXPORT_CLEANUP_V5_8.md
project/docs/MVP_RELEASE_HARDENING_V6_0.md
project/docs/MVP_RELEASE_BUNDLE_EXPORT_V6_1.md
project/docs/MVP_RELEASE_ARCHIVE_V6_2.md
```

## Demo Scope

The release supports a local demo through:

```text
/admin/v2
/admin/controlled-agents
/admin/agent-output-reviews
/admin/client-communications
/admin/audit-logs
```

The demo data contains four representative leads and shows controlled transitions through blocked claims, missing documents, application-ready cases, and communication review.

## Safety Position

This MVP is intentionally operator-controlled:

```text
auto_send: disabled
automatic_submission: disabled
automatic_lead_conversion: disabled
human_review_required: true
```

The system does not automatically send emails, WhatsApp messages, submit applications, convert leads, or mutate external portals.

## Verification Commands

Before publishing or sharing the archive, run:

```powershell
python scripts/check_local_quality.py
python scripts/export_mvp_release_archive.py --json
python scripts/check_github_release_ready.py --json
git status
```

Expected state:

```text
Local quality gate passed.
archive status: ready
GitHub release prep: ready
working tree clean
```

## Added after v6.3 release prep

- In-House Consultant Agent floating chat widget for operator assistance.
- Next.js Agent Console (`/agents/console`) for running controlled agents.
- Next.js Agent Review Queue (`/agents/review`) with bulk approve/reject/convert.
- Next.js Lead Detail Experience (`/leads/[id]`) with profiles, source references, documents, applications, and tabbed workflow history.
- Next.js Client Communication Drafts workspace (`/communications/*`) for post-approval client messaging.

## Suggested GitHub Release Title

```text
Global Mobility AIOS MVP Release v6.2
```

## Suggested GitHub Release Description

Use this file as the release body and attach:

```text
release_exports/mvp-release-archive-v6.2.zip
```
