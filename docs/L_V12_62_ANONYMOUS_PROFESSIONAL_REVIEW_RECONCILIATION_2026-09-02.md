# L — V12.62 Anonymous Professional Review Reconciliation

**Date:** 2026-09-02
**Branch:** `roadmap/global-mobility-aios-v12`
**Classification:** genuine blind professional-review evidence / current-fingerprint reconciliation candidate
**Milestone impact:** the external professional-review gate is satisfied; L remains `IMPLEMENTED / ACCEPTANCE PENDING` until this evidence head completes the final exact-head technical proof

## 1. Returned evidence

The same genuine independent Austria reviewer reaffirmed all three current v3 cases against the blind packet and exact source fingerprints.

The operator retains the real identity, qualification, independence and alias mapping outside Git. The repository contains only the approved non-identifying aliases:

```text
professional review  prof-ref-at-rwr-2026-v3-001
reviewer             rev-alias-at-2026-001
credential           cred-alias-at-2026-001
```

No personal name, registration number, contact detail, firm identity, address or public-profile URL is committed.

## 2. Fingerprint and contract validation

The returned `austria-professional-review-blind-return.v3` payload compiled into the canonical `mobility-professional-review-v1` bundle without translating or rewriting reviewer labels.

```text
source benchmark                         austria-rwr-shortage-2026-v1
source schema                            mobility-gold-v1
review batch                             at-rwr-v3-2026-0902-001
review count                             3
promoted count                           3
held / unreviewed                        0 / 0
confirmed / corrected                    0 / 3
disputed / needs more facts              0 / 0
independent review                       true on all three
```

All three fingerprints match the immutable current source benchmark:

```text
no job offer     sha256:45dca80bc3c4dc69056b0188b485b8451db392f0a0000d659bfeba0b50f7fd14
strong points    sha256:a77cd73ff22a782ebe974c0a7e6e570546638cc26940a80e654dfa79d8a7f2f2
under points     sha256:d216fc8b2188e43dcc9ae09c49cd968f42a4f000c23090d53ae3392d71b7422f
```

The immutable source benchmark remains `OFFICIAL_SOURCE_CURATED` / `NOT_REVIEWED`. The separate canonical review bundle promotes the reviewed cases to `PROFESSIONALLY_REVIEWED` provenance at compilation time.

## 3. Reconciliation outcome

The reviewer independently reached the same route-level eligibility directions as the source benchmark:

| Case | Reviewed outcome | Escalation |
|---|---|---|
| No binding job offer | `INELIGIBLE` | `false` |
| Strong points | `ELIGIBLE` | `false` |
| Under points | `INELIGIBLE` | `false` |

The compiler correctly derived `CORRECTED` rather than `CONFIRMED` because at least one complete label dimension differs in every case:

| Case | Professional correction |
|---|---|
| No binding job offer | `missing_evidence` is narrowed to `binding_job_offer`; source references are narrowed to §12a plus the route guidance. |
| Strong points | Source references retain the route, shortage-list, §12a, Annex B and 2026 regulation authorities, omitting the general application page. |
| Under points | Source references are narrowed to §12a and Annex B, the authorities material to the points failure. |

These differences are retained as professional corrections. They are not silently converted to confirmations and do not mutate the source-curated input file.

## 4. Durable repository evidence

The privacy-safe canonical bundle is committed at:

`apps/api/evaluations/professional_reviews/austria_rwr_shortage_2026_v1_review_2026_09_02.json`

Regression coverage proves that:

- the exact current bundle compiles;
- all three cases are promoted with `PROFESSIONALLY_REVIEWED` provenance;
- the correction count is three with no held or unreviewed cases;
- eligibility outcomes remain `INELIGIBLE / ELIGIBLE / INELIGIBLE`;
- the source benchmark remains immutable and `NOT_REVIEWED`;
- only the approved opaque aliases are present and common identifying metadata keys, email addresses and URLs are absent.

Focused reconciliation proof on the candidate source tree:

```text
36 passed / 1 existing Pydantic warning
```

Full local candidate proof:

```text
backend regression         1339 passed / 22 skipped / 1 existing warning
repository policy          PASS
release consistency        PASS — Alembic 0081 / Next.js 16.3.1
dependency constraints     PASS — 27 direct dependencies
diff hygiene               PASS
```

## 5. Remaining boundary

The professional-review gate is now satisfied. This record does not itself claim that the repository head is green.

L may be sealed only after the commit containing this canonical evidence and its regression coverage completes the repository policy and full V12 production proof at the exact current head. M remains blocked until that seal is recorded.
