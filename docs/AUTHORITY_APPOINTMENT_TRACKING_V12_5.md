# Authority Appointment Tracking v12.5

Authority Appointment Tracking adds a dedicated, auditable ledger for
application-facing appointments with government and mobility agencies (consulates,
visa application centres, biometric collection points, etc.). It is the first
slice of Phase 12's "Government and mobility-agency workflows".

## Purpose

Applications routinely require external appointments before a decision can be
recorded. This slice lets operators schedule those appointments, track their
outcomes, and preserve an immutable audit trail without mixing appointment
semantics into the application status field.

## Data model

`AuthorityAppointment` (`authority_appointments` table):

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID | Primary key |
| `application_id` | UUID | Foreign key to `applications.id`, indexed |
| `appointment_type` | string | Indexed. `biometric`, `interview`, `document_submission`, or `other` |
| `authority_name` | string | Human-facing agency name, e.g. "German Consulate Mumbai" |
| `location` | string? | Optional appointment location |
| `scheduled_at` | datetime | Indexed. Appointment date/time in UTC |
| `timezone` | string? | Defaults to `UTC` |
| `status` | string | Indexed. `scheduled`, `completed`, `cancelled`, or `no_show` |
| `reference_number` | string? | Optional authority reference number |
| `notes` | string? | Free-text operator notes |
| `created_by` | string | Indexed actor who created the record |
| `updated_by` | string | Indexed actor of last mutation |
| `created_at` | datetime | Indexed, default `now_utc` |
| `updated_at` | datetime | Default `now_utc` |

The table is created by migration `0048_authority_appointment_tracking`.

## API surface

All routes are under `/api/v1/authority-appointments`.

- `POST /api/v1/authority-appointments` — Create an appointment.
- `GET /api/v1/authority-appointments` — List appointments. Accepts optional query
  parameters `application_id` and `status`.
- `GET /api/v1/authority-appointments/{appointment_id}` — Read a single
  appointment.
- `POST /api/v1/authority-appointments/{appointment_id}/status` — Update the
  status of an appointment. Requires `status` and `reason` (min length 3).

## Business rules

1. `appointment_type` must be one of `biometric`, `interview`,
   `document_submission`, or `other`.
2. New appointments are created with `status = scheduled`.
3. Status transitions are only allowed from `scheduled` to one of `completed`,
   `cancelled`, or `no_show`.
4. `completed`, `cancelled`, and `no_show` are terminal states. No further
   status changes are permitted from a terminal state.
5. Creating an appointment for a non-existent application returns `404`.
6. Invalid status transitions return `409`.
7. Every creation and status change is recorded in `audit_logs` with the
   `authority_appointment` entity type and the before/after state.

## Audit events

| Action | When |
|--------|------|
| `authority_appointment_created` | After a successful `POST` |
| `authority_appointment_completed` | After status moves to `completed` |
| `authority_appointment_cancelled` | After status moves to `cancelled` |
| `authority_appointment_no_show` | After status moves to `no_show` |

All events use the source `authority_appointment_v12_5` and record the actor
from the request's authentication context.

## Automation outbox integration

### Status changes (v12.6.1)

When an appointment status changes and the linked application's lead is
associated with an active corporate mobility case, the change is bridged into
the governed automation outbox as an `appointment.status_changed` event. The
corporate account and case are derived from the lead's case link, so existing
automation rules can route the event through email, messaging, calendar, or CRM
connectors under the same review, retry, and audit controls as case events. If
no active corporate case link exists, the status change still completes but no
automation event is created.

### Reminders (v12.8.5)

A scheduled Celery beat task scans for `scheduled` appointments occurring within
the next 24 hours and emits one `appointment.reminder` automation event per
appointment when the linked application's lead is associated with an active
corporate mobility case. Events are idempotent per appointment per UTC day and
carry authority name, appointment type, scheduled time, location, timezone, and
reference number. Corporate automation rules can route these reminders through
email, messaging, or calendar connectors under the same review, retry, and
audit controls as other automation events.

## Scope and future work

This slice intentionally stays narrow: it does not handle credential or
encryption concerns, direct external calendar provider integration, or automated
provider dispatch. Future slices may add a calendar-channel adapter that
produces ICS/event payloads, deeper integration with external calendar APIs,
and additional reminder windows.
