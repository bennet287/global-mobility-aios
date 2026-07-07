# Data Model v0.1

## Lead

- id
- full_name
- email
- phone
- source
- intent
- target_country
- status
- notes
- created_at
- updated_at

## VerificationAudit

- id
- claim
- domain
- country
- verdict
- confidence
- official_sources_found
- requires_human_review
- explanation
- created_at

## DocumentRecord

- id
- lead_id
- document_type
- filename
- storage_key
- status
- extracted_metadata_json
- created_at

## ApplicationRecord

- id
- lead_id
- domain
- target_country
- target_institution_or_employer
- status
- risk_score
- created_at
