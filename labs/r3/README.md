# Technology Radar V1.3.6 R3 Labs

This tree contains isolated, synthetic experiments. Nothing here is production
architecture, canonical organization truth, authority, Evidence, Activity or an
accepted dependency merely because a lab passes.

```text
NO CANDIDATE SURVIVES ON THEORY ALONE.

Aggressive on: uncertainty, adversarial testing, evidence and elimination.
Conservative on: production, credentials, personal data, authority and truth.
```

## Structure

```text
common/             versioned contracts, fixtures, assertions and evidence tools
authority/          OpenFGA, OPA and bounded challenger experiments
interoperability/   MCP, A2A and hostile-provider fixtures
security/           Inspect AI, Promptfoo and garak experiments
skills/             AIOS Skill Registry fixtures
observability/      OpenTelemetry experiments
secrets/            SecretsPort/OpenBao experiments
recovery/           backup, restore and PITR-style experiments
integration/        cross-lane stress scenarios
```

Every executable run must carry an `r3_run_id`, use synthetic data, emit a
machine-readable result first, and fingerprint its corpus, configuration and
results. A finding is an observation until independently reproduced and accepted.

## Common proof

From repository root:

```bash
python -m pytest labs/r3/common/tests -q
python -m labs.r3.common.run_common --output .test-tmp/r3-common-results.json
```

The committed corpora are generated deterministically:

```bash
python -m labs.r3.common.generate_fixtures --check
```

## Permanent boundaries

```text
CAN DO != MAY DO
SKILL != AUTHORITY
MEMORY != EVIDENCE
TELEMETRY != CANONICAL ORGANIZATION ACTIVITY
PROVIDER OUTPUT != AUTHORITY
R3 PASS != PRODUCTION ADOPTION
```
