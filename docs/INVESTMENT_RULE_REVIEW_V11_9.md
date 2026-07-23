# Independent Investment-Rule Review v11.9

Phase 11.9 converts source extraction into a controlled decision rather than treating extracted text as verified intelligence.

## Control boundary

A proposal may target only a draft mobility-pathway version in the `investment`, `wealth`, `business`, or `entrepreneur` domain. The pathway must already reference:

- an active, same-country official source in an eligible domain; and
- an immutable source snapshot with a content hash.

Only one pending proposal may exist for a pathway version. Rule keys must be unique in the proposal, and guaranteed authority-outcome language is rejected.

## Independent decision

The proposal creator cannot review their own proposal. An authenticated reviewer must record an approval or rejection and a substantive reason.

- Rejection creates an append-only decision record and no verified rules.
- Approval creates source- and snapshot-pinned verified rules, supersedes the unverified pathway draft, and creates a replacement draft containing the approved rule identifiers.
- Approval does not publish the replacement pathway and does not create or publish an investment program. Those remain separate human decisions.

All proposal and review mutations produce audit events. Read-only users cannot mutate the ledger.

## Austria status

The v11.8 Austria Self-employed Key Worker extraction contains four proposed rules covering the macroeconomic-benefit test, the EUR 100,000 capital indicator and alternatives, the separate AMS/residence-authority roles, and the 24-month route duration.

The proposal is intentionally left `pending_review`. A reviewer must compare every statement with the exact Austrian Federal Government snapshot identified by SHA-256 `905a6e47c821be64863efc9037e99b611e31d0d797a6b6799d1fc8b2e5f8ba38` before making a decision in the Investment Programs workspace.
