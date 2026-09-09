# Post-Redesign Roadmap — Autonomous Global Regulatory Intelligence

**Status:** SCHEDULED — dependency-gated behind completion/sealing of the AIOS V2 redesign programme
**Priority after redesign:** HIGH
**Purpose:** Build a high-autonomy, evidence-grounded global immigration intelligence organization capable of discovering, extracting, verifying, maintaining, and safely promoting visa / residence / work / study / mobility rules across jurisdictions with minimal routine human intervention.

## 1. Product objective

AIOS should not depend on a human professional manually reading every ordinary government update before the system can remain current.

Target operating loop:

```text
official-source discovery
  -> source identity / authority certification
  -> immutable SourceSnapshot
  -> multilingual extraction
  -> structured rule assertions
  -> independent machine cross-checks
  -> contradiction / temporal / jurisdiction validation
  -> calibrated evidence sufficiency
  -> governed risk + authority gate
  -> automatic VerifiedRule promotion when machine-verifiable
  -> knowledge graph / pathways / eligibility / evidence requirements
  -> continuous monitoring, drift detection, re-verification and rollback
```

Human specialists are an exception path for ambiguity, contradiction, insufficient authoritative evidence, novel/high-consequence interpretation, or machine disagreement. Human review is not the default throughput mechanism.

## 2. Capacity target

The system must be designed for broad global coverage rather than one-country hard-coding:

- countries and dependent jurisdictions;
- visa, residence, work, study, family, business/investor, talent, remote-work/digital-nomad and permanent-residence routes where authoritative sources exist;
- nationality-dependent conditions and exemptions;
- bilateral / regional regimes such as EU/EEA/Schengen where relevant;
- pathway eligibility, documents, fees, salary/funds thresholds, quotas, validity, renewals, dependants, processing constraints and effective dates;
- legislation, regulations, official gazettes, immigration ministries, government portals, consulates/embassies and other certified competent authorities;
- multilingual source material with original-language evidence retained.

Coverage must be explicit. Unknown, unsupported, stale, conflicted and incomplete are first-class states. AIOS must never manufacture global coverage merely because an LLM can answer a question.

## 3. Organizational architecture

Create a durable **Global Immigration Intelligence Department** rather than one unconstrained super-agent.

Proposed persistent roles/capabilities:

1. **Global Source Discovery Officer** — discovers candidate official authorities and source surfaces.
2. **Authority & Source Certification Officer** — verifies source identity, jurisdiction, authority class and trust policy.
3. **Regulatory Retrieval Officer** — monitors certified sources and creates immutable snapshots/fingerprints.
4. **Multilingual Regulatory Analyst** — extracts normalized rule assertions while retaining original-language evidence.
5. **Cross-Source Verification Officer** — independently checks assertions against additional authoritative sources when available.
6. **Legal Consistency / Contradiction Officer** — detects conflicts, scope errors, exceptions and hierarchy problems.
7. **Temporal Intelligence Officer** — resolves publication/effective/expiry/supersession dates and historical versions.
8. **Rule Compiler** — converts supported assertions into deterministic AIOS rule contracts.
9. **Adversarial Verification Officer** — attempts to falsify proposed rules and tests boundary cases before promotion.
10. **Regulatory Release Governor** — applies deterministic promotion policy and automatically publishes only when the required machine evidence/gates are satisfied.
11. **Drift / Incident Officer** — continuously rechecks published rules, quarantines suspicious/stale rules and initiates rollback/reverification.
12. **Coverage Planner** — measures jurisdiction/pathway gaps and schedules acquisition work.

These are organizational capabilities and may share model/runtime infrastructure. Separation exists to create independent evidence and disagreement, not to multiply decorative agents.

## 4. Accuracy architecture — evidence beats model confidence

No rule may become canonical merely because a model reports high confidence.

A promotion decision should combine independently inspectable evidence such as:

- certified official source authority;
- immutable snapshot + content fingerprint;
- exact supporting passage/locator;
- jurisdiction and route scope match;
- original-language extraction plus translation lineage when applicable;
- deterministic schema/type/unit/currency/date validation;
- source hierarchy analysis;
- independent extraction/verifier agreement;
- cross-source corroboration when available;
- contradiction search;
- effective-date / supersession analysis;
- regression against existing VerifiedRules;
- pathway and eligibility boundary tests;
- adversarial/falsification pass;
- freshness policy;
- provenance completeness.

LLM confidence is diagnostic metadata, not legal authority.

## 5. Multi-model / independent-verifier policy

For consequential extraction, avoid a single-model self-review loop.

