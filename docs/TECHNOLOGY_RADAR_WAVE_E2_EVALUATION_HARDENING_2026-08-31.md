# Technology Radar Wave E2 — Evaluation / Adversarial Contract Hardening

**Date:** 2026-08-31
**Branch:** `roadmap/global-mobility-aios-v12`
**State:** IMPLEMENTED / BOUNDED DEFENSIVE EVALUATION TRANCHE
**Production framework adoption:** NONE
**Professional-review effect:** NONE
**Red Team runtime effect:** NONE
**Milestone effect:** L remains IMPLEMENTED / ACCEPTANCE PENDING; M remains NOT STARTED

## 1. Why this tranche exists

The existing Austria AI-domain corroboration harness already moved beyond shallow mock-only confidence by using blind benchmark packets, fresh official-source retrieval, live configured providers, provider/model identity recording and cross-provider corroboration. However, deterministic regression coverage around the evaluation contract itself was still narrow.

Wave E2 strengthens that layer before introducing another evaluation framework. The purpose is not to claim that deterministic tests prove model correctness. The purpose is to make known classes of authority, provenance, consensus and prompt-boundary failure cheap to reproduce and impossible to silently regress.

Permanent evidence separation:

```text
unit / contract test
!= live-provider correctness

adversarial mutation gate
!= live-model prompt-injection resistance

AI corroboration
!= professional Austria review

security test knowledge
!= Red Team execution authority
```

## 2. Implemented scope

Added:

```text
scripts/check_ai_domain_adversarial_contract.py
apps/api/tests/test_ai_domain_adversarial_contract.py
```

The new deterministic gate imports the existing Austria blind-review contract rather than creating a second evaluator or mock provider stack.

It executes a positive baseline plus adversarial mutations covering:

1. attempted `final_authority_decision=true` authority escalation;
2. undeclared route/pathway substitution;
3. forged source references;
4. duplicate case substitution;
5. silent case omission;
6. invented authority-like classifications;
7. conclusions with no source references;
8. conclusions with no rationale;
9. single-provider pseudo-corroboration;
10. duplicate runs from the same provider pretending to be independent corroboration;
11. cross-provider classification disagreement;
12. provider/model identity mismatch;
13. structurally invalid provider output;
14. source-label/pathway mismatch;
15. a positive two-distinct-provider matching control;
16. indirect prompt-injection content embedded in a source excerpt.

The prompt-injection scenario verifies only the architecture boundary that hostile source instructions remain inside the untrusted source payload while the system prompt explicitly says not to follow embedded source instructions or claim a final legal decision. It deliberately does **not** claim that a live model is resistant to that attack.

## 3. Why this is stronger than shallow mocks

The prior shallow pattern is:

```text
mock provider
→ expected JSON
→ assertion passes
```

The target evaluation stack is layered:

```text
unit contracts
→ deterministic adversarial mutation
→ property / invariant testing
→ mutation testing / fuzzing
→ fault injection
→ real-provider evaluation
→ fresh-source evaluation
→ cross-provider disagreement testing
→ live prompt-injection / poisoned-context evaluation
→ authorization / replay / tenant-isolation attacks
→ concurrency/race proof
→ independent professional domain review
→ isolated Red Team / purple-team retest
→ continuous regression
```

Wave E2 implements only the deterministic adversarial-contract layer. The later layers must retain their own proof labels.

## 4. Aggressive Technology Radar direction

The Technology Radar should remain aggressive about discovery and benchmarking while production adoption remains necessity- and authority-gated.

The following evaluation/security candidates are therefore explicit future research/benchmark targets, not current dependencies or adoption claims:

