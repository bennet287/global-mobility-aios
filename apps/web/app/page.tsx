"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import {
  ApplicationQueue,
  createLead,
  DashboardSummary,
  DocumentVerificationQueue,
  getAgentReviewDashboard,
  getApiBaseUrl,
  getApplicationQueue,
  getDashboardSummary,
  getDocumentVerificationQueue,
  getHealthStatus,
  getTruthResolutionQueue,
  HealthStatus,
  Lead,
  OptionalData,
  TruthClaim,
  TruthResolutionQueue,
  AgentReviewDashboard,
} from "../lib/api";

type LeadForm = {
  full_name: string;
  email: string;
  phone: string;
  source: string;
  intent: string;
  target_country: string;
  notes: string;
};

type LoadStatus = "idle" | "loading" | "ready" | "partial" | "offline";

const emptyLeadForm: LeadForm = {
  full_name: "",
  email: "",
  phone: "",
  source: "web_form",
  intent: "study_abroad",
  target_country: "",
  notes: "",
};

const emptySummary: DashboardSummary = {
  leads_total: 0,
  leads_new: 0,
  leads_human_review: 0,
  leads_converted: 0,
  truth_queue_pending: 0,
  truth_queue_resolved: 0,
  recent_leads: [],
  recent_truth_audits: [],
};

const safetyRules = [
  "Client messages remain drafts",
  "Applications are never submitted automatically",
  "Operator approval is required",
  "Visa and job claims use traceable sources",
];

function normalizeApiBase() {
  return getApiBaseUrl();
}

function compactNumber(value: number | undefined | null) {
  return new Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 1 }).format(value || 0);
}

function titleCase(value: string | undefined | null) {
  if (!value) return "—";
  return value.replaceAll("_", " ").replace(/\b\w/g, (match) => match.toUpperCase());
}

function statusTone(value: string | undefined | null) {
  const normalized = (value || "").toLowerCase();
  if (["verified", "approved", "converted", "completed", "ready", "ready_for_human_approval", "truth_clear", "ok", "good"].includes(normalized)) return "good";
  if (["pending", "needs_review", "human_review", "human_review_required", "documents_incomplete", "draft", "submitted", "decision_pending", "new", "warn", "partial"].includes(normalized)) return "warn";
  if (["rejected", "blocked_truth_rejected", "rejected_by_authority", "withdrawn", "failed", "closed", "bad", "offline"].includes(normalized)) return "bad";
  return "neutral";
}

function StatusBadge({ value }: { value: string | undefined | null }) {
  return <span className={`status-badge ${statusTone(value)}`}>{titleCase(value)}</span>;
}

function SectionTitle({ label, title, detail }: { label: string; title: string; detail?: string }) {
  return (
    <div className="section-title">
      <span>{label}</span>
      <h2>{title}</h2>
      {detail ? <p>{detail}</p> : null}
    </div>
  );
}

function MetricCard({ label, value, detail, tone = "neutral" }: { label: string; value: number; detail: string; tone?: "good" | "warn" | "bad" | "neutral" }) {
  return (
    <article className={`metric-card ${tone}`}>
      <div>
        <span>{label}</span>
        <strong>{compactNumber(value)}</strong>
      </div>
      <p>{detail}</p>
    </article>
  );
}

function EmptyState({ title, detail }: { title: string; detail: string }) {
  return (
    <div className="empty-state">
      <strong>{title}</strong>
      <p>{detail}</p>
    </div>
  );
}

function DataNotice({ label, data }: { label: string; data: OptionalData<unknown> }) {
  if (!data.error) return null;
  return (
    <div className="inline-notice">
      <strong>{label}</strong>
      <span>{data.error}</span>
    </div>
  );
}

function LeadIdentity({ lead }: { lead: Lead }) {
  return (
    <div className="lead-identity">
      <span>{lead.full_name?.slice(0, 1).toUpperCase() || "L"}</span>
      <div>
        <strong>{lead.full_name || "Unnamed lead"}</strong>
        <small>{lead.target_country || "No country"} · {titleCase(lead.intent)}</small>
      </div>
    </div>
  );
}

