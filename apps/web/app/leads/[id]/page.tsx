"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import Link from "next/link";
import { LeadDetail as LeadDetailType, getLeadDetail } from "../../../lib/api";
import { WorkspaceShell } from "../../../components/WorkspaceShell";
import { Topbar } from "../../../components/Topbar";
import { StatusBadge } from "../../../components/StatusBadge";
import { SectionTitle } from "../../../components/SectionTitle";
import { EmptyState } from "../../../components/EmptyState";
import { InlineNotice } from "../../../components/InlineNotice";
import { TruthClaimCard } from "../../../components/TruthClaimCard";
import { useBackendStatus } from "../../../hooks/useBackendStatus";
import { titleCase } from "../../../lib/utils";

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

export default function LeadDetailPage() {
  const params = useParams();
  const id = Array.isArray(params.id) ? params.id[0] : params.id;
  const { health } = useBackendStatus();
  const [detail, setDetail] = useState<LeadDetailType | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loadStatus, setLoadStatus] = useState<"idle" | "loading" | "ready" | "offline">("idle");

  const load = async () => {
    if (!id) return;
    setLoadStatus("loading");
    setError(null);
    try {
      const data = await getLeadDetail(id);
      setDetail(data);
      setLoadStatus("ready");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load lead detail");
      setLoadStatus("offline");
    }
  };

  useEffect(() => {
    void load();
  }, [id]);

  const lead = detail?.lead;
  if (!lead) return null;

  return (
    <WorkspaceShell health={health}>
      <Topbar
        title={lead ? lead.full_name || "Lead detail" : "Lead detail"}
        kicker="Case workspace"
        loadStatus={loadStatus === "loading" ? "loading" : loadStatus === "offline" ? "offline" : "ready"}
        onRefresh={load}
      />

      <div className="back-link">
        <Link href="/">← Back to workspace</Link>
      </div>

      {error ? <InlineNotice label="Unable to load lead" detail={error} /> : null}

      {loadStatus === "loading" || !detail ? (
        <section className="panel">
          <EmptyState title="Loading case details" detail="Fetching lead record, documents, claims, and workflow history." />
        </section>
      ) : (
        <>
          <section className="lead-hero">
            <div className="lead-hero-main">
              <div className="lead-hero-avatar">{lead.full_name?.slice(0, 1).toUpperCase() || "L"}</div>
              <div>
                <h2>{lead.full_name || "Unnamed lead"}</h2>
                <p>
                  {lead.target_country || "No country"} · {titleCase(lead.intent)} · Created {formatDate(lead.created_at)}
                </p>
              </div>
            </div>
            <StatusBadge value={lead.status} />
          </section>

          <section className="lead-grid">
            <article className="panel">
              <SectionTitle label="Overview" title="Case summary" detail="Key signals from the operator pipeline." />
              <div className="detail-list">
                <div className="detail-row">
                  <span>Email</span>
                  <strong>{lead.email || "—"}</strong>
                </div>
                <div className="detail-row">
                  <span>Phone</span>
                  <strong>{lead.phone || "—"}</strong>
                </div>
                <div className="detail-row">
                  <span>Source</span>
                  <strong>{titleCase(lead.source)}</strong>
                </div>
                <div className="detail-row">
                  <span>Notes</span>
                  <p className="detail-notes">{lead.notes || "No notes recorded."}</p>
                </div>
              </div>
            </article>

            <article className="panel">
              <SectionTitle label="Documents" title="Verification status" detail={`${detail.documents.length} document records`} />
              {detail.documents.length ? (
                <div className="compact-list">
                  {detail.documents.map((doc) => (
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
                <EmptyState title="No documents" detail="Documents uploaded for this lead will appear here." />
              )}
            </article>
          </section>

          <section className="lead-grid">
            <article className="panel">
              <SectionTitle label="Truth Engine" title="Claim verification" detail={`${detail.truth_claims.length} claims`} />
              {detail.truth_claims.length ? (
                <div className="claim-stack">
                  {detail.truth_claims.slice(0, 5).map((claim) => (
                    <TruthClaimCard claim={claim} key={claim.id} />
                  ))}
                </div>
              ) : (
                <EmptyState title="No truth claims" detail="Truth Engine results for this lead will appear here." />
              )}
            </article>

            <article className="panel">
              <SectionTitle label="Agents" title="Controlled outputs" detail={`${detail.agent_runs.length} runs`} />
              {detail.agent_runs.length ? (
                <div className="compact-list">
                  {detail.agent_runs.slice(0, 6).map((run) => (
                    <div className="compact-row" key={run.id}>
                      <div>
                        <strong>{titleCase(run.agent_name)}</strong>
                        <span>{run.task || run.status}</span>
                      </div>
                      <StatusBadge value={run.status} />
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState title="No agent runs" detail="Controlled agents have not produced outputs for this lead yet." />
              )}
            </article>
          </section>

          <section className="lead-grid">
            <article className="panel">
              <SectionTitle label="Applications" title="Authority pipeline" detail={`${detail.applications.length} applications`} />
              {detail.applications.length ? (
                <div className="compact-list">
                  {detail.applications.map((app) => (
                    <div className="compact-row" key={app.id}>
                      <div>
                        <strong>{titleCase(app.authority) || "Application"}</strong>
                        <span>Updated {formatDate(app.updated_at)}</span>
                      </div>
                      <StatusBadge value={app.status} />
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState title="No applications" detail="Application drafts and authority decisions will appear here." />
              )}
            </article>

            <article className="panel">
              <SectionTitle label="Activity" title="Workflow timeline" detail="Recent follow-ups and workflow runs" />
              {detail.follow_ups.length || detail.workflow_runs.length ? (
                <div className="timeline">
                  {detail.workflow_runs.slice(0, 4).map((run) => (
                    <div className="timeline-item" key={`wf-${run.id}`}>
                      <div className="timeline-dot" />
                      <div>
                        <strong>{titleCase(run.workflow_name)}</strong>
                        <span>{formatDate(run.created_at)}</span>
                      </div>
                      <StatusBadge value={run.status} />
                    </div>
                  ))}
                  {detail.follow_ups.slice(0, 4).map((followUp) => (
                    <div className="timeline-item" key={`fu-${followUp.id}`}>
                      <div className="timeline-dot" />
                      <div>
                        <strong>{titleCase(followUp.channel)} follow-up</strong>
                        <span>{formatDate(followUp.created_at)}</span>
                      </div>
                      <StatusBadge value={followUp.status} />
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState title="No recent activity" detail="Workflow runs and follow-ups will be listed here." />
              )}
            </article>
          </section>
        </>
      )}
    </WorkspaceShell>
  );
}
