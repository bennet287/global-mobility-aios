"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import Link from "next/link";
import {
  AgentRunDetail,
  approveAgentRun,
  convertAgentRun,
  getAgentRunDetail,
  getLeads,
  Lead,
  rejectAgentRun,
} from "../../../../lib/api";
import { WorkspaceShell } from "../../../../components/WorkspaceShell";
import { Topbar } from "../../../../components/Topbar";
import { StatusBadge } from "../../../../components/StatusBadge";
import { SectionTitle } from "../../../../components/SectionTitle";
import { EmptyState } from "../../../../components/EmptyState";
import { InlineNotice } from "../../../../components/InlineNotice";
import { useBackendStatus } from "../../../../hooks/useBackendStatus";
import { titleCase } from "../../../../lib/utils";

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

function safeJson(value: string | undefined | null): Record<string, unknown> | null {
  if (!value) return null;
  try {
    return JSON.parse(value) as Record<string, unknown>;
  } catch {
    return null;
  }
}

export default function AgentRunDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = Array.isArray(params.id) ? params.id[0] : params.id;
  const { health } = useBackendStatus();
  const [detail, setDetail] = useState<AgentRunDetail | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<string | null>(null);
  const [note, setNote] = useState("");

  const load = async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const [runDetail, leadList] = await Promise.all([getAgentRunDetail(id), getLeads()]);
      setDetail(runDetail);
      setLeads(leadList);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load agent run");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, [id]);

  const lead = leads.find((l) => l.id === detail?.run.lead_id);
  const output = safeJson(detail?.run.output_json);

  const handleApprove = async () => {
    if (!id) return;
    setLoading(true);
    try {
      await approveAgentRun(id, note);
      setResult("Agent output approved.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Approve failed");
    } finally {
      setLoading(false);
    }
  };

  const handleReject = async () => {
    if (!id) return;
    setLoading(true);
    try {
      await rejectAgentRun(id, note);
      setResult("Agent output rejected.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Reject failed");
    } finally {
      setLoading(false);
    }
  };

  const handleConvert = async () => {
    if (!id) return;
    setLoading(true);
    try {
      await convertAgentRun(id, note);
      setResult("Agent output converted.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Convert failed");
    } finally {
      setLoading(false);
    }
  };

  const canConvert = detail?.run.status === "approved";

  return (
    <WorkspaceShell health={health}>
      <Topbar
        title={detail ? titleCase(detail.run.agent_name) : "Agent run"}
        kicker="Review detail"
        loadStatus={loading ? "loading" : "ready"}
        onRefresh={load}
      />

      <div className="back-link">
        <Link href="/agents/review">← Back to review queue</Link>
      </div>

      {error && <InlineNotice label="Error" tone="bad" detail={error} />}
      {result && <InlineNotice label="Success" tone="good" detail={result} />}

      {!detail ? (
        <section className="panel">
          <EmptyState title="Loading run" detail="Fetching agent run details and audit history." />
        </section>
      ) : (
        <>
          <section className="panel">
            <SectionTitle
              label="Agent output"
              title={titleCase(detail.run.agent_name)}
              detail={`Created ${formatDate(detail.run.created_at)} · ${lead ? lead.full_name : detail.run.lead_id || "No lead"}`}
            />
            <div className="detail-list">
              <div className="detail-row">
                <span>Task</span>
                <strong>{detail.run.task}</strong>
              </div>
              <div className="detail-row">
                <span>Status</span>
                <StatusBadge value={detail.run.status} />
              </div>
              {lead && (
                <div className="detail-row">
                  <span>Lead</span>
                  <Link href={`/leads/${lead.id}`}>
                    <strong>{lead.full_name}</strong>
                  </Link>
                </div>
              )}
              {detail.latest_review_note && detail.latest_review_note !== "-" && (
                <div className="detail-row">
                  <span>Latest review note</span>
                  <p className="detail-notes">{detail.latest_review_note}</p>
                </div>
              )}
            </div>
          </section>

          <section className="panel">
            <SectionTitle label="Output" title="Generated output" detail="Preview before taking action." />
            {output ? (
              <pre className="agent-output-preview">{JSON.stringify(output, null, 2)}</pre>
            ) : (
              <EmptyState title="No output" detail="This run has no parseable output." />
            )}
          </section>

          <section className="panel">
            <SectionTitle label="Action" title="Review decision" detail="Approve, reject, or convert this output." />
            <div className="review-note-field">
              <label>
                <span>Reviewer note</span>
                <textarea
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  placeholder="Optional note for the audit log..."
                  rows={3}
                />
              </label>
            </div>
            <div className="form-actions">
              <button className="button" onClick={handleApprove} disabled={loading}>
                Approve
              </button>
              <button className="button secondary" onClick={handleReject} disabled={loading}>
                Reject
              </button>
              <button className="button primary" onClick={handleConvert} disabled={loading || !canConvert}>
                Convert
              </button>
            </div>
            {!canConvert && (
              <p className="hint">Only approved outputs can be converted.</p>
            )}
          </section>

          <section className="panel">
            <SectionTitle label="Audit" title="Audit history" detail={`${detail.audit_history.length} entries`} />
            {detail.audit_history.length ? (
              <div className="compact-list">
                {detail.audit_history.map((entry) => (
                  <div className="compact-row" key={entry.id}>
                    <div>
                      <strong>{titleCase(entry.action)}</strong>
                      <span>
                        {entry.actor} · {formatDate(entry.created_at)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState title="No audit entries" detail="This run has not been reviewed yet." />
            )}
          </section>
        </>
      )}
    </WorkspaceShell>
  );
}
