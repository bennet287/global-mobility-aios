# Sales Follow-up Engine v1.1

## Purpose

Sales Follow-up Engine v1.1 adds governance guardrails to the sales pipeline.

The sales system must not override the Truth Engine or human-review process. A lead can be contacted for clarification, but qualification and conversion are blocked when the case contains unresolved high-risk evidence.

## Main changes from v1

- Safer serialization of SQLModel table objects in API responses.
- `lead` is no longer returned as `{}` after qualify/convert actions.
- Qualification is blocked if the lead has:
  - rejected truth claims
  - truth claims requiring review
  - pending human reviews
- Conversion is blocked if the lead has:
  - rejected truth claims
  - truth claims requiring review
  - pending human reviews
- Conversion can optionally require documents to be ready by sending `require_documents_ready=true`.
- Admin sales buttons are disabled when hard guardrails are present.
- Follow-up creation remains allowed so staff can request clarification or documents.

## Governance rule

Sales conversion means only that a lead became a client or active agency case. It is not visa approval, job approval, immigration approval, university admission, or legal advice.

## Test expectation

For a lead with the claim:

`Germany student visa is guaranteed without financial proof`

The Truth Engine should reject the claim. Sales qualification and conversion should return HTTP `409 Conflict` until the rejected claim/pending review is resolved through the proper workflow.
