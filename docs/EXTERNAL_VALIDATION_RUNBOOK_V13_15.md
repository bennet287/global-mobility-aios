# External Validation Runbook — Phase 13.15

This document is the operational guide for executing the first real external
validation run that closes the Phase 13.5.2 gate and unblocks Phase 13.6
cross-functional programmes / Phase 14.

## Goal

Prove that one real mobility user and one independent professional/operator can
complete an end-to-end Truth Engine / pathway workflow, understand the result,
consider it operationally useful, and confirm that material rules are traceable
to reviewed official-source evidence with no unsupported legal certainty and no
silently missing critical documents.

The system records this as a deterministic `passed` external-validation gate
receipt.

## Scope

- **Scenario:** `at-skilled-worker-discovery-v1` — Austria skilled-employment
  pathway discovery.
- **Persona:** A third-country national skilled worker considering Austria.
- **Workflow:** Intake → eligibility → pathway comparison → document
  intelligence → recommendation, with explicit evidence traceability.
- **Tester pair required:**
  1. `mobility_user` — a real person going through or seriously considering this
     immigration pathway.
  2. `professional_operator` — an immigration lawyer, relocation consultant, HR
     mobility specialist, or international-office worker who handles Austria work
     permits in practice.

## Prerequisites

Before recruiting testers, confirm in the running app:

1. The API and web containers are healthy.
2. The Austria scenario is seeded: `/validation` → **Seed / verify Austria
   scenario**.
3. There is a real or realistic test lead with a completed pathway comparison
   for Austria skilled employment.
4. The comparison is pinned to a published pathway version with approved
   verified rules, official sources, and source snapshots.
5. You have admin access to the External Validation workspace (`/validation`).

## Tester recruitment briefs

### Mobility user

> We are building a tool that helps people understand their visa and work
> permit options for Austria. We would like you to use it as if you were planning
> to move, answer the questions honestly, look at the recommendation, and tell us
> whether it makes sense and is useful. You do not need to know immigration law;
> in fact, we especially want your reaction as a non-expert. The session takes
> 20–30 minutes. We will not use your real personal data for anything outside
> this test.

### Professional / operator

> We are building an AI-assisted platform for Austria work-permit guidance. We
> would like an independent practitioner to test the same workflow a user would
> see and judge whether the jurisdiction/pathway result is correct, whether the
> material rules are traceable to real sources, and whether the tool is
> operationally useful. We need your honest assessment, including any defects.
> The session takes 20–30 minutes.

Both testers must be **distinct individuals**. The system rejects a single
person acting as both reviewer types.

## Founder / operator checklist

### Before the sessions

- [ ] Open `/validation` and click **Seed / verify Austria scenario**.
- [ ] Create or select a lead that has completed an Austria skilled-worker
      pathway comparison.
- [ ] Copy the lead UUID and the pathway-comparison UUID.
- [ ] Create a validation run in `/validation` with those UUIDs.
- [ ] Record the run URL or run UUID to share with testers (only the parts they
      need; reviewers do not need admin access to `/validation`).
- [ ] Prepare the two tester instruction sheets below.
- [ ] Confirm testers can access the application (local URL, preview URL, or
      screen-share session).

### During the sessions

- [ ] Observe silently. Count how many times you must intervene to help the
      tester complete the workflow. Record this as the **founder intervention
      count**.
- [ ] Do not explain the expected answer or correct the system while the tester
      is working. Your role is to watch and record, not to teach.
- [ ] If a tester asks a clarifying question, answer neutrally. Count it as an
      intervention.

### After both sessions

- [ ] In `/validation`, select the run and attach the required evidence
      references:
  - Truth Engine claim(s) shown to the testers
  - Verified rule(s) used in the recommendation
  - Official source(s) backing the rules
  - Source snapshot(s) pinned to the sources
  - Published pathway version
  - Pinned pathway comparison
- [ ] Record the mobility-user review. Minimum required:
  - workflow completed: yes
  - understanding rating: 1–5 (must be ≥ 4 to pass)
  - usefulness rating: 1–5 (must be ≥ 4 to pass)
  - substantive feedback
- [ ] Record the professional/operator review. Minimum required:
  - workflow completed: yes
  - usefulness rating: 1–5 (must be ≥ 4 to pass)
  - jurisdiction/pathway correct: yes
  - material-rule traceability: 100% (must be 100 to pass)
  - unsupported legal-certainty count: 0 (must be 0 to pass)
  - missing critical-document count: 0 (must be 0 to pass)
  - substantive feedback
