# Client Portal Foundation v12.0

## Outcome

Phase 12 begins with a dedicated, responsive client web portal. A client can use an
operator-issued access link to see a deliberately narrow case dashboard containing
case status, the next action, milestone progress, client-visible document
metadata, authority appointments, agency submissions, external agency
assignments, and authority checklist items. The portal does not expose internal
notes, truth claims, review queues, agent outputs, audit records, source
registries, or other leads.

This increment replaces the legacy email-or-phone return lookup. Contact details
are no longer accepted as public access credentials.

## Access model

- An authenticated operator issues a grant for exactly one lead.
- The generated bearer token is shown only in the issuance response. Only its
  SHA-256 digest is stored.
- A grant expires after 1–90 days, can be revoked immediately, and cannot be moved
  to another lead.
- Portal reads require the token in `X-GMAI-Portal-Token`.
- The public dashboard is assembled through a client-safe projection rather than
  returning an internal lead or case model.
- Creation, successful access, automatic expiry, and revocation produce audit
  events with actor and grant context.
- New public-intake submissions receive an initial portal grant and a
  `/portal?token=...` return path.

The frontend removes the token from the address bar after loading and retains it
only in `sessionStorage`. The internal agent-chat control is not rendered on
client-facing portal routes.

## Operator workflow

The internal lead detail screen contains a **Create portal link** panel. The
operator selects an expiry period, issues the grant, and copies the one-time link
for controlled delivery to the client. Revocation and grant history are available
through the versioned API.

## API surface

- `POST /api/v1/client-portal/grants`
- `GET /api/v1/client-portal/grants?lead_id={lead_id}`
- `POST /api/v1/client-portal/grants/{grant_id}/revoke`
- `GET /api/v1/public/client-portal/dashboard` — returns a client-safe projection
  including case status, next action, milestone progress, document metadata,
  authority appointments, agency submissions, external agency assignments, and
  authority checklist items.

The dashboard route is public only in the sense that it does not require an
operator identity; possession of a valid, unexpired, non-revoked lead-scoped token
is still mandatory.

## Database and verification

Migration `0043_client_portal_foundation` adds
`client_portal_access_grants`. Focused tests cover hash-only token persistence,
lead isolation, client-safe response fields, expiry, revocation, audit events, and
operator authorization. The fresh-database migration checks and Next.js
production build also include this increment.

## Remaining Phase 12 scope

This is the client web foundation plus agency workflow visibility, not completion
of Phase 12. Native/mobile application session controls, employer and partner
tenancy, stable external API contracts, communication/calendar/CRM automation,
and remaining government or agency workflow depth remain pending.
