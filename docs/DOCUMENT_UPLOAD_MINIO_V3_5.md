> **Superseded access note:** upload storage remains valid, but direct object-key use and planned durable downloads are replaced by the signed, expiring grant flow in [`SIGNED_DOCUMENT_ACCESS_OBJECT_STORAGE_V9_5.md`](SIGNED_DOCUMENT_ACCESS_OBJECT_STORAGE_V9_5.md).

# Document Upload and MinIO v3.5

This milestone adds the production document upload foundation.

## Scope

Included:

- Multipart document upload API.
- Local storage backend for development and tests.
- MinIO storage backend for production-style object storage.
- SHA-256 file hash.
- File size and MIME type metadata.
- Storage provider and storage key metadata.
- Expiry date, verified-by, and verified-at fields.
- Audit event `document_uploaded`.
- Admin upload form.
- Alembic migration for document upload metadata.

Not included yet:

- OCR.
- AI document analysis.
- Signed, expiring document-access grants (delivered in v9.5).
- Client portal upload.
- Virus scanning.

## Routes

```text
POST /api/v1/documents/upload
GET  /api/v1/documents/{document_id}/file
GET  /admin/document-uploads
GET  /debug/document-uploads
```

## Configuration

Local development default:

```text
DOCUMENT_STORAGE_BACKEND=local
DOCUMENT_LOCAL_STORAGE_DIR=storage/documents
DOCUMENT_UPLOAD_MAX_MB=25
```

MinIO:

```text
DOCUMENT_STORAGE_BACKEND=minio
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_DOCUMENTS=gmai-documents
MINIO_SECURE=false
```

## Verification

Run:

```powershell
python -m compileall apps/api/app apps/api/tests scripts/seed_demo_data.py scripts/check_database_migrations.py scripts/check_docker_profile.py
python scripts/check_repo_policy.py --root .
python scripts/check_database_migrations.py
python scripts/check_docker_profile.py
$env:PYTHONPATH="apps/api"
python -m pytest apps/api/tests -q
```

Expected:

```text
Repository policy check passed.
Database migration check passed.
Docker production profile check passed.
All tests pass.
```

## Alembic

Migration added:

```text
apps/api/alembic/versions/0003_document_upload_minio.py
```
