# Phase 13.10.2 — External Mobility Validation Framework

## Purpose

Phase 13.10.2 is the release gate between the already-delivered bounded AI organization
and activation of additional executive departments. It tests the customer-facing mobility
product and the solo-founder operating model at the same time.

The framework does not ask an AI agent to judge whether its own work is good. A PASS
requires feedback from two distinct external humans: one real mobility user and one
independent professional/operator. The internal actor who records a review is stored
separately from the external reviewer identity and every mutation is audited.

## Data model

Migration `0068_external_validation_framework` introduces five durable tables:

- `external_validation_scenarios` — persona, jurisdiction, objectives, and evidence contract;
- `external_validation_runs` — one immutable/retest-oriented execution record with founder intervention count;
- `external_validation_reviews` — one mobility-user and one professional/operator review per run;
- `external_validation_findings` — Critical/High/Medium/Low defect ledger with remediation and Board-acceptance fields;
- `external_validation_evidence` — typed references to Truth Engine, source, pathway, comparison, document, or operator-note evidence.

The first scenario is `apps/api/validation/scenarios/austria_skilled_worker_v1.json`. It
intentionally does not contain the expected pathway name, eligibility threshold, or legal
conclusion. Supplying the answer in the fixture would invalidate the test.

## Required end-to-end evidence

The default Austria scenario requires durable evidence references for:

1. a Truth Claim produced/verified by the Truth Engine;
2. a reviewed Verified Rule;
3. the Official Source supporting that rule;
4. the immutable Source Snapshot;
5. the published pathway version used by the workflow; and
6. the pinned pathway comparison shown to the tester.

Additional document or operator-note evidence may be attached to the run or to a finding.
Every run must pin both the lead and the exact pathway comparison shown to the testers.
The deterministic gate also verifies that the captured pathway version is the comparison's
primary version, that the pathway jurisdiction/domain matches the scenario, that every
Verified Rule referenced by that version is captured, and that the rule/pathway Official
Source and content-hash-pinned Source Snapshot lineage is present. Unrelated records cannot
satisfy the gate merely by filling each evidence-type slot.

## Acceptance thresholds

The deterministic gate returns `held`, `failed`, or `passed`.

A run is **held** while required external reviews/evidence are missing or Medium/Low
findings remain untriaged.

A run **fails** when completed evidence shows a material product defect or an incoherent
provenance graph, including:

- mobility-user understanding below 4/5;
- mobility-user usefulness below 4/5;
- professional/operator usefulness below 4/5;
- jurisdiction/pathway correctness not confirmed;
- material-rule traceability below 100%;
- one or more unsupported legal-certainty statements;
- one or more missing critical document requirements; or
- any unresolved Critical/High finding; or
- a mismatch between the pinned comparison, pathway version, verified rules, official sources,
  immutable snapshots, scenario jurisdiction/domain, or lead-scoped Truth Engine claim.

A run **passes** only when both required external reviewers complete the workflow, all
acceptance metrics pass, all required evidence types are pinned, all Critical/High findings
are resolved, and every Medium/Low finding is triaged, resolved, or explicitly accepted by
the Human Board.

## Board authority

The ordinary reviewer/operator lane may create and triage findings. Only the `admin`
Human-Board role may call the Board-acceptance endpoint. Board acceptance is deliberately
limited to Medium/Low findings. Critical and High findings cannot be waived by this
framework and must be resolved and retested.

A passed run is treated as immutable for external-review submissions; a remediation retest
should create a new run so the original evidence and decision history remain auditable.

## Founder intervention metric

Each run records `founder_intervention_count`:

- `0` — excellent autonomy for the tested workflow;
- `1–2` — good;
- `3–5` — automation work is still needed;
- `>5` — the workflow is not autonomous enough for the intended operating model.

The number is reported by the deterministic gate but does not by itself convert a legally
correct result into a PASS or FAIL. It is an operating-model metric, not a legal-quality
metric.

## API surface

The `/api/v1/external-validation` router supports scenario creation/default seeding, run
creation/list/detail/update, external review capture, evidence capture, finding creation and
triage, Human-Board medium/low risk acceptance, and explicit gate evaluation.

Read operations follow the platform read-role policy. Scenario/run/evaluation mutations
require Admin/Operator; review/finding mutations additionally permit Reviewer; Board risk
acceptance is Admin only.

## Release gate

Finance, Communications, People, and Legal remain held until at least one real run reaches
`passed`. The framework existing in code does not satisfy that gate by itself.

## Data minimization

Reviewer identity fields exist to prove that the two required roles were fulfilled by distinct
external humans. Use the minimum identifier necessary for auditability (a reviewer-approved
pseudonym/reference is acceptable where appropriate), avoid storing unrelated personal data in
free-text feedback, and follow the project's normal access-control and retention rules.
