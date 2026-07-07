"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import {
  createLead,
  DashboardSummary,
  getDashboardSummary,
  getTruthQueue,
  resolveAudit,
  TruthAudit,
} from "../lib/api";

const queueStatusOptions = ["pending", "approved", "rejected", "all"] as const;

type QueueStatus = (typeof queueStatusOptions)[number];

function StatusBadge({ value }: { value: string }) {
  const cls = value.toLowerCase();
  return <span className={`badge badge-${cls.replaceAll("_", "-")}`}>{value}</span>;
}

export default function HomePage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [queue, setQueue] = useState<TruthAudit[]>([]);
  const [queueStatus, setQueueStatus] = useState<QueueStatus>("pending");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [reviewer, setReviewer] = useState("Quality Lead");
  const [notesById, setNotesById] = useState<Record<string, string>>({});
  const [busyAuditId, setBusyAuditId] = useState<string | null>(null);

  const [leadForm, setLeadForm] = useState({
    full_name: "",
    email: "",
    phone: "",
    source: "web_form",
    intent: "study_abroad",
    target_country: "",
    notes: "",
  });
  const [leadFormMessage, setLeadFormMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [summaryData, queueData] = await Promise.all([
        getDashboardSummary(),
        getTruthQueue(queueStatus),
      ]);
      setSummary(summaryData);
      setQueue(queueData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load dashboard");
    } finally {
      setIsLoading(false);
    }
  }, [queueStatus]);

  useEffect(() => {
    void load();
  }, [load]);

  const kpis = useMemo(() => {
    if (!summary) {
      return [];
    }
    return [
      { label: "Total Leads", value: summary.leads_total },
      { label: "New Leads", value: summary.leads_new },
      { label: "Leads in Human Review", value: summary.leads_human_review },
      { label: "Converted", value: summary.leads_converted },
      { label: "Truth Queue Pending", value: summary.truth_queue_pending },
      { label: "Truth Queue Resolved", value: summary.truth_queue_resolved },
    ];
  }, [summary]);

  async function onCreateLead(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLeadFormMessage(null);
    setError(null);

    try {
      await createLead({
        full_name: leadForm.full_name,
        email: leadForm.email || undefined,
        phone: leadForm.phone || undefined,
        source: leadForm.source || "web_form",
        intent: leadForm.intent,
        target_country: leadForm.target_country || undefined,
        notes: leadForm.notes || undefined,
      });

      setLeadForm({
        full_name: "",
        email: "",
        phone: "",
        source: "web_form",
        intent: "study_abroad",
        target_country: "",
        notes: "",
      });
      setLeadFormMessage("Lead created and pipeline refreshed.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create lead");
    }
  }

  async function onResolve(auditId: string, decision: "APPROVED" | "REJECTED") {
    if (!reviewer.trim()) {
      setError("Reviewer name is required before resolving queue items.");
      return;
    }

    setBusyAuditId(auditId);
    setError(null);
    try {
      await resolveAudit(auditId, {
        decision,
        reviewer,
        notes: notesById[auditId] || undefined,
      });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to resolve queue item");
    } finally {
      setBusyAuditId(null);
    }
  }

  return (
    <main className="container">
      <section className="hero">
        <h1>Global Mobility AIOS Control Room</h1>
        <p>
          Unified CRM pulse plus Truth Review Queue for safe visa, study, and recruitment
          operations.
        </p>
      </section>

      {error ? <p className="error">{error}</p> : null}

      <section className="grid kpi-grid">
        {kpis.map((kpi) => (
          <article className="card" key={kpi.label}>
            <p className="label">{kpi.label}</p>
            <p className="kpi-value">{kpi.value}</p>
          </article>
        ))}
      </section>

      <section className="grid main-grid">
        <div className="stack">
          <article className="card">
            <h2>Lead Intake</h2>
            <p className="small">Capture new opportunities directly into CRM.</p>
            <form onSubmit={onCreateLead}>
              <div className="row">
                <label>
                  Full name
                  <input
                    value={leadForm.full_name}
                    required
                    onChange={(e) => setLeadForm((prev) => ({ ...prev, full_name: e.target.value }))}
                  />
                </label>
                <label>
                  Email
                  <input
                    type="email"
                    value={leadForm.email}
                    onChange={(e) => setLeadForm((prev) => ({ ...prev, email: e.target.value }))}
                  />
                </label>
              </div>
              <div className="row">
                <label>
                  Intent
                  <select
                    value={leadForm.intent}
                    onChange={(e) => setLeadForm((prev) => ({ ...prev, intent: e.target.value }))}
                  >
                    <option value="study_abroad">study_abroad</option>
                    <option value="overseas_job">overseas_job</option>
                    <option value="visa">visa</option>
                    <option value="document">document</option>
                    <option value="unknown">unknown</option>
                  </select>
                </label>
                <label>
                  Target country
                  <input
                    value={leadForm.target_country}
                    onChange={(e) =>
                      setLeadForm((prev) => ({ ...prev, target_country: e.target.value }))
                    }
                  />
                </label>
              </div>
              <div className="row">
                <label>
                  Phone
                  <input
                    value={leadForm.phone}
                    onChange={(e) => setLeadForm((prev) => ({ ...prev, phone: e.target.value }))}
                  />
                </label>
                <label>
                  Source
                  <input
                    value={leadForm.source}
                    onChange={(e) => setLeadForm((prev) => ({ ...prev, source: e.target.value }))}
                  />
                </label>
              </div>
              <label>
                Notes
                <textarea
                  value={leadForm.notes}
                  onChange={(e) => setLeadForm((prev) => ({ ...prev, notes: e.target.value }))}
                />
              </label>
              <div className="action-row" style={{ marginTop: "0.8rem" }}>
                <button type="submit">Create Lead</button>
                <button
                  className="secondary"
                  type="button"
                  onClick={() => void load()}
                  disabled={isLoading}
                >
                  Refresh
                </button>
              </div>
            </form>
            {leadFormMessage ? <p className="success">{leadFormMessage}</p> : null}
          </article>

          <article className="card">
            <h2>Recent Leads</h2>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Intent</th>
                    <th>Country</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {(summary?.recent_leads || []).map((lead) => (
                    <tr key={lead.id}>
                      <td>{lead.full_name}</td>
                      <td>{lead.intent}</td>
                      <td>{lead.target_country || "-"}</td>
                      <td>
                        <StatusBadge value={lead.status.toUpperCase()} />
                      </td>
                    </tr>
                  ))}
                  {summary?.recent_leads.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="small">
                        No leads yet.
                      </td>
                    </tr>
                  ) : null}
                </tbody>
              </table>
            </div>
          </article>
        </div>

        <article className="card">
          <h2>Truth Review Queue</h2>
          <p className="small">Review risky or ambiguous claims before frontline use.</p>

          <div className="row" style={{ marginTop: "0.3rem" }}>
            <label>
              Queue view
              <select
                value={queueStatus}
                onChange={(e) => setQueueStatus(e.target.value as QueueStatus)}
              >
                {queueStatusOptions.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Reviewer
              <input value={reviewer} onChange={(e) => setReviewer(e.target.value)} />
            </label>
          </div>

          <div className="table-wrap" style={{ marginTop: "0.6rem" }}>
            <table>
              <thead>
                <tr>
                  <th>Claim</th>
                  <th>Verdict</th>
                  <th>Review</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {queue.map((audit) => (
                  <tr key={audit.id}>
                    <td>
                      <div>{audit.claim}</div>
                      <div className="small">
                        {audit.domain} • confidence {(audit.confidence * 100).toFixed(0)}%
                      </div>
                      <div style={{ marginTop: "0.2rem" }}>
                        {audit.official_sources_found === 0 ? (
                          <span className="badge badge-red-flag">No official source</span>
                        ) : (
                          <span className="badge badge-verified">
                            {audit.official_sources_found} official source(s)
                          </span>
                        )}
                      </div>
                    </td>
                    <td>
                      <StatusBadge value={audit.verdict} />
                    </td>
                    <td>
                      <StatusBadge value={audit.review_status} />
                      <textarea
                        placeholder="Resolution notes"
                        value={notesById[audit.id] || ""}
                        onChange={(e) =>
                          setNotesById((prev) => ({ ...prev, [audit.id]: e.target.value }))
                        }
                        style={{ marginTop: "0.4rem" }}
                      />
                    </td>
                    <td>
                      <div className="action-row">
                        <button
                          disabled={busyAuditId === audit.id || audit.review_status !== "PENDING"}
                          onClick={() => void onResolve(audit.id, "APPROVED")}
                        >
                          Approve
                        </button>
                        <button
                          className="secondary"
                          disabled={busyAuditId === audit.id || audit.review_status !== "PENDING"}
                          onClick={() => void onResolve(audit.id, "REJECTED")}
                        >
                          Reject
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
                {!queue.length && !isLoading ? (
                  <tr>
                    <td colSpan={4} className="small">
                      Queue is empty for this filter.
                    </td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </article>
      </section>
    </main>
  );
}
