# Corporate Mobility Relationships v11.1

## Scope

v11.1 extends the Phase 11 corporate-mobility foundation with sponsor entities, historical
case-sponsor assignments, dependant links, and compliance calendar events. Sponsor and
dependant records remain scoped to a governed corporate case and reuse existing account and
lead controls.

## Governance boundaries

- Sponsor entities belong to one corporate account; cross-account assignment is rejected.
- A case may have only one active sponsor assignment. Removing an assignment preserves its
  record and audit history before a replacement can be assigned.
- Dependants reference existing lead profiles so consent and PII controls are not duplicated.
- Compliance events always require human review. Completion records the authenticated actor;
  waivers additionally require a reason. Completed and waived events are immutable.
- Closed cases cannot receive sponsors, dependants, or compliance events. No delete endpoints
  exist for these records.
- These records schedule and organize work only. They do not determine eligibility, approve a
  sponsor, make a regulatory claim, submit a filing, or bypass Truth Engine review.

## Data and operator surface

Alembic revision `0034_corp_relationships` creates four additive tables without rewriting the
v11.0 account or case tables. The `/corporate-mobility` workspace adds a selected-case control
plane for sponsor assignment, dependant linking, and review-gated deadline management.
