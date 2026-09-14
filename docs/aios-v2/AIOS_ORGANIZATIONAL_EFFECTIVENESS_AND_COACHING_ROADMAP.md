# AIOS Organizational Effectiveness & Coaching Roadmap

**Status:** ACTIVE CROSS-PROGRAMME ROADMAP REQUIREMENT
**Date:** 2026-09-12
**Applies to:** every AIOS department, employee, skill and governed workstream

## 1. Non-negotiable principle — independent department effectiveness

A department is not effective merely because it is connected to QA, receives feedback, has employees in the organization graph, or appears in Living HQ.

**Every AIOS department must be independently capable of performing its own mandate effectively.** QA, coaching, CEO coordination and cross-department review are improvement and assurance layers; they are not substitutes for the department's own competence.

The required model is:

```text
independently capable department
        +
internal domain-specific quality controls
        +
measured outcomes
        +
external / independent QA where risk requires it
        +
coaching and learning
        =
continually improving department
```

A department that routinely depends on QA to repair its normal output is unhealthy even if the final organization-level output passes QA.

## 2. Department Operating Contract

Every production department must eventually declare and prove:

- mandate and explicit business outcomes owned;
- work types accepted and work types refused/routed elsewhere;
- specialist positions/employees and required skill bundles;
- tools and data sources required to perform the mandate;
- permissions and authority ceiling;
- domain-specific internal quality checks performed before handoff;
- service-level/cycle-time expectations;
- queue capacity and overload behavior;
- cost/budget envelope where applicable;
- handoff acceptance criteria;
- escalation boundaries;
- known failure modes;
- outcome and quality metrics;
- coaching/learning inputs;
- autonomy promotion and revocation conditions.

No department may be declared mature solely because its agents run successfully or because another department validates its work afterward.

## 3. Independent effectiveness scorecard

Activity is not productivity. Agent runs, messages, tokens, conversations, handoffs and generated artifacts are not success metrics by themselves.

Each department must be measurable on its own work using, where applicable:

```text
outcome success rate
human acceptance / modification / rejection rate
first-pass quality
rework rate
escaped-defect rate
cycle time / SLA attainment
cost per successful outcome
evidence/provenance quality
escalation precision
handoff acceptance rate
skill effectiveness by version
repeat-failure rate
backlog age and capacity pressure
```

The system should expose a Department Effectiveness Score only when supported by sufficient underlying evidence. Scores route attention; they do not grant authority.

## 4. Quality model — QA is independent assurance, not a crutch

Each department owns first-line quality for its own domain.

```text
Department work
  → department-specific internal validation
  → department outcome / handoff
  → independent QA or risk-based sampling where required
  → feedback / defect evidence
  → coaching / skill improvement
```

Examples:

- Engineering owns correctness, tests, maintainability and regression prevention before central QA proof.
- Marketing owns factual accuracy, brand alignment, creative diversity, audience relevance and experiment design before independent review.
- Regulatory owns evidence grounding, source hierarchy, temporal correctness and contradiction handling before higher-risk independent verification/promotion gates.
- Operations owns queue correctness, deadlines, handoff completeness and SLA management before organizational QA sampling.
- Research owns source quality, citation/provenance completeness, contradiction discovery and decision usefulness before downstream acceptance.

A rising QA rejection rate is evidence of a department problem, not evidence that QA is successfully compensating for it.

## 5. OE programme

### OE.1 — Department Operating Contracts

Define the independent mandate, outcomes, skills, tools, internal quality controls, authority, capacity and escalation boundaries for every department.

**Exit gate:** no production department exists as a label-only organizational unit; each has a testable operating contract.

### OE.2 — Department Outcome & Capacity Scorecards

Create department-specific outcome, quality, throughput, capacity, rework and cost telemetry. Avoid universal vanity metrics.

**Exit gate:** the Owner/CEO can distinguish a busy department from an effective department using canonical evidence.

### OE.3 — Skill Effectiveness Telemetry

Measure important skills by skill/version, context, work type and outcome. A skill is not considered useful merely because it can be invoked.

**Exit gate:** repeated success/failure can be attributed to the relevant capability version without conflating capability with authority.

### OE.4 — Evidence-Grounded Coaching

Introduce governed Coaching Episodes based on real work, QA findings, human corrections, incidents, rejected outputs, repeated blockers or measurable underperformance.

A Coaching Episode should capture employee/role, work context, observed problem, evidence, root-cause hypothesis, affected skill/behavior, proposed intervention, validation method and measured result.

**Exit gate:** coaching produces a testable improvement proposal rather than free-form advice.

### OE.5 — QA → Coaching → Skill Improvement Loop

```text
work
 → internal department validation
 → outcome
 → independent QA / human / market feedback
 → structured defect or quality evidence
 → coaching diagnosis
 → skill/process proposal
 → replay/sandbox validation
 → shadow use
 → measured uplift or rejection
```

Learning never silently changes authority or production permissions.

**Exit gate:** accepted skill/process improvements have before/after evidence and can be rejected, rolled back or superseded.

### OE.6 — Marketing Creative Intelligence

Marketing must mature beyond generic content generation into an independently effective growth/communication department:

```text
customer + social + market + competitor + product signals
 → audience intelligence
 → divergent creative hypotheses
 → channel-specific concepts
 → factual / brand / privacy internal validation
 → controlled experiments
 → real audience response
 → analytics and attribution
 → learning / coaching
```

