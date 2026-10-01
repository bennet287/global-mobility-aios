# Document Object-Store Backup + Recovery Proof v1

**Status:** IMPLEMENTED VERIFIER / TARGET-HOST RECOVERY PROOF PENDING

## Purpose

AIOS stores identity and case documents in external object storage. A provider backup declaration, bucket versioning, replication, or a successful live read is not recovery proof.

This contract separates vendor-specific backup/restore operations from AIOS verification. The storage provider owns how a backup is created and restored. AIOS verifies that objects selected **before backup** are readable from the recovered target with the same controlled key, SHA-256 digest, and byte size.

The verifier supports the canonical production document backends: MinIO/S3-compatible storage and OCI Object Storage. It reuses the existing document-storage adapter and does not create a second storage implementation.

## Safety and evidence boundary

- Never restore over the active production bucket.
- Use a separate recovery bucket/account/namespace target with equivalent private-access controls.
- Select synthetic/non-sensitive proof objects before backup. Do not put document bytes or credentials in the manifest.
- Create the manifest before the backup starts. A manifest produced after restore does not prove recovery.
- The verifier reads only the listed keys. It does not write, delete, create backups, invoke vendor restore APIs, or alter retention/versioning.
- A passing verifier proves only that the listed recovered bytes match the pre-backup manifest. It does not independently prove provider durability, encryption, public-read denial, retention, RPO/RTO, or recovery of every object.
- Repository tests are not target-host evidence.

## Pre-backup manifest

Create a private JSON manifest outside Git containing synthetic recovery objects that already exist under the controlled documents/ prefix. It uses schema `aios-document-storage-recovery-manifest-v1`, a unique manifest_id, storage_provider `minio` or `oci`, and object entries containing storage_key, 64-character lowercase sha256, and size_bytes.

Record separately in the protected operations evidence store: deployed commit/image digest, source bucket identity, provider backup/snapshot/version identifier, backup start/completion timestamps, recovery target identity, operator, and vendor-reported backup result.

## Recovery drill

1. Run the existing production storage preflight against the source bucket and retain its redacted result. This proves current adapter access only, not recovery.
2. Create and freeze the pre-backup manifest from synthetic proof objects already present in the source bucket. Record its SHA-256 digest.
3. Execute the documented backup mechanism for the actual object-store provider. Capture the provider's immutable backup/version/snapshot identifier and timestamps. If the provider cannot produce a restorable backup or equivalent independently recoverable copy, the gate is blocked.
4. Restore that backup to a **separate private recovery target**. Do not point the verifier at the live source bucket. Configure a one-off API container with the same backend type and recovery target bucket identity, using recovery-scoped credentials/instance identity.
5. Make the private manifest/receipt directory available to that one-off container through an operator-controlled private mount, then run `python -m app.services.document_storage_recovery --manifest <private-manifest-path> --receipt <private-receipt-path>`. Do not add the evidence directory to the application image or Git.
6. Require exit code 0 and `passed: true`. Independently verify the recovery target remains private and satisfies the backend's encryption/storage controls. Then destroy or quarantine the recovery target according to the provider procedure.
7. Only after the complete drill passes may the operator set `DOCUMENT_STORAGE_BACKUP_STRATEGY` to the concrete provider procedure identifier and `DOCUMENT_STORAGE_RECOVERY_TESTED_AT` to the actual UTC drill timestamp. Those settings remain declarations; retain the manifest, receipt, provider backup/restore evidence, privacy/encryption checks, and target identity as the authoritative evidence bundle.

## Failure handling

Any missing object, byte/hash/size mismatch, wrong backend, duplicate manifest key, invalid manifest, provider restore failure, privacy failure, or inability to identify an independently recoverable backup keeps object-store recovery **unverified**. Do not repair the recovered object manually and then reuse the same drill as evidence; start a new backup/recovery drill with a new manifest ID.

## Acceptance receipt

A complete target-host evidence bundle contains the exact deployed commit and image digest; pre-backup manifest plus digest; source and separate recovery target identities; provider backup/version/snapshot identifier and timestamps; provider restore result; AIOS recovery-verifier JSON receipt; independent privacy and encryption-control checks; operator and drill timestamp; cleanup/quarantine result; and explicit pass/fail/blocked conclusion.

Until such a bundle exists for the intended production storage provider, whole-product production recovery remains **NOT VERIFIED**.
