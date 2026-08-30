# garak — AIOS Vulnerability-Scanner Research

**State:** RESEARCH / R2
**Reviewed pin:** `NVIDIA/garak@8ed1543b985a5722adb659584182faf6f7907d4e`
**License:** Apache-2.0
**Primary sources:** `https://github.com/NVIDIA/garak`, `https://reference.garak.ai/en/latest/`

## Fit

garak is an independent LLM vulnerability scanner with generators, probes, detectors, harnesses and evaluators. It covers prompt injection, jailbreaks, data leakage, misinformation, package hallucination and other model/system failure classes, and can target REST endpoints.

Best proposed role: independent scanner/challenger to expose failure classes not covered by the primary Promptfoo suite.

## Risks

- large probe sets can create cost, rate and harmful-content handling burden;
- model-focused detectors may not understand AIOS authority/evidence semantics;
- REST adapter configuration can overexpose a target;
- results require normalization, reproduction and human triage;
- overlap with Promptfoo may not justify maintaining both.

## R3 trigger

Run only after the Promptfoo reference suite exists. Select a small mapped probe subset against the identical disposable target, then measure unique findings, false positives, execution cost, maintenance and artifact quality.

## Decision

Retain as independent challenger. Do not adopt alongside Promptfoo without demonstrated non-overlapping value.
