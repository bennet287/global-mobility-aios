# L — Austria Blind Professional Review Handoff Hardening

**Date:** 2026-08-31
**Branch:** `roadmap/global-mobility-aios-v12`
**Classification:** release-critical L acceptance prerequisite
**Milestone state:** `L IMPLEMENTED / ACCEPTANCE PENDING`; `M NOT STARTED`

## 1. Why this change was necessary

The repository already had a professional-review compiler, immutable benchmark fingerprints, reviewer/credential reference fields, a packet generator, return template, and fail-closed structural validation.

A deeper inspection before recruiting the independent Austria reviewer found one material independence defect in the existing handoff:

```text
reviewer packet included source_labels
reviewer packet included source_rationale
reviewer was asked to choose CONFIRMED vs CORRECTED
```

That design could anchor the reviewer to AIOS's official-source-curated benchmark answer. It was inconsistent with the project's stronger blind-evaluation direction, where expected labels are withheld until after an independent assessment.

This is not evidence that any prior professional review was invalid: **no genuine independent professional Austria review has yet been claimed.** It is a prerequisite hardening before that review occurs.

## 2. Anti-duplication decision

Do not create another professional-review system.

Existing canonical assets remain authoritative:

- `apps/api/app/evaluations/professional_review.py`
- `scripts/prepare_austria_professional_review.py`
- immutable source-case fingerprints;
- `mobility-professional-review-v1` canonical compiled review bundle;
- `compile_professional_reviews(...)` promotion/hold semantics;
- existing external-validation infrastructure and reviewer-credential reference boundary.

The change is an adapter/staging layer in front of the existing canonical compiler.

## 3. New blind handoff flow

```text
official-source-curated Austria benchmark
        ↓
existing immutable case fingerprint
        ↓
blind professional reviewer packet
  facts + official sources
  NO source_labels
  NO source_rationale
        ↓
blind reviewer return
  ASSESSED + independent reviewed_labels
  or DISPUTED
  or NEEDS_MORE_FACTS
        ↓
AIOS comparison after return
        ↓
derived canonical decision:
  matching labels  → CONFIRMED
  changed labels   → CORRECTED
  disputed         → DISPUTED
  more facts       → NEEDS_MORE_FACTS
        ↓
existing mobility-professional-review-v1 compiler
        ↓
existing fail-closed validation/promotion semantics
```

The human reviewer no longer needs to see the benchmark answer in order to choose `CONFIRMED` or `CORRECTED`.

## 4. Contracts

### Reviewer packet

`austria-professional-review-handoff.v2`

Required properties include:

```text
blind_review=true
expected_labels_excluded=true
source_rationale_excluded=true
```

Each case contains its exact immutable source-case fingerprint, supplied facts, official-source references, and reviewer instructions.

It must not contain `source_labels` or `source_rationale`.

### Blind reviewer return

`austria-professional-review-blind-return.v1`

Reviewer-facing `assessment_status` values:

```text
ASSESSED
DISPUTED
NEEDS_MORE_FACTS
```

For `ASSESSED`, the reviewer supplies their complete independent `reviewed_labels`.

For `DISPUTED` or `NEEDS_MORE_FACTS`, the review remains held outside the professionally promoted denominator, preserving existing semantics.

### Canonical compiled review

The canonical internal bundle remains:

`mobility-professional-review-v1`

No new professional truth model is introduced.

## 5. CLI flow

Prepare the blind packet:

```powershell
python scripts/prepare_austria_professional_review.py --prepare-packet --output .local/austria-professional-review-packet.json
```

Prepare the reviewer-facing blind return skeleton:

```powershell
python scripts/prepare_austria_professional_review.py --prepare-blind-return-template --output .local/austria-professional-review-return.json
```

After the genuine reviewer returns the completed blind file:

```powershell
python scripts/prepare_austria_professional_review.py --compile-blind-return .local/austria-professional-review-return.json --output .local/austria-professional-review-canonical.json
```

Then structurally validate the derived canonical review:

```powershell
python scripts/prepare_austria_professional_review.py --validate-bundle .local/austria-professional-review-canonical.json
```

The legacy `--prepare-return-template` remains available as an internal canonical-template compatibility path. It is **not** the recommended reviewer-facing handoff.

## 6. Reviewer identity and credential boundary

This hardening does not allow AIOS to certify a real person's identity or professional standing.

For L acceptance:

- reviewer identity must be real;
- independence must be established outside AIOS;
- professional standing/credential must be independently verifiable;
- durable `professional_review_reference`, `reviewer_reference`, and `reviewer_credential_reference` values must reference genuine external evidence;
- test-only, placeholder or fabricated values invalidate acceptance evidence.

The compiler validates structure and semantics only.

## 7. Test changes

`apps/api/tests/test_professional_review_cli.py` now requires:

