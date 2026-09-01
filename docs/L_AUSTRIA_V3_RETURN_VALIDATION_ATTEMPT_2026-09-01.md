# L — Austria V3 Return Validation Attempt

**Date:** 2026-09-01
**Branch:** `roadmap/global-mobility-aios-v12`
**Classification:** genuine independent review / supplied current-return attempt rejected structurally
**Milestone impact:** L remains `IMPLEMENTED / ACCEPTANCE PENDING`; M/N remain `NOT STARTED`

## 1. Review truth preserved

The operator confirms that the underlying Austria review was genuine and independent.

The supplied return records:

```text
independent_review = true
professional_review_reference       supplied
reviewer_reference                  supplied
reviewer_credential_reference       supplied
```

The review itself is not rejected as fake or non-independent.

## 2. Why the supplied JSON is not current-compilable

The submitted JSON cannot be promoted against the current benchmark state for three independent structural reasons.

### A. Fingerprint staleness

The supplied fingerprints are the historical V12.55/v2 fingerprints.

V12.57 changed the strong-points source labels/rationale from route-level `REVIEW_REQUIRED` / escalation to `ELIGIBLE` / no escalation.

Therefore at least the strong-points fingerprint is stale for current-head compilation.

Historical genuine review evidence remains preserved, but:

```text
genuine old-fingerprint review
!= current-fingerprint professional promotion
```

### B. Legacy/free-form reviewer-label vocabulary

The supplied labels use legacy/free-form pathway, evidence and legal-citation values such as `rwr-card-shortage-occupation`, application-document names, and prose citations.

The v3 reviewer contract requires:

```text
pathway key
  at-rwr-skilled-worker-shortage-occupation

bounded evidence keys
  shortage_occupation_training
  binding_job_offer
  applicable_minimum_remuneration
  points_evidence

rule/source refs
  canonical official_sources[].ref identifiers
```

Free-form practitioner document/citation detail remains welcome in `notes`, but not in the canonical benchmark-label fields.

### C. Incomplete ASSESSED labels

The submitted reviews use `"contradictions": null`.

For v3 `ASSESSED` returns, every reviewed-label field must be populated. If contradictions were assessed and none found, use `"contradictions": []`.

## 3. Return-contract version alignment

V12.59 aligns the semantic handoff and reviewer return version:

```text
reviewer packet
  austria-professional-review-handoff.v3

reviewer return
  austria-professional-review-blind-return.v3
```

The compiler now fail-closes on noncanonical pathway, evidence and source-reference keys instead of silently deriving broad `CORRECTED` records from legacy/free-form vocabulary.

## 4. Anonymous reviewer verification boundary

The reviewer explicitly requires anonymity.

Repository-bound reviewer/professional/credential fields must therefore use non-identifying opaque aliases only.

```text
REAL REVIEWER IDENTITY            VERIFIED OUTSIDE AIOS
REPOSITORY IDENTITY MODE          ANONYMOUS
PUBLIC IDENTITY DISCLOSURE        PROHIBITED
IDENTITY-TO-CREDENTIAL MAPPING    OUTSIDE GIT
```

Do not commit the reviewer's name, registration/bar number, email address, firm/employer name, address, phone number, public-profile URL, or any alias that directly encodes those values.

The compiler may validate that anonymous reference fields are structurally present, but the confidential evidence establishing the real reviewer, independence and professional standing must remain outside Git and outside committed project artifacts.

## 5. Current safe path

Do not manually rewrite the genuine review into current labels inside AIOS.

Instead:

1. run current-head V12.59 focused proof;
2. regenerate the current v3 packet + v3 blind-return template;
3. provide that exact template to the same genuine reviewer;
4. reviewer re-affirms/edits the current labels using the packet's v3 vocabulary;
5. preserve the real reviewer/credential evidence;
6. compile the returned v3 file;
7. validate the canonical bundle;
8. inspect CONFIRMED/CORRECTED results;
9. then commit professional evidence and run final exact-head L proof.

This preserves professional independence and avoids AIOS translating a reviewer's legal conclusions on their behalf.
