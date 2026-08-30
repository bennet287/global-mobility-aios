# R3 Security Lane

Inspect AI, Promptfoo and garak will compete against the AIOS-owned attack corpus.
The first executable slice establishes the native target/measurement baseline over
all 18 categories. The primary metric is unauthorized canonical effects—not how
often a model says it refused.

```bash
python -m pytest labs/r3/security/tests -q
python -m labs.r3.security.run_corpus --output .test-tmp/security-baseline.json
```

This baseline is not evidence that the three external tools passed, nor that the
system is secure. It proves that every owned category has an executable fixture,
a severity, a fail-closed result, and zero-effect counters.


## Deep state-diff corpus

The original 18-category baseline remains a T0 contract smoke layer. The deep
corpus executes 36 concrete synthetic payloads across the same 18 categories and
derives effects from before/after state.

```powershell
python -m pytest labs/r3/security/tests -q

python -m labs.r3.security.run_deep_corpus `
  --run-id security-deep-20260830-003 `
  --output labs/r3/security/results/security-deep-20260830-003.json

python -m labs.r3.common.verify_results labs/r3/security/results/*.json
```

The deep target includes synthetic canonical state for ActionOutputs, external
actions, authority grants, VerifiedRules, Evidence, organization state, tenant
data and secrets. It uses canary/taint markers and computes unauthorized effects
from actual state deltas and response disclosure rather than assigning
`ZERO_EFFECTS`.

Current deep target evidence is still a disposable synthetic target. External
Inspect AI, Promptfoo, garak and cross-lane Authority/MCP integration remain
separate evidence requirements.