- v2 packet is explicitly blind;
- expected labels are excluded;
- source rationale is excluded;
- blind matching labels derive `CONFIRMED` only after return;
- independently differing labels derive `CORRECTED`;
- the resulting canonical bundle still passes the existing validator.

`apps/api/tests/test_professional_review_return_template.py` now requires:

- the blind reviewer template has no canonical `decision` field;
- untouched blind templates cannot compile into evidence;
- the legacy canonical template remains fail-closed.

## 8. Relationship to Track B

The immediately preceding Track B pass ended with a deeper anti-duplication reclassification:

- runtime economics presentation — implemented;
- durable activity lineage — implemented and locally/browser proven at `958b796...`;
- collaboration/coordination — broader AIOS multi-surface foundation already exists;
- presence/heartbeat — demand-gated, canonical semantics not established;
- event synchronization — no demonstrated transport gap;
- provider transcript/tool capture — cannot bypass OrganizationActivity/evidence/privacy;
- Living Organization scene — no proven current need;
- AI Economics history — post-M/N/product-analytics need rather than a visual-only B2 addition.

Therefore continuing to add Track B features now would risk product-scope drift and duplicate state. The release-critical L professional-review gate correctly regains priority.

## 9. Observed V12.42 exact-head documentation proof

Before this source hardening, the user exercised documentation/repository gates at exact head:

`246413cc60cb7c9dc2cbc8112f35c176f93c13fc`

Observed:

```text
repository policy                         PASS
release consistency                       PASS
Python dependency constraints             PASS — 27 direct dependencies
diff hygiene                              PASS
git diff --check                          PASS
working tree synchronized with origin      PASS
frozen V11                                PASS — ac130deaafa7aa44068e9459facbda2b4df327d6
deep-R3 local backup                      PASS — 3a6fea2cbbf87d424459b81f1b168ecd6baaa312
```

That exact-head proof is historical documentation-only evidence and does not prove the later blind-review source changes.

## 10. First local acceptance attempt and repair

The first local V12.43 acceptance attempt at exact head
`b711ab619f3d80e077270900a8922651b2ecc964` did **not** pass and must not be recorded as green proof.

Observed focused professional-review result:

```text
18 passed
1 failed
1 warning
```

The failing test was:

`test_blind_assessment_derives_confirmed_only_after_return`

The canonical output and source labels were semantically equal, but the test asserted raw list equality. The professional-review model stores several label dimensions as sets and `_labels_payload(...)` serializes them in sorted order, while the source benchmark JSON preserved authoring order. The failure therefore showed order differences such as:

```text
["applicable_minimum_remuneration", "binding_job_offer"]
vs
["binding_job_offer", "applicable_minimum_remuneration"]
```

Repair:

`apps/api/tests/test_professional_review_cli.py`

The test helper now sorts all list-valued source-label dimensions before comparing them with canonical serialized output. Production compiler logic, blind-review decisions, fingerprints, authority boundaries and review semantics are unchanged.

The same acceptance attempt also exposed an operator-command defect in the ad-hoc PowerShell verification snippet. Passing a PowerShell here-string directly after `python -c` stripped Python string quoting and caused `SyntaxError`. That was an acceptance-command construction error, not a repository/product failure.

Future acceptance commands must therefore use PowerShell-native JSON assertions or a safe stdin/script invocation rather than the failed `python -c @'... '@` pattern.

The fail-closed untouched-return check **did** behave correctly during the failed attempt: the compiler returned exit code `2`, reported `review_batch_id must be a non-empty string`, and did not create canonical review evidence.

The full backend run was started after the earlier failures, but the supplied transcript ends while pytest is still printing progress dots. No full-backend PASS is claimed from that attempt.

Current state after repair and stable-head rerun:

```text
blind handoff implementation          IMPLEMENTED
test-oracle order repair              IMPLEMENTED
local focused proof after repair      PASS — 19 / 19 at d969c7d...
full backend proof after repair       PASS — 1332 passed / 22 skipped at d969c7d...
repository gates after repair         PASS at d969c7d...
stable start/end exact-head proof     PASS at d969c7d...
R3 interop recoverability             PASS — aad377e... pushed to origin
professional Austria review           PENDING
final post-review exact-head proof    PENDING
L acceptance                          PENDING
```

The durable proof record is:

`docs/L_BLIND_PROFESSIONAL_REVIEW_LOCAL_PROOF_2026-08-31.md`

This local proof closes the technical prerequisite for handing the packet to a genuine reviewer. It does not create professional review evidence and does not seal L.

## 11. Acceptance boundary

This change means only:

```text
professional-review handoff design hardened against answer anchoring
```

It does **not** mean:

```text
professional Austria review complete
reviewer identity verified by AIOS
reviewer credential verified by AIOS
L accepted
L sealed
M started
```

The next genuine L action remains obtaining the completed blind assessment from a qualified independent Austria professional, compiling/reconciling that real evidence, then running final exact-current-head technical proof.
