"use client";

import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  ApplicationRecord,
  DocumentRecord,
  FollowUp,
  getLeadDetail,
  getLeads,
  HumanReview,
  Lead,
  LeadDetail as LeadDetailType,
  Profile,
  SourceReference,
  WorkflowRun,
} from "../../../lib/api";
import { WorkspaceShell } from "../../../components/WorkspaceShell";
import { Topbar } from "../../../components/Topbar";
import { StatusBadge } from "../../../components/StatusBadge";
import { SectionTitle } from "../../../components/SectionTitle";
import { EmptyState } from "../../../components/EmptyState";
import { InlineNotice } from "../../../components/InlineNotice";
import { TruthClaimCard } from "../../../components/TruthClaimCard";
import { LeadIdentity } from "../../../components/LeadIdentity";
import { ActionCard, ActionItem } from "../../../components/ActionCard";
import { MetricPill } from "../../../components/MetricPill";
import { useBackendStatus } from "../../../hooks/useBackendStatus";
import { titleCase, statusTone, Tone } from "../../../lib/utils";
import {
  Skeleton,
  MetricSkeleton,
  ActionCardSkeleton,
} from "../../../components/Skeleton";

const TABS = [
  { key: "overview", label: "Overview" },
  { key: "truth", label: "Truth Engine" },
  { key: "agents", label: "Agent Outputs" },
  { key: "applications", label: "Applications" },
  { key: "communications", label: "Communications" },
  { key: "activity", label: "Activity" },
];

function formatDate(value: string | undefined | null): string {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return value;
  }
}

function DetailRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="detail-row">
      <span>{label}</span>
      <div className="detail-row-value">{children}</div>
    </div>
  );
}

