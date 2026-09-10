# AIOS Agent Execution & Verification Playbook v1

This playbook operationalizes the AIOS Agent Constitution for substantial repository work. It adapts useful goal/loop/swarm and project-local verification ideas to AIOS without importing an external agent framework or weakening AIOS truth, CI, visual, or merge contracts.

## 1. Goal contract

Every substantial slice starts with a checkable exit predicate. A goal is not "improve Mobility"; it is a statement that can be proven false or true.

A goal contract records:

- semantic outcome;
- authoritative base/ref;
- intended scope;
- truth boundary;
- required automated gates;
- required real-product/browser evidence;
- topology/normalization requirements;
- integration/merge requirement;
- explicit blockers that may legitimately stop execution.

The coordinator owns the exit predicate until it is satisfied, the user redirects/stops, or a genuine external blocker/product decision is reached. A plateau, a passing build, an opened PR, or one green workflow is not an exit condition.

## 2. Coordinator → Builder → Independent Verifier

Use role separation for non-trivial slices.

### Coordinator

Owns scope, current authoritative state, exit predicate, dependency ordering, acceptance evidence, and final integration verdict. The coordinator does not accept a builder's self-report as proof.

### Builder

Owns implementation and builder-level tests for one semantic slice. It reports the exact head SHA, changed scope, tests run, known limitations, and evidence locations. It does not declare the slice accepted or merged merely because its own tests pass.

### Independent verifier

Starts from the candidate's exact current head and acceptance contract, not from the builder's narrative. It checks the complete base-to-head diff, truth boundaries, relevant tests, browser/product behavior, responsive/accessibility requirements, and artifacts. It returns one verdict:

- `PASS` — predicate satisfied for the assigned verification surface;
- `ISSUES` — concrete evidenced defects remain;
- `BLOCKED` — verification cannot be completed because of a named external condition.

A verifier must not silently repair the candidate it is judging. Findings go back to the builder/coordinator; a changed head invalidates the old verification verdict and requires verification of the new head.

For small low-risk changes, one agent may perform multiple roles sequentially, but it must still preserve the same evidence boundaries: implementation evidence is not acceptance evidence.

## 3. Evidence loop

When the exit predicate is not yet true:

1. refresh authoritative repository/PR/workflow/artifact state;
2. identify the smallest change justified by current evidence;
3. implement that change without unrelated scope;
4. run the cheapest meaningful local/targeted verification first;
5. publish/update the candidate when appropriate;
6. verify the exact resulting head against the acceptance contract;
7. classify failures at the correct layer and fix/retry;
8. repeat until the predicate is true or a genuine blocker exists.

Do not add speculative belt-and-suspenders changes. Do not relax the predicate to declare success. A stale workflow, artifact, screenshot, review, or CI result never proves a newer head.

External waits such as CI are continuation points, not completion points. Re-check the owning system when useful; do not infer success from elapsed time or an earlier stage.

## 4. Controlled parallel execution

Parallelism is an optimization, not a success metric. Use it only when responsibilities can be isolated and results independently checked.

Good AIOS parallel lanes include:

- repository/architecture investigation;
- independent code review;
- truth-boundary review;
- accessibility/responsive review;
- browser/visual evidence review;
- test/failure analysis;
- competing design/implementation prototypes where a rubric can select a winner;
- independent semantic slices that do not share mutable state.

Do not parallelize dependent mutations, shared-file edits, normalization, readiness transitions, or merge operations. Give every writing worker an isolated branch/worktree/output. Define the done predicate, scope, verification method, and expected report before dispatch.

Aggregate worker reports into one coordinator verdict. Worker count, PR count, and activity are not evidence of progress; accepted semantic side effects and predicate movement are.

## 5. AIOS verification profiles

Verification profiles are project-local procedures. They describe how to prove a class of AIOS behavior from a cold start. They do not replace repository CI; they make the acceptance procedure explicit and reusable.

### `verify-pr-candidate`

