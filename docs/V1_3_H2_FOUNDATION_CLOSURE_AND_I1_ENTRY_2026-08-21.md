# Global Mobility AIOS — V1.3 H.2 Foundation Closure & I.1 Entry Decision — 2026-08-21

**Status:** ARCHITECTURAL STAGE DECISION — H.2 BOUNDED FOUNDATION READY TO CLOSE; I.1 DESIGN ENTRY OPEN  
**Runtime effect:** none by itself  
**Latest accepted technical checkpoint:** H.2.4 `e7584b90fc967e828960ae0730a35d8646fba74f`  
**Latest accepted H.2 refinement:** `25b19728e7dc35f3f0450f6ae839fa57fe36c1e4` — Production Proof `32505228943`  
**Canonical architecture:** `GLOBAL_MOBILITY_AIOS_COMBINED_ARCHITECTURE_V1_1.md`  

---

## 1. Decision

The accepted H.1/H.2 work is sufficient to close **H.2 as the bounded Organizational Immune System safety/measurement foundation** and move the Track C design programme into V1.3-I Earned Autonomy.

This decision does **not** claim that the complete future Organizational Immune System is implemented.

It means the project has already proven the minimum architecture required before defining canonical autonomy truth:

```text
measurement
+
trusted attribution
+
restrict-only circuit behavior
+
recovery boundary
+
concurrency/race visibility
+
production proof
```

No additional H.2 feature is justified merely to keep the stage open.

---

## 2. Evidence supporting H.2 closure

### H.1 — canonical lineage + restrictive circuit

Accepted:

- shared canonical eligibility lineage validation;
- structural integrity failure becomes a critical incident;
- exact aggregate circuit can open restrictively;
- fresh execution blocks before provider egress;
- recovery is authenticated/human and does not grant authority.

### H.2.1 — verifier disagreement recurrence

Accepted:

- warning recurrence is measured inside one recovery epoch;
- third verifier disagreement opens the exact aggregate circuit;
- concurrent threshold crossing produces one durable OPEN;
- unrelated warning kinds do not contribute.

### H.2.2 — runtime health attribution

Accepted:

- trusted producer/verifier runtime identity is durably attributed;
- attribution/warning is atomic;
- replay/identity drift fails closed;
- runtime-health warnings remain observation-only.

### H.2.2 classification refinement

Accepted:

```text
configuration_or_binding_failure      provider_egress_occurred=false
provider_transport_failure            provider_egress_occurred=true
provider_response_contract_failure    provider_egress_occurred=true
```

Legacy H.2.2 records remain replayable without rewriting.

### H.2.3 — pre-egress revision conflicts

Accepted:

- genuine lower-than-current reassessments are classified before provider egress;
- expected/current canonical revision identity is durable;
- false-positive classes remain excluded;
- no automatic retry/rebase is invented.

### H.2.4 — post-producer revision race

Accepted:

- producer egress may succeed while the canonical revision advances;
- verifier egress remains false;
- stale canonical effect remains false;
- event-time revision identity remains durable even if a later revision supersedes it before first persistence;
- shared aggregate lineage validation proves the historical/current chain.

---

## 3. What H.2 closure does not claim

Closing this bounded foundation does not claim:

- full Immune-System implementation;
- generic anomaly detection;
- provider/runtime health scoring;
- provider-wide quarantine;
- rolling-window health policy;
- automatic retry/rebase;
- automatic recovery;
- dynamic autonomy downgrade;
- blast-radius controls across arbitrary domains;
- root-cause automation across the whole organization;
- Earned Autonomy implementation.

Those remain future capabilities and must be justified by their own measured failure models.

---

## 4. Why the next stage is I, not another H increment

The V1.3 architecture requires autonomy to be capability + context specific and earned from evidence.

Current canonical organization state already has authority semantics such as `OrganizationPosition.authority_level`, while no equally explicit canonical capability-specific autonomy profile exists yet.

Building a Dynamic Autonomy Manager before that canonical truth exists would create one of two architectural errors:

```text
misuse authority as autonomy
or
invent a parallel autonomy truth store inside the Immune System
```

Both are prohibited.

