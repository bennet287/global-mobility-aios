# L — Austria Anonymous Reviewer Privacy Boundary

**Date:** 2026-09-01
**Branch:** `roadmap/global-mobility-aios-v12`
**Classification:** reviewer privacy / professional-review evidence governance
**Milestone impact:** L remains `IMPLEMENTED / ACCEPTANCE PENDING`; M/N remain `NOT STARTED`

## 1. Binding privacy requirement

The independent Austria reviewer requires anonymity.

That requirement is binding on all repository-bound artifacts.

```text
REAL REVIEWER IDENTITY            CONFIDENTIAL
REPOSITORY IDENTITY MODE          ANONYMOUS
PUBLIC IDENTITY DISCLOSURE        PROHIBITED
IDENTITY-TO-CREDENTIAL MAPPING    OUTSIDE GIT
```

## 2. Data that must not be committed

Do not commit or encode:

- personal name;
- bar / professional registration number;
- email address;
- phone number;
- postal address;
- firm or employer name when it identifies the reviewer;
- public profile or directory URL;
- aliases that directly embed any of the above.

This applies to review JSON, canonical compiled review bundles, proof documents, ROADMAP / CHANGELOG / state handoffs, real-reviewer test fixtures, and commit messages.

## 3. Repository-safe provenance

Repository artifacts may contain only non-identifying opaque aliases in:

```text
professional_review_reference
reviewer_reference
reviewer_credential_reference
```

The opaque aliases must not reveal the reviewer’s identity.

The confidential mapping from those aliases to real identity, credentials and supporting evidence must remain outside Git and outside committed project artifacts.

## 4. Acceptance boundary

Anonymity does not weaken professional-review requirements.

Outside AIOS, the operator must still establish that the reviewer is real, independent, professionally qualified, and that the review evidence is authentic.

Inside the repository, only privacy-safe aliases and review conclusions are retained.

```text
ANONYMOUS IN REPOSITORY != UNVERIFIED IN REAL WORLD
CONFIDENTIAL EXTERNAL VERIFICATION != PUBLIC IDENTITY DISCLOSURE
```

## 5. V3 handoff behavior

The Austria v3 packet contains `reviewer_privacy_contract` and instructs the operator/reviewer not to include identifying data in repository-bound reference fields.

The compiler validates review structure and label semantics. It does not require public identity disclosure.

## 6. Current next step

Generate the exact current v3 packet and v3 return template, have the same genuine reviewer re-affirm the current fingerprints/labels, and use only privacy-safe opaque reference aliases in the returned repository-bound JSON.

Keep all real identifying credential evidence confidential outside Git.
