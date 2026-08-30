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