| Capability | Candidate technologies / approaches | Current Wave E2 decision |
|---|---|---|
| AI regression / adversarial eval | Promptfoo | Existing pilot remains trial-eligible; extend rather than restart |
| LLM security scanning | Garak | RESEARCH / bounded live-model attack candidate |
| LLM adversarial orchestration | Microsoft PyRIT | RESEARCH / bounded isolated candidate |
| Evaluation metrics / datasets | DeepEval, Ragas-style retrieval/eval methods | RESEARCH / use only where metrics match an AIOS product question |
| Property-based testing | Hypothesis | BENCHMARK candidate for invariant-heavy Python domains |
| Mutation testing | mutmut / equivalent | RESEARCH / evaluate against high-value governance/evaluation modules |
| Python fuzzing | Atheris / property-guided fuzzing approaches | RESEARCH / bounded parser/contract targets |
| SAST | Semgrep, CodeQL | PRIORITY RESEARCH / CI security candidates |
| Container/IaC scanning | Trivy | PRIORITY RESEARCH / production-security candidate |
| SBOM / vulnerability correlation | Syft + Grype | RESEARCH / supply-chain evidence candidate |
| Build provenance | SLSA + Sigstore | RESEARCH / artifact provenance candidate |
| Secrets scanning | Gitleaks / equivalent | PRIORITY RESEARCH / repository-delivery candidate |
| API security | OWASP API Security testing/tooling | PRIORITY RESEARCH / FastAPI assurance candidate |
| LLM observability | Langfuse behind OpenTelemetry | RESEARCH / only if a measured LLM-specific observability gap exists |
| Isolated adversarial execution | Microsandbox | EXPLORE / post-L Red Team lab provider candidate |

The governing rule is:

> **Aggressive Radar. Conservative production authority.**

A candidate may be researched, benchmarked or attacked aggressively without becoming canonical runtime, organization truth, Evidence, authority, memory truth or a production dependency.

## 5. Red Team continuity

This tranche continues the existing V1.3.4/V1.3.5 Red Team programme rather than starting a duplicate architecture.

Existing programme truth remains:

```text
Red Team / adversarial architecture       STARTED
Cybersecurity donor evaluation            STARTED
Promptfoo bounded pilot                    COMPLETE / TRIAL-ELIGIBLE
Operational offensive Red Team runtime     NOT CLAIMED
Cybersecurity Skill Registry runtime       NOT CLAIMED
Microsandbox-backed execution lab          NOT CLAIMED
```

The new deterministic gate is a defensive precursor that can later become one input to the isolated lab. It does not create an `AdversarialEngagement`, grant network/credential scope, authorize offensive execution or change Command Gateway semantics.

## 6. Verification contract

Focused local commands for this tranche:

```text
python -m compileall -q scripts/check_ai_domain_adversarial_contract.py
python scripts/check_ai_domain_adversarial_contract.py
python -m pytest -q apps/api/tests/test_ai_domain_review_cli.py apps/api/tests/test_ai_domain_adversarial_contract.py
```

The GitHub-connected implementation session could validate Python syntax before push, but it cannot claim repository-environment pytest execution unless observed separately. Full local/CI proof remains required under normal repository acceptance rules.

## 7. Next hardening gates

The next evaluation-hardening steps should be selected by measured risk, not tool novelty. Strong candidates are:

1. turn the three-case Austria domain benchmark into a materially broader edge-case corpus before using it as a serious quality claim;
2. add live-provider adversarial variants with poisoned/contradictory source excerpts and explicit pass/fail security criteria;
3. add property/invariant testing for high-value governance/evaluation contracts;
4. benchmark mutation testing to measure whether the test suite actually kills meaningful logic mutations;
5. extend the existing Promptfoo pilot into continuous adversarial regression where it gives better coverage than first-party fixtures;
6. continue defensive cybersecurity-skill intake toward an AIOS-owned registry after the L gate permits it;
7. evaluate Garak/PyRIT only inside a bounded authorization and isolation model rather than adopting them because donor material mentions them.

Independent professional Austria review remains mandatory for professional correctness. Final exact-current-head technical proof remains mandatory before L can be sealed.
