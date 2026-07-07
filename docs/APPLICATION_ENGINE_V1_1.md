# Application Engine v1.1

Application Engine v1.1 fixes the API readiness endpoint and hardens application draft persistence.

## Fixes

- API readiness responses are explicitly JSON-encoded.
- Computed readiness stages such as `blocked_truth_rejected` are no longer stored in enum-backed application status/stage fields.
- Application drafts store safe workflow values such as `draft` while keeping computed readiness information in notes/metadata when supported by the model.
- Readiness calculation no longer loads full `ApplicationRecord` rows, preventing older experimental enum-invalid records from breaking the queue.

## Important invariant

```text
Computed readiness stage != persisted lead/application status
```

`blocked_truth_rejected` is a computed guardrail stage only.