Use role-separated passes and, where justified by consequence/uncertainty, independent model/provider families or deterministic verifiers. The system should measure agreement at the assertion level, not accept majority voting blindly.

Disagreement produces investigation work. It does not get averaged into truth.

Frontier models are escalation resources for difficult interpretation; cheaper models/deterministic tooling should handle routine extraction and validation where measured quality permits.

## 6. Automatic promotion classes

The goal is maximum safe automation, not maximum human approval.

### Class A — deterministic / routine

Examples: clearly stated fee, threshold, document name, validity period, application URL, explicit effective date.

May auto-promote when certified authoritative evidence and all required deterministic/machine verification gates pass.

### Class B — structured eligibility change

Examples: job-offer condition, qualification criterion, age condition, nationality restriction, dependant condition.

May auto-promote only with stronger independent verification, contradiction checks, temporal checks and regression/boundary tests.

### Class C — novel or interpretive high-consequence rule

Examples: ambiguous statutory interpretation, conflicting competent authorities, unclear transitional law, materially novel pathway semantics.

Machine system performs the full analysis first, but promotion escalates to specialist review unless future measured evidence justifies a narrower automated class.

### Class D — insufficient / conflicted

Never promote. Preserve evidence and state as `conflicted`, `insufficient_evidence`, `stale`, `unsupported`, or another truthful canonical state.

Promotion classes must be policy-driven and versioned. No employee may grant itself a higher authority class.

## 7. Automatic demotion, quarantine and rollback

Autonomy must work in both directions.

AIOS must automatically quarantine or demote a previously published rule when required evidence disappears, a certified authority contradicts it, a newer rule supersedes it, freshness expires, or regression/adversarial checks reveal a material defect.

Downstream pathways/cases must know that an input rule changed or was quarantined. Historical decisions retain the exact rule/source fingerprints used at the time.

## 8. Continuous global intelligence

The department should operate as a persistent system:

```text
coverage map
 -> prioritized source monitors
 -> change detection
 -> assertion-level diff
 -> verification swarm
 -> promotion/quarantine
 -> dependency impact analysis
 -> affected pathway/rule recomputation
 -> material-change notification
 -> measured learning
```

Polling frequency should be risk/change-rate aware rather than identical for every source. Official feeds/APIs/webhooks should be preferred where available; respectful conditional retrieval and content hashing should avoid unnecessary scraping.

## 9. Knowledge representation

Do not store visa knowledge as prose blobs alone.

Minimum normalized concepts should include:

- jurisdiction;
- competent authority;
- pathway / permit / visa category and version;
- applicant/nationality scope;
- purpose;
- eligibility predicates;
- exclusions/exemptions;
- thresholds and units;
- required evidence/documents;
- fees;
- validity/renewal;
- dependants;
- quota/cap where represented;
- application channel/location;
- publication/effective/expiry/supersession dates;
- source snapshots and locators;
- assertion confidence/evidence sufficiency metadata;
- verification results;
- VerifiedRule fingerprints;
- dependency links;
- uncertainty/conflict state.

The eligibility engine consumes versioned VerifiedRules; it does not independently reinterpret the open web for every client case.

## 10. Evaluation programme before broad autonomy

Automatic publication authority must be earned with measured performance.

Build a continuously growing gold/evaluation corpus across jurisdictions, languages, rule types and change patterns. Include difficult counterexamples, stale pages, contradictory guidance, transitional provisions, archived content and intentionally mutated sources.

Measure at least:

- source-authority classification precision;
- assertion extraction precision/recall;
- numeric/date/unit accuracy;
- scope and exception accuracy;
- contradiction detection;
- supersession/effective-date accuracy;
- false-promotion rate;
- false-quarantine rate;
- time-to-detect and time-to-verified-update;
- provenance completeness;
- pathway/eligibility regression accuracy;
- human escalation rate;
- specialist overturn rate;
- calibration by promotion class/jurisdiction/source type.

The primary safety KPI is not raw automation percentage. It is **correct autonomous throughput at an acceptably tiny false-promotion rate**.

## 11. Red-team and mutation testing

Every promotion pipeline should face adversarial cases such as:

- one digit changed in a salary threshold;
- currency/unit changes;
- old page ranking above new page;
- future effective date mistaken for current law;
- exception paragraph omitted;
- embassy guidance narrower than statute;
- translated page lagging original language;
- route with same/similar name in another jurisdiction;
- temporary policy notice;
- contradictory official pages;
- deleted/moved source;
- malicious or compromised non-official lookalike domain;
- LLM-generated unsupported interpretation.

A system that cannot reliably reject these cases is not ready for automatic publication authority.

