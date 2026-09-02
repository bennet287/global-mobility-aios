# Entrepreneur and Startup Dossiers v11.3

## Scope

v11.3 adds a governed founder and venture dossier to entrepreneur/startup corporate mobility
cases. The dossier records the founder, venture identity and stage, sector, destination,
incorporation context, founder role, and business-model summary.

Evidence items may record a declared amount in integer minor units and ISO currency, and may
reference an existing controlled document owned by the founder lead. Declarations are not
treated as verified funding or investment.

## Review boundary

- Only entrepreneur/startup cases may receive a venture dossier, and each case has at most one.
- Founder and destination data must remain consistent with the organizing mobility case.
- Review submission requires evidence, an explicit completeness attestation, and at least one
  controlled founder-owned document.
- The submitting operator cannot review their own dossier. Decisions are append-only and all
  mutations are actor-attributed in the audit log.
- Approval means only that the dossier was independently judged complete. It does not determine
  visa eligibility, validate funds, qualify an investment, recommend a program, or submit a
  government application.

Alembic revision `0036_entrepreneur_ventures` creates the dossier, evidence, and decision
tables. The Corporate Mobility case control plane renders the founder dossier only for the new
entrepreneur/startup case type.
