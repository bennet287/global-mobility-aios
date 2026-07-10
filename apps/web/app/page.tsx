"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import {
  ApplicationQueue,
  createLead,
  DashboardSummary,
  DocumentVerificationQueue,
  getAgentReviewDashboard,
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

const emptyLeadForm: LeadForm = {
  full_name: "",
  email: "",
  phone: "",
  source: "web_form",
  intent: "study_abroad",
  target_country: "",
  notes: "",
};

const adminLinks = [
  { label: "Admin v2", href: "http://localhost:8000/admin/v2", meta: "Lead workflow" },
  { label: "Agent Console", href: "http://localhost:8000/admin/controlled-agents", meta: "Run internal agents" },
  { label: "Review Queue", href: "http://localhost:8000/admin/agent-output-reviews", meta: "Approve / reject" },
  { label: "Drafts", href: "http://localhost:8000/admin/client-communications/drafts", meta: "Human-reviewed messages" },
  { label: "Audit Logs", href: "http://localhost:8000/admin/audit-logs", meta: "Traceability" },
  { label: "API Docs", href: "http://localhost:8000/docs", meta: "FastAPI" },
];

const safetyRules = [
  "No automatic client sending",
  "No automatic application submission",
  "Human review required",
  "Official-source truth checks",
];

function compactNumber(value: number | undefined | null) {
  return new Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 1 }).format(value || 0);
}

function titleCase(value: string | undefined | null) {
  if (!value) {
    return "-";
  }
  return value.replaceAll("_", " ").replace(/\b\w/g, (match) => match.toUpperCase());
}

function statusTone(value: string | undefined | null) {
  const normalized = (value || "").toLowerCase();
  if (["verified", "approved", "converted", "completed", "ready_for_human_approval", "truth_clear", "ok"].includes(normalized)) {
    return "good";
  }
  if (["pending", "needs_review", "human_review", "human_review_required", "documents_incomplete", "draft", "submitted", "decision_pending", "new"].includes(normalized)) {
    return "warn";
  }
  if (["rejected", "blocked_truth_rejected", "rejected_by_authority", "withdrawn", "failed", "closed"].includes(normalized)) {
    return "bad";
  }
  return "neutral";
}

function StatusBadge({ value, subtle = false }: { value: string | undefined | null; subtle?: boolean }) {
  const tone = statusTone(value);
  return <span className={`status-badge ${tone} ${subtle ? "subtle" : ""}`}>{titleCase(value)}</span>;
}

function ProgressBar({ value, tone = "good" }: { value: number; tone?: "good" | "warn" | "bad" | "neutral" }) {
  const safeValue = Math.min(100, Math.max(0, Math.round(value)));
  return (
    <div className="progress-track" aria-label={`${safeValue}%`}>
      <div className={`progress-fill ${tone}`} style={{ width: `${safeValue}%` }} />
    </div>
  );
}

function SectionHeader({ eyebrow, title, action }: { eyebrow: string; title: string; action?: React.ReactNode }) {
  return (
    <div className="section-header">
      <div>
        <span className="eyebrow">{eyebrow}</span>
        <h2>{title}</h2>
      </div>
      {action ? <div className="section-action">{action}</div> : null}
    </div>
  );
}

function KpiCard({ label, value, icon, meta, tone = "neutral" }: { label: string; value: number; icon: string; meta: string; tone?: "good" | "warn" | "bad" | "neutral" }) {
  return (
    <article className={`kpi-card ${tone}`}>
      <div className="kpi-topline">
        <span className="kpi-icon">{icon}</span>
        <StatusBadge value={tone === "neutral" ? "tracked" : tone} subtle />
      </div>
      <strong>{compactNumber(value)}</strong>
      <span>{label}</span>
      <p>{meta}</p>
    </article>
  );
}

function MetricPill({ label, value }: { label: string; value: number | string }) {
  return (
    <span className="metric-pill">
      <strong>{value}</strong>
      {label}
    </span>
  );
}

function EmptyState({ title, detail }: { title: string; detail: string }) {
  return (
    <div className="empty-state">
      <span>◇</span>
      <strong>{title}</strong>
      <p>{detail}</p>
    </div>
  );
}

function DataNotice({ label, data }: { label: string; data: OptionalData<unknown> }) {
  if (!data.error) {
    return null;
  }
  return (
    <div className="notice warn">
      <strong>{label} unavailable.</strong>
      <span>{data.error}</span>
    </div>
  );
}