function QueueStages({ queue }: { queue: TruthResolutionQueue | ApplicationQueue | null }) {
  const stages = Object.entries(queue?.stage_counts || {});
  if (!stages.length) {
    return <EmptyState title="No stage data" detail="Start the backend and seed demo data to populate this area." />;
  }
  return (
    <div className="stage-list">
      {stages.slice(0, 7).map(([stage, count]) => (
        <div className="stage-row" key={stage}>
          <div>
            <strong>{titleCase(stage)}</strong>
            <span>{count} case{count === 1 ? "" : "s"}</span>
          </div>
          <StatusBadge value={stage} />
        </div>
      ))}
    </div>
  );
}

function TruthClaimCard({ claim }: { claim: TruthClaim }) {
  const confidence = Math.round((claim.confidence || 0) * 100);
  return (
    <article className="claim-card">
      <div className="claim-topline">
        <StatusBadge value={claim.verdict} />
        <span>{claim.country || "Global"} · {titleCase(claim.domain)}</span>
      </div>
      <strong>{claim.claim}</strong>
      <p>{claim.explanation || claim.recommended_next_step || "No explanation recorded."}</p>
      <div className="confidence-row">
        <span>Confidence</span>
        <div className="confidence-track"><i style={{ width: `${Math.min(100, Math.max(0, confidence))}%` }} /></div>
        <strong>{confidence}%</strong>
      </div>
    </article>
  );
}

