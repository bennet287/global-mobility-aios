# R3 Security Evidence — Native Execution Baseline

**Date:** 2026-08-30

**Status:** NATIVE BASELINE PASS / EXTERNAL TOOL EXECUTION PENDING

**Technical candidate:** `1e15b2bfd2c9d7aa241a58644ecbcef99dab5837`

All 18 AIOS-owned adversarial categories executed with zero unauthorized
canonical effects. The machine result is:

```text
security-baseline-20260830-002.json
embedded result SHA-256:
12b2d7b67780a37122f91e17e5184c2588dfc9398f2e8d2c130717d19aa6f8bd
```

This proves the owned taxonomy, severity inputs, denial classes and zero-effect
measurement are executable. It does not prove production security or any external
tool. Inspect AI, Promptfoo and garak have not run against this target yet.

Disposition:

```text
CONTINUE_R3_WITH_SPECIFIC_GAP

trigger:
execute the retained corpus through isolated pinned Inspect AI, Promptfoo and
garak adapters, then compare overlap, unique findings and operational cost.
```
