# Authority Submission Checklist v12.8

Authority Submission Checklist adds per-authority templates of required
documents, fees, forms, and procedural steps, and lets operators instantiate
those templates against individual applications. It is the fourth slice of
Phase 12's "Government and mobility-agency workflows".

## Purpose

Every consulate, visa application centre, and mobility agency has a different
set of requirements before an application can be submitted. This slice gives
operators a reusable checklist template per authority and an application-specific
checklist that tracks whether each item is pending, completed, or not
applicable.

## Data model

`AuthorityChecklistTemplate` (`authority_checklist_templates` table):

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID | Primary key |
| `authority_name` | string | Indexed. e.g. "German Consulate Mumbai" |
| `country` | string? | Optional country filter |
| `item_key` | string | Indexed stable key, e.g. `passport_copy` |
| `item_label` | string | Human-readable label |
| `category` | string | Indexed. `document`, `fee`, `form`, or `step` |
| `is_required` | bool | Whether the item is required by default |
| `sort_order` | int | Display order |
| `created_by` | string | Indexed actor |
| `updated_by` | string | Indexed actor |
| `created_at` | datetime | Indexed |
| `updated_at` | datetime | |

`ApplicationAuthorityChecklistItem` (`application_authority_checklist_items` table):

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID | Primary key |
| `application_id` | UUID | Foreign key to `applications.id`, indexed |
| `template_item_id` | UUID? | Optional link to `authority_checklist_templates.id` |
| `authority_name` | string | Indexed |
| `item_key` | string | Indexed |
| `item_label` | string | |
| `category` | string | Indexed |
| `is_required` | bool | |
| `status` | string | Indexed. `pending`, `completed`, or `not_applicable` |
| `notes` | string? | Operator notes |
| `created_by` | string | Indexed actor |
| `updated_by` | string | Indexed actor |
| `created_at` | datetime | Indexed |
| `updated_at` | datetime | |

The tables are created by migration `0051_authority_submission_checklist`.

## API surface

### Templates

- `POST /api/v1/authority-checklist-templates` — Create a template item.
- `GET /api/v1/authority-checklist-templates` — List templates. Optional query
  parameters `authority_name` and `country`.
- `POST /api/v1/authority-checklist-templates/apply` — Copy all template items
  for an authority into an application's checklist. Skips items that already exist
  for that application/template combination (idempotent).

### Application checklist items

- `POST /api/v1/application-authority-checklist-items` — Create a manual checklist
  item for an application.
- `GET /api/v1/applications/{application_id}/authority-checklist` — List items
  for a specific application.
- `POST /api/v1/applications/{application_id}/authority-checklist/reminders` —
  Emit one `authority_checklist.reminder` automation event per pending checklist
  item for the application, scoped to the linked corporate case.
- `GET /api/v1/application-authority-checklist-items` — List items across
  applications. Optional query parameters `application_id`, `authority_name`,
  and `status`.
- `GET /api/v1/application-authority-checklist-items/{item_id}` — Read one item.
- `POST /api/v1/application-authority-checklist-items/{item_id}/status` — Update
  the status of an item. Optional `notes`.
- `DELETE /api/v1/application-authority-checklist-items/{item_id}` — Delete an item.

## Business rules

1. Template categories must be one of `document`, `fee`, `form`, or `step`.
2. Applying a template to an application creates a `pending` checklist item for
   every template item that does not already exist for that application.
3. Applying a template is idempotent; existing items are not duplicated.
4. Manual checklist items can be added to an application at any time.
5. Checklist item statuses are `pending`, `completed`, or `not_applicable`.
6. Required items must be `completed` or `not_applicable` before an agency
   submission can be created for the same application and authority; otherwise
   `POST /api/v1/agency-submissions` returns `409`.
7. Creating an item for a non-existent application returns `404`.
8. Every creation, status change, and deletion is recorded in `audit_logs` with
   the `application_authority_checklist_item` entity type and the before/after
   state.

## Audit events

| Entity | Action | When |
|--------|--------|------|
| `authority_checklist_template` | `authority_checklist_template_created` | After template creation |
| `application_authority_checklist_item` | `application_checklist_item_created` | After item creation from template or manually |
| `application_authority_checklist_item` | `application_checklist_item_{status}` | After status change |
| `application_authority_checklist_item` | `application_checklist_item_deleted` | After deletion |

All events use the source `authority_checklist_v12_8` and record the actor from
the request's authentication context.

## Automation events

When the application's lead is linked to an active corporate mobility case,
`POST /api/v1/applications/{application_id}/authority-checklist/reminders` emits
an `AutomationEvent` with type `authority_checklist.reminder` for each pending
checklist item (added in v12.8.2). The event payload includes the
`application_id`, `lead_id`, `lead_name`, `case_reference`, `authority_name`,
`item_key`, `item_label`, `is_required`, and `status`.

Events are idempotent per item per UTC day. They are scoped to the linked
corporate account and case, so automation rules can route reminder notifications
through email, messaging, calendar, or CRM connectors under the same review,
retry, and dispatch controls as other automation events. If no active corporate
case is linked, the endpoint returns an empty list and no events are created.

## Scope and future work

v12.8.2 adds a submission-blocking gate and governed reminders for pending
checklist items. Future slices may add scheduled/Celery-driven reminder
generation, due dates and escalation on individual checklist items, and
client-portal visibility of pending/completed checklist items.
