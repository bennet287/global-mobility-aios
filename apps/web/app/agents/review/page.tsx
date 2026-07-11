"use client";

import { useEffect, useState, useCallback, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import {
  AgentReviewDashboard,
  approveAgentRuns,
  convertAgentRuns,
  getAgentReviewDashboard,
  getHealthStatus,
  getLeads,
  HealthStatus,
  Lead,
  rejectAgentRuns,
} from "../../../lib/api";
import Link from "next/link";
import { EmptyState } from "../../../components/EmptyState";
import { InlineNotice } from "../../../components/InlineNotice";
import { SectionTitle } from "../../../components/SectionTitle";
import { StatusBadge } from "../../../components/StatusBadge";
import { Topbar } from "../../../components/Topbar";
import { WorkspaceShell } from "../../../components/WorkspaceShell";
import { titleCase } from "../../../lib/utils";

const STATUS_OPTIONS = [
  { value: "all", label: "All" },
  { value: "pending", label: "Pending review" },
  { value: "approved", label: "Approved" },
  { value: "rejected", label: "Rejected" },
  { value: "converted", label: "Converted" },
];

function ReviewPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const status = searchParams.get("status") || "all";
  const agentName = searchParams.get("agent_name") || "";
  const leadId = searchParams.get("lead_id") || "";

  const [dashboard, setDashboard] = useState<AgentReviewDashboard | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [note, setNote] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<string | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [data, healthData, leadList] = await Promise.all([
        getAgentReviewDashboard({
          status: status === "all" ? undefined : status,
          agent_name: agentName || undefined,
          lead_id: leadId || undefined,
        }),
        getHealthStatus(),
        getLeads(),
      ]);
      setDashboard(data);
      setHealth(healthData.data);
      setLeads(leadList);
      setSelected(new Set());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load review queue");
    } finally {
      setLoading(false);
    }
  }, [status, agentName, leadId]);

  useEffect(() => {
    load();
  }, [load]);

  const updateFilter = (key: string, value: string) => {
    const params = new URLSearchParams(searchParams.toString());
    if (value) params.set(key, value);
    else params.delete(key);
    router.replace(`/agents/review?${params.toString()}`);
  };

  const toggleRun = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleAll = () => {
    if (!dashboard) return;
    if (selected.size === dashboard.items.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(dashboard.items.map((i) => i.id)));
    }
  };

  const handleApprove = async () => {
    if (selected.size === 0) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await approveAgentRuns(Array.from(selected), note);
      setResult(`${res.approved} run(s) approved.`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Approve failed");
    } finally {
      setLoading(false);
    }
  };

  const handleReject = async () => {
    if (selected.size === 0) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await rejectAgentRuns(Array.from(selected), note);
      setResult(`${res.rejected} run(s) rejected.`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Reject failed");
    } finally {
      setLoading(false);
    }
  };

  const handleConvert = async () => {
    if (selected.size === 0) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await convertAgentRuns(Array.from(selected), note);
      setResult(`${res.converted} run(s) converted.`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Convert failed");
    } finally {
      setLoading(false);
    }
  };

  const pendingCount = dashboard?.counts?.pending ?? 0;
  const approvedCount = dashboard?.counts?.approved ?? 0;

  return (
    <WorkspaceShell health={health}>
      <Topbar title="Agent Review Queue" kicker="Human approvals" loadStatus={loading ? "loading" : "ready"} onRefresh={load} />
      <section className="panel agent-review-panel">
        <SectionTitle
          label="Review"
          title="Review outputs"
          detail="Approve, reject, or convert agent outputs. Only approved outputs can be converted."
        />
        {error && <InlineNotice label="Error" detail={error} />}
        {result && <InlineNotice label="Success" detail={result} />}

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
            <span>Agent name</span>
            <input
              type="text"
              value={agentName}
              onChange={(e) => updateFilter("agent_name", e.target.value)}
              placeholder="Filter by agent"
            />
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

        {dashboard && (
          <div className="agent-review-counts">
            <div className="metric-pill warn">
              <span>Pending</span>
              <strong>{pendingCount}</strong>
            </div>
            <div className="metric-pill good">
              <span>Approved</span>
              <strong>{approvedCount}</strong>
            </div>
            <div className="metric-pill">
              <span>Rejected</span>
              <strong>{dashboard.counts?.rejected ?? 0}</strong>
            </div>
            <div className="metric-pill">
              <span>Converted</span>
              <strong>{dashboard.counts?.converted ?? 0}</strong>
            </div>
          </div>
        )}

        <div className="agent-review-bulk">
          <label className="bulk-note">
            <span>Reviewer note</span>
            <input
              type="text"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="Optional batch note"
            />
          </label>
          <div className="form-actions">
            <button className="button primary" disabled={loading || selected.size === 0} onClick={handleApprove}>
              Approve selected
            </button>
            <button className="button secondary" disabled={loading || selected.size === 0} onClick={handleReject}>
              Reject selected
            </button>
            <button className="button secondary" disabled={loading || selected.size === 0} onClick={handleConvert}>
              Convert selected
            </button>
          </div>
        </div>

        {!dashboard || dashboard.items.length === 0 ? (
          <EmptyState title="No outputs" detail={loading ? "Loading..." : "No outputs match the current filters."} />
        ) : (
          <div className="agent-review-table">
            <div className="agent-review-head">
              <span>
                <input
                  type="checkbox"
                  checked={selected.size === dashboard.items.length && dashboard.items.length > 0}
                  onChange={toggleAll}
                />
              </span>
              <span>Run</span>
              <span>Agent</span>
              <span>Lead</span>
              <span>Status</span>
              <span>Conversion</span>
              <span>Summary</span>
            </div>
            {dashboard.items.map((run) => (
              <div key={run.id} className="agent-review-row">
                <span>
                  <input type="checkbox" checked={selected.has(run.id)} onChange={() => toggleRun(run.id)} />
                </span>
                <span className="monospace">{run.id.slice(0, 8)}</span>
                <span>{titleCase(run.agent_name)}</span>
                <span>
                  {run.lead_id ? (
                    <Link href={`/leads/${run.lead_id}`}>
                      {leads.find((l) => l.id === run.lead_id)?.full_name || run.lead_id.slice(0, 8)}
                    </Link>
                  ) : (
                    "—"
                  )}
                </span>
                <span>
                  <StatusBadge value={run.status} />
                </span>
                <span>{run.conversion_target || "—"}</span>
                <span className="run-summary">{run.summary}</span>
                <span>
                  <Link href={`/agents/review/${run.id}`}>Review →</Link>
                </span>
              </div>
            ))}
          </div>
        )}
      </section>
    </WorkspaceShell>
  );
}

export default function AgentReviewPage() {
  return (
    <Suspense fallback={<div className="workspace"><Topbar title="Agent Review Queue" kicker="Loading..." loadStatus="loading" onRefresh={() => {}} /></div>}>
      <ReviewPageContent />
    </Suspense>
  );
}
