# Signed Document Access and Object-Storage Controls v9.5

## Purpose

This final Phase 9 increment replaces durable document URLs and direct object-key
handling with short-lived, audited access grants. It supports local storage and
MinIO while preserving document verification, extraction, profile, application,
eligibility, and communication state.

A grant is an authorization to read one exact immutable document snapshot. It is
not a verification decision, sharing approval, client communication, or evidence
acceptance action.

## Grant model

`DocumentAccessGrant` stores:

- exact document and lead scope;
- authenticated recipient username and role;
- allowlisted operational purpose;
- immutable expiry time, maximum uses, and use count;
- upload hash, size, storage-provider, and hashed object-key snapshot;
- active, consumed, expired, or revoked lifecycle state;
- creator, last accessor, revoker, timestamps, and revocation reason; and
- only a SHA-256 token hash—never the reusable raw token.

Tokens are HMAC signed, returned once at creation, limited to 30–900 seconds, and
bound to the grant, document, lead, user, role, purpose, and expiry. Non-admin
operators can issue grants only to themselves. Administrators can delegate to a
specific authenticated user and role.

## Access controls

The content endpoint requires both:

1. a valid signed token; and
2. an authenticated session/header context matching the token recipient and role.

Every read revalidates grant state, expiry, use limits, lead scope, document
metadata, object location hash, byte size, and SHA-256 content hash. Access fails
closed for malformed or forged tokens, actor/role mismatch, revocation, expiry,
consumption, changed metadata, missing objects, or altered bytes.

Successful responses use attachment disposition and `no-store`, `nosniff`, and
sandbox headers. Storage credentials, raw object keys, and direct object URLs are
never returned.

## Audit lifecycle

Audit actions are:

- `document_access_grant_created`;
- `document_accessed`;
- `document_access_denied`;
- `document_access_grant_expired`; and
- `document_access_grant_revoked`.

Celery Beat expires active grants hourly. Listing or using grants also performs
expiry reconciliation, so enforcement does not depend solely on the scheduler.

## Production storage posture

`GET /api/v1/document-access/storage-posture` reports configuration posture
without exposing credentials. Strict production mode fails closed unless:

- MinIO is used, unless local storage is explicitly permitted;
- TLS is enabled;
- default MinIO credentials are replaced;
- the bucket is pre-provisioned rather than auto-created;
- a separate document-access signing secret is configured;
- maximum token lifetime does not exceed 900 seconds;
- retention, backup, and recovery-test records are configured; and
- the bucket does not expose public object-read policy.

Optional MinIO server-side encryption is applied on upload when configured.
Production operators must also configure private bucket policy, encrypted disks
or KMS-backed server-side encryption, lifecycle/retention rules, versioned
backups, and tested recovery procedures.

## API and workspace

- `POST /api/v1/document-access/documents/{document_id}/grants`
- `GET /api/v1/document-access/grants`
- `GET /api/v1/document-access/grants/{grant_id}`
- `POST /api/v1/document-access/grants/{grant_id}/revoke`
- `POST /api/v1/document-access/grants/expire`
- `POST /api/v1/document-access/content`
- `GET /api/v1/document-access/storage-posture`

The Document Intelligence workspace adds storage posture, active-access metrics,
one-use secure downloads, and a revocable access ledger. Existing document APIs
now return safe metadata without raw storage keys.

## Migration and verification

Migration `0026_document_access_grants` creates the grant ledger and indexes.
Regression tests cover issuance, one-use consumption, delegated role scope,
revocation, expiry, tamper denial, public-bucket policy detection, audit events,
and preservation of document verification state.
