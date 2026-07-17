# Document Expiry Monitoring and Reminder Tasks v9.2

## Purpose

This Phase 9 increment monitors expiry dates already recorded on governed
`DocumentRecord` metadata and creates internal, auditable reminder tasks. It does
not send email, SMS, messaging-app notifications, or any other external client
communication.

The reminder ledger is operational triage. It does not verify document
validity, determine whether renewal is legally required, change an application,
or make an immigration conclusion.

## Deterministic urgency bands

The scanner assigns one current urgency band per document and recorded expiry
version:

- more than 90 days: no task;
- 31 to 90 days: `expires_within_90_days`;
- 8 to 30 days: `expires_within_30_days`;
- 0 to 7 days: `expires_within_7_days`;
- past the recorded date: `expired`.

A later scan is idempotent for the same document, expiry timestamp, and urgency
band. When a more urgent band becomes active, the prior pending task is retained
as `superseded` and linked to the new task. When the document expiry date is
changed, stale pending tasks are superseded even when the renewed document is
outside the 90-day window.

## Immutable reminder basis

Every `DocumentExpiryReminderTask` snapshots:

- document and optional lead IDs;
- document type and filename;
- exact recorded expiry timestamp;
- urgency type, threshold, priority, and due time;
- deterministic reminder key;
- source and generation actor;
- external-delivery state fixed to `not_sent`;
- review and supersession provenance;
- creation and update timestamps.

Changing `DocumentRecord.expiry_date` never rewrites historical reminder rows.

## Human control

Pending tasks can be decided only by an authorized reviewer or administrator.
Supported decisions are:

- `acknowledged`;
- `resolved`;
- `dismissed`.

Every decision requires a note and creates an audit record. Reviewing a reminder
does not change document verification, extraction approval, application status,
profile facts, or any client communication record.

## Scheduling and API

Celery Beat runs the global deterministic scan every six hours. Operators can
also run a lead-scoped scan from the Document Intelligence workspace.

- `POST /api/v1/document-intelligence/expiry-reminders/scan`
- `GET /api/v1/document-intelligence/expiry-reminders`
- `GET /api/v1/document-intelligence/expiry-reminders/{reminder_id}`
- `POST /api/v1/document-intelligence/expiry-reminders/{reminder_id}/review`

Every scan response reports `external_messages_sent=0`.

## Audit actions

- `document_expiry_scan_completed`
- `document_expiry_reminder_created`
- `document_expiry_reminder_superseded`
- `document_expiry_reminder_acknowledged`
- `document_expiry_reminder_resolved`
- `document_expiry_reminder_dismissed`

## Database and rollback

Migration `0023_document_expiry_reminders` creates the reminder ledger, unique
reminder-key index, lifecycle indexes, and self-referencing supersession link.
Downgrade removes only the reminder table; source documents remain unchanged.

## Safety boundaries

- No external message is sent automatically.
- Extracted expiry values are not copied into document metadata automatically.
- A missing expiry date produces no assumption and no reminder.
- Reminder urgency is date arithmetic, not legal advice.
- Renewal, replacement, and application consequences remain human-controlled.
