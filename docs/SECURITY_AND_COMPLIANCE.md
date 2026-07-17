# Security and Compliance

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

## Production document controls

- Set `DOCUMENT_STORAGE_PRODUCTION_STRICT=true`.
- Use MinIO/S3-compatible private object storage with TLS and non-default credentials.
- Pre-provision the document bucket; disable application bucket auto-creation.
- Configure a separate long-random `DOCUMENT_ACCESS_TOKEN_SECRET`.
- Keep document grant TTL at or below 900 seconds and use the lowest practical use limit.
- Enable server-side encryption with a managed KMS where available and encrypted storage volumes otherwise.
- Configure legal/contractual retention and lifecycle rules; do not infer retention from immigration requirements.
- Maintain encrypted, versioned, off-site backups and record periodic restoration tests.
- Prohibit public bucket read policies and direct storage URLs.
- Review access-denial, expiry, revocation, and content-integrity audit events.

The API exposes a credential-safe posture report at
`GET /api/v1/document-access/storage-posture`; strict mode fails closed when
required production controls are missing.
