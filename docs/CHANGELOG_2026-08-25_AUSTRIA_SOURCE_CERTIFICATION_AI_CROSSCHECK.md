# 2026-08-25 — Austria 2026 Source-Certification AI Cross-Check

## Status

**SUPPLEMENTARY REVIEW EVIDENCE + REVIEW-PACK INTEGRITY TOOLING — L REMAINS IMPLEMENTED / ACCEPTANCE PENDING**

This change records the five-model cross-check of the Austria 2026 nationwide shortage-occupation source-certification reviewer packet and adds a deterministic exported-pack integrity checker.

Delivered:

- `docs/L_AUSTRIA_2026_SOURCE_CERTIFICATION_AI_CROSSCHECK_2026-08-25.md`
  - records Claude Sonnet 5, DeepSeek, Grok 4, Kimi K2.5, and Perplexity results without converting AI output into human evidence;
  - preserves conflicting evidence instead of majority-voting it away;
  - records the attached Kimi result as one #7 double-space normalization mismatch;
  - records the attached Perplexity result as eight reported mismatches while distinguishing the items its own explanation calls source-faithful/non-errors from the unresolved #7 whitespace, #28/#38/#51 snapshot-punctuation, and #49 structural interpretation concerns;
  - re-checks the official source's 2026 scope, 64 groups, #7 concatenation/live single-space rendering, and #49 period/title-boundary artifact;
  - explicitly rejects any attempt to treat an AI review as `independent_human_attestation`;
  - records that the exported v1 packet cannot independently reproduce the full `evidence_pack_sha256` because it does not expose the complete internal canonical-evidence input.
- `scripts/check_austria_source_certification_review_pack.py`
  - validates Austria / 2026 / national / 64 rows;
  - validates contiguous ordinals;
  - recomputes the ordered entry-set hash;
  - recomputes the source-content-text hash;
  - validates pinned snapshot-content-hash agreement;
  - reports the evidence-pack-hash reproducibility boundary instead of overstating proof.
- `apps/api/tests/test_austria_source_certification_review_pack_check.py`
  - covers successful deterministic recomputation;
  - accepts the existing reviewer-handoff wrapper shape as well as the raw review pack;
  - rejects changed entry-set hashes;
  - rejects changed source-text hashes;
  - rejects projections that do not contain exactly 64 Austria-wide 2026 groups.

The exact immutable reviewer packet itself is not committed to the repository or available as a current conversation/library file, so the new checker has not been claimed as run against that packet in this commit. The operator command remains documented for the local pinned packet.

No canonical shortage-occupation row, source snapshot, certification decision, migration schema, or external-action authority changes in this slice.

No AI output in this change is professional review, legal advice, human identity verification, or human attestation.
