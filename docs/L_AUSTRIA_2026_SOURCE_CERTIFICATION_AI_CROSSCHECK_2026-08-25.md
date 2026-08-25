# L Austria 2026 Primary-Source Certification — Five-Model AI Cross-Check

**Date:** 2026-08-25  
**Status:** SUPPLEMENTARY AI EVIDENCE ONLY / INDEPENDENT HUMAN ATTESTATION NOT SATISFIED  
**Milestone:** L — Live Organization  
**Official source:** https://www.migration.gv.at/en/types-of-immigration/permanent-immigration/austria-wide-shortage-occupations/  
**Target projection:** Austria / 2026 / national / 64 occupation groups

## Purpose

This record preserves the independent AI cross-check requested before a genuine human reviewer makes the governed Austria primary-source certification decision.

The five model reports are **decision support only**. None of them may set or imply `independent_human_attestation=true`, and none may substitute for the separate L professional-review benchmark tranche. The source-certification decision remains pending until a genuine separate human reviewer personally checks the immutable source snapshot and structured projection and submits the existing governed attestation contract.

## Inputs reviewed

The cross-check compared the exported Austria source-certification review packet against the official migration.gv.at Austria-wide shortage-occupation page. The review criteria were:

- correct source year and nationwide scope;
- exactly 64 top-level shortage-occupation groups in source order;
- no missing, extra, merged, or split top-level groups;
- exact occupation-group and alias text, including source-native spelling anomalies;
- preservation of the source's unusual formatting artifacts;
- no inference of person-level immigration eligibility.

## Model-result matrix

| Model | Reported groups | Reported result | Reported mismatches | Confidence | Material note |
| --- | ---: | --- | ---: | ---: | --- |
| Claude Sonnet 5 | 64 / 64 | `EXACT_MATCH` | 0 | 95 | Treated the #7 concatenation and #49 punctuation as source-native artifacts. |
| DeepSeek | 64 / 64 | `EXACT_MATCH` | 0 | 100 | Reported the same source-native anomalies. Any wording presenting this AI output as a human review is invalid. |
| Grok 4 | 64 / 64 | `EXACT_MATCH` | 0 | 98 | Reported line-by-line equality, including source-internal concatenations and punctuation, and stated that the live page matched the packet snapshot/content hash. |
| Kimi K2.5 | 64 / 64 | `MISMATCH` | 1 | 98 | Reported one #7 whitespace normalization: two spaces between `Kinder` and `und` in the immutable snapshot versus one space in the structured alias/live page. It also could not independently recompute the entry-set/evidence-pack hashes from the packet alone. |
| Perplexity | 64 / 64 | `MISMATCH` | 8 reported | 88 | Reported #7 whitespace, #28/#38/#51 snapshot-punctuation differences, and a #49 merge interpretation. Its count also includes #7 concatenation and #60/#61 spellings that its own explanation calls source-faithful/non-errors. |

The useful consensus is narrower than “five exact matches”: all five reports support the 2026 nationwide scope, all 64 top-level groups, the ordinal order, and no missing/extra top-level group. The exact-rendering reports conflict and must be adjudicated rather than majority-voted.

## Official-source re-check on 2026-08-25

A fresh check of the government page confirmed:

1. the page is explicitly the **2026** Austria-wide shortage-occupation list;
2. the page contains headings numbered **1 through 64**;
3. group **#7 Physicians** currently renders the two specialties as a concatenated sequence with no visible delimiter between `...Jugendchirurgie)` and the following `Facharzt/ ärztin (Innere Medizin und Pneumologie)`;
4. the live page currently renders `Facharzt/ ärztin (Kinder und Jugendpsychiatrie)` with one visible space between `Kinder` and `und`;
5. headings #28, #38, and #51 render normally on the live page; Perplexity's claimed extra-dot differences concern the packet's stored source representation and cannot be independently adjudicated without the exact immutable packet bytes;
6. group **#49 Graduate mechanical engineers** renders `Werkzeugkonstrukteur/in (DI).` followed by `Gebäudetechniker/in (Heizung/Lüftung/Sanitär) (DI)` in the published text;
7. the source still contains spelling/presentation anomalies such as `Pysiologie`, `Thoraxhchirug`, `Photoviltaiktechniker/in`, `Argonacschweißer/in`, and `Elementarpädaog(e)in`.

These anomalies are source evidence. They must not be silently corrected in the governed source projection merely because a normalized form would look cleaner.

## Disagreement adjudication

### #7 `Kinder  und Jugendpsychiatrie` whitespace

Kimi and Perplexity report that the immutable packet snapshot contains **two spaces** between `Kinder` and `und`, while the structured alias and current live page contain one. Grok reports exact equality between live source, immutable snapshot, and structured entries. These model reports therefore conflict about the same packet/source representation.

The current parser performs line-wise whitespace normalization before materializing structured entries. A whitespace difference of this kind is therefore plausible without implying an omitted occupation or changed semantic title, but it does mean the phrase **byte-for-byte faithful** must not be inferred from the structured projection alone.

Decision:

