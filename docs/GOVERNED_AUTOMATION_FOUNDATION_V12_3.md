# Governed Automation Foundation v12.3 / v12.4

Phase 12.3 replaces implicit communication side effects with a durable,
account-scoped event and delivery boundary. Phase 12.4 adds credential-backed
connector configs, provider adapters, retry, and scheduled delivery workers.
Together they prepare email, messaging, calendar, and CRM integrations
without silently enabling an external provider.

## Domain events

The following corporate operations create automation events in the same
database transaction as the source mutation:

- corporate mobility case creation;
- corporate mobility case status changes;
- compliance event creation;
- compliance event completion or waiver;
- relocation-task status changes.

Every event has a unique idempotency key, corporate account, case, source
entity, actor, occurrence time, minimized payload, and processing state.
Reusing a key for the same event returns the existing record. Reusing it for a
different tenant, event type, or entity fails closed.

## Account-scoped rules

Each rule belongs to one active corporate account and one supported event
type. A rule can project an event into one or more named destinations:

- email;
- messaging;
- calendar;
- CRM.

Rules from one account never match events from another. Paused rules remain
auditable but stop producing new delivery records. Event payloads exclude
internal notes and direct contact fields.

## Review and dispatch boundary

Email, messaging, and calendar rules always require human approval. The actor
who caused the event cannot approve its external delivery. Approval changes a
delivery to `ready`; rejection is terminal. CRM-only rules may explicitly use
an approval-free `ready` state for a controlled internal synchronization
queue.

This release does not claim that a provider accepted a delivery. A separate
dispatch-receipt action records the connector actor, provider message
identifier, timestamp, and attempt count only after a ready delivery has been
processed.

## Operator workspace

The `/automation` Automation Hub provides:

- corporate-account selection;
- rule creation and channel destination mapping;
- rule pause and reactivation;
- event-ledger visibility;
- pending-delivery review with mandatory notes;
- ready and dispatched metrics.

The workspace uses the established ivory and indigo operating-system visual
language and is available from the named sidebar navigation.

## API surface

- `POST /api/v1/automation/rules`
- `GET /api/v1/automation/rules`
- `POST /api/v1/automation/rules/{rule_id}/status`
- `POST /api/v1/automation/events`
- `GET /api/v1/automation/events`
- `GET /api/v1/automation/deliveries`
- `POST /api/v1/automation/deliveries/{delivery_id}/decision`
- `POST /api/v1/automation/deliveries/{delivery_id}/dispatch-record`
- `POST /api/v1/automation/connectors`
- `GET /api/v1/automation/connectors`
- `POST /api/v1/automation/connectors/{config_id}/status`
- `POST /api/v1/automation/deliveries/{delivery_id}/dispatch`

Rule changes and dispatch recording require operator authority. Delivery
decisions also permit the reviewer role and enforce a reviewer identity
different from the event actor. Connector configs require operator authority;
connector status changes are audited.

## Remaining provider work

The broad Phase 12 automation item remains in progress. The next slice must
add connector health checks, delivery reconciliation, provider-specific
contract tests, and encrypted credential handling. No provider is enabled
merely by creating an outbox rule.

Database migration `0046_governed_automation_outbox` creates the rule, event,
and delivery ledgers. Migration `0047_automation_connector_config` adds the
connector config table and delivery retry columns.

## Connector configs and provider adapters (v12.4)

A connector config binds a corporate account to one channel (`email`,
`messaging`, `calendar`, or `crm`) and one provider implementation (`console`,
`smtp`, and reserved placeholders for future providers). Only one active
config is allowed per account/channel pair.

- `console` writes the delivery to stdout and returns a test message id.
- `smtp` sends real email via STARTTLS using `host`, `port`, `username`, and
  `password` from the stored credentials.

Credentials are currently persisted as JSON inside the connector config and
must be encrypted at rest or moved to a secret manager before production use.

## Retry, scheduling, and dispatch

When a delivery is created, it is linked to the active connector config for
its account and channel. If no connector config exists, dispatch attempts still
increment the attempt counter and record the error.

- Up to 3 attempts are allowed with exponential backoff: 60s, 300s, 900s.
- A successful dispatch moves the delivery to `dispatched` with a provider
  message id, timestamp, and actor.
- A failed attempt with remaining tries moves the delivery to `retry` and sets
  `next_attempt_at`.
- The third failure moves the delivery to `failed` and clears `next_attempt_at`.
- Every dispatch and retry is audited.

The Celery beat task `dispatch_automation_deliveries_task` runs every 60
seconds and dispatches due `ready` or `retry` deliveries in order of creation.
Operators can also trigger dispatch per delivery via
`POST /api/v1/automation/deliveries/{delivery_id}/dispatch`.

## Application-status bridge (v12.6.1)

The event model was extended to support `appointment.status_changed` and
`submission.status_changed`. These events are produced by the authority
appointment and agency submission services when a status change occurs and the
application's lead is linked to an active corporate mobility case. The corporate
account and case are derived automatically from the lead's case link, so
existing corporate automation rules can match these events and route them
through the same connector, review, retry, and audit boundaries as case,
compliance, and task events. If no active corporate case link exists, the status
change is still recorded but no automation event is created.