export default function LeadDetailPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const id = Array.isArray(params.id) ? params.id[0] : params.id;
  const { health } = useBackendStatus();
  const [detail, setDetail] = useState<LeadDetailType | null>(null);
  const [allLeads, setAllLeads] = useState<Lead[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loadStatus, setLoadStatus] = useState<"idle" | "loading" | "ready" | "offline">("idle");

  const activeTab = searchParams.get("tab") || "overview";
  const setTab = (key: string) => {
    const url = new URL(window.location.href);
    url.searchParams.set("tab", key);
    router.replace(url.pathname + url.search);
  };

  const load = async () => {
    if (!id) return;
    setLoadStatus("loading");
    setError(null);
    try {
      const [data, leads] = await Promise.all([getLeadDetail(id), getLeads()]);
      setDetail(data);
      setAllLeads(leads);
      setLoadStatus("ready");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load lead detail");
      setLoadStatus("offline");
    }
  };

  useEffect(() => {
    void load();
  }, [id]);

  const leadIndex = useMemo(
    () => allLeads.findIndex((l) => l.id === id),
    [allLeads, id]
  );
  const prevLead = leadIndex > 0 ? allLeads[leadIndex - 1] : null;
  const nextLead = leadIndex >= 0 && leadIndex < allLeads.length - 1 ? allLeads[leadIndex + 1] : null;

  const lead = detail?.lead;

  const actions: ActionItem[] = useMemo(() => {
    const base: ActionItem[] = [
      {
        label: "Agent",
        title: "Run agent",
        detail: "Execute a controlled agent for this lead.",
        tone: "neutral",
        href: `/agents/console?lead_id=${id}`,
      },
    ];
    if (id) {
      base.push({
        label: "Communicate",
        title: "Draft communication pack",
        detail: "Generate post-approval client communication drafts.",
        tone: "good",
        href: `/communications/leads/${id}`,
      });
    }
    return base;
  }, [id]);

  if (loadStatus === "loading" && !detail) {
    return (
      <WorkspaceShell health={health}>
        <Topbar title="Lead detail" kicker="Case workspace" loadStatus="loading" onRefresh={load} />
        <section className="panel">
          <div className="lead-skeleton-header">
            <Skeleton className="skeleton-avatar-lg" />
            <div className="lead-skeleton-title">
              <Skeleton className="skeleton-title" />
              <Skeleton className="skeleton-text" />
            </div>
          </div>
          <div className="metric-row">
            <MetricSkeleton />
            <MetricSkeleton />
            <MetricSkeleton />
            <MetricSkeleton />
          </div>
          <div className="action-grid">
            <ActionCardSkeleton />
            <ActionCardSkeleton />
            <ActionCardSkeleton />
          </div>
        </section>
      </WorkspaceShell>
    );
  }

  if (error || !lead) {
    return (
      <WorkspaceShell health={health}>
        <Topbar title="Lead detail" kicker="Case workspace" loadStatus={loadStatus} onRefresh={load} />
        <section className="panel">
          <EmptyState
            title={error ? "Unable to load lead" : "Lead not found"}
            detail={error || "The requested lead could not be loaded."}
          />
          <div className="back-link">
            <Link href="/">← Back to workspace</Link>
          </div>
        </section>
      </WorkspaceShell>
    );
  }

  const metricItems: { label: string; value: number; tone: Tone }[] = [
    { label: "Truth claims", value: detail?.truth_claims.length || 0, tone: statusTone(detail?.truth_claims.some((c) => c.verdict === "NEEDS_REVIEW") ? "needs_review" : "verified") },
    { label: "Documents", value: detail?.documents.length || 0, tone: "neutral" },
    { label: "Applications", value: detail?.applications.length || 0, tone: "neutral" },
    { label: "Agent runs", value: detail?.agent_runs.length || 0, tone: "neutral" },
  ];

  return (
    <WorkspaceShell health={health}>
      <Topbar
        title={lead.full_name || "Lead detail"}
        kicker="Case workspace"
        loadStatus={loadStatus === "loading" ? "loading" : loadStatus === "offline" ? "offline" : "ready"}
        onRefresh={load}
      />

      <div className="lead-detail-actions">
        <div className="lead-detail-nav">
          <Link href="/" className="button secondary">← Workspace</Link>
          {prevLead && <Link href={`/leads/${prevLead.id}`} className="button secondary">← Prev</Link>}
          {nextLead && <Link href={`/leads/${nextLead.id}`} className="button secondary">Next →</Link>}
        </div>
        <div className="metric-row">
          {metricItems.map((m) => (
            <MetricPill key={m.label} label={m.label} value={m.value} tone={m.tone} />
          ))}
        </div>
      </div>

      <section className="lead-hero">
        <div className="lead-hero-main">
          <LeadIdentity lead={lead} />
        </div>
        <StatusBadge value={lead.status} />
      </section>

      <section className="panel">
        <div className="action-grid">
          {actions.map((action) => (
            <ActionCard key={action.title} action={action} />
          ))}
        </div>
      </section>

      {error ? <InlineNotice label="Error" detail={error} /> : null}

      <nav className="tab-bar">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            className={`tab ${activeTab === tab.key ? "active" : ""}`}
            onClick={() => setTab(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      {activeTab === "overview" && (
        <div className="lead-grid fade-in">
          <article className="panel">
            <SectionTitle label="Overview" title="Case summary" detail="Key signals from the operator pipeline." />
            <div className="detail-list">
              <DetailRow label="Full name">{lead.full_name || "—"}</DetailRow>
              <DetailRow label="Email">{lead.email || "—"}</DetailRow>
              <DetailRow label="Phone">{lead.phone || "—"}</DetailRow>
              <DetailRow label="Intent">{titleCase(lead.intent)}</DetailRow>
              <DetailRow label="Target country">{lead.target_country || "—"}</DetailRow>
              <DetailRow label="Source">{titleCase(lead.source)}</DetailRow>
              <DetailRow label="Created">{formatDate(lead.created_at)}</DetailRow>
              <DetailRow label="Notes">
                <p className="detail-notes">{lead.notes || "No notes recorded."}</p>
              </DetailRow>
            </div>
          </article>

          <ProfilesPanel profiles={detail?.profiles || []} />

          <article className="panel">
            <SectionTitle label="Documents" title="Verification status" detail={`${detail?.documents.length || 0} document records`} />
            <DocumentList documents={detail?.documents || []} />
          </article>

          <article className="panel">
            <SectionTitle label="Applications" title="Authority pipeline" detail={`${detail?.applications.length || 0} applications`} />
            <ApplicationList applications={detail?.applications || []} />
          </article>
        </div>
      )}

      {activeTab === "truth" && (
        <div className="lead-grid fade-in">
          <article className="panel">
            <SectionTitle label="Truth Engine" title="Claim verification" detail={`${detail?.truth_claims.length || 0} claims`} />
            {detail?.truth_claims.length ? (
              <div className="claim-stack">
                {detail.truth_claims.map((claim) => (
                  <TruthClaimCard claim={claim} key={claim.id} />
                ))}
              </div>
            ) : (
              <EmptyState title="No truth claims" detail="Truth Engine results for this lead will appear here." />
            )}
          </article>
          <SourceReferencesPanel references={detail?.source_references || []} />
        </div>
      )}

      {activeTab === "agents" && (
        <div className="lead-grid fade-in">
          <article className="panel">
            <SectionTitle label="Agents" title="Controlled outputs" detail={`${detail?.agent_runs.length || 0} runs`} />
            {detail?.agent_runs.length ? (
              <div className="compact-list">
                {detail.agent_runs.map((run) => (
                  <AgentRunRow run={run} key={run.id} />
                ))}
              </div>
            ) : (
              <EmptyState title="No agent runs" detail="Controlled agents have not produced outputs for this lead yet." />
            )}
          </article>
        </div>
      )}

      {activeTab === "applications" && (
        <div className="lead-grid fade-in">
          <article className="panel">
            <SectionTitle label="Applications" title="Authority pipeline" detail={`${detail?.applications.length || 0} records`} />
            <ApplicationList applications={detail?.applications || []} />
          </article>
        </div>
      )}

      {activeTab === "communications" && (
        <div className="lead-grid fade-in">
          <CommunicationsPanel followUps={detail?.follow_ups || []} leadId={id} />
        </div>
      )}

      {activeTab === "activity" && (
        <div className="lead-grid fade-in">
          <ActivityPanel workflowRuns={detail?.workflow_runs || []} followUps={detail?.follow_ups || []} />
          <ReviewsPanel reviews={detail?.reviews || []} />
        </div>
      )}
    </WorkspaceShell>
  );
}

function ProfilesPanel({ profiles }: { profiles: Profile[] }) {
  if (!profiles.length) return null;
  const profile = profiles[0];
  return (
    <article className="panel">
      <SectionTitle label="Profile" title="Intake profile" detail={`${profiles.length} profile record(s)`} />
      <div className="detail-list">
        <DetailRow label="Qualification">{profile.highest_qualification || "—"}</DetailRow>
        <DetailRow label="Field of study">{profile.field_of_study || "—"}</DetailRow>
        <DetailRow label="Current country">{profile.current_country || "—"}</DetailRow>
        <DetailRow label="Target country">{profile.target_country || "—"}</DetailRow>
        <DetailRow label="Desired role">{profile.desired_role || "—"}</DetailRow>
        <DetailRow label="Budget (EUR)">{profile.budget_eur ?? "—"}</DetailRow>
      </div>
    </article>
  );
}

function DocumentList({ documents }: { documents: DocumentRecord[] }) {
  if (!documents.length) {
    return <EmptyState title="No documents" detail="Documents uploaded for this lead will appear here." />;
  }
  return (
    <div className="compact-list">
      {documents.map((doc) => (
        <div className="compact-row" key={doc.id}>
          <div>
            <strong>{titleCase(doc.document_type)}</strong>
            <span>{doc.filename}</span>
          </div>
          <StatusBadge value={doc.status} />
        </div>
      ))}
    </div>
  );
}

function ApplicationList({ applications }: { applications: ApplicationRecord[] }) {
  if (!applications.length) {
    return <EmptyState title="No applications" detail="Application drafts and authority decisions will appear here." />;
  }
  return (
    <div className="compact-list">
      {applications.map((app) => (
        <div className="compact-row" key={app.id}>
          <div>
            <strong>{titleCase(app.domain)}</strong>
            <span>{app.target_institution_or_employer || app.target_country || "Application"}</span>
          </div>
          <StatusBadge value={app.status} />
        </div>
      ))}
    </div>
  );
}

function SourceReferencesPanel({ references }: { references: SourceReference[] }) {
  return (
    <article className="panel">
      <SectionTitle label="Sources" title="Official source references" detail={`${references.length} records`} />
      {references.length ? (
        <div className="compact-list">
          {references.map((ref) => (
            <div className="compact-row" key={ref.id}>
              <div>
                <strong>{ref.title || "Source"}</strong>
                <a href={ref.source_url} target="_blank" rel="noreferrer" className="source-link">
                  {ref.source_url}
                </a>
              </div>
              <StatusBadge value={ref.source_type || "official"} />
            </div>
          ))}
        </div>
      ) : (
        <EmptyState title="No source references" detail="Official sources attached to truth claims will appear here." />
      )}
    </article>
  );
}

function AgentRunRow({ run }: { run: import("../../../lib/api").AgentRun }) {
  return (
    <div className="compact-row">
      <div>
        <strong>{titleCase(run.agent_name)}</strong>
        <span>{run.task || run.status}</span>
      </div>
      <StatusBadge value={run.status} />
    </div>
  );
}

function CommunicationsPanel({ followUps, leadId }: { followUps: FollowUp[]; leadId?: string }) {
  return (
    <article className="panel">
      <SectionTitle
        label="Communications"
        title="Client communication drafts"
        detail={`${followUps.length} follow-up / draft records`}
      />
      {leadId && (
        <div className="panel-actions">
          <Link className="button" href={`/communications/leads/${leadId}`}>
            Open communication workspace
          </Link>
        </div>
      )}
      {followUps.length ? (
        <div className="compact-list">
          {followUps.map((fu) => (
            <div className="compact-row" key={fu.id}>
              <div>
                <strong>{titleCase(fu.channel)}</strong>
                <span>{fu.message ? fu.message.slice(0, 80) + "..." : "No preview"}</span>
              </div>
              <StatusBadge value={fu.status} />
            </div>
          ))}
        </div>
      ) : (
        <EmptyState title="No communications" detail="Client communication drafts and follow-ups will appear here." />
      )}
    </article>
  );
}

function ActivityPanel({ workflowRuns, followUps }: { workflowRuns: WorkflowRun[]; followUps: FollowUp[] }) {
  const items = [
    ...workflowRuns.map((run) => ({ type: "workflow" as const, data: run })),
    ...followUps.map((fu) => ({ type: "followup" as const, data: fu })),
  ].sort((a, b) => {
    const aDate = new Date((a.data as any).created_at || (a.data as any).started_at || 0).getTime();
    const bDate = new Date((b.data as any).created_at || (b.data as any).started_at || 0).getTime();
    return bDate - aDate;
  });

  return (
    <article className="panel">
      <SectionTitle label="Activity" title="Workflow timeline" detail="Recent follow-ups and workflow runs" />
      {items.length ? (
        <div className="timeline">
          {items.slice(0, 8).map((item, idx) =>
            item.type === "workflow" ? (
              <div className="timeline-item" key={`wf-${(item.data as WorkflowRun).id}-${idx}`}>
                <div className="timeline-dot" />
                <div>
                  <strong>{titleCase((item.data as WorkflowRun).workflow_name)}</strong>
                  <span>{formatDate((item.data as WorkflowRun).created_at)}</span>
                </div>
                <StatusBadge value={(item.data as WorkflowRun).status} />
              </div>
            ) : (
              <div className="timeline-item" key={`fu-${(item.data as FollowUp).id}-${idx}`}>
                <div className="timeline-dot" />
                <div>
                  <strong>{titleCase((item.data as FollowUp).channel)} follow-up</strong>
                  <span>{formatDate((item.data as FollowUp).created_at)}</span>
                </div>
                <StatusBadge value={(item.data as FollowUp).status} />
              </div>
            )
          )}
        </div>
      ) : (
        <EmptyState title="No recent activity" detail="Workflow runs and follow-ups will be listed here." />
      )}
    </article>
  );
}

function ReviewsPanel({ reviews }: { reviews: HumanReview[] }) {
  return (
    <article className="panel">
      <SectionTitle label="Reviews" title="Human review history" detail={`${reviews.length} reviews`} />
      {reviews.length ? (
        <div className="compact-list">
          {reviews.map((review) => (
            <div className="compact-row" key={review.id}>
              <div>
                <strong>{titleCase(review.review_type)}</strong>
                <span>{review.reason || review.reviewer_notes || "No reason recorded"}</span>
              </div>
              <StatusBadge value={review.status} />
            </div>
          ))}
        </div>
      ) : (
        <EmptyState title="No reviews" detail="Human review decisions for this lead will appear here." />
      )}
    </article>
  );
}
