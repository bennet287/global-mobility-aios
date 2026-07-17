# Explicit Reassessment Acceptance Controls v10.12

## Purpose

This Phase 10D increment prevents a newer universal profile or reviewed regulatory
replacement from silently refreshing a client pathway assessment. Existing comparisons
and timelines remain pinned to the exact profile and pathway versions that created them.

## Controlled lifecycle

1. The latest comparison is inspected for a newer current profile and resolved regulatory
   impacts with a human-published replacement pathway version.
2. Ordinary comparison generation is blocked while either change is pending acceptance.
3. An operator records the user's explicit acceptance, including an attestation and notes.
4. Recording acceptance creates only an immutable ledger row; it does not reassess anything.
5. A separate execute action consumes that acceptance and creates a new immutable comparison.

## Version boundaries

Profile-only reassessment uses the explicitly accepted current profile and keeps the
baseline pathway versions pinned. Regulatory reassessment applies only the selected,
reviewed replacement versions. Unselected pathway versions remain unchanged.

A profile that changes again after acceptance invalidates the pending acceptance. A newer
comparison also invalidates an unconsumed acceptance, preventing divergent reassessment
branches.

## API

- `GET /api/v1/pathways/comparisons/{lead_id}/reassessment`
- `GET /api/v1/pathways/comparisons/{lead_id}/reassessment-acceptances`
- `POST /api/v1/pathways/comparisons/{lead_id}/reassessment-acceptances`
- `POST /api/v1/pathways/reassessment-acceptances/{acceptance_id}/execute`

## Safety and audit

- Explicit user acceptance must be affirmed and described.
- Current profile consent must remain granted.
- Regulatory replacements must come from resolved, human-reviewed pathway impacts and
  published or superseded pathway versions.
- Acceptance creation and consumption emit separate audit events.
- Historical comparisons, timelines, milestones, profiles, pathways, and verified rules
  are never rewritten.
