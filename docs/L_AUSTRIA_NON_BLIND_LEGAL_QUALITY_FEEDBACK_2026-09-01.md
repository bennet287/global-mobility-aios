# L — Austria Non-Blind Legal-Quality Feedback Reconciliation

**Date:** 2026-09-01
**Branch:** `roadmap/global-mobility-aios-v12`
**Classification:** useful legal-quality feedback / NOT professional-review acceptance evidence
**Milestone impact:** L remains `IMPLEMENTED / ACCEPTANCE PENDING`; M/N remain `NOT STARTED`

## 1. Feedback received

A legal-quality assessment of the three Austria shortage-occupation benchmark cases concluded that the route-level directions were substantively sound:

```text
no Austrian job offer   → INELIGIBLE on stated facts
strong-points case      → REVIEW_REQUIRED
under-points case       → INELIGIBLE on stated facts
```

It also raised four material quality points:

1. `missing_evidence: []` in the strong-points case could be misread as documentary completeness;
2. asserted work experience should not be confused with documented qualification-matching experience accepted by AMS;
3. asserted completed training should not be confused with qualification/document acceptance;
4. the benchmark should cite direct RIS authorities for the 2026 Fachkräfteverordnung and AuslBG points/statutory requirements.

## 2. Why this assessment does not satisfy L professional review

The assessment explicitly states that the supplied packet was an obsolete answer-revealing v1 format and that expected labels/rationale were visible.

Therefore:

```text
useful legal-quality feedback
!= blind independent professional review
!= professionally reviewed benchmark tranche
!= L acceptance evidence
```

No reviewer identity, credential, independence or professional-review evidence is promoted by this record.

The benchmark remains:

`professional_review_status = NOT_REVIEWED`

## 3. Official-source verification

The feedback was cross-checked against current official Austrian sources.

Direct statutory sources now included in the benchmark:

```text
AuslBG § 12a
https://www.ris.bka.gv.at/eli/bgbl/1975/218/P12a/NOR40257948

AuslBG Anlage B
https://www.ris.bka.gv.at/eli/bgbl/1975/218/ANL2/NOR40252045

Fachkräfteverordnung 2026 § 1
https://www.ris.bka.gv.at/eli/bgbl/II/2025/316/P1/NOR40274302
```

Existing official guidance retained:

```text
migration.gv.at skilled workers in shortage occupations
migration.gv.at 2026 Austria-wide shortage occupations
oesterreich.gv.at RWR shortage-occupation application guidance
```

The verified legal direction is:

- relevant completed training must be proven;
- the statutory minimum-points requirement applies;
- qualifying work experience for Annex B is qualification-matching and capped at 20 points;
- intended employment must meet the statutory remuneration requirement;
- the 2026 shortage regulation contains the nationwide graduate-engineer/data-processing category, while the official migration list maps `Software Engineer (DI)` into that category;
- AMS assesses the labour-market-side requirements and the residence authority remains responsible for the remaining residence-title requirements.

## 4. Benchmark semantic hardening

The three outcome directions are retained.

The benchmark claim boundary now explicitly states:

```text
asserted scenario fact != authenticated document
asserted qualification != authority-accepted qualification evidence
asserted work experience != verified qualification-matching employment evidence
missing_evidence=[] != complete real application file
required_evidence taxonomy != exhaustive residence-document checklist
route-level benchmark outcome != final authority entitlement
```

Each case now carries an immutable-fingerprint-bound `fact_evidence_boundary` that is shown to the blind reviewer.

The strong-points rationale now makes the arithmetic explicit:

```text
training      30
experience    20 (10 asserted years, capped)
age 29        15
approx total  65
```

but keeps the canonical label `REVIEW_REQUIRED` because actual documents and authority assessment remain outstanding.

## 5. Reviewer-handoff stale-file protection

The current reviewer-facing packet remains:

`austria-professional-review-handoff.v2`

It now explicitly declares:

```text
reviewer_facing_packet = true
supersedes reviewer handoff v1
blind_review = true
expected_labels_excluded = true
source_rationale_excluded = true
```

and instructs the operator/reviewer to reject answer-revealing legacy v1 packets.

## 6. Fingerprint consequence

Adding direct RIS sources and fact-evidence semantics changes the immutable source-case fingerprints.

Therefore all previously generated professional-review packet/return artifacts are stale.

Before contacting a real reviewer:

1. prove the V12.55 focused professional-review suite locally;
2. regenerate a fresh v2 blind packet;
3. regenerate the blank blind return template;
4. verify the packet contains no expected labels/rationale;
5. send only those fresh artifacts to the qualified independent reviewer.

## 7. Acceptance boundary

This tranche improves benchmark quality and reviewer independence.

It does **not** mean:

```text
professional Austria review complete
reviewer identity verified
reviewer credential verified
three cases professionally promoted
L accepted
L sealed
M started
```

The next release-critical external gate remains a genuine blind independent Austria professional review using the fresh current-head v2 handoff.
