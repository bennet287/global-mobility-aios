# Phase 13.15 Round 6 Correctness Disposition

**Disposition date:** 2026-08-13
**Review mode:** Internal shadow validation; not genuine external-human acceptance
**Repository branch:** `roadmap/global-mobility-aios-v11`
**Repository baseline:** `dc22e7b2db4343bfaad702ebf53a2f9e5946e968`

## Deterministic disposition

> **ROUND 6 CORRECTNESS DISPOSITION: PASS**

Round 6 found zero Critical findings, zero High findings, and zero unsupported
legal certainty. The Phase 13.15 Round 6 correctness gate is complete. Phase
13.16.0 is **UNLOCKED / NOT STARTED**; the Medium and Low experience findings
recorded below are formal inputs to that work.

- **Critical correctness findings:** 0
- **High correctness findings:** 0
- **Unsupported legal certainty:** 0

This disposition does not complete Phase 13. Genuine external-human acceptance
remains mandatory in Phase 13.17 after Phase 13.16.10 integrated acceptance.
Phase 14 remains locked.

## Scope and review separation

Round 6 used a fresh synthetic Austria skilled-employment case and two separate
shadow-review perspectives:

1. A mobility-user review of the rendered end-to-end decision experience.
2. A professional review of legal certainty, traceability, lifecycle, and
   decision integrity.

These sessions were internal shadow validation. They are correctness evidence,
not a substitute for the distinct genuine external-human acceptance required by
Phase 13.17. No implementation, remediation, certification approval, publication,
or external action was performed as part of this disposition.

## Pinned case and persona

| Item | Pinned value |
|---|---|
| Case reference | `AT-1D68AB41` |
| Lead ID | `1d68ab41-c0b6-4e6d-bca7-b016ca991188` |
| Mobility profile | `aaa0ad1f-5872-4d0b-8ac8-76f64f430bee`, version 1 |
| Pathway comparison | `7b11c34b-0c5a-4860-b9b4-98821c8e1ca1` |
| Primary pathway | `5f1a3fb4-a5bb-4ab7-b350-e77958d9ef7b` |
| Primary pathway name | Austria Red-White-Red Card - Skilled Worker in a Shortage Occupation |
| Pathway version | v4, ID `4f02f390-1e22-4ac3-9237-8a67f6551807` |

The comparable persona was India to Austria for skilled employment as a
Software Engineer, with four years of experience, no Austrian job offer,
qualification recognition unknown, German A2, and province unknown.

## Review results

### Mobility-user shadow review

**Result: PASS WITH MEDIUM/LOW EXPERIENCE FINDINGS.**

The rendered journey preserved the binding job-offer blocker, conditional
occupation assessment, evidence provenance, draft lifecycle, pending-review
certification state, excluded-route boundary, and non-production warning. No
Critical or High correctness issue was found.

### Professional shadow review

**Result: PASS WITH MEDIUM/LOW FINDINGS.**

All 21 professional-review matrix checks passed. The review found no unsupported
legal certainty and no Critical or High correctness issue. The exact pinned case
also had rendered evidence from the mobility-user session; the professional
session's correctness checks used the live API, read-only PostgreSQL evidence,
and frontend-code inspection because that session had no browser backend.

| # | Professional correctness check | Result |
|---:|---|---|
| 1 | Correct candidate family | PASS |
| 2 | Binding job offer correctly blocking | PASS |
| 3 | Employer declaration correctly separate | PASS |
| 4 | Safe national occupation conditionality | PASS |
| 5 | Safe regional occupation handling | PASS |
| 6 | Qualification uncertainty preserved | PASS |
| 7 | EUR 218 government fee correct | PASS |
| 8 | Estimated total cost safely unresolved | PASS |
| 9 | 14 canonical evidence gaps | PASS |
| 10 | Profile provenance present | PASS |
| 11 | Rule traceability present | PASS |
| 12 | Official-source traceability present | PASS |
| 13 | Immutable snapshot traceability present | PASS |
| 14 | National certification state correct | PASS |
| 15 | Regional certification state correct | PASS |
| 16 | Draft lifecycle correct | PASS |
| 17 | Production recommendation false | PASS |
| 18 | Publication readiness false | PASS |
| 19 | Draft/non-production boundary intact | PASS |
| 20 | Human-review gate intact | PASS |
| 21 | Unsupported legal certainty = 0 | PASS |

## Material decision state

- The primary pathway remains `draft` and `simulation_candidate` under the
  `INTERNAL_SIMULATION_ONLY` boundary.
- Production use is `false`; simulation use is `true`; publication readiness is
  `false`.
- The application fee is EUR 218. Total cost remains `not_established`.
- Overall and national occupation results are `AMBIGUOUS`.
- Regional occupation status is `INSUFFICIENT_INFORMATION` because the province
  is unset.
- Qualification recognition is `UNRESOLVED`.
- The Austrian job offer is `ABSENT` and remains a binding blocker. The result is
  not an eligibility determination; `establishes_pathway_eligibility` is `false`.
- The employer declaration remains a separate required document.
- The canonical response contains 14 evidence gaps and four next actions.
- Self-employment is excluded and contributes no projected cost.
- Obsolete optional-job-offer wording occurrences: 0.
- Incorrect EUR 21,800 fee displays: 0.