Marketing should develop specialist capabilities for audience intelligence, social listening, creative strategy, channel strategy, community interaction, experimentation and analytics.

Do not optimize primarily for post count, impressions, likes or follower count. Prefer qualified engagement, conversion contribution, cost per meaningful engagement, response quality, creative fatigue/diversity, repeat engagement, useful product feedback and attributable business outcomes.

External social interaction must earn autonomy progressively. Legal/regulatory interpretation, sensitive complaints, privacy issues, commitments and other high-risk communication remain governed.

**Exit gate:** Marketing can demonstrate independent first-pass quality, creative diversity and measurable learning from real audience outcomes without relying on QA to create or repair the campaign.

### OE.7 — Organization Health & Living HQ Observability

Expose truthful department health from canonical state: incoming work, completion, WIP, backlog, oldest item, blocked ratio, SLA risk, review backlog, cost pressure, handoff delay and Owner dependency where available.

Living HQ may visualize these states but never invent them.

**Exit gate:** the Owner can identify healthy, overloaded, blocked or quality-degrading departments without reading raw logs.

### OE.8 — Earned Improvement, Demotion & Restructuring

Use measured outcomes to recommend skill promotion, demotion, quarantine, replacement, department specialization, merge, split, expansion, reduction or retirement. Recommendations do not silently restructure canonical authority.

**Exit gate:** AIOS can detect persistent organizational inefficiency and produce an evidence-backed improvement proposal with governed approval boundaries.

## 6. Department-specific effectiveness requirements

### Technical / Engineering

Track deployment success, escaped defects, regression rate, rollback rate, MTTR, performance/security regressions, architecture debt, CI false-failure rate, cost per successful change and percentage of defect fixes protected by regression tests. Repeated failure classes should trigger coaching or process improvement.

### QA / Quality

QA is an independent horizontal assurance function, not merely software test execution. Track escaped defects, false-positive findings, rework prevented, regression detection, review turnaround/cost, risk coverage and human overturn rate. Use risk-based sampling for low-risk work and independent verification for high-consequence work.

### Marketing

Track qualified engagement, conversion contribution, campaign learning, human modification/rejection, creative diversity, factual/brand defects, audience-response quality, cost per meaningful engagement and attributable outcomes. Marketing owns its own internal factual/brand/creative quality before QA.

### Regulatory / Legal

Track change-detection latency, freshness compliance, false promotion, missed-change rate, contradiction backlog, stale critical rules, impact-analysis closure, exception rate and human overturn. Department competence cannot bypass evidence/authority gates.

### Operations

Track cycle time, backlog age, missed deadlines, blocked ratio, rework, handoff delay, automation failures, exception load and SLA adherence. Operations should detect capacity problems before service quality fails.

### Research

Track source quality, provenance/citation completeness, contradiction discovery, evidence reuse, decision usefulness, human acceptance and time to useful answer. Report length is not a success metric.

### Executive / CEO

Track priority quality, objective progress, resource allocation, blocker resolution, decision reversal, department imbalance detection and Owner attention consumed. A successful AI CEO should reduce unnecessary Owner intervention rather than centralize all work.

### People / HR / Coaching

Track capability gaps, coaching outcomes, workload/capacity, learning velocity, repeated failure modes and validated skill improvement. Coaching infrastructure may be coordinated here, but every department remains responsible for its own professional competence.

### Finance and other specialist departments

Each must receive its own domain-specific operating contract and outcome metrics before being considered mature. Generic organization-wide quality scores are insufficient.

## 7. Coaching authority boundary

```text
coaching → capability/process improvement
coaching != permission
coaching != authority
coaching != automatic autonomy promotion
```

Improved performance may contribute evidence to existing autonomy evaluation, but production authority remains governed independently.

## 8. Initial proving departments

Use **Technical + QA + Marketing** as the first cross-domain proof set:

- Technical proves measurable correctness and regression prevention.
- QA proves independent assurance and defect-learning loops.
- Marketing proves that the framework supports creativity, audience interaction and experimentation rather than optimizing only deterministic work.

The framework is acceptable only if it improves all three without forcing Marketing into Engineering-style metrics or making QA responsible for another department's competence.

## 9. Integration with existing roadmap

This programme extends, rather than replaces:

- AUTO.QA autonomous quality engineering;
- AUTO.ORG event-driven organizational work;
- AUTO.HANDOFF real departmental handoffs;
- AUTO.LEARN evidence-based process improvement;
- Phase 14 Native Skills Registry;
- Phase 19 Organizational Learning & Optimization;
- Phase 20 Earned Autonomy;
- Living HQ canonical organizational observability.

RI work remains the active implementation priority. OE slices may proceed in parallel only when they do not mutate the same unsealed authority/evidence/WorkItem contracts.

## 10. Destination

AIOS must eventually be able to answer, from evidence rather than narrative:

> Is this department independently good at its job? What outcomes did it produce? What did it get wrong before QA? Which skills caused success or failure? What coaching occurred? Did the intervention improve future outcomes? Is the department overloaded? Does it still need its present structure? How much Owner attention does it consume?

The target is not a collection of agents protected by one central QA layer. The target is **a company of independently competent departments, each owning its professional quality, connected by independent assurance, governed handoffs, coaching and measurable organizational learning.**