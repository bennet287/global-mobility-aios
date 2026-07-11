"use client";

import { useMemo } from "react";
import Link from "next/link";
import {
  AgentReviewDashboard,
  ApplicationQueue,
  DashboardSummary,
  DocumentVerificationQueue,
  getApiBaseUrl,
  OptionalData,
  TruthResolutionQueue,
} from "../lib/api";
import { ActionCard, ActionItem } from "../components/ActionCard";
import { CaseTable } from "../components/CaseTable";
import { DataNotice } from "../components/DataNotice";
import { EmptyState } from "../components/EmptyState";
import { InlineNotice } from "../components/InlineNotice";
import { MetricPill } from "../components/MetricPill";
import { MetricSkeleton, ActionCardSkeleton } from "../components/Skeleton";
import { SectionTitle } from "../components/SectionTitle";
import { StatusBadge } from "../components/StatusBadge";
import { Topbar } from "../components/Topbar";
import { TruthClaimCard } from "../components/TruthClaimCard";
import { QueueStages } from "../components/QueueStages";
import { WorkspaceShell } from "../components/WorkspaceShell";
import { useBackendStatus } from "../hooks/useBackendStatus";
import { useLeadForm } from "../hooks/useLeadForm";
import { useWorkspaceData } from "../hooks/useWorkspaceData";
import { statusTone, titleCase, Tone } from "../lib/utils";

const safetyRules = [
  "Client messages remain drafts",
  "Applications stay operator controlled",
  "Human approval gates sensitive actions",
  "Visa and job claims keep source traceability",
];

function buildActionQueue({
  summary,
  truthQueue,
  documentQueue,
  agentDashboard,
  applicationQueue,
  apiBase,
}: {
  summary: DashboardSummary;
  truthQueue: OptionalData<TruthResolutionQueue>;
  documentQueue: OptionalData<DocumentVerificationQueue>;
  agentDashboard: OptionalData<AgentReviewDashboard>;
  applicationQueue: OptionalData<ApplicationQueue>;
  apiBase: string;
}): ActionItem[] {
  const actions: ActionItem[] = [];

  for (const lead of summary.recent_leads.filter((lead) => String(lead.status).toLowerCase() === "human_review").slice(0, 2)) {
    actions.push({
      label: "Human review",
      title: lead.full_name,
      detail: `${lead.target_country || "No country"} · ${titleCase(lead.intent)}`,
      tone: "warn",
      href: `${apiBase}/admin/v2`,
    });
  }

  for (const item of (truthQueue.data?.items || []).filter((item) => item.stage !== "truth_clear").slice(0, 2)) {
    actions.push({
      label: "Truth gate",
      title: item.lead.full_name,
      detail: item.next_action,
      tone: item.stage.includes("blocked") ? "bad" : "warn",
      href: `${apiBase}/api/v1/leads/${item.lead.id}/truth-resolution`,
    });
  }

  for (const doc of (documentQueue.data?.documents || []).slice(0, 2)) {
    actions.push({
      label: "Document",
      title: titleCase(doc.document_type),
      detail: `${doc.status} · ${doc.filename}`,
      tone: "warn",
      href: `${apiBase}/admin/v2`,
    });
  }

  for (const item of (agentDashboard.data?.items || []).slice(0, 2)) {
    actions.push({
      label: "Agent output",
      title: titleCase(item.agent_name),
      detail: item.summary,
      tone: "warn",
      href: "/agents/review",
    });
  }

  for (const item of (applicationQueue.data?.items || []).filter((item) => item.stage !== "ready_for_human_approval").slice(0, 1)) {
    actions.push({
      label: "Application",
      title: item.lead.full_name,
      detail: item.next_action,
      tone: statusTone(item.stage),
      href: `${apiBase}/admin/v2`,
    });
  }

  return actions.slice(0, 7);
}

