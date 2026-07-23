# Business and Wealth Mobility Advisory v11.4

## Purpose

The Business & Wealth Advisor turns an operator's detailed description of a founder, business, investor, HNWI, family-office, tax-residency, or asset-and-family objective into a structured decision-support assessment. It is designed to be commercially useful: it presents distinct routes, explains why each route may fit, identifies what would prevent execution, and provides the next evidence and specialist actions.

It does not manufacture certainty. A visa, residence, citizenship, tax, banking, investment, or authority outcome cannot be expressed as a reliable probability from the available inputs. The displayed meter is therefore a **feasibility-readiness score**, not a success guarantee or approval prediction.

## Assessment contract

Each assessment records:

- the client or unlinked scenario, primary intention, target countries, narrative, timing, family scope, and commercial facts;
- declared capital, net worth, revenue, staffing, business age, and founder experience where supplied;
- source-of-funds confirmation, disclosed risks, and controlled document references;
- information, evidence, commercial-fit, and published-pathway-grounding sub-scores;
- three ranked strategic options with rationales, blockers, next actions, linked published pathway versions, and verification state;
- an overall feasibility-readiness score and band, risk flags, escalation state, score semantics, generator, and timestamps.

The assessment is stored as a pending-review record. Review is append-only and must be performed by an authenticated actor other than the generator.

## Scoring semantics

The meter ranges from 0 to 100 and combines four visible components:

1. **Information completeness** — whether the facts needed to analyze the intention were supplied.
2. **Evidence strength** — whether the scenario is backed by controlled documents and a supportable source of funds.
3. **Commercial fit** — whether capital, operating history, revenue, staffing, experience, and timing support the proposed archetype.
4. **Pathway grounding** — whether the option is linked to a currently published, versioned pathway in the requested country and domain.

An assessment with no published route is capped below a strong-readiness result. A prohibited-conduct signal is capped at a low score and escalated. These caps prevent confident-looking results from outrunning verified evidence.

## Commercial strength and risk handling

The advisor must not stop at a generic warning when a route is weak. It should find the strongest supportable alternative: a different sequencing of founder and company moves, an operating-company route rather than passive investment, a narrower country strategy, staged evidence development, or referral to licensed immigration, tax, corporate, banking, sanctions, or investment specialists.

Material complications such as refusals, criminal history, litigation, bankruptcy, tax debt, politically exposed person or sanctions exposure, and complex source of funds are surfaced as explicit risk flags and specialist-review requirements. They are not silently ignored.

The system does not provide instructions to conceal ownership or funds, use nominees deceptively, fabricate or backdate documents, create sham operations, evade tax or sanctions, misrepresent facts, or unlawfully circumvent controls. When such an intention appears, the assessment records a blocker and proposes lawful remediation or a different route. This boundary protects clients from brittle strategies that can fail during immigration, tax, banking, due-diligence, or authority review.

## Source and review controls

- Only published pathway versions can contribute pathway-grounding points.
- Linked controlled documents must belong to the selected lead.
- The assessment retains the exact pathway-version identifiers used at generation time.
- Every create and review mutation is authenticated, actor-attributed, and audited.
- Read-only roles cannot create or review assessments.
- Human approval does not convert the assessment into legal, tax, investment, or authority advice; it confirms that a qualified operator reviewed the recorded decision support.

## API and interface

The API is exposed under `/api/v1/business-mobility-advisory/assessments` for create, list, read, and independent review operations. The `/business-advisory` workspace provides the narrative brief, commercial facts, feasibility meter, sub-scores, ranked strategies, blockers, execution sequence, escalation state, and assessment ledger.
