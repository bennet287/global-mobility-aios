# Technology Radar V1.3.6 R3 Labs

This tree contains isolated, synthetic experiments. Nothing here is production
architecture, canonical organization truth, authority, Evidence, Activity or an
accepted dependency merely because a lab passes.

```text
NO CANDIDATE SURVIVES ON THEORY ALONE.
NO CANDIDATE SURVIVES ON MOCKS ALONE.
NO TEST COUNT SUBSTITUTES FOR EVIDENCE DEPTH.

Aggressive on: uncertainty, adversarial testing, evidence and elimination.
Conservative on: production, credentials, personal data, authority and truth.
```

## Evidence-depth vocabulary

R3 labs use T0–T8 evidence tiers:

```text
T0 contract/mock/serialization
T1 real component correctness
T2 native feature depth
T3 stateful lifecycle
T4 adversarial/security
T5 chaos/failure/recovery
T6 concurrency/scale/property
T7 cross-component integration
T8 historical replay/restore/retirement
```

A lane is not "deep R3 verified" merely because many T0/T1 cases pass.

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

```bash
python -m pytest labs/r3/common/tests -q
python -m labs.r3.common.run_common --output .test-tmp/r3-common-results.json
python -m labs.r3.common.generate_fixtures --check
```

## Deep-proof rule

Mocks validate adapters. Real components validate components. Native feature
tests validate the reason the candidate exists. Lifecycle/chaos/property tests
validate resilience. Cross-lane tests validate architecture.

Security effects must eventually come from actual before/after state
measurements. A canned `ZERO_EFFECTS` contract is T0 smoke evidence only.

## Permanent boundaries

```text
CAN DO != MAY DO
SKILL != AUTHORITY
MEMORY != EVIDENCE
TELEMETRY != CANONICAL ORGANIZATION ACTIVITY
PROVIDER OUTPUT != AUTHORITY
R3 PASS != PRODUCTION ADOPTION
```
