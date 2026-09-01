# Global Mobility AIOS — Technology Radar Wave E3 Property / Invariant Testing

**Date:** 2026-08-31
**Status:** IMPLEMENTED / LOCAL-CI PROOF PENDING
**Classification:** SUPPORTING PARALLEL evaluation hardening
**Current product milestone:** L — Live Organization — IMPLEMENTED / ACCEPTANCE PENDING
**M milestone:** NOT STARTED

## 1. Purpose

Wave E3 advances the evaluation ladder from deterministic adversarial examples into generated property/invariant testing without creating a second evaluator stack.

The tranche uses Hypothesis only as test-generation infrastructure around AIOS-owned contracts. It does not become runtime authority, Evidence truth, professional-review authority, policy authority or organization truth.

```text
Wave E2 deterministic adversarial examples
→ Wave E3 generated property / invariant testing
→ later mutation testing
→ later fuzzing
→ later fault injection
→ later live-provider adversarial evaluation
```

## 2. Implementation

Added test dependency:

```text
hypothesis>=6.112
```

Added focused property suite:

```text
apps/api/tests/test_ai_domain_property_invariants.py
```

The suite directly exercises the existing first-party boundaries in:

```text
scripts/evaluate_austria_ai_domain_review.py
  _validate_provider_payload
  _corroboration_summary
```

No second provider adapter, evaluator runtime, benchmark store or business-truth system was introduced.

## 3. Generated invariants

The property suite generates bounded variations to prove the following contract properties:

1. arbitrary values other than literal `False` cannot escalate `final_authority_decision`;
2. arbitrary undeclared pathway identifiers fail closed;
3. arbitrary unknown source references fail closed;
4. arbitrary substituted case identifiers cannot escape the benchmark case set;
5. valid review input order is canonicalized back to the declared benchmark case order;
6. any number of repeated runs from one provider cannot manufacture independent corroboration;
7. a second provider must satisfy identity, structural-validity and source-label gates before corroboration can qualify;
8. cross-provider classification disagreement cannot qualify as corroboration;
9. every generated corroboration path retains `professional_review_status_effect = NONE`.

The suite intentionally focuses on invariant-heavy seams where generated data can expose gaps that one-example deterministic tests may miss.

## 4. Proof boundary

Wave E3 evidence must be labelled narrowly:

```text
Hypothesis-generated property/invariant test proof
!= exhaustive state-space proof
!= mutation-test strength proof
!= parser/input fuzz proof
!= live-model adversarial resistance
!= professional Austria correctness
!= operational Red Team proof
!= L acceptance
```

Hypothesis may shrink a failing generated example into a useful minimal counterexample. That counterexample remains engineering test evidence only.

## 5. Dependency and authority posture

Hypothesis is a bounded test dependency. It is not imported into first-party production runtime code.

Permanent boundaries remain:

```text
EVALUATOR SCORE != PROFESSIONAL CORRECTNESS
CAN DO != MAY DO
MEMORY != EVIDENCE
SECURITY FINDING != EXPLOITABILITY TRUTH
```

No product milestone or external production-adoption claim changes in this tranche.

## 6. Verification truth

The connected GitHub implementation session authored and pushed the dependency/test files but could not execute the repository Python environment itself. Therefore the repository does not yet claim a focused pytest PASS, full backend PASS, Woodpecker PASS or exact-current-head proof for Wave E3.

Canonical focused acceptance commands:

```powershell
python -m pip install -r apps/api/requirements.txt
python -m compileall -q apps/api/app scripts apps/api/tests/test_ai_domain_property_invariants.py
python -m pytest -q `
  apps/api/tests/test_ai_domain_review_cli.py `
  apps/api/tests/test_ai_domain_adversarial_contract.py `
  apps/api/tests/test_ai_domain_property_invariants.py
```

## 7. Current truth

```text
Technology Radar V1.3.7                  COMPLETE / ACTIVE CANONICAL RADAR
Wave E2 deterministic adversarial gate   IMPLEMENTED / LOCAL-CI PROOF PENDING
Wave E3 property/invariant testing        IMPLEMENTED / LOCAL-CI PROOF PENDING
Hypothesis runtime production adoption    NONE
professional Austria review               PENDING
final exact-current-head technical proof  PENDING
L                                          IMPLEMENTED / ACCEPTANCE PENDING
M                                          NOT STARTED
```

## 8. Next evaluation-hardening candidate

After Wave E3 receives local/CI proof, the next evidence-quality tranche should benchmark mutation testing on these same high-value validation/corroboration seams. The purpose is to determine whether the combined deterministic + property suite actually kills meaningful logic mutations rather than merely increasing test count or coverage.
