# Corporate Mobility Foundation v11.0

## Scope

v11.0 establishes the first Phase 11 business-mobility boundary. It introduces governed
corporate accounts and review-gated corporate mobility cases without changing individual
lead, profile, pathway, Truth Engine, document, application, or authority-decision records.

Corporate accounts capture the legal employer identity, operating country, registration
reference, contact, and accountable compliance owner. A corporate mobility case belongs to
exactly one account and may reference an existing lead as the employee. It records the case
type, origin, destination, sponsor, target start, and compliance deadline.

## Safety and governance

- Every case has `human_review_required=true`; the API does not accept a client override.
- Creating a case does not determine eligibility, approve sponsorship, submit an application,
  or make a regulated claim.
- Account and case mutations write before/after audit records with the authenticated actor.
- Read-only users cannot mutate corporate mobility data.
- Cases can move only through explicit state transitions. Closed accounts and cases are
  immutable, and there is no delete endpoint.
- Employee links must reference an existing lead. Regulated conclusions continue to use the
  existing official-source, Truth Engine, review, and publication controls.

## API

- `POST /api/v1/corporate-mobility/accounts`
- `GET /api/v1/corporate-mobility/accounts`
- `GET /api/v1/corporate-mobility/accounts/{account_id}`
- `PATCH /api/v1/corporate-mobility/accounts/{account_id}`
- `POST /api/v1/corporate-mobility/accounts/{account_id}/cases`
- `GET /api/v1/corporate-mobility/cases`
- `GET /api/v1/corporate-mobility/cases/{case_id}`
- `PATCH /api/v1/corporate-mobility/cases/{case_id}`

## Operator workspace

`/corporate-mobility` provides account onboarding, account-scoped case lists, employee-lead
linking, relocation and compliance dates, and controlled case transitions. It uses the shared
workspace shell and preserves the warm-ivory/deep-indigo visual system.

## Data and migration

Alembic revision `0033_corporate_mobility_foundation` creates `corporate_accounts` and
`corporate_mobility_cases`. The downgrade removes only those new tables and their indexes.

## Deferred Phase 11 work

Dedicated dependant relationships, sponsor entities, and compliance calendar events were
delivered in v11.1. Business and investment pathways, HNWI/family-office structures, and
tax/treaty specialist review remain future Phase 11 slices.