## Material traceability

| Conclusion or evidence role | Governed identifiers and state |
|---|---|
| Binding job-offer rule | Rule `9f14ed99-f70b-4772-97ae-fafe480d8699` |
| Employer-declaration rule | Rule `8bae83eb-2d1a-4c76-a10b-6698fcdc1c62` |
| Application-fee rule | Rule `36f6d9a7-57b7-4118-b089-449eded0d815` |
| Core pathway evidence | Source `2b070454-f22a-4bcf-b445-70563dd6e411`, “Austria Skilled Workers in Shortage Occupations”; snapshot `2df5b927-c381-4991-9f2a-471ebe8b06c8`; snapshot hash `02003039de782fada9e11d3fa542d69970a118507fc0b3ac74b58f1c66227f61`; certification `3b6d6ecf-7cd9-4eee-9cdf-fb34fed56799` (`approved`) |
| 2026 national occupation evidence | Source `1a589f02-d5c7-4307-807e-a255f630be1f`; snapshot `a1032556-81f1-49bf-acd6-fa8f43e45341`; snapshot hash `4115fd29a61b85d18f9189e8d888f77eaa0a9c3919264cef1c244e9437e41773`; entry-set hash `43f1b9fad49777a89da280395124a6d3e4608219b835d144765f47e148d00301`; certification `599f7ce7-b85e-4d02-b3ca-ea17b75aba84` (`pending_review`) |
| 2026 regional occupation evidence | Source `fdd2bc64-56b1-4150-b97d-b1b6c0525756`; snapshot `7a3503f3-dc9d-4ded-bf31-7a80738b7434`; snapshot hash `418cd6d19d5f22cf4221d7cd5b5715c6820fc80892a6df7d6d4271ee0bf2e977`; entry-set hash `5fd467b7bb3d1681dcf90f604d648af83483dfec443e4ae1d6bc5faf8e7bc238`; certification `f4cf5f04-0519-4cad-b5c2-88ec1183ded5` (`pending_review`) |

The core pathway certification is already approved. That approved core
certification must not be conflated with the national and regional 2026
occupation certifications, which remain `pending_review` and continue to block
publication. The official core source is
<https://www.migration.gv.at/index.php?id=1050>.

## Findings carried into Phase 13.16

| Finding | Severity | Category | Disposition and required experience input |
|---|---|---|---|
| `R6-MU-01` | Medium | Experience/presentation | The 35% overall score and 60% confidence can resemble an approval probability. Clarify score semantics and explicitly distinguish decision-support scoring from eligibility likelihood. |
| `R6-MU-02` | Medium | Experience/presentation | Draft, simulation, certification, and publication terminology is dense. Establish a plain-language status hierarchy while retaining every warning and governed state. |
| `R6-MU-03` | Low | Experience/presentation | Published-only messaging appears adjacent to the draft toggle. Distinguish internal simulation behavior from production availability more directly. |
| `R6-MU-04` | Low | Experience/presentation | The long document inventory competes with the binding job-offer blocker. Prioritize blockers and next actions before secondary document detail. |
| `R6-PRO-001` | Low | Operational evidence | The professional session lacked a browser backend. Include a focused professional rendered check during experience acceptance; this does not invalidate the API, read-only data, code, and mobility-user rendered evidence used in Round 6. |
| `R6-PRO-002` | Low | Experience/presentation | The excluded self-employment pathway appears under “Other plausible routes.” Separate excluded routes or rename the presentation so exclusion cannot imply plausibility. |

These findings do not override the correctness PASS. They are prioritized,
traceable acceptance inputs for Phase 13.16 and must be reassessed through its
integrated experience work.

## Gate evaluation

| Gate condition | Round 6 evidence | Result |
|---|---|---|
| Zero Critical/High correctness findings | Critical 0; High 0 across both reviews | PASS |
| Zero unsupported legal certainty | Professional review count 0 | PASS |
| Safe candidate family and occupation conditionality | Skilled-employment candidate retained; self-employment excluded; national ambiguity and province-dependent regional insufficiency preserved | PASS |
| Credible material gaps and costs | Binding offer absent; 14 canonical gaps; EUR 218 fee; total not established; excluded route contributes no cost | PASS |
| Accurate lifecycle and certification state | v4 draft, simulation only, not publication-ready; core approved; national/regional pending review | PASS |
| Production/draft boundary intact | Production false; simulation true; internal-simulation warning retained | PASS |
| Material conclusions traceable | Rules, sources, snapshots, hashes, certifications, profile, comparison, and pathway are pinned | PASS |

## Consequences and non-effects

- Phase 13.15 Round 6 is complete with a correctness disposition of PASS.
- Phase 13.16.0 is unlocked and is the next implementation slice, but it has not
  started in this documentation-only disposition.
- Phase 13 remains open. Phase 13.17 genuine external-human acceptance remains a
  mandatory later gate.
- Phase 14 remains locked until Phase 13 acceptance and measured scale demand
  justify it.
- Austria pathway v4 remains draft, unpublished, and not publication-ready.
- The national and regional occupation certifications remain `pending_review`.
- The already-approved core pathway certification remains approved; no
  certification state changed.
- No validation-ledger record, database row, runtime behavior, assessment,
  certification, or publication state was created or modified by this
  documentation-only disposition.