export default function HomePage() {
  const apiBase = normalizeApiBase();
  const adminLinks = useMemo(
    () => [
      { label: "Admin", href: `${apiBase}/admin/v2`, meta: "Lead workflow" },
      { label: "Agent Console", href: `${apiBase}/admin/controlled-agents`, meta: "Controlled internal agents" },
      { label: "Review Queue", href: `${apiBase}/admin/agent-output-reviews`, meta: "Human approvals" },
      { label: "Drafts", href: `${apiBase}/admin/client-communications/drafts`, meta: "Client-ready messages" },
      { label: "Audit", href: `${apiBase}/admin/audit-logs`, meta: "Traceability" },
      { label: "API Docs", href: `${apiBase}/docs`, meta: "FastAPI reference" },
    ],
    [apiBase]
  );

  const [summary, setSummary] = useState<DashboardSummary>(emptySummary);
  const [summaryError, setSummaryError] = useState<string | null>(null);
  const [truthQueue, setTruthQueue] = useState<OptionalData<TruthResolutionQueue>>({ data: null, error: null });
  const [applicationQueue, setApplicationQueue] = useState<OptionalData<ApplicationQueue>>({ data: null, error: null });
  const [documentQueue, setDocumentQueue] = useState<OptionalData<DocumentVerificationQueue>>({ data: null, error: null });
  const [agentDashboard, setAgentDashboard] = useState<OptionalData<AgentReviewDashboard>>({ data: null, error: null });
  const [health, setHealth] = useState<OptionalData<HealthStatus>>({ data: null, error: null });
  const [loadStatus, setLoadStatus] = useState<LoadStatus>("idle");
  const [leadForm, setLeadForm] = useState<LeadForm>(emptyLeadForm);
  const [leadFormMessage, setLeadFormMessage] = useState<string | null>(null);
  const [leadFormError, setLeadFormError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoadStatus("loading");
    setSummaryError(null);

    const [summaryResult, truthData, applicationData, documentData, agentData, healthData] = await Promise.all([
      getDashboardSummary()
        .then((data) => ({ data, error: null }))
        .catch((err) => ({ data: emptySummary, error: err instanceof Error ? err.message : "Failed to load CRM summary" })),
      getTruthResolutionQueue(),
      getApplicationQueue(),
      getDocumentVerificationQueue(),
      getAgentReviewDashboard(),
      getHealthStatus(),
    ]);

    setSummary(summaryResult.data);
    setSummaryError(summaryResult.error);
    setTruthQueue(truthData);
    setApplicationQueue(applicationData);
    setDocumentQueue(documentData);
    setAgentDashboard(agentData);
    setHealth(healthData);

    const errors = [summaryResult.error, truthData.error, applicationData.error, documentData.error, agentData.error, healthData.error].filter(Boolean);
    if (healthData.data?.status === "ok" && errors.length === 0) setLoadStatus("ready");
    else if (healthData.data?.status === "ok") setLoadStatus("partial");
    else setLoadStatus("offline");
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const recentLeads = summary.recent_leads.slice(0, 6);
  const recentTruthClaims = summary.recent_truth_audits.slice(0, 3);
  const priorityTruthItems = (truthQueue.data?.items || []).filter((item) => item.stage !== "truth_clear").slice(0, 4);
  const documentCount = documentQueue.data?.count || 0;
  const agentCount = agentDashboard.data?.items?.length || 0;
  const backendOnline = health.data?.status === "ok";

  const metrics = [
    { label: "Leads", value: summary.leads_total, detail: "Total CRM opportunities", tone: "neutral" as const },
    { label: "New", value: summary.leads_new, detail: "Awaiting qualification", tone: "warn" as const },
    { label: "Review", value: summary.leads_human_review, detail: "Need operator attention", tone: summary.leads_human_review ? "warn" as const : "good" as const },
    { label: "Converted", value: summary.leads_converted, detail: "Commercial progress", tone: "good" as const },
    { label: "Truth", value: summary.truth_queue_pending, detail: "Claims pending", tone: summary.truth_queue_pending ? "bad" as const : "good" as const },
    { label: "Agents", value: agentCount, detail: "Outputs waiting", tone: agentCount ? "warn" as const : "neutral" as const },
  ];

  async function onCreateLead(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLeadFormMessage(null);
    setLeadFormError(null);

    try {
      await createLead({
        full_name: leadForm.full_name.trim(),
        email: leadForm.email.trim() || undefined,
        phone: leadForm.phone.trim() || undefined,
        source: leadForm.source.trim() || "web_form",
        intent: leadForm.intent,
        target_country: leadForm.target_country.trim() || undefined,
        notes: leadForm.notes.trim() || undefined,
      });
      setLeadForm(emptyLeadForm);
      setLeadFormMessage("Lead created. The workspace has been refreshed.");
      await load();
    } catch (err) {
      setLeadFormError(err instanceof Error ? err.message : "Unable to create lead. Confirm the FastAPI backend is running.");
    }
  }

  return (
    <main className="app-frame">
      <aside className="sidebar">
        <div className="brand-lockup">
          <span>GM</span>
          <div>
            <strong>Global Mobility AIOS</strong>
            <small>Agency operations workspace</small>
          </div>
        </div>

        <nav className="side-nav" aria-label="Workspace navigation">
          <a href="#overview">Overview</a>
          <a href="#pipeline">Pipeline</a>
          <a href="#truth">Truth Engine</a>
          <a href="#documents">Documents</a>
          <a href="#controls">Controls</a>
        </nav>

        <div className={`connection-card ${backendOnline ? "online" : "offline"}`}>
          <span />
          <div>
            <strong>{backendOnline ? "Backend connected" : "Backend not connected"}</strong>
            <small>{backendOnline ? health.data?.environment || "local" : apiBase}</small>
          </div>
        </div>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <span className="page-kicker">Local-first · Human-controlled · Audit-safe</span>
            <h1>Operations Workspace</h1>
          </div>
          <div className="topbar-actions">
            <a className="button secondary" href={`${apiBase}/admin/v2`} target="_blank" rel="noreferrer">Open admin</a>
            <button className="button primary" type="button" onClick={() => void load()} disabled={loadStatus === "loading"}>
              {loadStatus === "loading" ? "Refreshing" : "Refresh"}
            </button>
          </div>
        </header>

        <section className={`system-banner ${loadStatus}`} id="overview">
          <div>
            <span>System status</span>
            <strong>
              {loadStatus === "ready" ? "All services reachable" : loadStatus === "partial" ? "Backend online with partial queues" : loadStatus === "loading" ? "Loading workspace data" : "Frontend running in offline view"}
            </strong>
            <p>
              {backendOnline
                ? "Live data is being loaded from the FastAPI backend. Sensitive actions remain review-gated."
                : "Start the FastAPI backend to populate live CRM, truth, document, and agent queues. The interface remains usable for layout review."}
            </p>
          </div>
          <div className="status-stack">
            <StatusBadge value={backendOnline ? "online" : "offline"} />
            <code>{apiBase}</code>
          </div>
        </section>

        {summaryError ? (
          <div className="soft-warning">
            <strong>CRM summary unavailable.</strong>
            <span>{summaryError}</span>
          </div>
        ) : null}

        <section className="metric-grid" aria-label="Workspace metrics">
          {metrics.map((metric) => <MetricCard key={metric.label} {...metric} />)}
        </section>

        <section className="layout-grid main-grid" id="pipeline">
          <article className="panel panel-large">
            <SectionTitle label="CRM" title="Lead intake" detail="Capture opportunities without bypassing downstream verification or human review." />
            <form className="intake-form" onSubmit={onCreateLead}>
              <label>
                Full name
                <input value={leadForm.full_name} required placeholder="Client name" onChange={(event) => setLeadForm((prev) => ({ ...prev, full_name: event.target.value }))} />
              </label>
              <label>
                Email
                <input type="email" value={leadForm.email} placeholder="client@example.com" onChange={(event) => setLeadForm((prev) => ({ ...prev, email: event.target.value }))} />
              </label>
              <label>
                Intent
                <select value={leadForm.intent} onChange={(event) => setLeadForm((prev) => ({ ...prev, intent: event.target.value }))}>
                  <option value="study_abroad">Study abroad</option>
                  <option value="overseas_job">Overseas job</option>
                  <option value="visa">Visa guidance</option>
                  <option value="document">Document handling</option>
                  <option value="unknown">Unknown</option>
                </select>
              </label>
              <label>
                Target country
                <input value={leadForm.target_country} placeholder="Germany, Austria, Canada..." onChange={(event) => setLeadForm((prev) => ({ ...prev, target_country: event.target.value }))} />
              </label>
              <label>
                Phone
                <input value={leadForm.phone} placeholder="Optional" onChange={(event) => setLeadForm((prev) => ({ ...prev, phone: event.target.value }))} />
              </label>
              <label>
                Source
                <input value={leadForm.source} onChange={(event) => setLeadForm((prev) => ({ ...prev, source: event.target.value }))} />
              </label>
              <label className="full-field">
                Notes
                <textarea value={leadForm.notes} placeholder="Budget, intake, visa constraints, documents, language score..." onChange={(event) => setLeadForm((prev) => ({ ...prev, notes: event.target.value }))} />
              </label>
              <div className="form-actions full-field">
                <button className="button primary" type="submit">Create lead</button>
                <button className="button secondary" type="button" onClick={() => setLeadForm(emptyLeadForm)}>Clear</button>
              </div>
            </form>
            {leadFormMessage ? <div className="soft-success"><strong>Saved.</strong><span>{leadFormMessage}</span></div> : null}
            {leadFormError ? <div className="soft-warning"><strong>Lead was not created.</strong><span>{leadFormError}</span></div> : null}
          </article>

          <article className="panel">
            <SectionTitle label="Pipeline" title="Recent leads" detail={`${recentLeads.length} visible records`} />
            {recentLeads.length ? (
              <div className="lead-list">
                {recentLeads.map((lead) => (
                  <div className="lead-row" key={lead.id}>
                    <LeadIdentity lead={lead} />
                    <StatusBadge value={lead.status} />
                  </div>
                ))}
              </div>
            ) : <EmptyState title="No live leads" detail="Create a lead or run demo seed data after starting the backend." />}
          </article>
        </section>

        <section className="layout-grid queue-grid" id="truth">
          <article className="panel">
            <SectionTitle label="Truth Engine" title="Resolution stages" detail="Claim checks remain explicit, traceable, and reviewable." />
            <DataNotice label="Truth queue unavailable" data={truthQueue as OptionalData<unknown>} />
            <QueueStages queue={truthQueue.data} />
          </article>

          <article className="panel">
            <SectionTitle label="Applications" title="Readiness" detail="Application steps stay operator-controlled." />
            <DataNotice label="Application queue unavailable" data={applicationQueue as OptionalData<unknown>} />
            <QueueStages queue={applicationQueue.data} />
          </article>

          <article className="panel" id="documents">
            <SectionTitle label="Documents" title="Verification" detail={`${documentCount} documents pending`} />
            <DataNotice label="Document queue unavailable" data={documentQueue as OptionalData<unknown>} />
            {documentQueue.data?.documents?.length ? (
              <div className="compact-list">
                {documentQueue.data.documents.slice(0, 6).map((doc) => (
                  <div className="compact-row" key={doc.id}>
                    <div>
                      <strong>{titleCase(doc.document_type)}</strong>
                      <span>{doc.filename}</span>
                    </div>
                    <StatusBadge value={doc.status} />
                  </div>
                ))}
              </div>
            ) : <EmptyState title="No document queue" detail="Documents marked received or needs review will appear here." />}
          </article>
        </section>

        <section className="layout-grid insight-grid">
          <article className="panel panel-large">
            <SectionTitle label="Priority" title="Truth review focus" detail={`${priorityTruthItems.length} active blockers`} />
            {priorityTruthItems.length ? (
              <div className="resolution-list">
                {priorityTruthItems.map((item) => (
                  <div className="resolution-card" key={item.lead.id}>
                    <div className="resolution-header">
                      <LeadIdentity lead={item.lead} />
                      <StatusBadge value={item.stage} />
                    </div>
                    <p>{item.next_action}</p>
                    <div className="mini-metrics">
                      <span><strong>{item.counts.truth_claims}</strong> claims</span>
                      <span><strong>{item.counts.rejected_truth_claims}</strong> rejected</span>
                      <span><strong>{item.counts.pending_reviews}</strong> reviews</span>
                    </div>
                    <a className="text-link" href={`${apiBase}/api/v1/leads/${item.lead.id}/truth-resolution`} target="_blank" rel="noreferrer">Open evidence JSON</a>
                  </div>
                ))}
              </div>
            ) : <EmptyState title="No active truth blockers" detail="Blocked claims will surface here when present." />}
          </article>

          <article className="panel">
            <SectionTitle label="Claims" title="Recent verification signals" />
            {recentTruthClaims.length ? (
              <div className="claim-stack">
                {recentTruthClaims.map((claim) => <TruthClaimCard claim={claim} key={claim.id} />)}
              </div>
            ) : <EmptyState title="No claim history" detail="Truth Engine audits will appear here after workflows run." />}
          </article>
        </section>

        <section className="layout-grid controls-grid" id="controls">
          <article className="panel">
            <SectionTitle label="Governance" title="Safety controls" detail="The product is an operator system, not an autonomous submission engine." />
            <div className="safety-list">
              {safetyRules.map((rule) => <div key={rule}><span>✓</span><strong>{rule}</strong></div>)}
            </div>
          </article>

          <article className="panel">
            <SectionTitle label="Agents" title="Output review" detail={`${agentCount} reviewable outputs`} />
            <DataNotice label="Agent review unavailable" data={agentDashboard as OptionalData<unknown>} />
            {agentDashboard.data?.items?.length ? (
              <div className="compact-list">
                {agentDashboard.data.items.slice(0, 5).map((item) => (
                  <div className="compact-row" key={item.id}>
                    <div>
                      <strong>{titleCase(item.agent_name)}</strong>
                      <span>{item.summary}</span>
                    </div>
                    <StatusBadge value={item.status} />
                  </div>
                ))}
              </div>
            ) : <EmptyState title="No pending agent outputs" detail="Controlled agent recommendations remain reviewable before client use." />}
          </article>

          <article className="panel panel-wide">
            <SectionTitle label="Shortcuts" title="Backend operator pages" />
            <div className="shortcut-grid">
              {adminLinks.map((link) => (
                <a className="shortcut-card" href={link.href} key={link.href} target="_blank" rel="noreferrer">
                  <strong>{link.label}</strong>
                  <span>{link.meta}</span>
                </a>
              ))}
            </div>
          </article>
        </section>
      </section>
    </main>
  );
}
