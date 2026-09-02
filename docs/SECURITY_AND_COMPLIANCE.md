# Security and Compliance

**Last verified:** 2026-08-08 against migration head `0067_marketing_runtime_contract`.
The repository CI checks that the roadmap migration-head declaration remains
aligned with the unique Alembic head.

## Sensitive Domains

- Visa/immigration guidance
- Job placement
- Financial proof
- Identity documents
- Medical or criminal records

## Rules

1. Do not promise visa, admission, or job outcomes.
2. Do not create or suggest fake documents.
3. Do not scrape websites in violation of terms or law.
4. Do not submit applications without explicit human approval.
5. Store documents securely with access control and audit logs.
6. Use only short-lived, signed document grants; never expose storage credentials, raw object keys, or durable object URLs.
7. Validate document byte size and SHA-256 hash at every controlled content access.
8. Separate AI suggestions from verified official facts.
9. Use only approved repositories from `docs/REPOSITORY_POLICY.md`.
10. Treat non-allowlisted repositories as denied by default pending legal and security review.


## Authentication baseline

- `AUTH_ALLOW_HEADER_ROLE` defaults to `false`; unsigned role headers are a
  local/test-only shortcut that must be enabled explicitly.
- `app.core.startup_safety.validate_production_settings()` runs in the API lifespan;
  production startup fails closed if authentication is disabled, header-role trust
  is enabled, `JWT_SECRET` is missing/default/too short, or the admin password is
  missing/default/too short.
- Production session cookies are marked `Secure` and `HttpOnly`.
- Route-role policy is declared in the ordered authorization registry instead of
  duplicated path checks. This remains an interim operator-auth layer; a full
  identity-provider/MFA user lifecycle remains future production hardening.

## Production document controls

- Production always requires the MinIO/S3-compatible backend; local document storage is refused even if strict mode is disabled.
- Set `DOCUMENT_STORAGE_PRODUCTION_STRICT=true` for the extended retention/backup/recovery posture.
- Use MinIO/S3-compatible private object storage with TLS and non-default credentials.
- Pre-provision the document bucket; disable application bucket auto-creation.
- Configure a separate long-random `DOCUMENT_ACCESS_TOKEN_SECRET`.
- Keep document grant TTL at or below 900 seconds and use the lowest practical use limit.
- Server-side encryption is enabled by default and is mandatory for production MinIO/S3 document writes; use a managed KMS where available and encrypted storage volumes as defense in depth.
- Configure legal/contractual retention and lifecycle rules; do not infer retention from immigration requirements.
- Maintain encrypted, versioned, off-site backups and record periodic restoration tests.
- Prohibit public bucket read policies and direct storage URLs.
- Review access-denial, expiry, revocation, and content-integrity audit events.

The API exposes a credential-safe posture report at
`GET /api/v1/document-access/storage-posture`; the production baseline always fails
closed when encryption/TLS/backend controls are missing, while strict mode adds the
retention, backup, recovery, and short-lived-access requirements.
