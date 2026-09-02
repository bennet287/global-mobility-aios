# Phase 13.17 — Owner-Led Human Acceptance Checkpoint

**Date:** 2026-08-18  
**State:** IN PROGRESS / PAUSED BY EVALUATOR  
**Baseline under evaluation:** `b8393d0b6bdaf02c958bb151b4909b5b82fd0d09` (`feat: complete integrated role experience acceptance`)  
**Branch:** `roadmap/global-mobility-aios-v11`

## 1. Evaluation status and limitation

Phase 13.17 is intended to gather genuine human-use evidence after the accepted 13.16 integrated role experience.

The current evaluator is the project Owner. This is therefore **owner-led human acceptance**, not independent third-party acceptance. The evaluator explicitly reported that an independent external evaluator is not currently practical to find or afford. This limitation must remain visible in any later Phase 13 disposition and must not be rewritten as independent validation.

The session used the real sealed local application rather than the earlier isolated browser mock harness. The backend and frontend were run locally against the accepted repository state. No Phase 13.17 product correction was applied during this session, and no finding below is treated as fixed merely because its intended semantics were explained after the unbiased task.

**Phase 13.17 is not PASS.** The evaluation is intentionally paused and will resume later.

## 2. Method used

The evaluator was given scenario-based tasks without being told the intended destination or exact control wherever doing so would bias the result. After the evaluator answered or became blocked, the intended model could be explained and the finding classified.

The session covered:

- Owner / Human Board first-impression and authority interpretation;
- Global Intelligence programme and VerifiedRule discoverability;
- source-review/evidence terminology comprehension;
- Board Room authority discovery;
- Owner diagnosis through Cockpit, Owner Inbox, and cross-department friction;
- Cockpit vs Operations vs My Mobility role separation;
- first Professional / Operator case task for missing documents.

The session was paused before Professional Task 2 because the evaluator found the process repetitive/boring. The remaining acceptance should use shorter scenarios and fewer screenshots while preserving unbiased task wording.

## 3. Positive human-acceptance evidence so far

### Owner / Board

- Cockpit desktop presentation was visually coherent in the live local application; no material clipping, overlap, broken loading state, or obvious visual corruption was observed in the submitted screenshots.
- The evaluator correctly concluded that no Owner intervention was currently required when Owner Attention, Board decisions, Board risk escalations, pending human requests, and overdue active work were all zero. Confidence was **medium**, not high.
- Global Intelligence → **Programmes** was discovered naturally when asked where new programmes would be investigated. This indicates that the deeper programme information architecture is discoverable even though the summary counters do not drill down.
- **Board Room** was discovered naturally for a hypothetical Board-reserved decision.
- The evaluator moved toward Cockpit/department inspection rather than immediately mutating state when asked to diagnose an unknown organizational problem.
- After guidance, **Owner Inbox** was understood as the place to inspect Owner-relevant decisions/escalations, with the current zero-state correctly interpreted as no attention required.
- **Operational Intelligence** was naturally identified as the starting area for blockers/dependencies/live work.
- Cross-department friction was rated **somewhat obvious** once opened.

### Professional / Operator

- The Operations workspace was visually recognizable as the professional workspace once explicitly opened.
- For **Demo 2 — Documents Pending**, the evaluator found and opened the correct case without guidance.
- The evaluator correctly identified:
  - `Financial Proof` — Missing;
  - `Admission Letter` — Missing;
  - `Insurance` — Needs Review;
  - `Passport` — Verified.
- Basic document status vocabulary was understood:
  - **Needs Review** → human/professional review required;
  - **Missing** → document is absent;
  - **Verified** → document has passed verification.

## 4. Findings — Owner / Board

### O-01 — Global Intelligence change-mix cards lack direct drill-down

**Severity:** Minor-to-Moderate usability / information-architecture issue

**Observed:** The evaluator naturally tried to click cards such as `New Program`, expecting the underlying programme/change records and their sources. The cards behaved as passive counters.

**Important nuance:** The evaluator later found the **Programmes** tab naturally, so the deeper information architecture is not completely hidden. The primary defect is the missing shortcut/drill-down from the summary metric.

**Expected direction:** A summary count should open the filtered underlying records and preserve access to source/provenance detail.

---

### O-02 — “Verified Rule” is not understandable to the Owner without prior AIOS knowledge

**Severity:** Moderate-to-Major trust/comprehension issue

**Observed evaluator reaction:** The evaluator could see the concept but did not know its purpose.

The UI currently exposes an internal governance term without sufficiently translating its human meaning: an evidence-backed structured rule that has passed the required review/publication gates and can be relied on only within its governed scope.

This is important because users must not confuse AIOS-derived structure with official-source/legal truth.

---