function LeadIdentity({ lead }: { lead: Lead }) {
  return (
    <div className="lead-identity">
      <span>{lead.full_name?.slice(0, 1).toUpperCase() || "L"}</span>
      <div>
        <strong>{lead.full_name}</strong>
        <small>{lead.target_country || "No target country"} • {titleCase(lead.intent)}</small>
      </div>
    </div>
  );
}

function TruthClaimCard({ claim }: { claim: TruthClaim }) {
  const confidence = Math.round((claim.confidence || 0) * 100);
  return (
    <div className="truth-card">
      <div className="truth-card-top">
        <StatusBadge value={claim.verdict} />
        <span>{claim.country || "Global"} • {titleCase(claim.domain)}</span>
      </div>
      <strong>{claim.claim}</strong>
      <p>{claim.explanation || claim.recommended_next_step || "No explanation recorded."}</p>
      <div className="confidence-line">
        <span>Confidence {confidence}%</span>
        <ProgressBar value={confidence} tone={confidence >= 80 ? "good" : confidence >= 50 ? "warn" : "bad"} />
      </div>
    </div>
  );
}

function QueueStageCards({ queue }: { queue: TruthResolutionQueue | ApplicationQueue | null }) {
  const stages = Object.entries(queue?.stage_counts || {});
  if (!stages.length) {
    return <EmptyState title="No stage data" detail="Run demo seed data or process leads to populate queue stage counts." />;
  }
  return (
    <div className="stage-grid">
      {stages.map(([stage, count]) => (
        <div className="stage-card" key={stage}>
          <StatusBadge value={stage} />
          <strong>{count}</strong>
          <span>{titleCase(stage)}</span>
        </div>
      ))}
    </div>
  );
}