## 12. Human intervention minimization

Human specialists should receive **exception packets**, not raw research workloads.

An escalation packet should already contain:

- exact disputed assertions;
- source snapshots/passages;
- authority hierarchy;
- machine interpretations;
- verifier disagreement;
- historical rule/version;
- detected contradiction;
- downstream impact;
- bounded question requiring judgment.

Human resolution becomes new evaluation evidence and may improve future routing/verification skills, but it does not silently grant new authority.

Target maturity is for routine, well-structured official changes to flow end-to-end without humans while humans concentrate on genuinely interpretive cases.

## 13. Learning and self-improvement

Connect this department to the AIOS Employee Capability & Skills Architecture.

Repeated successful acquisition/verification procedures may automatically become versioned reusable skills after machine validation. The system may learn source patterns, extraction strategies, verifier routing and regression tests.

Permanent invariant:

> Automatic capability acquisition does not imply automatic authority acquisition.

Learned skills cannot weaken promotion gates, grant themselves credentials, certify arbitrary sources, or expand legal publication authority.

## 14. Audit / replay requirements

Every canonical rule must be reconstructable:

```text
VerifiedRule
 -> promotion decision + policy version
 -> normalized assertions
 -> verification/falsification results
 -> model/provider/tool lineage where relevant
 -> SourceSnapshot(s)
 -> exact source locator(s)
 -> authority certification
 -> retrieval timestamp/fingerprint
```

Historical eligibility/pathway decisions must remain replayable against the exact rules that existed at the decision time.

## 15. Living Organization / UI integration

After the redesign is sealed, Global Intelligence should be visible as real organizational work rather than a generic dashboard:

- jurisdiction coverage map;
- source health/freshness;
- active regulatory changes;
- verification disagreements;
- auto-promoted rules;
- quarantined/conflicted rules;
- affected pathways/cases;
- escalation queue;
- evidence/provenance inspector;
- temporal rule history/replay;
- department/employee capability and current work.

Visualization remains downstream of canonical activity. No animated analyst may imply work that is not represented by real state.

## 16. Delivery sequence after redesign

1. Reconcile existing regulatory intelligence, VerifiedRule, SourceSnapshot, pathway and professional-review contracts.
2. Establish jurisdiction / authority / certified-source registry.
3. Build global coverage graph and explicit unsupported-state model.
4. Implement multilingual assertion extraction contract.
5. Add independent cross-source and assertion-level verification.
6. Add temporal/supersession engine.
7. Add contradiction + source-hierarchy reasoning.
8. Add deterministic rule compiler and pathway/eligibility regression harness.
9. Build adversarial/mutation verification officer.
10. Implement versioned automatic-promotion policy classes.
11. Implement quarantine/demotion/rollback and dependency impact propagation.
12. Build gold corpus + continuous evaluation/calibration programme.
13. Pilot autonomous publication on bounded low-risk rule classes/jurisdictions.
14. Expand authority only when measured false-promotion/overturn performance passes defined gates.
15. Scale coverage country-by-country/source-class-by-source-class without hard-coding the architecture to Austria.
16. Integrate Global Intelligence into the redesigned Operator / Owner / Living Organization surfaces.
17. Continue measured learning, source discovery and automatic skill acquisition.

## 17. Non-goals / permanent prohibitions

- No LLM answer becomes canonical merely because it sounds plausible.
- No confidence percentage alone authorizes publication.
- No fabricated source, citation, coverage or corroboration.
- No silent overwriting of historical legal state.
- No unofficial source silently promoted to official authority.
- No majority-vote shortcut over unresolved authoritative contradiction.
- No autonomous expansion of an employee's own permissions/authority.
- No client eligibility conclusion based on unverified open-web interpretation when a VerifiedRule contract is required.
- No visual animation used as evidence that regulatory work occurred.

## 18. Definition of success

This programme succeeds when AIOS can maintain broad, explicit global immigration knowledge with:

- high autonomous throughput for routine machine-verifiable regulatory changes;
- extremely low false-promotion rate;
- complete source/evidence/temporal lineage;
- automatic contradiction, drift, quarantine and rollback behavior;
- deterministic downstream rule/pathway/eligibility regression;
- transparent unsupported/conflicted states;
- measured jurisdiction/language/rule-class quality;
- specialist intervention concentrated on genuinely ambiguous/high-consequence interpretation rather than routine data entry;
- full replay of what AIOS knew, why it accepted it, what changed, and which downstream conclusions depended on it.

**North-star principle:**

> **Automate research, verification, promotion, monitoring and correction as far as evidence permits. Escalate judgment, not routine work.**