- do **not** rewrite the canonical projection from AI testimony;
- treat the #7 whitespace boundary as a reviewer-visible representation checkpoint;
- require the genuine human reviewer to compare the immutable `source_content_text` in the pinned packet with the structured #7 row;
- keep hash/evidence identity pinned to the immutable snapshot rather than to the current live rendering.

### #7 concatenated specialties

The current live source itself concatenates:

`Facharzt/ ärztin (Kinder- und Jugendchirurgie)Facharzt/ ärztin (Innere Medizin und Pneumologie)`

Kimi and Grok classify this as source-faithful formatting. Perplexity lists it inside its mismatch count but explicitly says the AIOS projection preserves the literal source concatenation and that it is a source-formatting anomaly rather than an AIOS textual error.

Decision:

- this is **not established as an AIOS extraction mismatch**;
- preserve the source-derived evidence string;
- preserve the existing lookup-only segmentation used to make the two specialties searchable;
- do not let lookup segmentation rewrite entry hashing or certification evidence.

### #28 / #38 / #51 source-snapshot punctuation

Perplexity reports that the packet's `source_content_text` contains extra dots after these ordinals while the current live page does not. The other model reports do not reproduce this concern, and the raw reviewer packet is not stored in the repository.

Decision:

- mark this as **unresolved packet-snapshot representation evidence** rather than a structured-projection defect;
- do not modify canonical data from one AI report;
- require the human reviewer to inspect the pinned immutable packet text directly;
- the deterministic checker verifies the snapshot text against its pinned hash, but intentionally cannot decide whether a historical immutable snapshot should equal today's live rendering.

### #49 period + rendered title boundary

The government page visibly places a period after `Werkzeugkonstrukteur/in (DI).` before `Gebäudetechniker/in (Heizung/Lüftung/Sanitär) (DI)`. Perplexity interprets this as two separately listed occupation titles and therefore a structural merge error when AIOS stores the source-derived string as one alias.

The current runtime deliberately handles this exact string through **lookup-only segmentation** while keeping the source-derived evidence projection unchanged. That separates matching ergonomics from canonical evidence.

Decision:

- no canonical data change is justified by the AI report alone;
- #49 remains a human-review checkpoint because the source presentation is structurally ambiguous;
- lookup-only segmentation remains non-authoritative and must not alter entry hashing or source-certification evidence.

### #60 / #61 spelling

Perplexity includes these ordinals in its reported mismatch count but also states that `Elementarpädaog(e)in` appears identically in the official source and AIOS projection and is therefore **not an extraction error**.

Decision: treat these as source-faithful anomaly checkpoints, not mismatches.

## Hash reproducibility finding

The cross-check surfaced a real tooling limitation that is separate from the 64-group content comparison.

The current repository deterministically computes:

- each structured entry SHA-256 from canonical JSON;
- `entry_set_sha256` from the ordered list of entry hashes;
- `source_content_text_sha256` from the immutable UTF-8 source text;
- `evidence_pack_sha256` from an internal `canonical_evidence` object using sorted compact JSON and UTF-8 SHA-256.

However, the exported v1 reviewer pack does not expose the complete internal `canonical_evidence` object used to compute `evidence_pack_sha256`. A reviewer can pin and compare the provided evidence-pack hash, but cannot independently reconstruct that exact hash from the exported packet alone because not every canonical input is exported.

The companion checker added with this record therefore recomputes only what the exported packet can prove directly and explicitly reports that `evidence_pack_sha256` is **not independently recomputable from the exported v1 packet**. It does not fabricate a reconstructed value.

## Deterministic packet-integrity checker

Use:

```powershell
python scripts/check_austria_source_certification_review_pack.py `
  --review-pack D:\gmai-review-packs\austria-2026-primary-source-certification-reviewer-packet.json
```

The checker verifies, without network access or mutation:

- Austria jurisdiction code;
- 2026 national scope;
- exactly 64 structured rows;
- contiguous source ordinals 1–64;
- ordered `entry_set_sha256` recomputation;
- `source_content_text_sha256` recomputation;
- snapshot-content-hash agreement between snapshot and projection;
- pinned `evidence_pack_sha256` format.

It deliberately does **not**:

- compare against the live migration.gv.at page;
- approve or reject a source certification;
- verify reviewer identity or credentials;
- infer individual visa/pathway eligibility;
- satisfy `independent_human_attestation`;
- claim to recompute `evidence_pack_sha256` from data that the exported v1 pack does not contain.

## Acceptance effect

This cross-check strengthens pre-review evidence but changes no acceptance state.

```text
Austria 2026 source projection:      AI cross-check completed; representation disagreements remain reviewer-visible
Top-level group count/year/scope:    64 / 2026 / national supported by all five model reports and live source re-check
Missing/extra top-level groups:      none reported by any model
Exact snapshot/live rendering:       CONFLICTING AI REPORTS / HUMAN CHECK REQUIRED
Independent human source review:     STILL REQUIRED
Independent human attestation:       NOT SATISFIED
L professional benchmark review:     SEPARATE REQUIREMENT / NOT SATISFIED BY THIS RECORD
L milestone:                         IMPLEMENTED / ACCEPTANCE PENDING
```

A future human reviewer may approve or reject the pinned certification only through the existing fail-closed reviewer return/submission contract. AI agreement, AI majority, or this document alone must never be converted into a human attestation.