export default function HomePage() {
  const apiBase = getApiBaseUrl();
  const adminLinks = useMemo(
    () => [
      { label: "Admin", href: `${apiBase}/admin/v2`, meta: "Lead workflow" },
      { label: "Agent Console", href: "/agents/console", meta: "Controlled internal agents" },
      { label: "Review Queue", href: "/agents/review", meta: "Human approvals" },
      { label: "Drafts", href: `${apiBase}/admin/client-communications/drafts`, meta: "Client-ready messages" },
      { label: "Audit", href: `${apiBase}/admin/audit-logs`, meta: "Traceability" },
      { label: "API Docs", href: `${apiBase}/docs`, meta: "FastAPI reference" },
    ],
    [apiBase]
  );

  const { health } = useBackendStatus();
  const backendOnline = health?.status === "ok";
  const { summary, summaryError, truthQueue, applicationQueue, documentQueue, agentDashboard, loadStatus, load } =
    useWorkspaceData(backendOnline);

  const { leadForm, setLeadForm, message: leadFormMessage, error: leadFormError, onSubmit } = useLeadForm(load);

  const documentCount = documentQueue.data?.count || 0;
  const agentCount = agentDashboard.data?.items?.length || 0;
  const recentLeads = summary.recent_leads.slice(0, 8);
  const recentTruthClaims = summary.recent_truth_audits.slice(0, 3);
  const actionQueue = buildActionQueue({ summary, truthQueue, documentQueue, agentDashboard, applicationQueue, apiBase });
  const readyApplications = applicationQueue.data?.stage_counts?.ready_for_human_approval || 0;
  const blockedApplications = applicationQueue.data?.stage_counts?.blocked_truth_rejected || 0;

  const metrics = [
    { label: "Active leads", value: summary.leads_total, tone: "neutral" as Tone },
    { label: "Review", value: summary.leads_human_review, tone: summary.leads_human_review ? ("warn" as Tone) : ("good" as Tone) },
    { label: "Converted", value: summary.leads_converted, tone: "good" as Tone },
    { label: "Truth pending", value: summary.truth_queue_pending, tone: summary.truth_queue_pending ? ("bad" as Tone) : ("good" as Tone) },
    { label: "Documents", value: documentCount, tone: documentCount ? ("warn" as Tone) : ("good" as Tone) },
    { label: "Agent outputs", value: agentCount, tone: agentCount ? ("warn" as Tone) : ("neutral" as Tone) },
  ];

  const postureCopy = {
    ready: { headline: "All services reachable", body: "Live CRM, truth, document, and agent queues are loaded. Sensitive actions remain review-gated." },
    partial: { headline: "Backend online with partial queues", body: "Some services returned errors. The workspace shows what is available." },
    loading: { headline: "Loading workspace data", body: "Fetching the latest operator queues from the backend." },
    offline: { headline: "Offline workspace preview", body: "Start the FastAPI backend to activate live data. UI remains available for operator review." },
    idle: { headline: "Initializing workspace", body: "Preparing the operator environment." },
  }[loadStatus];

  return (
    <WorkspaceShell health={health}>
      <Topbar
        title="Operations Workspace"
        kicker="Local-first · Human-controlled · Audit-safe"
        loadStatus={loadStatus}
        onRefresh={load}
      />

      <section className={`command-strip ${loadStatus}`} id="workbench">
        <div className="command-copy">
          <span>System posture</span>
          <strong>{postureCopy.headline}</strong>
          <p>{postureCopy.body}</p>
        </div>
        <div className="command-meta">
          <StatusBadge value={backendOnline ? "online" : "offline"} />
          <code>{apiBase}</code>
        </div>
      </section>

      {summaryError ? <InlineNotice label="CRM summary unavailable" detail={summaryError} /> : null}

      <section className="metric-row" aria-label="Workspace metrics">
        {loadStatus === "loading" || loadStatus === "idle"
          ? Array.from({ length: 6 }).map((_, index) => <MetricSkeleton key={index} />)
          : metrics.map((metric) => <MetricPill key={metric.label} {...metric} />)}
      </section>

      <section className="premium-grid" id="pipeline">
        <article className="panel pipeline-panel">
          <div className="panel-header-row">
            <SectionTitle label="Pipeline" title="Active cases" detail={`${recentLeads.length} visible records`} />
            <Link className="text-link" href="#pipeline">
              View pipeline
            </Link>
          </div>
          <CaseTable leads={recentLeads} loading={loadStatus === "loading" || loadStatus === "idle"} />
        </article>

        <aside className="panel action-panel">
          <SectionTitle label="Today" title="Priority queue" detail={`${actionQueue.length} operator actions`} />
          {loadStatus === "loading" || loadStatus === "idle" ? (
            <div className="action-list">
              <ActionCardSkeleton />
              <ActionCardSkeleton />
              <ActionCardSkeleton />
            </div>
          ) : actionQueue.length ? (
            <div className="action-list">
              {actionQueue.map((action, index) => (
                <ActionCard action={action} key={`${action.label}-${action.title}-${index}`} />
              ))}
            </div>
          ) : (
            <EmptyState title="No immediate actions" detail="When reviews, documents, or agent outputs need attention, they will appear here first." />
          )}
        </aside>
      </section>

      <section className="ops-grid" id="verification">
        <article className="panel">
          <SectionTitle label="Truth Engine" title="Resolution stages" detail={`${summary.truth_queue_resolved} claims resolved`} />
          <DataNotice label="Truth queue unavailable" data={truthQueue as OptionalData<unknown>} />
          <QueueStages queue={truthQueue.data} />
        </article>

        <article className="panel">
          <SectionTitle label="Applications" title="Readiness" detail={`${readyApplications} ready · ${blockedApplications} blocked`} />
          <DataNotice label="Application queue unavailable" data={applicationQueue as OptionalData<unknown>} />
          <QueueStages queue={applicationQueue.data} />
        </article>

        <article className="panel">
          <SectionTitle label="Documents" title="Verification" detail={`${documentCount} documents pending`} />
          <DataNotice label="Document queue unavailable" data={documentQueue as OptionalData<unknown>} />
          {documentQueue.data?.documents?.length ? (
            <div className="compact-list">
              {documentQueue.data.documents.slice(0, 5).map((doc) => (
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
            <EmptyState title="No document queue" detail="Documents marked received or needs review will appear here." />
          )}
        </article>
      </section>

      <section className="workbench-grid">
        <article className="panel intake-panel" id="intake">
          <SectionTitle label="CRM" title="Lead intake" detail="Capture opportunities without bypassing downstream verification or human review." />
          <form className="intake-form" onSubmit={onSubmit}>
            <label>
              Full name
              <input
                value={leadForm.full_name}
                required
                placeholder="Client name"
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
              <input value={leadForm.source} onChange={(event) => setLeadForm((prev) => ({ ...prev, source: event.target.value }))} />
            </label>
            <label className="full-field">
              Notes
              <textarea
                value={leadForm.notes}
                placeholder="Budget, intake, visa constraints, documents, language score..."
                onChange={(event) => setLeadForm((prev) => ({ ...prev, notes: event.target.value }))}
              />
            </label>
            <div className="form-actions full-field">
              <button className="button primary" type="submit">
                Create lead
              </button>
              <button className="button secondary" type="button" onClick={() => setLeadForm({
                full_name: "",
                email: "",
                phone: "",
                source: "web_form",
                intent: "study_abroad",
                target_country: "",
                notes: "",
              })}>
                Clear
              </button>
            </div>
          </form>
          {leadFormMessage ? (
            <div className="soft-success">
              <strong>Saved.</strong>
              <span>{leadFormMessage}</span>
            </div>
          ) : null}
          {leadFormError ? <InlineNotice label="Lead was not created" detail={leadFormError} /> : null}
        </article>

        <article className="panel intelligence-panel">
          <SectionTitle label="Claims" title="Recent verification signals" detail="Latest Truth Engine outputs" />
          {recentTruthClaims.length ? (
            <div className="claim-stack">
              {recentTruthClaims.map((claim) => (
                <TruthClaimCard claim={claim} key={claim.id} />
              ))}
            </div>
          ) : (
            <EmptyState title="No claim history" detail="Truth Engine audits will appear here after workflows run." />
          )}
        </article>
      </section>

      <section className="governance-grid" id="governance">
        <article className="panel">
          <SectionTitle label="Governance" title="Safety controls" detail="This is an operator system, not an autonomous submission engine." />
          <div className="safety-list">
            {safetyRules.map((rule) => (
              <div key={rule}>
                <span>✓</span>
                <strong>{rule}</strong>
              </div>
            ))}
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
          ) : (
            <EmptyState title="No pending agent outputs" detail="Controlled recommendations remain reviewable before client use." />
          )}
        </article>

        <article className="panel shortcuts-panel">
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
    </WorkspaceShell>
  );
}
