# External Agency Assignment Tracking v12.7

External Agency Assignment Tracking adds a registry of external mobility
agencies and the ability to assign applications to them, track the handoff
lifecycle, and record agency reference numbers. It is the third slice of Phase
12's "Government and mobility-agency workflows".

## Purpose

Some applications are handled partly or fully by external mobility agencies,
visa facilitators, or relocation service providers. This slice lets operators
maintain a directory of those agencies, mark their operational status, and
assign individual applications to them with a controlled handoff lifecycle.

## Data model

`ExternalAgency` (`external_agencies` table):

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID | Primary key |
| `name` | string | Agency name, indexed |
| `country` | string? | Optional country |
| `city` | string? | Optional city |
| `contact_email` | string? | Optional email |
| `contact_phone` | string? | Optional phone |
| `website` | string? | Optional website |
| `status` | string | Indexed. `active`, `suspended`, or `retired` |
| `notes` | string? | Free-text operator notes |
| `created_by` | string | Indexed actor |
| `updated_by` | string | Indexed actor |
| `created_at` | datetime | Indexed |
| `updated_at` | datetime | |

`ExternalAgencyAssignment` (`external_agency_assignments` table):

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID | Primary key |
| `application_id` | UUID | Foreign key to `applications.id`, indexed |
| `external_agency_id` | UUID | Foreign key to `external_agencies.id`, indexed |
| `status` | string | Indexed. `assigned`, `in_progress`, `handed_off`, `completed`, or `cancelled` |
| `agency_reference_number` | string? | Optional agency reference number |
| `handoff_at` | datetime? | Timestamp when status moved to `handed_off` |
| `completed_at` | datetime? | Timestamp when status moved to `completed` |
| `notes` | string? | Free-text operator notes |
| `created_by` | string | Indexed actor |
| `updated_by` | string | Indexed actor |
| `created_at` | datetime | Indexed |
| `updated_at` | datetime | |

The tables are created by migration `0050_external_agency_assignment`.

## API surface

### External agencies

- `POST /api/v1/external-agencies` — Create an agency.
- `GET /api/v1/external-agencies` — List agencies. Optional query `status`.
- `POST /api/v1/external-agencies/{agency_id}/status` — Update agency status.

### Assignments

- `POST /api/v1/external-agency-assignments` — Create an assignment.
- `GET /api/v1/external-agency-assignments` — List assignments. Optional query
  parameters `application_id`, `external_agency_id`, and `status`.
- `GET /api/v1/applications/{application_id}/external-agency-assignments` — List
  assignments for a specific application.
- `GET /api/v1/external-agency-assignments/{assignment_id}` — Read one assignment.
- `POST /api/v1/external-agency-assignments/{assignment_id}/status` — Update
  assignment status. Body requires `status` and `reason` (min length 3), and
  optionally `agency_reference_number`.

## Business rules

1. New agencies are created with `status = active`.
2. Only active agencies can receive new assignments.
3. An application can have only one active (non-terminal) assignment at a time.
4. Assignment status transitions are forward-only:
   - `assigned` → `in_progress` or `cancelled`
   - `in_progress` → `handed_off` or `cancelled`
   - `handed_off` → `completed` or `cancelled`
5. `completed` and `cancelled` are terminal states.
6. Moving to `handed_off` records `handoff_at`; moving to `completed` records
   `completed_at`.
7. Creating an assignment for a non-existent application or agency returns `404`.
8. Creating an assignment for an inactive agency or an application with an
   active assignment returns `409`.
9. Invalid status transitions return `409`.
10. Every creation and status change is recorded in `audit_logs` with the
    `external_agency` or `external_agency_assignment` entity type and the
    before/after state.

## Audit events

| Entity | Action | When |
|--------|--------|------|
| `external_agency` | `external_agency_created` | After agency creation |
| `external_agency` | `external_agency_active` / `suspended` / `retired` | After status change |
| `external_agency_assignment` | `external_agency_assignment_created` | After assignment creation |
| `external_agency_assignment` | `external_agency_assignment_{status}` | After each status change |

## Automation events

When the application's lead is linked to an active corporate mobility case, every
assignment status change also emits an `AutomationEvent` with type
`external_agency_assignment.status_changed` (added in v12.8.1). The event payload
includes the `application_id`, `lead_id`, `lead_name`, `case_reference`, and new
`status`, scoped to the linked corporate account. If no active corporate case is
linked, the status change still completes but no automation event is created.

## Scope and future work

This slice intentionally stays narrow: it does not sync with external agency
portals or handle agency billing. v12.8.1 links assignment status changes to the
governed automation outbox for handoff notifications. Future slices may add
agency-specific SLA tracking and expose agency assignments in the client
portal.