export default function HomePage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [truthQueue, setTruthQueue] = useState<OptionalData<TruthResolutionQueue>>({ data: null, error: null });
  const [applicationQueue, setApplicationQueue] = useState<OptionalData<ApplicationQueue>>({ data: null, error: null });
  const [documentQueue, setDocumentQueue] = useState<OptionalData<DocumentVerificationQueue>>({ data: null, error: null });
  const [agentDashboard, setAgentDashboard] = useState<OptionalData<AgentReviewDashboard>>({ data: null, error: null });
  const [health, setHealth] = useState<OptionalData<HealthStatus>>({ data: null, error: null });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [leadForm, setLeadForm] = useState<LeadForm>(emptyLeadForm);
  const [leadFormMessage, setLeadFormMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [summaryData, truthData, applicationData, documentData, agentData, healthData] = await Promise.all([
        getDashboardSummary(),
        getTruthResolutionQueue(),
        getApplicationQueue(),
        getDocumentVerificationQueue(),
        getAgentReviewDashboard(),
        getHealthStatus(),
      ]);
      setSummary(summaryData);
      setTruthQueue(truthData);
      setApplicationQueue(applicationData);
      setDocumentQueue(documentData);
      setAgentDashboard(agentData);
      setHealth(healthData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load the command center.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const kpis = useMemo(
    () => [
      {
        label: "Total Leads",
        value: summary?.leads_total || 0,
        icon: "◎",
        meta: "All CRM opportunities",
        tone: "neutral" as const,
      },
      {
        label: "New Leads",
        value: summary?.leads_new || 0,
        icon: "+",
        meta: "Ready for qualification",
        tone: "warn" as const,
      },
      {
        label: "Human Review",
        value: summary?.leads_human_review || 0,
        icon: "◐",
        meta: "Operator attention",
        tone: "warn" as const,
      },
      {
        label: "Converted",
        value: summary?.leads_converted || 0,
        icon: "✓",
        meta: "Commercial progress",
        tone: "good" as const,
      },
      {
        label: "Truth Pending",
        value: summary?.truth_queue_pending || 0,
        icon: "!",
        meta: "Claim review queue",
        tone: summary?.truth_queue_pending ? "bad" as const : "good" as const,
      },
      {
        label: "Agent Outputs",
        value: agentDashboard.data?.items?.length || 0,
        icon: "AI",
        meta: "Reviewable internal work",
        tone: agentDashboard.data?.items?.length ? "warn" as const : "neutral" as const,
      },
    ],
    [summary, agentDashboard.data]
  );

  const priorityTruthItems = useMemo(() => {
    const items = truthQueue.data?.items || [];
    return items
      .filter((item) => item.stage !== "truth_clear")
      .slice(0, 5);
  }, [truthQueue.data]);

  const recentTruthClaims = useMemo(() => summary?.recent_truth_audits?.slice(0, 4) || [], [summary]);
  const recentLeads = useMemo(() => summary?.recent_leads?.slice(0, 8) || [], [summary]);
  const documentCount = documentQueue.data?.count || 0;
  const apiOnline = health.data?.status === "ok";

  async function onCreateLead(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLeadFormMessage(null);
    setError(null);

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
      setLeadFormMessage("Lead created. The operator pipeline has been refreshed.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create lead.");
    }
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand-lockup">
          <span className="brand-mark">GM</span>
          <div>
            <strong>Global Mobility AIOS</strong>
            <small>Operator OS</small>
          </div>
        </div>

        <nav className="nav-stack" aria-label="Primary navigation">
          <a className="active" href="#overview">Overview</a>
          <a href="#intake">Lead Intake</a>
          <a href="#truth">Truth Engine</a>
          <a href="#operations">Operations</a>
          <a href="#safety">Safety</a>
        </nav>

        <div className="side-card">
          <span className={`live-dot ${apiOnline ? "online" : "offline"}`} />
          <div>
            <strong>{apiOnline ? "API online" : "API offline"}</strong>
            <small>{health.data?.environment || "Check FastAPI server"}</small>
          </div>
        </div>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <span className="eyebrow">Local-first AI agency backend</span>
            <h1>Operator Command Center</h1>
          </div>
          <div className="topbar-actions">
            <a className="ghost-button" href="http://localhost:8000/admin/v2" target="_blank" rel="noreferrer">
              Open Admin
            </a>
            <button className="primary-button" type="button" onClick={() => void load()} disabled={isLoading}>
              {isLoading ? "Refreshing…" : "Refresh"}
            </button>
          </div>
        </header>

        {error ? (
          <div className="notice bad">
            <strong>Command center could not load.</strong>
            <span>{error}</span>
          </div>
        ) : null}

        <section className="hero-panel" id="overview">
          <div className="hero-copy">
            <span className="release-pill">MVP sealed • UI v7.0 direction</span>
            <h2>Modern control room for verified global mobility operations.</h2>
            <p>
              Manage leads, truth checks, document review, agent outputs, and audit-safe workflows in one polished operator interface.
            </p>
            <div className="hero-actions">
              <a className="primary-link" href="#intake">Create a lead</a>
              <a className="secondary-link" href="http://localhost:8000/admin/agent-output-reviews" target="_blank" rel="noreferrer">
                Review agent outputs
              </a>
            </div>
          </div>
          <div className="hero-scorecard">
            <span>Governance posture</span>
            <strong>Human-controlled</strong>
            <div className="score-list">
              {safetyRules.map((rule) => (
                <span key={rule}>✓ {rule}</span>
              ))}
            </div>
          </div>
        </section>

        <section className="kpi-grid" aria-label="Key metrics">
          {kpis.map((kpi) => (
            <KpiCard key={kpi.label} {...kpi} />
          ))}
        </section>

        <section className="two-column-grid" id="intake">
          <article className="panel lead-panel">
            <SectionHeader eyebrow="CRM" title="Lead Intake" />
            <p className="panel-intro">Capture a new study, job, visa, or document case without bypassing downstream review controls.</p>
            <form className="intake-form" onSubmit={onCreateLead}>
              <label>
                Full name
                <input
                  value={leadForm.full_name}
                  required
                  placeholder="e.g., Arjun Kumar"
                  onChange={(event) => setLeadForm((prev) => ({ ...prev, full_name: event.target.value }))}
                />
              </label>
              <label>
                Email
                <input
                  type="email"
                  value={leadForm.email}
                  placeholder="client@example.com"
                  onChange={(event) => setLeadForm((prev) => ({ ...prev, email: event.target.value }))}
                />
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
                <input
                  value={leadForm.target_country}
                  placeholder="Germany, Austria, Canada..."
                  onChange={(event) => setLeadForm((prev) => ({ ...prev, target_country: event.target.value }))}
                />
              </label>
              <label>
                Phone
                <input
                  value={leadForm.phone}
                  placeholder="Optional"
                  onChange={(event) => setLeadForm((prev) => ({ ...prev, phone: event.target.value }))}
                />
              </label>
              <label>
                Source
                <input
                  value={leadForm.source}
                  onChange={(event) => setLeadForm((prev) => ({ ...prev, source: event.target.value }))}
                />
              </label>
              <label className="full-field">
                Notes
                <textarea
                  value={leadForm.notes}
                  placeholder="Budget, intake, visa constraints, language score, documents..."
                  onChange={(event) => setLeadForm((prev) => ({ ...prev, notes: event.target.value }))}
                />
              </label>
              <div className="form-actions full-field">
                <button className="primary-button" type="submit">Create lead</button>
                <button className="ghost-button" type="button" onClick={() => setLeadForm(emptyLeadForm)}>Clear</button>
              </div>
            </form>
            {leadFormMessage ? <div className="notice good"><strong>Success.</strong><span>{leadFormMessage}</span></div> : null}
          </article>

          <article className="panel">
            <SectionHeader eyebrow="Pipeline" title="Recent Leads" action={<MetricPill label="records" value={recentLeads.length} />} />
            {recentLeads.length ? (
              <div className="lead-list">
                {recentLeads.map((lead) => (
                  <div className="lead-row" key={lead.id}>
                    <LeadIdentity lead={lead} />
                    <StatusBadge value={lead.status} />
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState title="No leads yet" detail="Create a lead or seed demo data to populate the CRM pipeline." />
            )}
          </article>
        </section>

        <section className="three-column-grid" id="operations">
          <article className="panel">
            <SectionHeader eyebrow="Applications" title="Readiness Stages" />
            <DataNotice label="Application queue" data={applicationQueue as OptionalData<unknown>} />
            <QueueStageCards queue={applicationQueue.data} />
          </article>

          <article className="panel">
            <SectionHeader eyebrow="Documents" title="Verification Queue" action={<MetricPill label="docs" value={documentCount} />} />
            <DataNotice label="Document queue" data={documentQueue as OptionalData<unknown>} />
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
            ) : (
              <EmptyState title="No pending documents" detail="Received and needs-review documents will appear here." />
            )}
          </article>

          <article className="panel">
            <SectionHeader eyebrow="Agents" title="Output Review" action={<MetricPill label="items" value={agentDashboard.data?.items?.length || 0} />} />
            <DataNotice label="Agent dashboard" data={agentDashboard as OptionalData<unknown>} />
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
            ) : (
              <EmptyState title="No reviewable outputs" detail="Controlled agent work appears here before operator approval." />
            )}
          </article>
        </section>

        <section className="two-column-grid" id="truth">
          <article className="panel large-panel">
            <SectionHeader eyebrow="Truth Engine" title="Priority Resolution Queue" action={<MetricPill label="blocked" value={priorityTruthItems.length} />} />
            <DataNotice label="Truth resolution queue" data={truthQueue as OptionalData<unknown>} />
            {priorityTruthItems.length ? (
              <div className="resolution-list">
                {priorityTruthItems.map((item) => (
                  <div className="resolution-card" key={item.lead.id}>
                    <div className="resolution-top">
                      <LeadIdentity lead={item.lead} />
                      <StatusBadge value={item.stage} />
                    </div>
                    <p>{item.next_action}</p>
                    <div className="metric-strip">
                      <MetricPill label="claims" value={item.counts.truth_claims} />
                      <MetricPill label="rejected" value={item.counts.rejected_truth_claims} />
                      <MetricPill label="pending reviews" value={item.counts.pending_reviews} />
                    </div>
                    <a className="inline-link" href={`http://localhost:8000/api/v1/leads/${item.lead.id}/truth-resolution`} target="_blank" rel="noreferrer">
                      Open evidence JSON →
                    </a>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState title="Truth queue clear" detail="No blocked lead is currently waiting for truth resolution." />
            )}
          </article>

          <article className="panel large-panel">
            <SectionHeader eyebrow="Recent Claims" title="Verification Signals" />
            {recentTruthClaims.length ? (
              <div className="truth-stack">
                {recentTruthClaims.map((claim) => <TruthClaimCard claim={claim} key={claim.id} />)}
              </div>
            ) : (
              <EmptyState title="No claims yet" detail="Truth checks will appear here after claim verification workflows run." />
            )}
          </article>
        </section>

        <section className="bottom-grid" id="safety">
          <article className="panel safety-panel">
            <SectionHeader eyebrow="Controls" title="Safety Invariants" />
            <div className="safety-grid">
              {safetyRules.map((rule) => (
                <div className="safety-item" key={rule}>
                  <span>✓</span>
                  <strong>{rule}</strong>
                </div>
              ))}
            </div>
          </article>

          <article className="panel shortcuts-panel">
            <SectionHeader eyebrow="Deep Links" title="Backend Operator Pages" />
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
