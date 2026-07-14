# Controlled Regulatory Classification v10.4

## Outcome

Phase 10A now has a persisted, evidence-bound classification proposal layer
between immutable source comparison and regulatory-change review. A model may
assist classification, but it cannot approve a change, publish a verified rule,
update a pathway, or communicate a claim.

## Governed flow

```text
official source snapshots
  -> deterministic unified diff
  -> deterministic classification proposal
  -> optional configured model-assisted proposal
  -> schema, category, confidence, and diff-citation validation
  -> deterministic fallback on disabled, unavailable, invalid, or failed model
  -> human classification accept/reject
  -> separate regulatory-change review
  -> separate verified-rule publication
```

Each proposal stores the exact previous/current snapshot identifiers, proposed
change type and materiality, summary, rationale, confidence, cited diff lines,
method, provider/model metadata, prompt version, fallback reason, creator,
reviewer, notes, timestamps, and immutable audit events.

## Safety boundaries

- Model use is opt-in through both an operator request and
  `REGULATORY_MODEL_CLASSIFICATION_ENABLED=true`.
- A supported `LLM_PROVIDER` and its credential must also be configured.
- Only the fixed change-type and materiality vocabularies are accepted.
- Model input is limited to the numbered unified diff, with bounded line and
  total prompt sizes; full snapshot documents are not sent by this workflow.
- Model evidence line numbers must resolve to the stored unified snapshot diff.
- Model confidence is capped at `0.95`; it is proposal confidence, not legal or
  regulatory truth confidence.
- Any model execution, parsing, validation, category, or citation failure
  produces a persisted deterministic fallback with a visible reason.
- A new proposal supersedes an unresolved older proposal without deleting it.
- An accepted classification may update only the still-pending change's type,
  materiality, and summary.
- A pending change with proposal history cannot be approved until one proposal
  is explicitly accepted.
- Existing human validation and verified-rule publication gates remain intact.

## API

- `GET /api/v1/regulatory-intelligence/classification-proposals`
- `POST /api/v1/regulatory-intelligence/changes/{change_id}/classification-proposals`
- `POST /api/v1/regulatory-intelligence/classification-proposals/{proposal_id}/review`

Snapshot capture responses also include the automatically created deterministic
proposal for the first detected change returned by that capture.

## Operator workspace

The Regulatory Intelligence change review displays proposal history, status,
method, confidence, provider, prompt version, rationale, fallback reason, and
the exact cited diff lines. Operators may generate deterministic or configured
model-assisted proposals and must record notes when accepting or rejecting one.

## Migration and rollback

Migration `0020_regulatory_classification_proposals` creates the proposal
ledger and its provenance indexes. Downgrade drops only that table; it does not
alter source snapshots, regulatory changes, human reviews, or verified rules.