Therefore the next foundation must define autonomy truth first.

---

## 5. V1.3-I.1 — Capability-Specific Autonomy Profile & Evidence Foundation

**Entry status:** DESIGN OPEN / IMPLEMENTATION NOT STARTED

I.1 should introduce a canonical, governed way to answer:

> For this employee/position, this capability, this context and this policy version, what autonomy level currently exists, why does it exist, and what evidence supports it?

The first I.1 slice is intentionally measurement/governance focused.

It must not begin with automatic promotion.

---

## 6. Candidate canonical autonomy profile

Conceptual shape:

```text
CapabilityAutonomyProfile
├── tenant_key
├── position_key
├── capability_key
├── context_scope
├── autonomy_level              A0–A5
├── board_ceiling
├── authority_requirement
├── risk_ceiling
├── evidence_policy_version
├── effective_from
├── effective_to
├── lifecycle_status
├── supersedes_profile_id
├── granted_by / governance source
├── decision_activity_id
└── record_fingerprint
```

Important distinction:

```text
authority answers: MAY this actor ever perform the class of action?
autonomy answers: HOW independently may it perform that authorized capability here?
risk answers: WHAT consequence/verification floor applies?
```

No field may collapse these three concepts into one scalar.

---

## 7. Candidate autonomy evidence

Autonomy promotion/demotion decisions should be grounded in append-only, reconstructable evidence.

Conceptual evidence dimensions:

```text
capability key
context/risk band
sample window
successful governed outcomes
failed governed outcomes
verification disagreement
human correction rate
critical incident count
runtime-health failures
rollback/recovery quality
Evidence-grounding quality
policy violations
latency/SLA reliability
cost per successful governed outcome
freshness of evidence
minimum sample requirement
```

Evidence should point back to canonical outcomes/activities rather than trusting model self-evaluation.

Permanent rule:

> **Autonomy evidence measures organizational performance. It does not let an agent grade or promote itself.**

---

## 8. Promotion and downgrade asymmetry

Target doctrine:

```text
promotion
  requires sufficient fresh evidence
  requires policy/governance decision
  cannot exceed Board ceiling
  cannot create authority

downgrade
  may happen faster
  may be triggered restrictively once an accepted policy exists
  cannot remove Board authority
  should preserve explanation and recovery path
```

I.1 does not yet implement the Dynamic Autonomy Manager. It creates the canonical contract that such a manager may later consume.

---

## 9. I.1 hard non-goals

The first I.1 implementation must not include:

- automatic autonomy promotion;
- agent self-promotion;
- inferred authority expansion;
- provider/model-specific autonomy grants;
- organization-wide autonomy scoring;
- arbitrary weighted confidence score as permission;
- dynamic downgrade before canonical profile/evidence truth exists;
- replacement of Command Gateway authority decisions;
- weakening of human/professional/legal review floors.

---

## 10. I.1 acceptance direction

Before I.1 can be sealed, expected proof should include at least:

1. capability + context scoped identity;
2. explicit A0–A5 semantics;
3. authority/autonomy/risk separation;
4. Board ceiling enforcement;
5. append-only profile supersession;
6. deterministic evidence lineage;
7. no self-promotion path;
8. no request-body ability to choose autonomy;
9. replay/idempotency protection;
10. PostgreSQL concurrency proof for competing profile updates;
11. transparent read model for Cockpit/Board inspection;
12. full Production Proof on the exact technical candidate.

No migration/model design is accepted merely by this document; the implementation slice must be designed and proved separately.

---

## 11. Track relationship

```text
Track C — High-Autonomy Organization
H.2 bounded foundation closure
→ I.1 canonical autonomy profile/evidence
→ later Earned Autonomy promotion/downgrade policy
→ J Agent Organization Runtime

Track B — Technology Radar
Plasma Wiki pilot
Plasma Fractal engineering pilot
LLMLingua-2 benchmark
Mobility Model Benchmark / Model Router research

No authority crossover
```

---

## 12. Final boundary

> **Safety infrastructure earns the right to define autonomy; it does not grant autonomy by itself.**

> **Define canonical autonomy truth first. Only then allow promotion or restrictive downgrade policy to operate on it.**
