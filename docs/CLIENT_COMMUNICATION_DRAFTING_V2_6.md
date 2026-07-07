# Client Communication Drafting v2.6

## Purpose

Client Communication Drafting v2.6 generates safe, reviewable client communication drafts after authority approval.

The module creates drafts only. It does not send emails automatically.

## Eligibility

Drafting is allowed only when the lead has at least one application with:

```text
approved_by_authority
```

## Storage

No schema migration is required. Drafts are stored as `FollowUp` records with:

```text
channel = email_draft
status  = draft
message prefix = [client_communication_draft:v2.6]
```

## Templates

```text
approval_confirmation
post_approval_next_steps
travel_checklist
document_checklist
local_registration_guidance
```

## API routes

```text
GET  /api/v1/client-communications/templates
GET  /api/v1/client-communications/drafts
GET  /api/v1/client-communications/drafts/{draft_id}
GET  /api/v1/client-communications/leads/{lead_id}
POST /api/v1/client-communications/leads/{lead_id}/drafts/{template_key}
POST /api/v1/client-communications/leads/{lead_id}/draft-pack
POST /api/v1/client-communications/drafts/{draft_id}/mark-reviewed
```

## Admin routes

```text
GET  /admin/client-communications
GET  /admin/client-communications/drafts
GET  /admin/client-communications/leads/{lead_id}
```

## Safety rule

Drafts are generated for human review only. Sending remains outside the system until a dedicated reviewed-send workflow is built.