Required for governed PR convergence:

- refresh base/head/draft/mergeability;
- verify current integration base;
- inspect complete base-to-head diff and changed files;
- verify intended semantic scope and unrelated-change absence;
- verify required topology (for normalized redesign slices: normally one semantic commit, 1 ahead / 0 behind);
- fetch exact-head required workflows and require completed success;
- require any profile-specific evidence below;
- after any head change, invalidate prior exact-head acceptance and repeat;
- before merge, refresh PR head and required checks again;
- merge with expected head SHA when supported;
- verify owning-system merge success and post-merge integration ref/tree/parents as required.

### `verify-visible-aios`

Required for material visible frontend work:

- build/type/lint/test gates defined by the repository;
- exercise the real route/product surface with browser automation;
- capture required desktop and phone evidence;
- inspect the images themselves, not only screenshot-generation success;
- check hierarchy, clipping, horizontal overflow, readable density, navigation/states, focus/touch behavior where applicable, reduced motion and forced-colors/accessibility contracts where governed;
- reject generic or semantically misleading presentation even when it compiles.

### `verify-living-organization`

In addition to `verify-visible-aios`:

- canonical scene/backend state remains authoritative;
- presentation-only animation does not claim physical presence, locomotion, conversation, handoff, authority, or completion without canonical support;
- status-to-presentation mappings remain truthful;
- desktop/phone proof covers the changed scene state and important interaction;
- Living Organization/V2 hardening browser proof remains green on the exact candidate head.

### `verify-mobility`

In addition to `verify-visible-aios`:

- no protected personal case fact appears before secure access;
- Overview remains orientation/navigation unless a secure contract explicitly supports more;
- protected case access routes through the accepted secure surface;
- unavailable Documents/Timeline/Messages destinations remain visibly fail-closed until accepted;
- no invented decisions, evidence state, milestones, messages, workflow authority, or application status;
- browser proof asserts the stable Mobility navigation contract and no horizontal overflow on phone.

### `verify-truth-boundaries`

Use for any slice that presents canonical state:

- identify each user-visible semantic claim introduced or changed;
- trace it to canonical source/contract or classify it as presentation-only;
- reject inferred authority, state, presence, evidence, decision, completion, communication, or personal-case facts;
- verify unavailable/unknown states fail closed rather than being filled with plausible content.

## 6. Candidate lifecycle

The default governed lifecycle is:

`goal → inspect → implement → builder tests → candidate → independent verification → fix loop → normalized candidate → exact-head CI → exact-head product/visual proof → ready → final refresh → expected-SHA merge → post-merge verification → next roadmap slice`

Normalization is required when stale stacked ancestry or predecessor history would otherwise enter the sealed redesign base. Reconstruct only the accepted semantic delta on the latest sealed integration head and re-run acceptance on the normalized head.

## 7. Audit trail

For substantial work, keep a compact evidence trail in the PR/body or existing project acceptance mechanism containing:

- goal/exit predicate;
- base and exact candidate head;
- semantic changed-file scope;
- material decisions and rejected alternatives when relevant;
- exact-head workflow names/run numbers/results;
- artifact names and whether they were actually inspected;
- independent verifier verdict and evidenced findings;
- normalization topology when applicable;
- merge SHA and post-merge integration ref when merged.

Do not commit noisy private scratch logs solely to prove activity. The trail exists so another agent can resume and audit the decision, not to preserve internal reasoning.

## 8. Stop and override rules

Stop immediately when the user explicitly pauses or redirects the work. Otherwise continue reversible authorized work through the exit predicate.

Surface a question only for a genuinely new product/preference decision, unauthorized irreversible/destructive action, irreconcilable concurrent conflict, or missing external information that cannot be recovered from authoritative sources. Continue independent work while such a blocker exists.

This playbook is subordinate to higher-priority platform/system rules and the AIOS Agent Constitution. It must never be used to bypass required confirmation, safety controls, repository truth boundaries, or acceptance gates.
