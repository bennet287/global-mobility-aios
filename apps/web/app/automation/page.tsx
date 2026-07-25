"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  AutomationChannel,
  AutomationDelivery,
  AutomationEvent,
  AutomationRule,
  CorporateAccount,
  createAutomationRule,
  decideAutomationDelivery,
  listAutomationDeliveries,
  listAutomationEvents,
  listAutomationRules,
  listCorporateAccounts,
  updateAutomationRuleStatus,
} from "../../lib/api";
import { WorkspaceShell } from "../../components/WorkspaceShell";
import { Topbar } from "../../components/Topbar";
import { SectionTitle } from "../../components/SectionTitle";
import { StatusBadge } from "../../components/StatusBadge";
import { EmptyState } from "../../components/EmptyState";
import { InlineNotice } from "../../components/InlineNotice";
import { useBackendStatus } from "../../hooks/useBackendStatus";
import { titleCase } from "../../lib/utils";

const channels: AutomationChannel[] = ["email", "messaging", "calendar", "crm"];
const eventTypes = [
  "case.created",
  "case.status_changed",
  "compliance.created",
  "compliance.status_changed",
  "task.status_changed",
];

export default function AutomationPage() {
  const { health } = useBackendStatus();
  const [accounts, setAccounts] = useState<CorporateAccount[]>([]);
  const [accountId, setAccountId] = useState("");
  const [rules, setRules] = useState<AutomationRule[]>([]);
  const [events, setEvents] = useState<AutomationEvent[]>([]);
  const [deliveries, setDeliveries] = useState<AutomationDelivery[]>([]);
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [reviewNote, setReviewNote] = useState("");
  const [form, setForm] = useState({
    name: "Case status coordination",
    event_type: "case.status_changed",
    channels: ["crm"] as AutomationChannel[],
    destinations: {
      email: "",
      messaging: "",
      calendar: "",
      crm: "corporate-case-sync",
    } as Record<AutomationChannel, string>,
    subject_template: "{case_reference}: {event_type}",
    body_template: "{case_reference} changed from {previous_status} to {status}.",
  });

  async function load(selected = accountId) {
    setLoading(true);
    setError(null);
    try {
      const accountRows = await listCorporateAccounts();
      const resolved = selected || accountRows[0]?.id || "";
      setAccounts(accountRows);
      setAccountId(resolved);
      const [ruleRows, eventRows, deliveryRows] = await Promise.all([
        listAutomationRules(resolved || undefined),
        listAutomationEvents(resolved || undefined),
        listAutomationDeliveries(resolved || undefined),
      ]);
      setRules(ruleRows);
      setEvents(eventRows);
      setDeliveries(deliveryRows);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Automation workspace could not be loaded.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load("");
  }, []);

  useEffect(() => {
    if (accountId) void load(accountId);
  }, [accountId]);

  const metrics = useMemo(
    () => ({
      activeRules: rules.filter((rule) => rule.status === "active").length,
      pending: deliveries.filter((delivery) => delivery.status === "pending_review").length,
      ready: deliveries.filter((delivery) => delivery.status === "ready").length,
      dispatched: deliveries.filter((delivery) => delivery.status === "dispatched").length,
    }),
    [rules, deliveries]
  );

  async function submitRule(event: FormEvent) {
    event.preventDefault();
    if (!accountId) return;
    setWorking("rule");
    setError(null);
    setMessage(null);
    try {
      await createAutomationRule({
        corporate_account_id: accountId,
        name: form.name,
        event_type: form.event_type,
        channels: form.channels,
        destinations: Object.fromEntries(
          form.channels.map((channel) => [channel, form.destinations[channel]])
        ),
        subject_template: form.subject_template,
        body_template: form.body_template,
        requires_human_approval: form.channels.some((channel) => channel !== "crm"),
      });
      setMessage("Account-scoped automation rule created.");
      await load(accountId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Automation rule could not be created.");
    } finally {
      setWorking(null);
    }
  }

  async function toggleRule(rule: AutomationRule) {
    setWorking(rule.id);
    setError(null);
    try {
      await updateAutomationRuleStatus(
        rule.id,
        rule.status === "active" ? "paused" : "active",
        rule.status === "active"
          ? "Paused from the governed automation workspace."
          : "Reactivated from the governed automation workspace."
      );
      await load(accountId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Rule status could not be changed.");
    } finally {
      setWorking(null);
    }
  }

  async function decide(delivery: AutomationDelivery, decision: "approved" | "rejected") {
    if (reviewNote.trim().length < 3) {
      setError("Enter a review note before making a delivery decision.");
      return;
    }
    setWorking(delivery.id);
    setError(null);
    try {
      await decideAutomationDelivery(delivery.id, decision, reviewNote.trim());
      setReviewNote("");
      setMessage(
        decision === "approved"
          ? "Delivery approved for its configured connector."
          : "Delivery rejected and removed from dispatch readiness."
      );
      await load(accountId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delivery decision could not be recorded.");
    } finally {
      setWorking(null);
    }
  }

  function toggleChannel(channel: AutomationChannel) {
    setForm((current) => ({
      ...current,
      channels: current.channels.includes(channel)
        ? current.channels.filter((item) => item !== channel)
        : [...current.channels, channel],
    }));
  }

  return (
    <WorkspaceShell health={health}>
      <Topbar
        title="Automation Hub"
        kicker="Phase 12 · Governed case-event orchestration"
        loadStatus={loading ? "loading" : error ? "partial" : "ready"}
        onRefresh={() => load(accountId)}
      />

      <section className="automation-hero">
        <div>
          <span>Controlled orchestration</span>
          <h2>Events become accountable actions.</h2>
          <p>
            Coordinate email, messaging, calendar, and CRM work from immutable
            corporate case events without silently sending external actions.
          </p>
        </div>
        <div className="automation-metrics">
          <article><strong>{metrics.activeRules}</strong><span>Active rules</span></article>
          <article><strong>{metrics.pending}</strong><span>Awaiting review</span></article>
          <article><strong>{metrics.ready}</strong><span>Ready for connector</span></article>
          <article><strong>{metrics.dispatched}</strong><span>Dispatch receipts</span></article>
        </div>
      </section>

      {error ? <InlineNotice label="Automation attention required" detail={error} tone="bad" /> : null}
      {message ? <InlineNotice label="Automation updated" detail={message} tone="good" /> : null}

      <section className="automation-layout">
        <aside className="panel automation-rule-builder">
          <SectionTitle
            label="Account boundary"
            title="Create an event rule"
            detail="Every rule belongs to one corporate account. External channels always require review."
          />
          <form className="corporate-form" onSubmit={submitRule}>
            <label>
              Corporate account
              <select value={accountId} onChange={(event) => setAccountId(event.target.value)} required>
                <option value="">Select an account</option>
                {accounts.map((account) => (
                  <option value={account.id} key={account.id}>
                    {account.display_name || account.legal_name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Rule name
              <input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} required />
            </label>
            <label>
              Event
              <select value={form.event_type} onChange={(event) => setForm({ ...form, event_type: event.target.value })}>
                {eventTypes.map((item) => <option value={item} key={item}>{titleCase(item.replace(".", " "))}</option>)}
              </select>
            </label>
            <fieldset className="automation-channel-picker">
              <legend>Channels</legend>
              {channels.map((channel) => (
                <label key={channel}>
                  <input
                    type="checkbox"
                    checked={form.channels.includes(channel)}
                    onChange={() => toggleChannel(channel)}
                  />
                  <span>{titleCase(channel)}</span>
                </label>
              ))}
            </fieldset>
            {form.channels.map((channel) => (
              <label key={channel}>
                {titleCase(channel)} destination
                <input
                  value={form.destinations[channel]}
                  placeholder={`Named ${channel} connector or queue`}
                  onChange={(event) =>
                    setForm({
                      ...form,
                      destinations: { ...form.destinations, [channel]: event.target.value },
                    })
                  }
                  required
                />
              </label>
            ))}
            <label>
              Subject template
              <input value={form.subject_template} onChange={(event) => setForm({ ...form, subject_template: event.target.value })} />
            </label>
            <label>
              Body template
              <textarea value={form.body_template} onChange={(event) => setForm({ ...form, body_template: event.target.value })} />
            </label>
            <button className="button primary" disabled={working === "rule" || !accountId || !form.channels.length}>
              {working === "rule" ? "Creating…" : "Create governed rule"}
            </button>
          </form>
        </aside>

        <main className="automation-stream">
          <section className="panel">
            <SectionTitle
              label="Delivery review"
              title="External action outbox"
              detail="Approval makes an item connector-ready; it does not fabricate a provider receipt."
            />
            <label className="automation-review-note">
              Review note
              <input
                value={reviewNote}
                onChange={(event) => setReviewNote(event.target.value)}
                placeholder="Record the content, destination, and timing check"
              />
            </label>
            <div className="compact-list">
              {deliveries.map((delivery) => (
                <article className="compact-row automation-delivery-row" key={delivery.id}>
                  <div>
                    <span>{titleCase(delivery.channel)} · {delivery.destination || "No destination"}</span>
                    <strong>{delivery.subject || "Untitled automation action"}</strong>
                    <small>{new Date(delivery.created_at).toLocaleString()} · {delivery.attempt_count} dispatch attempts</small>
                  </div>
                  <div className="draft-row-actions">
                    <StatusBadge value={delivery.status} />
                    {delivery.status === "pending_review" ? (
                      <>
                        <button className="button secondary" disabled={working === delivery.id} onClick={() => decide(delivery, "rejected")}>Reject</button>
                        <button className="button primary" disabled={working === delivery.id} onClick={() => decide(delivery, "approved")}>Approve</button>
                      </>
                    ) : null}
                  </div>
                </article>
              ))}
              {!loading && !deliveries.length ? <EmptyState title="No delivery actions" detail="Matching case events will appear here after a rule is active." /> : null}
            </div>
          </section>

          <section className="automation-ledgers">
            <div className="panel">
              <SectionTitle label="Rules" title="Account automations" detail={`${rules.length} configured`} />
              <div className="compact-list">
                {rules.map((rule) => (
                  <article className="compact-row" key={rule.id}>
                    <div><strong>{rule.name}</strong><span>{rule.event_type} · {rule.channels.join(", ")}</span></div>
                    <div className="draft-row-actions">
                      <StatusBadge value={rule.status} />
                      <button className="button secondary" disabled={working === rule.id} onClick={() => toggleRule(rule)}>
                        {rule.status === "active" ? "Pause" : "Activate"}
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            </div>
            <div className="panel">
              <SectionTitle label="Event ledger" title="Recent case events" detail={`${events.length} immutable records`} />
              <div className="compact-list">
                {events.slice(0, 12).map((event) => (
                  <article className="compact-row" key={event.id}>
                    <div><strong>{event.event_type}</strong><span>{String(event.payload.case_reference || event.entity_id)}</span></div>
                    <div><StatusBadge value={event.status} /><small>{event.delivery_count} actions</small></div>
                  </article>
                ))}
              </div>
            </div>
          </section>
        </main>
      </section>
    </WorkspaceShell>
  );
}
