# Agency Submission Tracking v12.6

Agency Submission Tracking adds an immutable, auditable ledger for recording
when and how applications are submitted to government and mobility agencies. It
is the second slice of Phase 12's "Government and mobility-agency workflows".

## Purpose

Applications are submitted to consulates, visa application centres, and other
authorities through different channels (online, in person, courier, agency
hand-off). This slice records each submission event distinctly from the
application status so operators can track reference numbers, submission channels,
dates, and authority progress without overloading the application lifecycle
state machine.

## Data model

`AgencySubmission` (`agency_submissions` table):

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID | Primary key |
| `application_id` | UUID | Foreign key to `applications.id`, indexed |
| `authority_name` | string | Human-facing agency name, e.g. "German Consulate Mumbai" |
| `submission_channel` | string | Indexed. `online`, `in_person`, `courier`, or `agency` |
| `submitted_at` | datetime | Indexed. Submission date/time in UTC |
| `reference_number` | string? | Optional authority reference number |
| `tracking_url` | string? | Optional external tracking URL |
| `status` | string | Indexed. `submitted`, `acknowledged`, `under_review`, `decision_received`, or `returned` |
| `notes` | string? | Free-text operator notes |
| `created_by` | string | Indexed actor who created the record |
| `updated_by` | string | Indexed actor of last mutation |
| `created_at` | datetime | Indexed, default `now_utc` |
| `updated_at` | datetime | Default `now_utc` |

The table is created by migration `0049_agency_submission_tracking`.

## API surface

All routes are under `/api/v1/agency-submissions`.

- `POST /api/v1/agency-submissions` — Create a submission record.
- `GET /api/v1/agency-submissions` — List submissions. Accepts optional query
  parameters `application_id` and `status`.
- `GET /api/v1/agency-submissions/{submission_id}` — Read a single submission.
- `POST /api/v1/agency-submissions/{submission_id}/status` — Update the status
  of a submission. Requires `status` and `reason` (min length 3).

## Business rules

1. `submission_channel` must be one of `online`, `in_person`, `courier`, or
   `agency`.
2. New submissions are created with `status = submitted`.
3. Status transitions are forward-only:
   - `submitted` → `acknowledged`
   - `acknowledged` → `under_review`
   - `under_review` → `decision_received` or `returned`
4. `decision_received` and `returned` are terminal states. No further status
   changes are permitted from a terminal state.
5. Creating a submission for a non-existent application returns `404`.
6. Invalid status transitions return `409`.
7. Every creation and status change is recorded in `audit_logs` with the
   `agency_submission` entity type and the before/after state.

## Audit events

| Action | When |
|--------|------|
| `agency_submission_created` | After a successful `POST` |
| `agency_submission_acknowledged` | After status moves to `acknowledged` |
| `agency_submission_under_review` | After status moves to `under_review` |
| `agency_submission_decision_received` | After status moves to `decision_received` |
| `agency_submission_returned` | After status moves to `returned` |

All events use the source `agency_submission_v12_6` and record the actor from the
request's authentication context.

## Automation outbox integration (v12.6.1)

When a submission status changes and the linked application's lead is
associated with an active corporate mobility case, the change is bridged into
the governed automation outbox as a `submission.status_changed` event. The
corporate account and case are derived from the lead's case link, so existing
automation rules can route the event through email, messaging, calendar, or CRM
connectors under the same review, retry, and audit controls as case events. If
no active corporate case link exists, the status change still completes but no
automation event is created.

## Scope and future work

This slice intentionally stays narrow: it does not automate actual authority
submissions, encrypt credentials, or sync with external portals. Future slices
may add authority-specific submission checklists, link submissions to the
automation outbox for status-change notifications, and expose submission
history in the client portal.
