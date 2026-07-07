# Truth Engine Specification

## Purpose
Prevent hallucinated, misleading, or dangerous visa/job/study guidance.

## Required Inputs

- claim
- domain
- country
- source URLs
- retrieved date
- source type

## Verdicts

- VERIFIED: supported by official or trusted sources
- REJECTED: contradicted, high-risk, or unsafe
- NEEDS_REVIEW: insufficient evidence or sensitive case

## Confidence Policy

| Condition | Confidence |
|---|---:|
| Official source + no red flags | 0.75–0.90 |
| Official source + sensitive domain | 0.70–0.85 + review |
| No official source | 0.20–0.45 |
| High-risk phrase | reject with 0.90+ |

## High-Risk Claims

- Guaranteed visa
- 100% job placement
- Work visa without employer when not officially supported
- Fake documents
- Embassy bypass
- Agent contacts or secret channels

## Output Contract

Every client-facing answer must include:

- answer summary
- source URL
- access date
- country
- confidence
- assumptions
- human-review flag