- [ ] Add any findings raised by the testers, categorized and severity-rated.
- [ ] Click **Evaluate gate**.

## Tester instruction sheets

### Mobility-user sheet

1. Imagine you are a software engineer from India considering a skilled job in
   Austria. You do not yet have an offer letter.
2. Go to the intake page and answer the questions as honestly as you can. Use
   realistic but not your real passport or financial details if you prefer.
3. Look at the pathway comparison and recommendation.
4. Answer these questions:
   - Did you understand what the tool is telling you to do next?
   - How useful was the recommendation on a scale of 1 to 5?
   - Was there any point where you felt confused or lost trust?
   - Any other feedback?

### Professional/operator sheet

1. Review the same Austria skilled-employment scenario.
2. Go through the intake and recommendation as if you were quality-checking it
   for a client.
3. Judge whether the jurisdiction and pathway selected are correct for the facts.
4. Check whether every material rule used in the recommendation is traceable to a
   reviewed official source.
5. Count any statements that sound legally certain but are not supported by the
   attached source evidence.
6. Count any critical document requirements that were silently omitted.
7. Provide:
   - Correctness judgment (yes/no)
   - Material-rule traceability percentage
   - Unsupported legal-certainty count
   - Missing critical-document count
   - Usefulness rating 1–5
   - Substantive feedback, especially defects

## Triage decision tree

After both reviews and evidence are captured, evaluate the gate. The result is
deterministic.

### If the gate says `failed`

1. Read the gate reasons. They will list the concrete failures, for example:
   - "Mobility-user usefulness rating is below 4/5."
   - "Material-rule source traceability is below 100%."
   - "1 critical finding(s) remain unresolved."
2. Create a finding for each concrete defect if it is not already recorded.
3. Fix or retest the defect.
4. Mark the finding `resolved` with remediation notes.
5. Re-evaluate the gate.
6. Repeat until the gate passes or you decide to abandon the scenario.

### If the gate says `held`

1. Check which requirement is missing: a reviewer type, evidence type, or
   triage of a medium/low finding.
2. Complete it.
3. Re-evaluate.

### Medium/low findings

- You may **triage** them (mark as `triaged`) and continue, or
- You may **resolve** them, or
- The Human Board may **accept the risk** with a written rationale if the
  finding is medium or low and not resolved.

Critical and high findings **must be resolved**. They cannot be waived by the
Board.

### If the gate says `passed`

1. The run status becomes `completed` automatically.
2. The deterministic gate receipt is recorded.
3. Update `docs/ROADMAP.md`:
   - Mark `Phase 13.5.2` complete.
   - Close the external-validation gate.
   - Update the current quality evidence section with the passed receipt.
4. Update `docs/CHANGELOG.md` with the Phase 13.15 entry.
5. You may now resume Phase 13.6 departmental expansion or cross-functional
   programmes.

## What happens if the real run fails

A failed gate is valuable, not embarrassing. It means the system prevented a
false claim of validation. The correct action is:

1. Record the real findings honestly.
2. Fix the defects.
3. Re-run with a new lead/comparison if needed.
4. Do not manually override the gate or fabricate reviews. The audit log and
   deterministic gate make that detectable and would invalidate the entire
   Phase 13 governance foundation.

## Privacy and data handling

- Use realistic but not necessarily real personal data for testers if they
  prefer.
- If real documents are uploaded, they must be stored in the configured
  encrypted storage (MinIO/S3 in production; local storage is prohibited in
  production).
- Tell testers that their feedback becomes part of the durable validation ledger
  and may be referenced in release evidence.

## Definition of done for Phase 13.15

- [ ] One `mobility_user` review and one `professional_operator` review are
      recorded in the External Validation ledger.
- [ ] All required evidence types are pinned to the run.
- [ ] The evidence graph passes the fail-closed integrity check.
- [ ] No critical or high findings remain unresolved.
- [ ] All medium/low findings are triaged, resolved, or Board-accepted.
- [ ] The gate evaluates to `passed`.
- [ ] The deterministic gate receipt is persisted in the audit log.
- [ ] ROADMAP and CHANGELOG are updated.
- [ ] The commit is pushed.

## When this is done, what is unblocked

After the gate passes, you may resume:

- Finance expansion (`Accounts Lead`, `Investor Relations Lead`).
- Time-bounded cross-functional programmes with one accountable executive
  sponsor.
- Phase 14 scale work, but only when measured demand justifies each piece of
  infrastructure.
