"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  CommunicationDraft,
  getCommunicationDrafts,
  getHealthStatus,
  HealthStatus,
  Lead,
} from "../../lib/api";
import { WorkspaceShell } from "../../components/WorkspaceShell";
import { Topbar } from "../../components/Topbar";
import { StatusBadge } from "../../components/StatusBadge";
import { SectionTitle } from "../../components/SectionTitle";
import { EmptyState } from "../../components/EmptyState";
import { InlineNotice } from "../../components/InlineNotice";
import { useBackendStatus } from "../../hooks/useBackendStatus";
import { titleCase } from "../../lib/utils";

const STATUS_OPTIONS = [
  { value: "all", label: "All" },
  { value: "draft", label: "Draft" },
  { value: "reviewed", label: "Reviewed" },
];

function CommunicationsPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const status = searchParams.get("status") || "all";
  const leadId = searchParams.get("lead_id") || "";
  const { health } = useBackendStatus();
  const [drafts, setDrafts] = useState<CommunicationDraft[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [healthState, setHealthState] = useState<HealthStatus | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [data, healthData] = await Promise.all([
        getCommunicationDrafts({
          status: status === "all" ? undefined : status,
          lead_id: leadId || undefined,
        }),
        getHealthStatus(),
      ]);
      setDrafts(data.drafts);
      setHealthState(healthData.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load drafts");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, [status, leadId]);

  const updateFilter = (key: string, value: string) => {
    const params = new URLSearchParams(searchParams.toString());
    if (value) params.set(key, value);
    else params.delete(key);
    router.replace(`/communications?${params.toString()}`);
  };

  const counts = drafts.reduce(
    (acc, d) => {
      const s = d.communication.status || "unknown";
      acc[s] = (acc[s] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  return (
    <WorkspaceShell health={healthState}>
      <Topbar
        title="Communications"
        kicker="Client communication drafts"
        loadStatus={loading ? "loading" : "ready"}
        onRefresh={load}
      />
      <section className="panel">
        <SectionTitle
          label="Drafts"
          title="Client communication queue"
          detail="Review, edit, and approve post-approval client communication drafts. Sending is blocked in the MVP."
        />
        {error && <InlineNotice label="Error" detail={error} />}

        <div className="agent-review-filters">
          <label>
            <span>Status</span>
            <select value={status} onChange={(e) => updateFilter("status", e.target.value)}>
              {STATUS_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>Lead ID</span>
            <input
              type="text"
              value={leadId}
              onChange={(e) => updateFilter("lead_id", e.target.value)}
              placeholder="Filter by lead UUID"
            />
          </label>
        </div>

        <div className="agent-review-counts">
          <div className="metric-pill warn">
            <span>Drafts</span>
            <strong>{counts.draft ?? 0}</strong>
          </div>
          <div className="metric-pill good">
            <span>Reviewed</span>
            <strong>{counts.reviewed ?? 0}</strong>
          </div>
          <div className="metric-pill">
            <span>Total</span>
            <strong>{drafts.length}</strong>
          </div>
        </div>

        {drafts.length === 0 ? (
          <EmptyState title="No drafts" detail={loading ? "Loading..." : "No communication drafts match the filters."} />
        ) : (
          <div className="compact-list">
            {drafts.map((item) => (
              <DraftRow item={item} key={item.draft.id} />
            ))}
          </div>
        )}
      </section>
    </WorkspaceShell>
  );
}

function DraftRow({ item }: { item: CommunicationDraft }) {
  const lead = item.lead;
  return (
    <div className="compact-row communication-draft-row">
      <div>
        <strong>{item.communication.title}</strong>
        <span>{item.communication.subject}</span>
        <span className="draft-meta">
          {lead ? lead.full_name : item.draft.lead_id || "No lead"} · {item.communication.template_key}
        </span>
      </div>
      <div className="draft-row-actions">
        <StatusBadge value={item.communication.status} />
        <Link className="button secondary" href={`/communications/drafts/${item.draft.id}`}>
          Review
        </Link>
        {lead && (
          <Link className="button secondary" href={`/communications/leads/${lead.id}`}>
            Lead
          </Link>
        )}
      </div>
    </div>
  );
}

export default function CommunicationsPage() {
  return (
    <Suspense
      fallback={
        <div className="workspace">
          <Topbar title="Communications" kicker="Loading..." loadStatus="loading" onRefresh={() => {}} />
        </div>
      }
    >
      <CommunicationsPageContent />
    </Suspense>
  );
}
