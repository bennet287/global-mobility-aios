# Versioned Public and Partner APIs v12.2

Phase 12.2 establishes the first stable external API boundary for Global
Mobility AIOS. It separates unauthenticated product discovery from
credentialed, account-scoped partner data.

## Contract boundary

- Public discovery: `/api/public/v1` and `/api/public/v1/capabilities`
- Partner resources: `/api/partner/v1/account`, `/api/partner/v1/cases`, and
  `/api/partner/v1/compliance`
- Operator credential management: `/api/v1/partner-api/credentials`
- Contract response header: `X-GMAI-API-Version: 1.0`
- Current lifecycle response header: `Deprecation: false`

The public endpoints expose metadata only. They never return a tenant
identifier, client record, case, compliance event, or operational record.

## Authentication and tenant isolation

Operators issue a credential for exactly one active corporate account and one
or more of these scopes:

- `account:read`
- `cases:read`
- `compliance:read`

The raw `gmai_partner_live_...` key is returned once. The database stores only
its SHA-256 digest and a short display prefix. Partners send the raw value in
the `X-GMAI-Partner-Key` header.

Tenant scope always comes from the stored credential. Partner requests cannot
provide or change a corporate account identifier. Invalid, expired, revoked,
or suspended-account credentials return an authentication failure; a valid
credential without the required scope returns a forbidden response. Every
successful partner request updates usage metadata and creates an audit event.

## Stable projections

The account projection contains the external account reference, display name,
primary country, lifecycle status, and last update time.

The case projection contains the external case reference, case type, status,
employee display name, origin and destination, target and compliance dates,
and last update time.

The compliance projection contains the external case reference, event type,
title, due time, status, and evidence-required indicator.

These projections deliberately omit internal notes, direct contact data, lead
UUIDs, truth claims, controlled evidence, review records, agent output, audit
history, and operator actions.

## Pagination and caching

Case and compliance collections use `page` and `page_size` query parameters.
The default page size is 25 and the maximum is 100. Responses contain `data`
and a `meta` object with page, page size, total records, and total pages.

Public discovery can be cached for five minutes. All credentialed partner
responses carry `Cache-Control: private, no-store`.

## Credential lifecycle

Operators may issue credentials for 1 through 365 days, list credential
metadata, and revoke credentials with a recorded reason. Issuance, access,
automatic expiry, and revocation are auditable. Credential metadata never
returns the stored digest or reconstructs the raw key.

## Compatibility policy

Additive fields may be introduced within v1 when they do not change existing
field meaning. Removing or renaming fields, changing authentication semantics,
or changing tenant-scoping behavior requires a new path version. A future
deprecation will be announced through the lifecycle header and release notes
before removal.

## Verification

The focused regression suite covers:

- unauthenticated public discovery without tenant data;
- one-time secret issuance and hash-only persistence;
- stable version and cache headers;
- account-derived tenant isolation across two corporate accounts;
- field minimization;
- required scopes and bounded pagination;
- revocation, expiry, and suspended-account fail-closed behavior;
- management authentication and request auditing.

Database migration `0045_partner_api_credentials` creates the credential
ledger and advances the Phase 12 migration head.
