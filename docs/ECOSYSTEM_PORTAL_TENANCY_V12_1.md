# Employer and Partner Portal Tenancy v12.1

## Outcome

Phase 12 now includes a dedicated employer and authorized-partner workspace at
`/partner-portal`. The workspace shows a controlled portfolio view of corporate
mobility cases, open relocation tasks, and upcoming compliance obligations for
exactly one corporate account.

Employer and partner access is intentionally separate from internal operator
authentication and from the individual client portal.

## Tenant boundary

- Every access grant stores exactly one `corporate_account_id`.
- Each raw bearer token is returned once; only its SHA-256 digest is persisted.
- The token audience is explicitly recorded as `employer` or `partner`.
- Dashboard queries derive their account scope from the resolved grant. No account
  identifier supplied by the caller participates in authorization.
- Cases are selected by that account before employee names, tasks, or compliance
  records are projected.
- The response omits internal notes, lead identifiers, contact details, review
  records, audit records, truth claims, controlled evidence, and operator actions.
- A token cannot enumerate accounts or request a case from another account.
- Suspended or closed accounts fail closed even if a grant has not yet expired.

## Lifecycle and audit

Operators can issue a 1–90 day tenant link from the Corporate Mobility workspace.
Access can be revoked immediately. Creation, access, automatic expiry, and
revocation are recorded as audit events with the account and audience context.

The external route removes a presented token from the browser address bar and
keeps it only in session storage. Internal navigation and agent controls are not
rendered in the external workspace.

## API surface

- `POST /api/v1/ecosystem-portal/grants`
- `GET /api/v1/ecosystem-portal/grants?corporate_account_id={account_id}`
- `POST /api/v1/ecosystem-portal/grants/{grant_id}/revoke`
- `GET /api/v1/public/ecosystem-portal/dashboard`

The public dashboard requires `X-GMAI-Ecosystem-Token`. Grant management continues
to require internal role-based authentication.

## Database and verification

Migration `0044_ecosystem_portal_tenancy` adds
`ecosystem_portal_access_grants`. Regression coverage verifies hash-only token
storage, operator authentication, revocation, expiry, audit events, response-field
minimization, and a two-account isolation scenario in which Tenant A cannot observe
Tenant B's case reference, employee, or account identifier.

## Remaining Phase 12 scope

Native/mobile access, stable public and partner API contracts, ecosystem event
automation, and government or mobility-agency workflows remain pending.
