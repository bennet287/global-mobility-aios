# Global Mobility AIOS — V12.24 Outcome Evidence + Live Organization Programme

**Date:** 2026-08-22  
**Status:** DEVELOPMENT PROGRAMME OPEN / ACCEPTANCE NOT CLAIMED

## Parent checkpoint

V1.3-I.4 is COMPLETE / PASS / SEALED.

```text
technical candidate  46727cd130923f4ede825965cea3a011537a930b
Production Proof     32560318311 — 4/4 PASS
acceptance successor 793b15df26f188bfcf5b8a105c3a3333bee096f9
```

V12.24 does not reopen I.4 and does not authorize autonomy mutation.

## Development disposition

The project is shifting its immediate proof burden from additional governance architecture toward measured mobility usefulness and a real operating AI organization.

Canonical gate:

```text
docs/POST_I4_OUTCOME_AND_LIVE_ORGANIZATION_GATE_2026-08-22.md
```

Immediate priority:

```text
Outcome Evaluation foundation
→ J Agent Organization Runtime
→ K bounded Execution / Coworker Runtime
→ L Live Organization proof
→ curated mobility-domain evaluation
→ cost / latency / governance-overhead evidence
→ only then reconsider bounded autonomy mutation
```

## Plasma current-state reconciliation

Historical V12.19 documentation recorded Plasma PR #7 as draft/source-import-incomplete at that time.

Current repository truth is now:

```text
PR #7       MERGED
merge SHA   33425eb2b465b2dc14d9e43c556457e5135b626a
Wiki        1.2.0 pinned donor snapshot imported
Fractal     1.1.0 pinned donor snapshot imported
```

This is a current-state supersession, not a rewrite of the historical dated changelog entry.

Vendoring remains distinct from production adoption. Plasma still has no authority over AIOS Evidence, VerifiedRules, authority, autonomy, risk, Command Gateway decisions or canonical mobility state.

## First measurable engineering slice

V12.24 begins with a non-authorizing mobility outcome-evaluation harness in:

```text
apps/api/app/evaluations/mobility_outcomes.py
apps/api/tests/test_mobility_outcome_evaluation.py
```

Evaluation cases carry explicit provenance:

```text
SYNTHETIC
OFFICIAL_SOURCE_CURATED
PROFESSIONALLY_REVIEWED
HISTORICAL
LIVE_SHADOW
```

`OFFICIAL_SOURCE_CURATED` is intentionally distinct from professional review. Such a case must carry source provenance and cannot be represented as a professional/legal validation.

The harness preserves numerator and denominator rather than emitting a universal quality score. Unlabeled dimensions remain undefined rather than treated as success or failure.

Initial metric families:

```text
pathway identification
eligibility conclusion
evidence completeness / recall
missing-Evidence detection
contradiction detection
rule/source citation correctness
escalation correctness where labeled
```

Operational measurement also introduces risk-tiered Governance Amplification Factor:

```text
GAF = governed completion cost / minimally viable raw task cost
```

with risk-tiered p50/p95 latency, human/Board interventions, verifier calls and stale/retry counts.

## Austria official-source-curated seed

The first source-curated dataset is:

```text
apps/api/evaluations/mobility_cases/austria_rwr_shortage_2026_v1.json
```

Scope:

```text
Austria
Red-White-Red Card — Skilled Workers in Shortage Occupations
2026 source boundary
Software Engineer (DI) / data-processing shortage occupation example
```

The seed currently contains three synthetic-person fact patterns whose **labels are curated from current official Austrian sources**:

1. known absence of a binding Austrian job offer → current prerequisite fails;
2. strong route-specific facts/points → benchmark expects review rather than claiming an authority decision;
3. route identified but simplified points below the published 55-point minimum.

The source set is pinned in the dataset to Austrian government migration/administration pages. The dataset explicitly states `professional_review_status = NOT_REVIEWED`.

This is meaningful domain-evidence progress, but it is not yet a professionally validated gold set and does not establish live-case accuracy.

## Explicit non-claims

V12.24 does not yet claim:

- a professionally validated Austria benchmark;
- live-case correctness;
- a Live Organization;
- production Plasma adoption;
- autonomy mutation;
- automatic promotion/demotion;
- calibrated production economics.
