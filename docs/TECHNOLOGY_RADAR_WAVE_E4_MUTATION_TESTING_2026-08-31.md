# Technology Radar Wave E4 — Mutation Testing

**Date:** 2026-08-31
**Branch:** `roadmap/global-mobility-aios-v12`
**Status:** IMPLEMENTED / LOCAL EXACT-HEAD PROOF OBSERVED AT `5d8e940e3e979b097e20bba1b6c002ba6a0d8d72`
**Product milestone effect:** NONE — L remains IMPLEMENTED / ACCEPTANCE PENDING; M remains NOT STARTED

## 1. Purpose

Wave E4 strengthens the Austria AI-domain evaluation seam by testing the tests themselves. Wave E2 mutates adversarial inputs and Wave E3 generates input properties; Wave E4 mutates selected implementation logic and requires the safety probes to detect those regressions.

The target remains deliberately narrow:

```text
scripts/evaluate_austria_ai_domain_review.py
```

The implementation is:

```text
scripts/check_ai_domain_mutation_strength.py
apps/api/tests/test_ai_domain_mutation_strength.py
```

## 2. Anti-duplication and engine decision

The current repository had no mutation-testing engine dependency or existing Wave E4 receipt before this tranche. The first-party validator/corroboration seam already provided the semantic boundaries to probe, so Wave E4 does not introduce another evaluator implementation.

`mutmut` was rechecked as the named Radar challenger before implementation. Public package metadata on 2026-08-31 showed current `mutmut` 3.7.0, Python >=3.10 and Python 3.13 classification. Its current documentation also states that mutmut 3 requires operating-system `fork` support and therefore must run under WSL when used on Windows.

Reference:

```text
https://pypi.org/project/mutmut/
```

Because the project's canonical local proof operator currently uses Windows PowerShell/CPython and Wave E4 only needs a bounded high-value mutation-strength gate, this tranche does **not** add mutmut to the dependency contract. A fork/WSL-only engine would add environment burden without being necessary to prove the selected evaluator invariants.

This is an evidence-based defer, not a rejection. `mutmut` remains a challenger for a broader Linux/CI mutation campaign if measured need justifies it.

## 3. Implemented mutation model

The first-party gate performs exact semantic source substitutions against the existing evaluator implementation, loads each mutated variant in isolation, and executes a focused probe whose baseline must pass and whose mutant must fail.

Declared mutation classes:

```text
weaken explicit false-only authority enforcement
invert pathway/review-scope enforcement
weaken mixed valid+forged source rejection
weaken normalized non-empty rationale enforcement
raise the distinct-provider corroboration threshold
weaken unanimity cardinality
weaken all-provider source-label agreement to any-provider agreement
weaken exact provider-identity qualification
```

A selected mutant is `KILLED` only when:

```text
baseline probe == safe/pass
mutated implementation probe == unsafe/fail
```

Any surviving selected mutant causes the gate to fail.

## 4. Local acceptance defect discovered and repaired

The first local Wave E4 run correctly failed instead of producing a false green result. The failure exposed a defect in the mutation-test oracle for the `invert-route-scope-guard` mutation.

The original route probe changed only the first review's pathway. Under the inverted guard, that invalid first review escaped the intended check, but the second untouched valid review was then rejected by the inverted condition. Because the probe only observed whether *any* `ValueError` occurred, the mutant incorrectly appeared safe and survived.

The repaired probe now changes the pathway on every review in the payload. Therefore:

```text
baseline implementation
→ rejects the all-invalid pathway payload

inverted route-scope mutant
→ cannot rely on a later untouched valid review to raise a false-positive error
→ the oracle can directly observe the weakened guard
```

This repair changes only the Wave E4 mutation-strength harness. Production evaluator logic, authority semantics, source validation and corroboration behavior are unchanged.

The failed local run is retained as useful evidence that the mutation gate itself was capable of refusing an invalid proof configuration. The repaired head was subsequently rerun locally at exact head `5d8e940e3e979b097e20bba1b6c002ba6a0d8d72` and passed the declared mutation gate, focused suite, full backend suite and repository gates documented below.

## 5. Why this is mutation testing rather than another input-mutation suite

Wave E2 changes provider outputs and checks that production validation rejects them. Wave E4 changes the implementation logic of the validator/corroboration code itself and checks that the safety test oracle notices the regression.

Therefore:

```text
Wave E2: bad input → production guard should reject
Wave E4: weakened production guard → test oracle should detect weakness
```

The two layers are complementary and must not be conflated.

## 6. Proof boundaries

```text
bounded semantic mutation strength
!= exhaustive mutation coverage
!= statement/branch coverage
!= fuzzing
!= live-model adversarial resistance
!= professional Austria correctness
!= operational Red Team proof
!= L acceptance
```

The gate is intentionally deterministic and limited to the highest-value Austria AI-domain authority/corroboration seams. It does not claim that every function or every possible mutation in the repository has been exercised.

`professional_review_status_effect` remains `NONE`.

## 7. Canonical local proof

From repository root after installing the constrained Python dependency set:

```powershell
python -m compileall -q apps/api/app scripts apps/api/tests
python scripts/check_ai_domain_adversarial_contract.py
python scripts/check_ai_domain_mutation_strength.py
python -m pytest -q `
  apps/api/tests/test_ai_domain_review_cli.py `
  apps/api/tests/test_ai_domain_adversarial_contract.py `
  apps/api/tests/test_ai_domain_property_invariants.py `
  apps/api/tests/test_ai_domain_mutation_strength.py
python scripts/check_repo_policy.py --root .
python scripts/check_release_consistency.py --root .
python scripts/check_python_dependency_constraints.py
python scripts/check_diff_hygiene.py
```

Observed local exact-head proof at `5d8e940e3e979b097e20bba1b6c002ba6a0d8d72`: Wave E2 adversarial contract PASS 17/17; Wave E4 mutation gate PASS with 8/8 selected mutants killed and 0 survived; focused suite PASS 25 tests; full backend PASS 1328 passed / 22 skipped; repository policy, release consistency, Python dependency constraints and diff hygiene all PASS. GitHub Actions failure labels for this head corresponded to jobs with zero executed steps / no runner identity and therefore remain infrastructure/runner-startup evidence, not repository-test failure.

## 8. Current evaluation ladder

```text
Wave E2 deterministic adversarial input mutation     implemented / locally proven at historical head 285a7f08...
Wave E3 property/invariant testing                    implemented / locally proven at historical head 285a7f08...
Wave E4 implementation mutation strength              implemented / repaired / locally proven at 5d8e940e...
next bounded candidate                                fuzzing
```

The professional Austria review remains the independent L acceptance gate and is not replaced by any evaluation-hardening wave.
