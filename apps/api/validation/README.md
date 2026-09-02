# External Mobility Validation

Phase 13.10.2 converts the external-validation gate into repeatable product infrastructure.
The validation framework does **not** encode immigration conclusions in its scenarios. A
scenario supplies a persona, jurisdiction, goals, and acceptance criteria; the existing
Truth Engine and governed pathway catalogue must determine the actual candidate pathway
from reviewed evidence.

## Required reviewers

Every gate-closing run requires two distinct external humans:

1. a real mobility user; and
2. an independent professional/operator with practical mobility or immigration-process
   experience.

The API stores the internal submitter separately from the external reviewer identity and
requires an explicit external-human attestation. AI organization code does not create the
required reviewer records.

## Gate thresholds

A run must be pinned to one lead and the exact pathway-comparison assessment shown to the
testers. A run passes only when:

- both external reviewer types completed the workflow;
- user understanding and usefulness are at least 4/5;
- professional/operator usefulness is at least 4/5;
- jurisdiction/pathway correctness is confirmed by the professional/operator;
- material-rule traceability is 100%;
- unsupported legal-certainty statements are zero;
- missing critical document requirements are zero;
- no critical or high finding remains unresolved; and
- every medium/low finding is triaged, resolved, or explicitly accepted by the Human Board; and
- the comparison, primary pathway version, verified-rule set, official-source/snapshot lineage,
  scenario jurisdiction/domain, and lead-scoped Truth Engine claim form one coherent graph.

Critical and high findings cannot be waived by the Board through this framework. They
must be resolved and retested. Board risk acceptance is available only for medium/low
findings.

## First scenario

`scenarios/austria_skilled_worker_v1.json` is the first validation fixture. It deliberately
contains no expected pathway name or legal threshold. That prevents the validation data
from teaching the system the answer it is supposed to discover.

Use a new validation run for each retest so the audit trail remains append-only at the run
level.
