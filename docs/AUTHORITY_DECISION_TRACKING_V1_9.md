# Authority Decision Tracking v1.9

## Purpose

Authority Decision Tracking v1.9 adds the post-submission stage of the Global Mobility AIOS application workflow.

The previous lifecycle path could reach:

```text
submitted
```

v1.9 adds controlled post-submission transitions:

```text
submitted -> decision_pending
submitted/decision_pending -> approved_by_authority
submitted/decision_pending -> rejected_by_authority
submitted/decision_pending -> withdrawn
```

## Data model decision

`ApplicationRecord.status` is a plain string field, so v1.9 does not require a schema migration.

The module keeps authority decision metadata in the lead audit note because the current `applications` table does not yet have dedicated decision metadata columns.

## Lead status mapping

Final authority outcomes update the lead business status safely:

```text
approved_by_authority -> LeadStatus.converted
rejected_by_authority -> LeadStatus.closed
withdrawn             -> LeadStatus.closed
```

`decision_pending` does not change the lead business status.

## API routes

```text
GET  /api/v1/authority-decision/applications/{application_id}
GET  /api/v1/authority-decision/queue
GET  /api/v1/authority-decision/leads/{lead_id}
POST /api/v1/authority-decision/applications/{application_id}/decision-pending
POST /api/v1/authority-decision/applications/{application_id}/approve
POST /api/v1/authority-decision/applications/{application_id}/reject
POST /api/v1/authority-decision/applications/{application_id}/withdraw
```

## Admin route

```text
GET /admin/authority-decision
```

## Design rule

Authority decision state is separate from readiness state. Readiness proves prerequisites were satisfied; authority decision tracking records what happened after submission.
