# L — Austria Preliminary Blind Return Reconciliation

> **Superseding operator correction (V12.58):** the review itself was genuine and independent. The earlier `independent_review=false` values were operator transcription mistakes. This document remains useful for the v2 label-contract/fingerprint analysis, but its statements that the review was non-genuine/non-independent are superseded by `docs/L_AUSTRIA_GENUINE_BLIND_REVIEW_OPERATOR_CORRECTION_2026-09-01.md`. Null reviewer/professional/credential references remain structurally unresolved.

**Date:** 2026-09-01
**Branch:** `roadmap/global-mobility-aios-v12`
**Classification:** blind current-fingerprint draft feedback / NOT professional-review acceptance evidence
**Milestone impact:** L remains `IMPLEMENTED / ACCEPTANCE PENDING`; M/N remain `NOT STARTED`

## 1. Return received

A reviewer-style return was supplied against the fresh V12.55 blind packet.

The three source fingerprints in the return exactly matched the then-current V12.55 source fingerprints:

```text
case 1  sha256:45dca80bc3c4dc69056b0188b485b8451db392f0a0000d659bfeba0b50f7fd14
case 2  sha256:40702176f288522de5f42fdfc5c2c12bf2ebd4e9d27afd07cd9d438cb1b9d161
case 3  sha256:d216fc8b2188e43dcc9ae09c49cd968f42a4f000c23090d53ae3392d71b7422f
```

So this draft was based on the current blind source material rather than the obsolete answer-revealing v1 packet.

## 2. Why the return is not acceptance evidence

The return explicitly states that it is a preliminary route-evaluation draft for later review by a credentialed Austrian immigration practitioner.

Its structured fields also fail the canonical professional-review acceptance boundary:

```text
professional_review_reference       null on all three cases
reviewer_reference                  null on all three cases
reviewer_credential_reference       null on all three cases
independent_review                  false on cases 1 and 3
```

The compiler requires non-empty structural references for promotable review records, and CONFIRMED/CORRECTED reviews require `independent_review=true`.

Therefore:

```text
current-fingerprint blind draft
!= credentialed independent professional review
!= professionally reviewed benchmark promotion
!= L acceptance evidence
```

No supplied identity, title or unsigned "Immigration Counsel" label is treated as credential evidence.

## 3. Legal conclusions in the draft

The draft concluded:

```text
Case 1  INELIGIBLE
Case 2  ELIGIBLE
Case 3  INELIGIBLE
```

The route-level legal direction was cross-checked against current official Austrian sources.

For skilled workers in shortage occupations, the official migration guidance requires:

- completed training in the shortage occupation;
- a binding Austrian job offer with the applicable minimum remuneration; and
- at least 55 points.

AuslBG Anlage B gives 30 points for completed training, up to 20 for qualification-matching work experience, and 15 points for age under 30.

On the asserted facts:

```text
Case 1
no binding job offer
→ mandatory route criterion fails
→ INELIGIBLE

Case 2
training 30
10 asserted qualification-matching years → capped 20
age 29 → 15
total 65
binding job offer + remuneration asserted
→ mandatory route criteria satisfied on stated facts
→ route-level ELIGIBLE

Case 3
training 30
experience 0
language 0
age 51 → 0
total 30
→ below 55
→ INELIGIBLE
```

Route-level `ELIGIBLE` does not mean documentary authentication, AMS confirmation, residence-authority approval, submission authority or final issuance.

## 4. Handoff-contract defect exposed by the draft

Although the v2 packet withheld expected labels/rationale correctly, it did not define enough canonical label semantics.

The draft therefore used:

- `rwr-card-shortage-occupation` instead of the AIOS canonical tested route key;
- full application-document names inside `required_evidence` instead of the bounded benchmark evidence taxonomy;
- prose legal citations rather than canonical `official_sources[].ref` identifiers;
- `null` for contradictions where the benchmark distinguishes "not assessed" from "assessed and none";
- `escalation_required=true` for an alternative-route recommendation in Case 1, while AIOS uses escalation for unresolved tested-route classification;
- `ELIGIBLE` for Case 2 while the source benchmark had conflated normal downstream verification with `REVIEW_REQUIRED`.

That means a mechanical v2 comparison would derive broad CORRECTED differences even where the underlying legal conclusion is aligned.

## 5. V12.57 correction

The reviewer-facing handoff is advanced to:

`austria-professional-review-handoff.v3`

v3 explicitly defines:

### Eligibility

```text
ELIGIBLE
  mandatory legal criteria for the tested route are satisfied on asserted facts;
  does not imply document verification, AMS/residence approval or final issuance

INELIGIBLE
  at least one mandatory tested-route criterion fails on asserted facts

INSUFFICIENT_INFORMATION
  asserted facts are insufficient to determine the tested-route result

REVIEW_REQUIRED
  a material legal classification/interpretation remains unresolved even after
  accepting the asserted facts; not merely because routine downstream review exists
```

### Canonical route

For this tranche:

`at-rwr-skilled-worker-shortage-occupation`

Alternative-route recommendations belong in notes. If the tested route framing itself is professionally wrong, use `DISPUTED`.

### Bounded evidence taxonomy

```text
shortage_occupation_training
binding_job_offer
applicable_minimum_remuneration
points_evidence
```

Full application-document checklists may be recorded in notes, not substituted for benchmark label keys.

### Contradictions

`[]` means assessed and none found.

`null` is not permitted for a complete `ASSESSED` return.

### Rule/source refs

Use the canonical `official_sources[].ref` values supplied in the packet.

### Escalation

`true` means the tested route-level result itself requires escalation because a material ambiguity remains.

Routine authority review or a suggestion to explore another route does not by itself make escalation true.

## 6. Benchmark correction

The source benchmark strong-points case is corrected from:

```text
eligibility          REVIEW_REQUIRED
escalation_required  true
```

to:

```text
eligibility          ELIGIBLE
escalation_required  false
```

This separates:

```text
route eligibility
!= documentary verification
!= authority approval
!= governance permission
```

The other two eligibility results remain unchanged.

## 7. Full-backend stale-oracle repair

V12.55 added direct RIS sources, but `test_mobility_outcome_evaluation.py` still allowed only migration.gv.at and oesterreich.gv.at domains.

That stale oracle is corrected to permit `www.ris.bka.gv.at` and to assert the new route-level strong-case result.

No source-authority requirement is weakened.

## 8. Fingerprint consequence

Changing the strong-case expected labels/rationale changes its source fingerprint.

Therefore:

- the V12.55 v2 packet is now historical/stale;
- the preliminary return documented here is historical draft feedback only;
- all current reviewer artifacts must be regenerated from V12.57;
- the genuine credentialed reviewer must receive only the new v3 packet and fresh blind-return template.

## 9. Current gate

Before genuine reviewer handoff:

1. run the focused professional-review tests plus `test_mobility_outcome_evaluation.py`;
2. run repository gates;
3. regenerate a fresh v3 packet;
4. regenerate a fresh blind-return template;
5. verify the v3 label contract is present and no source labels/rationale are exposed;
6. only then send the artifacts to the credentialed independent reviewer.

L remains open until a genuinely independent credentialed review is returned and reconciled.
