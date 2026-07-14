# Global Live Intelligence Dashboard v10.0

## Outcome

Phase 10 now has a dedicated read-only global intelligence surface built from the
reviewed regulatory-intelligence foundation. It turns controlled source-change
records and active verified rules into an operator dashboard without claiming that
the current onboarded jurisdictions represent complete global coverage.

## Delivered surface

- API: `GET /api/v1/global-intelligence/dashboard`
- Web: `/global-intelligence`
- Window selector: 30, 90, 180, or 365 days in the web workspace
- API window: 1 to 730 days

The response includes:

- new programme and programme-removal events;
- countries and changes detected today;
- immigration-change activity by type, status, and materiality;
- processing-time changes;
- skilled-occupation and shortage-list changes;
- salary and investment-threshold changes;
- activity by onboarded country, territory, or autonomous jurisdiction;
- an evidence-based Opportunity Radar;
- registered jurisdiction, source, and verified-rule coverage counts.

## Evidence and review rules

Every displayed change retains its source, jurisdiction, materiality, review state,
detected time, and reviewer when available. Monitoring views include pending events
so operators can see the validation queue. This does not turn a pending event into a
verified rule.

The Opportunity Radar has a stricter boundary:

- only `published` regulatory changes contribute;
- new programmes, occupation-list changes, processing-time changes, policy changes,
  quotas, salary thresholds, and investment thresholds have deterministic weights;
- the output is labelled `evidence_based_activity_signal`;
- it is not predictive and is not a visa or destination recommendation.

## Coverage boundary

`scope.global_coverage_claim_ready` remains `false`. The UI displays the associated
warning because the current data covers onboarded jurisdictions only. Complete global
coverage requires the versioned Phase 10B registry, official-source onboarding, gap
tracking, and its release gate.

The heatmap therefore visualizes monitored activity, not country quality, user fit, or
the absence of immigration changes in jurisdictions that have not yet passed coverage
checks.

## Change classification

The deterministic classifier now recognizes `investment_threshold_change` in addition
to programme introductions/removals, rule changes, processing times, salary thresholds,
age limits, occupation lists, quotas, and policy changes.

## Verification

Automated coverage verifies that:

- today and window totals aggregate correctly;
- country heatmap counts preserve pending and published review states;
- only human-published evidence contributes to the Opportunity Radar;
- dashboard safety flags prohibit predictive and recommendation claims;
- global-coverage readiness remains false;
- investment-threshold language is classified correctly.

## Next Phase 10 priorities

1. Use the v10.2 human-review workflow to complete immigration-rule and parent assessments.
2. Add at least one reviewed primary authority and official source per required jurisdiction.
3. Add dashboard filters for freshness, coverage, authority, confidence, materiality,
   and review state.
4. Build global country ranking from the complete reviewed pathway catalogue.
5. Extend timelines into versioned cross-pathway and multi-country scenarios.
