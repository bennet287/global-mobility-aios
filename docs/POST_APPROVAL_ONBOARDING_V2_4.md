# Post-Approval Onboarding v2.4

## Purpose

Post-Approval Onboarding v2.4 starts the operational workflow after an application has reached:

```text
approved_by_authority
```

The module creates follow-up tasks for the agency team to support the client after approval.

## No schema migration

The current database does not have a dedicated onboarding table. v2.4 therefore stores onboarding actions as `FollowUp` records with a structured message prefix:

```text
[post_approval_onboarding:v2.4]
```

This keeps the workflow local-first and migration-free.

## Generated tasks

```text
confirm_authority_approval
send_client_next_steps
collect_travel_plan
verify_accommodation_arrival
confirm_insurance_and_documents
local_registration_guidance
```

## API routes

```text
GET  /api/v1/post-approval-onboarding/queue
GET  /api/v1/post-approval-onboarding/leads/{lead_id}
POST /api/v1/post-approval-onboarding/leads/{lead_id}/generate
POST /api/v1/post-approval-onboarding/follow-ups/{follow_up_id}/complete
```

## Admin route

```text
GET /admin/post-approval-onboarding
```

## Design rule

Post-approval onboarding must only start after authority approval. Leads without an `approved_by_authority` application are blocked.