### O-03 — Verified-rule totals and approval-queue counts are semantically ambiguous

**Severity:** Moderate

**Observed:** Global Intelligence displayed `Verified Rules: 1`, while the Rule approvals tab displayed `0` and the rules workspace showed no initial rule assertions.

This may be a legitimate state distinction (for example, one already verified/published rule and zero pending approvals), but the interface does not explain that distinction.

**Expected direction:** Separate and label states such as verified/published, pending review, and draft assertions rather than presenting counts that appear contradictory.

---

### O-04 — `Verified Rules: 1` cannot be inspected from the summary

**Severity:** Moderate

**Observed:** The evaluator clicked the visible `1` expecting the underlying rule, reviewer, jurisdiction, and source. Nothing happened.

For an evidence/governance product, a trusted-looking count should lead to its underlying evidence/provenance record.

---

### O-05 — Evidence/provenance terminology is not understandable without training

**Severity:** Major usability / trust-comprehension issue

On **Independent Source Review**, the evaluator reported:

- `immutable source evidence` → **no idea**;
- `exact source snapshot` → interpreted as possibly a screenshot;
- `structured projection` → **no idea**;
- official source vs AIOS interpretation → not clearly distinguished;
- overall page → **confusing**.

This is a safety-relevant comprehension defect because users need to distinguish:

1. official source;
2. saved/retrieved source version;
3. AIOS extraction/structured interpretation;
4. human review/certification;
5. any later VerifiedRule/publication state.

**Expected direction:** Keep the technical model, but pair it with plain-language labels/explanations such as `Official source`, `Saved source version`, `AIOS extraction`, and `Human review`.

---

### O-06 — `Pause organization` may be interpreted as a general troubleshooting fallback

**Severity:** Major governance/usability risk

**Observed:** When imagining an unknown serious problem, the evaluator said they might enter Board Room, inspect the page, and if they still could not find the issue, **pause the organization while fixing/investigating it**.

That is too broad a mental model for a global control. The intended use should be an emergency governance stop when continued execution itself is unsafe, not a default response to uncertainty.

**Expected direction:** Make emergency-stop semantics, scope, consequences, preconditions, and safer diagnostic alternatives unmistakable before activation.

---

### O-07 — Unknown-issue diagnosis can devolve into manual department hunting

**Severity:** Moderate operational-diagnosis issue

**Observed:** When told that something seemed wrong but the responsible department was unknown, the evaluator returned to Cockpit and began inspecting departments manually, including Legal.

Department drill-down itself was understandable, but the product did not strongly route the evaluator toward cross-organization diagnostic surfaces before manual inspection across many domains.

**Expected direction:** Strengthen the path from Cockpit → Owner Inbox / Operational Intelligence / cross-department friction before department-by-department hunting.

---

### O-08 — Owner Inbox categories are understandable only at a broad level

**Severity:** Moderate

**Observed:**

- no current Owner attention was correctly understood from the zero state;
- `Critical Owner attention` was interpreted broadly as possibly a tech issue or a new programme needing approval;
- `Human / escalation required` was interpreted as a human decision/intervention;
- the evaluator expected real items to be clickable and route to the underlying issue/source/context;
- overall page rating: **Somewhat obvious**.

The page correctly says that Owner Inbox routes authority rather than executing it, but this distinction is not yet prominent enough in the human mental model.

---

### O-09 — Cross-department relationship direction is not self-explanatory

**Severity:** Moderate

**Observed:** Asked to interpret a hypothetical `Legal → Document & Evidence Operations` relationship, the evaluator interpreted Legal as “the blocker” and Document & Evidence Operations as “the dependency.”

That is not sufficient to know who owns the blocking condition, whose work is affected, or which direction the dependency runs.

**Expected direction:** Explicit relationship language such as:

- `Blocked work: Legal`;
- `Blocked by: Document & Evidence Operations`;
- `Reason: ...`;
- or `Legal depends on → Document & Evidence Operations`.

---

### O-10 — `Require human action` and `Escalated / overdue` need clearer plain-language meaning

**Severity:** Minor-to-Moderate

**Observed:**

- `Require human action` was understood generally as needing human intervention/decision;
- `Escalated / overdue` was interpreted as possibly an SLA or KPI.

The current labels describe workflow/materiality state, not merely metrics, and should make that clearer.

---

### O-11 — Professional case work is not sufficiently distinguishable from Mobility User case information

**Severity:** Major role-separation/navigation issue

**Observed:** Given a scenario where a case had missing documents requiring **professional follow-up** but no Owner authority, the evaluator navigated through **Profiles → Timelines → My Mobility** and considered the My Mobility `Documents` card a plausible destination.

The intended destination was **Operations**.

The architecture technically preserves the role split, but the human navigation experience does not make the split clear enough.

---

### O-12 — Icon-only sidebar creates substantial navigation friction

**Severity:** Major usability / discoverability issue

**Evaluator feedback:** The icon-only sidebar is a “pain” because names appear mainly on hover; persistent **icons + names** would make navigation easier.

This is supported by the observed role-navigation failure in O-11. The evaluator had to infer or repeatedly hover to distinguish Cockpit, Operations, Profiles, Timelines, My Mobility, Source Review, and other destinations.

**Expected direction:** On desktop, strongly consider an expanded-by-default or user-expandable navigation rail with persistent icon + text labels, while retaining a compact collapsed option.

## 5. Findings — Professional / Operator

### P-01 — Document statuses are understandable, but the professional next action is not explicit enough

**Severity:** Moderate

**Observed:** In `Demo 2 — Documents Pending`, the evaluator correctly identified two missing documents and one document needing review, but proposed the next action as:

> upload the remaining two documents to finish the case

A professional may not possess or be authorized to supply client documents. The actual governed next action could instead be to request documents from the client, review an existing uploaded document, wait for client action, or use another specialist workflow.

**Expected direction:** Translate document state into explicit governed next-action choices rather than forcing the operator to infer whether to request, upload, review, wait, or route elsewhere.

---

### P-02 — `Context alignment` and `persisted pathway decision context` are not understandable to the professional user

**Severity:** Major comprehension / workflow-confidence issue

The case page prominently displayed:

- `Context alignment not established`;
- `No persisted pathway decision context`.

When asked what either meant, the evaluator answered **No** / did not understand them.

These warnings are safety-relevant because they explain why historical or context-mismatched document/timeline/evidence records cannot support the current decision. Internal precision is not enough if the professional cannot understand what information is currently safe to rely on.

**Expected direction:** Keep the deterministic alignment invariant, but translate it into professional language, for example:

> **Current pathway not confirmed yet.** Some older document and timeline records are shown for reference only and are not being used to decide current readiness.

## 6. Correction themes suggested by the evidence — not implemented yet

The following are candidate themes only. They are **not accepted implementation requirements until the remaining evaluation is completed and the findings are triaged together**.

1. **Navigation clarity**
   - persistent icon + label desktop sidebar;
   - clearer visual separation of Cockpit / Operations / My Mobility role surfaces.

2. **Metric-to-evidence drill-down**
   - clickable Global Intelligence summary counts;
   - direct access from VerifiedRule counts to rule, jurisdiction, reviewer, official source, saved snapshot, and publication/review state.

3. **Plain-language evidence/governance translation**
   - preserve exact domain semantics underneath;
   - add human-readable labels and explanations for source snapshot, immutable evidence, structured projection, VerifiedRule, context alignment, and decision context.

4. **Safer Owner controls**
   - make Pause Organization clearly an emergency governance control;
   - route uncertainty toward diagnosis before global intervention.

5. **Owner diagnostic routing**
   - strengthen Cockpit → Owner Inbox / Operational Intelligence / cross-department friction path;
   - reduce manual department hunting.

6. **Cross-department directionality**
   - explicitly label waiting/affected department, owning/blocking department, dependency direction, and reason.

7. **Professional next-action clarity**
   - clearly distinguish `request from client`, `review submitted document`, `upload/attach if authorized`, `wait`, and `route to specialist` actions.

## 7. Resume checkpoint

**Do not repeat the completed Owner tasks or Professional Task 1.**

Resume Phase 13.17 at:

### Professional Task 2 — Blocked Visa Claim / human-review case

Scenario:

> Start with the active case that appears to have the most serious review problem. Find the case that needs human review / truth resolution and determine what is blocked, why it is blocked, what evidence/claim is causing the problem, and what governed action should happen next.

The likely visible case from the current Operations priority queue is `Demo 1 — Blocked Visa Claim`, but the resumed task should still be phrased as an unassisted scenario before naming the expected case to avoid bias.

Questions to capture:

1. What exactly is blocked?
2. Why is it blocked?
3. What evidence or claim is causing the problem?
4. What does the evaluator believe the professional should do next?
5. Was the diagnosis obvious, somewhat obvious, or confusing?

After this, continue the Professional / Operator scenarios with shorter tasks, then perform Mobility User / secure Portal owner-led acceptance.

## 8. Current disposition

- Phase 13.16.10 remains the sealed accepted baseline.
- Phase 13.17 remains **IN PROGRESS**.
- No Phase 13.17 finding is considered fixed yet.
- No final external-human PASS is claimed.
- No independent third-party validation is claimed.
- Final Phase 13 disposition remains locked until the resumed acceptance work and any required bounded corrections are completed and re-accepted.
